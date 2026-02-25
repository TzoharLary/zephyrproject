const DATA = window.AUTOPTS_HUB_DATA || {};

const topTabsContainer = document.getElementById("hubTopTabsNav");
const quickStatusContainer = document.getElementById("hubQuickStatus");
const hubSearchInput = document.getElementById("hubSearchInput");

const state = {
  topTab: "overview",
  profileSubtabs: {
    BPS: "specs",
    WSS: "specs",
    SCPS: "specs",
  },
};

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
  if (s === "reviewed") return pill("נסקר", "mandatory");
  if (s === "ready") return pill("מוכן", "mandatory");
  if (s === "blocked") return pill("חסום", "conditional");
  if (s) return pill(s);
  return pill("—");
}

function boolPill(flag, yes = "כן", no = "לא") {
  return flag ? pill(yes, "mandatory") : pill(no, "conditional");
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
  const status = ((DATA.group_b || {}).status_tracker || {}).summary || {};
  quickStatusContainer.innerHTML = `
    <div class="quick-stat-grid">
      <div class="quick-stat"><span>Specs שסונכרנו</span><strong>${esc(String(status.spec_synced || 0))}/${esc(String(status.profiles || 0))}</strong></div>
      <div class="quick-stat"><span>פרופילים עם ממצאי לוגיקה</span><strong>${esc(String(status.logic_with_findings || 0))}</strong></div>
      <div class="quick-stat"><span>פרופילים עם ממצאי מבנה</span><strong>${esc(String(status.structure_with_findings || 0))}</strong></div>
      <div class="quick-stat"><span>לוגיקה baseline</span><strong>${esc(String(status.logic_baselined || 0))}</strong></div>
      <div class="quick-stat"><span>מבנה baseline</span><strong>${esc(String(status.structure_baselined || 0))}</strong></div>
      <div class="quick-stat"><span>מוכנים ל-Phase 1</span><strong>${esc(String(status.ready_for_impl_phase1 || 0))}</strong></div>
    </div>
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
          <div class="finding-head">
            <div class="chip-row">${statusPill(analysis.status)} ${pill(`profile:${uiLabel(profileId)}`)} ${pill(`kind:${kind}`)}</div>
          </div>
          <p class="lead">${esc(analysis.summary_he || "אין תקציר.")}</p>
          <div class="kv-grid">
            <div><span>ממצאים</span><strong>${esc(String((analysis.core_findings || []).length || 0))}</strong></div>
            <div><span>תצפיות מקור</span><strong>${esc(String((analysis.source_observations || []).length || 0))}</strong></div>
            <div><span>שאלות פתוחות</span><strong>${esc(String((analysis.open_questions || []).length || 0))}</strong></div>
            <div><span>קובץ מקור</span><code>${esc((docMeta.path) || "-")}</code></div>
          </div>
          <div class="mini-meta"><span>התפלגות ודאות:</span> ${confidenceChips}</div>
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
        <div class="kv-grid">
          <div><span>סנכרון Spec</span>${statusPill(row.spec_sync_status)}</div>
          <div><span>ארטיפקטים</span><strong>${esc(String(row.spec_artifacts || 0))}</strong></div>
          <div><span>מסמך לוגיקה</span>${statusPill(row.logic_doc_status)}</div>
          <div><span>ממצאי לוגיקה</span><strong>${esc(String(row.logic_findings || 0))}</strong></div>
          <div><span>תצפיות מקור לוגיקה</span><strong>${esc(String(row.logic_source_observations || 0))}</strong></div>
          <div><span>מסמך מבנה</span>${statusPill(row.structure_doc_status)}</div>
          <div><span>ממצאי מבנה</span><strong>${esc(String(row.structure_findings || 0))}</strong></div>
          <div><span>תצפיות מקור מבנה</span><strong>${esc(String(row.structure_source_observations || 0))}</strong></div>
          <div><span>Phase 1 subset</span>${boolPill(row.phase1_subset_decided, "הוגדר", "חסר")}</div>
          <div><span>Logic baseline</span>${boolPill(row.logic_analysis_baselined)}</div>
          <div><span>Structure baseline</span>${boolPill(row.structure_analysis_baselined)}</div>
          <div><span>מוכן ל-Phase 1</span>${boolPill(row.ready_for_impl_phase1, "מוכן", "לא מוכן")}</div>
        </div>
        ${(row.gaps_he || []).length ? `<ul class="compact-list">${(row.gaps_he || []).map((g) => `<li data-searchable="true">${esc(g)}</li>`).join("")}</ul>` : '<p class="muted">אין פערים פתוחים ברשימה.</p>'}
      </section>

      <section class="hub-card">
        <h3>Readiness gates (מפורטים)</h3>
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
        <h3>תיקוף schema / מסמכים</h3>
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
      </section>
    </div>
  `;
}

function renderProfilePanel(profileId) {
  const root = document.getElementById(`hubProfile${profileId}Content`);
  if (!root) return;
  const subtab = state.profileSubtabs[profileId] || "specs";
  const spec = ((((DATA.group_b || {}).spec_research || {}).profiles) || {})[profileId] || {};
  const logic = ((((DATA.group_b || {}).logic_analysis || {})[profileId]) || {});
  const structure = ((((DATA.group_b || {}).structure_analysis || {})[profileId]) || {});

  let body = "";
  if (subtab === "specs") body = renderProfileSpecs(profileId);
  else if (subtab === "logic") body = renderKnowledgeDoc(profileId, "logic");
  else if (subtab === "structure") body = renderKnowledgeDoc(profileId, "structure");
  else body = renderProfileStatus(profileId);

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
  renderOverviewTab();
  renderAutoptsTab();
  renderProfilePanel("BPS");
  renderProfilePanel("WSS");
  renderProfilePanel("SCPS");
  renderSourcesTab();
}

function bindEvents() {
  if (topTabsContainer) {
    topTabsContainer.addEventListener("click", (event) => {
      const btn = event.target.closest ? event.target.closest("[data-hub-top-tab]") : null;
      if (!btn) return;
      activateTopTab(btn.getAttribute("data-hub-top-tab") || "overview");
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

function bootstrap() {
  renderTopTabsNav();
  renderQuickStatus();
  renderAllPanels();
  bindEvents();
  activateTopTab("overview");
}

bootstrap();
