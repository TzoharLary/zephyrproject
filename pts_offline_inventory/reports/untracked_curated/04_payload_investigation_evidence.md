# Group 4: Payload Investigation Evidence

Files in group: **19** | Total size: **53.0 KB**

## מה יש בקבוצה

| File | Type | Size (bytes) |
|---|---|---:|
| `pts_offline_inventory/reports/payload_investigation/burn_signature_hits.tsv` | TSV | 1,823 |
| `pts_offline_inventory/reports/payload_investigation/cab_inventory_full.tsv` | TSV | 14,616 |
| `pts_offline_inventory/reports/payload_investigation/cab_inventory_top30.tsv` | TSV | 14,019 |
| `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv` | TSV | 5,789 |
| `pts_offline_inventory/reports/payload_investigation/ets_xml_prefix_counts.tsv` | TSV | 18 |
| `pts_offline_inventory/reports/payload_investigation/ets_xml_with_tcids.tsv` | TSV | 39 |
| `pts_offline_inventory/reports/payload_investigation/firmware_summary.tsv` | TSV | 428 |
| `pts_offline_inventory/reports/payload_investigation/investigation_summary.md` | MD | 1,249 |
| `pts_offline_inventory/reports/payload_investigation/msi_cab_tool_status.tsv` | TSV | 1,669 |
| `pts_offline_inventory/reports/payload_investigation/msi_feature_summary.tsv` | TSV | 254 |
| `pts_offline_inventory/reports/payload_investigation/msi_file_install_map.tsv` | TSV | 5,675 |
| `pts_offline_inventory/reports/payload_investigation/msi_keyword_hits.tsv` | TSV | 45 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Component.tsv` | TSV | 1,958 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Directory.tsv` | TSV | 2,807 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Feature.tsv` | TSV | 325 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/FeatureComponents.tsv` | TSV | 563 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/File.tsv` | TSV | 2,553 |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Media.tsv` | TSV | 82 |
| `pts_offline_inventory/reports/payload_investigation/payload_msi_cab_list.tsv` | TSV | 317 |

## שדות קריטיים שנשמרים

### `pts_offline_inventory/reports/payload_investigation/burn_signature_hits.tsv`
- Structure: `TSV`
- Data rows: **26**
- Columns: `file, token, offset`
- Truth columns: `file, token`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `file` | Extracted file name/path inside payload. | 26 | 3 |
| `token` | Signature token found during scan. | 26 | 3 |
| `offset` | Byte offset of token hit. | 26 | 26 |

- Sample rows:
```text
file=/Users/tzoharlary/PTS files/pts_setup_8_11_1.exe ; token=.wixburn ; offset=252768949
file=/Users/tzoharlary/PTS files/pts_setup_8_11_1.exe ; token=.wixburn ; offset=253014055
```

### `pts_offline_inventory/reports/payload_investigation/cab_inventory_full.tsv`
- Structure: `TSV`
- Data rows: **56**
- Columns: `cab_path, extract_dest, file, size_bytes, file_type`
- Truth columns: `file`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `cab_path` | Technical field as produced by source report. | 56 | 4 |
| `extract_dest` | Technical field as produced by source report. | 56 | 4 |
| `file` | Extracted file name/path inside payload. | 56 | 45 |
| `size_bytes` | File size in bytes. | 56 | 52 |
| `file_type` | File type by signature/magic detection. | 56 | 26 |

- Sample rows:
```text
cab_path=pts_offline_inventory/extracted/rawscan_2/2.cab ; extract_dest=pts_offline_inventory/reports/payload_investigation/extract_cab/80663c404052 ; file=u0 ; size_bytes=129536 ; file_type=PE32 executable (DLL) (GUI) Intel 80386, for MS Windows
cab_path=pts_offline_inventory/extracted/rawscan_2/2.cab ; extract_dest=pts_offline_inventory/reports/payload_investigation/extract_cab/80663c404052 ; file=u4 ; size_bytes=48163 ; file_type=Rich Text Format data, version 1, ANSI, code page 1252, default middle east language ID 1025
```

### `pts_offline_inventory/reports/payload_investigation/cab_inventory_top30.tsv`
- Structure: `TSV`
- Data rows: **53**
- Columns: `cab_path, extract_dest, file, size_bytes, file_type`
- Truth columns: `file`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `cab_path` | Technical field as produced by source report. | 53 | 4 |
| `extract_dest` | Technical field as produced by source report. | 53 | 4 |
| `file` | Extracted file name/path inside payload. | 53 | 44 |
| `size_bytes` | File size in bytes. | 53 | 51 |
| `file_type` | File type by signature/magic detection. | 53 | 26 |

- Sample rows:
```text
cab_path=pts_offline_inventory/extracted/rawscan_2/2.cab ; extract_dest=pts_offline_inventory/reports/payload_investigation/extract_cab/80663c404052 ; file=u0 ; size_bytes=129536 ; file_type=PE32 executable (DLL) (GUI) Intel 80386, for MS Windows
cab_path=pts_offline_inventory/extracted/rawscan_2/2.cab ; extract_dest=pts_offline_inventory/reports/payload_investigation/extract_cab/80663c404052 ; file=u4 ; size_bytes=48163 ; file_type=Rich Text Format data, version 1, ANSI, code page 1252, default middle east language ID 1025
```

### `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv`
- Structure: `TSV`
- Data rows: **57**
- Columns: `file, size_bytes, tcid_count`
- Truth columns: `file`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `file` | Extracted file name/path inside payload. | 57 | 57 |
| `size_bytes` | File size in bytes. | 57 | 57 |
| `tcid_count` | Technical field as produced by source report. | 57 | 1 |

- Sample rows:
```text
file=pts_offline_inventory/scan_workspace/expanded_archives/d1_10c62bae93ae/[Content_Types].xml ; size_bytes=3513 ; tcid_count=0
file=pts_offline_inventory/scan_workspace/expanded_archives/d1_10c62bae93ae/customXml/item1.xml ; size_bytes=192 ; tcid_count=0
```

### `pts_offline_inventory/reports/payload_investigation/ets_xml_prefix_counts.tsv`
- Structure: `TSV`
- Data rows: **0**
- Columns: `prefix, file_count`
- Truth columns: `prefix`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `prefix` | Profile/service prefix derived from TCID. | 0 | 0 |
| `file_count` | Technical field as produced by source report. | 0 | 0 |

### `pts_offline_inventory/reports/payload_investigation/ets_xml_with_tcids.tsv`
- Structure: `TSV`
- Data rows: **0**
- Columns: `file, tcid_count, prefixes, sample_tcids`
- Truth columns: `file`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `file` | Extracted file name/path inside payload. | 0 | 0 |
| `tcid_count` | Technical field as produced by source report. | 0 | 0 |
| `prefixes` | Technical field as produced by source report. | 0 | 0 |
| `sample_tcids` | Technical field as produced by source report. | 0 | 0 |

### `pts_offline_inventory/reports/payload_investigation/firmware_summary.tsv`
- Structure: `TSV`
- Data rows: **1**
- Columns: `main_extract_status, main_extract_mode, rawscan_dir, expanded_dir, expanded_archives_ok, xml_ets_files, tcid_unique_count, tcid_raw_file`
- Truth columns: `main_extract_status`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `main_extract_status` | Technical field as produced by source report. | 1 | 1 |
| `main_extract_mode` | Technical field as produced by source report. | 1 | 1 |
| `rawscan_dir` | Technical field as produced by source report. | 1 | 1 |
| `expanded_dir` | Technical field as produced by source report. | 1 | 1 |
| `expanded_archives_ok` | Technical field as produced by source report. | 1 | 1 |
| `xml_ets_files` | Technical field as produced by source report. | 1 | 1 |
| `tcid_unique_count` | Technical field as produced by source report. | 1 | 1 |
| `tcid_raw_file` | Technical field as produced by source report. | 1 | 1 |

- Sample rows:
```text
main_extract_status=ok ; main_extract_mode=regular ; rawscan_dir=/Users/tzoharlary/zephyrproject/pts_offline_inventory/reports/payload_investigation/firmware_scan/rawscan ; expanded_dir=/Users/tzoharlary/zephyrproject/pts_offline_inventory/reports/payload_investigation/firmware_scan/expanded ; expanded_archives_ok=0 ; xml_ets_files=0 ; tcid_unique_count=0 ; tcid_raw_file=payload_investigation/firmware_scan/firmware_tcid_matches_raw.txt
```

### `pts_offline_inventory/reports/payload_investigation/investigation_summary.md`
- Structure: `MD`
- Lines: **28** | Non-empty: **24**
- Detected shape: `bullet_path_list`
- Truth rule: each bullet line is a path/entity indicator.

- Sample lines:
```text
# PTS Payload Investigation
## Burn Signature Check
- setup exe checked: `/Users/tzoharlary/PTS files/pts_setup_8_11_1.exe`
- files checked for burn tokens: **6**
- files with burn token hits: **3**
```

### `pts_offline_inventory/reports/payload_investigation/msi_cab_tool_status.tsv`
- Structure: `TSV`
- Data rows: **5**
- Columns: `type, path, size_bytes, list_status, extract_status, list_log, extract_log, extract_dest, extracted_files`
- Truth columns: `type, path`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `type` | Artifact type (msi/cab/etc). | 5 | 2 |
| `path` | Scanned file path. | 5 | 5 |
| `size_bytes` | File size in bytes. | 5 | 5 |
| `list_status` | Technical field as produced by source report. | 5 | 1 |
| `extract_status` | Technical field as produced by source report. | 5 | 1 |
| `list_log` | Technical field as produced by source report. | 5 | 5 |
| `extract_log` | Technical field as produced by source report. | 5 | 5 |
| `extract_dest` | Technical field as produced by source report. | 5 | 5 |
| `extracted_files` | Technical field as produced by source report. | 5 | 5 |

- Sample rows:
```text
type=cab ; path=pts_offline_inventory/extracted/rawscan_2/2.cab ; size_bytes=83826 ; list_status=ok ; extract_status=ok ; list_log=pts_offline_inventory/reports/payload_investigation/logs/cab_list_80663c404052.log ; extract_log=pts_offline_inventory/reports/payload_investigation/logs/cab_extract_80663c404052.log ; extract_dest=pts_offline_inventory/reports/payload_investigation/extract_cab/80663c404052 ; extracted_files=7
type=cab ; path=pts_offline_inventory/extracted/rawscan_2/4.cab ; size_bytes=6082804 ; list_status=ok ; extract_status=ok ; list_log=pts_offline_inventory/reports/payload_investigation/logs/cab_list_a20f1e1da40a.log ; extract_log=pts_offline_inventory/reports/payload_investigation/logs/cab_extract_a20f1e1da40a.log ; extract_dest=pts_offline_inventory/reports/payload_investigation/extract_cab/a20f1e1da40a ; extracted_files=4
```

### `pts_offline_inventory/reports/payload_investigation/msi_feature_summary.tsv`
- Structure: `TSV`
- Data rows: **3**
- Columns: `Feature, Title, Description, Components`
- Truth columns: `Feature`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `Feature` | MSI feature identifier. | 3 | 3 |
| `Title` | Technical field as produced by source report. | 3 | 3 |
| `Description` | Technical field as produced by source report. | 3 | 3 |
| `Components` | Technical field as produced by source report. | 3 | 2 |

- Sample rows:
```text
Feature=MSXML ; Title=Microsoft XML Parser ; Description=Microsoft XML Parser ; Components=2
Feature=MSXMLSYS ; Title=MSXML (global installation) ; Description=Microsoft XML Parser (global installation) ; Components=2
```

### `pts_offline_inventory/reports/payload_investigation/msi_file_install_map.tsv`
- Structure: `TSV`
- Data rows: **15**
- Columns: `File, Component, DirectoryId, InstallDir, FileName, InstallPath, FileSize, Version, Language, Sequence`
- Truth columns: `File, InstallPath`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `File` | MSI file identifier/name. | 15 | 15 |
| `Component` | MSI component identifier. | 15 | 9 |
| `DirectoryId` | Technical field as produced by source report. | 15 | 8 |
| `InstallDir` | Technical field as produced by source report. | 15 | 7 |
| `FileName` | Technical field as produced by source report. | 15 | 7 |
| `InstallPath` | Resolved install path from MSI tables. | 15 | 15 |
| `FileSize` | Technical field as produced by source report. | 15 | 7 |
| `Version` | Technical field as produced by source report. | 6 | 1 |
| `Language` | Technical field as produced by source report. | 6 | 2 |
| `Sequence` | Technical field as produced by source report. | 15 | 15 |

- Sample rows:
```text
File=msxml4.dll.246EB7AD_459A_4FA8_83D1_41A46D7634B7 ; Component=MSXML4_System.246EB7AD_459A_4FA8_83D1_41A46D7634B7 ; DirectoryId=SystemFolder.246EB7AD_459A_4FA8_83D1_41A46D7634B7 ; InstallDir=TARGETDIR/System ; FileName=msxml4.dll ; InstallPath=TARGETDIR/System/msxml4.dll ; FileSize=1328968 ; Version=4.30.2100.0 ; Language=0 ; Sequence=2
File=ul_msxml4.dll.74974F83_779E_3983_FF6B_D6B9ABF34537 ; Component=uplevel.74974F83_779E_3983_FF6B_D6B9ABF34537 ; DirectoryId=payload_ul.74974F83_779E_3983_FF6B_D6B9ABF34537 ; InstallDir=TARGETDIR/Windows/winsxs/x86_microsoft.msxml2_6bd6b9abf345378f_4.30.2100.0_none_3983779e74974f83 ; FileName=msxml4.dll ; InstallPath=TARGETDIR/Windows/winsxs/x86_microsoft.msxml2_6bd6b9abf345378f_4.30.2100.0_none_3983779e74974f83/msxml4.dll ; FileSize=1328968 ; Version=4.30.2100.0 ; Language=0 ; Sequence=9
```

### `pts_offline_inventory/reports/payload_investigation/msi_keyword_hits.tsv`
- Structure: `TSV`
- Data rows: **0**
- Columns: `keyword, File, InstallPath, Component, FileSize`
- Truth columns: `File, InstallPath`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `keyword` | Technical field as produced by source report. | 0 | 0 |
| `File` | MSI file identifier/name. | 0 | 0 |
| `InstallPath` | Resolved install path from MSI tables. | 0 | 0 |
| `Component` | MSI component identifier. | 0 | 0 |
| `FileSize` | Technical field as produced by source report. | 0 | 0 |

### `pts_offline_inventory/reports/payload_investigation/msi_tables/Component.tsv`
- Structure: `TSV`
- Data rows: **10**
- Columns: `Component, ComponentId, Directory_, Attributes, Condition, KeyPath`
- Truth columns: `Component`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `Component` | MSI component identifier. | 10 | 10 |
| `ComponentId` | Technical field as produced by source report. | 10 | 10 |
| `Directory_` | Technical field as produced by source report. | 10 | 8 |
| `Attributes` | Technical field as produced by source report. | 10 | 3 |
| `Condition` | Technical field as produced by source report. | 6 | 2 |
| `KeyPath` | Technical field as produced by source report. | 9 | 9 |

- Sample rows:
```text
Component=RememberInstallFolder ; ComponentId={4075CDF6-D88F-4F57-AF1A-29A124755695} ; Directory_=MSXML ; Attributes=0
Component=EulaFile ; ComponentId={AD9EB29E-E802-4F60-9296-19D19D6966F8} ; Directory_=MSXML ; Attributes=0 ; KeyPath=xmleula.rtf
```

### `pts_offline_inventory/reports/payload_investigation/msi_tables/Directory.tsv`
- Structure: `TSV`
- Data rows: **23**
- Columns: `Directory, Directory_Parent, DefaultDir`
- Truth columns: `Directory`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `Directory` | Technical field as produced by source report. | 23 | 23 |
| `Directory_Parent` | Technical field as produced by source report. | 22 | 8 |
| `DefaultDir` | Technical field as produced by source report. | 23 | 18 |

- Sample rows:
```text
Directory=TARGETDIR ; DefaultDir=SourceDir
Directory=MSXML ; Directory_Parent=ProgramFilesFolder ; DefaultDir=MSXML4|MSXML 4.0:redist
```

### `pts_offline_inventory/reports/payload_investigation/msi_tables/Feature.tsv`
- Structure: `TSV`
- Data rows: **3**
- Columns: `Feature, Feature_Parent, Title, Description, Display, Level, Directory_, Attributes`
- Truth columns: `Feature`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `Feature` | MSI feature identifier. | 3 | 3 |
| `Feature_Parent` | Technical field as produced by source report. | 2 | 1 |
| `Title` | Technical field as produced by source report. | 3 | 3 |
| `Description` | Technical field as produced by source report. | 3 | 3 |
| `Display` | Technical field as produced by source report. | 3 | 2 |
| `Level` | Technical field as produced by source report. | 3 | 1 |
| `Directory_` | Technical field as produced by source report. | 0 | 0 |
| `Attributes` | Technical field as produced by source report. | 3 | 1 |

- Sample rows:
```text
Feature=MSXML ; Title=Microsoft XML Parser ; Description=Microsoft XML Parser ; Display=1 ; Level=3 ; Attributes=24
Feature=MSXMLSYS ; Feature_Parent=MSXML ; Title=MSXML (global installation) ; Description=Microsoft XML Parser (global installation) ; Display=1 ; Level=3 ; Attributes=24
```

### `pts_offline_inventory/reports/payload_investigation/msi_tables/FeatureComponents.tsv`
- Structure: `TSV`
- Data rows: **10**
- Columns: `Feature_, Component_`
- Truth columns: `Feature_`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `Feature_` | Technical field as produced by source report. | 10 | 3 |
| `Component_` | Technical field as produced by source report. | 10 | 10 |

- Sample rows:
```text
Feature_=MSXML ; Component_=RememberInstallFolder
Feature_=MSXML ; Component_=EulaFile
```

### `pts_offline_inventory/reports/payload_investigation/msi_tables/File.tsv`
- Structure: `TSV`
- Data rows: **15**
- Columns: `File, Component_, FileName, FileSize, Version, Language, Attributes, Sequence`
- Truth columns: `File`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `File` | MSI file identifier/name. | 15 | 15 |
| `Component_` | Technical field as produced by source report. | 15 | 9 |
| `FileName` | Technical field as produced by source report. | 15 | 15 |
| `FileSize` | Technical field as produced by source report. | 15 | 7 |
| `Version` | Technical field as produced by source report. | 6 | 1 |
| `Language` | Technical field as produced by source report. | 6 | 2 |
| `Attributes` | Technical field as produced by source report. | 3 | 1 |
| `Sequence` | Technical field as produced by source report. | 15 | 15 |

- Sample rows:
```text
File=xmleula.rtf ; Component_=EulaFile ; FileName=xmleula.rtf ; FileSize=154033 ; Attributes=512 ; Sequence=1
File=msxml4.dll.246EB7AD_459A_4FA8_83D1_41A46D7634B7 ; Component_=MSXML4_System.246EB7AD_459A_4FA8_83D1_41A46D7634B7 ; FileName=msxml4.dll ; FileSize=1328968 ; Version=4.30.2100.0 ; Language=0 ; Attributes=512 ; Sequence=2
```

### `pts_offline_inventory/reports/payload_investigation/msi_tables/Media.tsv`
- Structure: `TSV`
- Data rows: **1**
- Columns: `DiskId, LastSequence, DiskPrompt, Cabinet, VolumeLabel, Source`
- Truth columns: `DiskId`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `DiskId` | Technical field as produced by source report. | 1 | 1 |
| `LastSequence` | Technical field as produced by source report. | 1 | 1 |
| `DiskPrompt` | Technical field as produced by source report. | 0 | 0 |
| `Cabinet` | Technical field as produced by source report. | 1 | 1 |
| `VolumeLabel` | Technical field as produced by source report. | 0 | 0 |
| `Source` | Technical field as produced by source report. | 0 | 0 |

- Sample rows:
```text
DiskId=1 ; LastSequence=15 ; Cabinet=#XML_Core.cab
```

### `pts_offline_inventory/reports/payload_investigation/payload_msi_cab_list.tsv`
- Structure: `TSV`
- Data rows: **5**
- Columns: `type, size_bytes, path`
- Truth columns: `type, path`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `type` | Artifact type (msi/cab/etc). | 5 | 2 |
| `size_bytes` | File size in bytes. | 5 | 5 |
| `path` | Scanned file path. | 5 | 5 |

- Sample rows:
```text
type=cab ; size_bytes=83826 ; path=pts_offline_inventory/extracted/rawscan_2/2.cab
type=cab ; size_bytes=6082804 ; path=pts_offline_inventory/extracted/rawscan_2/4.cab
```


## תמצית תוכן מלאה-למשמעות

- Payload list: CAB **4**, MSI **1**.
- Payload total size: **22,057,998** bytes.
- Tool status rows: **5** | failures: **0**.
- Burn token hits: **26** | by token: {'.wixburn': 10, 'Burn v': 4, 'BootstrapperApplication': 12}.
- ETS/XML inventory: **57** files | with TCID hits: **0**.
- ETS/XML hit rows: **0**.

| Payload indicator | Value | Source |
|---|---:|---|
| CAB payload files | 4 | `pts_offline_inventory/reports/payload_investigation/payload_msi_cab_list.tsv` |
| MSI payload files | 1 | `pts_offline_inventory/reports/payload_investigation/payload_msi_cab_list.tsv` |
| Burn signature hits | 26 | `pts_offline_inventory/reports/payload_investigation/burn_signature_hits.tsv` |
| ETS/XML files scanned | 57 | `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv` |
| ETS/XML files with TCID hits | 0 | `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv` |

## קבצים שדורשים עיון מלא

| File | Size (bytes) | Why full review matters | Recommended cross-check |
|---|---:|---|---|
| `pts_offline_inventory/reports/payload_investigation/cab_inventory_full.tsv` | 14,616 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/cab_inventory_top30.tsv` | 14,019 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv` | 5,789 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/msi_file_install_map.tsv` | 5,675 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Directory.tsv` | 2,807 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/File.tsv` | 2,553 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/Component.tsv` | 1,958 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/burn_signature_hits.tsv` | 1,823 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/msi_cab_tool_status.tsv` | 1,669 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/investigation_summary.md` | 1,249 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/msi_tables/FeatureComponents.tsv` | 563 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/payload_investigation/firmware_summary.tsv` | 428 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |

## עקיבות

| Claim | Source |
|---|---|
| Burn signature evidence is captured in token-offset hits. | `pts_offline_inventory/reports/payload_investigation/burn_signature_hits.tsv` |
| MSI/CAB payload inventory and sizes come from payload list report. | `pts_offline_inventory/reports/payload_investigation/payload_msi_cab_list.tsv` |
| MSI/CAB tool success/failure is captured by list/extract status. | `pts_offline_inventory/reports/payload_investigation/msi_cab_tool_status.tsv` |
| ETS/XML scan coverage and hit counts come from ETS inventory files. | `pts_offline_inventory/reports/payload_investigation/ets_xml_inventory.tsv` |
