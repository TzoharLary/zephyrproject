---
profile_id: BPS
display_name_he: שירות לחץ דם
doc_kind: logic
status: in_progress
updated_at: 2026-02-24
primary_sdk_source_policy: nordic_official_only
secondary_pattern_sources_policy: local_or_official_only
language: he
schema_version: 1
---

## סיכום

לא זוהה מימוש BPS ישיר בנתיבי ה-Bluetooth שנסרקו ב-nRF Connect SDK (NCS) במסגרת ההכנה, ולכן הלוגיקה נגזרת משילוב של דפוסים רשמיים קרובים: שירותי health ב-NCS/Zephyr (בעיקר CGMS/HRS) וספריות שירות ייעודיות של TI עבור BPS. התוצאה בשלב זה היא מודל לוגי ברור למימוש עתידי: init + register callbacks + CCC gating + publish path (measurement / control-point related flow) + error handling/retry.

## ממצאים

```groupb_finding
{
  "id": "bps_logic_ncs_direct_impl_absent_in_scanned_paths",
  "title_he": "לא זוהה מימוש BPS ישיר בנתיבי Bluetooth שנסרקו ב-NCS",
  "statement_he": "בסריקת NCS (samples/bluetooth, subsys/bluetooth, doc/nrf) לא נמצאו התאמות ישירות ל-BPS/UUID 0x1810, ולכן אין כרגע מקור לוגיקה ישיר של BPS ב-NCS שניתן לבסס עליו מימוש 1:1.",
  "why_it_matters_he": "זה מכריח בניית לוגיקה מדפוסים קרובים ולא מהעתקה של דוגמה רשמית קיימת, ומגדיל את חשיבות עקיבות המקורות והסקת הדמיון.",
  "confidence": "medium",
  "status": "confirmed",
  "derivation_method_ids": ["repo_text_presence_scan"],
  "source_ids": ["nordic_sdk_nrf_repo", "nordic_ncs_docs"],
  "evidence_refs": [
    {
      "source_id": "nordic_sdk_nrf_repo",
      "what_identified_he": "היעדר התאמה ישירה ל-BPS/SCPS/WSS בנתיבי Bluetooth הרלוונטיים שנכללו ב-sparse checkout.",
      "how_identified_he": "סריקת טקסט ממוקדת לפי שמות שירות/ראשי תיבות/UUIDs ב-samples/subsys/doc תחת NCS.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf (sparse checkout: samples/bluetooth, subsys/bluetooth, doc)",
      "line_refs": ["search scope: samples/bluetooth + subsys/bluetooth + doc/nrf"],
      "confidence": "medium"
    }
  ],
  "implementation_notes_he": [
    "להשאיר את ה-finding הזה כממצא הקשר (context) ולא כמסקנה פונקציונלית על BPS עצמו.",
    "במימוש בפועל יש לעגן כל חלק לוגי במקור דפוס ספציפי (CGMS/HRS/TI BPS)."
  ]
}
```

```groupb_finding
{
  "id": "bps_logic_health_session_and_measurement_pipeline_pattern",
  "title_he": "דפוס לוגיקת health service ב-NCS: callback-driven session + measurement loop",
  "statement_he": "בדוגמת CGMS של NCS הלוגיקה בנויה סביב callback לשינוי מצב session, init של פרמטרי השירות, ולאחר מכן לולאת main שמגישה measurements רק כשה-session פעיל, כולל retry אם ההוספה נכשלת.",
  "why_it_matters_he": "BPS כולל זרימת measurement ו-control flow שדורשת gating של שליחה/קבלה; דפוס זה מתאים לבניית state gating ו-publish path גם אם השירות שונה.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["callback_registration_pattern", "api_call_sequence_analysis", "state_machine_flow_read"],
  "source_ids": ["nordic_ncs_sample_peripheral_cgms_main"],
  "evidence_refs": [
    {
      "source_id": "nordic_ncs_sample_peripheral_cgms_main",
      "what_identified_he": "רישום callback לשינוי session state והצמדתו ל-init params.",
      "how_identified_he": "קריאת רצף init: מילוי params + cb + קריאה ל-bt_cgms_init().",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_cgms/src/main.c",
      "line_refs": ["125-133", "144-175"],
      "confidence": "high"
    },
    {
      "source_id": "nordic_ncs_sample_peripheral_cgms_main",
      "what_identified_he": "לולאה מחזורית שמגישה measurement רק אם session פעיל, עם retry_count/retry_interval.",
      "how_identified_he": "קריאת while(1) + תנאי session_state + retry loop סביב bt_cgms_measurement_add().",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_cgms/src/main.c",
      "line_refs": ["183-212"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "ב-BPS יש להפריד בין gating של Measurement לבין זרימות control/feature נוספות.",
    "כדאי לשמר retry/error logging רק במסלול publish ולא בקוד callback של CCC."
  ]
}
```

```groupb_finding
{
  "id": "bps_logic_ccc_and_notify_gate_pattern_from_zephyr_hrs",
  "title_he": "דפוס CCC gating ו-notify API בשירות Zephyr HRS",
  "statement_he": "ב-Zephyr HRS קיימת הפרדה בין callback שינוי CCC (הפעלת/כיבוי notifications) לבין פונקציית notify ציבורית של השירות שמבצעת bt_gatt_notify על attribute ידוע ומנרמלת ENOTCONN.",
  "why_it_matters_he": "ב-BPS נדרש דפוס דומה עבור Measurement/Intermediate Cuff Pressure (indicate/notify לפי התמיכה), והפרדה זו מפשטת API פנימי ומעקב אחרי מצב subscription.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["ccc_handling_pattern", "notification_indication_enable_flow", "api_call_sequence_analysis"],
  "source_ids": ["zephyr_bt_hrs_service_c"],
  "evidence_refs": [
    {
      "source_id": "zephyr_bt_hrs_service_c",
      "what_identified_he": "Callback שינוי CCC שמתרגם value ל-notif_enabled ומפיץ event ל-listeners.",
      "how_identified_he": "קריאת hrmc_ccc_cfg_changed וזרימת SYS_SLIST_FOR_EACH_CONTAINER.",
      "artifact_ref": "zephyr/subsys/bluetooth/services/hrs.c",
      "line_refs": ["58-73"],
      "confidence": "high"
    },
    {
      "source_id": "zephyr_bt_hrs_service_c",
      "what_identified_he": "פונקציית שירות ציבורית bt_hrs_notify עם payload assembly וקריאת bt_gatt_notify().",
      "how_identified_he": "קריאת bt_hrs_notify כולל שימוש ב-hrs_svc.attrs[1] וטיפול ב-ENOTCONN.",
      "artifact_ref": "zephyr/subsys/bluetooth/services/hrs.c",
      "line_refs": ["129-140"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "ל-BPS יש סיכוי גבוה שנידרש לשתי פונקציות publish נפרדות (measurement + intermediate cuff) עם מדיניות subscription שונה.",
    "יש לשקול abstraction עבור indicate/notify כדי לא לקבע notify בלבד כמו HRS."
  ]
}
```

```groupb_finding
{
  "id": "bps_logic_app_init_sequence_pattern_from_nus",
  "title_he": "דפוס סדר האתחול האפליקטיבי ב-NCS: bt_enable -> settings_load -> service_init -> advertising",
  "statement_he": "בדוגמת peripheral_uart (NUS) סדר העבודה הוא אתחול Bluetooth, טעינת settings (אם פעיל), אתחול service callbacks, ורק אז התחלת advertising/work.",
  "why_it_matters_he": "זה דפוס בטוח לשילוב BPS, במיוחד אם יהיו CCC persistence / bonding / settings-dependent behavior בהמשך.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["api_call_sequence_analysis", "callback_registration_pattern"],
  "source_ids": ["nordic_ncs_sample_peripheral_uart_main"],
  "evidence_refs": [
    {
      "source_id": "nordic_ncs_sample_peripheral_uart_main",
      "what_identified_he": "רישום callback structure לשירות לפני service init.",
      "how_identified_he": "קריאת static struct bt_nus_cb nus_cb ו-bt_nus_init(&nus_cb).",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_uart/src/main.c",
      "line_refs": ["540-542", "641-645"],
      "confidence": "high"
    },
    {
      "source_id": "nordic_ncs_sample_peripheral_uart_main",
      "what_identified_he": "סדר אתחול: bt_enable -> settings_load -> service init -> advertising_start.",
      "how_identified_he": "קריאת main() סביב שורות האתחול המרכזיות.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_uart/src/main.c",
      "line_refs": ["628-649"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לשמר סדר זה גם אם נוסיף bonding/settings ו-CCC restore.",
    "אם BPS יישען על work queue לשליחת מדידות, להפעיל אותו רק אחרי service init + advertising start."
  ]
}
```

## תצפיות לפי מקור

```groupb_source_observation
{
  "id": "bps_logic_obs_nordic_repo_absence_scan",
  "profile_id": "BPS",
  "doc_kind": "logic",
  "source_id": "nordic_sdk_nrf_repo",
  "what_identified_he": "לא נמצאו התאמות ישירות ל-BPS בנתיבי ה-Bluetooth שנסרקו ב-NCS (scope של ההכנה).",
  "how_identified_he": "סריקת טקסט ממוקדת לפי BPS/SCPS/WSS/UUIDs ב-samples/bluetooth, subsys/bluetooth, doc/nrf לאחר sparse-checkout.",
  "artifact_ref": ".cache/vendor_src/sdk-nrf (commit 2ed6388, sparse checkout scope)",
  "line_refs": ["search scope only (no direct file hit)"],
  "confidence": "medium",
  "notes_he": "זהו ממצא scope-dependent: מאשר היעדר דוגמה ישירה בנתיבים שנסרקו, לא היעדר מוחלט בכל ecosystem של Nordic."
}
```

```groupb_source_observation
{
  "id": "bps_logic_obs_ncs_cgms_flow",
  "profile_id": "BPS",
  "doc_kind": "logic",
  "source_id": "nordic_ncs_sample_peripheral_cgms_main",
  "what_identified_he": "דפוס health-service עם session callback, init params, advertising, ולולאת measurement + retry.",
  "how_identified_he": "ניתוח רצף קריאות API וקריאת flow של state/session בתוך main().",
  "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_cgms/src/main.c",
  "line_refs": ["125-133", "144-175", "180-212"],
  "confidence": "high",
  "notes_he": "הדפוס משמש להסקת BPS logic ברמת orchestration, לא למבנה payload ספציפי של BPS."
}
```

```groupb_source_observation
{
  "id": "bps_logic_obs_zephyr_hrs_ccc_notify",
  "profile_id": "BPS",
  "doc_kind": "logic",
  "source_id": "zephyr_bt_hrs_service_c",
  "what_identified_he": "הפרדה בין CCC callback לבין פונקציית notify ציבורית של השירות.",
  "how_identified_he": "קריאת callback שינוי CCC, הגדרת השירות ב-BT_GATT_SERVICE_DEFINE, ופונקציית bt_hrs_notify().",
  "artifact_ref": "zephyr/subsys/bluetooth/services/hrs.c",
  "line_refs": ["58-73", "82-95", "129-140"],
  "confidence": "high",
  "notes_he": "ב-BPS נדרש להתאים את הדפוס ל-indications/control point ולא רק notifications."
}
```

```groupb_source_observation
{
  "id": "bps_logic_obs_ti_bps_service_apis",
  "profile_id": "BPS",
  "doc_kind": "logic",
  "source_id": "ti_blood_pressure_service_doxygen_h",
  "what_identified_he": "ממשק שירות BPS ב-TI מגדיר AddService/Register/SetParameter/GetParameter וקולבקים ייעודיים לשירות.",
  "how_identified_he": "קריאת File Reference של blood_pressure_service.h (חתימות API וסוגי callbacks).",
  "artifact_ref": "TI BLE5-Stack Doxygen: blood_pressure_service_8h.html",
  "line_refs": ["callback types around lines 235-315", "Add/Register/Set/Get around lines 638-728"],
  "confidence": "high",
  "notes_he": "משמש לאימות שהלוגיקה ב-BPS נדרשת להיות service-module centric ולא רק אפליקטיבית."
}
```

## שיטות חילוץ/ניתוח

```groupb_method
{
  "id": "repo_text_presence_scan",
  "profile_id": "BPS",
  "doc_kind": "logic",
  "status": "used",
  "notes_he": "סריקת טקסט ממוקדת בנתיבי NCS רלוונטיים כדי לקבוע האם קיים מימוש ישיר לפרופיל לפני מעבר להסקת דפוסים."
}
```

```groupb_method
{
  "id": "ti_doxygen_api_surface_read",
  "profile_id": "BPS",
  "doc_kind": "logic",
  "status": "used",
  "notes_he": "קריאת File Reference (header/c) של TI כדי לזהות את משטח ה-API וה-flow המרכזי של השירות.",
  "_note": "method id מקומי כי זה לא method קנוני ב-catalog"
}
```

## פערים ושאלות פתוחות

```groupb_open_question
{
  "id": "bps_logic_q1_indication_vs_notification_split",
  "profile_id": "BPS",
  "title_he": "איזה מסלולי publish יוגדרו כ-indication לעומת notification במימוש היעד",
  "detail_he": "יש למפות במדויק מול ה-spec של BPS אילו characteristics דורשים indication/notification ומהם תנאי ההפעלה (CCC + feature support).",
  "priority": "high",
  "status": "open",
  "source_ids": ["sig_bps_spec_page", "ti_blood_pressure_service_doxygen_h", "ti_blood_pressure_service_doxygen_c"]
}
```

```groupb_open_question
{
  "id": "bps_logic_q2_payload_builder_scope",
  "profile_id": "BPS",
  "title_he": "היכן למקם את בניית ה-payload של המדידה",
  "detail_he": "יש להחליט אם בניית payload תישב בשכבת השירות (service module) או בשכבת adapter/logic מעליה, כדי לשמור separation טוב בין domain data ל-BLE serialization.",
  "priority": "medium",
  "status": "open",
  "source_ids": ["ti_blood_pressure_service_doxygen_c", "zephyr_bt_hrs_service_c"]
}
```

## השלכות למימוש

- להתחיל מ-API שירות פנימי בסגנון `init/register/set/get/publish`, ולחבר אליו שכבת אפליקציה נפרדת.
- להפריד מוקדם בין `CCC state tracking` לבין `measurement payload production`.
- להגדיר מסלול retry/logging עבור publish failures (בדומה לדפוס CGMS), אבל לא לשלב retry בתוך callbacks של GATT.
- להוסיף abstraction ל-`notify/indicate` כדי לא להינעל על דפוס HRS של notify בלבד.

## מקורות

- `nordic_sdk_nrf_repo`
- `nordic_ncs_docs`
- `nordic_ncs_sample_peripheral_cgms_main`
- `nordic_ncs_sample_peripheral_uart_main`
- `zephyr_bt_hrs_service_c`
- `ti_blood_pressure_service_doxygen_h`
- `ti_blood_pressure_service_doxygen_c`
- `sig_bps_spec_page`
