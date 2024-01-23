import * as L from "leaflet"

const maxZoom = 25
const tileSize = 256
const optimalExportResolution = 1024
const earthRadius = 6371000
const earthCircumference = 40030173 // 2 * Math.PI * EARTH_RADIUS

// TODO: add information that only base layer is exported, no markers etc.

// https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob#quality
const imageQuality = 0.95

/**
 * Returns the optimal zoom level and resolution for exporting the map image
 * @param {number[]} bounds Map bounds in the format [minLat, minLon, maxLat, maxLon]
 */
export const getOptimalExportParams = (bounds) => {
    let [minLat, minLon, maxLat, maxLon] = bounds
    // The bounds cross the antimeridian
    if (minLon > maxLon) maxLon += 360

    const sizeInDegrees = L.point(maxLon - minLon, maxLat - minLat)
    const sizeInRadians = sizeInDegrees.multiplyBy(Math.PI / 180)
    const sizeInMeters = sizeInRadians.multiplyBy(earthRadius)
    const xProportion = sizeInMeters.x / earthCircumference
    const yProportion = sizeInMeters.y / earthCircumference

    let optimalZoom = maxZoom

    // Find the zoom level that closest matches the optimal export resolution
    for (let z = 0; z < maxZoom; z++) {
        const yResolution = tileSize * 2 ** z * yProportion
        if (yResolution < optimalExportResolution * (2 / 3)) continue
        optimalZoom = z
    }

    const optimalEarthResolution = tileSize * 2 ** optimalZoom
    const optimalXResolution = optimalEarthResolution * xProportion
    const optimalYResolution = optimalEarthResolution * yProportion

    return { zoom: optimalZoom, xResolution: optimalXResolution, yResolution: optimalYResolution }
}

/**
 * Get tile coordinates for the given coordinates and zoom level
 * @param {number} lon Longitude
 * @param {number} lat Latitude
 * @param {number} zoom Zoom level
 * @returns {{ x: number, y: number }} Tile coordinates
 * @example
 * getTileCoords(16.3725, 48.208889, 12)
 * // => { x: 2234, y: 1420 }
 */
const getTileCoords = (lon, lat, zoom) => {
    const n = 2 ** zoom
    const x = Math.floor(((lon + 180) / 360) * n)
    const y = Math.floor(
        ((1 - Math.log(Math.tan((lat * Math.PI) / 180) + 1 / Math.cos((lat * Math.PI) / 180)) / Math.PI) / 2) * n,
    )
    return { x, y }
}

/**
 * Get coordinates for the given tile coordinates and zoom level
 * @param {number} x Tile X coordinate
 * @param {number} y Tile Y coordinate
 * @param {number} zoom Zoom level
 * @returns {{ lon: number, lat: number }} Coordinates
 * @example
 * getLatLonFromTileCoords(2234, 1420, 12)
 * // => { lon: 16.3725, lat: 48.208889 }
 */
const getLatLonFromTileCoords = (x, y, zoom) => {
    const n = 2 ** zoom
    const lon = (x / n) * 360 - 180
    const lat = (Math.atan(Math.sinh(Math.PI * (1 - (2 * y) / n))) * 180) / Math.PI
    return { lat, lon }
}

/**
 * Wrap the tile coordinates to the valid range at the given zoom level
 * @param {number} x Tile X coordinate
 * @param {number} y Tile Y coordinate
 * @param {number} zoom Zoom level
 * @returns {{ x: number, y: number }} Wrapped tile coordinates
 * @example
 * wrapTileCoords(2234, 1420, 10)
 * // => { x: 186, y: 396 }
 */
const wrapTileCoords = (x, y, zoom) => {
    const n = 2 ** zoom
    return { x: ((x % n) + n) % n, y: ((y % n) + n) % n }
}

/**
 * Export the map image
 * @param {string} mimeType Image MIME type
 * @param {number[]} bounds Map bounds in the format [minLat, minLon, maxLat, maxLon]
 * @param {number} zoom Zoom level
 * @param {L.TileLayer} baseLayer Base layer
 * @returns {Promise<Blob>} Image blob
 * @example
 * exportMapImage("image/png", [48.208889, 16.3725, 48.209444, 16.373056], 12, baseLayer)
 * // => Blob { size: 123456, type: "image/png" }
 */
export const exportMapImage = async (mimeType, bounds, zoom, baseLayer) => {
    let [minLat, minLon, maxLat, maxLon] = bounds
    // The bounds cross the antimeridian
    if (minLon > maxLon) maxLon += 360

    const minTileCoords = getTileCoords(minLon, maxLat, zoom)
    const maxTileCoords = getTileCoords(maxLon, minLat, zoom)

    // Calculate the pixel position for trimming
    const wrappedMinTileCoords = wrapTileCoords(minTileCoords.x, minTileCoords.y, zoom)
    const minTopLeft = getLatLonFromTileCoords(wrappedMinTileCoords.x, wrappedMinTileCoords.y, zoom)
    const wrappedMinEndTileCoords = wrapTileCoords(minTileCoords.x + 1, minTileCoords.y + 1, zoom)
    const minBottomRight = getLatLonFromTileCoords(wrappedMinEndTileCoords.x, wrappedMinEndTileCoords.y, zoom)
    const wrappedMaxTileCoords = wrapTileCoords(maxTileCoords.x, maxTileCoords.y, zoom)
    const maxTopLeft = getLatLonFromTileCoords(wrappedMaxTileCoords.x, wrappedMaxTileCoords.y, zoom)
    const wrappedMaxEndTileCoords = wrapTileCoords(maxTileCoords.x + 1, maxTileCoords.y + 1, zoom)
    const maxBottomRight = getLatLonFromTileCoords(wrappedMaxEndTileCoords.x, wrappedMaxEndTileCoords.y, zoom)

    const topOffset = Math.round(((maxLat - minTopLeft.lat) / (minBottomRight.lat - minTopLeft.lat)) * tileSize)
    const leftOffset = Math.round(((minLon - minTopLeft.lon) / (minBottomRight.lon - minTopLeft.lon)) * tileSize)
    const bottomOffset = Math.round(((maxBottomRight.lat - minLat) / (maxBottomRight.lat - maxTopLeft.lat)) * tileSize)
    const rightOffset = Math.round(((maxBottomRight.lon - maxLon) / (maxBottomRight.lon - maxTopLeft.lon)) * tileSize)

    // Create a canvas to draw the tiles on
    const canvas = document.createElement("canvas")
    canvas.width = (maxTileCoords.x - minTileCoords.x + 1) * tileSize - leftOffset - rightOffset
    canvas.height = (maxTileCoords.y - minTileCoords.y + 1) * tileSize - topOffset - bottomOffset
    const ctx = canvas.getContext("2d", { alpha: false })

    const fetchTilePromise = (x, y) => {
        return new Promise((resolve, reject) => {
            const img = new Image()
            img.crossOrigin = "anonymous"
            img.onload = () => {
                const dx = (x - minTileCoords.x) * tileSize - leftOffset
                const dy = (y - minTileCoords.y) * tileSize - topOffset
                ctx.drawImage(img, dx, dy)
                resolve()
            }
            img.onerror = () => {
                reject(`Failed to load tile at x=${x}, y=${y}, z=${zoom}`)
            }
            img.src = baseLayer.getTileUrl({ x, y, z: zoom })
        })
    }

    // Fetch tiles in parallel
    const fetchTilesPromises = []
    for (let x = minTileCoords.x; x <= maxTileCoords.x; x++) {
        for (let y = minTileCoords.y; y <= maxTileCoords.y; y++) {
            const wrapped = wrapTileCoords(x, y, zoom)
            fetchTilesPromises.push(fetchTilePromise(wrapped.x, wrapped.y))
        }
    }

    await Promise.all(fetchTilesPromises)

    // Export the canvas to an image
    return new Promise((resolve, reject) => {
        canvas.toBlob(
            (blob) => {
                if (blob) resolve(blob)
                else reject("Failed to export the map image")
            },
            mimeType,
            imageQuality,
        )
    })
}