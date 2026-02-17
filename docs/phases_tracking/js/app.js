/**
 * app.js — Core application logic.
 *
 * Responsibilities:
 *   - Tab switching
 *   - Phase guide navigation
 *   - localStorage persistence for editable fields & status selects
 *   - Export & clear data
 */

(function () {
    "use strict";

    /* ============================================================
       Constants
       ============================================================ */
    var STORAGE_KEY = "ble_pts_tracking_data";

    /* ============================================================
       Tab Switching
       ============================================================ */

    function switchTab(tabName) {
        document.querySelectorAll(".tab-btn").forEach(function (b) {
            b.classList.remove("active");
        });
        document.querySelectorAll(".tab-pane").forEach(function (p) {
            p.classList.remove("active");
        });

        var btn = document.querySelector('[data-tab="' + tabName + '"]');
        var pane = document.getElementById(tabName);
        if (btn) btn.classList.add("active");
        if (pane) pane.classList.add("active");
    }

    function switchSubTab(subTabName) {
        document.querySelectorAll(".sub-tab-btn").forEach(function (b) {
            b.classList.remove("active");
        });
        document.querySelectorAll(".sub-tab-pane").forEach(function (p) {
            p.classList.remove("active");
        });

        var btn = document.querySelector('[data-subtab="' + subTabName + '"]');
        var pane = document.getElementById(subTabName);
        if (btn) btn.classList.add("active");
        if (pane) pane.classList.add("active");
    }

    function initTabs() {
        var buttons = document.querySelectorAll(".tab-btn");
        for (var i = 0; i < buttons.length; i++) {
            buttons[i].addEventListener("click", function (e) {
                e.preventDefault();
                var target = this.getAttribute("data-tab");
                switchTab(target);
            });
        }

        var subButtons = document.querySelectorAll(".sub-tab-btn");
        for (var j = 0; j < subButtons.length; j++) {
            subButtons[j].addEventListener("click", function (e) {
                e.preventDefault();
                var target = this.getAttribute("data-subtab");
                switchSubTab(target);
            });
        }
    }

    /* ============================================================
       Guide — Phase Sidebar Navigation
       ============================================================ */

    function initGuide() {
        var items = document.querySelectorAll(".guide-nav-item");
        items.forEach(function (item) {
            item.addEventListener("click", function () {
                var phase = item.getAttribute("data-phase");
                switchPhase(phase);
            });
        });
    }

    function switchPhase(id) {
        document.querySelectorAll(".guide-phase").forEach(function (el) {
            el.classList.remove("active");
        });
        document.querySelectorAll(".guide-nav-item").forEach(function (el) {
            el.classList.remove("active");
        });

        var phaseEl = document.getElementById("phase-" + id);
        if (phaseEl) phaseEl.classList.add("active");

        var navItem = document.querySelector('.guide-nav-item[data-phase="' + id + '"]');
        if (navItem) navItem.classList.add("active");
    }

    /* ============================================================
       Data Persistence (localStorage)
       ============================================================ */

    function getData() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
        } catch (_) {
            return {};
        }
    }

    function saveField(element) {
        var profile = element.getAttribute("data-profile");
        var field = element.getAttribute("data-field");
        if (!profile || !field) return;

        var value =
            element.tagName === "SELECT"
                ? element.value
                : (element.textContent || "").trim();

        var data = getData();
        if (!data[profile]) data[profile] = {};
        data[profile][field] = value;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(data));

        showToast();

        if (element.classList.contains("editable")) {
            element.classList.add("saved");
            setTimeout(function () {
                element.classList.remove("saved");
            }, 900);
        }
    }

    function loadData() {
        var data = getData();

        document.querySelectorAll(".editable").forEach(function (el) {
            var p = el.getAttribute("data-profile");
            var f = el.getAttribute("data-field");
            if (data[p] && data[p][f]) el.textContent = data[p][f];
        });

        document.querySelectorAll(".status-select").forEach(function (el) {
            var p = el.getAttribute("data-profile");
            var f = el.getAttribute("data-field");
            if (data[p] && data[p][f]) el.value = data[p][f];
        });
    }

    /* ============================================================
       Toast (Save Indicator)
       ============================================================ */

    var toastTimer;

    function showToast() {
        var el = document.getElementById("saveToast");
        if (!el) return;
        clearTimeout(toastTimer);
        el.classList.add("show");
        toastTimer = setTimeout(function () {
            el.classList.remove("show");
        }, 1800);
    }

    /* ============================================================
       Export & Clear
       ============================================================ */

    function exportData() {
        var raw = localStorage.getItem(STORAGE_KEY) || "{}";
        var blob = new Blob([raw], { type: "application/json" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "ble_pts_tracking_data.json";
        a.click();
        URL.revokeObjectURL(url);
    }

    function clearData() {
        if (confirm("למחוק את כל הנתונים שהוזנו? לא ניתן לשחזר.")) {
            localStorage.removeItem(STORAGE_KEY);
            location.reload();
        }
    }

    /* ============================================================
       Init
       ============================================================ */

    function bindDataEvents() {
        document.querySelectorAll(".editable").forEach(function (el) {
            el.addEventListener("blur", function () {
                saveField(el);
            });
        });

        document.querySelectorAll(".status-select").forEach(function (el) {
            el.addEventListener("change", function () {
                saveField(el);
            });
        });
    }

    document.addEventListener("DOMContentLoaded", function () {
        initTabs();
        initGuide();
        bindDataEvents();
        loadData();

        /* Expose export/clear to the buttons (onclick in HTML) */
        var exportBtn = document.getElementById("btnExport");
        var clearBtn = document.getElementById("btnClear");
        if (exportBtn) exportBtn.addEventListener("click", exportData);
        if (clearBtn) clearBtn.addEventListener("click", clearData);
    });
})();
