---
profile_id: SCPS
display_name_he: שירות פרמטרי סריקה
doc_kind: logic
status: reviewed
updated_at: 2026-02-25
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

```groupb_finding
{
  "id": "scps_logic_phase1_subset_write_and_refresh_split",
  "title_he": "החלטת Phase 1 לוגית: לממש write path בסיסי + Refresh path מפורש ולהשאיר policy scan מתקדם לשלב 2",
  "statement_he": "לשלב ראשון מומלץ לממש לוגיקה בסיסית של write handling עבור Scan Interval Window, שמירת state, ו-Refresh path מפורש (API/trigger), תוך דחיית policy scan מתקדם ואופטימיזציות runtime לשלב 2.",
  "why_it_matters_he": "הפרדה כזו מייצבת את התאימות לשירות GATT עצמו ומקטינה coupling מוקדם עם scan runtime behavior.",
  "confidence": "medium",
  "status": "inferred",
  "derivation_method_ids": ["api_call_sequence_analysis", "profile_similarity_inference", "callback_registration_pattern"],
  "source_ids": ["sig_scps_spec_page", "ti_scanparamservice_doxygen_h", "nordic_ncs_sample_shorter_conn_intervals_main"],
  "evidence_refs": [
    {
      "source_id": "ti_scanparamservice_doxygen_h",
      "what_identified_he": "קיום API מפורש ScanParam_RefreshNotify בנוסף ל-Set/Get/Register.",
      "how_identified_he": "קריאת declarations ב-header Doxygen.",
      "artifact_ref": "TI Doxygen: scanparamservice_8h.html",
      "line_refs": ["216-224", "243-322"],
      "confidence": "high"
    },
    {
      "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
      "what_identified_he": "פיצול בין GATT service לבין scan runtime callbacks/init.",
      "how_identified_he": "קריאת service definition מול scan_init/scan callbacks.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
      "line_refs": ["86-99", "130-182"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "שלב 2: policy מלא של scan runtime, retries, ותיאום מתקדם עם callbacks אפליקטיביים.",
    "לשמור את החלטת שלב 1 גם במסמך המבנה כדי לקבע גבולות מודולים."
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

```groupb_source_observation
{
  "id": "scps_logic_obs_sig_scps_page_scope",
  "profile_id": "SCPS",
  "doc_kind": "logic",
  "source_id": "sig_scps_spec_page",
  "what_identified_he": "עמוד spec רשמי adopted (Scan Parameters Service 1.0) וסט ארטיפקטים רשמי לתיחום תכולת Phase 1.",
  "how_identified_he": "קריאת עמוד spec רשמי והצלבה עם inventory המסונכרן ב-Hub (Spec/TS/ICS/TCRL).",
  "artifact_ref": "Bluetooth SIG spec page + docs/profiles/SCPS",
  "line_refs": ["spec page metadata", "hub spec inventory row"],
  "confidence": "high",
  "notes_he": "משמש להחלטות scope ושלבים; flow לוגי מפורט נגזר ממקורות TI/NCS."
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
  "status": "resolved",
  "source_ids": [
    "sig_scps_spec_page",
    "ti_scanparamservice_doxygen_c"
  ]
}
```

## השלכות למימוש

- להפריד בין state/policy של scan parameters לבין API של SCPS service handlers.
- להגדיר API נפרד ל-Scan Refresh notify/indicate (לפי spec) ולא לשלבו אוטומטית ב-write path.
- להשתמש ב-scan callback/events באפליקציה כדי לתרגם policy מעודכן לפעולות runtime.

## החלטות Phase 1

```groupb_decision
{
  "id": "scps_logic_phase1_refresh_trigger_decision",
  "profile_id": "SCPS",
  "doc_kind": "logic",
  "phase": "phase1",
  "title_he": "Phase 1: Scan Refresh מנוהל ע\"י trigger מפורש מהאפליקציה/stack adapter",
  "decision_he": "הלוגיקה לא תפעיל refresh באופן אוטומטי לפי heuristics; יוגדר trigger מפורש שמגיע משכבת adapter בהתאם לשינוי פרמטרי סריקה או אירוע חיבור.",
  "rationale_he": "מונע side effects מוקדמים ושומר על שליטה ברורה בזרימת runtime בשלב הראשון.",
  "status": "decided",
  "confidence": "high",
  "derivation_method_ids": [
    "api_call_sequence_analysis",
    "callback_registration_pattern"
  ],
  "source_ids": [
    "nordic_sdk_nrf_repo",
    "nordic_ncs_docs",
    "nordic_ncs_sample_shorter_conn_intervals_main",
    "ti_scanparamservice_doxygen_h"
  ],
  "impacts_he": [
    "מגדיר גבול אחריות ברור בין logic ל-adapter",
    "מקל על בדיקות PTS/AutoPTS ממוקדות trigger"
  ],
  "applies_to_checks": [
    "phase1_subset_decided",
    "implementation_contract_defined"
  ]
}
```

## חוזה מימוש (Implementation Contract)

חוזה המימוש המלא ל-Phase 1 מרוכז במסמך ה-Structure של הפרופיל כדי לשמור מקור אמת אחד לחוזה המבני/ריצתי.

- מסמך זה (Logic) מספק את ההחלטות הלוגיות והצדקת ה-flow.
- מסמך Structure מכיל את `groupb_impl_contract`, `groupb_test_target`, `groupb_review_signoff`.

## יעדי בדיקות Phase 1

- יעדי הבדיקות המלאים מרוכזים ב-Structure כדי למנוע כפילות.
- ברמת Logic יש לוודא בפרט: gating, trigger policy, ו-return status עקבי.

## חתימת Review / מוכנות

- review לוגיקה עבור ScPS נסגר ומסוכם בחתימת ה-review שבמסמך Structure.
- מסמך זה נשאר מקור ההסברים וההסקות הלוגיות, לא מקור חתימה כפול.

## מקורות

- `nordic_sdk_nrf_repo`
- `nordic_ncs_docs`
- `nordic_ncs_sample_shorter_conn_intervals_main`
- `ti_scanparamservice_doxygen_h`
- `ti_scanparamservice_doxygen_c`
- `sig_scps_spec_page`
