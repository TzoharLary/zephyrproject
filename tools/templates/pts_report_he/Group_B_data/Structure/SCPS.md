---
profile_id: SCPS
display_name_he: שירות פרמטרי סריקה
doc_kind: structure
status: reviewed
updated_at: 2026-02-25
primary_sdk_source_policy: ti_official_only
secondary_pattern_sources_policy: local_or_official_only
language: he
schema_version: 1
---

## סיכום

מבנה SCPS המוצע מבוסס על מודול `scanparamservice` של TI (שירות GATT ייעודי עם attr table, callbacks ו-RefreshNotify) ועל דפוסי NCS המפרידים בין scan runtime APIs לבין שירות GATT. המבנה המומלץ: service module ל-GATT + scan policy/adapter בשכבת אפליקציה.

## מבנה מוצע

- `scps_service.c/.h`: הגדרת UUIDs/attributes/read-write handlers/CCCs/refresh API.
- `scps_scan_policy.c/.h`: state של scan interval/window ותרגום ל-`bt_le_scan_param`.
- `scps_app_adapter.c`: אינטגרציה עם stack callbacks/work queue/scan control.
- `scps_internal.h` (אופציונלי): helper structs/validation/serialization קטנים.
- state struct פר-connection עבור subscription/pending refresh (אם נדרש).

## דפוסים שזוהו לפי מקור

```groupb_finding
{
  "id": "scps_structure_ti_scanparamservice_module_contract",
  "title_he": "TI scanparamservice מציג חוזה מודול שירות מלא כולל RefreshNotify",
  "statement_he": "ב-scanparamservice.h מופיעים AddService/Register/Set/GetParameter וגם ScanParam_RefreshNotify, מה שמצביע על מודול שירות עצמאי עם API נפרד למסלולי write/read ולמסלול refresh notify.",
  "why_it_matters_he": "מכוון למבנה שירות SCPS שבו refresh event אינו side effect סתמי של write, אלא API מפורש.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "callback_registration_pattern"],
  "source_ids": ["ti_scanparamservice_doxygen_h"],
  "evidence_refs": [
    {
      "source_id": "ti_scanparamservice_doxygen_h",
      "what_identified_he": "API ציבורי מלא כולל ScanParam_RefreshNotify.",
      "how_identified_he": "קריאת declarations ב-scanparamservice.h File Reference.",
      "artifact_ref": "TI Doxygen: scanparamservice_8h.html",
      "line_refs": ["216-224", "243-322"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לשמור API מפורש ל-refresh path ולא להחביא אותו בתוך write handler.",
    "להתייחס ל-refresh כזרימה עצמאית במודול השירות."
  ]
}
```

```groupb_finding
{
  "id": "scps_structure_ti_scanparamservice_attr_and_conn_status_callbacks",
  "title_he": "scanparamservice.c מרכז attr table, read/write handlers ו-conn status callback",
  "statement_he": "ב-File Reference של scanparamservice.c מופיעים scanParam_ReadAttrCB, scanParam_WriteAttrCB, scanParam_HandleConnStatusCB ו-scanParamServiceAttrTbl. זהו דפוס שירות GATT self-contained עם טיפול ב-state מחובר/מנותק.",
  "why_it_matters_he": "ב-SCPS זה חשוב במיוחד כי state של CCC/refresh/subscription עשוי להיות תלוי connection.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "ccc_handling_pattern"],
  "source_ids": ["ti_scanparamservice_doxygen_c"],
  "evidence_refs": [
    {
      "source_id": "ti_scanparamservice_doxygen_c",
      "what_identified_he": "read/write callbacks פנימיות + attr table של השירות + conn status hook.",
      "how_identified_he": "קריאת function/member list ב-scanparamservice.c File Reference.",
      "artifact_ref": "TI Doxygen: scanparamservice_8c.html",
      "line_refs": ["139-169"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לשמור cleanup/reset מסודר של state פר-connection במסלול disconnect.",
    "להימנע מקריאות scan runtime ישירות מתוך write callback."
  ]
}
```

```groupb_finding
{
  "id": "scps_structure_ncs_split_between_gatt_service_and_scan_runtime",
  "title_he": "ב-NCS דפוס סביר ל-SCPS הוא פיצול בין שכבת שירות GATT לשכבת scan runtime",
  "statement_he": "הדוגמה shorter_conn_intervals מדגימה מצד אחד custom GATT service סטטי, ומצד שני scan_init/scan callbacks/filters. השילוב תומך במבנה מפוצל: service module מעדכן state, ו-app adapter מפעיל scan APIs.",
  "why_it_matters_he": "מונע coupling בין write handlers של GATT לבין קריאות scan runtime שעלולות להיות תלויות הקשר/תזמון.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "api_call_sequence_analysis"],
  "source_ids": ["nordic_ncs_sample_shorter_conn_intervals_main"],
  "evidence_refs": [
    {
      "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
      "what_identified_he": "custom GATT service סטטי (read handler + BT_GATT_SERVICE_DEFINE).",
      "how_identified_he": "קריאת read_min_interval והגדרת service סטטי בקובץ הדוגמה.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
      "line_refs": ["86-99"],
      "confidence": "high"
    },
    {
      "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
      "what_identified_he": "scan runtime מוגדר ומנוהל דרך scan_init ו-callbacks נפרדים.",
      "how_identified_he": "קריאת scan callbacks + scan_init + filter add/enable.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
      "line_refs": ["130-182"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להפריד write validation/serialization ב-service מהפעלה בפועל של scan policy/runtime."
  ]
}
```

```groupb_finding
{
  "id": "scps_structure_zephyr_service_patterns_for_ccc_and_update_api",
  "title_he": "דפוסי Zephyr BAS/HRS משלימים את מבנה ה-service API בצד Zephyr",
  "statement_he": "BAS/HRS מספקים דפוסי service API ציבורי + CCC callbacks + notify path ב-Zephyr, שניתן להתאים ל-SCPS עבור read/write + refresh publish path.",
  "why_it_matters_he": "מספקים תבנית native ל-Zephyr עבור מימוש ה-service module, בנוסף למודל TI.",
  "confidence": "medium",
  "status": "confirmed",
  "derivation_method_ids": ["profile_similarity_inference", "ccc_handling_pattern"],
  "source_ids": ["zephyr_bt_bas_service_c", "zephyr_bt_hrs_service_c"],
  "evidence_refs": [
    {
      "source_id": "zephyr_bt_bas_service_c",
      "what_identified_he": "שירות סטטי עם API עדכון ערך ו-notify path.",
      "how_identified_he": "קריאת bas.c (BT_GATT_SERVICE_DEFINE + bt_bas_set_battery_level).",
      "artifact_ref": "zephyr/subsys/bluetooth/services/bas.c",
      "line_refs": ["50-70", "83-96"],
      "confidence": "high"
    },
    {
      "source_id": "zephyr_bt_hrs_service_c",
      "what_identified_he": "CCC callback נפרד ו-API notify ציבורי.",
      "how_identified_he": "קריאת hrs.c (CCC callback + bt_hrs_notify).",
      "artifact_ref": "zephyr/subsys/bluetooth/services/hrs.c",
      "line_refs": ["58-73", "129-140"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להשתמש בדפוס TI לקביעת חלוקת אחריות, ובדפוס Zephyr ליישום ה-GATT glue בפועל.",
    "להימנע מהסקת semantics של SCPS ישירות מ-HRS/BAS; הם רק דפוס מבני/תשתיתי."
  ]
}
```

```groupb_finding
{
  "id": "scps_structure_phase1_subset_service_and_scan_policy_split",
  "title_he": "החלטת Phase 1 מבנית: `scps_service` + `scps_scan_policy/app_adapter`, ללא הרחבת runtime policy מלאה",
  "statement_he": "לשלב ראשון מומלץ להקפיא מבנה מפוצל: `scps_service` עבור GATT plumbing ו-`scps_scan_policy`/`scps_app_adapter` עבור runtime integration בסיסי, תוך דחיית אופטימיזציות ומדיניות scan מתקדמת לשלב 2.",
  "why_it_matters_he": "החלטה זו משמרת separation of concerns קריטי ל-SCPS ומקטינה coupling מוקדם בין write handlers ל-scan runtime.",
  "confidence": "medium",
  "status": "inferred",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "api_call_sequence_analysis", "profile_similarity_inference"],
  "source_ids": ["sig_scps_spec_page", "ti_scanparamservice_doxygen_c", "nordic_ncs_sample_shorter_conn_intervals_main"],
  "evidence_refs": [
    {
      "source_id": "ti_scanparamservice_doxygen_c",
      "what_identified_he": "GATT plumbing פנימי מלא + conn status callback במודול שירות.",
      "how_identified_he": "קריאת File Reference של scanparamservice.c.",
      "artifact_ref": "TI Doxygen: scanparamservice_8c.html",
      "line_refs": ["139-169"],
      "confidence": "high"
    },
    {
      "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
      "what_identified_he": "פיצול טבעי בין service GATT לבין scan runtime callbacks/init.",
      "how_identified_he": "קריאת service definition מול scan_init/callbacks.",
      "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
      "line_refs": ["86-99", "130-182"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לשמור Phase 1 scan runtime minimal ולהרחיב policy בשלב 2 בלי לשבור API של `scps_service`.",
    "לרכז cleanup פר-connection כבר בשלב 1 במודול השירות."
  ]
}
```

## תצפיות לפי מקור

```groupb_source_observation
{
  "id": "scps_structure_obs_ti_scanparam_header_contract",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "source_id": "ti_scanparamservice_doxygen_h",
  "what_identified_he": "API ציבורי מלא לשירות כולל RefreshNotify, Set/Get ו-Register callbacks.",
  "how_identified_he": "קריאת declarations ב-header File Reference.",
  "artifact_ref": "TI Doxygen: scanparamservice_8h.html",
  "line_refs": ["216-224", "243-322"],
  "confidence": "high",
  "notes_he": "המקור העיקרי לגבולות interface של `scps_service.h`."
}
```

```groupb_source_observation
{
  "id": "scps_structure_obs_ti_scanparam_c_gatt_plumbing",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "source_id": "ti_scanparamservice_doxygen_c",
  "what_identified_he": "GATT plumbing פנימי מלא (attr table, read/write callbacks, conn status callback).",
  "how_identified_he": "קריאת function/member list ב-File Reference של scanparamservice.c.",
  "artifact_ref": "TI Doxygen: scanparamservice_8c.html",
  "line_refs": ["139-169"],
  "confidence": "high",
  "notes_he": "תומך בשירות self-contained עם cleanup פר-connection."
}
```

```groupb_source_observation
{
  "id": "scps_structure_obs_ncs_shorter_conn_intervals_split",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "source_id": "nordic_ncs_sample_shorter_conn_intervals_main",
  "what_identified_he": "הפרדה בין custom GATT service סטטי לבין scan runtime callbacks/init.",
  "how_identified_he": "קריאת שני אזורי קוד נפרדים באותה דוגמה: service definition מול scan callbacks/init.",
  "artifact_ref": ".cache/vendor_src/sdk-nrf/samples/bluetooth/shorter_conn_intervals/src/main.c",
  "line_refs": ["86-99", "130-182"],
  "confidence": "high",
  "notes_he": "זהו דפוס מבני טוב ל-target Zephyr/NCS גם אם לא דוגמת SCPS רשמית."
}
```

```groupb_source_observation
{
  "id": "scps_structure_obs_sig_scps_page_scope",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "source_id": "sig_scps_spec_page",
  "what_identified_he": "עמוד spec רשמי SCPS וארטיפקטי בדיקות שמאפשרים לתחום את גבולות Phase 1 ברמת service/runtime split.",
  "how_identified_he": "קריאת עמוד spec רשמי והצלבה עם inventory המסונכרן ב-Hub עבור SCPS.",
  "artifact_ref": "Bluetooth SIG spec page + docs/profiles/SCPS",
  "line_refs": ["spec page metadata", "hub spec inventory row"],
  "confidence": "high",
  "notes_he": "משמש כעוגן scope לשלבי מימוש, בנוסף למקורות TI/NCS המבניים."
}
```

## שיטות חילוץ/ניתוח

```groupb_method
{
  "id": "ti_doxygen_api_surface_read",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "status": "used",
  "notes_he": "קריאת Doxygen של scanparamservice כדי לחלץ חוזה מודול וארגון attr/callbacks."
}
```

```groupb_method
{
  "id": "local_pattern_mapping",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "status": "used",
  "notes_he": "מיפוי דפוסי shorter_conn_intervals + Zephyr services למבנה SCPS ב-target Zephyr/NCS."
}
```

## פערים ושאלות פתוחות

```groupb_open_question
{
  "id": "scps_structure_q1_conn_status_cleanup_scope",
  "profile_id": "SCPS",
  "title_he": "איזה state פר-connection צריך cleanup ב-disconnect",
  "detail_he": "קיום conn status callback ב-TI מרמז על cleanup/state reset. צריך להחליט אילו שדות subscription/refresh/pending updates נשמרים פר-connection במימוש היעד.",
  "priority": "medium",
  "status": "resolved",
  "source_ids": [
    "ti_scanparamservice_doxygen_c"
  ]
}
```

## השלכות למימוש

- לפצל SCPS ל-`service` (GATT plumbing) ו-`scan_policy/app_adapter` (runtime scan control).
- להגדיר API מפורש ל-`RefreshNotify` ולשמור אותו נפרד ממסלול write של Scan Interval Window.
- להחזיק state פר-connection עבור subscription/pending refresh אם נדרש לפי ההתנהגות שתיקבע.

## החלטות Phase 1

```groupb_decision
{
  "id": "scps_structure_phase1_conn_cleanup_scope_decision",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "phase": "phase1",
  "title_he": "Phase 1: cleanup ממוקד חיבור/CCC/state, ללא session-history",
  "decision_he": "ב-Phase 1 cleanup יתמקד באיפוס state חיבור, פרמטרים זמניים ו-CCC/refresh flags. לא יתווסף מנגנון session-history או persistence.",
  "rationale_he": "מספיק ליציבות runtime ולבדיקות, בלי להעמיס state management מתקדם שאינו נדרש לשלב ראשון.",
  "status": "decided",
  "confidence": "high",
  "derivation_method_ids": [
    "state_machine_flow_read",
    "vendor_sample_structure_pattern"
  ],
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_scanparamservice_doxygen_h",
    "ti_scanparamservice_doxygen_c"
  ],
  "impacts_he": [
    "מבהיר scope cleanup לשכבת service/adapter",
    "מונע חסימה על תכנון persistence מוקדם"
  ],
  "applies_to_checks": [
    "implementation_contract_defined",
    "phase1_blockers_closed_or_deferred"
  ]
}
```

## חוזה מימוש (Implementation Contract)

```groupb_impl_contract
{
  "id": "scps_phase1_impl_contract",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "phase": "phase1",
  "scope_in": [
    "ScPS: service module בסיסי עם attribute/CCC handling",
    "API פנימי ל-init/register callbacks/publish או update",
    "חיבור app adapter מינימלי לבדיקות bring-up",
    "לוגיקה בסיסית ל-gating ול-flow runtime עיקרי"
  ],
  "scope_out": [
    "אופטימיזציות performance או buffering מתקדם",
    "פיצולי מודולים נוספים שאינם נדרשים ל-Phase 1",
    "יכולות אופציונליות שסומנו ל-Phase 2 במסמכי הפרופיל"
  ],
  "service_api_contract": {
    "public_functions_he": [
      "scps_service_init/register_callbacks",
      "scps_service_publish_or_update (לפי semantics של הפרופיל)",
      "scps_service_set_feature_or_config (אם רלוונטי)"
    ],
    "callback_contract_he": "callbacks נרשמים ע\"י שכבת adapter/app; אין תלות ישירה בחיישן מתוך service module.",
    "notes_he": "שמות פונקציות סופיים ייקבעו במימוש, אך החוזה המבני נשמר."
  },
  "runtime_flow_contract": {
    "steps_he": [
      "init service + register callbacks",
      "adapter מספק events/data ללוגיקה",
      "לוגיקה מבצעת validation/gating",
      "service בונה/שולח payload לפי כללי CCC והפרופיל",
      "כשלי שליחה נרשמים ומוחזרים לשכבה מעל"
    ]
  },
  "data_model_contract": {
    "items_he": [
      "state לשירות (subscriptions/flags/capabilities)",
      "מבנה מדידה/פרמטרים לוגי נפרד מ-BLE serialization",
      "metadata מינימלי ל-debug/last publish result"
    ]
  },
  "ccc_and_notify_indicate_contract": {
    "rules_he": [
      "אין שליחה ללא enable מתאים ב-CCC",
      "בחירת notify/indicate נשלטת בשכבת service לפי characteristic requirements",
      "שכבת לוגיקה נשארת transport-agnostic ככל האפשר"
    ]
  },
  "error_policy_contract": {
    "rules_he": [
      "service מחזיר status/error code לשכבה מעל",
      "אין retry blocking בתוך callback של GATT",
      "logging ברור עבור validation failure ו-send failure"
    ]
  },
  "dependency_contract": {
    "items_he": [
      "תלות ב-Zephyr Bluetooth/GATT APIs",
      "adapter/app מספק מקור נתונים/אירועים",
      "אין תלות חובה ב-persistence ב-Phase 1"
    ]
  },
  "module_boundaries": {
    "modules_he": [
      "scps_service",
      "scps_logic",
      "scps_app_adapter"
    ],
    "boundaries_he": [
      "service אחראי על GATT plumbing ו-CCC",
      "logic אחראי על policy/gating/flow",
      "adapter אחראי על חיבור לאפליקציה/stack events"
    ]
  },
  "implementation_order": [
    "service skeleton + UUID/attributes/CCCs",
    "callback contract + app adapter hooks",
    "logic gating + publish/update path",
    "feature/config read-write path (אם רלוונטי)",
    "logging + smoke validation"
  ],
  "blocking_assumptions": [],
  "non_blocking_deferred": [
    "refactor לפיצול helper/serializer אם יגדל complexity",
    "הרחבת capabilities אופציונליות ל-Phase 2"
  ],
  "summary_he": "חוזה מימוש Phase 1 ל-ScPS: service+logic+adapter עם CCC gating, API פנימי ברור ותחום אחריות מודולרי.",
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_scanparamservice_doxygen_h",
    "ti_scanparamservice_doxygen_c",
    "nordic_ncs_sample_shorter_conn_intervals_main",
    "zephyr_bt_bas_service_c"
  ]
}
```

## יעדי בדיקות Phase 1

```groupb_test_target
{
  "id": "scps_phase1_test_targets",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "phase": "phase1",
  "manual_smoke_checks": [
    "ScPS: init/register ללא crash ועם logs צפויים",
    "שינוי/הזנת נתון דרך adapter -> publish/update path מופעל",
    "gating לפי CCC/enable חוסם שליחה לא מורשית",
    "כשל שליחה מחזיר סטטוס ונרשם בלוג"
  ],
  "pts_autopts_target_areas": [
    "GATT behavior בסיסי של characteristics/CCCs בפרופיל",
    "publish/indicate/notify gating לפי enable",
    "flow תקין של read/write/callbacks רלוונטיים ל-Phase 1"
  ],
  "ics_ixit_assumptions": [
    "ICS/IXIT יוגדרו בהתאם ל-subset Phase 1 בלבד",
    "יכולות אופציונליות שלא מומשו יסומנו כלא נתמכות",
    "נדרש מיפוי PIXIT/behavior לפני הרצת PTS מלאה"
  ],
  "phase1_done_criteria": [
    "build + smoke app runtime תקין",
    "manual smoke checks עוברים",
    "אין JS/data regression ב-Hub after docs update",
    "יעדי PTS/AutoPTS ל-Phase 1 מזוהים וממופים"
  ],
  "known_non_goals": [
    "כיסוי מלא של כל feature אופציונלי בפרופיל",
    "אופטימיזציה/cleanup מתקדם שאינו חוסם פונקציונליות"
  ],
  "summary_he": "יעדי בדיקות Phase 1 ל-ScPS: smoke ידני + מיקוד ב-GATT/CCC/runtime flow לפני הרחבת כיסוי.",
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_scanparamservice_doxygen_h",
    "ti_scanparamservice_doxygen_c"
  ]
}
```

## חתימת Review / מוכנות

```groupb_review_signoff
{
  "id": "scps_phase1_review_signoff",
  "profile_id": "SCPS",
  "doc_kind": "structure",
  "logic_reviewed": true,
  "structure_reviewed": true,
  "logic_reviewed_at": "2026-02-25",
  "structure_reviewed_at": "2026-02-25",
  "review_summary_he": "בוצע review הנדסי ל-Logic/Structure של ScPS, נסגרו החלטות Phase 1 ונוסח חוזה מימוש + יעדי בדיקות.",
  "reviewer_notes_he": [
    "החלטות Phase 1 סומנו מפורשות ומקושרות למקורות.",
    "פריטים שנדחו ל-Phase 2 אינם חוסמים bring-up ומימוש בסיסי.",
    "נדרש בשלב הבא לעבור לכתיבת קוד לפי חוזה המימוש המוגדר."
  ],
  "remaining_phase1_blockers": [],
  "ready_for_impl_phase1": true,
  "ready_decision_reason_he": "ScPS עומד בקריטריוני מוכנות Phase 1: review מלא, חוזה מימוש מוגדר, יעדי בדיקות מוגדרים, ללא blockers פתוחים.",
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_scanparamservice_doxygen_h",
    "ti_scanparamservice_doxygen_c"
  ]
}
```

## מקורות

- `ti_simplelink_sdk`
- `ti_ble5stack_docs_root`
- `ti_scanparamservice_doxygen_h`
- `ti_scanparamservice_doxygen_c`
- `nordic_ncs_sample_shorter_conn_intervals_main`
- `zephyr_bt_bas_service_c`
- `zephyr_bt_hrs_service_c`
- `sig_scps_spec_page`
