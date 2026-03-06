// ============================================================
// persistence.js — Run-status persistence and run-entry CRUD
// Part of the pts_report_he modular JS architecture.
// Load order: 2 of 4 (state → persistence → render → events)
// Depends on: state.js (RUN_STATUS_* constants, runStatusState)
// ============================================================
const runStatusPersistenceState = {
  mode: "localStorage",
  fileApiAvailable: false,
  lastError: "",
  saveTimer: null,
  saveInFlight: false,
  pendingSave: false,
};

function esc(str) {
  return String(str ?? "").replace(/[&<>"']/g, (s) =>
    ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[s]
  );
}

function runEntryKey(profileKey, tcid) {
  const profile = String(profileKey || "GLOBAL").trim() || "GLOBAL";
  const test = String(tcid || "").trim();
  return `${profile}::${test}`;
}

function emptyTrackState() {
  return { status: "not_tested", owner: "", reviewer: "" };
}

function normalizeTrackState(track) {
  const normalized = Object.assign({}, emptyTrackState(), track || {});
  if (!RUN_STATUS_VALUES.some((item) => item.value === normalized.status)) normalized.status = "not_tested";
  if (!RUN_STATUS_OWNERS.includes(normalized.owner)) normalized.owner = "";
  if (!RUN_STATUS_OWNERS.includes(normalized.reviewer)) normalized.reviewer = "";
  // Enforce: owner and reviewer must be different people.
  if (normalized.owner && normalized.reviewer && normalized.owner === normalized.reviewer) {
    normalized.reviewer = "";
  }
  return normalized;
}

function normalizeRunEntry(entry) {
  const safe = entry || {};
  return {
    manual: normalizeTrackState(safe.manual),
    autopts: normalizeTrackState(safe.autopts),
  };
}

function loadRunStatusState() {
  try {
    const raw = localStorage.getItem(RUN_STATUS_STORAGE_KEY);
    // Use explicit null/undefined check — falsy check would skip valid but
    // unlikely-but-possible edge cases like "0" stored as a key value.
    if (raw === null || raw === undefined) return {};
    if (raw === "") return {};
    return normalizeRunStatusPayload(JSON.parse(raw)).entries;
  } catch (error) {
    return {};
  }
}

function runStatusPayloadSnapshot() {
  return {
    version: RUN_STATUS_SCHEMA_VERSION,
    updated_at: new Date().toISOString(),
    entries: runStatusState,
  };
}

function normalizeRunStatusPayload(raw) {
  if (!raw || typeof raw !== "object") {
    return { version: RUN_STATUS_SCHEMA_VERSION, updated_at: null, entries: {} };
  }
  const entriesIn = raw.entries && typeof raw.entries === "object" ? raw.entries : {};
  const out = {};
  Object.entries(entriesIn).forEach(([key, value]) => {
    out[String(key)] = normalizeRunEntry(value);
  });
  const version = Number.isFinite(Number(raw.version)) ? Number(raw.version) : RUN_STATUS_SCHEMA_VERSION;
  const updatedAt = raw.updated_at ? String(raw.updated_at) : null;
  return { version, updated_at: updatedAt, entries: out };
}

function persistRunStatusStateLocal() {
  try {
    localStorage.setItem(RUN_STATUS_STORAGE_KEY, JSON.stringify(runStatusPayloadSnapshot()));
  } catch (error) {
    // Ignore localStorage failures in restricted contexts.
  }
}

function applyRunStatusEntries(entries) {
  const next = {};
  Object.entries(entries || {}).forEach(([key, value]) => {
    next[String(key)] = normalizeRunEntry(value);
  });
  runStatusState = next;
}

function syncAllRunControls() {
  const seen = new Set();
  document.querySelectorAll(".run-status-select[data-run-key]").forEach((element) => {
    const key = String(element.getAttribute("data-run-key") || "");
    if (!key || seen.has(key)) return;
    seen.add(key);
    syncRunControls(key);
  });
}

function rerenderRunStatusPanels() {
  rerenderOverviewPanel();
  Object.keys(PROFILE_PANEL_CONFIG).forEach((profileId) => rerenderProfilePanel(profileId));
  rerenderRuntimePanel();
  applySearch();
}

function handleRunStatusLoadedPayload(payload, sourceMode) {
  const normalized = normalizeRunStatusPayload(payload);
  applyRunStatusEntries(normalized.entries);
  persistRunStatusStateLocal();
  runStatusPersistenceState.mode = sourceMode || runStatusPersistenceState.mode;
  if (sourceMode === "file") {
    runStatusPersistenceState.fileApiAvailable = true;
    runStatusPersistenceState.lastError = "";
  }
  syncAllRunControls();
  rerenderRunStatusPanels();
}

async function loadRunStatusStateFromFileApi() {
  const response = await fetch(RUN_STATUS_FILE_API_PATH, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`run-status api GET failed (${response.status})`);
  }
  return await response.json();
}

async function loadRunStatusStateFromFileFallback() {
  const response = await fetch(RUN_STATUS_FILE_FALLBACK_PATH, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    throw new Error(`run-status file GET failed (${response.status})`);
  }
  return await response.json();
}

async function bootstrapRunStatusPersistence() {
  try {
    const payload = await loadRunStatusStateFromFileApi();
    handleRunStatusLoadedPayload(payload, "file");
    return;
  } catch (error) {
    runStatusPersistenceState.lastError = error && error.message ? String(error.message) : "file api unavailable";
  }

  try {
    const payload = await loadRunStatusStateFromFileFallback();
    handleRunStatusLoadedPayload(payload, "file-readonly");
    return;
  } catch (error) {
    // Keep localStorage state as final fallback.
  }

  syncAllRunControls();
}

async function persistRunStatusStateToFile() {
  const payload = runStatusPayloadSnapshot();
  const response = await fetch(RUN_STATUS_FILE_API_PATH, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`run-status api PUT failed (${response.status})`);
  }
  const result = await response.json().catch(() => ({}));
  runStatusPersistenceState.mode = "file";
  runStatusPersistenceState.fileApiAvailable = true;
  runStatusPersistenceState.lastError = "";
  return result;
}

function flushRunStatusStateToFileSoon() {
  if (runStatusPersistenceState.saveInFlight) {
    runStatusPersistenceState.pendingSave = true;
    return;
  }

  runStatusPersistenceState.saveInFlight = true;
  persistRunStatusStateToFile()
    .catch((error) => {
      runStatusPersistenceState.lastError = error && error.message ? String(error.message) : "save failed";
      runStatusPersistenceState.fileApiAvailable = false;
      // Silent fallback: state still persists in localStorage.
      if (window.console && typeof window.console.warn === "function") {
        console.warn("Run-status file persistence unavailable, keeping localStorage fallback.", error);
      }
    })
    .finally(() => {
      runStatusPersistenceState.saveInFlight = false;
      if (runStatusPersistenceState.pendingSave) {
        runStatusPersistenceState.pendingSave = false;
        scheduleRunStatusFilePersist();
      }
    });
}

function scheduleRunStatusFilePersist() {
  if (runStatusPersistenceState.saveTimer) {
    clearTimeout(runStatusPersistenceState.saveTimer);
  }
  runStatusPersistenceState.saveTimer = setTimeout(() => {
    runStatusPersistenceState.saveTimer = null;
    flushRunStatusStateToFileSoon();
  }, 200);
}

function persistRunStatusState() {
  persistRunStatusStateLocal();
  scheduleRunStatusFilePersist();
}

function getRunEntry(profileKey, tcid) {
  const key = runEntryKey(profileKey, tcid);
  if (!runStatusState[key]) runStatusState[key] = normalizeRunEntry({});
  return runStatusState[key];
}

function updateRunEntry(profileKey, tcid, track, field, value) {
  const key = runEntryKey(profileKey, tcid);
  const current = normalizeRunEntry(runStatusState[key]);
  const next = Object.assign({}, current);
  const targetTrack = track === "autopts" ? "autopts" : "manual";
  const normalizedTrack = normalizeTrackState(next[targetTrack]);
  if (field === "status") {
    normalizedTrack.status = RUN_STATUS_VALUES.some((item) => item.value === value) ? value : "not_tested";
  } else if (field === "owner") {
    const candidate = RUN_STATUS_OWNERS.includes(value) ? value : "";
    // Enforce: owner and reviewer must be different people.
    normalizedTrack.owner = candidate && candidate === normalizedTrack.reviewer ? "" : candidate;
  } else if (field === "reviewer") {
    const candidate = RUN_STATUS_OWNERS.includes(value) ? value : "";
    // Enforce: reviewer and owner must be different people.
    normalizedTrack.reviewer = candidate && candidate === normalizedTrack.owner ? "" : candidate;
  }
  next[targetTrack] = normalizedTrack;
  runStatusState[key] = next;
  persistRunStatusState();
}

function syncRunControls(runKey) {
  const entry = normalizeRunEntry(runStatusState[runKey]);
  const selectorKey =
    window.CSS && typeof window.CSS.escape === "function"
      ? window.CSS.escape(runKey)
      : String(runKey || "").replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  document.querySelectorAll(`[data-run-key="${selectorKey}"]`).forEach((element) => {
    const track = element.getAttribute("data-run-track");
    const field = element.getAttribute("data-run-field");
    if (!track || !field) return;
    const value = track === "autopts" ? entry.autopts : entry.manual;
    if (field === "status") element.value = value.status;
    if (field === "owner") element.value = value.owner;
    if (field === "reviewer") element.value = value.reviewer;
  });
}

