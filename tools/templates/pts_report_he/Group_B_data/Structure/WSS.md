---
profile_id: WSS
display_name_he: שירות משקל
doc_kind: structure
status: in_progress
updated_at: 2026-02-24
primary_sdk_source_policy: ti_official_only
secondary_pattern_sources_policy: local_or_official_only
language: he
schema_version: 1
---

## סיכום

מבנה WSS המוצע מבוסס על TI Weight Service כ-service module ייעודי עם API קבוע ו-callback registration, ובצד Zephyr/NCS על דפוסי שירותים סטטיים (BAS/HRS) והפרדת app glue. המטרה היא לארגן מראש מודול שירות, מודול לוגיקה, וממשק אפליקטיבי נקי שמתאים ל-target של Zephyr/NCS.

## מבנה מוצע

- `wss_service.c/.h`: UUIDs, attributes, CCCs, read/write handlers, publish APIs.
- `wss_logic.c/.h`: policy של מדידה/ייצוב/flags/זמן.
- `wss_serializer.c/.h` (אופציונלי): packing של measurement payload.
- `wss_app_adapter.c`: חיבור scheduler/work queue/חיישן למודול הלוגיקה/שירות.
- state struct לשירות (subscription/capabilities/last measurement metadata).

## דפוסים שזוהו לפי מקור

```groupb_finding
{
  "id": "wss_structure_ti_weight_module_contract",
  "title_he": "TI Weight Service מספק חוזה מודולרי סטנדרטי (Add/Register/Set/Get)",
  "statement_he": "ב-weightservice.h מופיעים APIs ציבוריים אופייניים לשירות BLE ייעודי: AddService, Register callbacks, SetParameter ו-GetParameter.",
  "why_it_matters_he": "מגדיר baseline למבנה מודול שירות נפרד עם API יציב, במקום תלות ישירה של האפליקציה ב-attribute table.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "callback_registration_pattern"],
  "source_ids": ["ti_weightservice_doxygen_h"],
  "evidence_refs": [
    {
      "source_id": "ti_weightservice_doxygen_h",
      "what_identified_he": "הצהרות API ציבוריות ורכיבי callback contract של Weight Service.",
      "how_identified_he": "קריאת File Reference של weightservice.h.",
      "artifact_ref": "TI Doxygen: weightservice_8h.html",
      "line_refs": ["196-242", "254-340"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "לשמור header ציבורי צר וברור.",
    "להעביר כל GATT plumbing פנימי לקובץ ה-service."
  ]
}
```

```groupb_finding
{
  "id": "wss_structure_ti_weight_attr_table_callbacks",
  "title_he": "קובץ weightservice.c מרכז attr table ו-read/write callbacks",
  "statement_he": "File Reference של weightservice.c מציג symbols פנימיים (weightServiceAttrTbl, weight_ReadAttrCB, weight_WriteAttrCB, callback pointer storage) המעידים על מודול שירות self-contained עם GATT plumbing פנימי.",
  "why_it_matters_he": "מסמן מה צריך להישאר ב-`wss_service.c` ולא לעלות ל-`wss_logic.c`: permissions, attr table, handlers, CCC state.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "data_model_struct_mapping"],
  "source_ids": ["ti_weightservice_doxygen_c"],
  "evidence_refs": [
    {
      "source_id": "ti_weightservice_doxygen_c",
      "what_identified_he": "symbols פנימיים של GATT service module (attr table / read-write callbacks / callbacks storage).",
      "how_identified_he": "קריאת function/member list ב-weightservice.c File Reference.",
      "artifact_ref": "TI Doxygen: weightservice_8c.html",
      "line_refs": ["157-176"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להשאיר handlers ו-attr table ב-service module.",
    "להימנע מהכנסת policy של המדידה ל-callbacks של GATT."
  ]
}
```

```groupb_finding
{
  "id": "wss_structure_zephyr_bas_hrs_pattern_for_static_service",
  "title_he": "דפוס Zephyr לשירות סטטי עם BT_GATT_SERVICE_DEFINE מתאים למבנה צד-Zephyr של WSS",
  "statement_he": "BAS/HRS ב-Zephyr מדגימים מבנה שירות סטטי עם attribute table מאקרו-מבוסס, CCC callback ו-API wrapper ציבורי. דפוס זה מתאים לשכבת ה-service ב-WSS כאשר ה-target הוא Zephyr/NCS.",
  "why_it_matters_he": "מחבר בין מודל TI (service module מופרד) לבין סגנון Zephyr (BT_GATT_SERVICE_DEFINE), ומאפשר מבנה היברידי נכון ל-target בפועל.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "profile_similarity_inference"],
  "source_ids": ["zephyr_bt_bas_service_c", "zephyr_bt_hrs_service_c"],
  "evidence_refs": [
    {
      "source_id": "zephyr_bt_bas_service_c",
      "what_identified_he": "BT_GATT_SERVICE_DEFINE עם characteristic+CCC+CPF ו-API ציבורי לעדכון ערך/notify.",
      "how_identified_he": "קריאת מבנה bas.c ושימוש ב-bt_gatt_notify מתוך API ציבורי.",
      "artifact_ref": "zephyr/subsys/bluetooth/services/bas.c",
      "line_refs": ["50-70", "83-96"],
      "confidence": "high"
    },
    {
      "source_id": "zephyr_bt_hrs_service_c",
      "what_identified_he": "CCC callback נפרד ו-API notify ציבורי נפרד של השירות.",
      "how_identified_he": "קריאת hrs.c (CCC callback + bt_hrs_notify).",
      "artifact_ref": "zephyr/subsys/bluetooth/services/hrs.c",
      "line_refs": ["58-73", "129-140"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "ליישם GATT glue בסגנון Zephyr, אך לשמור חלוקת אחריות מודולרית בהשראת TI."
  ]
}
```

```groupb_finding
{
  "id": "wss_structure_ti_app_message_queue_pattern",
  "title_he": "TI מדריך להפרדת App Task/Event Queue משירות BLE",
  "statement_he": "דפי TI על The Application ועל יצירת אפליקציה מותאמת מציגים event loop/message queue ו-posting מ-callbacks, ולכן מבנה היעד צריך להשאיר orchestration בשכבת app adapter ולא בתוך service handlers.",
  "why_it_matters_he": "מונע service handlers כבדים ומפחית coupling בין BLE callbacks ללוגיקת חיישן/מדידה.",
  "confidence": "high",
  "status": "confirmed",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "callback_registration_pattern"],
  "source_ids": ["ti_ble5stack_application_arch_page", "ti_ble5stack_custom_app_guide"],
  "evidence_refs": [
    {
      "source_id": "ti_ble5stack_application_arch_page",
      "what_identified_he": "תיאור event-driven app task/message queue.",
      "how_identified_he": "קריאת The Application (figure + event handling + stack callback posting).",
      "artifact_ref": "TI BLE5-Stack User Guide: the-application.html",
      "line_refs": ["470-580", "611-631"],
      "confidence": "high"
    },
    {
      "source_id": "ti_ble5stack_custom_app_guide",
      "what_identified_he": "דפוס callbacks שממירים אירועי Stack/App messages לאירועים פנימיים של האפליקציה.",
      "how_identified_he": "קריאת guide ליצירת אפליקציה מותאמת (app callback/event flow).",
      "artifact_ref": "TI BLE5-Stack Guide: Creating a custom Bluetooth Low Energy application",
      "line_refs": ["531-603"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להשאיר תזמון/queue/work ב-`wss_app_adapter` ולא ב-`wss_service`."
  ]
}
```

```groupb_finding
{
  "id": "wss_structure_phase1_subset_service_logic_adapter",
  "title_he": "החלטת Phase 1 מבנית: `wss_service` + `wss_logic` + `wss_app_adapter`, serializer אופציונלי",
  "statement_he": "לשלב ראשון מומלץ לקבע שלושה רכיבים מרכזיים (`wss_service`, `wss_logic`, `wss_app_adapter`) ולשמור את `wss_serializer` כאופציונלי שמופעל רק אם payload phase 1 מתברר כמורכב מספיק.",
  "why_it_matters_he": "החלטה זו מאזנת בין modularity לבין מורכבות מוקדמת מיותרת, ומונעת פיצול יתר לפני שיש צורך מוכח.",
  "confidence": "medium",
  "status": "inferred",
  "derivation_method_ids": ["vendor_sample_structure_pattern", "profile_similarity_inference", "data_model_struct_mapping"],
  "source_ids": ["sig_wss_spec_page", "ti_weightservice_doxygen_c", "zephyr_bt_bas_service_c"],
  "evidence_refs": [
    {
      "source_id": "ti_weightservice_doxygen_c",
      "what_identified_he": "מודול שירות self-contained עם attr table/callbacks פנימיים.",
      "how_identified_he": "קריאת File Reference של weightservice.c.",
      "artifact_ref": "TI Doxygen: weightservice_8c.html",
      "line_refs": ["157-176"],
      "confidence": "high"
    },
    {
      "source_id": "zephyr_bt_bas_service_c",
      "what_identified_he": "תבנית Zephyr לשירות סטטי עם API wrapper ציבורי.",
      "how_identified_he": "קריאת bas.c (BT_GATT_SERVICE_DEFINE + update/notify path).",
      "artifact_ref": "zephyr/subsys/bluetooth/services/bas.c",
      "line_refs": ["50-70", "83-96"],
      "confidence": "high"
    }
  ],
  "implementation_notes_he": [
    "להחליט על serializer נפרד לפי מורכבות payload בפועל של Phase 1, לא אוטומטית.",
    "לשמור API בין `wss_logic` ל-`wss_service` צר וניתן לבדיקה."
  ]
}
```

## תצפיות לפי מקור

```groupb_source_observation
{
  "id": "wss_structure_obs_ti_weight_header_contract",
  "profile_id": "WSS",
  "doc_kind": "structure",
  "source_id": "ti_weightservice_doxygen_h",
  "what_identified_he": "API ציבורי וקונטרקט callbacks של Weight Service.",
  "how_identified_he": "קריאת declarations וה-typedefs ב-header Doxygen.",
  "artifact_ref": "TI Doxygen: weightservice_8h.html",
  "line_refs": ["196-242", "254-340"],
  "confidence": "high",
  "notes_he": "המקור העיקרי לבניית interface של `wss_service.h`."
}
```

```groupb_source_observation
{
  "id": "wss_structure_obs_ti_weight_c_internals",
  "profile_id": "WSS",
  "doc_kind": "structure",
  "source_id": "ti_weightservice_doxygen_c",
  "what_identified_he": "ריכוז GATT plumbing פנימי (attr table, read/write callbacks, callback pointer storage).",
  "how_identified_he": "קריאת member/function list ב-File Reference של weightservice.c.",
  "artifact_ref": "TI Doxygen: weightservice_8c.html",
  "line_refs": ["157-176"],
  "confidence": "high",
  "notes_he": "תומך בהפרדה בין `wss_service` ל-`wss_logic`."
}
```

```groupb_source_observation
{
  "id": "wss_structure_obs_zephyr_bas_hrs_service_pattern",
  "profile_id": "WSS",
  "doc_kind": "structure",
  "source_id": "zephyr_bt_bas_service_c",
  "what_identified_he": "תבנית שירות Zephyr סטטי עם `BT_GATT_SERVICE_DEFINE` + CCC + API wrapper ציבורי.",
  "how_identified_he": "קריאת bas.c והצלבה עם hrs.c עבור CCC callback/notify path.",
  "artifact_ref": "zephyr/subsys/bluetooth/services/bas.c + zephyr/subsys/bluetooth/services/hrs.c",
  "line_refs": ["bas.c: 50-70, 83-96", "hrs.c: 58-73, 129-140"],
  "confidence": "high",
  "notes_he": "משמש כתבנית מימוש Zephyr-side, לא כתחליף ל-spec של WSS."
}
```

```groupb_source_observation
{
  "id": "wss_structure_obs_sig_wss_page_scope",
  "profile_id": "WSS",
  "doc_kind": "structure",
  "source_id": "sig_wss_spec_page",
  "what_identified_he": "עמוד spec רשמי WSS וארטיפקטי TS/ICS/TCRL לתיחום Phase 1 ו-Phase 2 ברמת מודולים.",
  "how_identified_he": "קריאת עמוד spec רשמי והצלבה עם inventory המסונכרן ב-Hub עבור WSS.",
  "artifact_ref": "Bluetooth SIG spec page + docs/profiles/WSS",
  "line_refs": ["spec page metadata", "hub spec inventory row"],
  "confidence": "high",
  "notes_he": "תצפית scope שתומכת בהחלטת תכולת שלב ראשון, לא מקור יחיד למבנה API."
}
```

## שיטות חילוץ/ניתוח

```groupb_method
{
  "id": "ti_doxygen_api_surface_read",
  "profile_id": "WSS",
  "doc_kind": "structure",
  "status": "used",
  "notes_he": "חילוץ מבנה מודול השירות מתוך header/c Doxygen של TI Weight Service."
}
```

```groupb_method
{
  "id": "ti_guide_architecture_pattern_read",
  "profile_id": "WSS",
  "doc_kind": "structure",
  "status": "used",
  "notes_he": "חילוץ דפוסי App Task/Event Queue/Callbacks מתוך TI BLE5-Stack guides."
}
```

## פערים ושאלות פתוחות

```groupb_open_question
{
  "id": "wss_structure_q1_serializer_split",
  "profile_id": "WSS",
  "title_he": "האם לפצל serializer ליחידה נפרדת כבר בשלב ראשון",
  "detail_he": "אם WSS payload יכלול שדות אופציונליים רבים (timestamp/user/BMI/height וכו'), פיצול serializer עשוי לשפר תחזוקה ובדיקות כבר מהשלב הראשון.",
  "priority": "medium",
  "status": "open",
  "source_ids": ["sig_wss_spec_page", "ti_weightservice_doxygen_c"]
}
```

## השלכות למימוש

- לאמץ `wss_service` כמודול שירות self-contained עם read/write/CCC plumbing.
- להשאיר logic orchestration בשכבת `wss_logic`/`wss_app_adapter` ולא ב-callbacks של GATT.
- להכין מראש state struct שמכיל capability flags + subscription state + last measurement metadata.

## מקורות

- `ti_simplelink_sdk`
- `ti_ble5stack_docs_root`
- `ti_weightservice_doxygen_h`
- `ti_weightservice_doxygen_c`
- `ti_ble5stack_application_arch_page`
- `ti_ble5stack_custom_app_guide`
- `zephyr_bt_bas_service_c`
- `zephyr_bt_hrs_service_c`
- `sig_wss_spec_page`
