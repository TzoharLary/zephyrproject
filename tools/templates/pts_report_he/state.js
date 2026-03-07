// ============================================================
// state.js — Application constants and mutable state
// Part of the pts_report_he modular JS architecture.
// Load order: 1 of 4 (state → persistence → render → events)
// ============================================================
const DATA = window.REPORT_DATA || {};
const navButtons = Array.from(document.querySelectorAll(".nav-btn"));
const panels = Array.from(document.querySelectorAll(".panel"));
const searchInput = document.getElementById("searchInput");

const BUCKETS = [
  {
    key: "mandatory",
    label: "חובה",
    className: "mandatory",
    explain:
      "פריטים שמוגדרים כחובה בקונפיגורציה הנוכחית ולכן צפויים להשפיע ישירות על סט בדיקות החובה.",
  },
  {
    key: "optional",
    label: "אופציונלי",
    className: "optional",
    explain:
      "פריטים שהתקן מאפשר, אך אינם חובה בקונפיגורציה הזו. במוצרים אחרים או בהגדרות אחרות הם יכולים להפוך לחובה.",
  },
  {
    key: "conditional",
    label: "תלוי-תנאי (Conditional)",
    className: "conditional",
    explain:
      "פריטים שרלוונטיים רק אם מתקיים תנאי מסוים (למשל יכולת פעילה, תפקיד ספציפי או שירות נוסף).",
  },
];

const PROFILE_PANEL_CONFIG = {
  DIS: {
    contentId: "disContent",
    tableKey: "dis",
    tcGroups: [{ key: "dis", title: "בדיקות DIS מתוך TCRL" }],
    icsGroups: [{ key: "DIS", title: "DIS" }],
  },
  BAS: {
    contentId: "basContent",
    tableKey: "bas",
    tcGroups: [{ key: "bas", title: "בדיקות BAS מתוך TCRL" }],
    icsGroups: [{ key: "BAS", title: "BAS" }],
  },
  HRS: {
    contentId: "hrsContent",
    tableKey: "hrs",
    tcGroups: [{ key: "hrs", title: "בדיקות HRS מתוך TCRL" }],
    icsGroups: [{ key: "HRS", title: "HRS" }],
  },
  HID: {
    contentId: "hidContent",
    tableKey: "hid",
    tcGroups: [{ key: "hid", title: "בדיקות HOGP מתוך TCRL" }],
    icsGroups: [{ key: "HOGP", title: "HOGP" }],
  },
};

const MAPPING_VIEW_META = {
  tcid: { label: "TCID-first" },
  tspc: { label: "TSPC-first" },
  builds: { label: "Builds-min" },
};

const overviewState = {
  profile: "DIS",
  bucket: "mandatory",
  expanded: false,
};

const mappingViewState = {
  overview: "tcid",
  profiles: {
    DIS: "tcid",
    BAS: "tcid",
    HRS: "tcid",
    HID: "tcid",
  },
};

const TCID_QUICK_FILTERS = [
  { key: "all", label: "הכל" },
  { key: "mandatory_only", label: "רק חובה" },
  { key: "expected_active", label: "רק צפוי לרוץ" },
  { key: "expected_inactive", label: "בסיכון (לא צפוי לרוץ)" },
  { key: "unmapped", label: "ללא מיפוי" },
];

const tcidQuickFilterState = {
  overview: "all",
  profiles: {
    DIS: "all",
    BAS: "all",
    HRS: "all",
    HID: "all",
  },
};

const runtimePanelState = {
  profile: "ALL",
  snapshotId: "",
};

const comparisonState = {
  status:
    (DATA.comparison && DATA.comparison.default_filter && DATA.comparison.default_filter.status) || "conflict",
  profile:
    (DATA.comparison && DATA.comparison.default_filter && DATA.comparison.default_filter.profile) || "ALL",
  topic: (DATA.comparison && DATA.comparison.default_filter && DATA.comparison.default_filter.topic) || "ALL",
};

const autoPtsPanelState = {
  cliGroup: "ALL",
  cliVisibility: "public",
  cliText: "",
  profileStack: "ALL",
  profileClass: "ALL",
  profileText: "",
};

const RUN_STATUS_STORAGE_KEY = "pts_report_run_status_v1";
const RUN_STATUS_FILE_API_PATH = "api/run-status";
const RUN_STATUS_FILE_FALLBACK_PATH = "data/run-status-state.json";
const RUN_STATUS_SCHEMA_VERSION = 1;
const RUN_STATUS_VALUES = [
  { value: "not_tested", label: "לא נבדק" },
  { value: "pass", label: "עבר" },
  { value: "fail", label: "נכשל" },
];
const RUN_STATUS_OWNERS = ["דוד", "עמית", "רעות", "צהר"];
const RUN_TRACKS = [
  { key: "manual", label: "ידני ב-PTS" },
  { key: "autopts", label: "אוטומטי ב-AutoPTS" },
];

const DRAWER_WIDTH_STORAGE_KEY = "pts_report_glossary_drawer_width";
const DRAWER_MIN_WIDTH = 300;
const DRAWER_MAX_WIDTH_CAP = 920;

let tableIdCounter = 0;
let runStatusState = {}; // populated by persistence.loadRunStatusState() in events.js init
