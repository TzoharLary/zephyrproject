/**
 * help.js — Context-sensitive help tooltip system.
 *
 * Usage in HTML:
 *   <button class="help-trigger" data-help="הסבר כלשהו">?</button>
 *
 * When user clicks the trigger the popup appears next to it.
 * Clicking anywhere else (or pressing Escape) closes the popup.
 */

(function () {
    "use strict";

    /* Shared popup element — one per page, repositioned as needed. */
    const popup = document.createElement("div");
    popup.className = "help-popup";
    popup.setAttribute("role", "tooltip");
    document.body.appendChild(popup);

    let activeTrigger = null;

    /** Position the popup near the trigger button. */
    function positionPopup(trigger) {
        const rect = trigger.getBoundingClientRect();
        const popupWidth = 300;

        /* Place below the trigger, aligned to the right (RTL). */
        let top = rect.bottom + 8;
        let left = rect.right - popupWidth;

        /* Keep inside viewport. */
        if (left < 8) left = 8;
        if (top + 200 > window.innerHeight) {
            top = rect.top - 8;
            popup.style.transform = "translateY(-100%)";
        } else {
            popup.style.transform = "none";
        }

        popup.style.top = top + "px";
        popup.style.left = left + "px";
        popup.style.width = popupWidth + "px";
    }

    /** Show popup for a given trigger. */
    function show(trigger) {
        const text = trigger.getAttribute("data-help");
        if (!text) return;

        popup.textContent = text;
        positionPopup(trigger);
        popup.classList.add("visible");
        activeTrigger = trigger;
    }

    /** Hide the popup. */
    function hide() {
        popup.classList.remove("visible");
        activeTrigger = null;
    }

    /* Delegate click on all .help-trigger buttons. */
    document.addEventListener("click", function (e) {
        const trigger = e.target.closest(".help-trigger");

        if (trigger) {
            e.stopPropagation();
            if (activeTrigger === trigger) {
                hide();
            } else {
                show(trigger);
            }
            return;
        }

        /* Click outside — close popup */
        if (activeTrigger) hide();
    });

    /* Escape to close */
    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && activeTrigger) hide();
    });
})();
