---
profile_id: SCPS
display_name_he: שירות פרמטרי סריקה
doc_kind: logic
status: in_progress
updated_at: 2026-02-24
primary_sdk_source_policy: nordic_official_only
secondary_pattern_sources_policy: local_or_official_only
language: he
schema_version: 1
---

## סיכום

לא זוהה מימוש SCPS ישיר ב-NCS בנתיבי ה-Bluetooth שנסרקו. הלוגיקה של SCPS נגזרת משילוב בין דפוסי סריקה ו-GATT custom service ב-NCS (`shorter_conn_intervals`) לבין המודול הייעודי `scanparamservice` ב-TI שמגדיר write callbacks, callback registration ו-RefreshNotify ייעודי.

## ממצאים

```groupb_finding
{
  "id": "scps_logic_ncs_direct_impl_absent_in_scanned_paths",
  "title_he": "לא זוהה מימוש SCPS ישיר ב-NCS ב-scope שנסרק",
  "statement_he": "בסריקת NCS לא נמצאו התאמות ישירות ל-Scan Parameters Service / SCPS / UUID 0x1813 בנתיבי Bluetooth שנסרקו.",
  "why_it_matters_he": "מוביל להסקת לוגיקה משילוב דפוסי scan + GATT patterns במקום sample ייעודי.",
  "confidence": "medium",
  "status": "confirmed",
  "derivation_method_ids": ["repo_text_presence_scan"],
  "source_ids": ["nordic_sdk_nrf_repo", "nordic_ncs_docs"]
}
```

```groupb_finding
{
  "id": "scps_logic_scan_parameter_runtime_pattern_from_shorter_conn_intervals",
  "title_he": "דפוס runtime של scan parameters ב-NCS זמין דרך shorter_conn_intervals",
  "statement_he": "דוגמת shorter_conn_intervals מדגימה scan_init עם struct bt_le_scan_param, רישום scan callbacks, והפעלת פילטר UUID. זה מספק דפוס לוגי רלוונטי למסלול scan parameter handling בצד האפליקציה.",
  "why_it_matters_he": "SCPS נוגע ישירות לפרמטרי סריקה; דפוס זה מספק עוגן פרקטי לשילוב בין service-level writes לבין מנגנון scan בפועל.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["api_call_sequence_analysis", "state_machine_flow_read"],
  "source_ids": ["nordic_ncs_sample_shorter_conn_intervals_main"],
  "evidence_refs": [
    {
      "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
      "what_identified_he": "scan_init עם bt_le_scan_param, bt_scan_init, bt_scan_cb_register ו-filter by UUID.",
      "how_identified_he": "קריאת scan_init() והפונקציות הסמוכות לו בקובץ הדוגמה.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
      "line_refs": ["130-182"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "SCPS service לא צריך להחזיק בעצמו את כל scan engine logic; הוא יכול לעדכן policy/state שממנו שכבת app מפעילה scan APIs."
  ]
}
```

```groupb_finding
{
  "id": "scps_logic_custom_gatt_service_pattern_from_shorter_conn_intervals",
  "title_he": "דפוס custom GATT service ב-NCS מתאים לבסיס SCPS בצד Zephyr",
  "statement_he": "ב-shorter_conn_intervals מוגדר שירות GATT סטטי עם read callback ו-characteristic UUID ייעודי. הדפוס מתאים לבניית SCPS ב-Zephyr (service define + read/write handlers) גם אם ה-UUIDs וה-props שונים.",
  "why_it_matters_he": "מאפשר לבנות SCPS service skeleton במהירות עם חלוקת אחריות נכונה בין handlers לבין scan logic.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "callback_registration_pattern"],
  "source_ids": ["nordic_ncs_sample_shorter_conn_intervals_main"],
  "evidence_refs": [
    {
      "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
      "what_identified_he": "read callback + BT_GATT_SERVICE_DEFINE לשירות custom.",
      "how_identified_he": "קריאת read_min_interval() והגדרת sci_min_interval_svc.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
      "line_refs": ["86-99"],
      "confidence": "high"
    }
  ]
}
```

```groupb_finding
{
  "id": "scps_logic_ti_scanparamservice_two_path_flow",
  "title_he": "TI scanparamservice מרמז על שני מסלולים לוגיים: write handling + refresh notify",
  "statement_he": "ב-API של TI Scan Parameter Service יש גם Set/Get/Register וגם פונקציה נפרדת ScanParam_RefreshNotify, ובקובץ ה-C מופיעים read/write callbacks ו-conn-status callback. זה מצביע על לוגיקה מפוצלת: טיפול בכתיבות פרמטרים מצד אחד ו-trigger ייעודי ל-Scan Refresh מצד שני.",
  "why_it_matters_he": "ב-SCPS חשוב לא לערבב בין עדכון פרמטרי סריקה לבין notification של Scan Refresh; הפרדה זו תשפר בהירות ותאימות ל-spec.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["api_call_sequence_analysis", "ccc_handling_pattern", "vendor_sample_structure_pattern"],
  "source_ids": ["ti_scanparamservice_doxygen_h", "ti_scanparamservice_doxygen_c"],
  "implementation_notes_he": [
    "להגדיר API נפרד עבור refresh notification ולא להסתיר אותו בתוך write handler.",
    "לשמור callback/adapter למסלול שמעדכן scan policy runtime."
  ]
}
```

## תצפיות לפי מקור

```groupb_source_observation
{
  "id": "scps_logic_obs_ncs_shorter_conn_intervals_scan",
  "profile_id": "SCPS",
  "doc_kind": "logic",
  "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
  "what_identified_he": "דפוס scan parameter struct + scan callbacks + UUID filters באפליקציית NCS.",
  "how_identified_he": "קריאת scan_init(), scan callbacks, ו-BT_SCAN_CB_INIT.",
  "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
  "line_refs": ["130-182"],
  "confidence": "high"
}
```

```groupb_source_observation
{
  "id": "scps_logic_obs_ti_scanparamservice_h_api",
  "profile_id": "SCPS",
  "doc_kind": "logic",
  "source_id": "ti_scanparamservice_doxygen_h",
  "what_identified_he": "קיום API ייעודי ScanParam_RefreshNotify בנוסף ל-Add/Register/Set/GetParameter.",
  "how_identified_he": "קריאת declarations ב-scanparamservice.h File Reference.",
  "artifact_ref": "TI Doxygen: scanparamservice_8h.html",
  "line_refs": ["216-224", "243-322"],
  "confidence": "high"
}
```

```groupb_source_observation
{
  "id": "scps_logic_obs_ti_scanparamservice_c_handlers",
  "profile_id": "SCPS",
  "doc_kind": "logic",
  "source_id": "ti_scanparamservice_doxygen_c",
  "what_identified_he": "read/write callbacks, conn status callback ו-attr table פנימי של השירות.",
  "how_identified_he": "קריאת function/member list ב-scanparamservice.c File Reference.",
  "artifact_ref": "TI Doxygen: scanparamservice_8c.html",
  "line_refs": ["139-169"],
  "confidence": "high"
}
```

## שיטות חילוץ/ניתוח

```groupb_method
{
  "id": "repo_text_presence_scan",
  "profile_id": "SCPS",
  "doc_kind": "logic",
  "status": "used",
  "notes_he": "סריקת NCS כדי לזהות אם יש מימוש SCPS ישיר לפני מעבר לדפוסי scan/GATT קרובים."
}
```

```groupb_method
{
  "id": "ti_doxygen_api_surface_read",
  "profile_id": "SCPS",
  "doc_kind": "logic",
  "status": "used",
  "notes_he": "חילוץ flow לוגי משירות TI דרך header/c Doxygen (write handlers + refresh notify)."
}
```

## פערים ושאלות פתוחות

```groupb_open_question
{
  "id": "scps_logic_q1_refresh_notification_trigger",
  "profile_id": "SCPS",
  "title_he": "מתי בדיוק להוציא Scan Refresh במימוש היעד",
  "detail_he": "יש למפות מול spec את תנאי ההוצאה של Scan Refresh (טריגרים ותנאי subscription), ולא להסתמך רק על API surface של TI/NCS patterns.",
  "priority": "high",
  "status": "open",
  "source_ids": ["sig_scps_spec_page", "ti_scanparamservice_d  "source_ids": ["sig_scps_spee_doxygen_c"]
}
```

## השלכות למימוש

- להפריד בין state/policy של scan parameters לבין API של SCPS service handlers.
- להגדיר API נפרד ל-Scan Refresh notify/indicate (לפי spec) ולא לשלבו אוטומטית ב-write path.
- להשתמש ב-scan callback/events באפליקציה כדי לתרגם policy מעודכן לפעולות runtime.

## מקורות

- `nordic_sdk_nrf_repo`
- `nordic_ncs_docs`
- `nordic_ncs_sample_shorter_conn_intervals_main`
- `ti_scanparamservice_doxygen_h`
- `ti_scanparamservice_doxygen_c`
- `sig_scps_spec_page`
