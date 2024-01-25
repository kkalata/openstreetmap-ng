import * as L from "leaflet"
import { getActionSidebar, switchActionSidebar } from "../_action-sidebar.js"
import { getMapState, setMapState } from "../_map-utils.js"
import { qsParse } from "../_qs.js"
import { routerNavigate } from "../_router.js"
import { configureStandardForm } from "../_standard-form.js"
import { getPageTitle } from "../_title.js"
import { isLatitude, isLongitude } from "../_utils.js"
import { DataLayer, getOverlayLayerById } from "../leaflet/_layers.js"
import { focusMapObject } from "../leaflet/_map-focus.js"

/**
 * Create a new new note controller
 * @param {L.Map} map Leaflet map
 * @returns {object} Controller
 */
export const getNewNoteController = (map) => {
    const sidebar = getActionSidebar("new-note")
    const sidebarTitle = sidebar.querySelector(".sidebar-title").textContent
    const form = sidebar.querySelector("form")
    const lonInput = form.querySelector("input[name=lon]")
    const latInput = form.querySelector("input[name=lat]")

    let halo = null

    // On marker drag start, remove the halo
    const onMarkerDragStart = () => {
        halo.setStyle({ opacity: 0 })
    }

    // On marker drag end, update the form's coordinates and add the halo
    const onMarkerDragEnd = () => {
        const latLng = marker.getLatLng()
        lonInput.value = latLng.lng
        latInput.value = latLng.lat

        halo.setLatLng(latLng)
        halo.setStyle(DataLayer.options.styles.noteHalo)
    }

    // On success callback, enable notes layer and navigate to the new note
    const onFormSuccess = (data) => {
        const state = getMapState(map)
        const notesLayerCode = getOverlayLayerById("notes").options.layerCode
        if (!state.layersCode.includes(notesLayerCode)) {
            state.layersCode += notesLayerCode
            setMapState(map, state)
        }

        routerNavigate(`/note/${data.noteId}`)
    }

    // Listen for events
    configureStandardForm(form, onFormSuccess)

    return {
        load: () => {
            form.reset()
            switchActionSidebar("new-note")
            document.title = getPageTitle(sidebarTitle)

            let center = map.getCenter()

            // Allow default location setting via URL search parameters
            const searchParams = qsParse(location.search.substring(1))
            if (searchParams.lon && searchParams.lat) {
                const lon = parseFloat(searchParams.lon)
                const lat = parseFloat(searchParams.lat)

                if (isLongitude(lon) && isLatitude(lat)) {
                    center = L.latLng(lat, lon)
                }
            }

            if (halo) console.warn("Halo already exists")

            halo = focusMapObject(map, {
                type: "note",
                id: null,
                lon: center.lng,
                lat: center.lat,
                icon: "new",
                draggable: true,
            })

            // Listen for events
            const marker = halo.marker
            marker.addEventListener("dragstart", onMarkerDragStart)
            marker.addEventListener("dragend", onMarkerDragEnd)
        },
        unload: () => {
            focusMapObject(map, null)
            halo = null
        },
    }
}
