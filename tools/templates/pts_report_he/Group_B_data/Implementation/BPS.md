---
profile_id: BPS
display_name_he: שירות לחץ דם
doc_kind: implementation
status: reviewed
updated_at: 2026-03-23
language: he
schema_version: 1
---

## סיכום

מימוש BPS ב-Phase 1 נשען על שלושה מודולים ברורים: `bps_service` שמחזיק את ה-GATT plumbing, `bps_logic` שמכין את ה-payload ומחליט אם בכלל מותר לפרסם, ו-`bps_app_adapter` שמחבר את הזרימה למקור המדידה בפועל. היעד כאן הוא לתת תצוגת implementation מלאה, אבל לשמור את ה-scope ממוקד למדידה הראשית ול-Indication path.

## קבצים למימוש

```groupb_impl_file
{
  "file_id": "bps_service_h",
  "filename": "bps_service.h",
  "relative_path": "zephyr/include/zephyr/bluetooth/services/bps_service.h",
  "language": "c",
  "purpose_he": "החוזה הציבורי של שכבת השירות: init, callbacks, publish ו-state בסיסי של subscription/ack.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "bps_logic_ccc_and_notify_gate_pattern_from_zephyr_hrs",
      "bps_logic_phase1_subset_publish_measurement_first"
    ],
    "structure_ids": [
      "bps_structure_ti_bps_service_api_surface",
      "bps_structure_phase1_subset_service_logic_split"
    ],
    "pattern_ids": ["10.2", "10.3"]
  },
  "decision_notes_he": [
    "ה-service מקבל payload מקודד מוכן ולא בונה אותו בעצמו.",
    "ה-header שומר API קטן כדי לא לנעול מוקדם מדי את שאר ה-stack."
  ],
  "source_ids": [
    "sig_bps_spec_page",
    "zephyr_bt_hrs_service_c",
    "ti_blood_pressure_service_doxygen_h"
  ]
}
```
```c
#ifndef ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_BPS_SERVICE_H_
#define ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_BPS_SERVICE_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <zephyr/bluetooth/conn.h>

struct bps_service_callbacks {
	void (*measurement_ccc_changed)(bool enabled);
	void (*send_error)(int err);
};

int bps_service_init(void);
void bps_service_register_callbacks(const struct bps_service_callbacks *callbacks);
bool bps_service_measurement_subscribed(void);
bool bps_service_indication_in_flight(void);
int bps_service_publish_measurement(struct bt_conn *conn, const uint8_t *payload, size_t len);
void bps_service_complete_indication(int err);

#endif /* ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_BPS_SERVICE_H_ */
```

```groupb_impl_file
{
  "file_id": "bps_service_c",
  "filename": "bps_service.c",
  "relative_path": "zephyr/subsys/bluetooth/services/bps_service.c",
  "language": "c",
  "purpose_he": "מימוש ה-GATT service, CCC callback, indicate gating, ו-API publish ברור למסלול המדידה הראשית.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "bps_logic_ccc_and_notify_gate_pattern_from_zephyr_hrs",
      "bps_logic_phase1_subset_publish_measurement_first"
    ],
    "structure_ids": [
      "bps_structure_ti_bps_attr_table_and_callbacks",
      "bps_structure_phase1_subset_service_logic_split"
    ],
    "pattern_ids": ["10.2"]
  },
  "decision_notes_he": [
    "ה-service שומר רק state קצר של CCC ו-ACK.",
    "כל policy על timing או sampling נשאר מחוץ לקובץ הזה."
  ],
  "source_ids": [
    "sig_bps_spec_page",
    "zephyr_bt_hrs_service_c",
    "ti_blood_pressure_service_doxygen_c"
  ]
}
```
```c
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/logging/log.h>
#include "bps_service.h"

LOG_MODULE_REGISTER(bps_service, LOG_LEVEL_INF);

static const struct bps_service_callbacks *callbacks;
static bool measurement_ccc_enabled;
static bool indication_in_flight;

static void bps_measurement_ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
	ARG_UNUSED(attr);
	measurement_ccc_enabled = (value == BT_GATT_CCC_INDICATE);
	if (callbacks && callbacks->measurement_ccc_changed) {
		callbacks->measurement_ccc_changed(measurement_ccc_enabled);
	}
}

BT_GATT_SERVICE_DEFINE(bps_svc,
	BT_GATT_PRIMARY_SERVICE(BT_UUID_DECLARE_16(0x1810)),
	BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(0x2A35),
			       BT_GATT_CHRC_INDICATE,
			       BT_GATT_PERM_NONE, NULL, NULL, NULL),
	BT_GATT_CCC(bps_measurement_ccc_changed,
		    BT_GATT_PERM_READ | BT_GATT_PERM_WRITE));

int bps_service_init(void)
{
	measurement_ccc_enabled = false;
	indication_in_flight = false;
	return 0;
}

void bps_service_register_callbacks(const struct bps_service_callbacks *new_callbacks)
{
	callbacks = new_callbacks;
}

bool bps_service_measurement_subscribed(void)
{
	return measurement_ccc_enabled;
}

bool bps_service_indication_in_flight(void)
{
	return indication_in_flight;
}

int bps_service_publish_measurement(struct bt_conn *conn, const uint8_t *payload, size_t len)
{
	struct bt_gatt_indicate_params params = {
		.attr = &bps_svc.attrs[2],
		.data = payload,
		.len = len,
	};

	if (!measurement_ccc_enabled || indication_in_flight) {
		return -EAGAIN;
	}

	indication_in_flight = true;
	return bt_gatt_indicate(conn, &params);
}

void bps_service_complete_indication(int err)
{
	indication_in_flight = false;
	if (err && callbacks && callbacks->send_error) {
		callbacks->send_error(err);
	}
}
```

```groupb_impl_file
{
  "file_id": "bps_logic_h",
  "filename": "bps_logic.h",
  "relative_path": "samples/bluetooth/group_b/bps/src/bps_logic.h",
  "language": "c",
  "purpose_he": "חוזה הלוגיקה של BPS: input פשוט, בדיקת gating, והכנת payload מקודד למסלול המדידה.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "bps_logic_health_session_and_measurement_pipeline_pattern",
      "bps_logic_phase1_subset_publish_measurement_first"
    ],
    "structure_ids": [
      "bps_structure_phase1_subset_service_logic_split"
    ],
    "pattern_ids": ["10.2"]
  },
  "decision_notes_he": [
    "הלוגיקה לא מדברת ישירות עם bt_gatt_indicate.",
    "ה-input נשאר בפורמט נוח לעבודה, לא בפורמט BLE-wire."
  ],
  "source_ids": [
    "sig_bps_spec_page",
    "nordic_ncs_sample_peripheral_cgms_main"
  ]
}
```
```c
#ifndef SAMPLES_BLUETOOTH_GROUP_B_BPS_SRC_BPS_LOGIC_H_
#define SAMPLES_BLUETOOTH_GROUP_B_BPS_SRC_BPS_LOGIC_H_

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

struct bps_logic_measurement {
	uint16_t systolic;
	uint16_t diastolic;
	uint16_t mean_arterial_pressure;
};

void bps_logic_init(void);
bool bps_logic_can_publish(bool ccc_enabled, bool indication_in_flight);
size_t bps_logic_encode_measurement(const struct bps_logic_measurement *measurement,
				      uint8_t *payload,
				      size_t payload_size);

#endif /* SAMPLES_BLUETOOTH_GROUP_B_BPS_SRC_BPS_LOGIC_H_ */
```

```groupb_impl_file
{
  "file_id": "bps_logic_c",
  "filename": "bps_logic.c",
  "relative_path": "samples/bluetooth/group_b/bps/src/bps_logic.c",
  "language": "c",
  "purpose_he": "לוגיקת ה-gating וה-encoding של המדידה הראשית ב-Phase 1.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "bps_logic_health_session_and_measurement_pipeline_pattern",
      "bps_logic_phase1_subset_publish_measurement_first"
    ],
    "structure_ids": [
      "bps_structure_multi_ccc_and_module_split_expectation"
    ],
    "pattern_ids": ["10.2"]
  },
  "decision_notes_he": [
    "ה-serializer נשאר helper קטן בתוך הלוגיקה.",
    "Intermediate Cuff ו-Control Point לא נכנסים כאן ב-Phase 1."
  ],
  "source_ids": [
    "sig_bps_spec_page",
    "nordic_ncs_sample_peripheral_cgms_main"
  ]
}
```
```c
#include <string.h>
#include "bps_logic.h"

void bps_logic_init(void)
{
	/* No complex state is needed in Phase 1. */
}

bool bps_logic_can_publish(bool ccc_enabled, bool indication_in_flight)
{
	return ccc_enabled && !indication_in_flight;
}

size_t bps_logic_encode_measurement(const struct bps_logic_measurement *measurement,
				      uint8_t *payload,
				      size_t payload_size)
{
	if (!measurement || !payload || payload_size < 7U) {
		return 0U;
	}

	memset(payload, 0, payload_size);
	payload[0] = 0x00; /* Flags: Phase 1 subset without optional fields */
	payload[1] = measurement->systolic & 0xff;
	payload[2] = measurement->systolic >> 8;
	payload[3] = measurement->diastolic & 0xff;
	payload[4] = measurement->diastolic >> 8;
	payload[5] = measurement->mean_arterial_pressure & 0xff;
	payload[6] = measurement->mean_arterial_pressure >> 8;
	return 7U;
}
```

```groupb_impl_file
{
  "file_id": "bps_app_adapter_h",
  "filename": "bps_app_adapter.h",
  "relative_path": "samples/bluetooth/group_b/bps/src/bps_app_adapter.h",
  "language": "c",
  "purpose_he": "חוזה האינטגרציה עם האפליקציה: init וטריגר פשוט לפרסום מדידה.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "bps_logic_app_init_sequence_pattern_from_nus"
    ],
    "structure_ids": [
      "bps_structure_phase1_subset_service_logic_split"
    ],
    "pattern_ids": []
  },
  "decision_notes_he": [
    "האדפטר מחבר bring-up ולא מוסיף policy עסקי משלו."
  ],
  "source_ids": [
    "nordic_ncs_sample_peripheral_uart_main",
    "ti_ble5stack_application_arch_page"
  ]
}
```
```c
#ifndef SAMPLES_BLUETOOTH_GROUP_B_BPS_SRC_BPS_APP_ADAPTER_H_
#define SAMPLES_BLUETOOTH_GROUP_B_BPS_SRC_BPS_APP_ADAPTER_H_

#include "bps_logic.h"

int bps_app_adapter_init(void);
int bps_app_adapter_publish_sample(const struct bps_logic_measurement *measurement);

#endif /* SAMPLES_BLUETOOTH_GROUP_B_BPS_SRC_BPS_APP_ADAPTER_H_ */
```

```groupb_impl_file
{
  "file_id": "bps_app_adapter_c",
  "filename": "bps_app_adapter.c",
  "relative_path": "samples/bluetooth/group_b/bps/src/bps_app_adapter.c",
  "language": "c",
  "purpose_he": "הדבקה בין מקור המדידה, הלוגיקה והשירות; זהו ה-entry point האפליקטיבי של Phase 1.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "bps_logic_app_init_sequence_pattern_from_nus",
      "bps_logic_phase1_subset_publish_measurement_first"
    ],
    "structure_ids": [
      "bps_structure_phase1_subset_service_logic_split"
    ],
    "pattern_ids": []
  },
  "decision_notes_he": [
    "האדפטר שומר את סדר האתחול ומעביר רק payloadים תקינים לשירות."
  ],
  "source_ids": [
    "nordic_ncs_sample_peripheral_uart_main",
    "zephyr_bt_hrs_service_c"
  ]
}
```
```c
#include "bps_app_adapter.h"
#include "bps_logic.h"
#include "bps_service.h"

int bps_app_adapter_init(void)
{
	bps_logic_init();
	return bps_service_init();
}

int bps_app_adapter_publish_sample(const struct bps_logic_measurement *measurement)
{
	uint8_t payload[7];
	size_t len;

	if (!bps_logic_can_publish(bps_service_measurement_subscribed(),
				       bps_service_indication_in_flight())) {
		return -EAGAIN;
	}

	len = bps_logic_encode_measurement(measurement, payload, sizeof(payload));
	if (!len) {
		return -EINVAL;
	}

	return bps_service_publish_measurement(NULL, payload, len);
}
```

## החלטות מימוש

```groupb_impl_decision
{
  "id": "bps_impl_decision_keep_serializer_internal",
  "title_he": "ה-serializer נשאר helper פנימי של הלוגיקה",
  "decision_he": "ב-Phase 1 אין קובץ serializer נפרד. הקידוד של המדידה הראשית נשאר בתוך `bps_logic.c` כדי לא לפצל מוקדם מדי את ה-flow.",
  "why_needed_he": "זה keeps the code path קצר וברור, ומונע פיצול מיותר לפני שיש Intermediate Cuff או וריאציות payload עשירות יותר.",
  "pattern_he": "measurement-delivery",
  "applies_to_files": ["bps_logic_c"],
  "tags": ["scope-control", "phase1"],
  "confidence": "high",
  "source_ids": [
    "sig_bps_spec_page",
    "nordic_ncs_sample_peripheral_cgms_main"
  ]
}
```

```groupb_impl_decision
{
  "id": "bps_impl_decision_service_only_sends",
  "title_he": "שכבת השירות רק שולחת, לא מחליטה מה לשלוח",
  "decision_he": "`bps_service` מחזיק CCC ו-ACK state בלבד. כל החלטה על publish timing או על בניית ה-payload נשארת בלוגיקה וב-adapter.",
  "why_needed_he": "זה שומר את הקובץ של השירות Zephyr-native ופשוט לבדיקה, ומונע ערבוב בין policy לבין GATT plumbing.",
  "pattern_he": "indication-flow",
  "applies_to_files": ["bps_service_c", "bps_logic_c", "bps_app_adapter_c"],
  "tags": ["separation-of-concerns"],
  "confidence": "high",
  "source_ids": [
    "zephyr_bt_hrs_service_c",
    "ti_blood_pressure_service_doxygen_c"
  ]
}
```

## מקורות

- `sig_bps_spec_page`
- `zephyr_bt_hrs_service_c`
- `ti_blood_pressure_service_doxygen_h`
- `ti_blood_pressure_service_doxygen_c`
- `nordic_ncs_sample_peripheral_cgms_main`
- `nordic_ncs_sample_peripheral_uart_main`
- `ti_ble5stack_application_arch_page`
