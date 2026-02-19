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

const RUN_STATUS_STORAGE_KEY = "pts_report_run_status_v1";
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
const runStatusState = loadRunStatusState();

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
  return { status: "not_tested", owner: "" };
}

function normalizeTrackState(track) {
  const normalized = Object.assign({}, emptyTrackState(), track || {});
  if (!RUN_STATUS_VALUES.some((item) => item.value === normalized.status)) normalized.status = "not_tested";
  if (!RUN_STATUS_OWNERS.includes(normalized.owner)) normalized.owner = "";
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
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== "object" || !parsed.entries || typeof parsed.entries !== "object") return {};
    const out = {};
    Object.entries(parsed.entries).forEach(([key, value]) => {
      out[String(key)] = normalizeRunEntry(value);
    });
    return out;
  } catch (error) {
    return {};
  }
}

function persistRunStatusState() {
  try {
    localStorage.setItem(
      RUN_STATUS_STORAGE_KEY,
      JSON.stringify({
        version: 1,
        updated_at: new Date().toISOString(),
        entries: runStatusState,
      })
    );
  } catch (error) {
    // Ignore localStorage failures in restricted contexts.
  }
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
    normalizedTrack.owner = RUN_STATUS_OWNERS.includes(value) ? value : "";
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
  });
}

function glossary(term) {
  return (DATA.glossary && DATA.glossary[term]) || "";
}

function profileById(profileId) {
  return (DATA.profiles_overview || []).find((p) => p.id === profileId);
}

function termChip(term, label) {
  const tip = glossary(term) || label || term;
  return `<span class="term-chip" title="${esc(tip)}">${esc(label || term)}</span>`;
}

function sourceRef(source) {
  if (!source || !source.file) return "";
  const line = source.line == null ? "" : `:${source.line}`;
  return `<code>${esc(`${source.file}${line}`)}</code>`;
}

function renderSourceItem(source) {
  if (!source || !source.file) return "";
  const parts = [sourceRef(source)];
  if (source.sheet) parts.push(`<span class="ltr"><code>sheet:${esc(source.sheet)}</code></span>`);
  if (source.row != null) parts.push(`<span class="ltr"><code>row:${esc(source.row)}</code></span>`);
  if (source.columns) parts.push(`<span class="ltr"><code>cols:${esc(source.columns)}</code></span>`);
  if (source.field_path) parts.push(`<span class="ltr"><code>field:${esc(source.field_path)}</code></span>`);
  if (source.note) parts.push(`<span>${esc(source.note)}</span>`);
  return parts.join(" · ");
}

function sourceDetails(items, label = "הצג מקור מדויק") {
  const safe = (items || []).filter((item) => item && item.file);
  if (!safe.length) return '<span class="muted">אין מקור זמין</span>';
  const body = safe.map((item) => `<li>${renderSourceItem(item)}</li>`).join("");
  return `<details class="src-details"><summary>${esc(label)}</summary><ul class="src-list">${body}</ul></details>`;
}

function columnHead(label, key, technicalName) {
  const technical = technicalName ? `<span class="col-tech">${esc(technicalName)}</span>` : "";
  return `
    <span class="col-head">
      <span>${esc(label)}</span>
      ${technical}
    </span>
  `;
}

function nextTableId(prefix) {
  tableIdCounter += 1;
  return `${prefix}-${tableIdCounter}`;
}

function columnHelpRow(columns) {
  const cells = columns
    .map((col) => {
      const help = (DATA.column_help && DATA.column_help[col.key]) || "אין הסבר זמין לעמודה זו.";
      return `<th><div class="col-help-cell">${esc(help)}</div></th>`;
    })
    .join("");
  return `<tr class="col-help-row" hidden>${cells}</tr>`;
}

function columnHelpToggle(tableId) {
  return `
    <button
      type="button"
      class="toggle-col-help"
      data-table-id="${esc(tableId)}"
      aria-expanded="false"
    >הצג הסבר לעמודות הטבלה</button>
  `;
}

function splitMandatoryOptionalConditional(rows) {
  const mandatory = [];
  const optional = [];
  const conditional = [];
  (rows || []).forEach((row) => {
    if (row.mandatory === "TRUE") {
      mandatory.push(row);
      return;
    }
    if ((row.status || "").startsWith("O")) {
      optional.push(row);
      return;
    }
    conditional.push(row);
  });
  return { mandatory, optional, conditional };
}

function getSummaryEntry(profile) {
  return (DATA.summary || []).find((entry) => entry.profile === profile);
}

function bucketMeta(key) {
  return BUCKETS.find((bucket) => bucket.key === key) || BUCKETS[0];
}

function profileCounts(summaryEntry) {
  return {
    mandatory: (summaryEntry.mandatory || []).length,
    optional: (summaryEntry.optional || []).length,
    conditional: (summaryEntry.conditional || []).length,
  };
}

function valuePill(value) {
  const normalized = String(value || "").toUpperCase();
  if (normalized === "TRUE") return '<span class="pill mandatory">TRUE</span>';
  if (normalized === "FALSE") return '<span class="pill conditional">FALSE</span>';
  return `<span class="pill">${esc(value || "-")}</span>`;
}

function mandatoryPill(value) {
  const normalized = String(value || "").toUpperCase();
  if (normalized === "TRUE") return '<span class="pill mandatory">חובה</span>';
  if (normalized === "FALSE") return '<span class="pill optional">לא חובה</span>';
  return `<span class="pill">${esc(value || "-")}</span>`;
}

function buildItemSources(item) {
  const sources = [];
  if (item && item.source && item.source.file) {
    if (item.source.name_line != null) {
      sources.push({
        file: item.source.file,
        line: item.source.name_line,
        note: "שורת מזהה בקובץ ה-Workspace",
      });
    }
    if (item.source.desc_line != null) {
      sources.push({
        file: item.source.file,
        line: item.source.desc_line,
        note: "שורת תיאור בקובץ ה-Workspace",
      });
    }
  }
  if (item && item.ics_doc_key) {
    const icsFile = (DATA.meta && DATA.meta.ics_files && DATA.meta.ics_files[item.ics_doc_key]) || item.ics_doc_key;
    sources.push({
      file: icsFile,
      line: item.ics_line,
      note: `התאמה למסמך ICS (${item.ics_doc_key})`,
    });
  }
  return sources;
}

function profileMappingRows(profileId) {
  return (DATA.mapping && DATA.mapping[profileId] && DATA.mapping[profileId].rows) || [];
}

function profileTsExtract(profileId) {
  return (DATA.ts_extracted && DATA.ts_extracted[profileId]) || {};
}

function profileMappingSummary(profileId) {
  return (DATA.mapping_summary && DATA.mapping_summary[profileId]) || {};
}

function profileTcs(profileId) {
  const key = String(profileId || "").toLowerCase();
  return (DATA.tcs && DATA.tcs[key]) || [];
}

function runtimeSnapshot() {
  return DATA.runtime_active || {};
}

function runtimeSnapshotAvailable() {
  return !!runtimeSnapshot().available;
}

function runtimeHistoryEntries() {
  const entries = Array.isArray(DATA.runtime_active_history) ? DATA.runtime_active_history : [];
  if (entries.length) return entries;
  const single = runtimeSnapshot();
  return single && Object.keys(single).length ? [single] : [];
}

function runtimeSnapshotUiId(entry, index) {
  return String(
    (entry && entry.id) || `${index}:${entry && entry.file ? entry.file : "snapshot"}:${entry && entry.generated_at ? entry.generated_at : ""}`
  );
}

function runtimePanelSelectedSnapshot() {
  const entries = runtimeHistoryEntries();
  if (!entries.length) return runtimeSnapshot();

  const targetId = runtimePanelState.snapshotId || "";
  const selected = entries.find((entry, index) => runtimeSnapshotUiId(entry, index) === targetId);
  if (selected) return selected;

  const first = entries[0];
  runtimePanelState.snapshotId = runtimeSnapshotUiId(first, 0);
  return first;
}

function runtimeProfileEntry(profileId, runtimeInput) {
  const runtime = runtimeInput || runtimeSnapshot();
  if (!runtime || !runtime.profiles) return null;
  return runtime.profiles[profileId] || null;
}

function runtimeActiveSet(profileId) {
  const profile = runtimeProfileEntry(profileId);
  const tcids = (profile && profile.active_tcids) || [];
  return new Set((tcids || []).filter((item) => typeof item === "string"));
}

function runtimeProfileCount(profileId, runtimeInput) {
  const profile = runtimeProfileEntry(profileId, runtimeInput);
  if (!profile) return 0;
  if (typeof profile.count === "number") return profile.count;
  const tcids = (profile && profile.active_tcids) || [];
  return (tcids || []).length;
}

function runtimeProfileTcids(profileId, runtimeInput) {
  const profile = runtimeProfileEntry(profileId, runtimeInput);
  const tcids = (profile && profile.active_tcids) || [];
  return (tcids || []).filter((item) => typeof item === "string").sort((a, b) => a.localeCompare(b));
}

function formatExactRuntimeTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${date.toISOString()} | מקומי: ${date.toLocaleString("he-IL")}`;
}

function confidenceRank(confidence) {
  const raw = String(confidence || "").toLowerCase();
  if (raw === "high") return 3;
  if (raw === "medium") return 2;
  if (raw === "low") return 1;
  return 0;
}

function conditionHintFromCondition(condition) {
  if (condition && condition.condition_hint) return condition.condition_hint;
  const value = String((condition && condition.value) || "").toUpperCase();
  const mandatory = String((condition && condition.mandatory) || "").toUpperCase();
  const status = String((condition && condition.tspc_status) || "").toUpperCase();
  const bucket = (condition && condition.bucket) || "";
  if (value !== "TRUE") return "inactive";
  if (mandatory === "TRUE") return "active_required";
  if (bucket === "conditional" || status.startsWith("C")) return "conditional";
  return "active_optional";
}

function runtimeSignalFromConditionSet(conditions) {
  const safe = (conditions || []).filter(Boolean);
  if (!safe.length) return "unknown";
  const hints = new Set(safe.map((condition) => conditionHintFromCondition(condition)));
  if (hints.has("active_required")) return "likely_active_mandatory";
  if (hints.has("active_optional") || hints.has("conditional")) return "likely_active_optional";
  if (hints.size === 1 && hints.has("inactive")) return "likely_inactive";
  return "unknown";
}

function conditionHintLabel(hint) {
  if (hint === "active_required") return "Active Required";
  if (hint === "active_optional") return "Active Optional";
  if (hint === "conditional") return "Conditional";
  if (hint === "inactive") return "Inactive";
  return "Unknown";
}

function boolMeaning(value, whenTrue, whenFalse, whenUnknown) {
  const normalized = String(value || "").toUpperCase();
  if (normalized === "TRUE") return whenTrue;
  if (normalized === "FALSE") return whenFalse;
  return whenUnknown;
}

function tspcStatusMeaning(status) {
  const normalized = String(status || "").toUpperCase();
  if (normalized.startsWith("M")) return "מוגדרת כחובה לפי התקן";
  if (normalized.startsWith("O")) return "מוגדרת כאופציונלית לפי התקן";
  if (normalized.startsWith("C")) return "מוגדרת כתלויה-תנאי לפי התקן";
  return "";
}

function conditionPracticalMeaning(hint) {
  if (hint === "active_required") return "במצב הזה הטסט צפוי להיות פעיל כחובה.";
  if (hint === "active_optional") return "במצב הזה הטסט יכול להיות פעיל, בהתאם להגדרות הפרופיל.";
  if (hint === "conditional") return "הטסט תלוי בתנאים נוספים מעבר לערך הזה.";
  if (hint === "inactive") return "במצב הזה הטסט לרוב לא ירוץ כי התנאי כבוי.";
  return "לא ניתן להסיק הפעלה ודאית רק מהתנאי הזה.";
}

function conditionPlainText(condition) {
  if (condition && condition.plain_condition_he) return condition.plain_condition_he;
  const capability = (condition && condition.tspc_capability) || (condition && condition.tspc_name) || "יכולת לא מזוהה";
  const valueMeaning = boolMeaning(condition && condition.value, "מופעלת", "כבויה", "ללא ערך ברור");
  const mandatoryMeaning = boolMeaning(
    condition && condition.mandatory,
    "מסומנת כחובה",
    "לא מסומנת כחובה",
    "ללא סימון חובה ברור"
  );
  const statusMeaning = tspcStatusMeaning(condition && condition.tspc_status);
  const hint = conditionHintFromCondition(condition);
  const tail = statusMeaning ? `${mandatoryMeaning}, ${statusMeaning}` : mandatoryMeaning;
  const tcmtFeature = condition && condition.tcmt_feature ? `כותרת היכולת ב-TS: ${condition.tcmt_feature}. ` : "";
  const evalResult = condition && condition.expression_eval && condition.expression_eval.result;
  let evalMeaning = "";
  if (evalResult === "true") evalMeaning = "לפי ערכי ההגדרות הנוכחיים, התנאי הלוגי מתקיים.";
  else if (evalResult === "false") evalMeaning = "לפי ערכי ההגדרות הנוכחיים, התנאי הלוגי לא מתקיים.";
  else if (evalResult === "unknown") evalMeaning = "לא ניתן להכריע את התנאי הלוגי רק מהנתונים הקיימים.";
  return `${tcmtFeature}${capability}: ${valueMeaning}, ${tail}. ${conditionPracticalMeaning(hint)} ${evalMeaning}`.trim();
}

function runtimeSignalLabel(signal) {
  if (signal === "likely_active_mandatory") return "צפוי לפעול כחובה";
  if (signal === "likely_active_optional") return "צפוי לפעול כאופציונלי";
  if (signal === "likely_inactive") return "צפוי להיות לא פעיל";
  return "לא ידוע";
}

function runtimeSignalClass(signal) {
  if (signal === "likely_active_mandatory") return "mandatory";
  if (signal === "likely_active_optional") return "optional";
  if (signal === "likely_inactive") return "conditional";
  return "";
}

function runtimeSignalPill(signal) {
  const normalized = signal || "unknown";
  return `<span class="pill ${runtimeSignalClass(normalized)}">${esc(runtimeSignalLabel(normalized))}</span>`;
}

function bestConfidence(conditions) {
  let best = "Unmapped";
  (conditions || []).forEach((condition) => {
    const next = condition && condition.confidence ? condition.confidence : "Unmapped";
    if (confidenceRank(next) > confidenceRank(best)) best = next;
  });
  return best;
}

function normalizeConditionFromLegacy(mapRow, mapped) {
  const condition = {
    map_id: mapRow.map_id,
    bucket: mapRow.bucket,
    tspc_name: mapRow.tspc_name,
    tspc_item: mapRow.tspc_item,
    tspc_capability: mapRow.tspc_capability,
    tspc_status: mapRow.tspc_status,
    mandatory: mapRow.mandatory,
    value: mapRow.value,
    confidence: (mapped && mapped.confidence) || mapRow.confidence || "Unmapped",
    score: mapped && mapped.score,
    mapping_source: (mapped && mapped.mapping_source) || mapRow.mapping_source || "legacy",
    item_expression: mapped && mapped.item_expression,
    expression_eval: mapped && mapped.expression_eval,
    tcmt_feature: mapped && mapped.tcmt_feature,
    tcmt_features: (mapped && mapped.tcmt_features) || [],
    tspc_evidence: mapRow.evidence || [],
    relation_evidence: (mapped && mapped.evidence) || [],
  };
  condition.condition_hint = conditionHintFromCondition(condition);
  return condition;
}

function deriveTcidRowsFromLegacy(profileId) {
  const mappingRows = profileMappingRows(profileId);
  const tcRows = profileTcs(profileId);
  const rowsByTcid = new Map();

  (tcRows || []).forEach((tc) => {
    if (!tc || !tc.tcid) return;
    rowsByTcid.set(tc.tcid, {
      tcid: tc.tcid,
      desc: tc.desc || "",
      category: tc.category || "",
      active_date: tc.active_date || "",
      ts_title: tc.ts_title || "",
      ts_title_source: tc.ts_title_source || {},
      source: tc.source || {},
      best_confidence: "Unmapped",
      runtime_active: null,
      runtime_signal: "unknown",
      bucket_flags: { mandatory: false, optional: false, conditional: false },
      condition_count: 0,
      active_conditions_count: 0,
      inactive_conditions_count: 0,
      tcmt_features: [],
      conditions: [],
      unmapped_note: "TCID זה נמצא ב-TCRL אך ללא תנאים משויכים ממיפוי TSPC הנוכחי.",
    });
  });

  (mappingRows || []).forEach((mapRow) => {
    (mapRow.mapped_tcids || []).forEach((mapped) => {
      const tcid = mapped && mapped.tcid;
      if (!tcid) return;

      if (!rowsByTcid.has(tcid)) {
        rowsByTcid.set(tcid, {
          tcid,
          desc: mapped.desc || "",
          category: mapped.category || "",
          active_date: mapped.active_date || "",
          ts_title: mapped.ts_title || "",
          ts_title_source: mapped.ts_title_source || {},
          source:
            ((mapped.evidence || [])[0] && (mapped.evidence[0].official_source || {})) ||
            {},
          best_confidence: "Unmapped",
          runtime_active: null,
          runtime_signal: "unknown",
          bucket_flags: { mandatory: false, optional: false, conditional: false },
          condition_count: 0,
          active_conditions_count: 0,
          inactive_conditions_count: 0,
          tcmt_features: [],
          conditions: [],
          unmapped_note: null,
        });
      }

      const row = rowsByTcid.get(tcid);
      const condition = normalizeConditionFromLegacy(mapRow, mapped);
      row.conditions.push(condition);
      if (condition.tcmt_feature && !row.tcmt_features.includes(condition.tcmt_feature)) {
        row.tcmt_features.push(condition.tcmt_feature);
      }
      row.condition_count += 1;
      row.bucket_flags[condition.bucket || "optional"] = true;
      if (condition.condition_hint === "inactive") {
        row.inactive_conditions_count += 1;
      } else {
        row.active_conditions_count += 1;
      }
      row.unmapped_note = null;
    });
  });

  const rows = Array.from(rowsByTcid.values()).map((row) => {
    row.conditions.sort((a, b) => {
      const confDiff = confidenceRank(b.confidence) - confidenceRank(a.confidence);
      if (confDiff) return confDiff;
      const aScore = typeof a.score === "number" ? a.score : -1;
      const bScore = typeof b.score === "number" ? b.score : -1;
      if (bScore !== aScore) return bScore - aScore;
      return String(a.tspc_name || "").localeCompare(String(b.tspc_name || ""));
    });
    row.best_confidence = bestConfidence(row.conditions);
    row.runtime_signal = runtimeSignalFromConditionSet(row.conditions);
    if (!row.condition_count && !row.unmapped_note) {
      row.unmapped_note = "לא נמצאו תנאים משויכים ל-TCID זה מתוך מיפוי TSPC↔TCID.";
    }
    return row;
  });

  rows.sort((a, b) => String(a.tcid || "").localeCompare(String(b.tcid || "")));
  return rows;
}

function profileTcidRows(profileId) {
  const explicit =
    (DATA.mapping_tcid && DATA.mapping_tcid[profileId] && DATA.mapping_tcid[profileId].rows) || null;
  const runtimeAvailable = runtimeSnapshotAvailable();
  const activeSet = runtimeActiveSet(profileId);
  const baseRows = explicit && explicit.length ? explicit : [];

  return (baseRows || []).map((row) => {
    const hasFact = row.runtime_active === true || row.runtime_active === false;
    const runtimeActive = hasFact
      ? row.runtime_active
      : runtimeAvailable
        ? activeSet.has(row.tcid || "")
        : null;
    return { ...row, runtime_active: runtimeActive };
  });
}

function summarizeTcidRows(rows) {
  const totals = {
    tcid_count: 0,
    with_conditions_count: 0,
    without_conditions_count: 0,
    high_count: 0,
    medium_count: 0,
    low_count: 0,
    runtime_active_count: 0,
    likely_active_count: 0,
    likely_inactive_count: 0,
    unknown_count: 0,
  };
  const bucketIndex = {
    mandatory: { tcids: new Set(), condition_count: 0 },
    optional: { tcids: new Set(), condition_count: 0 },
    conditional: { tcids: new Set(), condition_count: 0 },
  };

  (rows || []).forEach((row) => {
    totals.tcid_count += 1;
    if ((row.condition_count || 0) > 0) totals.with_conditions_count += 1;
    else totals.without_conditions_count += 1;

    if (row.best_confidence === "High") totals.high_count += 1;
    else if (row.best_confidence === "Medium") totals.medium_count += 1;
    else if (row.best_confidence === "Low") totals.low_count += 1;

    if (row.runtime_active === true) totals.runtime_active_count += 1;

    if (row.runtime_signal === "likely_active_mandatory" || row.runtime_signal === "likely_active_optional") {
      totals.likely_active_count += 1;
    } else if (row.runtime_signal === "likely_inactive") {
      totals.likely_inactive_count += 1;
    } else {
      totals.unknown_count += 1;
    }

    (row.conditions || []).forEach((condition) => {
      const bucket = condition.bucket || "optional";
      const target = bucketIndex[bucket] || bucketIndex.optional;
      target.condition_count += 1;
      target.tcids.add(row.tcid);
    });
  });

  return {
    totals,
    by_bucket: {
      mandatory: {
        tcid_count: bucketIndex.mandatory.tcids.size,
        condition_count: bucketIndex.mandatory.condition_count,
      },
      optional: {
        tcid_count: bucketIndex.optional.tcids.size,
        condition_count: bucketIndex.optional.condition_count,
      },
      conditional: {
        tcid_count: bucketIndex.conditional.tcids.size,
        condition_count: bucketIndex.conditional.condition_count,
      },
    },
  };
}

function profileTcidSummary(profileId, rows) {
  const explicit = DATA.mapping_tcid_summary && DATA.mapping_tcid_summary[profileId];
  if (explicit && explicit.totals && explicit.by_bucket) return explicit;
  return summarizeTcidRows(rows);
}

function confidenceClass(confidence) {
  const raw = String(confidence || "").toLowerCase();
  if (raw === "high") return "mandatory";
  if (raw === "medium") return "optional";
  if (raw === "low") return "conditional";
  return "";
}

function confidencePill(confidence) {
  const c = String(confidence || "Unmapped");
  return `<span class="pill ${confidenceClass(c)}">${esc(c)}</span>`;
}

function flattenEvidence(evidenceRows) {
  const out = [];
  (evidenceRows || []).forEach((entry) => {
    if (entry && entry.site_source && entry.site_source.file) {
      out.push({
        ...entry.site_source,
        note: `באתר: ${entry.note || entry.site_source.note || ""}`.trim(),
      });
    }
    if (entry && entry.official_source && entry.official_source.file) {
      out.push({
        ...entry.official_source,
        note: `במקור רשמי: ${entry.note || entry.official_source.note || ""}`.trim(),
      });
    }
  });
  return out;
}

function uniqueSources(items) {
  const dedup = new Map();
  (items || []).forEach((source) => {
    if (!source || !source.file) return;
    const key = [
      source.file,
      source.sheet || "",
      source.row == null ? "" : source.row,
      source.line == null ? "" : source.line,
      source.columns || "",
      source.field_path || "",
      source.note || "",
    ].join("|");
    if (!dedup.has(key)) dedup.set(key, source);
  });
  return Array.from(dedup.values());
}

function uniqueStrings(values) {
  const out = [];
  const seen = new Set();
  (values || []).forEach((value) => {
    const text = String(value || "").trim();
    if (!text || seen.has(text)) return;
    seen.add(text);
    out.push(text);
  });
  return out;
}

function collectTcmtFeatures(row) {
  const direct = Array.isArray(row && row.tcmt_features) ? row.tcmt_features : [];
  const fromConditions = (row && row.conditions ? row.conditions : [])
    .map((condition) => condition && condition.tcmt_feature)
    .filter(Boolean);
  return uniqueStrings([...direct, ...fromConditions]);
}

function tcidSummaryStatusMeta(status) {
  if (status === "expected_active") return { label: "צפוי לפעול", className: "expected-active" };
  if (status === "maybe_active") return { label: "עשוי לפעול", className: "maybe-active" };
  if (status === "expected_inactive") return { label: "צפוי לא לפעול", className: "expected-inactive" };
  return { label: "לא ידוע", className: "unknown" };
}

function fallbackSummaryStatus(row) {
  const signal = row && row.runtime_signal;
  if (signal === "likely_active_mandatory") return "expected_active";
  if (signal === "likely_active_optional") return "maybe_active";
  if (signal === "likely_inactive") return "expected_inactive";
  return "unknown";
}

function fallbackSummaryStatusReason(row) {
  const signal = row && row.runtime_signal;
  if (signal === "likely_active_mandatory") return "נמצא תנאי חובה פעיל ולכן הטסט צפוי להיות פעיל.";
  if (signal === "likely_active_optional") return "נמצא תנאי אופציונלי/תלוי-תנאי פעיל ולכן הטסט עשוי להיות פעיל.";
  if (signal === "likely_inactive") return "התנאים הפעילים מצביעים שהטסט צפוי לא לפעול.";
  return "אין מספיק נתונים כדי לקבוע מצב הפעלה.";
}

function officialWhatTestedEnglish(row) {
  if (row && row.what_tested_en_official) return row.what_tested_en_official;
  if (row && row.ts_title && row.desc) return `${row.desc} (TS: ${row.ts_title})`;
  if (row && row.desc) return row.desc;
  if (row && row.ts_title) return `TS: ${row.ts_title}`;
  return "No official English test description is available.";
}

function officialScenarioNameEnglish(row) {
  if (row && row.official_scenario_name_en) return row.official_scenario_name_en;
  if (row && row.desc) return row.desc;
  if (row && row.ts_title) return row.ts_title;
  return "No official English test description is available.";
}

function fallbackScenarioExplanation(row) {
  const scenario = officialScenarioNameEnglish(row);
  return `תרחיש שבודק שההתנהגות המוגדרת ב-${scenario} מתבצעת בפועל לפי מסמכי TS/TCRL.`;
}

function officialScenarioExplanationHe(row) {
  if (row && row.official_scenario_explanation_he) return row.official_scenario_explanation_he;
  return fallbackScenarioExplanation(row);
}

function officialScenarioExplanationSources(row) {
  if (row && Array.isArray(row.official_scenario_explanation_sources) && row.official_scenario_explanation_sources.length) {
    return uniqueSources(row.official_scenario_explanation_sources);
  }
  return whatTestedSources(row);
}

function whatTestedSources(row) {
  if (row && Array.isArray(row.what_tested_sources) && row.what_tested_sources.length) {
    return uniqueSources(row.what_tested_sources);
  }
  const sources = [];
  if (row && row.source && row.source.file) {
    sources.push({
      file: row.source.file,
      sheet: row.source.sheet,
      row: row.source.row,
      columns: row.source.columns,
      note: "תיאור טסט מתוך TCRL",
    });
  }
  if (row && row.ts_title_source && row.ts_title_source.file) {
    sources.push({
      file: row.ts_title_source.file,
      line: row.ts_title_source.line,
      note: row.ts_title_source.note || "כותרת טסט מתוך TS",
    });
  }
  return uniqueSources(sources);
}

function buildWhatTestedLines(row) {
  const scenarioName = officialScenarioNameEnglish(row);
  const scenarioExplanation = officialScenarioExplanationHe(row);
  return {
    scenarioName,
    scenarioExplanation,
    topLine: `הטסט מאמת את התרחיש הרשמי: ${scenarioName}.`,
    detailLine: `${scenarioName}: ${scenarioExplanation}`,
  };
}

function summaryWhatTested(row) {
  if (row && row.what_tested_he_verified) return row.what_tested_he_verified;
  if (row && row.summary_what_tested_he) return row.summary_what_tested_he;
  const lines = buildWhatTestedLines(row);
  return `${lines.topLine}\n${lines.detailLine}`;
}

function summaryWhyRelevant(row) {
  if (row && row.summary_why_relevant_he) return row.summary_why_relevant_he;
  const conditions = (row && row.conditions) || [];
  if (!conditions.length) return (row && row.unmapped_note) || "לא נמצא תנאי TCMT משויך ל-TCID זה.";
  const first = conditions[0];
  const plain = first && (first.plain_condition_he || conditionPlainText(first));
  if (conditions.length === 1) return plain || "נמצא תנאי יחיד עבור TCID זה.";
  return `${plain || "נמצא תנאי ראשי."} קיימות עוד ${conditions.length - 1} אפשרויות הפעלה חלופיות (OR).`;
}

function profileMembershipData(row) {
  const reason =
    (row && row.profile_membership_reason_he) ||
    "שיוך הטסט מבוסס על רשומת TCID רשמית ב-TCRL ועל התאמות מול TS/ICS כאשר קיימות.";
  const sources =
    row && Array.isArray(row.profile_membership_sources) && row.profile_membership_sources.length
      ? uniqueSources(row.profile_membership_sources)
      : whatTestedSources(row);
  return { reason, sources };
}

function runPreconditionsData(row) {
  if (row && row.run_preconditions && typeof row.run_preconditions === "object") {
    return {
      has_conditions: !!row.run_preconditions.has_conditions,
      conditions_he: row.run_preconditions.conditions_he || "",
      meaning_he: row.run_preconditions.meaning_he || "",
      how_to_meet_he: row.run_preconditions.how_to_meet_he || "",
      sources: uniqueSources(row.run_preconditions.sources || []),
    };
  }
  const conditions = (row && row.conditions) || [];
  if (!conditions.length) {
    return {
      has_conditions: false,
      conditions_he: "",
      meaning_he: "",
      how_to_meet_he: "",
      sources: [],
    };
  }
  const first = conditions[0];
  const firstText = (first && first.plain_condition_he) || conditionPlainText(first);
  const conditionsText =
    conditions.length > 1 ? `${firstText} קיימות עוד ${conditions.length - 1} אפשרויות חלופיות (OR).` : firstText;
  return {
    has_conditions: true,
    conditions_he: conditionsText,
    meaning_he: summaryStatusReason(row),
    how_to_meet_he: "לעדכן ערכי ICS/TSPC כך שביטוי התנאי עבור הטסט מתקיים.",
    sources: uniqueSources(
      conditions.flatMap((condition) => [
        ...flattenEvidence((condition && condition.tspc_evidence) || []),
        ...flattenEvidence((condition && condition.relation_evidence) || []),
      ])
    ),
  };
}

function logicEvalLabel(result) {
  if (result === "true") return "TRUE";
  if (result === "false") return "FALSE";
  return "UNKNOWN";
}

function buildWhyRelevantRows(row, options) {
  const settings = Object.assign({ includeDetails: false }, options || {});
  const conditions = (row && row.conditions) || [];
  if (!conditions.length) {
    return [
      { label: "הסבר תמציתי", value: summaryWhyRelevant(row) },
      { label: "מסקנה", value: summaryStatusReason(row) },
    ];
  }

  const primary = conditions[0] || {};
  const evalItems =
    primary && primary.expression_eval && Array.isArray(primary.expression_eval.items) ? primary.expression_eval.items : [];
  const icsValues = evalItems.length
    ? evalItems
        .map((item) => `${item && item.item ? item.item : "-"}=${item && item.value ? item.value : "-"}`)
        .join(" , ")
    : "לא סופקו ערכי ICS מפורשים.";

  const rows = [
    {
      label: "הסבר תמציתי",
      value: summaryWhyRelevant(row),
    },
    {
      label: "ערכי ICS עיקריים",
      value: icsValues,
    },
    {
      label: "מסקנת השפעה",
      value: summaryStatusReason(row),
    },
  ];

  if (conditions.length > 1) {
    rows.push({
      label: "אפשרויות נוספות (OR)",
      value: `${conditions.length - 1} וריאנטים נוספים זמינים ל-TCID זה.`,
      emphasis: true,
    });
  }

  if (settings.includeDetails && row && row.summary_why_relevant_he) {
    rows.push({
      label: "ניסוח מלא",
      value: row.summary_why_relevant_he,
    });
  }

  return rows;
}

function renderWhyRelevantStructured(row, options) {
  const items = buildWhyRelevantRows(row, options);
  return `
    <div class="tcid-why-grid">
      ${items
        .map(
          (item) => `
            <div class="tcid-why-item ${item.emphasis ? "tcid-why-item-emphasis" : ""}">
              <div class="tcid-why-label">${esc(item.label || "")}</div>
              <div class="tcid-why-value">${esc(item.value || "-")}</div>
            </div>
          `
        )
        .join("")}
    </div>
  `;
}

function renderWhatTestedBlock(row, options) {
  const settings = Object.assign({ includeSources: false, compact: false }, options || {});
  const whatLines = buildWhatTestedLines(row);
  const englishText = officialWhatTestedEnglish(row);
  const quality = (row && row.translation_quality) || "verified_from_mapping";
  const panelId = nextTableId("what-en");
  const sources = officialScenarioExplanationSources(row);
  return `
    <div class="tcid-what-wrap" dir="rtl" data-translation-quality="${esc(quality)}">
      <div class="tcid-what-headline">
        <div class="tcid-what-he">
          <div class="tcid-what-line tcid-what-line-label">שם התרחיש:</div>
          <div class="tcid-what-line tcid-what-line-primary">${esc(whatLines.scenarioName)}</div>
          <div class="tcid-what-line tcid-what-line-label">הסבר:</div>
          <div class="tcid-what-line tcid-what-line-secondary">${esc(whatLines.scenarioExplanation)}</div>
        </div>
        <button
          type="button"
          class="what-tested-en-toggle"
          data-target="${esc(panelId)}"
          aria-expanded="false"
          title="הצג ניסוח באנגלית"
        >EN</button>
      </div>
      <div id="${esc(panelId)}" class="what-tested-en-panel" hidden>
        <pre dir="ltr"><code>${esc(englishText)}</code></pre>
      </div>
      ${settings.includeSources ? `<div class="tcid-what-sources">${sourceDetails(sources, "מקורות לניסוח הטסט")}</div>` : ""}
    </div>
  `;
}

function summaryStatus(row) {
  return (row && row.summary_status) || fallbackSummaryStatus(row);
}

function summaryStatusReason(row) {
  return (row && row.summary_status_reason_he) || fallbackSummaryStatusReason(row);
}

function summaryBadges(row) {
  const explicit = row && Array.isArray(row.summary_badges) ? row.summary_badges : null;
  if (explicit && explicit.length) return explicit;
  const out = [];
  const flags = (row && row.bucket_flags) || {};
  if (flags.mandatory) out.push("חובה");
  if (flags.optional) out.push("אופציונלי");
  if (flags.conditional) out.push("תלוי-תנאי");
  return out;
}

function displayBadgeText(badge) {
  const value = String(badge || "").trim();
  if (value === "TCMT TRUE") return "תנאי TCMT מתקיים";
  if (value === "TCMT FALSE") return "תנאי TCMT לא מתקיים";
  if (value === "TCMT UNKNOWN") return "מצב TCMT לא ידוע";
  if (value === "Runtime Active") return "הופיע בצילום הרצה";
  if (value === "Runtime Inactive") return "לא הופיע בצילום הרצה";
  return value;
}

function renderStatusOptions(selectedValue) {
  return RUN_STATUS_VALUES.map(
    (item) => `<option value="${esc(item.value)}" ${selectedValue === item.value ? "selected" : ""}>${esc(item.label)}</option>`
  ).join("");
}

function renderOwnerOptions(selectedValue) {
  return [
    '<option value="">בחר מבצע</option>',
    ...RUN_STATUS_OWNERS.map(
      (owner) => `<option value="${esc(owner)}" ${selectedValue === owner ? "selected" : ""}>${esc(owner)}</option>`
    ),
  ].join("");
}

function renderRunStatusControls(row, options) {
  const settings = Object.assign({ profileKey: "GLOBAL", compact: false }, options || {});
  const tcid = row && row.tcid ? row.tcid : "";
  const runKey = runEntryKey(settings.profileKey, tcid);
  const entry = getRunEntry(settings.profileKey, tcid);
  return `
    <div class="tcid-run-widget ${settings.compact ? "compact" : ""}" data-run-key="${esc(runKey)}">
      ${RUN_TRACKS.map((track) => {
        const trackState = track.key === "autopts" ? entry.autopts : entry.manual;
        return `
          <div class="tcid-run-row">
            <div class="tcid-run-track">${esc(track.label)}</div>
            <label class="tcid-run-field">
              <span>סטטוס</span>
              <select
                class="run-status-select"
                data-run-key="${esc(runKey)}"
                data-run-track="${esc(track.key)}"
                data-run-field="status"
              >
                ${renderStatusOptions(trackState.status)}
              </select>
            </label>
            <label class="tcid-run-field">
              <span>מבצע</span>
              <select
                class="run-status-select"
                data-run-key="${esc(runKey)}"
                data-run-track="${esc(track.key)}"
                data-run-field="owner"
              >
                ${renderOwnerOptions(trackState.owner)}
              </select>
            </label>
          </div>
        `;
      }).join("")}
    </div>
  `;
}

function getQuickFilterForScope(scope) {
  if (scope === "overview") return tcidQuickFilterState.overview;
  if (scope && tcidQuickFilterState.profiles[scope]) return tcidQuickFilterState.profiles[scope];
  return "all";
}

function setQuickFilterForScope(scope, filterKey) {
  if (scope === "overview") {
    tcidQuickFilterState.overview = filterKey;
    return;
  }
  if (scope && Object.prototype.hasOwnProperty.call(tcidQuickFilterState.profiles, scope)) {
    tcidQuickFilterState.profiles[scope] = filterKey;
  }
}

function matchesTcidQuickFilter(row, filterKey) {
  const key = filterKey || "all";
  if (key === "mandatory_only") return !!((row && row.bucket_flags && row.bucket_flags.mandatory) || false);
  if (key === "expected_active") return summaryStatus(row) === "expected_active";
  if (key === "expected_inactive") return summaryStatus(row) === "expected_inactive";
  if (key === "unmapped") return Number((row && row.condition_count) || 0) === 0;
  return true;
}

function formatGeneratedAt() {
  const stamp = DATA && DATA.meta && DATA.meta.baseline && DATA.meta.baseline.generated_at;
  if (!stamp) return "-";
  const date = new Date(stamp);
  if (Number.isNaN(date.getTime())) return stamp;
  return date.toLocaleString("he-IL", { dateStyle: "short", timeStyle: "short" });
}

function renderDecisionHeader(title, stats) {
  const items = [
    { label: "בדיקות רלוונטיות", value: stats.total },
    { label: "צפוי לרוץ", value: stats.expectedActive },
    { label: "לא צפוי לרוץ", value: stats.expectedInactive },
    { label: "מצב לא ידוע", value: stats.unknown },
  ];
  return `
    <section class="decision-header" aria-label="שכבת החלטה מהירה">
      <div class="decision-headline">
        <h4>${esc(title || "מה חשוב עכשיו?")}</h4>
        <div class="small muted">עודכן לאחרונה: ${esc(formatGeneratedAt())}</div>
      </div>
      <div class="decision-kpi-grid">
        ${items
          .map(
            (item) => `
              <div class="decision-kpi">
                <span>${esc(item.label)}</span>
                <b>${esc(String(item.value || 0))}</b>
              </div>
            `
          )
          .join("")}
      </div>
    </section>
  `;
}

function renderTcidQuickFilters(scope, rows) {
  const active = getQuickFilterForScope(scope);
  return `
    <div class="tcid-quick-filters" role="group" aria-label="סינון מהיר">
      ${TCID_QUICK_FILTERS.map((filter) => {
        const count = (rows || []).filter((row) => matchesTcidQuickFilter(row, filter.key)).length;
        const isActive = filter.key === active;
        return `
          <button
            type="button"
            class="tcid-qf-btn ${isActive ? "active" : ""}"
            data-tcid-scope="${esc(scope)}"
            data-tcid-filter="${esc(filter.key)}"
            aria-pressed="${isActive ? "true" : "false"}"
          >${esc(filter.label)} · ${esc(String(count))}</button>
        `;
      }).join("")}
    </div>
  `;
}

function rowSearchText(row) {
  const parts = [
    row && row.tcid,
    row && row.desc,
    row && row.ts_title,
    summaryWhatTested(row),
    row && row.official_scenario_name_en,
    row && row.official_scenario_explanation_he,
    summaryWhyRelevant(row),
    summaryStatus(row),
    summaryStatusReason(row),
    row && row.profile_membership_reason_he,
    ...(summaryBadges(row) || []),
    ...((summaryBadges(row) || []).map((badge) => displayBadgeText(badge))),
  ];
  if (row && row.run_preconditions) {
    parts.push(row.run_preconditions.conditions_he);
    parts.push(row.run_preconditions.meaning_he);
    parts.push(row.run_preconditions.how_to_meet_he);
  }
  if (row && row.source) {
    parts.push(row.source.file, row.source.sheet, row.source.row, row.source.columns);
  }
  if (row && row.ts_title_source) {
    parts.push(row.ts_title_source.file, row.ts_title_source.line);
  }
  ((row && row.conditions) || []).forEach((condition) => {
    parts.push(condition && condition.map_id);
    parts.push(condition && condition.tspc_name);
    parts.push(condition && condition.tspc_capability);
    parts.push(condition && condition.plain_condition_he);
    parts.push(condition && condition.logic_eval_reason_he);
    parts.push(condition && condition.item_expression);
    const evidence = [
      ...(flattenEvidence((condition && condition.tspc_evidence) || []) || []),
      ...(flattenEvidence((condition && condition.relation_evidence) || []) || []),
    ];
    evidence.forEach((entry) => {
      parts.push(entry && entry.file, entry && entry.sheet, entry && entry.row, entry && entry.note, entry && entry.columns);
    });
    const expr = condition && condition.expression_eval;
    if (expr && Array.isArray(expr.items)) {
      expr.items.forEach((item) => {
        parts.push(item && item.item);
        parts.push(item && item.value);
      });
    }
  });
  return parts.filter(Boolean).join(" ");
}

function renderTcidStatusPill(status, reason) {
  const meta = tcidSummaryStatusMeta(status || "unknown");
  return `<span class="pill tcid-status-pill ${esc(meta.className)}" title="${esc(reason || "")}">${esc(meta.label)}</span>`;
}

function renderTcidMeaningCell(row) {
  const tcmtFeatures = collectTcmtFeatures(row);
  const lines = [];

  lines.push(renderWhatTestedBlock(row, { includeSources: true }));

  if (tcmtFeatures.length) {
    const featureItems = tcmtFeatures.map((feature) => `<li>${esc(feature)}</li>`).join("");
    lines.push(`
      <details class="tcid-feature-details">
        <summary>משמעות לפי TCMT ב-TS (${tcmtFeatures.length})</summary>
        <ul class="src-list">${featureItems}</ul>
      </details>
    `);
  }

  return `<div class="tcid-test-cell">${lines.join("")}</div>`;
}

function renderProfileMembershipBlock(row) {
  const membership = profileMembershipData(row);
  return `
    <details class="tcid-inline-details">
      <summary>על בסיס מה הטסט שייך לפרופיל</summary>
      <div class="tcid-inline-details-body">
        <div class="tcid-inline-details-text">${esc(membership.reason)}</div>
        <div class="small muted">${sourceDetails(membership.sources, "מקורות לשיוך הטסט")}</div>
      </div>
    </details>
  `;
}

function renderRunPreconditionsBlock(row) {
  const pre = runPreconditionsData(row);
  if (!pre.has_conditions) {
    return `
      <div class="tcid-inline-details tcid-inline-details-empty">
        <div class="tcid-inline-details-title">תנאי הרצה</div>
        <div class="small muted">לא הוגדרו תנאי הרצה משויכים לטסט זה.</div>
      </div>
    `;
  }
  return `
    <details class="tcid-inline-details">
      <summary>תנאי הרצה (פתח פירוט)</summary>
      <div class="tcid-inline-details-body">
        <div class="tcid-pre-grid">
          <div class="tcid-pre-item">
            <div class="tcid-pre-label">תנאי הרצה</div>
            <div class="tcid-pre-value">${esc(pre.conditions_he || "-")}</div>
          </div>
          <div class="tcid-pre-item">
            <div class="tcid-pre-label">איך עומדים בהם (מה עושים בפועל)</div>
            <div class="tcid-pre-value">${esc(pre.how_to_meet_he || "-")}</div>
          </div>
        </div>
        <div class="small muted">${sourceDetails(pre.sources || [], "מקורות לתנאי ההרצה")}</div>
      </div>
    </details>
  `;
}

function renderMappedTcidsCell(mappedTcids, unmappedReason) {
  if (!mappedTcids || !mappedTcids.length) {
    return `
      <span class="pill optional">לא נמצא קשר ודאי ל-TCID</span>
      <div class="small muted" style="margin-top:6px;">${esc(unmappedReason || "לא נמצא מיפוי ודאי במקורות.")}</div>
    `;
  }

  const rows = mappedTcids
    .map((mapped) => {
      const sources = flattenEvidence(mapped.evidence || []);
      return `
        <article class="mapped-tcid-row" data-searchable>
          <div class="mapped-tcid-head">
            <code>${esc(mapped.tcid || "")}</code>
            ${confidencePill(mapped.confidence)}
            <span class="pill">score: ${esc(String(mapped.score != null ? mapped.score : "-"))}</span>
          </div>
          <div class="small">${esc(mapped.desc || "")}</div>
          <div class="small muted">Category: ${esc(mapped.category || "-")} · Active Date: ${esc(mapped.active_date || "-")}</div>
          ${sourceDetails(sources, "מקור למיפוי זה")}
        </article>
      `;
    })
    .join("");

  return `
    <details class="mapped-tcid-details">
      <summary>${mappedTcids.length} TCID משויכים</summary>
      <div class="mapped-tcid-list">${rows}</div>
    </details>
  `;
}

function renderMappingTable(title, rows, options) {
  const settings = Object.assign({ collapsed: false, showBucket: false }, options || {});
  if (!rows || !rows.length) {
    return `<div class="muted">אין נתוני מיפוי להצגה עבור ${esc(title)}.</div>`;
  }

  const columns = [
    { label: "מזהה TSPC", key: "tspc_id", technical: "TSPC" },
    { label: "משמעות פונקציונלית", key: "meaning" },
    { label: "Mandatory", key: "mandatory_flag" },
    { label: "Value", key: "value_flag" },
    { label: "TCID משויכים", key: "mapped_tcids", technical: "TCID" },
    { label: "רמת ודאות", key: "mapping_confidence" },
    { label: "מקור", key: "source" },
  ];

  if (settings.showBucket) {
    columns.splice(1, 0, { label: "סיווג", key: "mapping_bucket" });
  }

  const tableId = nextTableId("map-table");
  const body = rows
    .map((row) => {
      const sources = flattenEvidence(row.evidence || []);
      const bucketLabel = bucketMeta(row.bucket || "optional").label;
      return `
      <tr data-searchable>
        <td>
          <code>${esc(row.tspc_name || "")}</code>
          <div class="small muted">ICS Item: ${esc(row.tspc_item || "-")}</div>
          <div class="small muted">Status: ${esc(row.tspc_status || "-")}</div>
        </td>
        ${
          settings.showBucket
            ? `<td><span class="pill ${esc(bucketMeta(row.bucket || "optional").className)}">${esc(bucketLabel)}</span></td>`
            : ""
        }
        <td>${esc(row.tspc_capability || "")}</td>
        <td>${mandatoryPill(row.mandatory)}</td>
        <td>${valuePill(row.value)}</td>
        <td>${renderMappedTcidsCell(row.mapped_tcids || [], row.unmapped_reason)}</td>
        <td>${confidencePill(row.confidence)}</td>
        <td>${sourceDetails(sources, "מקור למיפוי")}</td>
      </tr>
    `;
    })
    .join("");

  const table = `
    <div class="table-tools">${columnHelpToggle(tableId)}</div>
    <div class="table-wrap">
      <table id="${esc(tableId)}">
        <thead>
          <tr>
            ${columns
              .map((col) => `<th>${columnHead(col.label, col.key, col.technical)}</th>`)
              .join("")}
          </tr>
          ${columnHelpRow(columns)}
        </thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  `;

  if (!settings.collapsed) return `<h3>${esc(title)}</h3>${table}`;
  return `
    <details>
      <summary>${esc(title)} (${rows.length})</summary>
      ${table}
    </details>
  `;
}

function renderMappingViewToggle(scope, view) {
  return `
    <div class="mapping-view-toggle" role="group" aria-label="בחירת תצוגת מיפוי">
      <button
        type="button"
        class="mapping-view-btn ${view === "tcid" ? "active" : ""}"
        data-mapping-scope="${esc(scope)}"
        data-mapping-view="tcid"
        aria-pressed="${view === "tcid" ? "true" : "false"}"
      >TCID-first</button>
      <button
        type="button"
        class="mapping-view-btn ${view === "tspc" ? "active" : ""}"
        data-mapping-scope="${esc(scope)}"
        data-mapping-view="tspc"
        aria-pressed="${view === "tspc" ? "true" : "false"}"
      >TSPC-first</button>
    </div>
  `;
}

function renderMappingControls(scope, view) {
  return `
    <section class="mapping-controls" aria-label="בקרות תצוגת מיפוי">
      <div class="mapping-control-group">
        <div class="mapping-control-label">תצוגת מיפוי</div>
        ${renderMappingViewToggle(scope, view)}
      </div>
    </section>
  `;
}

function renderConditionBucketPill(bucket) {
  const meta = bucketMeta(bucket || "optional");
  return `<span class="pill tcid-bucket-pill ${esc(meta.className)}">${esc(meta.label)}</span>`;
}

function renderTcidConditionsCell(row, options) {
  const settings = Object.assign({ bucket: null }, options || {});
  const allConditions = row.conditions || [];
  const filteredConditions = settings.bucket
    ? allConditions.filter((condition) => condition.bucket === settings.bucket)
    : allConditions;

  if (!filteredConditions.length) {
    const reason = row.unmapped_note || "אין תנאים להצגה עבור TCID זה בחתך הנוכחי.";
    return `
      <div class="tcid-conditions-empty">
        <span class="pill optional">ללא תנאי הפעלה משויכים</span>
        <div class="small muted">${esc(reason)}</div>
      </div>
    `;
  }

  const orHint =
    filteredConditions.length > 1
      ? `<div class="small muted tcid-condition-or-hint">נמצאו כמה אפשרויות הפעלה לאותו TCID (לוגיקת OR).</div>`
      : "";

  const rows = filteredConditions
    .map((condition) => {
      const tspcSources = flattenEvidence(condition.tspc_evidence || []);
      const relationSources = flattenEvidence(condition.relation_evidence || []);
      const sources = uniqueSources([...tspcSources, ...relationSources]);
      return `
        <article class="tcid-condition-row" data-searchable>
          <div class="tcid-condition-head">
            <span class="tcid-condition-source"><code>${esc(condition.tspc_name || "TSPC לא מזוהה")}</code></span>
            ${renderConditionBucketPill(condition.bucket)}
            ${mandatoryPill(condition.mandatory)}
            ${valuePill(condition.value)}
            ${confidencePill(condition.confidence)}
          </div>
          <div class="tcid-condition-plain">${esc(conditionPlainText(condition))}</div>
          <div class="small muted">${sourceDetails(sources, "מקור לתנאי זה")}</div>
        </article>
      `;
    })
    .join("");

  return `
    <div class="tcid-conditions">
      ${orHint}
      <div class="tcid-conditions-list">${rows}</div>
    </div>
  `;
}

function buildTcidVariantRows(rows, options) {
  const settings = Object.assign({ bucket: null }, options || {});
  const variantRows = [];

  (rows || []).forEach((row) => {
    const conditions = settings.bucket
      ? (row.conditions || []).filter((condition) => condition.bucket === settings.bucket)
      : row.conditions || [];

    if (!conditions.length) {
      variantRows.push({
        tcid: row.tcid || "",
        variant: "-",
        category: row.category || "-",
        active_date: row.active_date || "-",
        desc: row.desc || "",
        applicable_tspc: "-",
        ics_ixit_prereq: "-",
        pics_pxit_conditions: "-",
        execution_notes: row.unmapped_note || "אין תנאים משויכים ל-TCID זה.",
        runtime_active: row.runtime_active,
        runtime_signal: row.runtime_signal || "unknown",
        best_confidence: row.best_confidence || "Unmapped",
        tcid_source: [
          {
            file: row.source && row.source.file,
            sheet: row.source && row.source.sheet,
            row: row.source && row.source.row,
            columns: row.source && row.source.columns,
            note: "שורת TCID מתוך TCRL",
          },
        ],
        relation_sources: [],
        tspc_sources: [],
      });
      return;
    }

    conditions.forEach((condition, index) => {
      const hint = conditionHintFromCondition(condition);
      variantRows.push({
        tcid: row.tcid || "",
        variant: `${row.tcid || ""}#${index + 1}`,
        category: row.category || "-",
        active_date: row.active_date || "-",
        desc: row.desc || "",
        applicable_tspc: condition.tspc_name || "-",
        ics_ixit_prereq: `ICS Item: ${condition.tspc_item || "-"} · Status: ${condition.tspc_status || "-"}`,
        pics_pxit_conditions: `Mandatory: ${condition.mandatory || "-"} · Value: ${condition.value || "-"}`,
        execution_notes: [
          `Condition: ${conditionHintLabel(hint)}`,
          `Confidence: ${condition.confidence || "Unmapped"}`,
          `Mapped Bucket: ${bucketMeta(condition.bucket || "optional").label}`,
        ].join(" · "),
        runtime_active: row.runtime_active,
        runtime_signal: row.runtime_signal || "unknown",
        best_confidence: condition.confidence || row.best_confidence || "Unmapped",
        condition_hint: hint,
        tcid_source: [
          {
            file: row.source && row.source.file,
            sheet: row.source && row.source.sheet,
            row: row.source && row.source.row,
            columns: row.source && row.source.columns,
            note: "שורת TCID מתוך TCRL",
          },
        ],
        relation_sources: flattenEvidence(condition.relation_evidence || []),
        tspc_sources: flattenEvidence(condition.tspc_evidence || []),
      });
    });
  });

  return variantRows;
}

function renderTcidCompactLegend() {
  const legend = (DATA.ui_presentations && DATA.ui_presentations.tcid_compact_legend) || {};
  const title = legend.title || "איך לקרוא את הרשימה במהירות";
  return `
    <div class="tcid-compact-legend small">
      <b>${esc(title)}</b><br>
      <span><b>מה הטסט בודק:</b> ${esc(legend.what_tested || "מה נבדק בפועל.")}</span>
      <span> · <b>למה רלוונטי:</b> ${esc(legend.why_relevant || "למה מופיע עכשיו ברשימה.")}</span>
      <span> · <b>סטטוס:</b> ${esc(legend.status || "צפוי לרוץ / עשוי לרוץ / לא צפוי לרוץ / לא ידוע.")}</span>
      <span> · <b>OR:</b> ${esc(legend.or_logic || "כמה תנאים מוצגים כאפשרויות חלופיות.")}</span>
    </div>
  `;
}

function renderTcidExpandedDetails(row, options) {
  const settings = Object.assign({ bucket: null, profileKey: "GLOBAL" }, options || {});
  const conditionSources = (row.conditions || []).flatMap((condition) => [
    ...flattenEvidence(condition.tspc_evidence || []),
    ...flattenEvidence(condition.relation_evidence || []),
  ]);
  const rowSources = [];
  if (row.source && row.source.file) {
    rowSources.push({
      file: row.source.file,
      sheet: row.source.sheet,
      row: row.source.row,
      columns: row.source.columns,
      note: "רשומת TCID מתוך TCRL",
    });
  }
  if (row.ts_title_source && row.ts_title_source.file) {
    rowSources.push({
      file: row.ts_title_source.file,
      line: row.ts_title_source.line,
      note: "כותרת טסט מתוך TS",
    });
  }
  const sources = uniqueSources([...rowSources, ...conditionSources]);
  const mapIds = uniqueStrings((row.conditions || []).map((condition) => condition && condition.map_id).filter(Boolean));
  const badges = (summaryBadges(row) || [])
    .map((badge) => `<span class="pill">${esc(displayBadgeText(badge))}</span>`)
    .join("");
  const statusValue = summaryStatus(row);
  const statusReason = summaryStatusReason(row);
  const runStatusWidget = renderRunStatusControls(row, { profileKey: settings.profileKey, compact: false });

  return `
    <div class="tcid-expand-panel">
      <div class="tcid-expand-section">
        <h4>מה הטסט בודק (פירוט מלא)</h4>
        ${renderTcidMeaningCell(row)}
      </div>
      <div class="tcid-expand-section">
        <h4>למה רלוונטי עכשיו</h4>
        ${renderWhyRelevantStructured(row, { includeDetails: true })}
      </div>
      <div class="tcid-expand-section">
        <h4>תנאי הרצה מעשיים</h4>
        ${renderRunPreconditionsBlock(row)}
      </div>
      <div class="tcid-expand-section">
        <h4>על בסיס מה הטסט שייך לפרופיל</h4>
        ${renderProfileMembershipBlock(row)}
      </div>
      <div class="tcid-expand-section">
        <h4>פרטים מתקדמים</h4>
        <div class="tcid-expand-meta">
          <div><b>קטגוריה:</b> ${esc(row.category || "-")}</div>
          <div><b>תאריך רלוונטיות:</b> ${esc(row.active_date || "-")}</div>
          <div><b>רמת ודאות:</b> ${confidencePill(row.best_confidence || "Unmapped")}</div>
          <div><b>מספר תנאים:</b> ${esc(String(row.condition_count || 0))}</div>
          <div><b>סטטוס קומפקטי:</b> ${renderTcidStatusPill(statusValue, statusReason)}</div>
          <div><b>תגיות:</b> ${badges || '<span class="muted">אין תגיות</span>'}</div>
          <div><b>מזהי מיפוי:</b> ${mapIds.length ? mapIds.map((id) => `<code>${esc(id)}</code>`).join(" ") : "-"}</div>
        </div>
        <div class="tcid-expand-run-status">${runStatusWidget}</div>
        <div class="tcid-expand-conditions">${renderTcidConditionsCell(row, settings)}</div>
      </div>
      <div class="tcid-expand-section tcid-expand-sources">
        <h4>מקורות מלאים</h4>
        ${sourceDetails(sources, "פתח מקורות לשורה זו")}
      </div>
    </div>
  `;
}

function renderTcidCompactRow(row, settings) {
  const statusValue = summaryStatus(row);
  const statusReason = summaryStatusReason(row);
  const badges = (summaryBadges(row) || [])
    .map((badge) => `<span class="pill tcid-inline-badge">${esc(displayBadgeText(badge))}</span>`)
    .join("");
  const runStatusWidget = renderRunStatusControls(row, { profileKey: settings.profileKey || "GLOBAL", compact: true });
  const membershipBlock = renderProfileMembershipBlock(row);
  const pre = runPreconditionsData(row);
  const preconditionsBlock = pre.has_conditions ? renderRunPreconditionsBlock(row) : "";

  return `
    <article
      class="tcid-row-card"
      data-searchable
      data-search-text="${esc(rowSearchText(row))}"
    >
      <div class="tcid-row-head">
        <div class="tcid-compact-main">
          <div class="tcid-test-name"><span>שם הטסט:</span> <code>${esc(row.tcid || "")}</code></div>
          ${badges ? `<div class="tcid-compact-badges">${badges}</div>` : ""}
        </div>
        <div class="tcid-compact-status">
          ${renderTcidStatusPill(statusValue, statusReason)}
        </div>
      </div>
      <div class="tcid-row-grid">
        <section class="tcid-row-block">
          <h4>מה הטסט בודק</h4>
          ${renderWhatTestedBlock(row, { includeSources: false, compact: true })}
        </section>
        <section class="tcid-row-block tcid-row-block-status">
          <h4>סטטוס וניהול הרצה</h4>
          <div class="small muted">${esc(statusReason)}</div>
          ${runStatusWidget}
        </section>
      </div>
      <div class="tcid-row-collapsibles">
        ${membershipBlock}
        ${preconditionsBlock}
      </div>
    </article>
  `;
}

function renderTcidMappingTable(title, rows, options) {
  const settings = Object.assign({ collapsed: false, bucket: null, scope: "overview", profileKey: "GLOBAL" }, options || {});
  if (!rows || !rows.length) return `<div class="muted">אין נתוני TCID להצגה עבור ${esc(title)}.</div>`;
  const visibleRows = settings.bucket
    ? rows.filter((row) => (row.conditions || []).some((condition) => condition.bucket === settings.bucket))
    : rows;
  if (!visibleRows.length) return `<div class="muted">אין שורות TCID להצגה עבור ${esc(title)}.</div>`;
  const activeQuickFilter = getQuickFilterForScope(settings.scope);
  const filteredRows = visibleRows.filter((row) => matchesTcidQuickFilter(row, activeQuickFilter));

  const tableId = nextTableId("tcid-map-table");
  const cards = filteredRows
    .map((row) => renderTcidCompactRow(row, settings))
    .join("");

  const table = `
    ${renderTcidCompactLegend()}
    ${renderTcidQuickFilters(settings.scope, visibleRows)}
    <div class="tcid-cards" id="${esc(tableId)}">
      ${
        cards ||
        '<div class="tcid-empty muted">אין שורות שמתאימות לפילטר הנוכחי. אפשר לעבור ל"הכל" או לפילטר אחר.</div>'
      }
    </div>
  `;

  if (!settings.collapsed) return `<h3>${esc(title)} (${filteredRows.length})</h3>${table}`;
  return `
    <details>
      <summary>${esc(title)} (${filteredRows.length})</summary>
      ${table}
    </details>
  `;
}

function renderOverviewProfileCards() {
  const cards = (DATA.profiles_overview || [])
    .map(
      (profile) => `
    <details class="profile-accordion">
      <summary>
        <span class="profile-code">${esc(profile.name)}</span>
        <span class="profile-summary">${esc(profile.what_it_is || "")}</span>
      </summary>
      <div class="profile-accordion-body">
        <div><b>מה זה:</b> ${esc(profile.what_it_is || "")}</div>
        <div><b>מה השירותים שהוא מספק:</b> ${esc(profile.services || "")}</div>
        <div><b>למה זה חשוב:</b> ${esc(profile.why_it_matters || "")}</div>
      </div>
    </details>
  `
    )
    .join("");

  return `
    <div class="card span-12">
      <h2 class="section-title">סקירה מהירה</h2>
      <h3>מה כולל כל פרופיל</h3>
      <p class="section-intro">לחץ על שם פרופיל כדי לפתוח את ההסבר. כך רואים קודם מה הערך של כל פרופיל ורק אחר כך את רשימות הבדיקות.</p>
      <div class="profile-accordion-list">${cards}</div>
    </div>
  `;
}

function renderOverviewSummaryCards() {
  const cards = (DATA.summary || [])
    .map((entry) => {
      const tcidRows = profileTcidRows(entry.profile);
      const tcidSummary = profileTcidSummary(entry.profile, tcidRows);
      const byBucket = tcidSummary.by_bucket || {};
      const counts = {
        mandatory: ((byBucket.mandatory || {}).tcid_count || 0),
        optional: ((byBucket.optional || {}).tcid_count || 0),
        conditional: ((byBucket.conditional || {}).tcid_count || 0),
      };
      const profileActive = overviewState.profile === entry.profile;
      const buttons = BUCKETS.map((bucket) => {
        const active = profileActive && overviewState.bucket === bucket.key;
        return `
        <button
          type="button"
          class="bucket-btn ${active ? "active" : ""}"
          data-ov-profile="${esc(entry.profile)}"
          data-ov-bucket="${esc(bucket.key)}"
          aria-pressed="${active ? "true" : "false"}"
        >${esc(bucket.label)}: ${counts[bucket.key] || 0}</button>
      `;
      }).join("");

      return `
      <article class="summary-card ${profileActive ? "active" : ""}">
        <h4>${esc(entry.profile)}</h4>
        <div class="small muted">בחר קטגוריה כדי לפתוח שכבת פירוט שנייה בלי עומס מידע מיידי.</div>
        <div class="bucket-row">${buttons}</div>
      </article>
    `;
    })
    .join("");

  return `
    <div class="card span-12">
      <h3>${esc((DATA.ui_labels && DATA.ui_labels.overview_title) || "סקירה מהירה")}</h3>
      <p class="section-intro">
        לחיצה על חובה/אופציונלי/תלוי-תנאי פותחת פירוט מדורג.
        במסך זה המספרים נספרים לפי <code>TCID</code> ולא לפי <code>TSPC</code>.
      </p>
      <div class="summary-cards">${cards}</div>
    </div>
  `;
}

function renderTsProfileSummary(profileId) {
  const ts = profileTsExtract(profileId);
  if (!ts || !ts.meta) return "";

  const meta = ts.meta || {};
  const tcmt = ts.tcmt || {};
  const groups = Array.isArray(ts.test_groups) ? ts.test_groups : [];
  const convention = ts.tcid_convention || {};
  const revisionNotes = (ts.revision_notes || []).slice(0, 4);
  const source = ts.source && ts.source.file ? [{ file: ts.source.file, note: "מסמך TS רשמי" }] : [];

  const notes = revisionNotes.length
    ? revisionNotes.map((note) => `<li>${esc(note.text || "")}</li>`).join("")
    : '<li class="muted">לא נמצאו הערות Revision לחיתוך זה.</li>';

  const groupPreview = groups.length ? groups.slice(0, 10).join(" | ") : "-";
  const summaryFields = [
    {
      label: "גרסת מסמך TS",
      value: meta.Revision || "-",
      help: "מזהה הגרסה הרשמי של מסמך ה-TS שעליו מבוסס הפענוח בעמוד זה.",
    },
    {
      label: "תאריך גרסה",
      value: meta["Revision Date"] || meta["Version Date"] || "-",
      help: "התאריך שבו פורסמה או עודכנה גרסת ה-TS שממנה נלקחו הנתונים.",
    },
    {
      label: "פורסם במסגרת TCRL",
      value: meta["Published during TCRL"] || "-",
      help: "מחזור ה-TCRL שבו גרסת ה-TS הזו פורסמה רשמית.",
    },
    {
      label: "מספר שורות TCMT",
      value: String(tcmt.row_count || 0),
      help: "כמה שורות מיפוי TCMT נמצאו במסמך TS עבור הפרופיל.",
    },
    {
      label: "TCID שמופו ב-TCMT",
      value: String(tcmt.mapped_tcid_count || 0),
      help: "כמה מזהי טסט (TCID) חוברו בפועל דרך טבלת ה-TCMT.",
    },
    {
      label: "שורות TCMT לא חד-משמעיות",
      value: String(tcmt.rows_with_unknown_eval || 0),
      help: "כמה שורות TCMT לא הוכרעו באופן מלא לפי ערכי הביטוי שנקראו.",
    },
    {
      label: "כותרות טסט שחולצו",
      value: String(ts.tcid_titles_count || 0),
      help: "מספר כותרות הטסט שחולצו אוטומטית מתוך מסמך ה-TS.",
    },
    {
      label: "פורמט מזהה TCID",
      value: convention.format_hint || "-",
      help: "התבנית הרשמית של מזהה טסט כפי שה-TS מתאר.",
    },
    {
      label: "דוגמת TCID מהמסמך",
      value: convention.example_tcid || "-",
      help: "דוגמה ממסמך ה-TS שעוזרת להבין איך נראה מזהה תקני אמיתי.",
    },
    {
      label: "קבוצות בדיקה שזוהו",
      value: `${groups.length} (${groupPreview})`,
      help: "קבוצות בדיקה שזוהו מה-TS; הערך כולל כמות ותצוגת דוגמה מקוצרת.",
    },
  ];

  return `
    <div class="card span-12 ts-summary-card">
      <h3>תקציר TS (${esc(profileId)})</h3>
      <div class="ts-summary-grid">
        ${summaryFields
          .map(
            (field) => `
              <article class="ts-summary-field">
                <div class="ts-summary-label">${esc(field.label)}</div>
                <div class="ts-summary-value">${esc(field.value)}</div>
                <div class="ts-summary-help">${esc(field.help)}</div>
              </article>
            `
          )
          .join("")}
      </div>
      <details class="small ts-revision-details">
        <summary>הערות גרסה (Revision Notes / TSE)</summary>
        <ul class="src-list">${notes}</ul>
      </details>
      <div class="small muted">${sourceDetails(source, "מקור TS")}</div>
    </div>
  `;
}

function renderOverviewDetails() {
  const summaryEntry = getSummaryEntry(overviewState.profile);
  if (!summaryEntry) return '<div class="card span-12 warning">לא נמצאו נתוני סקירה מהירה.</div>';

  const bucket = bucketMeta(overviewState.bucket);
  const selectedView = mappingViewState.overview || "tcid";
  const mappingRows = profileMappingRows(summaryEntry.profile);
  const filteredTspcRows = mappingRows.filter((row) => row.bucket === overviewState.bucket);
  const tcidRows = profileTcidRows(summaryEntry.profile);
  const tcidSummary = profileTcidSummary(summaryEntry.profile, tcidRows);
  const filteredTcidRows = tcidRows.filter((row) =>
    (row.conditions || []).some((condition) => condition.bucket === overviewState.bucket)
  );

  const previewLimit = 8;
  const visible = overviewState.expanded
    ? selectedView === "tcid"
      ? filteredTcidRows
      : filteredTspcRows
    : (selectedView === "tcid" ? filteredTcidRows : filteredTspcRows).slice(0, previewLimit);

  const expandButton =
    (selectedView === "tcid" ? filteredTcidRows.length : filteredTspcRows.length) > previewLimit
      ? `<button id="overviewExpandBtn" type="button" class="toggle-inline">${
          overviewState.expanded
            ? "הצג פחות"
            : `הצג פרטים מלאים (${selectedView === "tcid" ? filteredTcidRows.length : filteredTspcRows.length})`
        }</button>`
      : "";

  const profileSources = sourceDetails(
    (summaryEntry.source || []).map((source) => ({ ...source, note: `מקור רמת פרופיל ${summaryEntry.profile}` })),
    `מקורות כלליים ל-${summaryEntry.profile}`
  );
  const decisionStats = {
    total: filteredTcidRows.length,
    expectedActive: filteredTcidRows.filter((row) => summaryStatus(row) === "expected_active").length,
    expectedInactive: filteredTcidRows.filter((row) => summaryStatus(row) === "expected_inactive").length,
    unknown: filteredTcidRows.filter((row) => summaryStatus(row) === "unknown").length,
  };

  const conditionalNotice =
    overviewState.bucket === "conditional"
      ? `
      <div class="warning small">
        <b>${termChip("Conditional", "מה זה Conditional?")}</b>
        ${esc(glossary("Conditional"))}
        <ul class="src-list">
          <li>במסך הזה: פריט מסווג לקטגוריה אחת בלבד (חובה / אופציונלי / תלוי-תנאי) לפי הקונפיגורציה הנוכחית.</li>
          <li>בקונפיגורציה אחרת אותו פריט יכול לעבור לקטגוריה אחרת, ולכן חשוב לראות גם ${termChip(
            "TCID",
            "TCID"
          )} בלשוניות הפרופילים.</li>
        </ul>
      </div>
    `
      : "";

  return `
    <div class="card span-12 overview-details">
      <h3>מה חשוב עכשיו: ${esc(summaryEntry.profile)} / ${esc(bucket.label)}</h3>
      <p class="section-intro">${esc(bucket.explain)}</p>
      ${renderDecisionHeader(`תמונת החלטה מהירה עבור ${summaryEntry.profile} (${bucket.label})`, decisionStats)}
      <details class="notice small overview-help-box">
        <summary><b>איך לקרוא את המסך הזה</b></summary>
        <ul class="src-list">
          <li><b>מה הטסט בודק:</b> שם התרחיש והסבר מו נבדק בפועל מתוך מסמכי התקן.</li>
          <li><b>סטטוס:</b> הערכה אם הטסט צפוי לרוץ כרגע.</li>
          <li><b>תנאי הרצה:</b> תנאי TCMT/ICS שצריכים להתקיים כדי להריץ את הטסט.</li>
        </ul>
      </details>
      ${conditionalNotice}
      ${renderMappingControls("overview", selectedView)}
      <div class="items">
        ${
          visible.length
            ? selectedView === "tcid"
              ? renderTcidMappingTable(`TCID-first ${summaryEntry.profile} (${bucket.label})`, visible, {
                  collapsed: false,
                  bucket: overviewState.bucket,
                  scope: "overview",
                  profileKey: summaryEntry.profile,
                })
              : renderMappingTable(`מיפוי ${summaryEntry.profile} (${bucket.label})`, visible, {
                  collapsed: false,
                  showBucket: false,
                })
            : `<div class="muted">אין פריטי ${selectedView === "tcid" ? "TCID" : "מיפוי"} בקטגוריה זו.</div>`
        }
      </div>
      ${expandButton}
      <div class="small muted" style="margin-top:10px;">${profileSources}</div>
    </div>
  `;
}

function renderGlossaryDrawerContent() {
  const extended = DATA.glossary_extended || {};
  const priority = ["TSPC", "TCID", "TSPC_TCID_RELATION", "Conditional", "IOPT", "Mandatory", "Value", "Category"];
  const cards = [];

  priority.forEach((term) => {
    if (extended[term]) {
      const entry = extended[term];
      const bullets = (entry.how_to_read || [])
        .map((line) => `<li>${esc(line)}</li>`)
        .join("");
      const sources = sourceDetails(entry.sources || [], "מקורות להסבר");
      const example = entry.example
        ? `
          <div class="glossary-example">
            <b>דוגמה קצרה</b>
            ${entry.example.tspc_name ? `<div><code>${esc(entry.example.tspc_name)}</code></div>` : ""}
            ${entry.example.tcid ? `<div><code>${esc(entry.example.tcid)}</code></div>` : ""}
            ${entry.example.capability ? `<div class="small">${esc(entry.example.capability)}</div>` : ""}
            ${entry.example.desc ? `<div class="small">${esc(entry.example.desc)}</div>` : ""}
          </div>
        `
        : "";
      cards.push(`
        <article class="glossary-item">
          <h4>${esc(entry.title || term)}</h4>
          <div class="small"><b>בשורה אחת:</b> ${esc(entry.short || "")}</div>
          <div class="small">${esc(entry.long || DATA.glossary?.[term] || "")}</div>
          ${bullets ? `<ul class="src-list">${bullets}</ul>` : ""}
          ${example}
          <div class="small muted">${sources}</div>
        </article>
      `);
      return;
    }

    if (DATA.glossary && DATA.glossary[term]) {
      cards.push(`
        <article class="glossary-item">
          <h4>${esc(term)}</h4>
          <div class="small">${esc(DATA.glossary[term])}</div>
        </article>
      `);
    }
  });

  Object.entries(DATA.glossary || {}).forEach(([term, description]) => {
    if (priority.includes(term) || extended[term]) return;
    cards.push(`
      <article class="glossary-item">
        <h4>${esc(term)}</h4>
        <div class="small">${esc(description)}</div>
      </article>
    `);
  });

  return `
    <div class="glossary-drawer-inner">
      <p class="section-intro">כאן מרוכזים כל המונחים עם הסבר בעברית פשוטה, כולל איך לקרוא יחד TSPC ו-TCID.</p>
      <div class="glossary-grid">${cards.join("")}</div>
    </div>
  `;
}

function renderOverviewPanel() {
  const counts = (DATA.meta && DATA.meta.counts) || {};

  return `
    <div class="grid">
      ${renderOverviewProfileCards()}
      ${renderOverviewSummaryCards()}
      ${renderOverviewDetails()}

      <div class="card span-12 success">
        <b>ספירות בדיקות לפי TCRL</b>
        <ul class="src-list">
          <li data-searchable>DIS: ${esc(String((counts.dis && counts.dis.total) || 0))}</li>
          <li data-searchable>BAS: ${esc(String((counts.bas && counts.bas.total) || 0))}</li>
          <li data-searchable>HRS: ${esc(String((counts.hrs && counts.hrs.total) || 0))}</li>
          <li data-searchable>HID (HOGP): ${esc(String((counts.hid && counts.hid.total) || 0))}</li>
        </ul>
      </div>
    </div>
  `;
}

function renderTspcTable(title, rows) {
  if (!rows || !rows.length) return `<div class="muted">אין פריטי קונפיגורציה להצגה עבור ${esc(title)}.</div>`;

  const columns = [
    { label: "מזהה קונפיגורציה", key: "tspc_id", technical: "TSPC" },
    { label: "סעיף ב-ICS", key: "ics_item" },
    { label: "משמעות פונקציונלית", key: "meaning" },
    { label: "סטטוס בתקן", key: "status" },
    { label: "האם חובה לפי הקונפיגורציה", key: "mandatory_flag" },
    { label: "ערך בפועל בקונפיגורציה", key: "value_flag" },
    { label: "מקור", key: "source" },
  ];
  const tableId = nextTableId("tspc-table");

  const body = rows
    .map((row) => {
      const sources = buildItemSources(row);
      return `
      <tr data-searchable>
        <td><code>${esc(row.name || "")}</code></td>
        <td><code>${esc(row.item || "")}</code></td>
        <td>${esc(row.capability || "")}</td>
        <td><span class="pill">${esc(row.status || "-")}</span></td>
        <td>${mandatoryPill(row.mandatory)}</td>
        <td>${valuePill(row.value)}</td>
        <td>${sourceDetails(sources)}</td>
      </tr>
    `;
    })
    .join("");

  return `
    <h3>${esc(title)}</h3>
    <div class="small muted" style="margin-bottom:8px;">הטבלה מציגה את היכולות שמוגדרות בקונפיגורציית PTS, ואת ההקשר שלהן במסמכי ICS.</div>
    <div class="table-tools">${columnHelpToggle(tableId)}</div>
    <div class="table-wrap">
      <table id="${esc(tableId)}">
        <thead>
          <tr>
            ${columns
              .map((col) => `<th>${columnHead(col.label, col.key, col.technical)}</th>`)
              .join("")}
          </tr>
          ${columnHelpRow(columns)}
        </thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  `;
}

function renderIcsReferences(title, refs) {
  if (!refs || !refs.length) return `<div class="muted">אין אסמכתאות ICS זמינות עבור ${esc(title)}.</div>`;

  const rows = refs
    .map(
      (ref) => `
    <article class="item-row" data-searchable>
      <div><b>${esc(ref.needle || "")}</b></div>
      ${sourceDetails([{ file: ref.file, line: ref.line, note: `מסמך ${title}` }], "מקור אסמכתא")}
    </article>
  `
    )
    .join("");

  return `
    <h3>${esc(`אסמכתאות ICS עבור ${title}`)}</h3>
    <div class="small muted">אלו טקסטים שמצאנו במסמכי ICS ומחברים בין ההגדרות בקונפיגורציה למסמך התקן.</div>
    <div class="items">${rows}</div>
  `;
}

function renderTcTable(title, rows, options) {
  const settings = Object.assign({ collapsed: true, profileKey: "GLOBAL" }, options || {});
  if (!rows || !rows.length) return `<div class="muted">אין בדיקות TCID להצגה עבור ${esc(title)}.</div>`;

  const columns = [
    { label: "מזהה בדיקת תקן", key: "tcid", technical: "TCID" },
    { label: "סוג בדיקה", key: "tc_category", technical: "Category" },
    { label: "תאריך רלוונטיות", key: "active_date", technical: "Active Date" },
    { label: "מה הטסט בודק (עברית מאומתת)", key: "test_desc" },
    { label: "סטטוס הרצה (ידני/AutoPTS)", key: "execution_status" },
    { label: "שיוך ותנאי הרצה", key: "membership_preconditions" },
    { label: "מקור", key: "source" },
  ];
  const tableId = nextTableId("tc-table");

  const body = rows
    .map((row) => {
      const src = sourceDetails(whatTestedSources(row), "מקור לניסוח ולרשומת TCID");
      const runStatus = renderRunStatusControls(row, { profileKey: settings.profileKey, compact: true });
      const membership = renderProfileMembershipBlock(row);
      const preconditions = runPreconditionsData(row).has_conditions ? renderRunPreconditionsBlock(row) : "";
      return `
      <tr data-searchable>
        <td><code>${esc(row.tcid || "")}</code></td>
        <td>${esc(row.category || "")}</td>
        <td>${esc(row.active_date || "")}</td>
        <td>${renderWhatTestedBlock(row, { includeSources: false })}</td>
        <td>${runStatus}</td>
        <td><div class="tcid-table-collapsible">${membership}${preconditions}</div></td>
        <td>${src}</td>
      </tr>
    `;
    })
    .join("");

  const table = `
    <div class="table-tools">${columnHelpToggle(tableId)}</div>
    <div class="table-wrap">
      <table id="${esc(tableId)}">
        <thead>
          <tr>
            ${columns
              .map((col) => `<th>${columnHead(col.label, col.key, col.technical)}</th>`)
              .join("")}
          </tr>
          ${columnHelpRow(columns)}
        </thead>
        <tbody>${body}</tbody>
      </table>
    </div>
  `;

  if (!settings.collapsed) return `<h3>${esc(title)}</h3>${table}`;

  return `
    <details>
      <summary>${esc(title)} (${rows.length})</summary>
      <div class="small muted" style="margin:8px 0;">ברירת המחדל מוצגת בעברית מאומתת. לחיצה על EN בכל תא חושפת את הניסוח האנגלי הרשמי.</div>
      ${table}
    </details>
  `;
}

function runtimeProfileDelta(profileId) {
  const snapshots = runtimeHistoryEntries();
  if (!snapshots.length) return null;
  const latest = snapshots[0];
  const previous = snapshots.length > 1 ? snapshots[1] : null;
  if (!previous) {
    return {
      latest,
      previous: null,
      added: [],
      removed: [],
    };
  }
  const latestSet = new Set(runtimeProfileTcids(profileId, latest));
  const previousSet = new Set(runtimeProfileTcids(profileId, previous));
  const added = Array.from(latestSet).filter((tcid) => !previousSet.has(tcid)).sort((a, b) => a.localeCompare(b));
  const removed = Array.from(previousSet).filter((tcid) => !latestSet.has(tcid)).sort((a, b) => a.localeCompare(b));
  return { latest, previous, added, removed };
}

function renderProfileRuntimeDeltaCard(profileId) {
  const delta = runtimeProfileDelta(profileId);
  if (!delta) {
    return `
      <div class="card span-12 profile-delta-card">
        <h3>שינויי קונפיגורציה והשפעה על סט ההרצה</h3>
        <div class="small muted">לא נטען Snapshot Runtime, לכן כרגע אין בסיס לחישוב Delta עבור ${esc(profileId)}.</div>
      </div>
    `;
  }
  if (!delta.previous) {
    return `
      <div class="card span-12 profile-delta-card">
        <h3>שינויי קונפיגורציה והשפעה על סט ההרצה</h3>
        <div class="small muted">נמצא Snapshot יחיד בלבד. כדי לחשב Added/Removed צריך לפחות שני Snapshots בהיסטוריה.</div>
      </div>
    `;
  }

  const addedCount = delta.added.length;
  const removedCount = delta.removed.length;
  const latestTime = formatExactRuntimeTime(delta.latest.generated_at);
  const previousTime = formatExactRuntimeTime(delta.previous.generated_at);

  const addedRows = delta.added.length
    ? delta.added.map((tcid) => `<li><code>${esc(tcid)}</code></li>`).join("")
    : '<li class="muted">לא נוספו TCID.</li>';
  const removedRows = delta.removed.length
    ? delta.removed.map((tcid) => `<li><code>${esc(tcid)}</code></li>`).join("")
    : '<li class="muted">לא הוסרו TCID.</li>';

  return `
    <div class="card span-12 profile-delta-card">
      <h3>שינויי קונפיגורציה והשפעה על סט ההרצה</h3>
      <div class="small muted">השוואה בין שני Snapshots אחרונים עבור ${esc(profileId)} בלבד.</div>
      <div class="profile-delta-grid">
        <div class="profile-delta-kpi">
          <div class="profile-delta-label">נוספו</div>
          <div class="profile-delta-value">${esc(String(addedCount))}</div>
        </div>
        <div class="profile-delta-kpi">
          <div class="profile-delta-label">הוסרו</div>
          <div class="profile-delta-value">${esc(String(removedCount))}</div>
        </div>
      </div>
      <div class="small">Snapshot חדש: <code>${esc(latestTime)}</code></div>
      <div class="small">Snapshot קודם: <code>${esc(previousTime)}</code></div>
      <details class="profile-delta-details">
        <summary>TCID שנוספו (${esc(String(addedCount))})</summary>
        <ul class="src-list">${addedRows}</ul>
      </details>
      <details class="profile-delta-details">
        <summary>TCID שהוסרו (${esc(String(removedCount))})</summary>
        <ul class="src-list">${removedRows}</ul>
      </details>
    </div>
  `;
}

function renderProfilePanel(profileId, tableKey, tcGroups, icsGroups) {
  const profile = profileById(profileId);
  const rows = (DATA.tspc_tables && DATA.tspc_tables[tableKey]) || [];
  const split = splitMandatoryOptionalConditional(rows);
  const mappingRows = profileMappingRows(profileId);
  const mappingSummary = profileMappingSummary(profileId);
  const mappingView = (mappingViewState.profiles && mappingViewState.profiles[profileId]) || "tcid";
  const tcidRows = profileTcidRows(profileId);
  const profileDecisionStats = {
    total: tcidRows.length,
    expectedActive: tcidRows.filter((row) => summaryStatus(row) === "expected_active").length,
    expectedInactive: tcidRows.filter((row) => summaryStatus(row) === "expected_inactive").length,
    unknown: tcidRows.filter((row) => summaryStatus(row) === "unknown").length,
  };

  const tcBlocks = (tcGroups || [])
    .map((group) => {
      const dataRows = (DATA.tcs && DATA.tcs[group.key]) || [];
      return renderTcTable(group.title, dataRows, { collapsed: true, profileKey: profileId });
    })
    .join("");

  const icsBlocks = (icsGroups || [])
    .map(
      (group) => `
    <div class="card span-6">
      ${renderIcsReferences(group.title, (DATA.ics_refs && DATA.ics_refs[group.key]) || [])}
    </div>
  `
    )
    .join("");

  return `
    <div class="grid">
      <div class="card span-12">
        <h2 class="section-title">${esc(profileId)}</h2>
        <p class="section-intro">מה הערך שתקבל כאן: תמונת מצב מלאה של ההגדרות בפרופיל ${esc(profileId)}, והקישור שלהן לבדיקות התקן.</p>
      </div>

      <div class="card span-12 success">
        <b>הקשר עסקי קצר</b><br>
        ${esc((profile && profile.what_it_is) || "")}
        <br>
        ${esc((profile && profile.why_it_matters) || "")}
      </div>

      ${renderTsProfileSummary(profileId)}
      ${renderProfileRuntimeDeltaCard(profileId)}

      <div class="card span-4">
        <p class="kpi">${split.mandatory.length}</p>
        <p class="kpi-sub">פריטי חובה בקונפיגורציה</p>
      </div>
      <div class="card span-4">
        <p class="kpi">${split.optional.length}</p>
        <p class="kpi-sub">פריטים אופציונליים</p>
      </div>
      <div class="card span-4">
        <p class="kpi">${split.conditional.length}</p>
        <p class="kpi-sub">פריטים תלויי-תנאי</p>
      </div>

      <div class="card span-12">
        ${renderMappingControls(profileId, mappingView)}
        ${
          mappingView === "tcid"
            ? `
              ${renderDecisionHeader(`מה ירוץ כנראה בפרופיל ${profileId}`, profileDecisionStats)}
              <details class="notice small overview-help-box">
                <summary><b>איך לקרוא את רשימת הטסטים</b></summary>
                <ul class="src-list">
                  <li>המסך מציג קודם החלטה מהירה לכל טסט, ורק אחר כך פירוט טכני.</li>
                  <li>פילטרים מהירים מאפשרים להתמקד ב"חובה", "צפוי לרוץ" או "ללא מיפוי".</li>
                </ul>
              </details>
            `
            : `
              <div class="mapping-kpi-row">
                <div class="mapping-kpi"><b>#TSPC</b><span>${esc(String(mappingSummary.totals ? mappingSummary.totals.tspc_count : rows.length))}</span></div>
                <div class="mapping-kpi"><b>#TCID משויכים</b><span>${esc(String(mappingSummary.totals ? mappingSummary.totals.mapped_tcid_count : 0))}</span></div>
                <div class="mapping-kpi"><b>#ללא מיפוי</b><span>${esc(String(mappingSummary.totals ? mappingSummary.totals.unmapped_tspc_count : 0))}</span></div>
                <div class="mapping-kpi"><b>High</b><span>${esc(String(mappingSummary.totals ? mappingSummary.totals.high_count : 0))}</span></div>
              </div>
            `
        }
        ${
          mappingView === "tcid"
            ? renderTcidMappingTable(`מיפוי מאוחד TCID↔TSPC עבור ${profileId}`, tcidRows, {
                collapsed: false,
                bucket: null,
                scope: profileId,
                profileKey: profileId,
              })
            : renderMappingTable(`מיפוי מאוחד TSPC↔TCID עבור ${profileId}`, mappingRows, {
                collapsed: false,
                showBucket: true,
              })
        }
      </div>

      ${icsBlocks}

      <div class="card span-12">
        <details class="raw-data-details">
          <summary>Raw tables לשקיפות מלאה (TSPC ו-TCID המקוריים)</summary>
          <div class="raw-data-body">
            ${renderTspcTable(`TSPC raw של ${profileId}`, rows)}
            <div style="margin-top:12px;">${tcBlocks}</div>
          </div>
        </details>
      </div>
    </div>
  `;
}

function renderIoptPanel() {
  const intro = (DATA.ui_labels && DATA.ui_labels.iopt_intro) || "";
  const deepIntro = (DATA.ui_labels && DATA.ui_labels.iopt_deep_intro) || "";
  const qualityContext = (DATA.ui_labels && DATA.ui_labels.iopt_quality_context) || "";
  const relationToIssue = (DATA.ui_labels && DATA.ui_labels.iopt_relation_to_issues) || "";

  return `
    <div class="grid">
      <div class="card span-12">
        <h2 class="section-title">${esc((DATA.ui_labels && DATA.ui_labels.iopt_tab_title) || "IOPT")}</h2>
        <p class="section-intro">מה הערך שתקבל כאן: בדיקות שמוודאות שהפרופילים לא רק עובדים בנפרד, אלא גם משתלבים נכון יחד.</p>
      </div>

      <div class="card span-12 notice">
        <b>${termChip("IOPT", "IOPT")} מה זה ולמה זה חשוב</b><br>
        ${esc(intro)}
      </div>

      <div class="card span-12">
        <details class="iopt-details">
          <summary>פתח הסבר מלא: למה יש בדיקות IOPT, ומה הקשר לבעיות אינטגרציה</summary>
          <div class="iopt-details-body">
            <p>${esc(glossary("IOPT"))}</p>
            <p>${esc(deepIntro)}</p>
            <p>${esc(qualityContext)}</p>
            <p>${esc(relationToIssue)}</p>
          </div>
        </details>
      </div>

      <div class="card span-12">${renderTcTable("בדיקות שילוב לפרופיל BAS (IOPT/BAS)", (DATA.tcs && DATA.tcs.iopt_bas) || [], { collapsed: true, profileKey: "IOPT/BAS" })}</div>
      <div class="card span-12">${renderTcTable("בדיקות שילוב לפרופיל DIS (IOPT/DIS)", (DATA.tcs && DATA.tcs.iopt_dis) || [], { collapsed: true, profileKey: "IOPT/DIS" })}</div>
      <div class="card span-12">${renderTcTable("בדיקות שילוב לפרופיל HRS (IOPT/HRS)", (DATA.tcs && DATA.tcs.iopt_hrs) || [], { collapsed: true, profileKey: "IOPT/HRS" })}</div>
      <div class="card span-12">${renderTcTable("בדיקות שילוב לפרופיל HID (IOPT/HID)", (DATA.tcs && DATA.tcs.iopt_hid) || [], { collapsed: true, profileKey: "IOPT/HID" })}</div>
    </div>
  `;
}

function comparisonStatusLabel(status) {
  if (status === "match") return "תואם";
  if (status === "partial") return "התאמה חלקית";
  if (status === "conflict") return "סתירה";
  if (status === "unverified") return "לא מאומת";
  return status || "-";
}

function comparisonStatusMeaning(status) {
  if (status === "match") return "הטענה באתר תואמת למסמך הרשמי.";
  if (status === "partial") return "רק חלק מהטענה נתמך במקור הרשמי, וחלק דורש דיוק/בדיקה נוספת.";
  if (status === "conflict") return "נמצאה סתירה בין האתר למסמך הרשמי.";
  if (status === "unverified") return "אין כרגע מקור רשמי מספיק כדי לאמת את הטענה.";
  return "ללא פירוש זמין.";
}

function comparisonStatusClass(status) {
  if (status === "match") return "mandatory";
  if (status === "partial") return "optional";
  if (status === "conflict") return "conditional";
  return "";
}

function renderComparisonPanel() {
  const comp = DATA.comparison || {};
  const findings = comp.findings || [];
  const summary = comp.summary || {};
  const profiles = ["DIS", "BAS", "HRS", "HID"];
  const allTopics = Array.from(new Set(findings.map((f) => f.topic).filter(Boolean))).sort();

  const statusOptions = [
    { value: "conflict", label: "סתירות בלבד" },
    { value: "partial", label: "התאמה חלקית בלבד" },
    { value: "unverified", label: "לא מאומת בלבד" },
    { value: "match", label: "תואם בלבד" },
    { value: "ALL", label: "כל הסטטוסים" },
  ];

  const filtered = findings.filter((item) => {
    if (comparisonState.status !== "ALL" && item.status !== comparisonState.status) return false;
    if (comparisonState.profile !== "ALL" && item.profile !== comparisonState.profile) return false;
    if (comparisonState.topic !== "ALL" && item.topic !== comparisonState.topic) return false;
    return true;
  });

  const profileCards = profiles
    .map((profile) => {
      const s = summary[profile] || {};
      return `
      <article class="comparison-kpi">
        <h4>${esc(profile)}</h4>
        <div class="small">${comparisonStatusLabel("conflict")}: ${esc(String(s.conflict || 0))}</div>
        <div class="small">${comparisonStatusLabel("partial")}: ${esc(String(s.partial || 0))}</div>
        <div class="small">${comparisonStatusLabel("unverified")}: ${esc(String(s.unverified || 0))}</div>
        <div class="small">${comparisonStatusLabel("match")}: ${esc(String(s.match || 0))}</div>
      </article>
    `;
    })
    .join("");

  const rows = filtered
    .map((item) => {
      const siteSrc = item.site_source && item.site_source.file ? sourceDetails([item.site_source], "מקור באתר") : "";
      const officialSrc =
        item.official_source && item.official_source.file ? sourceDetails([item.official_source], "מקור רשמי") : "";
      return `
      <tr data-searchable>
        <td>
          <span class="pill ${comparisonStatusClass(item.status)}">${esc(comparisonStatusLabel(item.status))}</span>
          <div class="small muted">${esc(comparisonStatusMeaning(item.status))}</div>
        </td>
        <td><b>${esc(item.profile || "-")}</b></td>
        <td><code>${esc(item.topic || "-")}</code></td>
        <td>
          ${esc(item.site_claim || "-")}
          ${siteSrc ? `<div class="small muted">${siteSrc}</div>` : ""}
        </td>
        <td>
          ${esc(item.official_evidence || "-")}
          ${officialSrc ? `<div class="small muted">${officialSrc}</div>` : ""}
        </td>
        <td>
          ${esc(item.impact_meaning || "-")}
          <div class="small"><b>המלצה:</b> ${esc(item.recommended_action || "-")}</div>
        </td>
      </tr>
    `;
    })
    .join("");

  const officialCards = profiles
    .map((profile) => {
      const src = (DATA.official_sources && DATA.official_sources[profile]) || {};
      const spec = src.spec || {};
      const ics = src.ics || {};
      const ts = src.ts || {};
      return `
      <article class="official-card">
        <h4>${esc(profile)}</h4>
        <div class="small">${sourceDetails([{ file: spec.file, note: "Specification" }], "Spec")}</div>
        <div class="small">${sourceDetails([{ file: ics.file, note: "ICS" }], "ICS")}</div>
        <div class="small">${sourceDetails([{ file: ts.file, note: "TS" }], "TS")}</div>
        <div class="small muted">Revision: ${esc((ics.meta && ics.meta.Revision) || (spec.meta && spec.meta.Version) || "-")}</div>
      </article>
    `;
    })
    .join("");

  return `
    <div class="grid">
      <div class="card span-12">
        <h2 class="section-title">אימות מול מקורות רשמיים</h2>
        <p class="section-intro">השוואה שיטתית בין הטענות המוצגות באתר לבין מסמכי הבסיס הרשמיים בתיקיות <code>docs/Profiles</code>.</p>
        <p class="small muted">ברירת מחדל: סינון על סתירות בלבד.</p>
      </div>

      <div class="card span-12 notice small">
        <b>איך לקרוא את הסטטוסים?</b>
        <ul class="src-list">
          <li><b>תואם</b>: הטענה באתר נתמכת במלואה במקור הרשמי.</li>
          <li><b>התאמה חלקית</b>: רק חלק מהטענה נתמך; השאר דורש ניסוח מדויק יותר או מקור נוסף.</li>
          <li><b>סתירה</b>: נמצא פער ישיר בין האתר למקור הרשמי.</li>
          <li><b>לא מאומת</b>: אין כרגע ראיה רשמית מספקת.</li>
        </ul>
      </div>

      <div class="card span-12 comparison-kpi-grid">${profileCards}</div>

      <div class="card span-12">
        <h3>מקורות רשמיים פעילים</h3>
        <div class="official-grid">${officialCards}</div>
      </div>

      <div class="card span-12 comparison-filters">
        <label>
          סטטוס
          <select id="comparisonStatusFilter">
            ${statusOptions
              .map(
                (option) =>
                  `<option value="${esc(option.value)}" ${
                    comparisonState.status === option.value ? "selected" : ""
                  }>${esc(option.label)}</option>`
              )
              .join("")}
          </select>
        </label>
        <label>
          פרופיל
          <select id="comparisonProfileFilter">
            <option value="ALL" ${comparisonState.profile === "ALL" ? "selected" : ""}>כל הפרופילים</option>
            ${profiles
              .map(
                (profile) =>
                  `<option value="${esc(profile)}" ${comparisonState.profile === profile ? "selected" : ""}>${esc(
                    profile
                  )}</option>`
              )
              .join("")}
          </select>
        </label>
        <label>
          נושא
          <select id="comparisonTopicFilter">
            <option value="ALL" ${comparisonState.topic === "ALL" ? "selected" : ""}>כל הנושאים</option>
            ${allTopics
              .map(
                (topic) =>
                  `<option value="${esc(topic)}" ${comparisonState.topic === topic ? "selected" : ""}>${esc(
                    topic
                  )}</option>`
              )
              .join("")}
          </select>
        </label>
      </div>

      <div class="card span-12">
        <h3>מטריצת ממצאים (${filtered.length})</h3>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>סטטוס</th>
                <th>פרופיל</th>
                <th>נושא</th>
                <th>מה כתוב באתר</th>
                <th>מה כתוב במקור הרשמי</th>
                <th>משמעות והמלצה</th>
              </tr>
            </thead>
            <tbody>${rows || '<tr><td colspan="6" class="muted">אין ממצאים להצגה עבור הפילטרים שנבחרו.</td></tr>'}</tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

function renderRuntimePanel() {
  const snapshots = runtimeHistoryEntries();
  const runtime = runtimePanelSelectedSnapshot();
  const runtimeMeta = (DATA.meta && DATA.meta.active_runtime) || {};
  const profiles = ["DIS", "BAS", "HRS", "HID"];
  const available = !!runtime.available;
  const selectedProfile = runtimePanelState.profile || "ALL";
  const activeProfiles = selectedProfile === "ALL" ? profiles : profiles.filter((profile) => profile === selectedProfile);

  const summaryCards = profiles
    .map((profile) => {
      const activeCount = runtimeProfileCount(profile, runtime);
      const totalCount = profileTcs(profile).length;
      return `
        <article class="comparison-kpi">
          <h4>${esc(profile)}</h4>
          <div class="small"><b>Active ב-Snapshot:</b> ${esc(String(activeCount))}</div>
          <div class="small"><b>סה״כ ב-TCRL:</b> ${esc(String(totalCount))}</div>
        </article>
      `;
    })
    .join("");

  const activeRows = [];
  activeProfiles.forEach((profile) => {
    const tcMap = new Map(profileTcs(profile).map((row) => [row.tcid, row]));
    runtimeProfileTcids(profile, runtime).forEach((tcid) => {
      const tc = tcMap.get(tcid) || {};
      const tcSource = tc.source && tc.source.file ? sourceDetails([tc.source], "מקור TCRL") : '<span class="muted">אין מקור זמין</span>';
      activeRows.push(`
        <tr data-searchable>
          <td><b>${esc(profile)}</b></td>
          <td><code>${esc(tcid)}</code></td>
          <td>${esc(tc.category || "-")}</td>
          <td>${esc(tc.desc || "-")}</td>
          <td>${tcSource}</td>
        </tr>
      `);
    });
  });

  const snapshotOptions = snapshots
    .map((entry, index) => {
      const id = runtimeSnapshotUiId(entry, index);
      const dateText = formatExactRuntimeTime(entry.generated_at);
      const label = `${dateText} | ${entry.file || "-"}`;
      return `<option value="${esc(id)}" ${runtimePanelState.snapshotId === id ? "selected" : ""}>${esc(label)}</option>`;
    })
    .join("");

  const historyRows = snapshots
    .map((entry, index) => {
      const counts = profiles
        .map((profile) => `${profile}: ${runtimeProfileCount(profile, entry)}`)
        .join(" · ");
      return `
        <tr data-searchable>
          <td>${esc(String(index + 1))}</td>
          <td><code>${esc(formatExactRuntimeTime(entry.generated_at))}</code></td>
          <td><code>${esc(entry.file || "-")}</code></td>
          <td>${esc(counts)}</td>
          <td><code>${esc(entry.workspace || "-")}</code></td>
        </tr>
      `;
    })
    .join("");

  return `
    <div class="grid">
      <div class="card span-12">
        <h2 class="section-title">תוצאות הרצת PTS</h2>
        <p class="section-intro">
          כל מה שקשור לריצה בפועל מרוכז בלשונית הזו בלבד: סטטוס snapshot ורשימת
          <code>TCID</code> פעילים מתוך PTS.
        </p>
      </div>

      <div class="card span-12 notice small">
        <b>מה זה Snapshot?</b>
        זהו קובץ נתונים (JSON) שמיוצא מה-PTS עם רשימת בדיקות פעילות.
        זה לא צילום מסך.
      </div>

      <div class="card span-12 ${available ? "success" : "warning"}">
        <b>סטטוס Snapshot:</b>
        ${
          available
            ? `נטען בהצלחה מקובץ <code>${esc(runtime.file || "-")}</code> בתאריך <code>${esc(
                formatExactRuntimeTime(runtime.generated_at)
              )}</code>.`
            : "לא נטען Snapshot Runtime. לכן אין כאן רשימת TCID פעילים בפועל."
        }
        <div class="small muted" style="margin-top:8px;">
          Workspace: <code>${esc(runtime.workspace || "-")}</code> · Export Tool: <code>${esc(
            runtime.export_tool || "-"
          )}</code>
        </div>
      </div>

      <div class="card span-12 comparison-filters">
        <label>
          Snapshot להצגה
          <select id="runtimeSnapshotFilter">
            ${snapshotOptions || '<option value="">אין Snapshot זמין</option>'}
          </select>
        </label>
        <label>
          פרופיל
          <select id="runtimeProfileFilter">
            <option value="ALL" ${selectedProfile === "ALL" ? "selected" : ""}>כל הפרופילים</option>
            ${profiles
              .map(
                (profile) =>
                  `<option value="${esc(profile)}" ${selectedProfile === profile ? "selected" : ""}>${esc(profile)}</option>`
              )
              .join("")}
          </select>
        </label>
      </div>

      <div class="card span-12 comparison-kpi-grid">${summaryCards}</div>

      <div class="card span-12">
        <h3>היסטוריית Snapshots (${snapshots.length})</h3>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>זמן יצירה מדויק</th>
                <th>קובץ Snapshot</th>
                <th>Active TCID לפי פרופיל</th>
                <th>Workspace</th>
              </tr>
            </thead>
            <tbody>${historyRows || '<tr><td colspan="5" class="muted">אין היסטוריית Snapshot להצגה.</td></tr>'}</tbody>
          </table>
        </div>
      </div>

      <div class="card span-12">
        <h3>מקור טכני לייצוא Runtime</h3>
        ${sourceDetails(
          [
            { file: runtimeMeta.file, line: runtimeMeta.line_get_tc, note: "הפקת רשימת בדיקות בזמן ריצה" },
            { file: runtimeMeta.file, line: runtimeMeta.line_is_active, note: "בדיקת אקטיביות בדיקות" },
            { file: runtime.file, note: "קובץ Snapshot שנקלט לדוח" },
          ],
          "פתח מקורות Runtime"
        )}
      </div>

      <div class="card span-12">
        <h3>TCID פעילים מתוך Snapshot (${activeRows.length})</h3>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>פרופיל</th>
                <th>TCID פעיל</th>
                <th>קטגוריה</th>
                <th>תיאור</th>
                <th>מקור</th>
              </tr>
            </thead>
            <tbody>${activeRows.join("") || '<tr><td colspan="5" class="muted">אין TCID פעילים להצגה.</td></tr>'}</tbody>
          </table>
        </div>
      </div>
    </div>
  `;
}

function renderSourcesPanel() {
  const workspaceFile = DATA.meta && DATA.meta.workspace && DATA.meta.workspace.file;
  const formula = DATA.meta && DATA.meta.tspc_formula;
  const icsFiles = Object.values((DATA.meta && DATA.meta.ics_files) || {});

  return `
    <div class="grid">
      <div class="card span-12">
        <h2 class="section-title">מקורות</h2>
        <p class="section-intro">מה הערך שתקבל כאן: שקיפות מלאה לגבי הקבצים והשורות שעליהם נשען הדוח.</p>
      </div>

      <div class="card span-12">
        <h3>קבצי מקור מרכזיים</h3>
        <p class="small muted">
          כל ההפניות מסוג Workspace בדוח נלקחו מקובץ יחיד ועדכני: <code>${esc(workspaceFile || "")}</code>.
        </p>
        ${sourceDetails(
          [
            { file: workspaceFile, note: "Workspace עם הגדרות PICS/PIXIT" },
            { file: formula && formula.file, line: formula && formula.line_formula, note: "נוסחת יצירת מזהי TSPC" },
          ],
          "פתח רשימת מקורות מרכזיים"
        )}
      </div>

      <div class="card span-12">
        <h3>מסמכי ICS שנעשה בהם שימוש</h3>
        ${sourceDetails(icsFiles.map((file) => ({ file, note: "מסמך ICS" })), "פתח רשימת קבצי ICS")}
      </div>

      <div class="card span-12">
        <h3>קישורים רשמיים (Bluetooth SIG)</h3>
        <ul class="src-list">
          ${(DATA.links || [])
            .map(
              (link) =>
                `<li><a href="${esc(link.url)}" target="_blank" rel="noopener">${esc(link.title)}</a></li>`
            )
            .join("")}
        </ul>
      </div>
    </div>
  `;
}

function renderProfileFromConfig(profileId, root) {
  const cfg = PROFILE_PANEL_CONFIG[profileId];
  if (!cfg || !root) return;
  root.innerHTML = renderProfilePanel(profileId, cfg.tableKey, cfg.tcGroups, cfg.icsGroups);
}

function rerenderOverviewPanel() {
  const overview = document.getElementById("overviewContent");
  if (!overview) return;
  overview.innerHTML = renderOverviewPanel();
  bindOverviewActions();
  applySearch();
}

function rerenderProfilePanel(profileId) {
  const cfg = PROFILE_PANEL_CONFIG[profileId];
  if (!cfg) return;
  const root = document.getElementById(cfg.contentId);
  if (!root) return;
  renderProfileFromConfig(profileId, root);
  applySearch();
}

function rerenderRuntimePanel() {
  const root = document.getElementById("runtimeContent");
  if (!root) return;
  root.innerHTML = renderRuntimePanel();
  bindRuntimeActions();
  applySearch();
}

function fillPanels() {
  const overview = document.getElementById("overviewContent");
  const iopt = document.getElementById("ioptContent");
  const runtime = document.getElementById("runtimeContent");
  const comparison = document.getElementById("comparisonContent");
  const sources = document.getElementById("sourcesContent");
  const glossaryDrawerContent = document.getElementById("glossaryDrawerContent");

  if (overview) overview.innerHTML = renderOverviewPanel();

  Object.entries(PROFILE_PANEL_CONFIG).forEach(([profileId, cfg]) => {
    const root = document.getElementById(cfg.contentId);
    if (!root) return;
    renderProfileFromConfig(profileId, root);
  });

  if (iopt) iopt.innerHTML = renderIoptPanel();
  if (runtime) runtime.innerHTML = renderRuntimePanel();
  if (comparison) comparison.innerHTML = renderComparisonPanel();
  if (sources) sources.innerHTML = renderSourcesPanel();
  if (glossaryDrawerContent) glossaryDrawerContent.innerHTML = renderGlossaryDrawerContent();

  bindOverviewActions();
  bindRuntimeActions();
  bindComparisonActions();
}

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
  panels.forEach((panel) => panel.classList.toggle("active", panel.id === `panel-${id}`));
  navButtons.forEach((button) => button.classList.toggle("active", button.dataset.panelTarget === id));
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
      if (!scope || (view !== "tcid" && view !== "tspc")) return;

      if (scope === "overview") {
        mappingViewState.overview = view;
        overviewState.expanded = false;
        rerenderOverviewPanel();
        return;
      }

      if (PROFILE_PANEL_CONFIG[scope]) {
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

fillPanels();
bindGlobalEvents();
initGlossaryDrawerWidthControls();
activatePanel("overview");
