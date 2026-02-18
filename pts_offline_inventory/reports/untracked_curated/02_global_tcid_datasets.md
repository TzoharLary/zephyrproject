# Group 2: Global TCID Datasets

Files in group: **5** | Total size: **555.7 KB**

## מה יש בקבוצה

| File | Type | Size (bytes) |
|---|---|---:|
| `pts_offline_inventory/reports/tcid_all_sources.tsv` | TSV | 286,943 |
| `pts_offline_inventory/reports/tcid_unique_with_sources.tsv` | TSV | 239,577 |
| `pts_offline_inventory/reports/tcids_unique_all.txt` | TXT | 42,493 |
| `pts_offline_inventory/reports/tcids_unmapped.txt` | TXT | 0 |
| `pts_offline_inventory/reports/tcids_unmapped_with_source.tsv` | TSV | 16 |

## שדות קריטיים שנשמרים

### `pts_offline_inventory/reports/tcid_all_sources.tsv`
- Structure: `TSV`
- Data rows: **2,028**
- Columns: `tcid, sources`
- Truth columns: `tcid, sources`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `tcid` | Full TCID identifier (truth key for test identity). | 2,028 | 2,028 |
| `sources` | All source locations where TCID was found. | 2,028 | 146 |

- Sample rows:
```text
tcid=AIOS/SR/CI/BV-01-C ; sources=pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_indication.json ; pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_notification.json ; pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_indication.json ; pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_notification.json ; pts_offline_inventory/extracted/python_automation/platforms/Cyble/handlers/aiosHandler.py
tcid=AIOS/SR/CI/BV-02-C ; sources=pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_indication.json ; pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_notification.json ; pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_indication.json ; pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_notification.json
```

### `pts_offline_inventory/reports/tcid_unique_with_sources.tsv`
- Structure: `TSV`
- Data rows: **2,028**
- Columns: `prefix, tcid, source_count, one_source`
- Truth columns: `prefix, tcid, one_source`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `prefix` | Profile/service prefix derived from TCID. | 2,028 | 42 |
| `tcid` | Full TCID identifier (truth key for test identity). | 2,028 | 2,028 |
| `source_count` | How many sources contain this TCID. | 2,028 | 5 |
| `one_source` | One representative source path for this TCID. | 2,028 | 118 |

- Sample rows:
```text
prefix=AIOS ; tcid=AIOS/SR/CI/BV-01-C ; source_count=5 ; one_source=pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_indication.json
prefix=AIOS ; tcid=AIOS/SR/CI/BV-02-C ; source_count=4 ; one_source=pts_offline_inventory/extracted/python_automation/platforms/Cyble/Configs/aios_aggregate_indication.json
```

### `pts_offline_inventory/reports/tcids_unique_all.txt`
- Structure: `TXT`
- Lines: **2,028** | Non-empty: **2,028**
- Detected shape: `tcid_list`
- Truth rule: each non-empty line is a full TCID.

- Sample lines:
```text
AIOS/SR/CI/BV-01-C
AIOS/SR/CI/BV-02-C
AIOS/SR/CI/BV-03-C
AIOS/SR/CI/BV-04-C
AIOS/SR/CI/BV-05-C
```

### `pts_offline_inventory/reports/tcids_unmapped.txt`
- Structure: `TXT`
- Lines: **0** | Non-empty: **0**
- Detected shape: `general_text`
- Truth rule: preserve line-level textual evidence.

### `pts_offline_inventory/reports/tcids_unmapped_with_source.tsv`
- Structure: `TSV`
- Data rows: **0**
- Columns: `tcid, one_source`
- Truth columns: `tcid, one_source`

| Column | Meaning | Non-empty | Unique non-empty |
|---|---|---:|---:|
| `tcid` | Full TCID identifier (truth key for test identity). | 0 | 0 |
| `one_source` | One representative source path for this TCID. | 0 | 0 |


## תמצית תוכן מלאה-למשמעות

- `tcid_unique_with_sources.tsv`: **2,028** unique TCIDs.
- `tcid_all_sources.tsv`: **2,028** `TCID -> sources` rows.
- `tcids_unique_all.txt`: **2,028** TCID lines.
- `tcids_unmapped_with_source.tsv`: **0** unmapped rows.
- `source_count`: max **5**, avg **1.30**.

| Top prefix (from `tcids_unique_all.txt`) | TCID count |
|---|---:|
| `MMDL` | 379 |
| `MESH` | 304 |
| `GATT` | 141 |
| `UDS` | 133 |
| `AIOS` | 131 |
| `IDS` | 107 |
| `SM` | 80 |
| `CGMS` | 79 |
| `IPS` | 62 |
| `CPS` | 46 |
| `LNS` | 42 |
| `HIDS` | 40 |
| `ESS` | 39 |
| `GLS` | 38 |
| `PLXS` | 36 |
| `HPS` | 29 |
| `ANS` | 28 |
| `GAP` | 25 |
| `PASS` | 19 |
| `RSCS` | 19 |

## קבצים שדורשים עיון מלא

| File | Size (bytes) | Why full review matters | Recommended cross-check |
|---|---:|---|---|
| `pts_offline_inventory/reports/tcid_all_sources.tsv` | 286,943 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/tcid_unique_with_sources.tsv` | 239,577 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/tcids_unique_all.txt` | 42,493 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/tcids_unmapped_with_source.tsv` | 16 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |
| `pts_offline_inventory/reports/tcids_unmapped.txt` | 0 | High-density file with strong impact on conclusions. | Cross-check against group summaries and source evidence files. |

## עקיבות

| Claim | Source |
|---|---|
| Unique TCID cardinality comes from `tcid_unique_with_sources.tsv`. | `pts_offline_inventory/reports/tcid_unique_with_sources.tsv` |
| All-source coverage comes from `tcid_all_sources.tsv`. | `pts_offline_inventory/reports/tcid_all_sources.tsv` |
| Prefix distribution is computed from `tcids_unique_all.txt`. | `pts_offline_inventory/reports/tcids_unique_all.txt` |
