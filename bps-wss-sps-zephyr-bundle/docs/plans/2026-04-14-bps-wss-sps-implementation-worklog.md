# 2026-04-14 — BPS + WSS + SPS/SCPS Implementation Worklog

- Date: 2026-04-14
- Workspace: `/Users/tzoharlary/zephyrproject`
- Scope root for implementation paths: `zephyr/`
- Status: in-progress

## Milestone 0 — Intake + Plan Snapshot

### Goal
Implement Zephyr-native BLE GATT services for:
- BPS (Blood Pressure Service)
- WSS (Weight Scale Service)
- SPS/SCPS (Scan Parameters Service, alias handled explicitly)

### Initial execution plan
1. Reconcile sources and naming (SPS vs SCPS)
2. Classify each profile independently
3. Select profile-specific references/fallbacks
4. Implement headers and service `.c` files
5. Integrate service Kconfig + CMake
6. Validate via targeted builds
7. Write transfer README and changelog updates

## Source Trust Matrix (Phase 0)

### 1) Authoritative for UUIDs / mandatory characteristics
- `data/raw/bluetooth_sig/profiles/BPS/*` (official spec bundle)
- `data/raw/bluetooth_sig/profiles/WSS/*` (official spec bundle)
- `data/raw/bluetooth_sig/profiles/SCPS/*` (official spec bundle)
- `zephyr/include/zephyr/bluetooth/uuid.h` (authoritative in-tree UUID macro source for implementation)
- `.github/data/profiles-db.yaml` (project canonical metadata registry for expected service topology)

### 2) Implementation guidance only (not normative spec authority)
- `.github/data/profile-patterns.md` (pattern overlays and recommended implementation templates)
- `data/curated/group_b/profiles/{BPS,WSS,SCPS}/{logic,structure,implementation}.md`
- Existing Zephyr services in `zephyr/subsys/bluetooth/services/` (`bas.c`, `hrs.c`, `ias/ias.c`, `tps.c`, `ots/`)
- `data/catalog/group_b/*` registries/manifests for provenance and mapping

### 3) Inferred assumptions requiring validation during implementation
- Which optional characteristics are enabled in this first implementation cut
- Security/permission level defaults for writable characteristics (unless explicit policy requires stronger perms)
- Whether to expose SCPS alias as wrappers/macros only vs a separate header shim

## Required reconciliation decision — SPS vs SCPS naming

### Evidence
- `data/raw/bluetooth_sig/profiles/SCPS/Scan_Parameters_Service_1.0.pdf` uses **Scan Parameters Service** naming (SCPS context folder)
- `.github/data/profiles-db.yaml` profile entry uses `id: SPS` with service UUID `0x1813`
- `zephyr/include/zephyr/bluetooth/uuid.h` defines `BT_UUID_SPS_VAL 0x1813`

### Decision
- **Canonical implementation naming in code/API:** `sps` (`bt_sps_*`, `CONFIG_BT_SPS`, `sps.c`, `sps.h`)
- **Compatibility alias:** provide explicit SCPS alias mapping via `scps.h` shim (macro/type/function aliases to `sps` names)
- **Reason:** aligns with existing Zephyr UUID macro naming while preserving explicit user-facing SCPS terminology compatibility

## Sources consulted in Milestone 0

- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.github/instructions/zephyr-bt-profile-builder.instructions.md`
- `.github/prompts/zephyr-bt-profile-builder.prompt.md`
- `.github/data/profiles-db.yaml`
- `.github/data/profile-patterns.md`
- `.github/data/sources-map.yaml`
- `data/README.md`
- `data/raw/bluetooth_sig/profiles/{BPS,WSS,SCPS}/...`
- `data/curated/group_b/profiles/{BPS,WSS,SCPS}/...`
- `data/catalog/group_b/{methods,registries,sources,sync}/...`

## Open items before coding
- Finalize profile-by-profile classification table in this worklog
- Confirm fallback references where `profiles-db.yaml` reference files are missing in current tree

## Milestone 1 — Per-profile classification + reference resolution

### Classification table

| Profile | Type | Complexity | Pattern | Mandatory chars (this implementation baseline) | Optional chars | CCC requirements | Control-point / per-connection state |
|---|---|---|---|---|---|---|---|
| BPS | Simple | Medium | Indicate | Blood Pressure Measurement (`0x2A35`), Blood Pressure Feature (`0x2A49`) | Intermediate Cuff Pressure (`0x2A36`) | CCC required for Measurement Indicate; CCC required for Intermediate Cuff if enabled | No control point in baseline; no per-connection state required |
| WSS | Simple | Low | Indicate | Weight Measurement (`0x2A9D`), Weight Scale Feature (`0x2A9E`) | (none in baseline) | CCC required for Weight Measurement Indicate | No control point; no per-connection state required |
| SPS/SCPS | Simple | Low | Write | Scan Interval Window (`0x2A4F`) | Scan Refresh (`0x2A31`) | CCC required only for optional Scan Refresh Notify | No control point; no per-connection state required |

### Profile-specific reference selection algorithm outcome

#### BPS
- `profiles-db.yaml` similar profiles: `HTS`, `BCS`, `WSS`
- `profiles-db.yaml` reference files: `include/zephyr/bluetooth/services/bps.h`, `subsys/bluetooth/services/bps.c`
- Existence check in current tree: **missing** (target files not yet implemented)
- Similar profile files in current tree:
	- `hts.*`: missing
	- `bcs.*`: missing
	- `wss.*`: missing
- Fallbacks selected:
	- `.github/data/profile-patterns.md` §10.2 (Indicate-based measurement)
	- `zephyr/subsys/bluetooth/services/hrs.c` (callbacks + CCC structure + registration style)
	- `zephyr/subsys/bluetooth/services/bas.c` (read characteristic and notification error handling style)

#### WSS
- `profiles-db.yaml` similar profiles: `BCS`, `HTS`
- `profiles-db.yaml` reference files: `include/zephyr/bluetooth/services/wss.h`, `subsys/bluetooth/services/wss.c`
- Existence check in current tree: **missing** (target files not yet implemented)
- Similar profile files in current tree:
	- `bcs.*`: missing
	- `hts.*`: missing
- Fallbacks selected:
	- `.github/data/profile-patterns.md` §10.2 (Indicate-based measurement)
	- `zephyr/subsys/bluetooth/services/hrs.c` (subscription callback registration style)
	- `zephyr/subsys/bluetooth/services/bas.c` + `tps.c` (read characteristic style and attribute read handlers)

#### SPS/SCPS
- `profiles-db.yaml` profile id: `SPS` (UUID `0x1813`), similar profiles: `IAS`, `LLS`
- `profiles-db.yaml` reference files: `include/zephyr/bluetooth/services/sps.h`, `subsys/bluetooth/services/sps.c`
- Existence check in current tree: **missing** (target files not yet implemented)
- Similar profile files in current tree:
	- `ias.*`: exists
	- `lls.*`: missing
- Fallbacks selected:
	- `.github/data/profile-patterns.md` §10.1 (server-requests-client-refresh pattern)
	- `zephyr/subsys/bluetooth/services/ias/ias.c` (write-without-response handler patterns and validation)
	- `zephyr/subsys/bluetooth/services/hrs.c` / `bas.c` (CCC notify handling)

### Delta from Milestone 0
- Closed both open items from Milestone 0:
	- per-profile classification is now explicit
	- missing reference file fallback path is now resolved per profile

## Milestone 2 — Zephyr-native implementation

### Files created

#### BPS
- `zephyr/include/zephyr/bluetooth/services/bps.h`
- `zephyr/subsys/bluetooth/services/bps.c`
- `zephyr/subsys/bluetooth/services/Kconfig.bps`

#### WSS
- `zephyr/include/zephyr/bluetooth/services/wss.h`
- `zephyr/subsys/bluetooth/services/wss.c`
- `zephyr/subsys/bluetooth/services/Kconfig.wss`

#### SPS/SCPS
- `zephyr/include/zephyr/bluetooth/services/sps.h`
- `zephyr/include/zephyr/bluetooth/services/scps.h` (alias shim)
- `zephyr/subsys/bluetooth/services/sps.c`
- `zephyr/subsys/bluetooth/services/Kconfig.sps`

#### Shared integration files modified
- `zephyr/subsys/bluetooth/services/Kconfig`
- `zephyr/subsys/bluetooth/services/CMakeLists.txt`
- `zephyr/subsys/bluetooth/Kconfig.logging`

### Key implementation decisions
- BPS/WSS implemented as indicate-based measurement services with callback registration and CCC change fan-out.
- SPS implemented with strict write validation for Scan Interval Window and optional Scan Refresh notification.
- SCPS support provided as a compatibility alias header only (single backend in `sps.c`).
- Logging integration added through Bluetooth logging Kconfig module entries to keep `CONFIG_BT_<service>_LOG_LEVEL` symbols valid.

### Source references used during implementation
- `zephyr/include/zephyr/bluetooth/gatt.h` (macro/attribute semantics)
- `zephyr/include/zephyr/bluetooth/uuid.h` (UUID macro authority)
- `zephyr/subsys/bluetooth/services/{hrs.c,bas.c,ias/ias.c,tps.c}` (style and callback patterns)
- `.github/data/profile-patterns.md` (§10.1, §10.2)

### Delta from Milestone 1
- Classification output moved into concrete code artifacts.
- Alias strategy (`SPS` canonical + `SCPS` compatibility) now enforced in API surface.

## Milestone 3 — Validation and blockers

### Local diagnostics
- `get_errors` reported no editor-detected errors in all touched new/updated files.

### Build environment handling
- Build requirement acknowledged: run only from virtual environment.
- Project-local `.venv` was recreated (Python 3.13) and activated before all subsequent builds.
- Build commands executed using active venv interpreter (`python -m west ...`).

### Build attempts (from active `.venv`)
- `qemu_x86` with `CONFIG_BT_BPS=y` → failed due external module compile issue.
- `qemu_x86` with `CONFIG_BT_WSS=y` → failed due external module compile issue.
- `qemu_x86` with `CONFIG_BT_SPS=y` → failed due external module compile issue.
- combined `CONFIG_BT_BPS=y CONFIG_BT_WSS=y CONFIG_BT_SPS=y` → failed due external module compile issue.

### Confirmed compilation reach
- In combined build log, objects for new services were compiled:
	- `subsys/bluetooth/services/bps.c.obj`
	- `subsys/bluetooth/services/wss.c.obj`
	- `subsys/bluetooth/services/sps.c.obj`

### Blocking issue (outside current change scope)
- Fatal missing header from TI HAL module tree:
	- `ti/ble/stack_util/lib_opt/opt_dependencies.h`
- This is external/environmental to the newly added services and prevented full link-complete validation.

### Delta from Milestone 2
- Validation progressed from static checks to actual compilation of new service units.
- Full build remains blocked by pre-existing TI module dependency issue.

## Milestone 4 — Transfer package and changelog completion

### Transfer README
- Created: `zephyr/README-bps-wss-sps-transfer.md`
- Included:
	- full artifact matrix per profile
	- export/import workflow
	- full-file copy vs manual merge checklist
	- explicit SPS↔SCPS alias section and safe migration rules
	- post-copy verification checklist

### Changelog updates
- Added primary entry:
	- `CHANGELOG/firmware/2026-04-14-add-bps-wss-sps-services.md`
- Updated index:
	- `CHANGELOG/INDEX.md`

### Delta from Milestone 3
- Handoff/readability deliverables are complete.
- Repository-level change tracking is now synchronized with implementation artifacts.
