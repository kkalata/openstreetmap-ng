import * as L from "leaflet"
import { qsParse, qsStringify } from "./_qs.js"
import { shortLinkEncode } from "./_shortlink.js"
import { isLatitude, isLongitude, isZoom, zoomPrecision } from "./_utils.js"
import { getBaseLayerById, getLayerIdByCode, getOverlayLayerById } from "./leaflet/_layers.js"

// Encode current layers to a string using layer codes
export const getMapLayersCode = (map) => {
    const layerCodes = []
    map.eachLayer((layer) => {
        if (layer.options.layerCode) layerCodes.push(layer.options.layerCode)
    })
    return layerCodes.join("")
}

// Get the base layer id of the map
export const getMapBaseLayerId = (map) => {
    let baseLayerId = null
    map.eachLayer((layer) => {
        if (getBaseLayerById(layer.options.layerId)) baseLayerId = layer.options.layerId
    })
    if (!baseLayerId) throw new Error("No base layer found")
    return baseLayerId
}

// Get the base layer instance of the map
export const getMapBaseLayer = (map) => {
    let baseLayer = null
    map.eachLayer((layer) => {
        if (getBaseLayerById(layer.options.layerId)) baseLayer = layer
    })
    if (!baseLayer) throw new Error("No base layer found")
    return baseLayer
}

// Set the map layers from a layers code
export const setMapLayersCode = (map, layersCode) => {
    const layersIds = new Set()

    // Extract base layers to validate the code
    // and to check whether we need to use default base layer
    const baseLayers = []

    for (let i = 0; i < layersCode.length; i++) {
        const layerCode = layersCode[i]
        const layerId = getLayerIdByCode(layerCode)
        layersIds.add(layerId)

        const baseLayer = getBaseLayerById(layerId)
        if (baseLayer) baseLayers.push(baseLayer)
    }

    if (baseLayers.length > 1) {
        console.error("Invalid layers code (too many base layers)", layersCode)
        return
    }

    // Add default base layer if no base layer is present
    if (baseLayers.length === 0) {
        const layerId = getLayerIdByCode("")
        layersIds.add(layerId)
        const layer = getBaseLayerById(layerId)
        baseLayers.push(layer)
    }

    // Remove layers not found in the code
    map.eachLayer((layer) => {
        if (!layersIds.has(layer.options.layerId)) {
            map.removeLayer(layer)
        } else {
            layersIds.delete(layer.options.layerId)
        }
    })

    // Add missing layers
    for (const layerId of layersIds) {
        const layer = getBaseLayerById(layerId) ?? getOverlayLayerById(layerId)
        map.addLayer(layer)
    }

    // Trigger the baselayerchange event
    // https://leafletjs.com/reference.html#map-baselayerchange
    // https://leafletjs.com/reference.html#layerscontrolevent
    map.fire("baselayerchange", { layer: baseLayers[0], name: baseLayers[0].options.layerId })
}

// Get the current map state object
export const getMapState = (map) => {
    const center = map.getCenter()
    const zoom = map.getZoom()
    const layersCode = getMapLayersCode(map)
    return { center, zoom, layersCode }
}

// Set the map state from a state object
export const setMapState = (map, state, options) => {
    const { center, zoom, layersCode } = state
    console.debug("setMapState", state)
    if (center && zoom) map.setView(center, zoom, options)
    if (layersCode) setMapLayersCode(map, layersCode)
}

// TODO: always map?
// Create a hash string for a state
// Accepts either a map object or an object with the following properties:
//   center: LatLng
//   zoom: number
//   layers: string
// Returns a string like "#map=15/51.505/-0.09&layers=BT"
export const encodeMapState = (args) => {
    let center
    let zoom
    let layersCode

    if (args instanceof L.Map) {
        ;({ center, zoom, layersCode } = getMapState(args))
    } else {
        center = args.center ?? L.latLng(args.lat, args.lon)
        center = center.wrap()
        zoom = args.zoom
        layersCode = args.layersCode ?? args.layers ?? ""
    }

    const precision = zoomPrecision(zoom)
    const lat = center.lat.toFixed(precision)
    const lon = center.lng.toFixed(precision)

    const hash = layersCode ? `#map=${zoom}/${lat}/${lon}&layers=${layersCode}` : `#map=${zoom}/${lat}/${lon}`
    return hash
}

// Parse a hash string into a state
export const parseMapState = (hash) => {
    const result = {}

    // Skip if there's no hash
    const i = hash.indexOf("#")
    if (i < 0) return result

    // Parse the hash as a query string
    const params = qsParse(hash.slice(i + 1))

    // Assign map state only if present and length is 3
    if (params.map) {
        const components = params.map.split("/")
        if (components.length === 3) {
            const zoom = parseInt(components[0], 10)
            const lat = parseFloat(components[1])
            const lon = parseFloat(components[2])

            // Assign position only if it's valid
            if (isZoom(zoom) && isLatitude(lat) && isLongitude(lon)) {
                result.zoom = zoom
                result.center = L.latLng(lat, lon)
            }
        }
    }

    // Assign layers only if present
    if (params.layers) result.layersCode = params.layers

    return result
}

// Get a URL for the current map location, optionally including a marker
export const getMapUrl = (map, showMarker = false) => {
    const { center, zoom, layersCode } = getMapState(map)
    const precision = zoomPrecision(zoom)
    const lat = center.lat.toFixed(precision)
    const lon = center.lng.toFixed(precision)
    const hash = encodeMapState({ center, zoom, layersCode })

    if (showMarker) {
        return `${location.protocol}//${location.host}/?mlat=${lat}&mlon=${lon}${hash}`
    }

    return `${location.protocol}//${location.host}/${hash}`
}

// Get a short URL for the current map location, optionally including a marker
export const getMapShortUrl = (map, showMarker = false) => {
    const { center, zoom, layersCode } = getMapState(map)
    const precision = zoomPrecision(zoom)
    const lat = center.lat.toFixed(precision)
    const lon = center.lng.toFixed(precision)

    const code = shortLinkEncode(lon, lat, zoom)
    const params = {}

    if (layersCode) params.layers = layersCode
    if (showMarker) params.m = ""

    let protocol = "https:"
    let host = "osm.org"

    // Use the current protocol and host if running locally
    if (location.hostname === "localhost" || location.hostname === "127.0.0.1") {
        protocol = location.protocol
        host = location.host
    }

    if (Object.keys(params).length > 0) {
        return `${protocol}//${host}/go/${code}?${qsStringify(params)}`
    }

    return `${protocol}//${host}/go/${code}`
}

// Get HTML for embedding the current map location, optionally including a marker
export const getMapEmbedHtml = (map, markerLatLng = null) => {
    const bbox = map.getBounds().toBBoxString()
    const layerId = map.getBaseLayerId()

    const params = {
        bbox: bbox,
        layer: layerId,
    }

    if (markerLatLng) {
        // Don't apply precision on embeds
        const lat = markerLatLng.lat
        const lon = markerLatLng.lng
        params.marker = `${lat},${lon}`
    }

    // Container for HTML generation
    const container = document.createElement("div")

    // Create the iframe
    const iframe = document.createElement("iframe")
    iframe.width = 425
    iframe.height = 350
    iframe.src = `${location.protocol}//${location.host}/export/embed.html?${qsStringify(params)}`
    iframe.style.border = "1px solid black"
    container.appendChild(iframe)

    // Create the link to view the larger map
    const small = document.createElement("small")
    const link = document.createElement("a")
    link.href = getMapUrl(map, markerLatLng)
    link.textContent = I18n.t("javascripts.share.view_larger_map")
    small.appendChild(link)
    container.appendChild(small)

    return container.innerHTML
}

// Get a geo URI for the current map location
export const getMapGeoUri = (map) => {
    const { center, zoom } = getMapState(map)
    const precision = zoomPrecision(zoom)
    const lat = center.lat.toFixed(precision)
    const lon = center.lng.toFixed(precision)
    return `geo:${lat},${lon}?z=${zoom}`
}