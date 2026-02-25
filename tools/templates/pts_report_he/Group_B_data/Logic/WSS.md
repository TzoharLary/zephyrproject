---
profile_id: WSS
display_name_he: שירות משקל
doc_kind: logic
status: in_progress
updated_at: 2026-02-24
primary_sdk_source_policy: nordic_official_only
secondary_pattern_sources_policy: local_or_official_only
language: he
schema_version: 1
---

## סיכום

לא זוהה מימוש WSS ישיר בנתיבי NCS שנסרקו, ולכן לוגיקת WSS נגזרת מדפוסי health/measurement רשמיים ב-NCS/Zephyr (HRS/BAS/CGMS) בשילוב API surface של TI Weight Service. הדגש בשלב ההכנה הוא על publish path עם gating לפי subscription, תזמון/טריגר מדידות, וסדר אתחול שירות ברור.

## ממצאים

```groupb_finding
{
  "id": "wss_logic_ncs_direct_impl_absent_in_scanned_paths",
  "title_he": "לא זוהה מימוש WSS ישיר ב-NCS ב-scope שנסרק",
  "statement_he": "בסריקת NCS בנתיבי Bluetooth הרלוונטיים לא נמצאו התאמות ישירות לשירות Weight Scale או ל-UUID 0x181D.",
  "why_it_matters_he": "מחייב בנייה מדפוסי health service דומים במקום הסתמכות על sample ייעודי.",
  "confidence": "medium",
  "status": "confirmed",
  "derivation_method_ids": ["repo_text_presence_scan"],
  "source_ids": ["nordic_sdk_nrf_repo", "nordic_ncs_docs"],
  "evidence_refs": [
    {
      "source_id": "nordic_sdk_nrf_repo",
      "what_identified_he": "היעדר התאמות ישירות ל-WSS/UUID 0x181D בנתיבי Bluetooth שנסרקו.",
      "how_identified_he": "סריקת טקסט ממוקדת ב-samples/bluetooth, subsys/bluetooth, doc/nrf לאחר sparse checkout.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf (sparse checkout scope)",
      "line_refs": ["search scope only (no direct file hit)"],
      "confidence": "medium"
    }
  ]
}
```

```groupb_finding
{
  "id": "wss_logic_periodic_measurement_simulation_pattern",
  "title_he": "דפוס מדידה מחזורית + publish דרך work handler (NCS peripheral_hr_coded)",
  "statement_he": "בדוגמת peripheral_hr_coded קיימת לוגיקת סימולציה מחזורית של ערכי שירותים (HRS/BAS) המופעלת ב-work delayable ומבצעת publish מחזורי.",
  "why_it_matters_he": "WSS לרוב בנוי סביב אירוע מדידה/פרסום; דפוס work-driven publish שימושי להכנה גם אם במימוש הסופי הטריגר יהיה חיישן אמיתי.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["api_call_sequence_analysis", "profile_similarity_inference"],
  "source_ids": ["nordic_ncs_sample_peripheral_hr_coded_main"],
  "evidence_refs": [
    {
      "source_id": "nordic_ncs_sample_peripheral_hr_coded_main",
      "what_identified_he": "notify_work_handler שמריץ hrs_notify + bas_notify ומבצע reschedule מחזורי.",
      "how_identified_he": "קריאת work delayable definition ו-handler body.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_hr_coded/src/main.c",
      "line_refs": ["35-40", "154-188"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "ב-WSS יש לאפשר מעבר מטריגר מחזורי לטריגר event-based (מדידה יציבה/סיום שקילה)."
  ]
}
```

```groupb_finding
{
  "id": "wss_logic_ccc_notify_and_update_api_pattern",
  "title_he": "דפוס CCC + update/notify API מתוך Zephyr BAS/HRS",
  "statement_he": "BAS/HRS ב-Zephyr ממחישים דפוס חשוב ל-WSS: callback שינוי CCC, פונקציית update/notify ציבורית, וטיפול פשוט ב-ENOTCONN במסלול ה-publish.",
  "why_it_matters_he": "WSS צפוי להזדקק ל-publish API ציבורי של measurement/feature updates עם gating על subscription ו-error normalization.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["ccc_handling_pattern", "notification_indication_enable_flow", "api_call_sequence_analysis"],
  "source_ids": ["zephyr_bt_bas_service_c", "zephyr_bt_hrs_service_c"],
  "evidence_refs": [
    {
      "source_id": "zephyr_bt_bas_service_c",
      "what_identified_he": "דפוס read+CCC+service define ו-API `bt_bas_set_battery_level()` עם notify.",
      "how_identified_he": "קריאת `BT_GATT_SERVICE_DEFINE(bas)` ו-`bt_bas_set_battery_level()`.",
      "artifact_ref": "zephyr/subsys/bluetooth/services/bas.c",
      "line_refs": ["30-38", "50-70", "83-96"],
      "confidence": "high"
    },
    {
      "source_id": "zephyr_bt_hrs_service_c",
      "what_identified_he": "דפוס notify API ציבורי ושינוי CCC callback נפרד.",
      "how_identified_he": "קריאת `hrmc_ccc_cfg_changed` ו-`bt_hrs_notify`.",
      "artifact_ref": "zephyr/subsys/bluetooth/services/hrs.c",
      "line_refs": ["58-73", "129-140"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לבנות `wss_publish_measurement()` כ-API שירות/לוגיקה ברור עם gating על subscription.",
    "להחזיק CCC state בנפרד ממדיניות יצירת המדידה."
  ]
}
```

```groupb_finding
{
  "id": "wss_logic_ti_weight_service_implies_service_callback_flow",
  "title_he": "ממשק TI Weight Service מרמז על flow לוגי מבוסס callbacks ושירות כיחידה עצמאית",
  "statement_he": "API של TI Weight Service (Add/Register/Set/Get + callbacks) מצביע על לוגיקה שבה השירות מטפל ב-GATT plumbing, והאפליקציה מספקת/צורכת אירועים דרך callbacks ו-parameters.",
  "why_it_matters_he": "זה תומך במודל לוגי שבו `wss_logic` נפרדת משכבת GATT serialization/state הפנימי של השירות.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["callback_registration_pattern", "vendor_sample_structure_pattern"],
  "source_ids": ["ti_weightservice_doxygen_h", "ti_weightservice_doxygen_c"],
  "evidence_refs": [
    {
      "source_id": "ti_weightservice_doxygen_h",
      "what_identified_he": "API שירות ציבורי + callback contracts ב-header.",
      "how_identified_he": "קריאת File Reference של weightservice.h.",
      "artifact_ref": "TI Doxygen: weightservice_8h.html",
      "line_refs": ["196-242", "254-340"],
      "confidence": "high"
    },
    {
      "source_id": "ti_weightservice_doxygen_c",
      "what_identified_he": "מימוש שירות self-contained עם callbacks פנימיים ו-attr table.",
      "how_identified_he": "קריאת File Reference של weightservice.c (member/function list).",
      "artifact_ref": "TI Doxygen: weightservice_8c.html",
      "line_refs": ["157-176"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להגדיר callback contract מצומצם שימנע coupling לאפליקציה הראשית.",
    "להשאיר Set/GetParameter רק עבור state/features של השירות, לא לוגיקת orchestration מלאה."
  ]
}
```

```groupb_finding
{
  "id": "wss_logic_phase1_subset_single_measurement_publish_flow",
  "title_he": "החלטת Phase 1 לוגית: מסלול publish יחיד למדידה עם gating על subscription",
  "statement_he": "לשלב ראשון של WSS מומלץ לממש מסלול publish יחיד של weight measurement עם gating על subscription/CCC, ולהשאיר מדיניות טריגר מתקדמת ושדות אופציונליים רבים לשלב 2.",
  "why_it_matters_he": "זה מאפשר לאמת early את מסלול המדידה והאינטגרציה מול GATT מבלי להסתבך מוקדם עם payload אופציונלי עשיר וטריגרים מורכבים.",
  "confidence": "medium",
  "status": "inferred",
  "derivation_method_ids": ["profile_similarity_inference", "api_call_sequence_analysis", "callback_registration_pattern"],
  "source_ids": ["sig_wss_spec_page", "nordic_ncs_sample_peripheral_hr_coded_main", "ti_weightservice_doxygen_h"],
  "evidence_refs": [
    {
      "source_id": "nordic_ncs_sample_peripheral_hr_coded_main",
      "what_identified_he": "דפוס publish מחזורי/work-driven שמתאים ל-Phase 1 גם לפני policy סופי.",
      "how_identified_he": "קריאת notify_work_handler וה-reschedule flow.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_hr_coded/src/main.c",
      "line_refs": ["154-188", "190-219"],
      "confidence": "high"
    },
    {
      "source_id": "ti_weightservice_doxygen_h",
      "what_identified_he": "API שירות מודולרי שמאפשר התחלה מ-flow בסיסי לפני הרחבת features.",
      "how_identified_he": "קריאת header Doxygen של Weight Service.",
      "artifact_ref": "TI Doxygen: weightservice_8h.html",
      "line_refs": ["196-242", "254-340"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לשלב 2: הרחבת trigger policy ושדות payload אופציונליים לפי החלטות spec-driven.",
    "להשאיר serializer מפוצל כאופציה אם payload phase 2 יגדל."
  ]
}
```

## תצפיות לפי מקור

```groupb_source_observation
{
  "id": "wss_logic_obs_hr_coded_periodic_publish",
  "profile_id": "WSS",
  "doc_kind": "logic",
  "source_id": "nordic_ncs_sample_peripheral_hr_coded_main",
  "what_identified_he": "דפוס סימולציה מחזורית ופרסום שירותים דרך work delayable.",
  "how_identified_he": "קריאת `notify_work_handler`, reschedule של work, וזרימות `hrs_notify`/`bas_notify`.",
  "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/peripheral_hr_coded/src/main.c",
  "line_refs": ["154-188", "190-219"],
  "confidence": "high",
  "notes_he": "משמש דפוס orchestration בלבד; semantics של WSS ייקבעו מול ה-spec."
}
```

```groupb_source_observation
{
  "id": "wss_logic_obs_zephyr_bas_update_notify",
  "profile_id": "WSS",
  "doc_kind": "logic",
  "source_id": "zephyr_bt_bas_service_c",
  "what_identified_he": "דפוס פונקציית set שמעדכנת state פנימי ומבצעת notify על characteristic ידוע.",
  "how_identified_he": "קריאת `bt_bas_set_battery_level` כולל ולידציה וטיפול ב-ENOTCONN.",
  "artifact_ref": "zephyr/subsys/bluetooth/services/bas.c",
  "line_refs": ["83-96"],
  "confidence": "high",
  "notes_he": "תומך בהפרדת update state מול publish path גם עבור WSS."
}
```

```groupb_source_observation
{
  "id": "wss_logic_obs_ti_weight_api_surface",
  "profile_id": "WSS",
  "doc_kind": "logic",
  "source_id": "ti_weightservice_doxygen_h",
  "what_identified_he": "ממשק שירות Weight עם Add/Register/Set/GetParameter + callback contracts.",
  "how_identified_he": "קריאת declarations ב-weightservice.h File Reference.",
  "artifact_ref": "TI Doxygen: weightservice_8h.html",
  "line_refs": ["196-242", "254-340"],
  "confidence": "high",
  "notes_he": "משמש לאימות שהלוגיקה צריכה להיות service-centric ולא רק אפליקטיבית."
}
```

```groupb_source_observation
{
  "id": "wss_logic_obs_sig_wss_page_scope",
  "profile_id": "WSS",
  "doc_kind": "logic",
  "source_id": "sig_wss_spec_page",
  "what_identified_he": "עמוד spec רשמי adopted (WSS 1.0.1) וארטיפקטי TS/ICS/TCRL זמינים לתיחום שלב ראשון.",
  "how_identified_he": "קריאת עמוד spec רשמי והצלבה עם inventory המסונכרן ב-Hub.",
  "artifact_ref": "Bluetooth SIG spec page + docs/profiles/WSS",
  "line_refs": ["spec page metadata", "hub spec inventory row"],
  "confidence": "high",
  "notes_he": "תצפית scope: משמשת לתכנון שלבים ולקישור למקורות המפרט, לא ל-flow לוגי מקוד."
}
```

## שיטות חילוץ/ניתוח

```groupb_method
{
  "id": "repo_text_presence_scan",
  "profile_id": "WSS",
  "doc_kind": "logic",
  "status": "used",
  "notes_he": "סריקה ממוקדת להכרעה אם יש מימוש WSS ישיר ב-NCS לפני שימוש בדפוסים דומים."
}
```

```groupb_method
{
  "id": "ti_doxygen_api_surface_read",
  "profile_id": "WSS",
  "doc_kind": "logic",
  "status": "used",
  "notes_he": "קריאת Doxygen של weightservice כדי לעגן את ה-flow השירותי ברמת API/callbacks."
}
```

## פערים ושאלות פתוחות

```groupb_open_question
{
  "id": "wss_logic_q1_measurement_trigger_policy",
  "profile_id": "WSS",
  "title_he": "מהו טריגר הפרסום במימוש היעד של WSS",
  "detail_he": "יש להכריע אם publish יתבצע מחזורית, על מדידה יציבה, או על event ייעודי (למשל יציאת משתמש מהמשקל), כדי לעצב נכון work queue/state machine.",
  "priority": "high",
  "status": "open",
  "source_ids": ["sig_wss_spec_page", "nordic_ncs_sample_peripheral_hr_coded_main"]
}
```

## השלכות למימוש

- להגדיר publish flow מבוסס work/event עם gating ברור על subscription.
- להפריד בין data acquisition / stabilization לבין BLE publish כדי לפשט בדיקות.
- לאמץ API שירות פנימי שמאפשר גם update feature/state וגם publish measurement בנפרד.

## מקורות

- `nordic_sdk_nrf_repo`
- `nordic_ncs_docs`
- `nordic_ncs_sample_peripheral_hr_coded_main`
- `zephyr_bt_bas_service_c`
- `zephyr_bt_hrs_service_c`
- `ti_weightservice_doxygen_h`
- `ti_weightservice_doxygen_c`
- `sig_wss_spec_page`
