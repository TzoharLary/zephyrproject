# untracked_curated

This folder is a curated documentation layer for untracked (non-ignored) reports under `pts_offline_inventory/reports`.
It preserves critical meaning, provides grouping, and keeps traceability to source report files.

## Purpose

- Keep source report meaning intact without modifying tracked baseline report files.
- Provide one readable index for profile TCIDs, global datasets, coverage audit, and payload evidence.
- Ensure every source file is mapped to exactly one group.

## Difference vs `reports/`

- `reports/` contains raw and intermediate outputs from extraction and scans.
- `reports/untracked_curated/` adds structured interpretation, critical fields, and claim-to-source mapping.

## Group Index

| Group | File | Scope |
|---|---|---|
| G1 | `01_profile_prefix_tcids.md` | `tcids_by_prefix/` + prefix summaries |
| G2 | `02_global_tcid_datasets.md` | global TCID datasets (`all/unique/unmapped`) |
| G3 | `03_coverage_and_scope_audit.md` | scan coverage/scope gap/extraction audit |
| G4 | `04_payload_investigation_evidence.md` | Burn/MSI/CAB/ETS evidence |

## Coverage Manifest (Snapshot)

Snapshot time: `2026-02-18T14:10:10`
Source files in snapshot: **118**

| Source file | Group | Type | Size (bytes) |
|---|---|---|---:|
| `pts_offline_inventory/reports/archive_extraction_log.tsv` | `G3` | TSV | 4,664 |
| `pts_offline_inventory/reports/ets_name_hits.txt` | `G3` | TXT | 205 |
| `pts_offline_inventory/reports/outside_previous_scope.tsv` | `G3` | TSV | 50,650 |
| `pts_offline_inventory/reports/outside_previous_scope_with_tcid_hits.tsv` | `G3` | TSV | 75 |
| `pts_offline_inventory/reports/payload_investigation/burn_signature_hits.tsv` | `G4` | TSV | 1,823 |
| `pts_offline_inventory/reports/payload_investigation/cab_inventory_full.tsv` | `G4` | TSV | 14,616 |
| `pts_offline_inventory/reports/payload_investigation/cab_inventory_top30.tsv` | `G4` | TSV | 14,019 |
| `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv` | `G4` | TSV | 5,789 |
| `pts_offline_inventory/reports/payload_investigation/ets_xml_prefix_counts.tsv` | `G4` | TSV | 18 |
| `pts_offline_inventory/reports/payload_investigation/ets_xml_with_tcids.tsv` | `G4` | TSV | 39 |
| `pts_offline_inventory/reports/payload_investigation/firmware_summary.tsv` | `G4` | TSV | 428 |
| `pts_offline_inventory/reports/payload_investigation/investigation_summary.md` | `G4` | MD | 1,249 |
| `pts_offline_inventory/reports/payload_investigation/msi_cab_tool_status.tsv` | `G4` | TSV | 1,669 |
| `pts_offline_inventory/reports/payload_investigation/msi_feature_summary.tsv` | `G4` | TSV | 254 |
| `pts_offline_inventory/reports/payload_investigation/msi_file_install_map.tsv` | `G4` | TSV | 5,675 |
| `pts_offline_inventory/reports/payload_investigation/msi_keyword_hits.tsv` | `G4` | TSV | 45 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Component.tsv` | `G4` | TSV | 1,958 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Directory.tsv` | `G4` | TSV | 2,807 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Feature.tsv` | `G4` | TSV | 325 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/FeatureComponents.tsv` | `G4` | TSV | 563 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/File.tsv` | `G4` | TSV | 2,553 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Media.tsv` | `G4` | TSV | 82 |
| `pts_offline_inventory/reports/payload_investigation/payload_msi_cab_list.tsv` | `G4` | TSV | 317 |
| `pts_offline_inventory/reports/prefix_counts.txt` | `G1` | TXT | 392 |
| `pts_offline_inventory/reports/prefix_counts_unique_tcids.txt` | `G1` | TXT | 392 |
| `pts_offline_inventory/reports/scan_coverage_inventory.tsv` | `G3` | TSV | 139,421 |
| `pts_offline_inventory/reports/tcid_all_sources.tsv` | `G2` | TSV | 286,943 |
| `pts_offline_inventory/reports/tcid_match_files_top.txt` | `G3` | TXT | 5,944 |
| `pts_offline_inventory/reports/tcid_unique_with_sources.tsv` | `G2` | TSV | 239,577 |
| `pts_offline_inventory/reports/tcids_by_prefix/AIOS.txt` | `G1` | TXT | 2,967 |
| `pts_offline_inventory/reports/tcids_by_prefix/AIOS_sources.txt` | `G1` | TXT | 494 |
| `pts_offline_inventory/reports/tcids_by_prefix/ANP.txt` | `G1` | TXT | 402 |
| `pts_offline_inventory/reports/tcids_by_prefix/ANP_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/ANS.txt` | `G1` | TXT | 552 |
| `pts_offline_inventory/reports/tcids_by_prefix/ANS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/BAS.txt` | `G1` | TXT | 130 |
| `pts_offline_inventory/reports/tcids_by_prefix/BAS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/BCS.txt` | `G1` | TXT | 307 |
| `pts_offline_inventory/reports/tcids_by_prefix/BCS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/BLS.txt` | `G1` | TXT | 372 |
| `pts_offline_inventory/reports/tcids_by_prefix/BLS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/BMS.txt` | `G1` | TXT | 317 |
| `pts_offline_inventory/reports/tcids_by_prefix/BMS_sources.txt` | `G1` | TXT | 179 |
| `pts_offline_inventory/reports/tcids_by_prefix/CGMS.txt` | `G1` | TXT | 1,759 |
| `pts_offline_inventory/reports/tcids_by_prefix/CGMS_sources.txt` | `G1` | TXT | 298 |
| `pts_offline_inventory/reports/tcids_by_prefix/CPS.txt` | `G1` | TXT | 899 |
| `pts_offline_inventory/reports/tcids_by_prefix/CPS_sources.txt` | `G1` | TXT | 179 |
| `pts_offline_inventory/reports/tcids_by_prefix/CSCS.txt` | `G1` | TXT | 331 |
| `pts_offline_inventory/reports/tcids_by_prefix/CSCS_sources.txt` | `G1` | TXT | 84 |
| `pts_offline_inventory/reports/tcids_by_prefix/CTS.txt` | `G1` | TXT | 341 |
| `pts_offline_inventory/reports/tcids_by_prefix/CTS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/DIS.txt` | `G1` | TXT | 250 |
| `pts_offline_inventory/reports/tcids_by_prefix/DIS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/EPS.txt` | `G1` | TXT | 312 |
| `pts_offline_inventory/reports/tcids_by_prefix/EPS_sources.txt` | `G1` | TXT | 198 |
| `pts_offline_inventory/reports/tcids_by_prefix/ESS.txt` | `G1` | TXT | 757 |
| `pts_offline_inventory/reports/tcids_by_prefix/ESS_sources.txt` | `G1` | TXT | 178 |
| `pts_offline_inventory/reports/tcids_by_prefix/GAP.txt` | `G1` | TXT | 522 |
| `pts_offline_inventory/reports/tcids_by_prefix/GAP_sources.txt` | `G1` | TXT | 180 |
| `pts_offline_inventory/reports/tcids_by_prefix/GATT.txt` | `G1` | TXT | 2,820 |
| `pts_offline_inventory/reports/tcids_by_prefix/GATT_sources.txt` | `G1` | TXT | 659 |
| `pts_offline_inventory/reports/tcids_by_prefix/GLS.txt` | `G1` | TXT | 778 |
| `pts_offline_inventory/reports/tcids_by_prefix/GLS_sources.txt` | `G1` | TXT | 262 |
| `pts_offline_inventory/reports/tcids_by_prefix/HIDS.txt` | `G1` | TXT | 829 |
| `pts_offline_inventory/reports/tcids_by_prefix/HIDS_sources.txt` | `G1` | TXT | 183 |
| `pts_offline_inventory/reports/tcids_by_prefix/HPS.txt` | `G1` | TXT | 574 |
| `pts_offline_inventory/reports/tcids_by_prefix/HPS_sources.txt` | `G1` | TXT | 170 |
| `pts_offline_inventory/reports/tcids_by_prefix/HRP.txt` | `G1` | TXT | 370 |
| `pts_offline_inventory/reports/tcids_by_prefix/HRP_sources.txt` | `G1` | TXT | 183 |
| `pts_offline_inventory/reports/tcids_by_prefix/HRS.txt` | `G1` | TXT | 276 |
| `pts_offline_inventory/reports/tcids_by_prefix/HRS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/HTS.txt` | `G1` | TXT | 349 |
| `pts_offline_inventory/reports/tcids_by_prefix/HTS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/IAS.txt` | `G1` | TXT | 86 |
| `pts_offline_inventory/reports/tcids_by_prefix/IAS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/IDS.txt` | `G1` | TXT | 2,146 |
| `pts_offline_inventory/reports/tcids_by_prefix/IDS_sources.txt` | `G1` | TXT | 177 |
| `pts_offline_inventory/reports/tcids_by_prefix/IPS.txt` | `G1` | TXT | 1,135 |
| `pts_offline_inventory/reports/tcids_by_prefix/IPS_sources.txt` | `G1` | TXT | 385 |
| `pts_offline_inventory/reports/tcids_by_prefix/LLS.txt` | `G1` | TXT | 140 |
| `pts_offline_inventory/reports/tcids_by_prefix/LLS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/LNS.txt` | `G1` | TXT | 820 |
| `pts_offline_inventory/reports/tcids_by_prefix/LNS_sources.txt` | `G1` | TXT | 202 |
| `pts_offline_inventory/reports/tcids_by_prefix/MESH.txt` | `G1` | TXT | 7,309 |
| `pts_offline_inventory/reports/tcids_by_prefix/MESH_sources.txt` | `G1` | TXT | 3,571 |
| `pts_offline_inventory/reports/tcids_by_prefix/MMDL.txt` | `G1` | TXT | 7,777 |
| `pts_offline_inventory/reports/tcids_by_prefix/MMDL_sources.txt` | `G1` | TXT | 3,219 |
| `pts_offline_inventory/reports/tcids_by_prefix/NDCS.txt` | `G1` | TXT | 71 |
| `pts_offline_inventory/reports/tcids_by_prefix/NDCS_sources.txt` | `G1` | TXT | 84 |
| `pts_offline_inventory/reports/tcids_by_prefix/PASP.txt` | `G1` | TXT | 272 |
| `pts_offline_inventory/reports/tcids_by_prefix/PASP_sources.txt` | `G1` | TXT | 84 |
| `pts_offline_inventory/reports/tcids_by_prefix/PASS.txt` | `G1` | TXT | 393 |
| `pts_offline_inventory/reports/tcids_by_prefix/PASS_sources.txt` | `G1` | TXT | 174 |
| `pts_offline_inventory/reports/tcids_by_prefix/PLXS.txt` | `G1` | TXT | 741 |
| `pts_offline_inventory/reports/tcids_by_prefix/PLXS_sources.txt` | `G1` | TXT | 89 |
| `pts_offline_inventory/reports/tcids_by_prefix/PVNR.txt` | `G1` | TXT | 198 |
| `pts_offline_inventory/reports/tcids_by_prefix/PVNR_sources.txt` | `G1` | TXT | 90 |
| `pts_offline_inventory/reports/tcids_by_prefix/RSCS.txt` | `G1` | TXT | 393 |
| `pts_offline_inventory/reports/tcids_by_prefix/RSCS_sources.txt` | `G1` | TXT | 84 |
| `pts_offline_inventory/reports/tcids_by_prefix/RTUS.txt` | `G1` | TXT | 135 |
| `pts_offline_inventory/reports/tcids_by_prefix/RTUS_sources.txt` | `G1` | TXT | 84 |
| `pts_offline_inventory/reports/tcids_by_prefix/SCPS.txt` | `G1` | TXT | 136 |
| `pts_offline_inventory/reports/tcids_by_prefix/SCPS_sources.txt` | `G1` | TXT | 84 |
| `pts_offline_inventory/reports/tcids_by_prefix/SM.txt` | `G1` | TXT | 1,538 |
| `pts_offline_inventory/reports/tcids_by_prefix/SM_sources.txt` | `G1` | TXT | 262 |
| `pts_offline_inventory/reports/tcids_by_prefix/TIP.txt` | `G1` | TXT | 305 |
| `pts_offline_inventory/reports/tcids_by_prefix/TIP_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/TPS.txt` | `G1` | TXT | 43 |
| `pts_offline_inventory/reports/tcids_by_prefix/TPS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/UDS.txt` | `G1` | TXT | 2,410 |
| `pts_offline_inventory/reports/tcids_by_prefix/UDS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_by_prefix/WSS.txt` | `G1` | TXT | 231 |
| `pts_offline_inventory/reports/tcids_by_prefix/WSS_sources.txt` | `G1` | TXT | 83 |
| `pts_offline_inventory/reports/tcids_new_vs_extended.txt` | `G3` | TXT | 0 |
| `pts_offline_inventory/reports/tcids_unique_all.txt` | `G2` | TXT | 42,493 |
| `pts_offline_inventory/reports/tcids_unmapped.txt` | `G2` | TXT | 0 |
| `pts_offline_inventory/reports/tcids_unmapped_with_source.tsv` | `G2` | TSV | 16 |
| `pts_offline_inventory/reports/xml_signature_files.txt` | `G3` | TXT | 126 |

## Maintenance Rules

1. Every new untracked report file must appear in the manifest and in exactly one group.
2. Group priority order is fixed: payload_investigation -> tcids_by_prefix/prefix summaries -> coverage -> global.
3. Each group document must preserve these fixed section headers:
   - `## מה יש בקבוצה`
   - `## שדות קריטיים שנשמרים`
   - `## תמצית תוכן מלאה-למשמעות`
   - `## קבצים שדורשים עיון מלא`
   - `## עקיבות`
4. Every numeric claim must map to explicit source files.

## Critical vs Raw

- Critical: TCID/prefix identity, source paths, coverage counters, hit counts, extraction status, and payload signatures.
- Raw: full binary payload and verbose raw logs; kept in source files and summarized here at semantic level.