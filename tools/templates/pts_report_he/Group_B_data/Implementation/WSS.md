---
profile_id: WSS
display_name_he: שירות משקל
doc_kind: implementation
status: reviewed
updated_at: 2026-03-23
language: he
schema_version: 1
---

## סיכום

מימוש WSS ב-Phase 1 נשען על אותו עיקרון של שלוש שכבות, אבל עם דגש קל יותר: `wss_service` מחזיק את מסלול ה-Indication וה-CCCD, `wss_logic` מחליט מתי יש מדידה ראויה לפרסום ומקודד אותה, ו-`wss_app_adapter` מחבר את המדידה או ה-work trigger למימוש. אין כאן קובץ serializer נפרד; הוא נשאר helper פנימי של הלוגיקה.

## קבצים למימוש

```groupb_impl_file
{
  "file_id": "wss_service_h",
  "filename": "wss_service.h",
  "relative_path": "zephyr/include/zephyr/bluetooth/services/wss_service.h",
  "language": "c",
  "purpose_he": "החוזה הציבורי של שירות WSS: init, callbacks, בדיקת subscription ו-publish של Weight Measurement.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "wss_logic_ccc_notify_and_update_api_pattern",
      "wss_logic_phase1_subset_single_measurement_publish_flow"
    ],
    "structure_ids": [
      "wss_structure_ti_weight_module_contract",
      "wss_structure_phase1_subset_service_logic_adapter"
    ],
    "pattern_ids": ["10.2", "10.3"]
  },
  "decision_notes_he": [
    "ה-header מכוון למסלול מדידה יחיד ב-Phase 1.",
    "Feature update נשאר אופציונלי ולא מכתיב API נפרד כרגע."
  ],
  "source_ids": [
    "sig_wss_spec_page",
    "zephyr_bt_hrs_service_c",
    "ti_weightservice_doxygen_h"
  ]
}
```
```c
#ifndef ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_WSS_SERVICE_H_
#define ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_WSS_SERVICE_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <zephyr/bluetooth/conn.h>

struct wss_service_callbacks {
	void (*measurement_ccc_changed)(bool enabled);
	void (*send_error)(int err);
};

int wss_service_init(void);
void wss_service_register_callbacks(const struct wss_service_callbacks *callbacks);
bool wss_service_measurement_subscribed(void);
bool wss_service_indication_in_flight(void);
int wss_service_publish_measurement(struct bt_conn *conn, const uint8_t *payload, size_t len);
void wss_service_complete_indication(int err);

#endif /* ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_WSS_SERVICE_H_ */
```

```groupb_impl_file
{
  "file_id": "wss_service_c",
  "filename": "wss_service.c",
  "relative_path": "zephyr/subsys/bluetooth/services/wss_service.c",
  "language": "c",
  "purpose_he": "מימוש שירות WSS ב-Zephyr: characteristic ראשי, CCC callback ומסלול Indication עם ACK gating.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "wss_logic_ccc_notify_and_update_api_pattern",
      "wss_logic_phase1_subset_single_measurement_publish_flow"
    ],
    "structure_ids": [
      "wss_structure_ti_weight_attr_table_callbacks",
      "wss_structure_zephyr_bas_hrs_pattern_for_static_service"
    ],
    "pattern_ids": ["10.2"]
  },
  "decision_notes_he": [
    "השירות לא שומר policy של יציבות מדידה.",
    "הגייטינג מול ACK ו-CCCD נשמר כאן כי זה transport concern."
  ],
  "source_ids": [
    "sig_wss_spec_page",
    "zephyr_bt_hrs_service_c",
    "ti_weightservice_doxygen_c"
  ]
}
```
```c
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/logging/log.h>
#include "wss_service.h"

LOG_MODULE_REGISTER(wss_service, LOG_LEVEL_INF);

static const struct wss_service_callbacks *callbacks;
static bool measurement_ccc_enabled;
static bool indication_in_flight;

static void wss_measurement_ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
	ARG_UNUSED(attr);
	measurement_ccc_enabled = (value == BT_GATT_CCC_INDICATE);
	if (callbacks && callbacks->measurement_ccc_changed) {
		callbacks->measurement_ccc_changed(measurement_ccc_enabled);
	}
}

BT_GATT_SERVICE_DEFINE(wss_svc,
	BT_GATT_PRIMARY_SERVICE(BT_UUID_DECLARE_16(0x181D)),
	BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(0x2A9D),
			       BT_GATT_CHRC_INDICATE,
			       BT_GATT_PERM_NONE, NULL, NULL, NULL),
	BT_GATT_CCC(wss_measurement_ccc_changed,
		    BT_GATT_PERM_READ | BT_GATT_PERM_WRITE));

int wss_service_init(void)
{
	measurement_ccc_enabled = false;
	indication_in_flight = false;
	return 0;
}

void wss_service_register_callbacks(const struct wss_service_callbacks *new_callbacks)
{
	callbacks = new_callbacks;
}

bool wss_service_measurement_subscribed(void)
{
	return measurement_ccc_enabled;
}

bool wss_service_indication_in_flight(void)
{
	return indication_in_flight;
}

int wss_service_publish_measurement(struct bt_conn *conn, const uint8_t *payload, size_t len)
{
	struct bt_gatt_indicate_params params = {
		.attr = &wss_svc.attrs[2],
		.data = payload,
		.len = len,
	};

	if (!measurement_ccc_enabled || indication_in_flight) {
		return -EAGAIN;
	}

	indication_in_flight = true;
	return bt_gatt_indicate(conn, &params);
}

void wss_service_complete_indication(int err)
{
	indication_in_flight = false;
	if (err && callbacks && callbacks->send_error) {
		callbacks->send_error(err);
	}
}
```

```groupb_impl_file
{
  "file_id": "wss_logic_h",
  "filename": "wss_logic.h",
  "relative_path": "samples/bluetooth/group_b/wss/src/wss_logic.h",
  "language": "c",
  "purpose_he": "חוזה הלוגיקה של WSS: input קריא, בדיקת publish readiness, וקידוד מדידה למסלול Phase 1.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "wss_logic_periodic_measurement_simulation_pattern",
      "wss_logic_phase1_subset_single_measurement_publish_flow"
    ],
    "structure_ids": [
      "wss_structure_phase1_subset_service_logic_adapter"
    ],
    "pattern_ids": ["10.2"]
  },
  "decision_notes_he": [
    "הקידוד נשמר פנימי ל-logic כדי לא לפתוח serializer file מוקדם מדי."
  ],
  "source_ids": [
    "sig_wss_spec_page",
    "nordic_ncs_sample_peripheral_hr_coded_main"
  ]
}
```
```c
#ifndef SAMPLES_BLUETOOTH_GROUP_B_WSS_SRC_WSS_LOGIC_H_
#define SAMPLES_BLUETOOTH_GROUP_B_WSS_SRC_WSS_LOGIC_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

struct wss_logic_measurement {
	uint16_t weight_kg_x200;
	bool measurement_ready;
};

void wss_logic_init(void);
bool wss_logic_can_publish(bool ccc_enabled, bool indication_in_flight, bool measurement_ready);
size_t wss_logic_encode_measurement(const struct wss_logic_measurement *measurement,
				      uint8_t *payload,
				      size_t payload_size);

#endif /* SAMPLES_BLUETOOTH_GROUP_B_WSS_SRC_WSS_LOGIC_H_ */
```

```groupb_impl_file
{
  "file_id": "wss_logic_c",
  "filename": "wss_logic.c",
  "relative_path": "samples/bluetooth/group_b/wss/src/wss_logic.c",
  "language": "c",
  "purpose_he": "לוגיקת readiness וקידוד משקל למסלול המדידה הראשי.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "wss_logic_periodic_measurement_simulation_pattern",
      "wss_logic_phase1_subset_single_measurement_publish_flow"
    ],
    "structure_ids": [
      "wss_structure_phase1_subset_service_logic_adapter"
    ],
    "pattern_ids": ["10.2"]
  },
  "decision_notes_he": [
    "ה-helper של הקידוד נשאר בקובץ הזה.",
    "fields אופציונליים של WSS לא נכנסים ל-Phase 1."
  ],
  "source_ids": [
    "sig_wss_spec_page",
    "nordic_ncs_sample_peripheral_hr_coded_main"
  ]
}
```
```c
#include <string.h>
#include "wss_logic.h"

void wss_logic_init(void)
{
}

bool wss_logic_can_publish(bool ccc_enabled, bool indication_in_flight, bool measurement_ready)
{
	return ccc_enabled && !indication_in_flight && measurement_ready;
}

size_t wss_logic_encode_measurement(const struct wss_logic_measurement *measurement,
				      uint8_t *payload,
				      size_t payload_size)
{
	if (!measurement || !payload || payload_size < 3U) {
		return 0U;
	}

	memset(payload, 0, payload_size);
	payload[0] = 0x00; /* Flags: basic subset */
	payload[1] = measurement->weight_kg_x200 & 0xff;
	payload[2] = measurement->weight_kg_x200 >> 8;
	return 3U;
}
```

```groupb_impl_file
{
  "file_id": "wss_app_adapter_h",
  "filename": "wss_app_adapter.h",
  "relative_path": "samples/bluetooth/group_b/wss/src/wss_app_adapter.h",
  "language": "c",
  "purpose_he": "חוזה האינטגרציה של WSS: init ופרסום מדידה מהאפליקציה.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "wss_logic_periodic_measurement_simulation_pattern"
    ],
    "structure_ids": [
      "wss_structure_ti_app_message_queue_pattern"
    ],
    "pattern_ids": []
  },
  "decision_notes_he": [
    "ה-adapter נשאר דק ומחבר בין trigger למדידה לבין service publish."
  ],
  "source_ids": [
    "nordic_ncs_sample_peripheral_hr_coded_main",
    "ti_ble5stack_application_arch_page"
  ]
}
```
```c
#ifndef SAMPLES_BLUETOOTH_GROUP_B_WSS_SRC_WSS_APP_ADAPTER_H_
#define SAMPLES_BLUETOOTH_GROUP_B_WSS_SRC_WSS_APP_ADAPTER_H_

#include "wss_logic.h"

int wss_app_adapter_init(void);
int wss_app_adapter_publish_sample(const struct wss_logic_measurement *measurement);

#endif /* SAMPLES_BLUETOOTH_GROUP_B_WSS_SRC_WSS_APP_ADAPTER_H_ */
```

```groupb_impl_file
{
  "file_id": "wss_app_adapter_c",
  "filename": "wss_app_adapter.c",
  "relative_path": "samples/bluetooth/group_b/wss/src/wss_app_adapter.c",
  "language": "c",
  "purpose_he": "entry point אפליקטיבי פשוט ל-WSS ב-Phase 1.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "wss_logic_periodic_measurement_simulation_pattern",
      "wss_logic_phase1_subset_single_measurement_publish_flow"
    ],
    "structure_ids": [
      "wss_structure_ti_app_message_queue_pattern"
    ],
    "pattern_ids": []
  },
  "decision_notes_he": [
    "אם later נעבור לחיישן אמיתי, מחליפים רק את מקור ה-trigger ולא את מבנה ה-service."
  ],
  "source_ids": [
    "nordic_ncs_sample_peripheral_hr_coded_main",
    "zephyr_bt_bas_service_c"
  ]
}
```
```c
#include "wss_app_adapter.h"
#include "wss_logic.h"
#include "wss_service.h"

int wss_app_adapter_init(void)
{
	wss_logic_init();
	return wss_service_init();
}

int wss_app_adapter_publish_sample(const struct wss_logic_measurement *measurement)
{
	uint8_t payload[8];
	size_t len;

	if (!wss_logic_can_publish(wss_service_measurement_subscribed(),
				       wss_service_indication_in_flight(),
				       measurement && measurement->measurement_ready)) {
		return -EAGAIN;
	}

	len = wss_logic_encode_measurement(measurement, payload, sizeof(payload));
	if (!len) {
		return -EINVAL;
	}

	return wss_service_publish_measurement(NULL, payload, len);
}
```

## החלטות מימוש

```groupb_impl_decision
{
  "id": "wss_impl_decision_no_serializer_file_in_phase1",
  "title_he": "אין serializer file נפרד ב-Phase 1",
  "decision_he": "הקידוד של Weight Measurement נשאר helper פנימי בתוך `wss_logic.c`. אם payload Phase 2 יגדל, נוציא אותו לקובץ נפרד.",
  "why_needed_he": "המסלול הנוכחי פשוט, והפרדה מוקדמת רק מוסיפה קפיצה מיותרת בין קבצים.",
  "pattern_he": "measurement-delivery",
  "applies_to_files": ["wss_logic_c"],
  "tags": ["scope-control", "phase1"],
  "confidence": "high",
  "source_ids": [
    "sig_wss_spec_page",
    "nordic_ncs_sample_peripheral_hr_coded_main"
  ]
}
```

```groupb_impl_decision
{
  "id": "wss_impl_decision_trigger_policy_outside_service",
  "title_he": "trigger policy נשאר מחוץ לשירות",
  "decision_he": "`wss_service` לא מחליט מתי המדידה יציבה או מתי נכון לפרסם. הוא רק מבצע את ה-Indication כשמביאים לו payload מוכן.",
  "why_needed_he": "כך אפשר להחליף later בין trigger מחזורי, חיישן אמיתי או work queue בלי לפתוח את קוד השירות.",
  "pattern_he": "indication-flow",
  "applies_to_files": ["wss_service_c", "wss_logic_c", "wss_app_adapter_c"],
  "tags": ["separation-of-concerns"],
  "confidence": "high",
  "source_ids": [
    "zephyr_bt_hrs_service_c",
    "ti_weightservice_doxygen_c"
  ]
}
```

## מקורות

- `sig_wss_spec_page`
- `zephyr_bt_hrs_service_c`
- `zephyr_bt_bas_service_c`
- `ti_weightservice_doxygen_h`
- `ti_weightservice_doxygen_c`
- `nordic_ncs_sample_peripheral_hr_coded_main`
- `ti_ble5stack_application_arch_page`
