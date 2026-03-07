// ============================================================
// events.js — Event binding, panel navigation, and initialization
// Part of the pts_report_he modular JS architecture.
// Load order: 4 of 4 (state → persistence → render → events)
// Depends on: state.js, persistence.js, render.js
// ============================================================
function bindOverviewActions() {
  document.querySelectorAll("[data-ov-profile][data-ov-bucket]").forEach((button) => {
    button.addEventListener("click", () => {
      overviewState.profile = button.getAttribute("data-ov-profile") || overviewState.profile;
      overviewState.bucket = button.getAttribute("data-ov-bucket") || overviewState.bucket;
      overviewState.expanded = false;
      tcidQuickFilterState.overview = "all";
      rerenderOverviewPanel();
    });
  });

  const expandButton = document.getElementById("overviewExpandBtn");
  if (expandButton) {
    expandButton.addEventListener("click", () => {
      overviewState.expanded = !overviewState.expanded;
      rerenderOverviewPanel();
    });
  }
}

function bindComparisonActions() {
  const statusFilter = document.getElementById("comparisonStatusFilter");
  const profileFilter = document.getElementById("comparisonProfileFilter");
  const topicFilter = document.getElementById("comparisonTopicFilter");
  const comparisonRoot = document.getElementById("comparisonContent");
  if (!comparisonRoot) return;

  const rerender = () => {
    comparisonRoot.innerHTML = renderComparisonPanel();
    bindComparisonActions();
    applySearch();
  };

  if (statusFilter) {
    statusFilter.addEventListener("change", () => {
      comparisonState.status = statusFilter.value || "ALL";
      rerender();
    });
  }
  if (profileFilter) {
    profileFilter.addEventListener("change", () => {
      comparisonState.profile = profileFilter.value || "ALL";
      rerender();
    });
  }
  if (topicFilter) {
    topicFilter.addEventListener("change", () => {
      comparisonState.topic = topicFilter.value || "ALL";
      rerender();
    });
  }
}

function bindRuntimeActions() {
  const snapshotFilter = document.getElementById("runtimeSnapshotFilter");
  const profileFilter = document.getElementById("runtimeProfileFilter");
  if (snapshotFilter) {
    snapshotFilter.addEventListener("change", () => {
      runtimePanelState.snapshotId = snapshotFilter.value || "";
      rerenderRuntimePanel();
    });
  }
  if (profileFilter) {
    profileFilter.addEventListener("change", () => {
      runtimePanelState.profile = profileFilter.value || "ALL";
      rerenderRuntimePanel();
    });
  }
}

function bindAutoPtsActions() {
  const cliGroup = document.getElementById("autoptsCliGroupFilter");
  const cliVisibility = document.getElementById("autoptsCliVisibilityFilter");
  const cliText = document.getElementById("autoptsCliTextFilter");
  const profileStack = document.getElementById("autoptsProfileStackFilter");
  const profileClass = document.getElementById("autoptsProfileClassFilter");
  const profileText = document.getElementById("autoptsProfileTextFilter");

  if (cliGroup) {
    cliGroup.addEventListener("change", () => {
      autoPtsPanelState.cliGroup = cliGroup.value || "ALL";
      rerenderAutoPtsPanel();
    });
  }

  if (cliVisibility) {
    cliVisibility.addEventListener("change", () => {
      autoPtsPanelState.cliVisibility = cliVisibility.value || "public";
      rerenderAutoPtsPanel();
    });
  }

  if (cliText) {
    cliText.addEventListener("input", () => {
      autoPtsPanelState.cliText = cliText.value || "";
      rerenderAutoPtsPanel();
    });
  }

  if (profileStack) {
    profileStack.addEventListener("change", () => {
      autoPtsPanelState.profileStack = profileStack.value || "ALL";
      rerenderAutoPtsPanel();
    });
  }

  if (profileClass) {
    profileClass.addEventListener("change", () => {
      autoPtsPanelState.profileClass = profileClass.value || "ALL";
      rerenderAutoPtsPanel();
    });
  }

  if (profileText) {
    profileText.addEventListener("input", () => {
      autoPtsPanelState.profileText = profileText.value || "";
      rerenderAutoPtsPanel();
    });
  }

  document.querySelectorAll("[data-autopts-jump]").forEach((link) => {
    link.addEventListener("click", (event) => {
      const id = link.getAttribute("data-autopts-jump");
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      if (history && history.replaceState) {
        history.replaceState(null, "", `#${id}`);
      }
    });
  });
}

function getActivePanel() {
  return document.querySelector(".panel.active");
}

function applySearch() {
  const panel = getActivePanel();
  if (!panel) return;
  const query = String(searchInput && searchInput.value ? searchInput.value : "").trim().toLowerCase();
  panel.querySelectorAll("[data-searchable]").forEach((element) => {
    const explicit = String(element.getAttribute("data-search-text") || "").toLowerCase();
    const text = explicit || String(element.innerText || "").toLowerCase();
    const isMatch = !query || text.includes(query);
    element.style.display = isMatch ? "" : "none";
  });
}

function activatePanel(id) {
  panels.forEach((panel) => {
    const isActive = panel.id === `panel-${id}`;
    panel.classList.toggle("active", isActive);
    panel.setAttribute("aria-hidden", isActive ? "false" : "true");
  });
  navButtons.forEach((button) => {
    const isActive = button.dataset.panelTarget === id;
    button.classList.toggle("active", isActive);
    button.setAttribute("aria-pressed", isActive ? "true" : "false");
  });
  applySearch();

  document.body.classList.remove("nav-open");
  const overlay = document.getElementById("overlay");
  if (overlay) overlay.classList.remove("active");

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function openGlossaryDrawer() {
  const drawer = document.getElementById("glossaryDrawer");
  const overlay = document.getElementById("glossaryOverlay");
  const trigger = document.getElementById("openGlossaryDrawer");
  if (drawer) drawer.setAttribute("aria-hidden", "false");
  if (overlay) overlay.classList.add("active");
  if (trigger) trigger.setAttribute("aria-expanded", "true");
  document.body.classList.add("glossary-open");
}

function closeGlossaryDrawer() {
  const drawer = document.getElementById("glossaryDrawer");
  const overlay = document.getElementById("glossaryOverlay");
  const trigger = document.getElementById("openGlossaryDrawer");
  if (drawer) drawer.setAttribute("aria-hidden", "true");
  if (overlay) overlay.classList.remove("active");
  if (trigger) trigger.setAttribute("aria-expanded", "false");
  document.body.classList.remove("glossary-open");
}

function drawerMaxWidth() {
  return Math.max(DRAWER_MIN_WIDTH, Math.min(DRAWER_MAX_WIDTH_CAP, window.innerWidth - 24));
}

function clampDrawerWidth(width) {
  if (!Number.isFinite(width)) return 430;
  return Math.max(DRAWER_MIN_WIDTH, Math.min(drawerMaxWidth(), width));
}

function applyGlossaryDrawerWidth(width, persist) {
  const clamped = Math.round(clampDrawerWidth(width));
  document.documentElement.style.setProperty("--glossary-drawer-width", `${clamped}px`);

  const range = document.getElementById("glossaryDrawerWidthRange");
  if (range) range.value = String(clamped);

  const out = document.getElementById("glossaryDrawerWidthValue");
  if (out) out.textContent = `${clamped}px`;

  if (persist) {
    try {
      localStorage.setItem(DRAWER_WIDTH_STORAGE_KEY, String(clamped));
    } catch (error) {
      // Ignore localStorage failures in restricted contexts.
    }
  }
}

function initGlossaryDrawerWidthControls() {
  const range = document.getElementById("glossaryDrawerWidthRange");
  const drawer = document.getElementById("glossaryDrawer");
  const resizer = document.getElementById("glossaryDrawerResizer");

  let initial = 430;
  try {
    const saved = Number(localStorage.getItem(DRAWER_WIDTH_STORAGE_KEY));
    if (Number.isFinite(saved)) initial = saved;
  } catch (error) {
    // Ignore localStorage failures in restricted contexts.
  }
  applyGlossaryDrawerWidth(initial, false);

  if (range) {
    range.max = String(drawerMaxWidth());
    range.addEventListener("input", () => {
      applyGlossaryDrawerWidth(Number(range.value), true);
    });
  }

  if (resizer && drawer) {
    let dragState = null;

    const onMove = (event) => {
      if (!dragState) return;
      const next = dragState.startWidth + (event.clientX - dragState.startX);
      applyGlossaryDrawerWidth(next, true);
    };

    const onUp = () => {
      if (!dragState) return;
      dragState = null;
      document.body.style.userSelect = "";
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
    };

    resizer.addEventListener("pointerdown", (event) => {
      dragState = {
        startX: event.clientX,
        startWidth: drawer.getBoundingClientRect().width,
      };
      document.body.style.userSelect = "none";
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
      window.addEventListener("pointercancel", onUp);
    });
  }

  window.addEventListener("resize", () => {
    if (range) range.max = String(drawerMaxWidth());
    const current = Number.parseInt(
      getComputedStyle(document.documentElement).getPropertyValue("--glossary-drawer-width"),
      10
    );
    applyGlossaryDrawerWidth(Number.isFinite(current) ? current : 430, false);
  });
}

function bindGlobalEvents() {
  navButtons.forEach((button) => {
    button.addEventListener("click", () => activatePanel(button.dataset.panelTarget));
  });

  if (searchInput) searchInput.addEventListener("input", applySearch);

  const clearSearchBtn = document.getElementById("clearSearchBtn");
  if (clearSearchBtn) {
    clearSearchBtn.addEventListener("click", () => {
      if (searchInput) searchInput.value = "";
      applySearch();
      if (searchInput) searchInput.focus();
    });
  }

  document.addEventListener("click", (event) => {
    const quickFilterBtn = event.target && event.target.closest ? event.target.closest(".tcid-qf-btn") : null;
    if (quickFilterBtn) {
      const scope = quickFilterBtn.getAttribute("data-tcid-scope");
      const filterKey = quickFilterBtn.getAttribute("data-tcid-filter");
      if (!scope || !filterKey) return;
      setQuickFilterForScope(scope, filterKey);
      if (scope === "overview") {
        rerenderOverviewPanel();
      } else if (PROFILE_PANEL_CONFIG[scope]) {
        rerenderProfilePanel(scope);
      }
      return;
    }

    const enToggle = event.target && event.target.closest ? event.target.closest(".what-tested-en-toggle") : null;
    if (enToggle) {
      const targetId = enToggle.getAttribute("data-target");
      if (!targetId) return;
      const panel = document.getElementById(targetId);
      if (!panel) return;
      const isOpen = !panel.hasAttribute("hidden");
      if (isOpen) {
        panel.setAttribute("hidden", "");
        enToggle.setAttribute("aria-expanded", "false");
      } else {
        panel.removeAttribute("hidden");
        enToggle.setAttribute("aria-expanded", "true");
      }
      return;
    }

    const viewBtn = event.target && event.target.closest ? event.target.closest(".mapping-view-btn") : null;
    if (viewBtn) {
      const scope = viewBtn.getAttribute("data-mapping-scope");
      const view = viewBtn.getAttribute("data-mapping-view");
      if (!scope || !view) return;

      if (scope === "overview") {
        if (view !== "tcid" && view !== "tspc") return;
        mappingViewState.overview = view;
        overviewState.expanded = false;
        rerenderOverviewPanel();
        return;
      }

      if (PROFILE_PANEL_CONFIG[scope]) {
        if (view !== "tcid" && view !== "tspc" && view !== "builds") return;
        mappingViewState.profiles[scope] = view;
        rerenderProfilePanel(scope);
      }
      return;
    }

    const button = event.target && event.target.closest ? event.target.closest(".toggle-col-help") : null;
    if (!button) return;

    const tableId = button.getAttribute("data-table-id");
    if (!tableId) return;

    const table = document.getElementById(tableId);
    if (!table) return;

    const helpRow = table.querySelector(".col-help-row");
    if (!helpRow) return;

    const currentlyOpen = !helpRow.hasAttribute("hidden");
    if (currentlyOpen) {
      helpRow.setAttribute("hidden", "");
      button.setAttribute("aria-expanded", "false");
      button.textContent = "הצג הסבר לעמודות הטבלה";
      return;
    }

    helpRow.removeAttribute("hidden");
    button.setAttribute("aria-expanded", "true");
    button.textContent = "הסתר הסבר עמודות";
  });

  document.addEventListener("change", (event) => {
    const control = event.target && event.target.closest ? event.target.closest(".run-status-select") : null;
    if (!control) return;

    const runKey = control.getAttribute("data-run-key");
    const track = control.getAttribute("data-run-track");
    const field = control.getAttribute("data-run-field");
    if (!runKey || !track || !field) return;

    const [profileKey, ...tcidParts] = runKey.split("::");
    const tcid = tcidParts.join("::");
    updateRunEntry(profileKey, tcid, track, field, control.value || "");
    syncRunControls(runKey);
    // When owner changes, rebuild the reviewer dropdown for this widget
    // to exclude the newly selected owner from the available reviewer options.
    if (field === "owner") {
      const widget = control.closest(".tcid-run-widget");
      if (widget) {
        widget.querySelectorAll(`[data-run-track="${CSS.escape ? CSS.escape(track) : track}"][data-run-field="reviewer"]`).forEach((reviewerSelect) => {
          const currentReviewer = reviewerSelect.value;
          const currentOwner = control.value || "";
          reviewerSelect.innerHTML = renderReviewerOptions(currentReviewer, currentOwner);
        });
      }
    }
  });

  const openSourcesBtn = document.getElementById("openSourcesBtn");
  if (openSourcesBtn) {
    openSourcesBtn.addEventListener("click", () => {
      const panel = getActivePanel();
      if (!panel) return;
      panel.querySelectorAll(".src-details").forEach((details) => {
        details.open = true;
      });
    });
  }

  const closeSourcesBtn = document.getElementById("closeSourcesBtn");
  if (closeSourcesBtn) {
    closeSourcesBtn.addEventListener("click", () => {
      const panel = getActivePanel();
      if (!panel) return;
      panel.querySelectorAll(".src-details").forEach((details) => {
        details.open = false;
      });
    });
  }

  const toggleNav = document.getElementById("toggleNav");
  if (toggleNav) {
    toggleNav.addEventListener("click", () => {
      document.body.classList.toggle("nav-open");
      const overlay = document.getElementById("overlay");
      if (overlay) overlay.classList.toggle("active");
    });
  }

  const overlay = document.getElementById("overlay");
  if (overlay) {
    overlay.addEventListener("click", () => {
      document.body.classList.remove("nav-open");
      overlay.classList.remove("active");
    });
  }

  const openGlossaryBtn = document.getElementById("openGlossaryDrawer");
  if (openGlossaryBtn) {
    openGlossaryBtn.addEventListener("click", () => {
      if (document.body.classList.contains("glossary-open")) {
        closeGlossaryDrawer();
        return;
      }
      openGlossaryDrawer();
    });
  }

  const closeGlossaryBtn = document.getElementById("closeGlossaryDrawer");
  if (closeGlossaryBtn) {
    closeGlossaryBtn.addEventListener("click", () => closeGlossaryDrawer());
  }

  const glossaryOverlay = document.getElementById("glossaryOverlay");
  if (glossaryOverlay) {
    glossaryOverlay.addEventListener("click", () => closeGlossaryDrawer());
  }

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.body.classList.contains("glossary-open")) {
      closeGlossaryDrawer();
    }
  });
}

// Load persisted run-status state before rendering panels.
runStatusState = loadRunStatusState();
fillPanels();
bindGlobalEvents();
initGlossaryDrawerWidthControls();
activatePanel("overview");
bootstrapRunStatusPersistence();
