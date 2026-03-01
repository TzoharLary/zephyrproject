# Zephyr BLE GATT Profile Builder — System Journal

> **Purpose of this document:** Provide precise historical context for any future agent or developer reading this repo. After reading this file, the reader should know exactly what the system is, why every design decision was made, what bugs were found and fixed, and what the intended next steps are.
>
> **Last updated:** 2026-03-01
> **Current status:** Phase 1 complete. All 24 profiles validated. System ready for Phase 2.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [File Architecture](#2-file-architecture)
3. [Creation Timeline](#3-creation-timeline)
4. [Phase 1: Design Decisions](#4-phase-1-design-decisions)
5. [Phase 1: Complete Bug Inventory](#5-phase-1-complete-bug-inventory)
6. [Data Schema — Field-by-Field Meaning for the Agent](#6-data-schema--field-by-field-meaning-for-the-agent)
7. [Current State (as of 2026-03-01)](#7-current-state-as-of-2026-03-01)
8. [What Phase 2 Should Look Like](#8-what-phase-2-should-look-like)

---

## 1. System Overview

### What it is

The **Zephyr BLE GATT Profile Builder** is a knowledge-driven agent that creates, extends, explains, and debugs Bluetooth Low Energy GATT profiles for Zephyr RTOS.

### Core principle

The agent operates from **pre-loaded, structured knowledge** — it does NOT perform unguided research at runtime. All knowledge is pre-researched and stored in three files under `.github/data/`. The agent queries those files instead of re-researching every time.

### What the agent can do (4 actions)

| Action | Description |
|--------|-------------|
| `create` | Build a new BLE GATT profile from scratch |
| `extend` | Add characteristics to an existing profile |
| `understand` | Explain structure and architecture |
| `debug` | Diagnose and fix an existing implementation |

### Non-negotiable rules

- Output is **always Zephyr-native**. Never Nordic SDK style, never TI SDK style.
- No unguided internet research at runtime. Only sources defined in `sources-map.yaml`.
- All generated code follows Zephyr patterns: `BT_GATT_SERVICE_DEFINE`, `bt_gatt_attr_read/write`, `BT_GATT_CCC`, `BT_UUID_DECLARE_16`, `LOG_MODULE_REGISTER`.

### Input levels supported

| User provides | Agent behavior |
|--------------|----------------|
| Full (UUIDs + characteristics + requirements) | Classify → Match → Generate immediately |
| Partial (e.g. service UUID only) | Classify → Fill gaps from BT Spec → Generate |
| Name only (e.g. "Temperature Profile") | Classify → Map to ESS or similar → Research spec → Generate |
| Nothing (e.g. "I need a BLE sensor") | Ask one focused question → Then proceed |

---

## 2. File Architecture

All system files live under `.github/`:

```
.github/
├── data/
│   ├── profiles-db.yaml          # The knowledge database (24 profiles)
│   ├── profile-patterns.md       # Static implementation patterns
│   └── sources-map.yaml          # Source governance rules
├── docs/
│   └── system-journal.md         # THIS FILE — historical context
├── instructions/
│   └── zephyr-bt-profile-builder.instructions.md   # Agent behavior rules
└── prompts/
    └── zephyr-bt-profile-builder.prompt.md          # 5-step agent workflow
```

### What each file does

#### `profiles-db.yaml` — The Agent's Brain
Contains metadata for all 24 Zephyr BLE GATT profiles. Every field maps directly to a decision the agent makes during CLASSIFY or BUILD:

- `type: Simple/Complex` → which code template to use
- `has_control_point` → whether to generate RACP / SC CP / OACP handler
- `uses_indicate` → whether to generate semaphore + `bt_gatt_indicate()` flow
- `per_connection_state_required` → whether to add `bt_conn` callbacks + per-connection struct
- `pattern: Notify/Indicate/Read/...` → which characteristic property type to generate
- `similar_profiles` → from which existing profile to adapt the output

Without this file being **correct**, the agent generates wrong code silently. This is why Phase 1 existed.

#### `profile-patterns.md` — Static Implementation Knowledge
Pre-researched, permanent documentation of every implementation pattern the agent needs:
- Simple profile: `.h` / `.c` / `Kconfig` templates
- Complex profile: state machine, CCC, connection callbacks
- All characteristic types: Read, Write, Write-Without-Response, Notify, Indicate, Mixed
- Phase 1 discovered patterns (§10.1–§10.7): SCPS server-request-refresh, Indicate-based measurement delivery, Conditional Feature Indication, Technical Tag classification rules, ESS Extended Descriptor, RACP (GLS/CGMS/PLXS), SC Control Point (RSCS/CSCS)

#### `sources-map.yaml` — Research Governance
Defines which sources the agent may consult, for what purpose, in what priority order, and what is forbidden. Prevents the agent from copying Nordic/TI code into Zephyr output.

Priority order:
1. Zephyr RTOS (primary — always first, all implementation)
2. TI SimpleLink Zephyr (reference — Zephyr-compatible alternatives)
3. Intel Auto-PTS (validation — compliance and edge cases)
4. Bluetooth SIG Specification (specification — UUIDs, mandatory/optional)
5. Nordic nRF Connect SDK (logic understanding **only** — never copy code)

#### `zephyr-bt-profile-builder.instructions.md` — Behavior Rules
Formal rules for the agent covering: Simple vs. Complex classification criteria (exact thresholds), source priority and per-source usage policy, Zephyr naming conventions, how to handle missing input, how to handle profiles not in the database, Nordic usage policy, output quality checklist, anti-patterns table.

#### `zephyr-bt-profile-builder.prompt.md` — 5-Step Workflow
The agent's explicit step-by-step process:
1. **IDENTIFY** — Which profile? What action? What data does the user have?
2. **CLASSIFY** — Query profiles-db.yaml; determine Simple/Complex; find reference profile
3. **RESEARCH** — Only if profile not in DB; consult sources in priority order
4. **BUILD** — Generate `.h` + `.c` + `Kconfig` using patterns from profile-patterns.md
5. **EXPLAIN** — Show flow, explain UUID placement, explain reference choice

---

## 3. Creation Timeline

### Issue #1 — Founding document (2026-02-25)
**Title:** "Build Zephyr BLE GATT Profile Builder System"
**Author:** TzoharLary
**Status:** Closed by PR #2

This issue defined the entire system from scratch. Key decisions made here:
- Five deliverables: profiles-db, sources-map, profile-patterns, prompt file, instruction file
- The 5-step agent flow (IDENTIFY → CLASSIFY → RESEARCH → BUILD → EXPLAIN)
- Minimum 12 profiles to cover (HRS, DIS, BAS, HTS, ESS, CTS, LLS, TPS, IAS, OTS, HIDS + more)
- Four input levels (full → partial → name only → nothing)
- Output rules: always Zephyr-native, never copy Nordic/TI

### PR #2 — Framework baseline (2026-02-25 to 2026-02-26)
**Title:** "Add Zephyr BLE GATT Profile Builder System (with Phase 1 Validation)"
**Author:** Copilot SWE agent
**Merged by:** TzoharLary
**Fixes:** Issue #1
**Added:** 2831 lines across 5 new files

This PR created all five system files. However, it explicitly acknowledged that Phase 1 was only a **spot-check on 6 profiles** (HRS, BAS, DIS, HTS, ESS, OTS), with the remaining 18+ profiles unvalidated. BPS was also discovered during this PR (present in `docs/profiles/BPS/` but missing from the DB) and added.

PR #2 introduced 3 new technical classification fields to the DB schema:
- `has_control_point` — true for profiles with RACP, HID CP, or OTS OACP
- `uses_indicate` — true for profiles that use Indicate
- `per_connection_state_required` — true for profiles requiring per-connection state tracking

### Issue #3 — Phase 1 completion mandate (2026-02-26)
**Title:** "Phase 1 Completion: Comprehensive GATT Profile Data Extraction (All Sources)"
**Author:** TzoharLary
**Status:** Closed by PR #8

This issue explicitly rejected the baseline as "done" and mandated full deep validation:
> "This is NOT 'framework validation on 6 profiles'. This IS 'full cross-source, profile-level deep analysis for all profiles'."

**Definition of Done per profile (6 criteria):**
1. UUID verification against BT SIG spec PDFs
2. Characteristic mapping — names, properties, required descriptors
3. Mandatory/optional correctness
4. Complexity classification validation
5. Technical tags correctness (`has_control_point`, `uses_indicate`, `per_connection_state_required`)
6. Pattern extraction → update `profile-patterns.md`

**PR strategy:** Batches of 6–8 profiles per PR, using `Refs #3` until the final batch which used `Fixes #3`.

### PR #4 — Review debt cleanup (2026-02-26)
**Title:** "Review Debt Cleanup (baseline correctness) — Refs #3"
**Branch:** `review-debt-cleanup`
**Changed files:** 3 | **+31 / -26**

Resolved 7 unimplemented review comments from PR #2's automated Copilot review that were merged without being acted upon. See [Phase 1: Complete Bug Inventory](#5-phase-1-complete-bug-inventory) for full details.

### PR #5 — Phase 1 Batch 1 (2026-02-26)
**Title:** "Phase 1 Batch 1: Deep Validation (HRS, BAS, DIS, HTS, ESS, OTS) — Refs #3"
**Branch:** `phase1-batch1`
**Changed files:** 2 | **+99 / -15**

Upgraded the 6 spot-checked profiles from baseline to deep validation. Discovered the ESS Extended Descriptor Pattern (§10.5). Fixed HRS complexity and `has_control_point` flag.

### PR #6 — Phase 1 Batch 2 (2026-02-26)
**Title:** "Phase 1 Batch 2: Deep Validation (CTS, LLS, TPS, IAS, SPS, RSCS) — Refs #3"
**Branch:** `phase1-batch2`
**Changed files:** 1 | **+17 / -9**

Fixed RSCS `has_control_point` and `uses_indicate` (SC Control Point discovered). Added metadata for all 6 profiles. Documented the SPS server-request-refresh pattern cross-reference (§10.1).

### PR #7 — Phase 1 Batch 3 (2026-02-26)
**Title:** "Phase 1 Batch 3: Deep Validation (CSCS, GLS, HIDS, ANS, PASS, UDS) — Refs #3"
**Branch:** `phase1-batch3`
**Changed files:** 1 | **+18 / -10**

Fixed CSCS (same SC CP bugs as RSCS). Fixed GLS pattern (Indicate → Notify). Added metadata for all 6 profiles.

### PR #8 — Phase 1 Batch 4 / Final (2026-02-26)
**Title:** "Phase 1 Batch 4: Final Validation (BCS, WSS, CGMS, PLXS, IPS, BPS) — Fixes #3"
**Branch:** `phase1-batch4`

Fixed BCS/WSS complexity (Medium → Low). Fixed PLXS `has_control_point` (RACP present). Added RACP pattern (§10.6) and SC Control Point pattern (§10.7) to `profile-patterns.md`. Resolved merge conflict with Batch 1 (`profile-patterns.md` additive-only). Marked Phase 1 complete in DB header.

---

## 4. Phase 1: Design Decisions

### Decision: Source priority order
**Chosen order:** Zephyr → TI SimpleLink → Auto-PTS → BT Spec → Nordic

**Rationale:** Zephyr is always primary because the system generates Zephyr-native code. TI SimpleLink is second because it is a Zephyr fork with Zephyr-compatible code (not a foreign SDK). Auto-PTS is third because it defines compliance requirements that must be met. BT Spec is fourth because it is authoritative for UUIDs/fields but says nothing about implementation. Nordic is last because it has rich business logic but uses non-Zephyr APIs and must never be copied.

PR #4 fixed a conflict between the prompt file (which ordered BT Spec before Auto-PTS and TI) and `sources-map.yaml`. The sources-map is now the single authoritative definition.

### Decision: `has_control_point` is a presence flag, not a mandatory flag
**Rationale (from PR #5, HRS):** "The flag tracks presence, not mandatory status." A characteristic can be optional in the spec but still require a protocol handler when present. If the flag only tracked mandatory characteristics, the agent would miss implementing the handler for optional-but-present control points. For example, HR Control Point (0x2A39) is optional in HRS spec, but `has_control_point: true` ensures the agent knows a WRITE+response protocol exists.

### Decision: `pattern` field reflects primary data flow, not control mechanism
**Rationale (from PR #7, GLS):** GLS was initially classified as `pattern: Indicate` because RACP uses Indicate for responses. Corrected to `pattern: Notify` because the **primary data delivery** (Glucose Measurement 0x2A18) is Notify. The agent uses `pattern` to choose the main characteristic property type in generated code. Using Indicate as the pattern would produce wrong `bt_gatt_indicate()` code for the main data stream. RACP Indicate is captured separately via `has_control_point: true` and the RACP pattern in §10.6.

### Decision: Complexity is determined by rule, not by judgment
**Classification rules in `instructions.md`:**
- `Simple`: ≤4 characteristics, no per-connection state, single access pattern
- `Complex`: any of — ≥5 characteristics, per-connection state tracking, has control point, multiple CCCs, connection/disconnection callbacks, operational modes

**Why explicit thresholds matter:** Without rigid rules, PRs #4 had DIS/ANS/IPS all misclassified as Simple. Three profiles with 8, 5, and 9 characteristics respectively. The agent would have generated Simple templates (no state machine, no multiple CCC tracking) for profiles that absolutely require Complex structure.

### Decision: Batches of 6 profiles per Phase 1 PR
**Rationale:** Smaller diffs prevent large merge conflicts and make review tractable. The independent-branch strategy (all batches branching from the same `main` SHA) was chosen because each batch edits different profile blocks in `profiles-db.yaml` — guaranteed non-conflicting except for `profile-patterns.md` where additive sections can conflict (handled in Batch 4 merge conflict resolution).

---

## 5. Phase 1: Complete Bug Inventory

### P0 — Safety / Correctness (profile-patterns.md) — Fixed in PR #4

#### Bug 1: Wrong attribute index in `bt_gatt_notify`
- **What was wrong:** Pattern showed `bt_gatt_notify(conn, &bt__svc.attrs[1], ...)`
- **Why it's wrong:** `attrs[0]` = service declaration, `attrs[1]` = characteristic declaration, `attrs[2]` = characteristic value. Index 1 targets the declaration attribute — the BT stack silently discards notifications sent to declaration attributes.
- **Impact:** Any profile generated from this pattern would have non-functional notifications. The connection would succeed, subscriptions would appear to work, but no data would ever reach the client.
- **Fix:** Changed to `attrs[2]`, added comment: `/* attrs[0]=service decl, attrs[1]=char decl, attrs[2]=char value */`

#### Bug 2: Unsafe `memcpy` in write handler (pointer arithmetic on typed pointer)
- **What was wrong:** Pattern showed `memcpy(&value + offset, buf, len)` where `value` is a typed variable (e.g., `uint16_t`).
- **Why it's wrong:** `&value` is a `uint16_t *`. Adding `offset` (a byte count) advances the pointer by `offset × sizeof(uint16_t)` bytes — not `offset` bytes. On any non-`uint8_t` type this writes to a completely wrong address, bypassing all bounds checks. Stack corruption is possible.
- **Impact:** Write handlers for any multi-byte characteristic value would silently corrupt memory.
- **Fix:** `uint8_t *dst = (uint8_t *)&value; memcpy(dst + offset, buf, len);` — cast to byte pointer first, then add byte offset.

### P0 — Data Integrity (profiles-db.yaml) — Fixed in PR #4

#### Bug 3: DIS classified as `type: Simple`
- **Was:** `type: Simple`, `complexity: Low`
- **Should be:** `type: Complex`, `complexity: Medium`
- **Why:** DIS has 8 characteristics (Manufacturer Name, Model Number, Serial Number, Hardware Revision, Firmware Revision, Software Revision, System ID, PnP ID). Classification rule: ≥5 characteristics → Complex.
- **Impact:** Agent would generate Simple template (no state machine, single CCC) for an 8-characteristic service.

#### Bug 4: ANS classified as `type: Simple`
- **Was:** `type: Simple`, `complexity: Medium`
- **Should be:** `type: Complex`, `complexity: Medium`
- **Why:** ANS has 5 characteristics including Alert Notification Control Point. Classification rule: ≥5 characteristics AND has_control_point → Complex.
- **Impact:** Agent would generate Simple template for a service with a control point protocol.

#### Bug 5: IPS classified as `type: Simple`
- **Was:** `type: Simple`, `complexity: Medium`
- **Should be:** `type: Complex`, `complexity: High`
- **Why:** IPS (Indoor Positioning Service) has 9 characteristics. Classification rule: ≥5 characteristics → Complex; ≥5 characteristics with required connection state → High.
- **Impact:** Agent would generate Simple template for a 9-characteristic advertising-primary service.

### P1 — Governance (prompt.md) — Fixed in PR #4

#### Bug 6: Source priority order in Step 3 conflicted with sources-map.yaml
- **Was:** Step 3 listed priority as `Zephyr → BT Spec → Auto-PTS → Nordic → TI`
- **Should be:** `Zephyr → TI SimpleLink → Auto-PTS → BT Spec → Nordic` (matching sources-map.yaml)
- **Why:** Non-deterministic agent behavior when two sources gave conflicting guidance. The agent had no way to resolve the conflict because the two authoritative documents disagreed.
- **Fix:** Step 3 now mirrors `sources-map.yaml` exactly. `sources-map.yaml` is the single source of truth for priority.

### P2 — Formatting (prompt.md) — Fixed in PR #4

#### Bug 7: Escaped backticks in Output format section
- **Was:** `` \```c `` in the Output format section
- **Impact:** Agent would emit a literal backslash before code fences in its output.
- **Fix:** Outer fence changed to 4-backtick fence, inner code blocks use normal triple-backticks.

### Data bugs fixed in Batches 1–4

| Profile | Field | Before | After | Reason |
|---------|-------|--------|-------|--------|
| HRS | `complexity` | Low | Medium | 3 chars → Medium by rule (3–4 = Medium) |
| HRS | `has_control_point` | false | true | HR Control Point (0x2A39) present in spec |
| RSCS | `has_control_point` | false | true | SC Control Point (0x2A55) defined in RSCS spec |
| RSCS | `uses_indicate` | false | true | SC CP responses delivered via Indicate |
| CSCS | `has_control_point` | false | true | SC Control Point (0x2A55) identical to RSCS |
| CSCS | `uses_indicate` | false | true | SC CP responses delivered via Indicate |
| GLS | `pattern` | Indicate | Notify | Primary data (Glucose Measurement 0x2A18) is Notify; RACP Indicate is control only |
| BCS | `complexity` | Medium | Low | 2 chars, no per-connection state → Low by rule |
| WSS | `complexity` | Medium | Low | 2 chars, no per-connection state → Low by rule |
| PLXS | `has_control_point` | false | true | RACP (0x2A52) is defined in PLX Service spec |

---

## 6. Data Schema — Field-by-Field Meaning for the Agent

Each field in `profiles-db.yaml` drives a specific agent decision:

```yaml
- name: "Heart Rate Service"     # Human-readable; used in EXPLAIN output
  id: HRS                        # Primary lookup key for CLASSIFY step
  category: Health               # Used for similar-profile matching (same category preferred)
  type: Simple | Complex         # → chooses Simple or Complex code template
  complexity: Low | Medium | High # → determines depth of state machine, number of CCCs
  pattern: Notify | Read | Write | Indicate | Mixed | State Machine
    # → determines primary characteristic property in BUILD
    # → Notify: bt_gatt_notify() + CCC + ccc_cfg_changed
    # → Indicate: bt_gatt_indicate() + semaphore + bt_conn tracking
    # → State Machine: connection callbacks + per-conn struct
  uuids:
    service: "0x180D"            # Used verbatim in BT_UUID_DECLARE_16() in generated .h
    characteristics:
      - name: "..."              # Used in function names and comments
        uuid: "0x2A37"           # Used in BT_UUID_<PROFILE>_<CHAR>_VAL macro
        properties: [Notify]    # → GATT attribute permission flags in BT_GATT_CHARACTERISTIC()
        mandatory: true         # → whether to include in generated code unconditionally
  callbacks: true                # → whether to expose callback typedefs in .h
  state_management: false        # → same as per_connection_state_required (legacy field)
  has_control_point: true        # → generate control point WRITE handler + response Indicate
  uses_indicate: true            # → generate bt_gatt_indicate() flow + semaphore pattern
  per_connection_state_required: true  # → generate bt_conn_cb + per-conn struct
  kconfig_symbol: BT_HRS         # → used in Kconfig entry: config BT_HRS
  spec_version: "1.0"            # → informational; reference for UUID verification
  spec_doc: "docs/profiles/..."  # → local PDF path for UUID cross-check
  pts_tracked: true              # → informational; whether Auto-PTS has test cases for this profile
  reference_files:
    header: "include/..."        # → the closest existing Zephyr .h to study for BUILD
    impl: "subsys/..."           # → the closest existing Zephyr .c to study for BUILD
  similar_profiles: [BAS, DIS]   # → candidate reference profiles for CLASSIFY step
  tags: [health, sensor, notify] # → secondary similarity matching for unknown profiles
  notes: "..."                   # → documented edge cases, spec errata, cross-references
```

---

## 7. Current State (as of 2026-03-01)

### Completed

| Component | Status | Details |
|-----------|--------|---------|
| `profiles-db.yaml` | ✅ Phase 1 complete | All 24 profiles validated; all bugs fixed |
| `profile-patterns.md` | ✅ Phase 1 complete | §1–§10.7 documented |
| `sources-map.yaml` | ✅ Complete | All 5 sources documented with full governance rules |
| `zephyr-bt-profile-builder.instructions.md` | ✅ Complete | Classification rules, output rules, anti-patterns |
| `zephyr-bt-profile-builder.prompt.md` | ✅ Complete | 5-step flow, all input levels, source order fixed |

### Profile coverage (24 total, all validated)

| Batch | Profiles | PR |
|-------|----------|----|
| Baseline (PR #2) | HRS, BAS, DIS, HTS, ESS, OTS, CTS, LLS, TPS, IAS, SPS, RSCS, CSCS, GLS, ANS, PASS, UDS, BCS, WSS, CGMS, PLXS, IPS, **BPS** (added) | #2 |
| Review debt | DIS, ANS, IPS type/complexity fixes; pattern.md P0 bugs | #4 |
| Batch 1 deep | HRS, BAS, DIS, HTS, ESS, OTS | #5 |
| Batch 2 deep | CTS, LLS, TPS, IAS, SPS, RSCS | #6 |
| Batch 3 deep | CSCS, GLS, HIDS, ANS, PASS, UDS | #7 |
| Batch 4 deep | BCS, WSS, CGMS, PLXS, IPS, BPS | #8 |

### Patterns documented in `profile-patterns.md`

| Section | Pattern | Profiles |
|---------|---------|----------|
| §1 | Simple Profile (.h + .c + Kconfig) | All Simple profiles |
| §2 | Complex Profile (state machine, CCC) | All Complex profiles |
| §3–§9 | Characteristic types (Read, Write, WNR, Notify, Indicate, Mixed) | — |
| §10.1 | Server-Requests-Client-Refresh | SPS/SCPS |
| §10.2 | Indicate-Based Measurement Delivery | BPS, HTS, BCS, WSS |
| §10.3 | Conditional Feature Indication | WSS, BPS |
| §10.4 | Technical Tag Classification Rules | All profiles |
| §10.5 | ESS Extended Descriptor Pattern | ESS |
| §10.6 | RACP Pattern | GLS, CGMS, PLXS |
| §10.7 | SC Control Point Pattern | RSCS, CSCS |

---

## 8. What Phase 2 Should Look Like

Phase 1 ensured the data is **correct**. Phase 2 is about making the system **complete** and **usable end-to-end**.

### Suggested Phase 2 scope

#### 2.1 End-to-end generation test
Test the full 5-step agent flow for each of the 4 input levels:
- Known profile (e.g., ask for HRS) → agent should generate correct Zephyr `.h` + `.c` + `Kconfig`
- Functional description (e.g., "temperature sensor") → agent should map to ESS/HTS, generate accordingly
- Unknown-to-Zephyr profile (exists in Nordic/BT Spec only) → agent should research via sources-map priority order
- No data ("I need a BLE sensor") → agent should ask exactly one clarifying question

#### 2.2 Profile generation for BPS
BPS was added to the DB in PR #2 but is the only profile where no Zephyr implementation exists yet in `subsys/bluetooth/services/`. Generating a complete Zephyr-native BPS implementation would be a good validation test.

#### 2.3 Validation against Auto-PTS
For all `pts_tracked: true` profiles, validate that what the agent generates would pass PTS qualification. Run against the Auto-PTS workspace in `auto-pts/autopts/ptsprojects/zephyr/`.

#### 2.4 profiles-db.yaml schema v2.0 considerations
Fields potentially worth adding in Phase 2 (discovered during Phase 1 notes):
- `errata_refs` — references to known BT SIG errata affecting the profile
- `zephyr_impl_status` — whether a Zephyr implementation exists (`upstream`, `missing`, `partial`)
- `pts_coverage` — which PTS test cases exist for this profile
- `dual_role` — whether the profile has both server and client roles

#### 2.5 Missing profile coverage
The current DB covers the profiles found in `subsys/bluetooth/services/`. A scan of the Nordic SDK and BT SIG assigned numbers list would reveal which Bluetooth profiles are commonly needed but **not yet** in the DB. Those would need a separate "Phase 1" validation cycle before the agent can generate them.

---

## Appendix: PR Summary Table

| PR | Title | Status | Key changes |
|----|-------|--------|-------------|
| #2 | Framework baseline | Merged | All 5 files created; 24 profiles in DB; spot-check on 6 |
| #4 | Review debt cleanup | Merged | 2 P0 code bugs in patterns; 3 classification bugs in DB; 2 governance fixes |
| #5 | Phase 1 Batch 1 | Merged | Deep validation: HRS, BAS, DIS, HTS, ESS, OTS; §10.5 added |
| #6 | Phase 1 Batch 2 | Merged | Deep validation: CTS, LLS, TPS, IAS, SPS, RSCS |
| #7 | Phase 1 Batch 3 | Merged | Deep validation: CSCS, GLS, HIDS, ANS, PASS, UDS |
| #8 | Phase 1 Batch 4 | Merged | Deep validation: BCS, WSS, CGMS, PLXS, IPS, BPS; §10.6, §10.7 added; Phase 1 complete |

## Appendix: Issue Summary Table

| Issue | Title | Status | Resolved by |
|-------|-------|--------|-------------|
| #1 | Build Zephyr BLE GATT Profile Builder System | Closed | PR #2 |
| #3 | Phase 1 Completion: Comprehensive GATT Profile Data Extraction | Closed | PR #8 |
