import { Tooltip } from "bootstrap"
import * as L from "leaflet"

const minZoom = 12

export const getNewNoteControl = (options) => {
    const control = L.control(options)

    // On zoomend, disable/enable button
    const onZoomEnd = () => {
        const currentZoom = control.map.getZoom()

        // Enable/disable buttons based on current zoom level
        if (currentZoom < minZoom) {
            if (!control.button.disabled) {
                control.button.disabled = true
                control.tooltip.setContent({
                    ".tooltip-inner": I18n.t("javascripts.site.createnote_disabled_tooltip"),
                })
            }
        } else {
            // biome-ignore lint/style/useCollapsedElseIf: Readability
            if (control.button.disabled) {
                control.button.disabled = false
                control.tooltip.setContent({
                    ".tooltip-inner": I18n.t("javascripts.site.createnote_tooltip"),
                })
            }
        }
    }

    control.onAdd = (map) => {
        // Create container
        const container = document.createElement("div")

        // Create a button and a tooltip
        const button = document.createElement("button")
        button.className = "control-button"
        button.innerHTML = "<span class='icon note'></span>"

        const tooltip = Tooltip.getOrCreateInstance(button, {
            title: "",
            placement: "left",
            // TODO: check RTL support, also with leaflet options
        })

        control.button = button
        control.tooltip = tooltip
        control.map = map

        // Listen for events
        map.addEventListener("zoomend", onZoomEnd)

        // Initial update to set button states
        onZoomEnd()

        return container
    }

    return control
}
