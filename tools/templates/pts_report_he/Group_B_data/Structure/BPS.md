---
profile_id: BPS
display_name_he: שירות לחץ דם
doc_kind: structure
status: reviewed
updated_at: 2026-02-25
primary_sdk_source_policy: ti_official_only
secondary_pattern_sources_policy: local_or_official_only
language: he
schema_version: 1
---

## סיכום

מבנה היעד עבור BPS נגזר בעיקר ממודל השירותים של TI BLE5-Stack: מודול שירות ייעודי עם API קבוע (`AddService/Register/Set/GetParameter`), callback registration לאפליקציה, וטיפול פנימי ב-attribute table / CCC / read/write callbacks. דפוסי Zephyr/NCS משמשים כהשלמת מבנה בצד Zephyr (שירות סטטי + API wrapper + app glue), ולא כהעתקה ישירה של BPS.

## מבנה מוצע

- מודול שירות `bps_service` (UUIDs, attr table, CCC callbacks, read/write handlers, publish APIs).
- מודול `bps_logic` (policy, state gating, payload preparation orchestration).
- שכבת `bps_app_adapter` (חיבור לחיישן/זמן/threads/work queue ולאירועי מערכת).
- Header ציבורי מצומצם (`init/register/set/get/publish`) + internal header אופציונלי.
- state struct מפורש עם שדות CCC/feature flags/connection-related state.

## דפוסים שזוהו לפי מקור

```groupb_finding
{
  "id": "bps_structure_ti_bps_service_api_surface",
  "title_he": "TI BPS מגדיר מודול שירות ייעודי עם API קבוע בסגנון Add/Register/Set/Get",
  "statement_he": "ב-header של TI BPS מופיעים APIs ציבוריים להוספת השירות ל-GATT, רישום callbacks, ו-Set/GetParameter. זה מצביע על הפרדה ברורה בין שכבת השירות לשכבת האפליקציה.",
  "why_it_matters_he": "זה מגדיר baseline למבנה קבצים יציב: service module עם API קטן וקבוע במקום פיזור לוגיקה בקוד האפליקציה.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "callback_registration_pattern"],
  "source_ids": ["ti_blood_pressure_service_doxygen_h"],
  "evidence_refs": [
    {
      "source_id": "ti_blood_pressure_service_doxygen_h",
      "what_identified_he": "חתימות API ציבוריות (AddService/Register/SetParameter/GetParameter).",
      "how_identified_he": "קריאת File Reference של blood_pressure_service.h באזור declarations הציבוריים.",
      "artifact_ref": "TI Doxygen: blood_pressure_service_8h.html",
      "line_refs": ["638-728"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לאמץ API דומה גם אם שמות הפונקציות יותאמו לסגנון Zephyr/NCS.",
    "להימנע מחשיפת attribute table פנימי דרך ה-header הציבורי."
  ]
}
```

```groupb_finding
{
  "id": "bps_structure_ti_bps_callback_registration_contract",
  "title_he": "TI BPS משתמש ב-callback types ו-callback struct ייעודיים לשירות",
  "statement_he": "ה-header של TI BPS מתעד callback type(s) ו-struct לרישום callbacks של האפליקציה מול השירות, במקום תלות ישירה של השירות בלוגיקת האפליקציה.",
  "why_it_matters_he": "זה תומך במבנה testable ו-modular שבו שכבת השירות אינה מכירה את מקור המדידות או ה-state machine המלא.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["callback_registration_pattern", "vendor_sample_structure_pattern"],
  "source_ids": ["ti_blood_pressure_service_doxygen_h"],
  "evidence_refs": [
    {
      "source_id": "ti_blood_pressure_service_doxygen_h",
      "what_identified_he": "סוגי callback ו-struct callback registration ב-header.",
      "how_identified_he": "קריאת declarations ב-File Reference (callback type + callback table struct).",
      "artifact_ref": "TI Doxygen: blood_pressure_service_8h.html",
      "line_refs": ["235-315"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "במימוש היעד כדאי להגדיר callback table מינימלי (למשל control point write / subscription changed / error event)."
  ]
}
```

```groupb_finding
{
  "id": "bps_structure_ti_bps_attr_table_and_callbacks",
  "title_he": "קובץ ה-C של TI BPS מרכז attr table, read/write callbacks ו-conn status callback",
  "statement_he": "בדף File Reference של blood_pressure_service.c מופיעים symbols פנימיים אופייניים לשירות GATT מלא: attr table, read/write callbacks ו-conn status callback. זה מצביע על מבנה שירות self-contained.",
  "why_it_matters_he": "מבנה זה עוזר להחליט אילו אחריויות יישארו במודול השירות (GATT plumbing/CCC/attribute permissions) ואילו יעלו לשכבת הלוגיקה.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "api_call_sequence_analysis"],
  "source_ids": ["ti_blood_pressure_service_doxygen_c"],
  "evidence_refs": [
    {
      "source_id": "ti_blood_pressure_service_doxygen_c",
      "what_identified_he": "קיום symbols פנימיים bp_ReadAttrCB / bp_WriteAttrCB / bp_HandleConnStatusCB / bpAttrTbl[].",
      "how_identified_he": "קריאת member/function documentation ב-File Reference של blood_pressure_service.c.",
      "artifact_ref": "TI Doxygen: blood_pressure_service_8c.html",
      "line_refs": ["197-233"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לשמור attr table וה-callbacks הפנימיים בקובץ שירות אחד (או split פנימי בלבד), ולחשוף החוצה API צר.",
    "לשקול hook נפרד ל-connection status cleanup אם נשמר state פר-connection."
  ]
}
```

```groupb_finding
{
  "id": "bps_structure_multi_ccc_and_module_split_expectation",
  "title_he": "BPS דורש תכנון מבנה שמאפשר כמה CCCs וחלוקת אחריות בין service ל-logic",
  "statement_he": "שילוב הראיות מ-TI BPS (attr table + callbacks + service APIs) עם דפי TI על GATT/App architecture מצביע על צורך במודול שירות self-contained, אך עם state מפורט מספיק לכמה מסלולי publish ו-subscription states נפרדים.",
  "why_it_matters_he": "הנחה של state/CCC גלובלי יחיד תיצור חוב טכני ותסבך הוספת מאפיינים אופציונליים בהמשך.",
  "confidence": "medium",
  "status": "inferred",
  "derivation_method_ids": ["ccc_handling_pattern", "vendor_sample_structure_pattern", "profile_similarity_inference"],
  "source_ids": ["ti_blood_pressure_service_doxygen_c", "ti_gatt_services_profile_guide", "ti_ble5stack_application_arch_page", "sig_bps_spec_page"],
  "evidence_refs": [
    {
      "source_id": "ti_blood_pressure_service_doxygen_c",
      "what_identified_he": "מבנה שירות עשיר עם attr table ו-callbacks פנימיים.",
      "how_identified_he": "קריאת File Reference של blood_pressure_service.c ורשימת members/functions.",
      "artifact_ref": "TI Doxygen: blood_pressure_service_8c.html",
      "line_refs": ["167-233"],
      "confidence": "high"
    },
    {
      "source_id": "ti_gatt_services_profile_guide",
      "what_identified_he": "דפוס פרופיל/שירות עם API סטנדרטי והפרדה בין profile לבין application.",
      "how_identified_he": "קריאת GATT Services and Profile guide (Simple Profile API pattern).",
      "artifact_ref": "TI BLE5-Stack Guide: GATT Services and Profile",
      "line_refs": ["651-700"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להגדיר state struct שירות עם שדות CCC נפרדים לפי מאפיין רלוונטי.",
    "למקם orchestration ותזמון publish בשכבת logic/app adapter ולא בתוך handlers."
  ]
}
```

```groupb_finding
{
  "id": "bps_structure_phase1_subset_service_logic_split",
  "title_he": "החלטת Phase 1 מבנית: מודול שירות + לוגיקה בסיסית למדידה ראשית, ללא הרחבת feature set מלא",
  "statement_he": "לשלב ראשון מומלץ לבנות `bps_service` + `bps_logic` + `bps_app_adapter` עם תמיכה במסלול המדידה הראשית וה-CCC/gating הבסיסי, תוך דחיית הרחבות מודוליות למסלולי Control Point/Intermediate Cuff לשלב 2.",
  "why_it_matters_he": "זה מאפשר להקפיא גבולות מודולים ו-API מוקדם, בלי להתחייב לכל וריאציות ה-BPS כבר בגרסה הראשונה.",
  "confidence": "medium",
  "status": "inferred",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "profile_similarity_inference", "data_model_struct_mapping"],
  "source_ids": ["sig_bps_spec_page", "ti_blood_pressure_service_doxygen_c", "zephyr_bt_hrs_service_c"],
  "evidence_refs": [
    {
      "source_id": "ti_blood_pressure_service_doxygen_c",
      "what_identified_he": "שירות self-contained עם attr table/callbacks פנימיים מתאים לבסיס `bps_service`.",
      "how_identified_he": "קריאת File Reference של blood_pressure_service.c.",
      "artifact_ref": "TI Doxygen: blood_pressure_service_8c.html",
      "line_refs": ["167-233"],
      "confidence": "high"
    },
    {
      "source_id": "zephyr_bt_hrs_service_c",
      "what_identified_he": "תבנית Zephyr לשירות עם CCC callback + publish API ציבורי.",
      "how_identified_he": "קריאת hrs.c (service definition + notify API).",
      "artifact_ref": "zephyr/subsys/bluetooth/services/hrs.c",
      "line_refs": ["58-73", "82-95", "129-140"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להגדיר Phase 2 backlog מפורש למסלולי BPS שנדחו, כדי למנוע זליגה לא מתוכננת ל-Phase 1.",
    "לעדכן readiness gate ברגע שמחליטים רשמית על subset בתיעוד/סקירה."
  ]
}
```

## תצפיות לפי מקור

```groupb_source_observation
{
  "id": "bps_structure_obs_ti_bps_header_contract",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "source_id": "ti_blood_pressure_service_doxygen_h",
  "what_identified_he": "חוזה מודול שירות ציבורי + callback registration types/struct.",
  "how_identified_he": "קריאת declarations וה-type definitions ב-File Reference של header השירות.",
  "artifact_ref": "TI Doxygen: blood_pressure_service_8h.html",
  "line_refs": ["235-315", "638-728"],
  "confidence": "high",
  "notes_he": "זהו המקור העיקרי לקביעת גבולות ה-API הציבורי של מודול השירות."
}
```

```groupb_source_observation
{
  "id": "bps_structure_obs_ti_bps_c_internal_gatt_plumbing",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "source_id": "ti_blood_pressure_service_doxygen_c",
  "what_identified_he": "ריכוז attr table ו-read/write/conn-status callbacks בתוך מודול שירות self-contained.",
  "how_identified_he": "קריאת function/member list ב-File Reference של קובץ ה-C.",
  "artifact_ref": "TI Doxygen: blood_pressure_service_8c.html",
  "line_refs": ["167-233"],
  "confidence": "high",
  "notes_he": "תומך בהחלטה להשאיר GATT plumbing במודול service ולא בשכבת האפליקציה."
}
```

```groupb_source_observation
{
  "id": "bps_structure_obs_ti_guides_app_vs_service_split",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "source_id": "ti_ble5stack_application_arch_page",
  "what_identified_he": "דפוס הפרדה בין App Task/Event Queue לבין קוד profile/service.",
  "how_identified_he": "קריאת The Application + GATT Services/Profile guide לזיהוי חלוקת אחריות קונספטואלית.",
  "artifact_ref": "TI BLE5-Stack User Guide + GATT Services/Profile",
  "line_refs": ["the-application: 470-580, 611-631", "gatt-profile: 651-700"],
  "confidence": "high",
  "notes_he": "לא מעתיקים ארכיטקטורת TI 1:1, אלא מאמצים את עקרון ההפרדה."
}
```

```groupb_source_observation
{
  "id": "bps_structure_obs_sig_bps_page_scope",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "source_id": "sig_bps_spec_page",
  "what_identified_he": "עמוד spec רשמי וארטיפקטים (Spec/TS/ICS/TCRL) שמאפשרים לתחום את תכולת Phase 1 ברמת מודולים.",
  "how_identified_he": "קריאת עמוד spec רשמי והצלבה עם inventory המסונכרן ב-Hub עבור BPS.",
  "artifact_ref": "Bluetooth SIG spec page + docs/profiles/BPS",
  "line_refs": ["spec page metadata", "hub spec inventory row"],
  "confidence": "high",
  "notes_he": "משמש לתיחום scope והחלטות build-up של מודולים, לא למבנה API קונקרטי מתוך קוד."
}
```

## שיטות חילוץ/ניתוח

```groupb_method
{
  "id": "ti_doxygen_api_surface_read",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "status": "used",
  "notes_he": "קריאת Doxygen File Reference (header/c) לזיהוי מבנה מודול השירות, callbacks ו-attr table."
}
```

```groupb_method
{
  "id": "ti_guide_architecture_pattern_read",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "status": "used",
  "notes_he": "קריאת דפי TI User Guide (The Application / GATT Services and Profile / Custom App) להסקת חלוקת אחריות בין App Task לשירותים."
}
```

## פערים ושאלות פתוחות

```groupb_open_question
{
  "id": "bps_structure_q1_initial_feature_subset",
  "profile_id": "BPS",
  "title_he": "מהו subset ראשוני של BPS לשלב ראשון",
  "detail_he": "יש להחליט אילו characteristics/flows ייכנסו לשלב ראשון (Measurement בלבד / גם Intermediate Cuff / גם Control Point), כי זה משנה את מבנה state וה-CCCs במודול השירות.",
  "priority": "high",
  "status": "resolved",
  "source_ids": [
    "sig_bps_spec_page",
    "ti_blood_pressure_service_doxygen_c"
  ]
}
```

```groupb_open_question
{
  "id": "bps_structure_q2_service_vs_serializer_split",
  "profile_id": "BPS",
  "title_he": "האם להפריד serializer של BPS ליחידת קוד נפרדת",
  "detail_he": "אם payload של BPS מורכב (flags/optional fields), ייתכן שכדאי להפריד serialization/helpers מתוך service.c כדי לשמור קריאות ו-testability.",
  "priority": "medium",
  "status": "deferred_phase2",
  "source_ids": [
    "ti_blood_pressure_service_doxygen_c",
    "zephyr_bt_hrs_service_c"
  ]
}
```

## השלכות למימוש

- לבנות `bps_service.c/.h` כמודול self-contained ל-GATT plumbing (attributes/CCCs/read-write callbacks).
- להגדיר callback registration ברור לשכבת לוגיקה/אפליקציה במקום תלות ישירה בחיישן או scheduler.
- להכין state struct שמסוגל לנהל כמה CCCs ו-capability flags בנפרד.
- לשקול פיצול serializer/helpers כדי למנוע `service.c` גדול מדי.

## החלטות Phase 1

```groupb_decision
{
  "id": "bps_structure_phase1_subset_and_serializer_decision",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "phase": "phase1",
  "title_he": "Phase 1: subset מצומצם + serializer helper פנימי (לא מודול נפרד)",
  "decision_he": "בשלב ראשון ייכנסו characteristic המדידה המרכזית ו-feature read, בעוד מסלולים אופציונליים יידחו. serializer ימומש כפונקציות עזר פנימיות בשירות/לוגיקה ולא כמודול נפרד.",
  "rationale_he": "סוגר את שתי השאלות הפתוחות (subset + split) בלי להעמיס מבנה מוקדם מדי.",
  "status": "decided",
  "confidence": "high",
  "derivation_method_ids": [
    "vendor_sample_structure_pattern",
    "profile_similarity_inference"
  ],
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_blood_pressure_service_doxygen_h",
    "ti_blood_pressure_service_doxygen_c"
  ],
  "impacts_he": [
    "מצמצם surface area למימוש Phase 1",
    "דוחה פיצול serializer לשלב 2 אם יידרש לפי מורכבות payload"
  ],
  "applies_to_checks": [
    "phase1_subset_decided",
    "implementation_contract_defined"
  ]
}
```

## חוזה מימוש (Implementation Contract)

```groupb_impl_contract
{
  "id": "bps_phase1_impl_contract",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "phase": "phase1",
  "scope_in": [
    "BPS: service module בסיסי עם attribute/CCC handling",
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
      "bps_service_init/register_callbacks",
      "bps_service_publish_or_update (לפי semantics של הפרופיל)",
      "bps_service_set_feature_or_config (אם רלוונטי)"
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
      "bps_service",
      "bps_logic",
      "bps_app_adapter"
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
  "summary_he": "חוזה מימוש Phase 1 ל-BPS: service+logic+adapter עם CCC gating, API פנימי ברור ותחום אחריות מודולרי.",
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_blood_pressure_service_doxygen_h",
    "ti_blood_pressure_service_doxygen_c",
    "ti_ble5stack_application_arch_page",
    "ti_ble5stack_custom_app_guide"
  ]
}
```

## יעדי בדיקות Phase 1

```groupb_test_target
{
  "id": "bps_phase1_test_targets",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "phase": "phase1",
  "manual_smoke_checks": [
    "BPS: init/register ללא crash ועם logs צפויים",
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
  "summary_he": "יעדי בדיקות Phase 1 ל-BPS: smoke ידני + מיקוד ב-GATT/CCC/runtime flow לפני הרחבת כיסוי.",
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_blood_pressure_service_doxygen_h",
    "ti_blood_pressure_service_doxygen_c"
  ]
}
```

## חתימת Review / מוכנות

```groupb_review_signoff
{
  "id": "bps_phase1_review_signoff",
  "profile_id": "BPS",
  "doc_kind": "structure",
  "logic_reviewed": true,
  "structure_reviewed": true,
  "logic_reviewed_at": "2026-02-25",
  "structure_reviewed_at": "2026-02-25",
  "review_summary_he": "בוצע review הנדסי ל-Logic/Structure של BPS, נסגרו החלטות Phase 1 ונוסח חוזה מימוש + יעדי בדיקות.",
  "reviewer_notes_he": [
    "החלטות Phase 1 סומנו מפורשות ומקושרות למקורות.",
    "פריטים שנדחו ל-Phase 2 אינם חוסמים bring-up ומימוש בסיסי.",
    "נדרש בשלב הבא לעבור לכתיבת קוד לפי חוזה המימוש המוגדר."
  ],
  "remaining_phase1_blockers": [],
  "ready_for_impl_phase1": true,
  "ready_decision_reason_he": "BPS עומד בקריטריוני מוכנות Phase 1: review מלא, חוזה מימוש מוגדר, יעדי בדיקות מוגדרים, ללא blockers פתוחים.",
  "source_ids": [
    "ti_simplelink_sdk",
    "ti_ble5stack_docs_root",
    "ti_blood_pressure_service_doxygen_h",
    "ti_blood_pressure_service_doxygen_c"
  ]
}
```

## מקורות

- `ti_simplelink_sdk`
- `ti_ble5stack_docs_root`
- `ti_blood_pressure_service_doxygen_h`
- `ti_blood_pressure_service_doxygen_c`
- `ti_ble5stack_application_arch_page`
- `ti_ble5stack_custom_app_guide`
- `ti_gatt_services_profile_guide`
- `zephyr_bt_hrs_service_c`
- `sig_bps_spec_page`
