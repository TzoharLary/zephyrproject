# Group 3: Coverage and Scope Audit

Files in group: **8** | Total size: **196.4 KB**

## מה יש בקבוצה

| File | Type | Size (bytes) |
|---|---|---:|
| `pts_offline_inventory/reports/archive_extraction_log.tsv` | TSV | 4,664 |
| `pts_offline_inventory/reports/ets_name_hits.txt` | TXT | 205 |
| `pts_offline_inventory/reports/outside_previous_scope.tsv` | TSV | 50,650 |
| `pts_offline_inventory/reports/outside_previous_scope_with_tcid_hits.tsv` | TSV | 75 |
| `pts_offline_inventory/reports/scan_coverage_inventory.tsv` | TSV | 139,421 |
| `pts_offline_inventory/reports/tcid_match_files_top.txt` | TXT | 5,944 |
| `pts_offline_inventory/reports/tcids_new_vs_extended.txt` | TXT | 0 |
| `pts_offline_inventory/reports/xml_signature_files.txt` | TXT | 126 |

## שדות קריטיים שנשמרים

### `pts_offline_inventory/reports/archive_extraction_log.tsv`
- Structure: `TSV`
- Data rows: **13**
- Columns: `archive_path, depth, status, output_dir, extracted_files, log_excerpt`
- Truth columns: `status`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `archive_path` | Technical field as produced by source report. | 13 | 13 |
| `depth` | Expansion depth used in archive traversal. | 13 | 2 |
| `status` | Execution status for tool step. | 13 | 1 |
| `output_dir` | Technical field as produced by source report. | 13 | 13 |
| `extracted_files` | Technical field as produced by source report. | 13 | 10 |
| `log_excerpt` | Technical field as produced by source report. | 13 | 1 |

- Sample rows:
```text
archive_path=/Users/tzoharlary/zephyrproject/pts_offline_inventory/extracted/python_automation/PTSTestAutomationGuide_updated.docx ; depth=0 ; status=ok ; output_dir=/Users/tzoharlary/zephyrproject/pts_offline_inventory/scan_workspace/expanded_archives/d1_10c62bae93ae ; extracted_files=43 ; log_excerpt=| 7-Zip [64] 17.05 : Copyright (c) 1999-2021 Igor Pavlov : 2017-08-28 | p7zip Version 17.05 (locale=utf8,Utf16=on,HugeFiles=on,64 bits,16 CPUs x64)
archive_path=/Users/tzoharlary/zephyrproject/pts_offline_inventory/extracted/python_automation/platforms/Wiced/wicedtools/ChipLoad.exe ; depth=0 ; status=ok ; output_dir=/Users/tzoharlary/zephyrproject/pts_offline_inventory/scan_workspace/expanded_archives/d1_c035256d5da9 ; extracted_files=6 ; log_excerpt=| 7-Zip [64] 17.05 : Copyright (c) 1999-2021 Igor Pavlov : 2017-08-28 | p7zip Version 17.05 (locale=utf8,Utf16=on,HugeFiles=on,64 bits,16 CPUs x64)
```

### `pts_offline_inventory/reports/ets_name_hits.txt`
- Structure: `TXT`
- Lines: **4** | Non-empty: **4**
- Detected shape: `bullet_path_list`
- Truth rule: each bullet line is a path/entity indicator.

- Sample lines:
```text
- extracted/python_automation/etsStateMachine.py.bak
- extracted/python_automation/etsStateMachine.py
- extracted/python_automation/etsAssetProvider.py
- extracted/python_automation/handlers/etsHandler.py
```

### `pts_offline_inventory/reports/outside_previous_scope.tsv`
- Structure: `TSV`
- Data rows: **307**
- Columns: `path, root, depth, previous_scope, extracted_from, archive_candidate, tcid_hits`
- Truth columns: `path`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `path` | Scanned file path. | 307 | 307 |
| `root` | Logical scan root (extracted/scan_workspace/etc). | 307 | 2 |
| `depth` | Expansion depth used in archive traversal. | 307 | 3 |
| `previous_scope` | Whether file was in previous scan scope. | 307 | 1 |
| `extracted_from` | Parent archive/file path if expanded. | 301 | 13 |
| `archive_candidate` | Flag for archive-like content. | 307 | 2 |
| `tcid_hits` | Number of TCID matches found in this file. | 307 | 1 |

- Sample rows:
```text
path=pts_offline_inventory/scan_workspace/expanded_archives/d1_10c62bae93ae/[Content_Types].xml ; root=extracted ; depth=1 ; previous_scope=no ; extracted_from=pts_offline_inventory/extracted/python_automation/PTSTestAutomationGuide_updated.docx ; archive_candidate=no ; tcid_hits=0
path=pts_offline_inventory/scan_workspace/expanded_archives/d1_10c62bae93ae/_rels/.rels ; root=extracted ; depth=1 ; previous_scope=no ; extracted_from=pts_offline_inventory/extracted/python_automation/PTSTestAutomationGuide_updated.docx ; archive_candidate=no ; tcid_hits=0
```

### `pts_offline_inventory/reports/outside_previous_scope_with_tcid_hits.tsv`
- Structure: `TSV`
- Data rows: **0**
- Columns: `path, root, depth, previous_scope, extracted_from, archive_candidate, tcid_hits`
- Truth columns: `path`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `path` | Scanned file path. | 0 | 0 |
| `root` | Logical scan root (extracted/scan_workspace/etc). | 0 | 0 |
| `depth` | Expansion depth used in archive traversal. | 0 | 0 |
| `previous_scope` | Whether file was in previous scan scope. | 0 | 0 |
| `extracted_from` | Parent archive/file path if expanded. | 0 | 0 |
| `archive_candidate` | Flag for archive-like content. | 0 | 0 |
| `tcid_hits` | Number of TCID matches found in this file. | 0 | 0 |

### `pts_offline_inventory/reports/scan_coverage_inventory.tsv`
- Structure: `TSV`
- Data rows: **956**
- Columns: `path, root, depth, previous_scope, extracted_from, archive_candidate, tcid_hits`
- Truth columns: `path`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `path` | Scanned file path. | 956 | 956 |
| `root` | Logical scan root (extracted/scan_workspace/etc). | 956 | 2 |
| `depth` | Expansion depth used in archive traversal. | 956 | 3 |
| `previous_scope` | Whether file was in previous scan scope. | 956 | 2 |
| `extracted_from` | Parent archive/file path if expanded. | 301 | 13 |
| `archive_candidate` | Flag for archive-like content. | 956 | 2 |
| `tcid_hits` | Number of TCID matches found in this file. | 956 | 44 |

- Sample rows:
```text
path=pts_offline_inventory/extracted/python_automation/.git/COMMIT_EDITMSG ; root=extracted ; depth=0 ; previous_scope=yes ; archive_candidate=no ; tcid_hits=0
path=pts_offline_inventory/extracted/python_automation/.git/HEAD ; root=extracted ; depth=0 ; previous_scope=yes ; archive_candidate=no ; tcid_hits=0
```

### `pts_offline_inventory/reports/tcid_match_files_top.txt`
- Structure: `TXT`
- Lines: **80** | Non-empty: **80**
- Detected shape: `counted_list`
- Truth rule: each line is count + key summary.

- Sample lines:
```text
211 extracted/python_automation/platforms/Cyble/Configs_temp/ids.json
164 extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_indication.json
152 extracted/python_automation/platforms/Cyble/Configs/sm.json
145 extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_notification.json
133 extracted/python_automation/platforms/Cyble/Configs/uds.json
```

### `pts_offline_inventory/reports/tcids_new_vs_extended.txt`
- Structure: `TXT`
- Lines: **0** | Non-empty: **0**
- Detected shape: `general_text`
- Truth rule: preserve line-level textual evidence.

### `pts_offline_inventory/reports/xml_signature_files.txt`
- Structure: `TXT`
- Lines: **4** | Non-empty: **4**
- Detected shape: `general_text`
- Truth rule: preserve line-level textual evidence.

- Sample lines:
```text
extracted/rawscan_2/1
extracted/rawscan_3/1
extracted/python_automation/utilities/ykushcmd/bin/hidapi.dll
extracted/setup/[0]
```


## תמצית תוכן מלאה-למשמעות

- `scan_coverage_inventory.tsv`: **956** rows (`yes`: 649, `no`: 307).
- Files with `tcid_hits > 0`: **140** | Total hits: **2,643**.
- `outside_previous_scope.tsv`: **307** rows.
- `outside_previous_scope_with_tcid_hits.tsv`: **0** rows.
- `archive_extraction_log.tsv`: status distribution {'ok': 13} | total extracted files **301**.
- `ets_name_hits.txt`: **4** entries.
- `xml_signature_files.txt`: **4** entries.

| Control file | Key metric | Value |
|---|---|---:|
| `scan_coverage_inventory.tsv` | rows | 956 |
| `scan_coverage_inventory.tsv` | files with hits | 140 |
| `outside_previous_scope.tsv` | rows | 307 |
| `outside_previous_scope_with_tcid_hits.tsv` | rows | 0 |
| `archive_extraction_log.tsv` | extracted files total | 301 |

## קבצים שדורשים עיון מלא

| File | Size (bytes) | Why full review matters | Recommended cross-check |
|---|---:|---|---|
| `pts_offline_inventory/reports/scan_coverage_inventory.tsv` | 139,421 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/outside_previous_scope.tsv` | 50,650 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/tcid_match_files_top.txt` | 5,944 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/archive_extraction_log.tsv` | 4,664 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/ets_name_hits.txt` | 205 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/xml_signature_files.txt` | 126 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/outside_previous_scope_with_tcid_hits.tsv` | 75 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/tcids_new_vs_extended.txt` | 0 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |

## עקיבות

| Claim | Source |
|---|---|
| Coverage totals and hit counts are computed from `scan_coverage_inventory.tsv`. | `pts_offline_inventory/reports/scan_coverage_inventory.tsv` |
| Out-of-scope inventory comes from `outside_previous_scope*.tsv`. | `pts_offline_inventory/reports/outside_previous_scope.tsv` |
| Archive extraction status comes from `archive_extraction_log.tsv`. | `pts_offline_inventory/reports/archive_extraction_log.tsv` |
