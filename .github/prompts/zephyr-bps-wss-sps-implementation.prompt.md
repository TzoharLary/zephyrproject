---
agent: agent
description: "Implement Zephyr BLE GATT profiles BPS, WSS, and SPS/SCPS with source reconciliation, profile-specific references, persistent worklog, and transfer README."
---

# Zephyr BPS + WSS + SPS/SCPS Implementation Prompt

## Mission

Implement three BLE GATT profiles in Zephyr-native style:
- **BPS** — Blood Pressure Service
- **WSS** — Weight Scale Service
- **SPS/SCPS** — Scan Parameters Service (handle naming alias explicitly)

Assume `zephyr/` is the project root for all paths in this task.

---

## Phase 0 — Mandatory Source Reconciliation (before coding)

Read these files first:
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/instructions/zephyr-bt-profile-builder.instructions.md`
- `.github/prompts/zephyr-bt-profile-builder.prompt.md`
- `.github/data/profiles-db.yaml`
- `.github/data/profile-patterns.md`
- `.github/data/sources-map.yaml`
- `data/README.md`

Then inspect local profile knowledge:
- `data/raw/bluetooth_sig/profiles/BPS/**`
- `data/raw/bluetooth_sig/profiles/WSS/**`
- `data/raw/bluetooth_sig/profiles/SCPS/**`
- `data/curated/group_b/profiles/BPS/**`
- `data/curated/group_b/profiles/WSS/**`
- `data/curated/group_b/profiles/SCPS/**`
- `data/catalog/group_b/**`

Produce a short **Source Trust Matrix** in your working notes:
1. Authoritative for UUIDs/mandatory characteristics
2. Implementation guidance only
3. Inferred assumptions requiring validation

### Required reconciliation decision
If profile naming differs between sources (e.g., `SPS` vs `SCPS`), explicitly document alias mapping, UUID evidence, and final chosen naming in code/API.

---

## Phase 1 — Classify each profile independently

For **each** profile (BPS, WSS, SPS/SCPS), determine and document:
- type: `Simple` or `Complex`
- complexity level
- pattern (`Read`, `Write`, `Notify`, `Indicate`, `Mixed`, `State Machine`)
- mandatory vs optional characteristics
- CCC requirements
- whether control-point/per-connection state is required

Do **not** use one generic reference set for all three profiles.

---

## Phase 2 — Choose profile-specific references

Selection algorithm per profile:
1. Start with `.github/data/profiles-db.yaml`:
   - `similar_profiles`
   - `reference_files`
   - `pattern`, `type`, `complexity`, `tags`
2. Verify those reference files exist in this repository.
3. If missing, fallback to:
   - `.github/data/profile-patterns.md` (relevant sections, including §10.x overlays)
   - closest existing Zephyr service implementations in `zephyr/subsys/bluetooth/services/`
4. Use TI/Nordic only for behavior understanding, never direct code copy.

---

## Phase 3 — Use built-in subagents when available

If built-in planning/exploration subagents are available:
- Use planning subagent first to create concrete implementation steps.
- Use exploration subagent to gather file-level evidence quickly.
- Keep implementation in the main agent.

If subagents are not available, follow the same process manually and document evidence sources.

---

## Phase 4 — Implement Zephyr-native files

Implement/update required files for each profile:
- headers: `zephyr/include/zephyr/bluetooth/services/`
- sources: `zephyr/subsys/bluetooth/services/`
- Kconfig integration: `zephyr/subsys/bluetooth/services/Kconfig`
- CMake integration (if needed): `zephyr/subsys/bluetooth/services/CMakeLists.txt`

Follow Zephyr conventions:
- `BT_GATT_SERVICE_DEFINE`
- `bt_gatt_attr_read` / `bt_gatt_attr_write`
- `BT_GATT_CCC` for notify/indicate characteristics
- strict write bounds checks (`offset + len`)
- correct ATT error returns via `BT_GATT_ERR(...)`
- robust notify/indicate return handling
- Zephyr logging style (`LOG_MODULE_REGISTER`)
- no Nordic/TI-specific APIs or identifiers in final code

---

## Phase 5 — Persistent worklog (required)

Create and continuously update:
- `docs/plans/2026-04-14-bps-wss-sps-implementation-worklog.md`

Update it at each milestone:
- plan snapshot
- decisions and rationale
- files/sources consulted
- blockers and resolution
- delta since previous checkpoint

Do not rely only on in-memory context.

---

## Phase 6 — Transfer README for other engineers (required)

After implementation is complete, create:
- `zephyr/README-bps-wss-sps-transfer.md`

This README must include:
1. **Artifact matrix** with exact final paths for every generated/modified file per profile (BPS, WSS, SPS/SCPS)
2. Explicit export/import steps for moving implementation into another Zephyr workspace
3. Copy checklist: full-file copy vs manual merge locations
4. Alias section: explain `SPS` vs `SCPS` mapping and safe naming migration
5. Post-copy verification checklist (build/config/test sanity)

Use only paths relative to `zephyr/` root.

---

## Phase 7 — Validation and changelog

Before finishing:
- run relevant build/lint/test checks for touched files
- confirm no policy violations

Then update changelog according to repository policy in `AGENTS.md`:
- add/update entry under `CHANGELOG/infra/`
- update `CHANGELOG/INDEX.md`
- if no commit exists in this task, use:
  - `Commit: pending (no commit in this task)`

---

## Required final output

Provide:
1. list of files changed
2. per-profile design summary
3. assumptions/gaps needing manual verification
4. reconciliation summary (including SPS/SCPS alias decision)
5. validation results
6. transfer README path and summary
