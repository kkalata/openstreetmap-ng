import { read } from "bun:ffi"
import { qsEncode, qsParse } from "../_qs.js"
import { getMarkerIcon } from "../leaflet/_utils.js"
import { getActionSidebar, switchActionSidebar } from "./_action-sidebar.js"
import * as L from "leaflet"

const logTen = Math.log(10)

export const getMeasuringController = (map) => {
    const sidebar = getActionSidebar("measure")
    const totalDistanceLabel = sidebar.querySelector(".total-distance")
    let markers = []
    let divIcons = []
    let line = null
    let distance = 0
    let param = ""

    map.createPane("labelPane")
    map.getPane("labelPane").style.zIndex = 400
    map.getPane("labelPane").style.pointerEvents = "none"

    const formatDistance = (distance) => {
        // TODO: support for miles
        const precision = 10 ** (2 - Math.floor(Math.log(distance) / logTen)) || 1
        const roundedMeters = Math.round(distance * precision) / precision || 1
        const num = roundedMeters < 1000 ? `${roundedMeters}m` : `${roundedMeters / 1000}km`
        return num
    }

    const saveParam = () => {
        if (param[0] === ";") param = param.substring(1)
        const url = new URL(document.URL)
        url.searchParams.set("pos", param)
        history.replaceState(null, "", url)
    }

    const addLabel = (index) => {
        const point = markers[index].getLatLng()
        const previous = markers[index - 1].getLatLng()
        const middle = L.LineUtil.polylineCenter([point, previous], L.CRS.EPSG3857)
        const screenPoint = map.latLngToContainerPoint(point)
        const previousScreen = map.latLngToContainerPoint(previous)
        const _distance = point.distanceTo(previous)
        const num = formatDistance(_distance)
        let angle =
            (-Math.atan2(screenPoint.x - previousScreen.x, screenPoint.y - previousScreen.y) * 180) / Math.PI + 90

        if (angle > 90) angle -= 180
        if (angle < -90) angle += 180

        const label = L.marker(middle, {
            pane: "labelPane",
            icon: L.divIcon({
                className: "measure-label",
                html: `<div style="transform:rotate(${angle}deg)">${num}</div>`,
                iconSize: [0, 0],
            }),
        })
            .addTo(map)
            .on("click", onLineClick)
        divIcons.push(label)
        param += `;${point.lat.toFixed(4)},${point.lng.toFixed(4)}`

        distance += _distance
        totalDistanceLabel.innerText = formatDistance(distance)
    }

    const addLabels = () => {
        distance = 0
        const point = markers[0].getLatLng()
        param = `${point.lat.toFixed(4)},${point.lng.toFixed(4)}`
        for (const icon of divIcons) {
            icon.remove()
        }
        divIcons = []
        for (let index = 1; index < markers.length; index++) {
            addLabel(index)
        }
    }

    const reAdd = () => {
        updateLine()
        addLabels()
    }

    const updateLine = () => {
        const latLngs = markers.map((marker) => marker.getLatLng())
        line.setLatLngs(latLngs)
    }

    const onMarkerDrag = () => {
        // after dragging markers have wrong z-indexes
        map.fire("viewreset")

        reAdd()
    }

    const markerFactory = (color) =>
        L.marker(L.latLng(0, 0), {
            icon: getMarkerIcon(color, true),
            draggable: true,
            autoPan: true,
        })
            .addTo(map)
            .on("drag", onMarkerDrag)
            .on("dragend", saveParam)

    const onHeadMarkerClick = () => {
        if (markers.length === 2) return
        const lastMarker = markers[markers.length - 2] // remove second to last marker from array
        markers.splice(markers.length - 2, 1)
        markers[markers.length - 1].setLatLng(lastMarker.getLatLng())
        lastMarker.remove() // remove second to last marker from map
        reAdd()
        saveParam()
    }

    const onTailMarkerClick = () => {
        if (!markers[2]) return
        markers[0].setLatLng(markers[1].getLatLng())
        markers[1].remove()
        markers.splice(1, 1)
        reAdd()
        saveParam()
    }

    const addMarker = (e) => {
        // if there are 0 markers create green one
        if (markers.length === 0) {
            const startMarker = markerFactory("green").setLatLng(e.latlng)
            markers.push(startMarker)
            startMarker.addEventListener("click", onTailMarkerClick)
            param = `${e.latlng.lat.toFixed(4)},${e.latlng.lng.toFixed(4)}`
            line = L.polyline([e.latlng], { color: "#6ea8fe", weight: 5, noClip: true }).addTo(map)
            line.addEventListener("mousedown", onLineClick)
            totalDistanceLabel.innerText = "0km"
            return
        }

        // if there is 1 marker create red marker, else blue
        if (markers.length === 1) {
            const headMarker = markerFactory("red")
            markers.push(headMarker)
            headMarker.addEventListener("click", onHeadMarkerClick)
        } else {
            const marker = markerFactory("blue")
                .setLatLng(markers[markers.length - 1].getLatLng())
                .addEventListener("click", () => {
                    markers.splice(markers.indexOf(marker), 1)
                    marker.remove()
                    reAdd()
                    saveParam()
                })
            markers.splice(markers.length - 1, 0, marker)
        }

        markers[markers.length - 1].setLatLng(e.latlng)
        line.addLatLng(e.latlng)
        addLabel(markers.length - 1)
        saveParam()
    }

    const onLineClick = (e) => {
        // TODO: clicking on line should add marker
        // why closestLayerPoint returns null?

        // skip adding marker
        map.removeEventListener("click", addMarker)
        setTimeout(() => map.addEventListener("click", addMarker), 0)

        console.log("clicked on line. \nI have no idea what to do")

        let minPoint = null
        let minDistance = Number.POSITIVE_INFINITY
        let index = 0

        for (let i = 1; i < markers.length; i++) {
            const marker = markers[i]
            const previous = markers[i - 1]
            const point = L.LineUtil.closestPointOnSegment(
                map.latLngToLayerPoint(e.latlng),
                map.latLngToLayerPoint(marker.getLatLng()),
                map.latLngToLayerPoint(previous.getLatLng()),
            )
            const distance = map.distance(map.layerPointToLatLng(point), e.latlng)
            if (distance < minDistance) {
                minPoint = point
                minDistance = distance
                index = i
            }
        }

        const marker = markerFactory("blue")
            .setLatLng(map.layerPointToLatLng(minPoint))
            .addEventListener("click", () => {
                markers.splice(markers.indexOf(marker), 1)
                marker.remove()
                reAdd()
                saveParam()
            })
        console.log(minPoint, index)
        markers = [...markers.slice(0, index), ...markers.slice(index)]
        reAdd()
        saveParam()
    }

    return {
        load: () => {
            distance = 0
            const searchParams = qsParse(location.search.substring(1))
            if (searchParams.pos) {
                const positions = searchParams.pos.split(";")
                if (positions.length === 0) return
                for (const pos of positions) {
                    const [lat, lng] = pos.split(",").map(Number)

                    // Grecefully handle errors
                    if (Number.isNaN(lat + lng) && !Number.isFinite(lat + lng)) continue

                    addMarker({ latlng: { lat: lat, lng: lng } })
                }

                if (markers.length > 1) {
                    const bounds = line.getBounds()
                    map.fitBounds(bounds, {
                        animate: false,
                    })
                }
            }

            switchActionSidebar(map, "measure")
            map.addEventListener("click", addMarker)
        },
        unload: () => {
            for (const label of divIcons) {
                label?.remove()
            }
            for (const label of markers) {
                label?.remove()
            }
            divIcons = []
            markers = []
            line?.remove()

            map.removeEventListener("click", addMarker)
            line?.removeEventListener("click", onLineClick)
        },
    }
}
