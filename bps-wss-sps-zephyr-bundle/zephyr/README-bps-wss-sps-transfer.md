# BPS + WSS + SPS/SCPS Transfer README

## Scope
This document explains how to transfer the implemented BLE GATT services:
- BPS (Blood Pressure Service)
- WSS (Weight Scale Service)
- SPS (Scan Parameters Service)
- SCPS compatibility alias (name-mapping layer to SPS)

All paths below are relative to `zephyr/` root.

## Artifact matrix

| Profile | Type | Paths |
|---|---|---|
| BPS | New public API header | `include/zephyr/bluetooth/services/bps.h` |
| BPS | New service implementation | `subsys/bluetooth/services/bps.c` |
| BPS | New service Kconfig | `subsys/bluetooth/services/Kconfig.bps` |
| WSS | New public API header | `include/zephyr/bluetooth/services/wss.h` |
| WSS | New service implementation | `subsys/bluetooth/services/wss.c` |
| WSS | New service Kconfig | `subsys/bluetooth/services/Kconfig.wss` |
| SPS | New public API header | `include/zephyr/bluetooth/services/sps.h` |
| SPS | New service implementation | `subsys/bluetooth/services/sps.c` |
| SPS | New service Kconfig | `subsys/bluetooth/services/Kconfig.sps` |
| SPS/SCPS | Compatibility alias header | `include/zephyr/bluetooth/services/scps.h` |
| Shared integration | Services menu include list updated | `subsys/bluetooth/services/Kconfig` |
| Shared integration | Service source registration updated | `subsys/bluetooth/services/CMakeLists.txt` |
| Shared integration | Logging module symbols added | `subsys/bluetooth/Kconfig.logging` |

## Export/import steps (between Zephyr workspaces)

1. Export the files listed in the artifact matrix from source workspace `zephyr/`.
2. Import each file into the destination workspace at the exact same relative path.
3. For files marked as "Shared integration", merge carefully (do not overwrite the entire file unless destination is identical branch/state).
4. Re-run Kconfig and CMake generation in destination workspace.
5. Build with service-specific options enabled to validate integration.

## Copy checklist (full-file copy vs manual merge)

### Full-file copy (recommended)
- `include/zephyr/bluetooth/services/bps.h`
- `include/zephyr/bluetooth/services/wss.h`
- `include/zephyr/bluetooth/services/sps.h`
- `include/zephyr/bluetooth/services/scps.h`
- `subsys/bluetooth/services/bps.c`
- `subsys/bluetooth/services/wss.c`
- `subsys/bluetooth/services/sps.c`
- `subsys/bluetooth/services/Kconfig.bps`
- `subsys/bluetooth/services/Kconfig.wss`
- `subsys/bluetooth/services/Kconfig.sps`

### Manual merge (required)
- `subsys/bluetooth/services/Kconfig`
  - add `rsource "Kconfig.bps"`
  - add `rsource "Kconfig.sps"`
  - add `rsource "Kconfig.wss"`
- `subsys/bluetooth/services/CMakeLists.txt`
  - add `zephyr_sources_ifdef(CONFIG_BT_BPS bps.c)`
  - add `zephyr_sources_ifdef(CONFIG_BT_SPS sps.c)`
  - add `zephyr_sources_ifdef(CONFIG_BT_WSS wss.c)`
- `subsys/bluetooth/Kconfig.logging`
  - add logging module entries for `BT_BPS`, `BT_SPS`, `BT_WSS`

## SPS vs SCPS alias mapping and safe migration

### Mapping decision
- Canonical implementation name: **SPS**
- Compatibility alias name: **SCPS**

### UUID evidence
- Service UUID used by implementation: `0x1813`
- Zephyr UUID macro source: `BT_UUID_SPS_VAL`
- Bluetooth SIG docs often name this service “ScPS” (Scan Parameters Service)

### Safe naming migration rules
- New code should prefer `bt_sps_*` APIs and `CONFIG_BT_SPS`.
- Existing SCPS-facing code can include `include/zephyr/bluetooth/services/scps.h` and keep using alias names.
- Do not duplicate service backends (`sps.c` is the only backend).

## Post-copy verification checklist

- [ ] Headers resolve: `bps.h`, `wss.h`, `sps.h`, `scps.h`.
- [ ] Kconfig symbols visible: `BT_BPS`, `BT_WSS`, `BT_SPS`.
- [ ] CMake includes new service sources.
- [ ] Logging symbols available: `CONFIG_BT_BPS_LOG_LEVEL`, `CONFIG_BT_WSS_LOG_LEVEL`, `CONFIG_BT_SPS_LOG_LEVEL`.
- [ ] Build with each service option enabled separately.
- [ ] Build with all three services enabled together.
- [ ] Confirm runtime failures (if any) are not from missing service symbols but from platform/module environment.
