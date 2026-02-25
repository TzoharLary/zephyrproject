const DATA = window.AUTOPTS_HUB_DATA || {};

const topTabsContainer = document.getElementById("hubTopTabsNav");
const quickStatusContainer = document.getElementById("hubQuickStatus");
const hubSearchInput = document.getElementById("hubSearchInput");

const state = {
  topTab: "BPS",
  profileSubtabs: {
    BPS: "status",
    WSS: "status",
    SCPS: "status",
  },
  taskBoardUi: {
    viewModeByProfile: { BPS: "overview", WSS: "overview", SCPS: "overview" },
    activeGroupByProfile: { BPS: "", WSS: "", SCPS: "" },
    expandedTaskByProfile: { BPS: null, WSS: null, SCPS: null },
    filtersByProfile: {
      BPS: { q: "", assignee: "", status: "", priority: "", category: "", stage: "", chip: "all" },
      WSS: { q: "", assignee: "", status: "", priority: "", category: "", stage: "", chip: "all" },
      SCPS: { q: "", assignee: "", status: "", priority: "", category: "", stage: "", chip: "all" },
    },
    sortByProfile: { BPS: "default", WSS: "default", SCPS: "default" },
  },
};

const GROUP_B_TASKS_API_PATH = "/api/group-b-tasks";
const TASK_STATUS_ORDER = ["todo", "in_progress", "blocked", "deferred", "done"];
const TASK_STAGE_ORDER = ["foundations", "service_layer", "logic_layer", "app_integration", "validation_tests", "closure_decisions", "uncategorized"];
const DEFAULT_TASK_ASSIGNEE = "tzohar";
const TASK_STATUS_LABELS = {
  todo: "לביצוע",
  in_progress: "בתהליך",
  done: "בוצע",
  blocked: "חסום",
  deferred: "נדחה",
};
const TASK_PRIORITY_LABELS = {
  high: "גבוהה",
  medium: "בינונית",
  low: "נמוכה",
};
const TASK_CATEGORY_LABELS = {
  logic: "לוגיקה",
  structure: "מבנה",
  tests: "בדיקות",
  integration: "אינטגרציה",
  docs: "תיעוד/החלטות",
};

const taskStateApi = {
  available: false,
  readOnly: true,
  loading: false,
  error: null,
  payload: {
    version: 1,
    updated_at: null,
    profiles: {
      BPS: { tasks: {} },
      WSS: { tasks: {} },
      SCPS: { tasks: {} },
    },
  },
};

let taskSaveTimer = null;
let pendingTaskSaveReason = "";

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (s) =>
    ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    })[s]
  );
}

function profileMapRows() {
  return ((DATA.group_b || {}).profile_map || {}).profiles || [];
}

function profileRow(profileId) {
  return profileMapRows().find((r) => String(r.profile_id || "").toUpperCase() === String(profileId || "").toUpperCase()) || {};
}

function uiLabel(profileId) {
  const row = profileRow(profileId);
  return row.ui_label || (profileId === "SCPS" ? "ScPS" : profileId);
}

function displayNameHe(profileId) {
  const row = profileRow(profileId);
  return row.display_name_he || uiLabel(profileId);
}

function sourceRef(source) {
  if (!source) return "";
  if (source.url) {
    const title = source.title || source.url;
    return `<a href="${esc(source.url)}" target="_blank" rel="noopener">${esc(title)}</a>`;
  }
  if (source.file) {
    const line = source.line == null ? "" : `:${source.line}`;
    return `<code>${esc(`${source.file}${line}`)}</code>`;
  }
  if (source.note) return `<span>${esc(source.note)}</span>`;
  return "";
}

function renderSourceItem(source) {
  if (!source) return "";
  const bits = [];
  const main = sourceRef(source);
  if (main) bits.push(main);
  if (source.retrieved_at) bits.push(`<span class="muted"><code>retrieved:${esc(source.retrieved_at)}</code></span>`);
  if (source.note) bits.push(`<span>${esc(source.note)}</span>`);
  return bits.join(" · ");
}

function sourceDetails(items, label = "מקורות") {
  const safe = (items || []).filter((x) => x && (x.file || x.url || x.note));
  if (!safe.length) return '<span class="muted">אין מקור זמין</span>';
  const list = safe.map((src) => `<li>${renderSourceItem(src)}</li>`).join("");
  return `<details class="src-details"><summary>${esc(label)}</summary><ul class="src-list">${list}</ul></details>`;
}

function pill(text, kind = "") {
  const cls = kind ? ` pill ${kind}` : "pill";
  return `<span class="${cls}">${esc(text)}</span>`;
}

function confidencePill(confidence) {
  const c = String(confidence || "").toLowerCase();
  if (c === "high") return pill("מאומת", "mandatory");
  if (c === "medium") return pill("בינוני", "optional");
  if (c === "low") return pill("נמוך", "conditional");
  return pill(confidence || "לא ידוע");
}

function statusPill(status) {
  const s = String(status || "");
  if (s === "high") return pill("גבוה", "mandatory");
  if (s === "medium") return pill("בינוני", "optional");
  if (s === "low") return pill("נמוך", "conditional");
  if (s === "none") return pill("לא נמצא", "conditional");
  if (s === "confirmed") return pill("מאומת", "mandatory");
  if (s === "inferred") return pill("מוסק", "optional");
  if (s === "needs_validation") return pill("דורש אימות", "conditional");
  if (s === "synced") return pill("סונכרן", "mandatory");
  if (s === "in_progress") return pill("בתהליך", "optional");
  if (s === "partial") return pill("חלקי", "optional");
  if (s === "draft") return pill("טיוטה", "optional");
  if (s === "missing") return pill("חסר", "conditional");
  if (s === "present") return pill("קיים", "optional");
  if (s === "scaffold") return pill("טיוטת שלד", "optional");
  if (s === "open") return pill("פתוח", "conditional");
  if (s === "resolved") return pill("נסגר", "mandatory");
  if (s === "deferred_phase2") return pill("נדחה ל-Phase 2", "optional");
  if (s === "reviewed") return pill("נסקר", "mandatory");
  if (s === "ready") return pill("מוכן", "mandatory");
  if (s === "blocked") return pill("חסום", "conditional");
  if (s) return pill(s);
  return pill("—");
}

function boolPill(flag, yes = "כן", no = "לא") {
  return flag ? pill(yes, "mandatory") : pill(no, "conditional");
}

function renderListOrMuted(items, emptyText = "אין נתונים") {
  const rows = (items || []).filter(Boolean);
  if (!rows.length) return `<p class="muted">${esc(emptyText)}</p>`;
  return `<ul class="compact-list">${rows.map((x) => `<li data-searchable="true">${esc(String(x))}</li>`).join("")}</ul>`;
}

function renderNamedObjectKv(obj, labels = {}) {
  if (!obj || typeof obj !== "object" || Array.isArray(obj) || !Object.keys(obj).length) {
    return '<p class="muted">אין נתונים</p>';
  }
  return `
    <div class="kv-grid compact">
      ${Object.entries(obj).map(([k, v]) => {
        const label = labels[k] || k;
        if (Array.isArray(v)) return `<div><span>${esc(label)}</span><strong>${esc(String(v.length))}</strong></div>`;
        if (typeof v === "object" && v !== null) return `<div><span>${esc(label)}</span><strong>אובייקט</strong></div>`;
        return `<div><span>${esc(label)}</span><strong>${esc(String(v))}</strong></div>`;
      }).join("")}
    </div>
  `;
}

function profileTaskTemplates(profileId) {
  return ((((DATA.group_b || {}).current_work || {}).profiles || {})[profileId] || {}).task_templates || [];
}

function profileTaskTemplateById(profileId, taskId) {
  return profileTaskTemplates(profileId).find((t) => String(t.task_id || "") === String(taskId || "")) || null;
}

function profileTaskState(profileId) {
  const profiles = (taskStateApi.payload && taskStateApi.payload.profiles) || {};
  return (profiles[profileId] && profiles[profileId].tasks) || {};
}

function defaultTaskStateFromTemplate(tpl) {
  return {
    assignee: tpl.default_assignee || "",
    status: tpl.default_status || "todo",
    priority: tpl.suggested_priority || "medium",
    notes: "",
    blocked_reason: "",
    depends_on: [],
    updated_at: null,
    updated_by: tpl.default_assignee || "",
  };
}

function mergedTasksForProfile(profileId) {
  const templates = profileTaskTemplates(profileId);
  const stateMap = profileTaskState(profileId);
  return templates.map((tpl) => {
    const taskId = String(tpl.task_id || "");
    const override = stateMap[taskId] && typeof stateMap[taskId] === "object" ? stateMap[taskId] : {};
    const merged = { ...defaultTaskStateFromTemplate(tpl), ...override };
    return {
      ...tpl,
      current: merged,
      task_id: taskId,
      parent_task_id: tpl.parent_task_id || null,
    };
  });
}

function taskSummaryFromMerged(tasks) {
  const byStatus = { todo: 0, in_progress: 0, done: 0, blocked: 0, deferred: 0 };
  const byPriority = { high: 0, medium: 0, low: 0 };
  (tasks || []).forEach((t) => {
    const st = String((t.current || {}).status || "todo");
    const pr = String((t.current || {}).priority || "medium");
    if (Object.prototype.hasOwnProperty.call(byStatus, st)) byStatus[st] += 1;
    if (Object.prototype.hasOwnProperty.call(byPriority, pr)) byPriority[pr] += 1;
  });
  return {
    total: (tasks || []).length,
    done: byStatus.done,
    in_progress: byStatus.in_progress,
    blocked: byStatus.blocked,
    deferred: byStatus.deferred,
    byStatus,
    byPriority,
  };
}

function setTaskApiError(errorText) {
  taskStateApi.error = errorText ? String(errorText) : null;
}

async function loadGroupBTasksState() {
  taskStateApi.loading = true;
  try {
    const resp = await fetch(GROUP_B_TASKS_API_PATH, { cache: "no-store" });
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }
    const payload = await resp.json();
    if (!payload || typeof payload !== "object") {
      throw new Error("Invalid payload");
    }
    const profiles = payload.profiles && typeof payload.profiles === "object" ? payload.profiles : {};
    taskStateApi.payload = {
      version: Number(payload.version || 1),
      updated_at: payload.updated_at || null,
      profiles: {
        BPS: profiles.BPS && typeof profiles.BPS === "object" ? profiles.BPS : { tasks: {} },
        WSS: profiles.WSS && typeof profiles.WSS === "object" ? profiles.WSS : { tasks: {} },
        SCPS: profiles.SCPS && typeof profiles.SCPS === "object" ? profiles.SCPS : { tasks: {} },
      },
    };
    taskStateApi.available = true;
    taskStateApi.readOnly = false;
    setTaskApiError(null);
  } catch (err) {
    taskStateApi.available = false;
    taskStateApi.readOnly = true;
    setTaskApiError(`שמירת משימות מושבתת (אין שרת או API זמין: ${err && err.message ? err.message : err})`);
  } finally {
    taskStateApi.loading = false;
  }
}

function ensureTaskProfileState(profileId) {
  if (!taskStateApi.payload || typeof taskStateApi.payload !== "object") {
    taskStateApi.payload = { version: 1, updated_at: null, profiles: {} };
  }
  if (!taskStateApi.payload.profiles || typeof taskStateApi.payload.profiles !== "object") {
    taskStateApi.payload.profiles = {};
  }
  if (!taskStateApi.payload.profiles[profileId] || typeof taskStateApi.payload.profiles[profileId] !== "object") {
    taskStateApi.payload.profiles[profileId] = { tasks: {} };
  }
  if (!taskStateApi.payload.profiles[profileId].tasks || typeof taskStateApi.payload.profiles[profileId].tasks !== "object") {
    taskStateApi.payload.profiles[profileId].tasks = {};
  }
  return taskStateApi.payload.profiles[profileId].tasks;
}

function updateTaskStateValue(profileId, taskId, field, value) {
  const tasks = ensureTaskProfileState(profileId);
  const tpl = profileTaskTemplateById(profileId, taskId);
  const current = tasks[taskId] && typeof tasks[taskId] === "object" ? tasks[taskId] : {};
  const next = { ...(tpl ? defaultTaskStateFromTemplate(tpl) : {}), ...current, [field]: value };
  if (field === "status" && value !== "blocked") {
    next.blocked_reason = "";
  }
  next.updated_at = new Date().toISOString();
  next.updated_by = String(next.assignee || "manual");
  tasks[taskId] = next;
}

function normalizeTaskFieldValue(field, rawValue) {
  if (field === "depends_on") {
    return String(rawValue || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean);
  }
  return rawValue;
}

async function saveGroupBTasksState(reason = "") {
  if (!taskStateApi.available || taskStateApi.readOnly) return false;
  const payload = {
    version: Number((taskStateApi.payload || {}).version || 1),
    updated_at: (taskStateApi.payload || {}).updated_at || null,
    profiles: (taskStateApi.payload || {}).profiles || {},
  };
  try {
    const resp = await fetch(GROUP_B_TASKS_API_PATH, {
      method: "PUT",
      headers: { "Content-Type": "application/json; charset=utf-8" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) {
      const text = await resp.text();
      throw new Error(`HTTP ${resp.status} ${text}`);
    }
    taskStateApi.available = true;
    taskStateApi.readOnly = false;
    setTaskApiError(null);
    taskStateApi.payload.updated_at = new Date().toISOString();
    pendingTaskSaveReason = "";
    return true;
  } catch (err) {
    taskStateApi.available = false;
    taskStateApi.readOnly = true;
    setTaskApiError(`שמירת משימות נכשלה${reason ? ` (${reason})` : ""}: ${err && err.message ? err.message : err}`);
    return false;
  }
}

function scheduleTaskSave(reason = "update") {
  pendingTaskSaveReason = reason;
  if (taskSaveTimer) {
    clearTimeout(taskSaveTimer);
  }
  taskSaveTimer = setTimeout(async () => {
    taskSaveTimer = null;
    const ok = await saveGroupBTasksState(pendingTaskSaveReason);
    if (!ok) {
      renderProfilePanel("BPS");
      renderProfilePanel("WSS");
      renderProfilePanel("SCPS");
    } else if (["BPS", "WSS", "SCPS"].includes(state.topTab)) {
      renderProfilePanel(state.topTab);
    }
  }, 500);
}

function taskStatusLabel(status) {
  return TASK_STATUS_LABELS[String(status || "")] || String(status || "todo");
}

function taskPriorityLabel(priority) {
  return TASK_PRIORITY_LABELS[String(priority || "")] || String(priority || "medium");
}

function profileCurrentWorkVm(profileId) {
  return ((((DATA.group_b || {}).current_work || {}).profiles) || {})[profileId] || {};
}

function profileTaskGroups(profileId) {
  const vm = profileCurrentWorkVm(profileId);
  return Array.isArray(vm.task_groups) ? vm.task_groups : [];
}

function taskBoardUiProfileState(profileId) {
  if (!state.taskBoardUi) state.taskBoardUi = { viewModeByProfile: {}, activeGroupByProfile: {}, expandedTaskByProfile: {}, filtersByProfile: {}, sortByProfile: {} };
  const ui = state.taskBoardUi;
  if (!ui.viewModeByProfile) ui.viewModeByProfile = {};
  if (!ui.activeGroupByProfile) ui.activeGroupByProfile = {};
  if (!ui.expandedTaskByProfile) ui.expandedTaskByProfile = {};
  if (!ui.filtersByProfile) ui.filtersByProfile = {};
  if (!ui.sortByProfile) ui.sortByProfile = {};
  if (!ui.viewModeByProfile[profileId]) ui.viewModeByProfile[profileId] = "overview";
  if (!(profileId in ui.activeGroupByProfile)) ui.activeGroupByProfile[profileId] = "";
  if (!(profileId in ui.expandedTaskByProfile)) ui.expandedTaskByProfile[profileId] = null;
  if (!ui.filtersByProfile[profileId]) {
    ui.filtersByProfile[profileId] = { q: "", assignee: "", status: "", priority: "", category: "", stage: "", chip: "all" };
  }
  if (!ui.sortByProfile[profileId]) ui.sortByProfile[profileId] = "default";
  return {
    viewMode: ui.viewModeByProfile[profileId],
    activeGroup: ui.activeGroupByProfile[profileId] || "",
    expandedTask: ui.expandedTaskByProfile[profileId] || null,
    filters: ui.filtersByProfile[profileId],
    sort: ui.sortByProfile[profileId] || "default",
  };
}

function setTaskBoardUiField(profileId, key, value) {
  taskBoardUiProfileState(profileId);
  if (key === "activeGroup") state.taskBoardUi.activeGroupByProfile[profileId] = value || "";
  else if (key === "expandedTask") state.taskBoardUi.expandedTaskByProfile[profileId] = value || null;
  else if (key === "sort") state.taskBoardUi.sortByProfile[profileId] = value || "default";
  else if (key === "viewMode") state.taskBoardUi.viewModeByProfile[profileId] = value || "overview";
}

function setTaskBoardFilter(profileId, field, value) {
  taskBoardUiProfileState(profileId);
  const filters = state.taskBoardUi.filtersByProfile[profileId];
  filters[field] = value == null ? "" : String(value);
  if (field !== "chip") filters.chip = "all";
}

function setTaskBoardChip(profileId, chip) {
  taskBoardUiProfileState(profileId);
  state.taskBoardUi.filtersByProfile[profileId].chip = chip || "all";
}

function toggleTaskBoardGroup(profileId, groupId) {
  taskBoardUiProfileState(profileId);
  const current = state.taskBoardUi.activeGroupByProfile[profileId] || "";
  const next = String(current) === String(groupId || "") ? "" : String(groupId || "");
  state.taskBoardUi.activeGroupByProfile[profileId] = next;
  state.taskBoardUi.expandedTaskByProfile[profileId] = null;
}

function toggleTaskBoardTaskCard(profileId, taskId) {
  taskBoardUiProfileState(profileId);
  const current = state.taskBoardUi.expandedTaskByProfile[profileId] || null;
  state.taskBoardUi.expandedTaskByProfile[profileId] = String(current) === String(taskId || "") ? null : String(taskId || "");
}

function _fallbackTaskGroupMeta(groupId) {
  const defs = {
    foundations: { label_he: "יסודות והכנה", summary_he: "הכנה, reviews, חוזים וחתימות מוכנות.", goal_he: "לסגור תשתית והכנות לפני מימוש." },
    service_layer: { label_he: "שכבת שירות", summary_he: "Service/GATT/CCC/API וקבצי שירות.", goal_he: "להעמיד שירות יציב ברמת GATT." },
    logic_layer: { label_he: "שכבת לוגיקה", summary_he: "התנהגות, flow ומדיניות.", goal_he: "לממש את הלוגיקה שנגזרה מהמחקר." },
    app_integration: { label_he: "אינטגרציית אפליקציה", summary_he: "Adapter/app integration ו-bring-up.", goal_he: "לחבר את המימוש למערכת/אפליקציה." },
    validation_tests: { label_he: "בדיקות ואימות", summary_he: "Smoke/PTS/AutoPTS ויעדי בדיקות.", goal_he: "לאמת Phase 1 לפי יעדי בדיקות." },
    closure_decisions: { label_he: "סגירת החלטות", summary_he: "Follow-ups והחלטות Phase 1/תיעוד.", goal_he: "לסגור חסמים והחלטות לפני סיום השלב." },
    uncategorized: { label_he: "לא משויך", summary_he: "משימות שעדיין לא שויכו לשלב.", goal_he: "לשייך את המשימות לשלב מתאים." },
  };
  return defs[groupId] || defs.uncategorized;
}

function _containsAnyText(text, words) {
  const hay = String(text || "").toLowerCase();
  return (words || []).some((w) => hay.includes(String(w || "").toLowerCase()));
}

function fallbackTaskGroupIdForTask(task, parentGroupId = "") {
  const explicit = String(task.task_group_id || task.task_group_override || "").trim();
  if (explicit) return explicit;
  if (parentGroupId) return parentGroupId;
  const derived = String(task.derived_from || "").toLowerCase();
  const category = String(task.category || "").toLowerCase();
  const text = `${task.title_he || ""} ${task.description_he || ""}`.toLowerCase();
  if (task.is_completed_seed || derived === "codex_completed") return "foundations";
  if (derived === "test_targets" || category === "tests") return "validation_tests";
  if (derived === "readiness") return "closure_decisions";
  if (category === "docs") {
    return _containsAnyText(text, ["phase 1", "review", "מוכנות", "חתימה", "החלטה", "signoff"]) ? "closure_decisions" : "foundations";
  }
  if (derived === "logic" || category === "logic") return "logic_layer";
  if (_containsAnyText(text, ["pts", "autopts", "smoke", "בדיקה"])) return "validation_tests";
  if (_containsAnyText(text, ["adapter", "app", "bring-up", "integration", "אינטגר"])) return "app_integration";
  if (_containsAnyText(text, ["gatt", "ccc", "service", "characteristic", "attribute", "שירות"])) return "service_layer";
  if (_containsAnyText(text, ["לוגיקה", "behavior", "policy", "flow", "gating"])) return "logic_layer";
  if (category === "integration") return _containsAnyText(text, ["phase 1", "מימוש"]) ? "service_layer" : "app_integration";
  if (category === "structure") return "service_layer";
  return "uncategorized";
}

function fallbackTaskGroupsForProfile(profileId, tasks) {
  const groupForTask = {};
  const rootsByGroup = {};
  (tasks || []).forEach((task) => {
    const parentId = task.parent_task_id || null;
    const groupId = fallbackTaskGroupIdForTask(task, parentId ? groupForTask[parentId] : "");
    groupForTask[task.task_id] = groupId;
    task.task_group_id = task.task_group_id || groupId;
    if (!parentId) {
      if (!rootsByGroup[groupId]) rootsByGroup[groupId] = [];
      rootsByGroup[groupId].push(task);
    }
  });
  const groups = [];
  TASK_STAGE_ORDER.forEach((groupId, idx) => {
    const roots = rootsByGroup[groupId] || [];
    if (!roots.length) return;
    const meta = _fallbackTaskGroupMeta(groupId);
    groups.push({
      group_id: groupId,
      label_he: meta.label_he,
      summary_he: meta.summary_he,
      goal_he: meta.goal_he,
      order: (idx + 1) * 10,
      task_ids: roots.map((t) => t.task_id),
      highlight_task_ids: roots.slice(0, 4).map((t) => t.task_id),
      sources: [],
    });
  });
  if (!profileTaskGroups(profileId).length) {
    console.warn(`[task-board] task_groups missing in hub-data for ${profileId}; using runtime fallback grouping`);
  }
  return groups;
}

function taskGroupsForProfileResolved(profileId, tasks) {
  const groups = profileTaskGroups(profileId);
  return (groups && groups.length) ? groups : fallbackTaskGroupsForProfile(profileId, tasks);
}

function buildTaskIndexes(tasks) {
  const byId = {};
  const childrenByParent = {};
  (tasks || []).forEach((task) => {
    byId[task.task_id] = task;
    const p = task.parent_task_id || "__root__";
    if (!childrenByParent[p]) childrenByParent[p] = [];
    childrenByParent[p].push(task);
  });
  return { byId, childrenByParent };
}

function taskStatusSortRank(status) {
  const idx = TASK_STATUS_ORDER.indexOf(String(status || ""));
  return idx === -1 ? TASK_STATUS_ORDER.length : idx;
}

function taskPrioritySortRank(priority) {
  const p = String(priority || "medium");
  if (p === "high") return 0;
  if (p === "medium") return 1;
  if (p === "low") return 2;
  return 3;
}

function applyTaskBoardChip(task, filters) {
  const chip = String(filters.chip || "all");
  const cur = task.current || {};
  const assignee = String(cur.assignee || "").trim().toLowerCase();
  const status = String(cur.status || "todo");
  const priority = String(cur.priority || "medium");
  if (chip === "all") return true;
  if (chip === "mine") return assignee === DEFAULT_TASK_ASSIGNEE;
  if (chip === "todo") return status === "todo";
  if (chip === "in_progress") return status === "in_progress";
  if (chip === "blocked") return status === "blocked";
  if (chip === "high") return priority === "high";
  if (chip === "unassigned") return !assignee;
  return true;
}

function taskMatchesBoardFilters(task, filters) {
  const cur = task.current || {};
  const q = String(filters.q || "").trim().toLowerCase();
  const assignee = String(cur.assignee || "").trim();
  const status = String(cur.status || "todo");
  const priority = String(cur.priority || "medium");
  const category = String(task.category || "");
  const stage = String(task.task_group_id || "");
  if (filters.assignee && String(filters.assignee) !== assignee) return false;
  if (filters.status && String(filters.status) !== status) return false;
  if (filters.priority && String(filters.priority) !== priority) return false;
  if (filters.category && String(filters.category) !== category) return false;
  if (filters.stage && String(filters.stage) !== stage) return false;
  if (!applyTaskBoardChip(task, filters)) return false;
  if (!q) return true;
  const text = `${task.task_id || ""} ${task.title_he || ""} ${task.description_he || ""} ${task.category || ""} ${assignee} ${cur.notes || ""}`.toLowerCase();
  return text.includes(q);
}

function descendantsOfTask(taskId, childrenByParent) {
  const out = [];
  const stack = [...(childrenByParent[taskId] || [])];
  while (stack.length) {
    const t = stack.shift();
    if (!t) continue;
    out.push(t);
    (childrenByParent[t.task_id] || []).forEach((c) => stack.push(c));
  }
  return out;
}

function firstActionableTaskGroupId(groups, tasksById) {
  for (const group of groups || []) {
    const hasActionable = (group.task_ids || []).some((tid) => {
      const t = tasksById[tid];
      const st = String(((t || {}).current || {}).status || "todo");
      return st !== "done" && st !== "deferred";
    });
    if (hasActionable) return group.group_id;
  }
  return (groups && groups[0] && groups[0].group_id) || "";
}

function topTabs() {
  return (DATA.navigation || {}).top_tabs || [];
}

function profileSubtabs() {
  return (DATA.navigation || {}).profile_subtabs || [];
}

function activePanel() {
  return document.querySelector(".hub-panel.active");
}

function applySearch() {
  const panel = activePanel();
  if (!panel) return;
  const q = String(hubSearchInput && hubSearchInput.value ? hubSearchInput.value : "").trim().toLowerCase();
  panel.querySelectorAll("[data-searchable]").forEach((el) => {
    const explicit = String(el.getAttribute("data-search-text") || "").toLowerCase();
    const text = explicit || String(el.innerText || "").toLowerCase();
    const ok = !q || text.includes(q);
    el.style.display = ok ? "" : "none";
  });
}

function activateTopTab(tabId) {
  state.topTab = tabId;
  document.querySelectorAll(".hub-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.getAttribute("data-top-tab") === tabId);
  });
  document.querySelectorAll("[data-hub-top-tab]").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-hub-top-tab") === tabId);
  });
  applySearch();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function setProfileSubtab(profileId, subtabId) {
  state.profileSubtabs[profileId] = subtabId;
  renderProfilePanel(profileId);
}

function renderTopTabsNav() {
  if (!topTabsContainer) return;
  topTabsContainer.innerHTML = topTabs()
    .map(
      (tab) => `
      <button
        type="button"
        class="hub-top-tab-btn ${state.topTab === tab.id ? "active" : ""}"
        data-hub-top-tab="${esc(tab.id)}"
      >${esc(tab.label)}</button>`
    )
    .join("");
}

function renderQuickStatus() {
  if (!quickStatusContainer) return;
  const groupB = DATA.group_b || {};
  const status = (groupB.status_tracker || {}).summary || {};
  const rows = ((groupB.status_tracker || {}).rows) || [];
  const profileRows = ["BPS", "WSS", "SCPS"]
    .map((pid) => rows.find((r) => r.profile_id === pid) || { profile_id: pid, ready_for_impl_phase1: false });
  quickStatusContainer.innerHTML = `
    <div class="quick-status-meaning">
      <p class="muted">מה חשוב כאן: כמה מתוך 3 הפרופילים כבר מוכנים להתחלת מימוש (Phase 1), ומה הסטטוס של כל פרופיל.</p>
    </div>
    <div class="quick-stat-grid">
      <div class="quick-stat"><span>מוכנים למימוש (Phase 1)</span><strong>${esc(String(status.ready_for_impl_phase1 || 0))}/${esc(String(status.profiles || 3))}</strong></div>
      <div class="quick-stat"><span>חוזה מימוש + יעדי בדיקות</span><strong>${esc(String(Math.min(status.implementation_contract_defined || 0, status.phase1_test_targets_defined || 0)))}/${esc(String(status.profiles || 3))}</strong></div>
    </div>
    <div class="quick-profile-list">
      ${profileRows.map((row) => `
        <div class="quick-profile-row" data-searchable="true" data-search-text="${esc(`${row.profile_id} ${uiLabel(row.profile_id)} ${displayNameHe(row.profile_id)}`)}">
          <div>
            <strong>${esc(uiLabel(row.profile_id))}</strong>
            <span class="muted">${esc(displayNameHe(row.profile_id))}</span>
          </div>
          <div>${boolPill(!!row.ready_for_impl_phase1, "מוכן למימוש", "עדיין בהכנה")}</div>
        </div>
      `).join("")}
    </div>
  `;
}

function renderProfileSubtabGuide(profileId, subtab) {
  const guides = {
    specs: {
      title: "מה יש כאן ולמה זה חשוב",
      text: "הלשונית הזו מראה אילו מסמכי מפרט רשמיים (Spec / TCRL / מסמכי עזר) כבר סונכרנו לפרופיל. משתמשים בה כדי לוודא שלא חסר חומר רשמי לפני מימוש.",
      bullets: [
        "אם חסר מסמך חשוב: עוצרים ומרעננים sync.",
        "אם הכל קיים: עוברים ללוגיקה/מבנה.",
      ],
    },
    logic: {
      title: "איך לקרוא את לשונית הלוגיקה",
      text: "הלשונית הזו מציגה רק שני דברים: אילו מקורות נחקרו כדי להבין את הלוגיקה, ומה סיכום הלוגיקה בפועל למימוש.",
      bullets: [
        "התחל ב'סיכום הלוגיקה של הפרופיל (תכלס)'.",
        "חזור ל'מקורות שנחקרו' רק אם אתה רוצה להבין מאיפה הסיכום נגזר.",
      ],
    },
    structure: {
      title: "איך לקרוא את לשונית המבנה",
      text: "הלשונית הזו מציגה רק שני דברים: אילו מקורות נחקרו כדי להבין מבנה, ומה מבנה המימוש המומלץ (קבצים + מבנה פנימי).",
      bullets: [
        "התחל ב'סיכום מבנה המימוש המומלץ'.",
        "השתמש ב'מקורות שנחקרו' רק כשצריך להבין למה המבנה הוצע כך.",
      ],
    },
    status: {
      title: "מה נותנת לשונית מצב עבודה נוכחי",
      text: "זו לשונית העבודה בפועל. כאן מנהלים משימות ותתי-משימות, רואים מה הבא, מה בוצע, ומה חסום — על בסיס הלוגיקה, המבנה וחוזה המימוש.",
      bullets: [
        "זו נקודת הכניסה המומלצת לכל פרופיל.",
        "עדכן בעלים/סטטוס/עדיפות כאן, והמערכת שומרת לקובץ דרך השרת המקומי.",
      ],
    },
  };
  const g = guides[subtab] || guides.specs;
  return `
    <section class="hub-card span-12 tab-guide-card" data-searchable="true" data-search-text="${esc(`${profileId} ${subtab} ${g.title} ${g.text}`)}">
      <h3>${esc(g.title)}</h3>
      <p>${esc(g.text)}</p>
      <ul class="compact-list">${(g.bullets || []).map((b) => `<li>${esc(b)}</li>`).join("")}</ul>
    </section>
  `;
}

function renderOverviewTab() {
  const meta = DATA.meta || {};
  const statusRows = (((DATA.group_b || {}).status_tracker || {}).rows) || [];
  const specRows = (((DATA.group_b || {}).spec_research || {}).rows) || [];
  const readinessSummary = (((DATA.group_b || {}).readiness_gates || {}).summary) || {};
  const qaMeta = ((DATA.group_b || {}).qa_meta) || {};

  const profileCards = statusRows
    .map((row) => {
      const pid = row.profile_id;
      return `
      <article class="hub-card profile-card" data-searchable="true" data-search-text="${esc(`${pid} ${row.display_name_he || ""} ${(row.gaps_he || []).join(" ")}`)}">
        <div class="profile-card-head">
          <h3>${esc(row.ui_label || pid)}</h3>
          ${statusPill(row.spec_sync_status)}
        </div>
        <p class="muted">${esc(row.display_name_he || "")}</p>
        <div class="kpi-row">
          <div><span>ארטיפקטים</span><strong>${esc(String(row.spec_artifacts || 0))}</strong></div>
          <div><span>לוגיקה</span><strong>${esc(String(row.logic_findings || 0))}</strong></div>
          <div><span>מבנה</span><strong>${esc(String(row.structure_findings || 0))}</strong></div>
        </div>
        <div class="row-actions">
          <button type="button" class="mini-btn" data-jump-profile="${esc(pid)}">פתח לשונית ${esc(row.ui_label || pid)}</button>
        </div>
        ${(row.gaps_he || []).length ? `<ul class="compact-list">${(row.gaps_he || []).map((g) => `<li>${esc(g)}</li>`).join("")}</ul>` : ""}
      </article>`;
    })
    .join("");

  const specTableRows = specRows
    .map((row) => {
      const s = row.summary || {};
      return `
      <tr data-searchable="true" data-search-text="${esc(`${row.ui_label || row.profile_id} ${row.display_name_he || ""}`)}">
        <td>${esc(row.ui_label || row.profile_id || "")}</td>
        <td>${esc(row.display_name_he || "")}</td>
        <td>${statusPill(row.sync_status)}</td>
        <td>${esc(String(s.artifact_count || 0))}</td>
        <td>${esc(String(s.tcrl_xlsx_total || 0))}</td>
        <td>${row.spec_page_url ? `<a href="${esc(row.spec_page_url)}" target="_blank" rel="noopener">עמוד spec</a>` : '<span class="muted">-</span>'}</td>
        <td>${sourceDetails(row.sources || [], "מקורות")}</td>
      </tr>`;
    })
    .join("");

  const root = document.getElementById("hubOverviewContent");
  if (!root) return;
  root.innerHTML = `
    <div class="hub-panel-grid">
      <section class="hub-card span-12">
        <h2>סקירה</h2>
        <p class="lead">${esc(meta.summary_he || "מרכז עבודה ל-AutoPTS + Group B.")}</p>
        <div class="meta-grid">
          <div><span>נוצר</span><code>${esc(meta.generated_date || "-")}</code></div>
          <div><span>Builder</span><code>${esc(meta.builder_script || "-")}</code></div>
          <div><span>Templates</span><code>${esc(meta.templates_root || "-")}</code></div>
          <div><span>Hub output</span><code>${esc(meta.hub_output_dir || "-")}</code></div>
        </div>
        ${sourceDetails(meta.sources || [], "מקורות meta")}
      </section>

      <section class="hub-card span-12">
        <h3>סטטוס מהיר לפרופילים (BPS / WSS / ScPS)</h3>
        <div class="cards-grid three">${profileCards}</div>
      </section>

      <section class="hub-card span-12">
        <h3>מחקר מפרטים (Specs): מצב סנכרון וארטיפקטים</h3>
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>פרופיל</th>
                <th>שם</th>
                <th>סטטוס סנכרון</th>
                <th>ארטיפקטים</th>
                <th>TCRL xlsx</th>
                <th>עמוד spec</th>
                <th>מקורות</th>
              </tr>
            </thead>
            <tbody>${specTableRows || '<tr><td colspan="7" class="muted">אין נתונים.</td></tr>'}</tbody>
          </table>
        </div>
      </section>

      <section class="hub-card span-12">
        <h3>מוכנות למימוש (Readiness gates) + QA</h3>
        <div class="cards-grid two">
          <article class="hub-card nested-card" data-searchable="true">
            <h4>סיכום readiness</h4>
            <div class="kv-grid compact">
              <div><span>Spec sync complete</span><strong>${esc(String(readinessSummary.spec_sync_complete || 0))}</strong></div>
              <div><span>Logic baseline</span><strong>${esc(String(readinessSummary.logic_analysis_baselined || 0))}</strong></div>
              <div><span>Structure baseline</span><strong>${esc(String(readinessSummary.structure_analysis_baselined || 0))}</strong></div>
              <div><span>Phase 1 subset decided</span><strong>${esc(String(readinessSummary.phase1_subset_decided || 0))}</strong></div>
              <div><span>Implementation contract</span><strong>${esc(String(readinessSummary.implementation_contract_defined || 0))}</strong></div>
              <div><span>Phase 1 test targets</span><strong>${esc(String(readinessSummary.phase1_test_targets_defined || 0))}</strong></div>
              <div><span>Phase 1 blockers closed/deferred</span><strong>${esc(String(readinessSummary.phase1_blockers_closed_or_deferred || 0))}</strong></div>
              <div><span>Review signoff complete</span><strong>${esc(String(readinessSummary.review_signoff_complete || 0))}</strong></div>
              <div><span>Logic reviewed</span><strong>${esc(String(readinessSummary.logic_analysis_reviewed || 0))}</strong></div>
              <div><span>Structure reviewed</span><strong>${esc(String(readinessSummary.structure_analysis_reviewed || 0))}</strong></div>
              <div><span>Ready for impl phase 1</span><strong>${esc(String(readinessSummary.ready_for_impl_phase1 || 0))}</strong></div>
            </div>
          </article>
          <article class="hub-card nested-card" data-searchable="true">
            <h4>QA / Smoke</h4>
            <div class="kv-grid compact">
              <div><span>מצב smoke</span>${statusPill(qaMeta.smoke_test_mode || "manual")}</div>
              <div><span>בדיקה אחרונה</span><code>${esc(qaMeta.last_smoke_test_at || "-")}</code></div>
            </div>
            ${(qaMeta.known_expected_console_errors || []).length ? `<ul class="compact-list">${(qaMeta.known_expected_console_errors || []).map((e) => `<li>${esc(e)}</li>`).join("")}</ul>` : ""}
            ${sourceDetails(qaMeta.sources || [], "מקורות QA meta")}
          </article>
        </div>
      </section>
    </div>
  `;
}

function renderAutoptsTab() {
  const root = document.getElementById("hubAutoptsContent");
  if (!root) return;
  const a = DATA.auto_pts_summary || {};
  const ov = a.overview || {};
  const qs = a.quickstart || {};
  const cli = a.cli || {};
  const layers = a.test_support_3_layers || {};
  const stacks = a.stacks || {};

  const scenarioBlocks = (qs.scenarios || [])
    .map(
      (sc) => `
      <details class="hub-detail" data-searchable="true" open>
        <summary>
          <span>${esc(sc.title || "-")}</span>
          <span class="muted">תרחיש הפעלה</span>
        </summary>
        <div class="detail-body">
          ${(sc.commands || [])
            .map(
              (cmd) => `
            <div class="cmd-block">
              <div class="cmd-label">${esc(cmd.when || "")}</div>
              <pre><code>${esc(cmd.command || "")}</code></pre>
            </div>`
            )
            .join("")}
          ${sourceDetails(sc.sources || [], "מקורות scenario")}
        </div>
      </details>`
    )
    .join("");

  const stackRows = (stacks.rows || [])
    .map(
      (r) => `
      <tr data-searchable="true" data-search-text="${esc(`${r.stack || ""} ${(r.profiles || []).join(" ")}`)}">
        <td>${esc(r.stack || "-")}</td>
        <td>${esc(String(r.profile_count || 0))}</td>
        <td>${esc((r.profiles || []).join(", ") || "-")}</td>
        <td>${sourceDetails(r.sources || [], "מקור")}</td>
      </tr>`
    )
    .join("");

  root.innerHTML = `
    <div class="hub-panel-grid">
      <section class="hub-card span-12">
        <h2>AutoPTS (תקציר ממוקד)</h2>
        <p class="lead">${esc(a.summary_he || "")}</p>
        <div class="cards-grid four">
          <div class="mini-kpi"><span>ארגומנטים ב-CLI</span><strong>${esc(String((cli.summary || {}).total || 0))}</strong></div>
          <div class="mini-kpi"><span>Stacks נתמכים</span><strong>${esc(String((stacks.rows || []).length || 0))}</strong></div>
          <div class="mini-kpi"><span>מלאי פרופילים</span><strong>${esc(String((a.profiles_inventory || {}).rows_count || 0))}</strong></div>
          <div class="mini-kpi"><span>תרחישי Quick Start</span><strong>${esc(String((qs.scenarios || []).length || 0))}</strong></div>
        </div>
        ${sourceDetails(a.sources || [], "מקורות AutoPTS")}
      </section>

      <section class="hub-card span-12">
        <h3>מה חשוב לנו להמשך Group B</h3>
        <ul class="compact-list">
          <li data-searchable="true">הבנת תשתית AutoPTS תומכת בהכנה לבדיקות עתידיות של הפרופילים החדשים, אך לא מחליפה מימוש שירותים עצמם.</li>
          <li data-searchable="true">בחירת טסטים ב-AutoPTS צריכה להיקרא תמיד ב-3 שכבות: כיסוי קוד, bundled workspaces, exact runtime list.</li>
          <li data-searchable="true">Exact runtime list עדיין תלוי Windows + PTS COM, ולכן מוצג כאן כהנחיות וכלים בלבד.</li>
        </ul>
      </section>

      <section class="hub-card span-12">
        <h3>3 שכבות תמיכה (תקציר)</h3>
        <div class="cards-grid three">
          <div class="layer-card" data-searchable="true">
            <h4>כיסוי קוד</h4>
            <p class="muted">סיכום נגזר מקוד modules/profile handlers.</p>
            <div class="kv-stack">
              <div><span>שורות matrix</span><code>${esc(String((((layers.code_support || {}).summary || {}).rows) || 0))}</code></div>
              <div><span>סיווגים</span><span>${esc(JSON.stringify((((layers.code_support || {}).summary || {}).by_classification) || {}))}</span></div>
            </div>
            ${sourceDetails((layers.code_support || {}).sources || [], "מקורות")}
          </div>
          <div class="layer-card" data-searchable="true">
            <h4>Bundled workspaces</h4>
            <p class="muted">מה נמצא ב-<code>.pqw6</code>/<code>.pts</code>/<code>.bqw</code> הכלולים.</p>
            <div class="kv-stack">
              <div><span>קבצים</span><code>${esc(String((((layers.bundled_workspaces || {}).summary || {}).workspace_files) || 0))}</code></div>
              <div><span>פורמטים</span><span>${esc(JSON.stringify((((layers.bundled_workspaces || {}).summary || {}).formats) || {}))}</span></div>
            </div>
            <ul class="compact-list">
              <li>פענוח ה-workspaces כאן הוא ברמת metadata בלבד.</li>
              <li>רשימת testcases פעילים מדויקת דורשת שאילתה ל-PTS runtime (COM).</li>
            </ul>
          </div>
          <div class="layer-card" data-searchable="true">
            <h4>Exact runtime</h4>
            <p class="muted">רשימה מדויקת דורשת PTS COM runtime.</p>
            <div class="chip-row">${((layers.exact_runtime || {}).platform_requirements || []).map((x) => pill(x)).join(" ")}</div>
            ${(layers.exact_runtime || {}).commands ? `<details class="hub-detail"><summary>פקודות עיקריות</summary><div class="detail-body">${(layers.exact_runtime || {}).commands.map((c) => `<pre><code>${esc(c.command || "")}</code></pre>`).join("")}</div></details>` : ""}
          </div>
        </div>
        ${sourceDetails(layers.sources || [], "מקורות 3 שכבות")}
      </section>

      <section class="hub-card span-12">
        <h3>Stacks נתמכים (תקציר)</h3>
        <div class="table-wrap">
          <table>
            <thead><tr><th>סטאק</th><th>כמות פרופילים</th><th>פרופילים</th><th>מקור</th></tr></thead>
            <tbody>${stackRows || '<tr><td colspan="4" class="muted">אין נתונים.</td></tr>'}</tbody>
          </table>
        </div>
        ${sourceDetails(stacks.sources || [], "מקורות stacks")}
      </section>

      <section class="hub-card span-12">
        <h3>Quick Start (תקציר שימוש)</h3>
        ${scenarioBlocks || '<p class="muted">אין scenarios להצגה.</p>'}
        ${sourceDetails(qs.sources || [], "מקורות Quick Start")}
      </section>
    </div>
  `;
}

function renderProfileSubtabs(profileId) {
  return `
    <div class="subtabs" role="tablist" aria-label="תתי לשוניות ${esc(uiLabel(profileId))}">
      ${profileSubtabs()
        .map(
          (tab) => `
          <button
            type="button"
            class="subtab-btn ${state.profileSubtabs[profileId] === tab.id ? "active" : ""}"
            data-profile-subtab="${esc(profileId)}:${esc(tab.id)}"
          >${esc(tab.label)}</button>`
        )
        .join("")}
    </div>
  `;
}

function renderProfileSpecs(profileId) {
  const spec = ((((DATA.group_b || {}).spec_research || {}).profiles) || {})[profileId] || {};
  const summary = spec.summary || {};
  const artifacts = spec.artifacts || [];
  const artifactRows = artifacts
    .map(
      (a) => `
      <tr data-searchable="true" data-search-text="${esc(`${a.kind || ""} ${a.name || ""}`)}">
        <td>${esc(a.kind || "-")}</td>
        <td><code>${esc(a.name || "-")}</code></td>
        <td>${a.is_dir ? "תיקייה" : "קובץ"}</td>
        <td>${esc(String(a.xlsx_count || a.size_bytes || "-"))}</td>
        <td>${a.sample_files ? `<details class="inline-detail"><summary>דוגמאות</summary><div class="detail-body"><ul class="src-list">${a.sample_files.map((p) => `<li><code>${esc(p)}</code></li>`).join("")}</ul></div></details>` : '<span class="muted">-</span>'}</td>
        <td>${sourceDetails(a.sources || [], "מקור")}</td>
      </tr>`
    )
    .join("");
  return `
    <div class="profile-sections">
      <section id="${profileId}-specs-summary" class="hub-card" data-searchable="true">
        <h3>מפרטים - תקציר</h3>
        <div class="kv-grid">
          <div><span>סטטוס סנכרון</span>${statusPill(spec.sync_status)}</div>
          <div><span>כותרת שזוהתה</span><strong>${esc(spec.resolved_title || "-")}</strong></div>
          <div><span>תיקיית spec</span><code>${esc(spec.spec_dir || "-")}</code></div>
          <div><span>ארטיפקטים</span><strong>${esc(String(summary.artifact_count || 0))}</strong></div>
          <div><span>TCRL xlsx</span><strong>${esc(String(summary.tcrl_xlsx_total || 0))}</strong></div>
          <div><span>קיים IXIT</span><strong>${(summary.has_ixit ? "כן" : "לא")}</strong></div>
        </div>
        <div class="row-actions">
          ${spec.spec_page_url ? `<a class="mini-btn linkish" href="${esc(spec.spec_page_url)}" target="_blank" rel="noopener">עמוד spec רשמי</a>` : ""}
        </div>
        ${(spec.notes || []).length ? `<ul class="compact-list">${(spec.notes || []).map((n) => `<li>${esc(n)}</li>`).join("")}</ul>` : ""}
        ${sourceDetails(spec.sources || [], "מקורות מפרטים")}
      </section>

      <section id="${profileId}-specs-artifacts" class="hub-card">
        <h3>ארטיפקטים שסונכרנו</h3>
        <div class="table-wrap">
          <table>
            <thead><tr><th>סוג</th><th>שם</th><th>טיפוס</th><th>גודל/כמות</th><th>פרטים</th><th>מקור</th></tr></thead>
            <tbody>${artifactRows || '<tr><td colspan="6" class="muted">אין ארטיפקטים להצגה.</td></tr>'}</tbody>
          </table>
        </div>
      </section>
    </div>
  `;
}

function renderProfileSpecsSimple(profileId) {
  const specP = ((((DATA.group_b || {}).specs_presentation || {}).profiles) || {})[profileId] || {};
  const groups = specP.groups || [];
  return `
    <div class="profile-sections">
      <section class="hub-card" data-searchable="true">
        <h3>מה סונכרן, מאיזה מקור, ומה זה נותן לנו</h3>
        <p class="muted">הלשונית הזו מיועדת להבנה מהירה של חומר המקור הרשמי שקיים לנו, ומה תפקיד כל קובץ/תיקייה בהכנה למימוש ולבדיקות.</p>
        <div class="kv-grid compact">
          <div><span>סטטוס סנכרון</span>${statusPill(specP.sync_status || "missing")}</div>
          <div><span>קבוצות מקור</span><strong>${esc(String(groups.length || 0))}</strong></div>
        </div>
        ${specP.spec_page_url ? `<div class="row-actions"><a class="mini-btn linkish" href="${esc(specP.spec_page_url)}" target="_blank" rel="noopener">עמוד spec רשמי</a></div>` : ""}
      </section>
      ${groups.map((g, idx) => `
        <section class="hub-card" data-searchable="true" data-search-text="${esc(`${g.source_label_he || ""} ${g.summary_he || ""}`)}">
          <details class="hub-detail" ${idx === 0 ? "open" : ""}>
            <summary>
              <span>${esc(g.source_label_he || `מקור ${idx + 1}`)}</span>
              <span class="muted">${esc(g.summary_he || "")}</span>
            </summary>
            <div class="detail-body">
              <div class="row-actions">
                ${g.source_url ? `<a class="mini-btn linkish" href="${esc(g.source_url)}" target="_blank" rel="noopener">פתח מקור</a>` : ""}
                ${g.source_kind ? pill(`source:${g.source_kind}`) : ""}
              </div>
              <div class="cards-grid two">
                ${(g.files || []).map((f) => `
                  <article class="hub-card nested-card spec-file-card" data-searchable="true" data-search-text="${esc(`${f.name || ""} ${f.what_it_is_he || ""} ${f.what_we_take_from_it_he || ""}`)}">
                    <h4><code>${esc(f.name || "-")}</code></h4>
                    <p class="muted">${esc(f.display_kind_he || (f.is_dir ? "תיקייה" : "קובץ"))}</p>
                    <div class="obs-row"><span>מה זה</span><p>${esc(f.what_it_is_he || "-")}</p></div>
                    <div class="obs-row"><span>מה לוקחים ממנו</span><p>${esc(f.what_we_take_from_it_he || "-")}</p></div>
                    ${f.relevance_he ? `<div class="chip-row">${pill(`רלוונטיות: ${f.relevance_he}`)}</div>` : ""}
                    ${f.path ? `<div class="mini-meta"><span>נתיב מסונכרן:</span> <code>${esc(f.path)}</code></div>` : ""}
                    ${sourceDetails(f.sources || [], "מקורות קובץ")}</article>
                `).join("") || '<p class="muted">אין קבצים בקבוצה זו.</p>'}
              </div>
              ${sourceDetails(g.sources || [], "מקורות קבוצה")}
            </div>
          </details>
        </section>
      `).join("")}
    </div>
  `;
}

function renderResearchedSourcesCards(items, kindLabel) {
  if (!items || !items.length) {
    return '<p class="muted">לא נמצאו מקורות שנחקרו להצגה.</p>';
  }
  return `
    <div class="cards-grid two">
      ${items.map((item) => `
        <article class="hub-card nested-card" data-searchable="true" data-search-text="${esc(`${item.source_id || ""} ${item.source_label_he || ""} ${item.what_was_found_he || ""}`)}">
          <div class="finding-head">
            <h4>${esc(item.source_label_he || item.source_id || "מקור")}</h4>
            <div class="chip-row">${statusPill(item.relevance || "none")} ${pill(item.contribution_level_he || "לא ידוע")}</div>
          </div>
          <p class="muted">${esc(item.source_type || "")}</p>
          <div class="obs-row"><span>מה נחקר בו</span><p>${esc(item.what_was_checked_he || "-")}</p></div>
          <div class="obs-row"><span>מה נמצא</span><p>${esc(item.what_was_found_he || "-")}</p></div>
          <div class="obs-row"><span>מה למדנו מזה עבור ${esc(kindLabel)}</span><p>${esc(item[`what_we_learned_for_${kindLabel === "לוגיקה" ? "logic" : "structure"}_he`] || "-")}</p></div>
          ${sourceDetails(item.sources || [], "מקורות")}
        </article>
      `).join("")}
    </div>
  `;
}

function renderProfileLogicSimple(profileId) {
  const vm = ((((DATA.group_b || {}).logic_presentation || {}).profiles) || {})[profileId] || {};
  const summary = vm.logic_summary || {};
  return `
    <div class="profile-sections">
      <section class="hub-card">
        <h3>מקורות שנחקרו להבנת הלוגיקה</h3>
        <p class="muted">כאן רואים מה בדקנו בכל מקור, מה מצאנו, ומה לקחנו ממנו כדי להבין את ההתנהגות הנדרשת של הפרופיל.</p>
        ${renderResearchedSourcesCards(vm.researched_sources || [], "לוגיקה")}
      </section>
      <section class="hub-card">
        <h3>סיכום הלוגיקה של הפרופיל (תכלס)</h3>
        <p class="lead">${esc(summary.summary_he || "אין עדיין סיכום לוגיקה.")}</p>
        <h4>מה הפרופיל צריך לדעת לעשות</h4>
        ${renderListOrMuted(summary.behaviors_required_he || [], "אין סעיפי לוגיקה מסונתזים עדיין.")}
        <h4>פוקוס לשלב 1 (Phase 1)</h4>
        ${renderListOrMuted(summary.phase1_focus_he || [], "לא הוגדר פוקוס Phase 1 בלוגיקה.")}
        ${summary.important_conditions_he && summary.important_conditions_he.length ? `<h4>תנאים/דגשים חשובים</h4>${renderListOrMuted(summary.important_conditions_he, "אין")}` : ""}
        ${sourceDetails(summary.sources || [], "מקורות הסיכום")}
      </section>
    </div>
  `;
}

function renderStructureFilePlanTable(filePlan) {
  if (!filePlan || !filePlan.length) {
    return '<p class="muted">אין עדיין תכנית קבצים להצגה.</p>';
  }
  return `
    <div class="table-wrap">
      <table>
        <thead><tr><th>נתיב</th><th>שם קובץ</th><th>מטרה</th><th>פאזה</th><th>תלויות</th></tr></thead>
        <tbody>
          ${filePlan.map((f) => `
            <tr data-searchable="true" data-search-text="${esc(`${f.path || ""} ${f.filename || ""} ${f.purpose_he || ""}`)}">
              <td><code>${esc(f.path || "-")}</code></td>
              <td>${esc(f.filename || "-")}</td>
              <td>${esc(f.purpose_he || "-")}</td>
              <td>${pill(f.created_in_phase || "-")}</td>
              <td>${(f.depends_on || []).length ? (f.depends_on || []).map((d) => `<code>${esc(d)}</code>`).join(" ") : '<span class="muted">-</span>'}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderFileBlueprints(blueprints) {
  if (!blueprints || !blueprints.length) return '<p class="muted">אין blueprint פנימי לקבצים.</p>';
  return `
    <div class="cards-grid two">
      ${blueprints.map((bp) => `
        <article class="hub-card nested-card" data-searchable="true" data-search-text="${esc(`${bp.file_key || ""} ${(bp.responsibilities_he || []).join(" ")}`)}">
          <h4><code>${esc(bp.file_key || "-")}</code></h4>
          <h5>מבנה פנימי מוצע</h5>
          ${renderListOrMuted(bp.internal_sections_he || [], "אין")}
          <h5>אחריות / פונקציות מרכזיות</h5>
          ${renderListOrMuted(bp.responsibilities_he || bp.functions_he || [], "אין")}
          ${(bp.notes_he || []).length ? `<h5>הערות</h5>${renderListOrMuted(bp.notes_he, "אין")}` : ""}
        </article>
      `).join("")}
    </div>
  `;
}

function renderProfileStructureSimple(profileId) {
  const vm = ((((DATA.group_b || {}).structure_presentation || {}).profiles) || {})[profileId] || {};
  const complexity = vm.profile_complexity || {};
  const summary = vm.structure_summary || {};
  const baseRef = summary.base_profile_structure_ref || {};
  return `
    <div class="profile-sections">
      <section class="hub-card">
        <h3>מקורות שנחקרו להבנת המבנה</h3>
        <p class="muted">כאן מוצגים המקורות והדפוסים שנבדקו כדי להבין איך נכון לבנות את המימוש בקוד, כולל דמיון לפרופילים אחרים.</p>
        <div class="cards-grid two">
          <article class="hub-card nested-card">
            <h4>סיווג מורכבות</h4>
            <div class="chip-row">${complexity.classification === "complex" ? pill("Profile מורכב", "optional") : pill("Profile פשוט", "mandatory")}</div>
            <p>${esc(complexity.classification_reason_he || "אין נימוק זמין.")}</p>
            ${sourceDetails(complexity.sources || [], "מקורות סיווג")}
          </article>
          <article class="hub-card nested-card">
            <h4>פרופילים דומים שנמצאו</h4>
            ${(vm.similar_profiles || []).length ? `
              <ul class="compact-list">
                ${(vm.similar_profiles || []).map((sp) => `<li><strong>${esc(sp.profile_name || "-")}</strong> — ${esc(sp.why_similar_he || "")}<br><span class="muted">${esc(sp.what_can_be_learned_he || "")}</span></li>`).join("")}
              </ul>` : '<p class="muted">לא זוהו פרופילים דומים מפורשים בממצאים הנוכחיים.</p>'}
          </article>
        </div>
        ${renderResearchedSourcesCards(vm.researched_sources || [], "מבנה")}
      </section>
      <section class="hub-card">
        <h3>סיכום מבנה המימוש המומלץ</h3>
        <p class="lead">${esc(summary.summary_he || "אין עדיין סיכום מבנה.")}</p>
        <div class="warning-box">
          <strong>מבנה בסיסי לכל פרופיל:</strong>
          ${esc(baseRef.detail_he || "המקור הבסיסי טרם הוזן; כרגע מוצג fallback מסונתז מהמחקר והחוזה.")}
        </div>
        <h4>תכנית קבצים מוצעת</h4>
        ${renderStructureFilePlanTable(summary.file_plan || [])}
        <h4>מבנה פנימי מוצע לכל קובץ</h4>
        ${renderFileBlueprints(summary.file_internal_blueprints || [])}
        ${sourceDetails(summary.sources || [], "מקורות סיכום מבנה")}
      </section>
    </div>
  `;
}

function taskStatusPill(status) {
  const s = String(status || "todo");
  if (s === "done") return pill("בוצע", "mandatory");
  if (s === "in_progress") return pill("בתהליך", "optional");
  if (s === "blocked") return pill("חסום", "conditional");
  if (s === "deferred") return pill("נדחה", "optional");
  return pill("לביצוע");
}

function renderTaskOptions(selected, optionsMap) {
  const entries = Object.entries(optionsMap || {});
  return entries
    .map(([value, label]) => `<option value="${esc(value)}" ${String(selected) === String(value) ? "selected" : ""}>${esc(label)}</option>`)
    .join("");
}

function renderTaskCard(task, allTasks, readOnly) {
  const cur = task.current || {};
  const children = (allTasks || []).filter((t) => (t.parent_task_id || null) === task.task_id);
  const isParent = children.length > 0;
  const disabled = readOnly ? "disabled" : "";
  const assigneeListId = `assigneeSuggestions-${esc(task.task_id)}`;
  return `
    <article class="hub-card nested-card task-card ${isParent ? "task-parent" : ""}" data-searchable="true" data-search-text="${esc(`${task.title_he || ""} ${task.description_he || ""} ${task.category || ""} ${cur.assignee || ""}`)}">
      <div class="task-card-head">
        <div>
          <h4>${esc(task.title_he || "משימה")}</h4>
          <p class="muted">${esc(task.description_he || "")}</p>
        </div>
        <div class="chip-row">
          ${taskStatusPill(cur.status)}
          ${pill(`עדיפות: ${taskPriorityLabel(cur.priority)}`)}
          ${pill(TASK_CATEGORY_LABELS[String(task.category || "")] || String(task.category || "task"))}
          ${task.is_completed_seed ? pill("בוצע קודם ע\"י Codex", "mandatory") : ""}
        </div>
      </div>
      <div class="task-form-grid">
        <label>מי עושה
          <input type="text" list="${assigneeListId}" data-task-field="assignee" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(task.profile_id || "")}" value="${esc(cur.assignee || "")}" ${disabled} />
          <datalist id="${assigneeListId}">
            <option value="codex"></option>
            <option value="tzohar"></option>
            <option value="manual"></option>
          </datalist>
        </label>
        <label>סטטוס
          <select data-task-field="status" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(task.profile_id || "")}" ${disabled}>
            ${renderTaskOptions(cur.status || "todo", TASK_STATUS_LABELS)}
          </select>
        </label>
        <label>עדיפות
          <select data-task-field="priority" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(task.profile_id || "")}" ${disabled}>
            ${renderTaskOptions(cur.priority || task.suggested_priority || "medium", TASK_PRIORITY_LABELS)}
          </select>
        </label>
        <label>תלויות (IDs, מופרד בפסיקים)
          <input type="text" data-task-field="depends_on" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(task.profile_id || "")}" value="${esc((cur.depends_on || []).join(', '))}" ${disabled} />
        </label>
        <label class="task-field-wide">הערות
          <textarea rows="2" data-task-field="notes" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(task.profile_id || "")}" ${disabled}>${esc(cur.notes || "")}</textarea>
        </label>
        ${(String(cur.status || "") === "blocked") ? `
          <label class="task-field-wide">סיבת חסימה
            <input type="text" data-task-field="blocked_reason" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(task.profile_id || "")}" value="${esc(cur.blocked_reason || "")}" ${disabled} />
          </label>` : ""}
      </div>
      <div class="task-card-meta">
        <span>${task.derived_from ? `נגזר מ: ${esc(task.derived_from)}` : ""}</span>
        <span>${cur.updated_at ? `עודכן: ${esc(cur.updated_at)}` : ""}</span>
      </div>
      ${sourceDetails(task.source_refs || [], "מקורות משימה")}
      ${children.length ? `<div class="task-subtasks">${children.map((child) => renderTaskCard(child, allTasks, readOnly)).join("")}</div>` : ""}
    </article>
  `;
}

function renderTaskBucket(title, tasks, allTasks, readOnly, emptyText) {
  return `
    <section class="hub-card">
      <h3>${esc(title)}</h3>
      ${(tasks || []).length ? `<div class="task-list">${(tasks || []).map((t) => renderTaskCard(t, allTasks, readOnly)).join("")}</div>` : `<p class="muted">${esc(emptyText)}</p>`}
    </section>
  `;
}

function taskBoardHasActiveFilters(filters) {
  if (!filters) return false;
  return !!(filters.q || filters.assignee || filters.status || filters.priority || filters.category || filters.stage || (filters.chip && filters.chip !== "all"));
}

function sortTasksForBoard(tasks, sortMode = "default") {
  return [...(tasks || [])].sort((a, b) => {
    const mode = String(sortMode || "default");
    if (mode === "title") {
      return String(a.title_he || "").localeCompare(String(b.title_he || ""), "he");
    }
    if (mode === "status") {
      const sa = taskStatusSortRank((a.current || {}).status || "todo");
      const sb = taskStatusSortRank((b.current || {}).status || "todo");
      if (sa !== sb) return sa - sb;
      return String(a.title_he || "").localeCompare(String(b.title_he || ""), "he");
    }
    const pa = taskPrioritySortRank((a.current || {}).priority || a.suggested_priority);
    const pb = taskPrioritySortRank((b.current || {}).priority || b.suggested_priority);
    if (pa !== pb) return pa - pb;
    const sa = taskStatusSortRank((a.current || {}).status || "todo");
    const sb = taskStatusSortRank((b.current || {}).status || "todo");
    if (sa !== sb) return sa - sb;
    return String(a.title_he || "").localeCompare(String(b.title_he || ""), "he");
  });
}

function deriveTaskBoardContext(profileId) {
  const vm = profileCurrentWorkVm(profileId);
  const tasks = mergedTasksForProfile(profileId).map((t) => ({ ...t, profile_id: profileId }));
  const { byId, childrenByParent } = buildTaskIndexes(tasks);
  const groups = [...taskGroupsForProfileResolved(profileId, tasks)].sort((a, b) => Number(a.order || 999) - Number(b.order || 999));
  const ui = taskBoardUiProfileState(profileId);
  const sortMode = ui.sort || "default";
  const filters = { ...(ui.filters || {}) };
  const allFiltered = tasks.filter((t) => taskMatchesBoardFilters(t, filters));
  const filteredTaskIds = new Set(allFiltered.map((t) => t.task_id));
  const hasFilters = taskBoardHasActiveFilters(filters);

  const stageVms = groups.map((group) => {
    const groupId = String(group.group_id || "");
    const groupTasksAll = tasks.filter((t) => String(t.task_group_id || fallbackTaskGroupIdForTask(t)) === groupId);
    const groupTasksFiltered = groupTasksAll.filter((t) => filteredTaskIds.has(t.task_id));
    const counts = taskSummaryFromMerged(groupTasksFiltered);
    counts.todo = ((counts.byStatus || {}).todo || 0);
    counts.deferred = ((counts.byStatus || {}).deferred || 0);
    const totalForProgress = Math.max(1, groupTasksFiltered.length || groupTasksAll.length || 1);
    const progressPct = Math.round(((counts.done || 0) / totalForProgress) * 100);

    const visibleRoots = [];
    for (const rootId of group.task_ids || []) {
      const root = byId[rootId];
      if (!root) continue;
      const descendants = descendantsOfTask(root.task_id, childrenByParent);
      const visible = !hasFilters || filteredTaskIds.has(root.task_id) || descendants.some((d) => filteredTaskIds.has(d.task_id));
      if (visible) visibleRoots.push(root);
    }

    const orderedTasks = [];
    const seen = new Set();
    const pushTree = (task, depth) => {
      if (!task || seen.has(task.task_id)) return;
      const selfVisible = !hasFilters || filteredTaskIds.has(task.task_id);
      const descendants = childrenByParent[task.task_id] || [];
      const descendantHasVisible = descendants.some((d) => filteredTaskIds.has(d.task_id) || descendantsOfTask(d.task_id, childrenByParent).some((x) => filteredTaskIds.has(x.task_id)));
      if (!selfVisible && !descendantHasVisible && hasFilters) return;
      seen.add(task.task_id);
      orderedTasks.push({ ...task, _depth: depth, _selfVisible: selfVisible });
      sortTasksForBoard(descendants, sortMode).forEach((child) => pushTree(child, depth + 1));
    };
    visibleRoots.forEach((root) => pushTree(root, 0));
    // Add orphaned tasks (fallback/migration or mismatched parent group)
    sortTasksForBoard(groupTasksFiltered.filter((t) => !seen.has(t.task_id)), sortMode).forEach((t) => orderedTasks.push({ ...t, _depth: t.parent_task_id ? 1 : 0, _selfVisible: true }));

    const highlightIds = (hasFilters ? visibleRoots.map((t) => t.task_id) : (group.highlight_task_ids || group.task_ids || []))
      .filter(Boolean)
      .slice(0, 4);
    const highlightTitles = highlightIds.map((tid) => byId[tid]).filter(Boolean).map((t) => String(t.title_he || ""));

    return {
      ...group,
      group_id: groupId,
      counts,
      progressPct,
      totalVisible: groupTasksFiltered.length,
      hasMatches: groupTasksFiltered.length > 0,
      hasBlockers: (counts.blocked || 0) > 0,
      visibleRoots,
      orderedTasks,
      highlightTitles,
    };
  });

  let activeGroup = ui.activeGroup;
  const validActive = stageVms.some((g) => g.group_id === activeGroup);
  if (!validActive) {
    const firstMatching = stageVms.find((g) => g.hasMatches);
    activeGroup = (hasFilters && firstMatching ? firstMatching.group_id : firstActionableTaskGroupId(stageVms, byId)) || (stageVms[0] && stageVms[0].group_id) || "";
    setTaskBoardUiField(profileId, "activeGroup", activeGroup);
  } else if (hasFilters && !activeGroup) {
    const firstMatching = stageVms.find((g) => g.hasMatches);
    if (firstMatching) {
      activeGroup = firstMatching.group_id;
      setTaskBoardUiField(profileId, "activeGroup", activeGroup);
    }
  }

  let expandedTaskId = ui.expandedTask;
  if (expandedTaskId) {
    const activeStage = stageVms.find((g) => g.group_id === activeGroup);
    const visibleTaskIds = new Set((activeStage && activeStage.orderedTasks || []).map((t) => t.task_id));
    if (!visibleTaskIds.has(expandedTaskId)) {
      expandedTaskId = null;
      setTaskBoardUiField(profileId, "expandedTask", null);
    }
  }

  const summaryAll = taskSummaryFromMerged(tasks);
  summaryAll.todo = ((summaryAll.byStatus || {}).todo || 0);
  summaryAll.deferred = ((summaryAll.byStatus || {}).deferred || 0);
  const summaryFiltered = taskSummaryFromMerged(allFiltered);
  summaryFiltered.todo = ((summaryFiltered.byStatus || {}).todo || 0);
  summaryFiltered.deferred = ((summaryFiltered.byStatus || {}).deferred || 0);

  const actionablePool = sortTasksForBoard((hasFilters ? allFiltered : tasks).filter((t) => {
    const st = String((t.current || {}).status || "todo");
    return st === "todo" || st === "in_progress";
  }), sortMode);
  const topActions = actionablePool
    .map((t) => {
      const deps = (t.current || {}).depends_on || [];
      const openDeps = Array.isArray(deps) ? deps.filter((id) => {
        const dep = byId[id];
        return dep && !["done", "deferred"].includes(String(((dep.current || {}).status || "todo")));
      }) : [];
      return { ...t, _openDepsCount: openDeps.length };
    })
    .filter((t) => String((t.current || {}).status || "") !== "blocked")
    .sort((a, b) => {
      if (a._openDepsCount !== b._openDepsCount) return a._openDepsCount - b._openDepsCount;
      if (!!a.parent_task_id !== !!b.parent_task_id) return a.parent_task_id ? 1 : -1;
      return 0;
    })
    .slice(0, 5);

  const assigneeSummary = {};
  (hasFilters ? allFiltered : tasks).forEach((t) => {
    const st = String((t.current || {}).status || "todo");
    if (["done", "deferred"].includes(st)) return;
    const key = String((t.current || {}).assignee || "").trim() || "לא משויך";
    assigneeSummary[key] = (assigneeSummary[key] || 0) + 1;
  });

  const categorySummary = {};
  (hasFilters ? allFiltered : tasks).forEach((t) => {
    const key = String(t.category || "other");
    categorySummary[key] = (categorySummary[key] || 0) + 1;
  });

  return {
    profileId,
    vm,
    readOnly: !!taskStateApi.readOnly,
    hasFilters,
    filters,
    uiMode: ui.viewMode,
    activeGroup,
    expandedTaskId,
    tasks,
    taskById: byId,
    childrenByParent,
    stageVms,
    summaryAll,
    summaryFiltered,
    topActions,
    assigneeSummary,
    categorySummary,
    assigneeOptions: Array.from(new Set(tasks.map((t) => String(((t.current || {}).assignee || "")).trim()).filter(Boolean))).sort((a, b) => a.localeCompare(b, "he")),
  };
}

function renderTaskBoardSummaryCards(ctx) {
  const summary = ctx.hasFilters ? ctx.summaryFiltered : ctx.summaryAll;
  const assignees = Object.entries(ctx.assigneeSummary || {}).sort((a, b) => b[1] - a[1]);
  const topActions = ctx.topActions || [];
  const categoryBits = Object.entries(ctx.categorySummary || {})
    .sort((a, b) => b[1] - a[1])
    .map(([k, v]) => `<span>${esc(TASK_CATEGORY_LABELS[k] || k)} <strong>${esc(String(v))}</strong></span>`)
    .join("");
  return `
    <div class="task-summary-strip">
      <section class="hub-card nested-card">
        <h4>מה עושים עכשיו</h4>
        <p class="muted">3-5 משימות מומלצות להתחלה לפי סטטוס/עדיפות/תלויות פתוחות.</p>
        ${topActions.length ? `<ul class="compact-list">${topActions.map((t) => `<li data-searchable="true"><strong>${esc(t.title_he || t.task_id)}</strong> — ${taskStatusPill((t.current || {}).status)} ${pill(`עדיפות: ${taskPriorityLabel((t.current || {}).priority)}`)} ${t._openDepsCount ? pill(`תלויות פתוחות: ${t._openDepsCount}`, "conditional") : ""}</li>`).join("")}</ul>` : '<p class="muted">אין כרגע משימות מומלצות (ייתכן שהכל בוצע/חסום/מסונן).</p>'}
      </section>
      <section class="hub-card nested-card">
        <h4>מי עושה מה</h4>
        ${assignees.length ? `<div class="mini-metrics-grid">${assignees.map(([name, count]) => `<div><span>${esc(name)}</span><strong>${esc(String(count))}</strong></div>`).join("")}</div>` : '<p class="muted">אין משימות פתוחות משויכות כרגע.</p>'}
      </section>
      <section class="hub-card nested-card">
        <h4>תמונת מצב${ctx.hasFilters ? " (מסונן)" : ""}</h4>
        <div class="mini-metrics-grid">
          <div><span>סה\"כ</span><strong>${esc(String(summary.total || 0))}</strong></div>
          <div><span>בוצע</span><strong>${esc(String(summary.done || 0))}</strong></div>
          <div><span>בתהליך</span><strong>${esc(String(summary.in_progress || 0))}</strong></div>
          <div><span>לא בוצע</span><strong>${esc(String(summary.todo || 0))}</strong></div>
          <div><span>חסום</span><strong>${esc(String(summary.blocked || 0))}</strong></div>
          <div><span>נדחה</span><strong>${esc(String(summary.deferred || 0))}</strong></div>
        </div>
        ${categoryBits ? `<div class="mini-meta task-category-breakdown">${categoryBits}</div>` : ""}
      </section>
    </div>
  `;
}

function renderTaskBoardControls(profileId, ctx) {
  const f = ctx.filters || {};
  const chipDefs = [
    ["all", "הכל"],
    ["mine", "שלי"],
    ["todo", "לביצוע"],
    ["in_progress", "בתהליך"],
    ["blocked", "חסום"],
    ["high", "עדיפות גבוהה"],
    ["unassigned", "ללא משויך"],
  ];
  const assigneeOpts = ["", "codex", DEFAULT_TASK_ASSIGNEE, ...ctx.assigneeOptions.filter((x) => !["codex", DEFAULT_TASK_ASSIGNEE].includes(x))];
  const stageOpts = ["", ...(ctx.stageVms || []).map((g) => g.group_id)];
  const sortVal = (state.taskBoardUi.sortByProfile || {})[profileId] || "default";
  const mode = (state.taskBoardUi.viewModeByProfile || {})[profileId] || "overview";
  return `
    <section class="hub-card task-board-controls">
      <div class="task-board-controls-head">
        <div>
          <h3>לוח עבודה לפי שלבים — ${esc(uiLabel(profileId))}</h3>
          <p class="muted">כאן עובדים לפי שלבים: בוחרים שלב, רואים משימות, ופותחים משימה לעריכה מלאה רק כשצריך.</p>
        </div>
        <div class="chip-row">
          <button type="button" class="mini-btn ${mode === "overview" ? "active" : ""}" data-task-view-mode="${esc(profileId)}:overview">סקירה</button>
          <button type="button" class="mini-btn ${mode === "edit" ? "active" : ""}" data-task-view-mode="${esc(profileId)}:edit">עריכה</button>
          ${ctx.readOnly ? pill("קריאה בלבד", "conditional") : pill("שמירה פעילה", "mandatory")}
        </div>
      </div>
      ${taskStateApi.loading ? '<p class="muted">טוען מצב משימות מהשרת...</p>' : ""}
      ${taskStateApi.error ? `<div class="warning-box"><strong>הערת API:</strong> ${esc(taskStateApi.error)}</div>` : ""}
      <div class="task-filter-bar">
        <label>חיפוש
          <input type="text" value="${esc(f.q || "")}" data-task-board-filter="q" data-profile-id="${esc(profileId)}" placeholder="חיפוש שם משימה / assignee / notes..." />
        </label>
        <label>מבצע
          <select data-task-board-filter="assignee" data-profile-id="${esc(profileId)}">
            ${assigneeOpts.map((opt) => `<option value="${esc(opt)}" ${String(f.assignee || "") === String(opt) ? "selected" : ""}>${esc(opt || "הכל")}</option>`).join("")}
          </select>
        </label>
        <label>סטטוס
          <select data-task-board-filter="status" data-profile-id="${esc(profileId)}">
            <option value="" ${!f.status ? "selected" : ""}>הכל</option>
            ${Object.entries(TASK_STATUS_LABELS).map(([k, v]) => `<option value="${esc(k)}" ${String(f.status || "") === k ? "selected" : ""}>${esc(v)}</option>`).join("")}
          </select>
        </label>
        <label>עדיפות
          <select data-task-board-filter="priority" data-profile-id="${esc(profileId)}">
            <option value="" ${!f.priority ? "selected" : ""}>הכל</option>
            ${Object.entries(TASK_PRIORITY_LABELS).map(([k, v]) => `<option value="${esc(k)}" ${String(f.priority || "") === k ? "selected" : ""}>${esc(v)}</option>`).join("")}
          </select>
        </label>
        <label>קטגוריה
          <select data-task-board-filter="category" data-profile-id="${esc(profileId)}">
            <option value="" ${!f.category ? "selected" : ""}>הכל</option>
            ${Object.entries(TASK_CATEGORY_LABELS).map(([k, v]) => `<option value="${esc(k)}" ${String(f.category || "") === k ? "selected" : ""}>${esc(v)}</option>`).join("")}
          </select>
        </label>
        <label>שלב
          <select data-task-board-filter="stage" data-profile-id="${esc(profileId)}">
            ${stageOpts.map((gid) => {
              const g = (ctx.stageVms || []).find((x) => x.group_id === gid);
              const label = gid ? ((g && g.label_he) || gid) : "הכל";
              return `<option value="${esc(gid)}" ${String(f.stage || "") === String(gid) ? "selected" : ""}>${esc(label)}</option>`;
            }).join("")}
          </select>
        </label>
        <label>מיון
          <select data-task-board-sort="1" data-profile-id="${esc(profileId)}">
            <option value="default" ${sortVal === "default" ? "selected" : ""}>ברירת מחדל (עדיפות/סטטוס/שם)</option>
            <option value="title" ${sortVal === "title" ? "selected" : ""}>לפי שם</option>
            <option value="status" ${sortVal === "status" ? "selected" : ""}>לפי סטטוס</option>
          </select>
        </label>
      </div>
      <div class="task-filter-chips">
        ${chipDefs.map(([id, label]) => `<button type="button" class="chip-btn ${String(f.chip || "all") === id ? "active" : ""}" data-task-chip="${esc(profileId)}:${esc(id)}">${esc(label)}</button>`).join("")}
      </div>
      ${sourceDetails(ctx.vm.sources || [], "מקורות תבניות משימות")}
    </section>
  `;
}

function renderTaskStageCardCompact(profileId, stage, ctx) {
  const isActive = String(ctx.activeGroup || "") === String(stage.group_id || "");
  const counts = stage.counts || {};
  return `
    <button type="button"
      class="task-stage-card ${isActive ? "active" : ""} ${stage.hasBlockers ? "has-blocker" : ""}"
      data-task-group-toggle="${esc(profileId)}:${esc(stage.group_id)}"
      data-searchable="true"
      data-search-text="${esc(`${stage.label_he || ""} ${(stage.highlightTitles || []).join(" ")}`)}">
      <div class="task-stage-card-head">
        <div>
          <h4>${esc(stage.label_he || stage.group_id || "שלב")}</h4>
          <p class="muted">${esc(stage.goal_he || stage.summary_he || "")}</p>
        </div>
        <div class="chip-row">
          ${stage.hasBlockers ? pill("יש חסימה", "conditional") : ""}
          ${stage.totalVisible ? pill(`${stage.totalVisible} משימות`) : pill("אין התאמות", "optional")}
        </div>
      </div>
      <div class="task-stage-progress">
        <div class="task-stage-progress-bar"><span style="width:${Math.max(0, Math.min(100, Number(stage.progressPct || 0)))}%"></span></div>
        <strong>${esc(String(stage.progressPct || 0))}%</strong>
      </div>
      <div class="task-stage-metrics">
        <div><span>בוצע</span><strong>${esc(String(counts.done || 0))}</strong></div>
        <div><span>בתהליך</span><strong>${esc(String(counts.in_progress || 0))}</strong></div>
        <div><span>לא בוצע</span><strong>${esc(String(counts.todo || 0))}</strong></div>
        <div><span>חסום</span><strong>${esc(String(counts.blocked || 0))}</strong></div>
        ${(counts.deferred || 0) ? `<div><span>נדחה</span><strong>${esc(String(counts.deferred || 0))}</strong></div>` : ""}
      </div>
      <div class="task-stage-highlights">
        ${(stage.highlightTitles || []).length ? `<ul>${(stage.highlightTitles || []).map((t) => `<li>${esc(t)}</li>`).join("")}</ul>` : '<p class="muted">אין משימות עיקריות להצגה בשלב זה.</p>'}
      </div>
    </button>
  `;
}

function compactAssigneeOptions(selected, extraOptions) {
  const opts = ["", "codex", DEFAULT_TASK_ASSIGNEE, ...((extraOptions || []).filter((x) => !["", "codex", DEFAULT_TASK_ASSIGNEE].includes(x)))];
  return Array.from(new Set(opts))
    .map((v) => `<option value="${esc(v)}" ${String(selected || "") === String(v) ? "selected" : ""}>${esc(v || "לא משויך")}</option>`)
    .join("");
}

function renderTaskMiniCardCompact(profileId, task, ctx) {
  const cur = task.current || {};
  const children = (ctx.childrenByParent[task.task_id] || []);
  const mode = ctx.uiMode || "overview";
  const readOnly = ctx.readOnly;
  const disabled = readOnly ? "disabled" : "";
  const parentTitle = task.parent_task_id && ctx.taskById[task.parent_task_id] ? String((ctx.taskById[task.parent_task_id] || {}).title_he || "") : "";
  return `
    <article class="hub-card nested-card task-mini-card depth-${Math.min(Number(task._depth || 0), 3)} ${String(ctx.expandedTaskId || "") === String(task.task_id || "") ? "active" : ""}"
      data-task-card-toggle="${esc(profileId)}:${esc(task.task_id)}"
      data-searchable="true"
      data-search-text="${esc(`${task.title_he || ""} ${task.description_he || ""} ${cur.assignee || ""}`)}">
      <div class="task-mini-head">
        <div>
          <h4>${esc(task.title_he || "משימה")}</h4>
          ${parentTitle ? `<p class="muted">תת-משימה של: ${esc(parentTitle)}</p>` : ""}
        </div>
        <div class="chip-row">
          ${taskStatusPill(cur.status)}
          ${pill(`עדיפות: ${taskPriorityLabel(cur.priority)}`)}
          ${pill(TASK_CATEGORY_LABELS[String(task.category || "")] || String(task.category || "task"))}
          ${children.length ? pill(`${children.length} תתי־משימות`) : ""}
        </div>
      </div>
      <div class="task-mini-meta">
        <span>מבצע: <strong>${esc(cur.assignee || "לא משויך")}</strong></span>
        ${cur.updated_at ? `<span>עודכן: <code>${esc(cur.updated_at)}</code></span>` : ""}
        ${String(cur.status || "") === "blocked" && cur.blocked_reason ? `<span class="muted">סיבת חסימה: ${esc(cur.blocked_reason)}</span>` : ""}
      </div>
      ${(mode === "edit" && !readOnly) ? `
        <div class="task-inline-quick-edit" data-task-field-container="true">
          <label>מבצע
            <select data-task-field="assignee" data-task-compact-edit="1" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" ${disabled}>
              ${compactAssigneeOptions(cur.assignee || "", ctx.assigneeOptions)}
            </select>
          </label>
          <label>סטטוס
            <select data-task-field="status" data-task-compact-edit="1" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" ${disabled}>
              ${renderTaskOptions(cur.status || "todo", TASK_STATUS_LABELS)}
            </select>
          </label>
        </div>` : ""}
    </article>
  `;
}

function renderTaskMiniCardExpanded(profileId, task, ctx) {
  const cur = task.current || {};
  const readOnly = ctx.readOnly;
  const disabled = readOnly ? "disabled" : "";
  const parentTitle = task.parent_task_id && ctx.taskById[task.parent_task_id] ? String((ctx.taskById[task.parent_task_id] || {}).title_he || "") : "";
  const assigneeListId = `assigneeSuggestions-${esc(task.task_id)}-mini`;
  return `
    <article class="hub-card nested-card task-mini-card task-mini-card-expanded depth-${Math.min(Number(task._depth || 0), 3)} active"
      data-searchable="true"
      data-search-text="${esc(`${task.title_he || ""} ${task.description_he || ""} ${task.category || ""} ${cur.assignee || ""}`)}">
      <div class="task-card-head">
        <div>
          <h4>${esc(task.title_he || "משימה")}</h4>
          ${parentTitle ? `<p class="muted">תת-משימה של: ${esc(parentTitle)}</p>` : ""}
          <p class="muted">${esc(task.description_he || "")}</p>
        </div>
        <div class="chip-row">
          ${taskStatusPill(cur.status)}
          ${pill(`עדיפות: ${taskPriorityLabel(cur.priority)}`)}
          ${pill(TASK_CATEGORY_LABELS[String(task.category || "")] || String(task.category || "task"))}
          ${task.is_completed_seed ? pill('בוצע קודם ע"י Codex', "mandatory") : ""}
          <button type="button" class="mini-btn" data-task-card-toggle="${esc(profileId)}:${esc(task.task_id)}">סגור</button>
        </div>
      </div>
      <div class="task-form-grid">
        <label>מי עושה
          <input type="text" list="${assigneeListId}" data-task-field="assignee" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" value="${esc(cur.assignee || "")}" ${disabled} />
          <datalist id="${assigneeListId}">
            <option value="codex"></option>
            <option value="${esc(DEFAULT_TASK_ASSIGNEE)}"></option>
            <option value="manual"></option>
          </datalist>
        </label>
        <label>סטטוס
          <select data-task-field="status" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" ${disabled}>
            ${renderTaskOptions(cur.status || "todo", TASK_STATUS_LABELS)}
          </select>
        </label>
        <label>עדיפות
          <select data-task-field="priority" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" ${disabled}>
            ${renderTaskOptions(cur.priority || task.suggested_priority || "medium", TASK_PRIORITY_LABELS)}
          </select>
        </label>
        <label>תלויות (IDs, מופרד בפסיקים)
          <input type="text" data-task-field="depends_on" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" value="${esc((cur.depends_on || []).join(", "))}" ${disabled} />
        </label>
        <label class="task-field-wide">הערות
          <textarea rows="2" data-task-field="notes" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" ${disabled}>${esc(cur.notes || "")}</textarea>
        </label>
        ${String(cur.status || "") === "blocked" ? `
          <label class="task-field-wide">סיבת חסימה
            <input type="text" data-task-field="blocked_reason" data-task-id="${esc(task.task_id)}" data-profile-id="${esc(profileId)}" value="${esc(cur.blocked_reason || "")}" ${disabled} />
          </label>` : ""}
      </div>
      <div class="task-card-meta">
        <span>${task.derived_from ? `נגזר מ: ${esc(task.derived_from)}` : ""}</span>
        <span>${cur.updated_at ? `עודכן: ${esc(cur.updated_at)}` : ""}</span>
      </div>
      <details class="inline-detail">
        <summary>פרטים מתקדמים / מקורות</summary>
        <div class="detail-body">
          ${sourceDetails(task.source_refs || [], "מקורות משימה")}
        </div>
      </details>
    </article>
  `;
}

function renderTaskStageExpanded(profileId, stage, ctx) {
  const visibleTasks = stage.orderedTasks || [];
  return `
    <section class="hub-card task-stage-expanded-row" data-searchable="true" data-search-text="${esc(`${stage.label_he || ""} ${(stage.highlightTitles || []).join(" ")}`)}">
      <div class="task-stage-expanded-head">
        <div>
          <h3>${esc(stage.label_he || stage.group_id || "שלב")}</h3>
          <p class="lead">${esc(stage.goal_he || stage.summary_he || "")}</p>
          ${stage.summary_he ? `<p class="muted">${esc(stage.summary_he)}</p>` : ""}
        </div>
        <div class="chip-row">
          ${stage.hasBlockers ? pill("יש חסימות", "conditional") : pill("ללא חסימות", "mandatory")}
          <button type="button" class="mini-btn" data-task-group-toggle="${esc(profileId)}:${esc(stage.group_id)}">כיווץ שלב</button>
        </div>
      </div>
      <div class="task-stage-progress task-stage-progress-inline">
        <div class="task-stage-progress-bar"><span style="width:${Math.max(0, Math.min(100, Number(stage.progressPct || 0)))}%"></span></div>
        <strong>${esc(String(stage.progressPct || 0))}%</strong>
        <div class="task-stage-metrics inline">
          <div><span>בוצע</span><strong>${esc(String((stage.counts || {}).done || 0))}</strong></div>
          <div><span>בתהליך</span><strong>${esc(String((stage.counts || {}).in_progress || 0))}</strong></div>
          <div><span>לא בוצע</span><strong>${esc(String((stage.counts || {}).todo || 0))}</strong></div>
          <div><span>חסום</span><strong>${esc(String((stage.counts || {}).blocked || 0))}</strong></div>
        </div>
      </div>
      ${visibleTasks.length ? `
        <div class="task-mini-grid">
          ${visibleTasks.map((task) => {
            const isExpanded = String(ctx.expandedTaskId || "") === String(task.task_id);
            return isExpanded
              ? renderTaskMiniCardExpanded(profileId, task, ctx)
              : renderTaskMiniCardCompact(profileId, task, ctx);
          }).join("")}
        </div>` : '<p class="muted task-empty-state-inline">אין התאמות בשלב זה לפי החיפוש/הפילטרים הנוכחיים.</p>'}
      ${sourceDetails(stage.sources || [], "מקורות stage grouping")}
    </section>
  `;
}

function renderTaskBoardStageLayout(profileId, ctx) {
  const active = (ctx.stageVms || []).find((g) => g.group_id === ctx.activeGroup) || null;
  const others = (ctx.stageVms || []).filter((g) => !active || g.group_id !== active.group_id);
  return `
    <section class="hub-card">
      <h3>שלבי עבודה</h3>
      <p class="muted">בחר שלב כדי לפתוח אותו. בתוך השלב המשימות מוצגות בכרטיסיות קומפקטיות, ולחיצה על משימה פותחת עריכה מלאה.</p>
      <div class="task-stage-grid">
        ${active ? renderTaskStageExpanded(profileId, active, ctx) : ""}
        ${(active ? others : (ctx.stageVms || [])).map((g) => renderTaskStageCardCompact(profileId, g, ctx)).join("")}
      </div>
    </section>
  `;
}

function renderProfileCurrentWork(profileId) {
  const ctx = deriveTaskBoardContext(profileId);
  return `
    <div class="profile-sections">
      ${renderTaskBoardControls(profileId, ctx)}
      ${renderTaskBoardSummaryCards(ctx)}
      ${renderTaskBoardStageLayout(profileId, ctx)}
    </div>
  `;
}

function renderKnowledgeCenterTab() {
  const root = document.getElementById("hubKnowledgeCenterContent");
  if (!root) return;
  const kc = ((DATA.group_b || {}).knowledge_center) || {};
  const sections = kc.sections || [];
  const byId = Object.fromEntries((sections || []).map((s) => [s.id, s]));
  root.innerHTML = `
    <div class="hub-panel-grid">
      <section class="hub-card span-12">
        <h2>מרכז ידע</h2>
        <p class="lead">כאן נמצא כל המידע העמוק/טכני שלא מוצג במסכי הפרופילים הפשוטים — כדי שלא יאבד ידע, אבל גם לא יעמיס במסכי העבודה.</p>
      </section>

      <section class="hub-card span-12">
        <h3>קטגוריות במרכז הידע</h3>
        <div class="cards-grid two">
          ${(sections || []).map((s) => `
            <article class="hub-card nested-card" data-searchable="true" data-search-text="${esc(`${s.label_he || ""} ${s.summary_he || ""}`)}">
              <h4>${esc(s.label_he || s.id || "קטגוריה")}</h4>
              <p>${esc(s.summary_he || "")}</p>
              <div class="mini-meta"><code>${esc(s.id || "")}</code></div>
            </article>`).join("")}
        </div>
      </section>

      <section class="hub-card span-12">
        <details class="hub-detail">
          <summary>Deep Dive לפרופילים (לוגיקה/מבנה מלאים + raw)</summary>
          <div class="detail-body">
            ${["BPS", "WSS", "SCPS"].map((pid) => `
              <details class="hub-detail">
                <summary>${esc(uiLabel(pid))} — תצוגות עומק</summary>
                <div class="detail-body">
                  <section class="hub-card nested-card"><h4>לוגיקה (עמוק)</h4>${renderKnowledgeDoc(pid, "logic")}</section>
                  <section class="hub-card nested-card"><h4>מבנה (עמוק)</h4>${renderKnowledgeDoc(pid, "structure")}</section>
                </div>
              </details>`).join("")}
          </div>
        </details>
      </section>

      <section class="hub-card span-12">
        <details class="hub-detail">
          <summary>מטא-דטה טכני של מפרטים / readiness / validation</summary>
          <div class="detail-body">
            ${(byId.spec_artifacts_technical && byId.spec_artifacts_technical.entries) ? `
              <div class="cards-grid three">
                ${byId.spec_artifacts_technical.entries.map((e) => `
                  <article class="hub-card nested-card">
                    <h4>${esc(e.ui_label || e.profile_id || "")}</h4>
                    <div class="kv-grid compact">
                      <div><span>sync</span>${statusPill(e.sync_status)}</div>
                      <div><span>artifacts</span><strong>${esc(String(e.artifact_count || 0))}</strong></div>
                      <div><span>spec dir</span><code>${esc(e.spec_dir || "-")}</code></div>
                    </div>
                    <details class="inline-detail"><summary>kind_counts</summary><div class="detail-body"><pre><code>${esc(JSON.stringify(e.kind_counts || {}, null, 2))}</code></pre></div></details>
                    ${e.spec_page_url ? `<a class="mini-btn linkish" target="_blank" rel="noopener" href="${esc(e.spec_page_url)}">עמוד spec</a>` : ""}
                  </article>`).join("")}
              </div>` : '<p class="muted">אין נתוני metadata למפרטים.</p>'}
            <div class="cards-grid two" style="margin-top:10px;">
              ${(byId.readiness_validation_qa && (byId.readiness_validation_qa.panels || [])).map((p) => `
                <article class="hub-card nested-card">
                  <h4>${esc(p.label_he || p.id || "panel")}</h4>
                  <pre><code>${esc(JSON.stringify(p.data || {}, null, 2))}</code></pre>
                </article>`).join("")}
            </div>
            ${["BPS", "WSS", "SCPS"].map((pid) => `
              <details class="hub-detail">
                <summary>${esc(uiLabel(pid))} — סטטוס/validation/QA עמוק</summary>
                <div class="detail-body">${renderProfileStatus(pid)}</div>
              </details>`).join("")}
          </div>
        </details>
      </section>

      <section class="hub-card span-12">
        <details class="hub-detail">
          <summary>AutoPTS Deep (מעבר לתקציר)</summary>
          <div class="detail-body">
            <div class="cards-grid three">
              ${(((byId.autopts_deep_dive || {}).panels) || []).map((p) => `
                <article class="hub-card nested-card">
                  <h4>${esc(p.label_he || p.id || "")}</h4>
                  <pre><code>${esc(JSON.stringify(p.data || {}, null, 2))}</code></pre>
                </article>`).join("")}
            </div>
          </div>
        </details>
      </section>

      <section class="hub-card span-12">
        <details class="hub-detail">
          <summary>Raw Markdown / Debug</summary>
          <div class="detail-body">
            ${(((byId.raw_markdown_and_debug || {}).entries) || []).map((e) => `
              <article class="hub-card nested-card">
                <h4>${esc(e.ui_label || e.profile_id || "")}</h4>
                <p class="muted">לוגיקה: <code>${esc(e.logic_path || "-")}</code></p>
                <details class="inline-detail"><summary>Preview לוגיקה</summary><div class="detail-body"><pre><code>${esc(e.logic_raw_markdown_preview || "")}</code></pre></div></details>
                <p class="muted">מבנה: <code>${esc(e.structure_path || "-")}</code></p>
                <details class="inline-detail"><summary>Preview מבנה</summary><div class="detail-body"><pre><code>${esc(e.structure_raw_markdown_preview || "")}</code></pre></div></details>
              </article>`).join("")}
          </div>
        </details>
      </section>
    </div>
  `;
}

function renderFindingsCards(findings) {
  if (!findings || !findings.length) {
    return `
      <div class="empty-state" data-searchable="true">
        <h4>אין עדיין ממצאים מובנים</h4>
        <p>קובץ ה-MD קיים (scaffold), אבל טרם חולצו findings מתוך מקורות Nordic/TI. ה-parser והתצוגה כבר מוכנים.</p>
      </div>
    `;
  }
  return `
    <div class="cards-grid two">
      ${findings
        .map(
          (f) => `
        <article class="hub-card finding-card" data-searchable="true" data-search-text="${esc(`${f.title_he || ""} ${f.statement_he || ""} ${f.why_it_matters_he || ""}`)}">
          <div class="finding-head">
            <h4>${esc(f.title_he || "ממצא")}</h4>
            <div class="chip-row">${confidencePill(f.confidence)} ${statusPill(f.status)}</div>
          </div>
          <p>${esc(f.statement_he || "")}</p>
          ${f.why_it_matters_he ? `<p class="muted">${esc(f.why_it_matters_he)}</p>` : ""}
          ${(f.derivation_method_ids || []).length ? `<div class="mini-meta"><span>שיטות:</span> ${f.derivation_method_ids.map((m) => `<code>${esc(m)}</code>`).join(" ")}</div>` : ""}
          ${(f.source_ids || []).length ? `<div class="mini-meta"><span>מזהי מקורות:</span> ${f.source_ids.map((s) => `<code>${esc(s)}</code>`).join(" ")}</div>` : ""}
          ${(f.evidence_refs || []).length ? `
            <details class="inline-detail">
              <summary>Evidence / ייחוסי ראיות (${esc(String((f.evidence_refs || []).length))})</summary>
              <div class="detail-body">
                <ul class="src-list">
                  ${(f.evidence_refs || [])
                    .map((ev) => {
                      const lineRefs = Array.isArray(ev.line_refs) && ev.line_refs.length
                        ? `<div class="mini-meta"><span>line refs:</span> ${ev.line_refs.map((lr) => `<code>${esc(String(lr))}</code>`).join(" ")}</div>`
                        : "";
                      const what = ev.what_identified_he ? `<div class="obs-row"><span>מה זוהה</span><p>${esc(ev.what_identified_he)}</p></div>` : "";
                      const how = ev.how_identified_he ? `<div class="obs-row"><span>איך זוהה</span><p>${esc(ev.how_identified_he)}</p></div>` : "";
                      const art = ev.artifact_ref ? `<div class="obs-row"><span>artifact_ref</span><code>${esc(String(ev.artifact_ref))}</code></div>` : "";
                      const q = ev.quote_excerpt ? `<blockquote class="quote-mini">${esc(ev.quote_excerpt)}</blockquote>` : "";
                      return `<li>${what}${how}${art}${lineRefs}${q}</li>`;
                    })
                    .join("")}
                </ul>
              </div>
            </details>` : ""}
          ${(f.implementation_notes_he || []).length ? `<ul class="compact-list">${f.implementation_notes_he.map((n) => `<li>${esc(n)}</li>`).join("")}</ul>` : ""}
          ${sourceDetails(f.sources || [], "מקורות finding")}
        </article>`
        )
        .join("")}
    </div>
  `;
}

function renderSourceObservations(observations) {
  if (!observations || !observations.length) {
    return '<p class="muted">אין עדיין תצפיות מקור מובְנות.</p>';
  }
  return `
    <div class="cards-grid two">
      ${observations
        .map(
          (o) => `
        <article class="hub-card source-obs-card" data-searchable="true" data-search-text="${esc(`${o.what_identified_he || ""} ${o.how_identified_he || ""} ${o.source_id || ""}`)}">
          <div class="finding-head">
            <h4>${esc(o.source_id || "מקור")}</h4>
            <div>${confidencePill(o.confidence)}</div>
          </div>
          <div class="obs-row"><span>מה זוהה</span><p>${esc(o.what_identified_he || "-")}</p></div>
          <div class="obs-row"><span>איך זוהה</span><p>${esc(o.how_identified_he || "-")}</p></div>
          ${o.artifact_ref ? `<div class="obs-row"><span>מיקום/ייחוס</span><code>${esc(o.artifact_ref)}</code></div>` : ""}
          ${(o.line_refs || []).length ? `<div class="obs-row"><span>line refs</span><div class="chip-row">${(o.line_refs || []).map((lr) => `<code>${esc(String(lr))}</code>`).join(" ")}</div></div>` : ""}
          ${o.quote_excerpt ? `<blockquote class="quote-mini">${esc(o.quote_excerpt)}</blockquote>` : ""}
          ${o.notes_he ? `<div class="obs-row"><span>הערות</span><p>${esc(o.notes_he)}</p></div>` : ""}
          ${sourceDetails(o.sources || [], "מקורות תצפית")}
        </article>`
        )
        .join("")}
    </div>
  `;
}

function renderMethodsPanel(methods) {
  if (!methods || !methods.length) {
    return '<p class="muted">אין שיטות נגזרות להצגה. ניתן להוסיף <code>groupb_method</code> בקובץ ה-MD.</p>';
  }
  return `
    <div class="cards-grid two">
      ${methods
        .map(
          (m) => `
        <article class="hub-card method-card" data-searchable="true" data-search-text="${esc(`${m.id || ""} ${m.label_he || ""} ${m.description_he || ""}`)}">
          <div class="finding-head">
            <h4>${esc(m.label_he || m.id || "שיטה")}</h4>
            ${m.status ? statusPill(m.status) : ""}
          </div>
          ${m.description_he ? `<p>${esc(m.description_he)}</p>` : ""}
          ${m.risk_notes_he ? `<p class="muted">${esc(m.risk_notes_he)}</p>` : ""}
          ${m.example_he ? `<p class="muted"><strong>דוגמה:</strong> ${esc(m.example_he)}</p>` : ""}
          ${m.notes_he ? `<p class="muted">${esc(m.notes_he)}</p>` : ""}
          ${m.id ? `<div class="mini-meta"><code>${esc(m.id)}</code></div>` : ""}
          ${sourceDetails(m.sources || [], "מקורות שיטה")}
        </article>`
        )
        .join("")}
    </div>
  `;
}

function renderOpenQuestions(questions) {
  if (!questions || !questions.length) {
    return '<p class="muted">אין שאלות פתוחות רשומות.</p>';
  }
  return `
    <div class="cards-grid two">
      ${questions
        .map(
          (q) => `
        <article class="hub-card question-card" data-searchable="true" data-search-text="${esc(`${q.title_he || ""} ${q.detail_he || ""}`)}">
          <div class="finding-head">
            <h4>${esc(q.title_he || "שאלה פתוחה")}</h4>
            <div>${statusPill(q.status)} ${pill(q.priority || "medium")}</div>
          </div>
          <p>${esc(q.detail_he || "")}</p>
          ${(q.source_ids || []).length ? `<div class="mini-meta"><span>מזהי מקורות:</span> ${q.source_ids.map((s) => `<code>${esc(s)}</code>`).join(" ")}</div>` : ""}
          ${sourceDetails(q.sources || [], "מקורות שאלה")}
        </article>`
        )
        .join("")}
    </div>
  `;
}

function renderKnowledgeDoc(profileId, kind) {
  const kindLabel = kind === "logic" ? "לוגיקה" : "מבנה";
  const analysis = (((DATA.group_b || {})[`${kind}_analysis`]) || {})[profileId] || {};
  const docMeta = analysis.doc_meta || {};
  const validation = analysis.validation || {};
  const tocIdPrefix = `${profileId}-${kind}`;
  const sections = [
    { id: `${tocIdPrefix}-summary`, label: "מה זוהה" },
    { id: `${tocIdPrefix}-findings`, label: "ממצאים" },
    { id: `${tocIdPrefix}-sources`, label: "לפי מקור" },
    { id: `${tocIdPrefix}-methods`, label: "איך זיהינו" },
    { id: `${tocIdPrefix}-gaps`, label: "פערים/שאלות" },
    { id: `${tocIdPrefix}-implications`, label: "השלכות" },
    { id: `${tocIdPrefix}-raw`, label: "Markdown גולמי" },
  ];

  const implications = analysis.implementation_implications || [];
  const confidenceMap = analysis.confidence_scores || {};
  const confidenceChips = Object.keys(confidenceMap).length
    ? Object.entries(confidenceMap)
        .map(([k, v]) => `${confidencePill(k)} <span class="muted">x${esc(String(v))}</span>`)
        .join(" ")
    : '<span class="muted">אין עדיין confidence distribution</span>';

  return `
    <div class="knowledge-layout">
      <aside class="knowledge-toc">
        <div class="hub-card toc-card">
          <h3>${kindLabel} - ניווט</h3>
          <div class="toc-links">
            ${sections.map((s) => `<a href="#${esc(s.id)}" data-hub-anchor="${esc(s.id)}">${esc(s.label)}</a>`).join("")}
          </div>
        </div>
      </aside>

      <div class="knowledge-main">
        <section id="${tocIdPrefix}-summary" class="hub-card" data-searchable="true" data-search-text="${esc(`${analysis.summary_he || ""} ${analysis.status || ""}`)}">
          <h3>${kindLabel} - מה זיהינו (תמצית)</h3>
          <p class="muted">זה הסיכום המהיר של הלשונית. אם אתה רוצה להבין מה לממש, תתחיל מכאן ורק אחר כך תרד לממצאים ולמקורות.</p>
          <div class="finding-head">
            <div class="chip-row">${statusPill(analysis.status)} ${pill(`profile:${uiLabel(profileId)}`)} ${pill(`kind:${kind}`)}</div>
          </div>
          <p class="lead">${esc(analysis.summary_he || "אין תקציר.")}</p>
          <div class="kv-grid">
            <div><span>ממצאים</span><strong>${esc(String((analysis.core_findings || []).length || 0))}</strong></div>
            <div><span>תצפיות מקור</span><strong>${esc(String((analysis.source_observations || []).length || 0))}</strong></div>
            <div><span>שאלות פתוחות</span><strong>${esc(String((analysis.open_questions || []).length || 0))}</strong></div>
            <div><span>שאלות שעדיין פתוחות</span><strong>${esc(String((analysis.open_questions || []).filter((q) => String(q.status || "") === "open").length))}</strong></div>
          </div>
          <div class="mini-meta"><span>התפלגות ודאות:</span> ${confidenceChips}</div>
          <details class="inline-detail">
            <summary>פרטים טכניים של מסמך המקור (לא חובה לקריאה)</summary>
            <div class="detail-body">
              <div class="kv-grid compact">
                <div><span>קובץ מקור</span><code>${esc((docMeta.path) || "-")}</code></div>
                <div><span>סטטוס מסמך</span>${statusPill(docMeta.status || analysis.status)}</div>
              </div>
            </div>
          </details>
          ${(docMeta.missing_sections || []).length ? `<div class="warning-box"><strong>חלקי sections חסרים:</strong> ${(docMeta.missing_sections || []).map((x) => `<code>${esc(x)}</code>`).join(" ")}</div>` : ""}
          ${sourceDetails(analysis.sources || [], "מקורות ניתוח")}
        </section>

        <section id="${tocIdPrefix}-findings" class="hub-card">
          <h3>ממצאים מובנים</h3>
          ${renderFindingsCards(analysis.core_findings || [])}
        </section>

        <section id="${tocIdPrefix}-sources" class="hub-card">
          <h3>לפי מקור - מה זוהה ואיך</h3>
          ${renderSourceObservations(analysis.source_observations || [])}
        </section>

        <section id="${tocIdPrefix}-methods" class="hub-card">
          <h3>איך זיהינו (שיטות חילוץ/ניתוח)</h3>
          ${renderMethodsPanel(analysis.derivation_methods || [])}
        </section>

        <section id="${tocIdPrefix}-gaps" class="hub-card">
          <h3>פערים / שאלות פתוחות / מחלוקות</h3>
          ${(validation.missing_methods || []).length ? `<div class="warning-box"><strong>שיטות חסרות ב-catalog:</strong> ${(validation.missing_methods || []).map((m) => `<code>${esc(m)}</code>`).join(" ")}</div>` : ""}
          ${renderOpenQuestions(analysis.open_questions || [])}
        </section>

        <section id="${tocIdPrefix}-implications" class="hub-card">
          <h3>השלכות להמשך המימוש</h3>
          ${(implications || []).length ? `<ul class="compact-list">${implications.map((x) => `<li data-searchable="true">${esc(x)}</li>`).join("")}</ul>` : '<p class="muted">אין עדיין השלכות מנוסחות.</p>'}
        </section>

        <section id="${tocIdPrefix}-raw" class="hub-card">
          <h3>Markdown גולמי (משני / review)</h3>
          <details class="hub-detail">
            <summary>הצג Markdown גולמי (לא התצוגה הראשית)</summary>
            <div class="detail-body">
              <pre><code>${esc(analysis.raw_markdown || "")}</code></pre>
            </div>
          </details>
        </section>
      </div>
    </div>
  `;
}

function renderPhase1Decisions(profileId) {
  const decisions = ((((DATA.group_b || {}).phase1_decisions || {})[profileId]) || {}).rows || [];
  if (!decisions.length) {
    return '<p class="muted">אין עדיין החלטות Phase 1 מובנות.</p>';
  }
  return `
    <div class="cards-grid two">
      ${decisions.map((d) => `
        <article class="hub-card nested-card" data-searchable="true" data-search-text="${esc(`${d.id || ""} ${d.title_he || ""} ${d.decision_he || ""}`)}">
          <div class="profile-card-head">
            <h4>${esc(d.title_he || d.id || "החלטה")}</h4>
            <div class="chip-row">${statusPill(d.status)} ${confidencePill(d.confidence)}</div>
          </div>
          <p>${esc(d.decision_he || "")}</p>
          ${d.rationale_he ? `<p class="muted">${esc(d.rationale_he)}</p>` : ""}
          ${(d.impacts_he || []).length ? renderListOrMuted(d.impacts_he, "אין השלכות") : ""}
          ${(d.applies_to_checks || []).length ? `<p class="muted">משפיע על gates: ${(d.applies_to_checks || []).map((x) => `<code>${esc(x)}</code>`).join(" ")}</p>` : ""}
          ${sourceDetails(d.sources || [], "מקורות החלטה")}
        </article>
      `).join("")}
    </div>
  `;
}

function renderImplementationContract(profileId) {
  const c = ((((DATA.group_b || {}).implementation_contracts || {})[profileId]) || {});
  if (!Object.keys(c).length) return '<p class="muted">אין חוזה מימוש זמין.</p>';
  return `
    <div class="cards-grid two">
      <article class="hub-card nested-card" data-searchable="true">
        <h4>תיחום Phase 1</h4>
        ${c.summary_he ? `<p>${esc(c.summary_he)}</p>` : ""}
        <h5>נכנס ל-Phase 1</h5>
        ${renderListOrMuted(c.scope_in || [], "טרם הוגדר scope_in")}
        <h5>מחוץ ל-Phase 1 / נדחה</h5>
        ${renderListOrMuted(c.scope_out || [], "אין scope_out")}
      </article>
      <article class="hub-card nested-card">
        <h4>סדר מימוש והנחות</h4>
        <h5>סדר מימוש מומלץ</h5>
        ${renderListOrMuted(c.implementation_order || [], "טרם הוגדר סדר מימוש")}
        <h5>הנחות חוסמות</h5>
        ${renderListOrMuted(c.blocking_assumptions || [], "אין הנחות חוסמות")}
        <h5>נדחה לא חוסם</h5>
        ${renderListOrMuted(c.non_blocking_deferred || [], "אין פריטים שנדחו")}
      </article>
      <article class="hub-card nested-card">
        <h4>חוזה API/Runtime</h4>
        <h5>Service API</h5>
        ${renderNamedObjectKv(c.service_api_contract || {}, { public_functions_he: "פונקציות ציבוריות", callback_contract_he: "קונטרקט callbacks", notes_he: "הערות" })}
        ${(c.service_api_contract || {}).public_functions_he ? renderListOrMuted((c.service_api_contract || {}).public_functions_he, "אין") : ""}
        <h5>Runtime flow</h5>
        ${(c.runtime_flow_contract || {}).steps_he ? renderListOrMuted((c.runtime_flow_contract || {}).steps_he, "אין שלבים") : renderNamedObjectKv(c.runtime_flow_contract || {})}
      </article>
      <article class="hub-card nested-card">
        <h4>חוזה מבני/מדיניות</h4>
        <h5>מודל נתונים</h5>
        ${(c.data_model_contract || {}).items_he ? renderListOrMuted((c.data_model_contract || {}).items_he, "אין items") : renderNamedObjectKv(c.data_model_contract || {})}
        <h5>CCC / notify / indicate</h5>
        ${(c.ccc_and_notify_indicate_contract || {}).rules_he ? renderListOrMuted((c.ccc_and_notify_indicate_contract || {}).rules_he, "אין rules") : renderNamedObjectKv(c.ccc_and_notify_indicate_contract || {})}
        <h5>גבולות מודולים</h5>
        ${renderNamedObjectKv(c.module_boundaries || {}, { modules_he: "מודולים", boundaries_he: "גבולות" })}
        ${(c.module_boundaries || {}).modules_he ? renderListOrMuted((c.module_boundaries || {}).modules_he, "אין מודולים") : ""}
        ${(c.module_boundaries || {}).boundaries_he ? renderListOrMuted((c.module_boundaries || {}).boundaries_he, "אין גבולות") : ""}
      </article>
      <article class="hub-card nested-card">
        <h4>Error / Dependencies</h4>
        <h5>מדיניות שגיאות</h5>
        ${(c.error_policy_contract || {}).rules_he ? renderListOrMuted((c.error_policy_contract || {}).rules_he, "אין rules") : renderNamedObjectKv(c.error_policy_contract || {})}
        <h5>תלויות</h5>
        ${(c.dependency_contract || {}).items_he ? renderListOrMuted((c.dependency_contract || {}).items_he, "אין תלויות") : renderNamedObjectKv(c.dependency_contract || {})}
      </article>
    </div>
    ${sourceDetails(c.sources || [], "מקורות חוזה מימוש")}
  `;
}

function renderPhase1TestTargets(profileId) {
  const t = ((((DATA.group_b || {}).test_targets_phase1 || {})[profileId]) || {});
  if (!Object.keys(t).length) return '<p class="muted">אין יעדי בדיקות Phase 1.</p>';
  return `
    <div class="cards-grid two">
      <article class="hub-card nested-card">
        <h4>בדיקות smoke ידניות</h4>
        ${t.summary_he ? `<p>${esc(t.summary_he)}</p>` : ""}
        ${renderListOrMuted(t.manual_smoke_checks || [], "טרם הוגדר")}
      </article>
      <article class="hub-card nested-card">
        <h4>יעדי PTS / AutoPTS</h4>
        ${renderListOrMuted(t.pts_autopts_target_areas || [], "טרם הוגדר")}
      </article>
      <article class="hub-card nested-card">
        <h4>הנחות ICS / IXIT</h4>
        ${renderListOrMuted(t.ics_ixit_assumptions || [], "טרם הוגדר")}
      </article>
      <article class="hub-card nested-card">
        <h4>קריטריון Done ל-Phase 1</h4>
        ${renderListOrMuted(t.phase1_done_criteria || [], "טרם הוגדר")}
      </article>
      <article class="hub-card nested-card">
        <h4>Known non-goals</h4>
        ${renderListOrMuted(t.known_non_goals || [], "אין")}
      </article>
    </div>
    ${sourceDetails(t.sources || [], "מקורות יעדי בדיקות")}
  `;
}

function renderReviewSignoff(profileId) {
  const s = ((((DATA.group_b || {}).review_signoffs || {})[profileId]) || {});
  if (!Object.keys(s).length) return '<p class="muted">אין חתימת review זמינה.</p>';
  return `
    <div class="cards-grid two">
      <article class="hub-card nested-card">
        <h4>חתימת Review / מוכנות</h4>
        <div class="kv-grid compact">
          <div><span>Logic reviewed</span>${boolPill(!!s.logic_reviewed, "כן", "לא")}</div>
          <div><span>Structure reviewed</span>${boolPill(!!s.structure_reviewed, "כן", "לא")}</div>
          <div><span>מוכן ל-Phase 1</span>${boolPill(!!s.ready_for_impl_phase1, "מוכן", "לא מוכן")}</div>
          <div><span>Logic reviewed at</span><code>${esc(s.logic_reviewed_at || "-")}</code></div>
          <div><span>Structure reviewed at</span><code>${esc(s.structure_reviewed_at || "-")}</code></div>
        </div>
        ${s.review_summary_he ? `<p>${esc(s.review_summary_he)}</p>` : ""}
        ${s.ready_decision_reason_he ? `<p class="muted">${esc(s.ready_decision_reason_he)}</p>` : ""}
      </article>
      <article class="hub-card nested-card">
        <h4>חסמים סופיים (Phase 1)</h4>
        ${(s.remaining_phase1_blockers || []).length ? renderListOrMuted(s.remaining_phase1_blockers || [], "אין") : '<p class="muted">אין חסמים פתוחים ל-Phase 1.</p>'}
        <h5>הערות reviewer</h5>
        ${renderListOrMuted(s.reviewer_notes_he || [], "אין הערות")}
      </article>
    </div>
    ${sourceDetails(s.sources || [], "מקורות חתימת review")}
  `;
}

function renderProfileStatus(profileId) {
  const row = ((((DATA.group_b || {}).status_tracker || {}).rows) || []).find((r) => r.profile_id === profileId) || {};
  const logic = ((((DATA.group_b || {}).logic_analysis || {})[profileId]) || {});
  const structure = ((((DATA.group_b || {}).structure_analysis || {})[profileId]) || {});
  const readiness = (((DATA.group_b || {}).readiness_gates || {}).profiles || {})[profileId] || {};
  const qaMeta = ((DATA.group_b || {}).qa_meta) || {};
  return `
    <div class="profile-sections">
      <section class="hub-card" data-searchable="true">
        <h3>סטטוס עבודה - ${esc(uiLabel(profileId))}</h3>
        <p class="muted">הבלוק הזה עוזר לענות רק על שאלה אחת: האם אפשר להתחיל לממש עכשיו. הנתונים הטכניים המפורטים מופיעים למטה וניתנים לדילוג.</p>
        <div class="kv-grid">
          <div><span>חוזה מימוש</span>${boolPill(row.implementation_contract_defined, "מוגדר", "חסר")}</div>
          <div><span>יעדי בדיקות Phase 1</span>${boolPill(row.phase1_test_targets_defined, "מוגדרים", "חסרים")}</div>
          <div><span>חתימת review</span>${boolPill(row.review_signoff_complete, "הושלמה", "חסרה")}</div>
          <div><span>חסמי Phase 1</span>${boolPill(row.phase1_blockers_closed_or_deferred, "סגורים/נדחו", "פתוחים")}</div>
          <div><span>מוכן ל-Phase 1</span>${boolPill(row.ready_for_impl_phase1, "מוכן", "לא מוכן")}</div>
        </div>
        <details class="hub-detail">
          <summary>הצג פרטי סטטוס טכניים (counts / baseline / סנכרון)</summary>
          <div class="detail-body">
            <div class="kv-grid compact">
              <div><span>סנכרון Spec</span>${statusPill(row.spec_sync_status)}</div>
              <div><span>ארטיפקטים</span><strong>${esc(String(row.spec_artifacts || 0))}</strong></div>
              <div><span>מסמך לוגיקה</span>${statusPill(row.logic_doc_status)}</div>
              <div><span>ממצאי לוגיקה</span><strong>${esc(String(row.logic_findings || 0))}</strong></div>
              <div><span>תצפיות מקור לוגיקה</span><strong>${esc(String(row.logic_source_observations || 0))}</strong></div>
              <div><span>מסמך מבנה</span>${statusPill(row.structure_doc_status)}</div>
              <div><span>ממצאי מבנה</span><strong>${esc(String(row.structure_findings || 0))}</strong></div>
              <div><span>תצפיות מקור מבנה</span><strong>${esc(String(row.structure_source_observations || 0))}</strong></div>
              <div><span>Phase 1 subset</span>${boolPill(row.phase1_subset_decided, "הוגדר", "חסר")}</div>
              <div><span>החלטות Phase 1</span><strong>${esc(String(row.phase1_decisions_count || 0))}</strong></div>
              <div><span>Logic baseline</span>${boolPill(row.logic_analysis_baselined)}</div>
              <div><span>Structure baseline</span>${boolPill(row.structure_analysis_baselined)}</div>
            </div>
          </div>
        </details>
        ${(row.gaps_he || []).length ? `<ul class="compact-list">${(row.gaps_he || []).map((g) => `<li data-searchable="true">${esc(g)}</li>`).join("")}</ul>` : '<p class="muted">אין פערים פתוחים ברשימה.</p>'}
      </section>

      <section class="hub-card">
        <h3>בדיקות מוכנות (Readiness gates) - פירוט טכני</h3>
        <p class="muted">זהו פירוט טכני של check-list פנימי. אם המטרה שלך היא להתחיל לממש, התשובה החשובה כבר מופיעה למעלה בשדה "מוכן ל-Phase 1".</p>
        <div class="cards-grid two">
          <article class="hub-card nested-card">
            <h4>Completed</h4>
            ${(readiness.completed_checks || []).length ? `<ul class="compact-list">${(readiness.completed_checks || []).map((x) => `<li><code>${esc(x)}</code></li>`).join("")}</ul>` : '<p class="muted">אין checks שהושלמו.</p>'}
          </article>
          <article class="hub-card nested-card">
            <h4>Blocked / חסר</h4>
            ${(readiness.blocked_checks || []).length ? `<ul class="compact-list">${(readiness.blocked_checks || []).map((x) => `<li><code>${esc((x || {}).id || "")}</code> — ${esc((x || {}).reason_he || "")}</li>`).join("")}</ul>` : '<p class="muted">אין חסימות.</p>'}
          </article>
        </div>
        ${(readiness.decision_notes_he || []).length ? `<details class="hub-detail"><summary>הערות החלטה / מוכנות</summary><div class="detail-body"><ul class="compact-list">${(readiness.decision_notes_he || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div></details>` : ""}
      </section>

      <section class="hub-card">
        <h3>החלטות Phase 1</h3>
        ${renderPhase1Decisions(profileId)}
      </section>

      <section class="hub-card">
        <h3>חוזה מימוש Phase 1</h3>
        ${renderImplementationContract(profileId)}
      </section>

      <section class="hub-card">
        <h3>יעדי בדיקות Phase 1</h3>
        ${renderPhase1TestTargets(profileId)}
      </section>

      <section class="hub-card">
        <h3>חתימת Review / מוכנות</h3>
        ${renderReviewSignoff(profileId)}
      </section>

      <section class="hub-card">
        <details class="hub-detail">
          <summary>תיקוף schema / מסמכים (טכני, אפשר לדלג)</summary>
          <div class="detail-body">
        <div class="cards-grid two">
          <article class="hub-card nested-card">
            <h4>לוגיקה</h4>
            <div class="kv-grid compact">
              <div><span>סטטוס</span>${statusPill(logic.status)}</div>
              <div><span>sections חסרים</span><strong>${esc(String(((logic.validation || {}).missing_sections || []).length || 0))}</strong></div>
              <div><span>שיטות חסרות</span><strong>${esc(String(((logic.validation || {}).missing_methods || []).length || 0))}</strong></div>
              <div><span>warnings</span><strong>${esc(String(((logic.validation || {}).warnings || []).length || 0))}</strong></div>
            </div>
            ${sourceDetails(logic.sources || [], "מקורות לוגיקה")}
          </article>
          <article class="hub-card nested-card">
            <h4>מבנה</h4>
            <div class="kv-grid compact">
              <div><span>סטטוס</span>${statusPill(structure.status)}</div>
              <div><span>sections חסרים</span><strong>${esc(String(((structure.validation || {}).missing_sections || []).length || 0))}</strong></div>
              <div><span>שיטות חסרות</span><strong>${esc(String(((structure.validation || {}).missing_methods || []).length || 0))}</strong></div>
              <div><span>warnings</span><strong>${esc(String(((structure.validation || {}).warnings || []).length || 0))}</strong></div>
            </div>
            ${sourceDetails(structure.sources || [], "מקורות מבנה")}
          </article>
        </div>
        <details class="hub-detail">
          <summary>QA meta (גלובלי לעמוד)</summary>
          <div class="detail-body">
            <div class="kv-grid compact">
              <div><span>smoke mode</span><code>${esc(qaMeta.smoke_test_mode || "-")}</code></div>
              <div><span>last smoke</span><code>${esc(qaMeta.last_smoke_test_at || "-")}</code></div>
            </div>
            ${(qaMeta.last_manual_review_notes_he || []).length ? `<ul class="compact-list">${(qaMeta.last_manual_review_notes_he || []).map((n) => `<li>${esc(n)}</li>`).join("")}</ul>` : ""}
          </div>
        </details>
          </div>
        </details>
      </section>
    </div>
  `;
}

function renderProfilePanel(profileId) {
  const root = document.getElementById(`hubProfile${profileId}Content`);
  if (!root) return;
  const subtab = state.profileSubtabs[profileId] || "status";
  const spec = ((((DATA.group_b || {}).spec_research || {}).profiles) || {})[profileId] || {};
  const logic = ((((DATA.group_b || {}).logic_analysis || {})[profileId]) || {});
  const structure = ((((DATA.group_b || {}).structure_analysis || {})[profileId]) || {});

  let body = "";
  if (subtab === "specs") body = renderProfileSpecsSimple(profileId);
  else if (subtab === "logic") body = renderProfileLogicSimple(profileId);
  else if (subtab === "structure") body = renderProfileStructureSimple(profileId);
  else body = renderProfileCurrentWork(profileId);

  root.innerHTML = `
    <div class="hub-panel-grid">
      <section class="hub-card span-12" data-searchable="true" data-search-text="${esc(`${uiLabel(profileId)} ${displayNameHe(profileId)} ${(spec.resolved_title || "")}`)}">
        <div class="profile-hero-head">
          <div>
            <h2>${esc(uiLabel(profileId))}</h2>
            <p class="lead">${esc(displayNameHe(profileId))}</p>
          </div>
          <div class="chip-row">
            ${statusPill(spec.sync_status)}
            ${statusPill(logic.status)}
            ${statusPill(structure.status)}
          </div>
        </div>
        ${renderProfileSubtabs(profileId)}
      </section>
      ${renderProfileSubtabGuide(profileId, subtab)}
      <section class="span-12">
        ${body}
      </section>
    </div>
  `;
}

function renderSourcesTab() {
  const root = document.getElementById("hubSourcesContent");
  if (!root) return;
  const group = DATA.group_b || {};
  const policy = group.sources_policy || {};
  const official = group.official_sources || {};
  const sdk = group.sdk_sources || {};
  const methods = group.derivation_methods_catalog || {};
  const trace = group.traceability_index || {};

  const policyCards = ["sig", "sdk_nordic", "sdk_ti", "autopts_official", "ux_ui"]
    .map((key) => {
      const row = policy[key] || {};
      if (!row || !row.allowed_domains) return "";
      return `
      <article class="hub-card nested-card" data-searchable="true" data-search-text="${esc(`${key} ${(row.allowed_domains || []).join(" ")}`)}">
        <h4>${esc(key)}</h4>
        <p class="muted">${esc(row.rule_he || "")}</p>
        <div class="chip-row">${(row.allowed_domains || []).map((d) => pill(d)).join(" ")}</div>
      </article>`;
    })
    .join("");

  const officialRows = (official.entries || [])
    .map(
      (e) => `
      <tr data-searchable="true" data-search-text="${esc(`${e.id || ""} ${e.title || ""} ${e.domain || ""}`)}">
        <td><code>${esc(e.id || "-")}</code></td>
        <td>${sourceRef(e)}</td>
        <td><code>${esc(e.domain || "-")}</code></td>
        <td>${esc((e.profile_ids || []).join(", ") || "-")}</td>
        <td>${esc(e.category || "-")}</td>
        <td>${esc(e.retrieved_at || "-")}</td>
      </tr>`
    )
    .join("");

  const sdkRows = (sdk.entries || [])
    .map(
      (e) => `
      <tr data-searchable="true" data-search-text="${esc(`${e.id || ""} ${e.title || ""} ${e.vendor || ""} ${e.domain || ""}`)}">
        <td><code>${esc(e.id || "-")}</code></td>
        <td>${sourceRef(e)}</td>
        <td>${esc(e.vendor || "-")}</td>
        <td>${esc((e.used_for || []).join(", ") || "-")}</td>
        <td><code>${esc(e.domain || "-")}</code></td>
        <td>${esc(e.retrieved_at || "-")}</td>
      </tr>`
    )
    .join("");

  const methodRows = (methods.methods || [])
    .map(
      (m) => `
      <tr data-searchable="true" data-search-text="${esc(`${m.id || ""} ${m.label_he || ""}`)}">
        <td><code>${esc(m.id || "-")}</code></td>
        <td>${esc(m.label_he || "-")}</td>
        <td>${esc(m.description_he || "-")}</td>
        <td>${esc(m.risk_notes_he || "-")}</td>
      </tr>`
    )
    .join("");

  const localRows = (trace.local || [])
    .slice(0, 120)
    .map(
      (r) => `
      <tr data-searchable="true">
        <td><code>${esc(r.file || "-")}${r.line ? `:${esc(String(r.line))}` : ""}</code></td>
        <td>${esc(String(r.count || 0))}</td>
      </tr>`
    )
    .join("");

  const webRows = (trace.web || [])
    .map(
      (r) => `
      <tr data-searchable="true" data-search-text="${esc(`${r.url || ""} ${r.title || ""}`)}">
        <td>${sourceRef(r)}</td>
        <td><code>${esc(r.retrieved_at || "-")}</code></td>
        <td>${esc(String(r.count || 0))}</td>
      </tr>`
    )
    .join("");

  root.innerHTML = `
    <div class="hub-panel-grid">
      <section class="hub-card span-12">
        <h2>מקורות ועקיבות</h2>
        <p class="lead">כל המידע בעמוד נשען על קבצי מקור מקומיים או מקורות רשמיים מאושרים בלבד, עם עקיבות למקור ולשיטת חילוץ.</p>
        <ul class="compact-list">
          ${(policy.enforcement_rules || []).map((x) => `<li data-searchable="true">${esc(x)}</li>`).join("")}
        </ul>
        ${sourceDetails(policy.sources || [], "מקורות מדיניות")}
      </section>

      <section class="hub-card span-12">
        <h3>Source policy - whitelists</h3>
        <div class="cards-grid two">${policyCards}</div>
      </section>

      <section class="hub-card span-12">
        <h3>מקורות רשמיים (SIG + UX/UI)</h3>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>מקור</th><th>Domain</th><th>פרופילים</th><th>קטגוריה</th><th>retrieved</th></tr></thead>
            <tbody>${officialRows || '<tr><td colspan="6" class="muted">אין נתונים.</td></tr>'}</tbody>
          </table>
        </div>
        ${sourceDetails(official.sources || [], "מקורות manifest")}
      </section>

      <section class="hub-card span-12">
        <h3>מקורות SDK (Nordic / TI)</h3>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>מקור</th><th>Vendor</th><th>שימוש</th><th>Domain</th><th>retrieved</th></tr></thead>
            <tbody>${sdkRows || '<tr><td colspan="6" class="muted">אין נתונים.</td></tr>'}</tbody>
          </table>
        </div>
        ${sourceDetails(sdk.sources || [], "מקורות manifest")}
      </section>

      <section class="hub-card span-12">
        <h3>מילון שיטות חילוץ/ניתוח</h3>
        <div class="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>שם</th><th>תיאור</th><th>סיכון/הטיה</th></tr></thead>
            <tbody>${methodRows || '<tr><td colspan="4" class="muted">אין נתונים.</td></tr>'}</tbody>
          </table>
        </div>
        ${sourceDetails(methods.sources || [], "מקורות methods catalog")}
      </section>

      <section class="hub-card span-12">
        <h3>Traceability index</h3>
        <div class="cards-grid two">
          <div class="hub-card nested-card"><h4>סיכום</h4><div class="kv-grid compact"><div><span>Local sources</span><strong>${esc(String((trace.summary || {}).local_sources || 0))}</strong></div><div><span>Web sources</span><strong>${esc(String((trace.summary || {}).web_sources || 0))}</strong></div></div></div>
          <div class="hub-card nested-card"><h4>Known limits</h4><ul class="compact-list">${((DATA.known_limits || {}).items || []).map((i) => `<li>${esc(i.title_he || "")} — ${esc(i.detail_he || "")}</li>`).join("")}</ul></div>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Local file[:line]</th><th>Refs</th></tr></thead>
            <tbody>${localRows || '<tr><td colspan="2" class="muted">אין נתונים.</td></tr>'}</tbody>
          </table>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Web URL</th><th>retrieved</th><th>Refs</th></tr></thead>
            <tbody>${webRows || '<tr><td colspan="3" class="muted">אין נתונים.</td></tr>'}</tbody>
          </table>
        </div>
      </section>
    </div>
  `;
}

function renderAllPanels() {
  renderAutoptsTab();
  renderProfilePanel("BPS");
  renderProfilePanel("WSS");
  renderProfilePanel("SCPS");
  renderKnowledgeCenterTab();
  renderSourcesTab();
}

function bindEvents() {
  if (topTabsContainer) {
    topTabsContainer.addEventListener("click", (event) => {
      const btn = event.target.closest ? event.target.closest("[data-hub-top-tab]") : null;
      if (!btn) return;
      activateTopTab(btn.getAttribute("data-hub-top-tab") || "BPS");
    });
  }

  document.addEventListener("click", (event) => {
    const jumpBtn = event.target.closest ? event.target.closest("[data-jump-profile]") : null;
    if (jumpBtn) {
      const pid = jumpBtn.getAttribute("data-jump-profile");
      if (!pid) return;
      activateTopTab(pid);
      return;
    }

    const subtabBtn = event.target.closest ? event.target.closest("[data-profile-subtab]") : null;
    if (subtabBtn) {
      const raw = subtabBtn.getAttribute("data-profile-subtab") || "";
      const [profileId, subtabId] = raw.split(":");
      if (!profileId || !subtabId) return;
      setProfileSubtab(profileId, subtabId);
      return;
    }

    const anchor = event.target.closest ? event.target.closest("[data-hub-anchor]") : null;
    if (anchor) {
      const id = anchor.getAttribute("data-hub-anchor");
      if (!id) return;
      const target = document.getElementById(id);
      if (!target) return;
      event.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      return;
    }

    if (event.target.closest && (event.target.closest("[data-task-field]") || event.target.closest(".task-inline-quick-edit"))) {
      return;
    }

    const modeBtn = event.target.closest ? event.target.closest("[data-task-view-mode]") : null;
    if (modeBtn) {
      const raw = modeBtn.getAttribute("data-task-view-mode") || "";
      const [profileId, mode] = raw.split(":");
      if (!profileId || !mode) return;
      setTaskBoardUiField(profileId, "viewMode", mode);
      renderProfilePanel(profileId);
      return;
    }

    const chipBtn = event.target.closest ? event.target.closest("[data-task-chip]") : null;
    if (chipBtn) {
      const raw = chipBtn.getAttribute("data-task-chip") || "";
      const [profileId, chip] = raw.split(":");
      if (!profileId) return;
      setTaskBoardChip(profileId, chip || "all");
      setTaskBoardUiField(profileId, "expandedTask", null);
      renderProfilePanel(profileId);
      return;
    }

    const stageBtn = event.target.closest ? event.target.closest("[data-task-group-toggle]") : null;
    if (stageBtn) {
      const raw = stageBtn.getAttribute("data-task-group-toggle") || "";
      const [profileId, groupId] = raw.split(":");
      if (!profileId || !groupId) return;
      toggleTaskBoardGroup(profileId, groupId);
      renderProfilePanel(profileId);
      return;
    }

    const taskCard = event.target.closest ? event.target.closest("[data-task-card-toggle]") : null;
    if (taskCard) {
      const raw = taskCard.getAttribute("data-task-card-toggle") || "";
      const [profileId, taskId] = raw.split(":");
      if (!profileId || !taskId) return;
      toggleTaskBoardTaskCard(profileId, taskId);
      renderProfilePanel(profileId);
      return;
    }
  });

  document.addEventListener("change", (event) => {
    const filterEl = event.target && event.target.closest ? event.target.closest("[data-task-board-filter]") : null;
    if (filterEl) {
      const profileId = filterEl.getAttribute("data-profile-id") || "";
      const field = filterEl.getAttribute("data-task-board-filter") || "";
      if (!profileId || !field) return;
      setTaskBoardFilter(profileId, field, "value" in filterEl ? filterEl.value : "");
      setTaskBoardUiField(profileId, "expandedTask", null);
      renderProfilePanel(profileId);
      return;
    }
    const sortEl = event.target && event.target.closest ? event.target.closest("[data-task-board-sort]") : null;
    if (sortEl) {
      const profileId = sortEl.getAttribute("data-profile-id") || "";
      if (!profileId) return;
      setTaskBoardUiField(profileId, "sort", "value" in sortEl ? sortEl.value : "default");
      setTaskBoardUiField(profileId, "expandedTask", null);
      renderProfilePanel(profileId);
    }
  });

  const handleTaskFieldEvent = (event) => {
    const el = event.target && event.target.closest ? event.target.closest("[data-task-field]") : null;
    if (!el) return;
    const profileId = el.getAttribute("data-profile-id") || "";
    const taskId = el.getAttribute("data-task-id") || "";
    const field = el.getAttribute("data-task-field") || "";
    if (!profileId || !taskId || !field) return;
    const rawValue = "value" in el ? el.value : "";
    const value = normalizeTaskFieldValue(field, rawValue);
    updateTaskStateValue(profileId, taskId, field, value);

    const compactEdit = el.hasAttribute && el.hasAttribute("data-task-compact-edit");
    if (field === "status" || (compactEdit && field === "assignee")) {
      renderProfilePanel(profileId);
    }

    scheduleTaskSave(`${profileId}:${taskId}:${field}`);
  };

  document.addEventListener("change", handleTaskFieldEvent);
  document.addEventListener("input", (event) => {
    const filterEl = event.target && event.target.closest ? event.target.closest("[data-task-board-filter]") : null;
    if (filterEl && (filterEl.tagName || "").toLowerCase() === "input") {
      const profileId = filterEl.getAttribute("data-profile-id") || "";
      const field = filterEl.getAttribute("data-task-board-filter") || "";
      if (!profileId || !field) return;
      setTaskBoardFilter(profileId, field, filterEl.value || "");
      setTaskBoardUiField(profileId, "expandedTask", null);
      renderProfilePanel(profileId);
      return;
    }
    const el = event.target && event.target.closest ? event.target.closest("[data-task-field]") : null;
    if (!el) return;
    const tag = String(el.tagName || "").toLowerCase();
    const field = el.getAttribute("data-task-field") || "";
    // Text inputs/textareas should update state while typing, selects are handled on change.
    if (tag === "select") return;
    if (field === "depends_on") return;
    handleTaskFieldEvent(event);
  });

  if (hubSearchInput) {
    hubSearchInput.addEventListener("input", applySearch);
  }

  const clearBtn = document.getElementById("hubClearSearchBtn");
  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (hubSearchInput) hubSearchInput.value = "";
      applySearch();
      if (hubSearchInput) hubSearchInput.focus();
    });
  }

  const openSourcesBtn = document.getElementById("hubOpenSourcesBtn");
  if (openSourcesBtn) {
    openSourcesBtn.addEventListener("click", () => {
      const panel = activePanel();
      if (!panel) return;
      panel.querySelectorAll(".src-details").forEach((d) => {
        d.open = true;
      });
    });
  }

  const closeSourcesBtn = document.getElementById("hubCloseSourcesBtn");
  if (closeSourcesBtn) {
    closeSourcesBtn.addEventListener("click", () => {
      const panel = activePanel();
      if (!panel) return;
      panel.querySelectorAll(".src-details").forEach((d) => {
        d.open = false;
      });
    });
  }
}

async function bootstrap() {
  renderTopTabsNav();
  renderQuickStatus();
  renderAllPanels();
  bindEvents();
  activateTopTab("BPS");
  await loadGroupBTasksState();
  renderProfilePanel("BPS");
  renderProfilePanel("WSS");
  renderProfilePanel("SCPS");
  applySearch();
}

bootstrap();
