---
profile_id: SCPS
display_name_he: שירות פרמטרי סריקה
doc_kind: implementation
status: reviewed
updated_at: 2026-03-23
language: he
schema_version: 1
---

## סיכום

מימוש SCPS ב-Phase 1 שונה מהפרופילים המדידתיים: `scps_service` מחזיק את ה-GATT service ואת מסלול ה-write/refresh, `scps_scan_policy` שומר את ערכי ה-scan והחלטת ההפעלה בפועל, ו-`scps_app_adapter` מחבר את זה ל-runtime דרך work queue או callback. ההפרדה הזו קריטית כדי לא להפעיל scan runtime מתוך write handler.

## קבצים למימוש

```groupb_impl_file
{
  "file_id": "scps_service_h",
  "filename": "scps_service.h",
  "relative_path": "zephyr/include/zephyr/bluetooth/services/scps_service.h",
  "language": "c",
  "purpose_he": "החוזה הציבורי של שירות SCPS: רישום callbacks, שמירת Scan Interval Window, ו-Scan Refresh request.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "scps_logic_ti_scanparamservice_two_path_flow",
      "scps_logic_phase1_subset_write_and_refresh_split"
    ],
    "structure_ids": [
      "scps_structure_ti_scanparamservice_module_contract",
      "scps_structure_phase1_subset_service_and_scan_policy_split"
    ],
    "pattern_ids": ["10.1"]
  },
  "decision_notes_he": [
    "ה-service לא מחליט מה לעשות עם הערכים אחרי ה-write; הוא רק מעביר אותם הלאה.",
    "ה-refresh request נשאר API מפורש ולא side effect שקט."
  ],
  "source_ids": [
    "sig_scps_spec_page",
    "ti_scanparamservice_doxygen_h"
  ]
}
```
```c
#ifndef ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_SCPS_SERVICE_H_
#define ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_SCPS_SERVICE_H_

#include <stdint.h>
#include <zephyr/bluetooth/conn.h>

struct scps_written_window {
	uint16_t interval;
	uint16_t window;
};

struct scps_service_callbacks {
	void (*interval_window_written)(const struct scps_written_window *params);
	void (*refresh_requested)(void);
};

int scps_service_init(void);
void scps_service_register_callbacks(const struct scps_service_callbacks *callbacks);
int scps_service_store_interval_window(const struct scps_written_window *params);
int scps_service_request_refresh(struct bt_conn *conn);

#endif /* ZEPHYR_INCLUDE_ZEPHYR_BLUETOOTH_SERVICES_SCPS_SERVICE_H_ */
```

```groupb_impl_file
{
  "file_id": "scps_service_c",
  "filename": "scps_service.c",
  "relative_path": "zephyr/subsys/bluetooth/services/scps_service.c",
  "language": "c",
  "purpose_he": "מימוש ה-GATT service של SCPS: write handler ל-Scan Interval Window ומסלול notify עבור Scan Refresh.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "scps_logic_custom_gatt_service_pattern_from_shorter_conn_intervals",
      "scps_logic_ti_scanparamservice_two_path_flow"
    ],
    "structure_ids": [
      "scps_structure_ti_scanparamservice_attr_and_conn_status_callbacks",
      "scps_structure_phase1_subset_service_and_scan_policy_split"
    ],
    "pattern_ids": ["10.1"]
  },
  "decision_notes_he": [
    "ה-write callback רק מבצע parsing בסיסי ומעביר הלאה.",
    "Scan Refresh נשאר notify path קטן וברור."
  ],
  "source_ids": [
    "sig_scps_spec_page",
    "ti_scanparamservice_doxygen_c",
    "nordic_ncs_sample_shorter_conn_intervals_main"
  ]
}
```
```c
#include <string.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/logging/log.h>
#include "scps_service.h"

LOG_MODULE_REGISTER(scps_service, LOG_LEVEL_INF);

static const struct scps_service_callbacks *callbacks;
static bool refresh_ccc_enabled;
static struct scps_written_window last_written;

static ssize_t scps_write_interval_window(struct bt_conn *conn,
					  const struct bt_gatt_attr *attr,
					  const void *buf,
					  uint16_t len,
					  uint16_t offset,
					  uint8_t flags)
{
	ARG_UNUSED(conn);
	ARG_UNUSED(attr);
	ARG_UNUSED(flags);

	if (offset || len != sizeof(last_written)) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
	}

	memcpy(&last_written, buf, sizeof(last_written));
	if (callbacks && callbacks->interval_window_written) {
		callbacks->interval_window_written(&last_written);
	}

	return len;
}

static void scps_refresh_ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
	ARG_UNUSED(attr);
	refresh_ccc_enabled = (value == BT_GATT_CCC_NOTIFY);
}

BT_GATT_SERVICE_DEFINE(scps_svc,
	BT_GATT_PRIMARY_SERVICE(BT_UUID_DECLARE_16(0x1813)),
	BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(0x2A4F),
			       BT_GATT_CHRC_WRITE_WITHOUT_RESP,
			       BT_GATT_PERM_WRITE, NULL, scps_write_interval_window, NULL),
	BT_GATT_CHARACTERISTIC(BT_UUID_DECLARE_16(0x2A31),
			       BT_GATT_CHRC_NOTIFY,
			       BT_GATT_PERM_NONE, NULL, NULL, NULL),
	BT_GATT_CCC(scps_refresh_ccc_changed,
		    BT_GATT_PERM_READ | BT_GATT_PERM_WRITE));

int scps_service_init(void)
{
	memset(&last_written, 0, sizeof(last_written));
	refresh_ccc_enabled = false;
	return 0;
}

void scps_service_register_callbacks(const struct scps_service_callbacks *new_callbacks)
{
	callbacks = new_callbacks;
}

int scps_service_store_interval_window(const struct scps_written_window *params)
{
	if (!params) {
		return -EINVAL;
	}
	last_written = *params;
	return 0;
}

int scps_service_request_refresh(struct bt_conn *conn)
{
	uint8_t refresh = 0x00;

	if (!refresh_ccc_enabled) {
		return -EAGAIN;
	}

	if (callbacks && callbacks->refresh_requested) {
		callbacks->refresh_requested();
	}

	return bt_gatt_notify(conn, &scps_svc.attrs[4], &refresh, sizeof(refresh));
}
```

```groupb_impl_file
{
  "file_id": "scps_scan_policy_h",
  "filename": "scps_scan_policy.h",
  "relative_path": "samples/bluetooth/group_b/scps/src/scps_scan_policy.h",
  "language": "c",
  "purpose_he": "חוזה ה-scan policy: validation לערכים ושמירת state שמוכן להפעלה ע\"י האדפטר.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "scps_logic_scan_parameter_runtime_pattern_from_shorter_conn_intervals",
      "scps_logic_phase1_subset_write_and_refresh_split"
    ],
    "structure_ids": [
      "scps_structure_ncs_split_between_gatt_service_and_scan_runtime",
      "scps_structure_phase1_subset_service_and_scan_policy_split"
    ],
    "pattern_ids": ["10.1"]
  },
  "decision_notes_he": [
    "הקובץ הזה מחזיק policy, לא GATT.",
    "הוא מדבר במונחים של scan values ולא במונחים של attributes."
  ],
  "source_ids": [
    "nordic_ncs_sample_shorter_conn_intervals_main",
    "sig_scps_spec_page"
  ]
}
```
```c
#ifndef SAMPLES_BLUETOOTH_GROUP_B_SCPS_SRC_SCPS_SCAN_POLICY_H_
#define SAMPLES_BLUETOOTH_GROUP_B_SCPS_SRC_SCPS_SCAN_POLICY_H_

#include <stdbool.h>
#include "scps_service.h"

void scps_scan_policy_init(void);
bool scps_scan_policy_accept(const struct scps_written_window *params);
void scps_scan_policy_store(const struct scps_written_window *params);
const struct scps_written_window *scps_scan_policy_current(void);
bool scps_scan_policy_needs_refresh(void);
void scps_scan_policy_mark_refresh_sent(void);

#endif /* SAMPLES_BLUETOOTH_GROUP_B_SCPS_SRC_SCPS_SCAN_POLICY_H_ */
```

```groupb_impl_file
{
  "file_id": "scps_scan_policy_c",
  "filename": "scps_scan_policy.c",
  "relative_path": "samples/bluetooth/group_b/scps/src/scps_scan_policy.c",
  "language": "c",
  "purpose_he": "מימוש validation ושמירת state של Scan Interval Window, עם flag קטן ל-refresh pending.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "scps_logic_scan_parameter_runtime_pattern_from_shorter_conn_intervals",
      "scps_logic_phase1_subset_write_and_refresh_split"
    ],
    "structure_ids": [
      "scps_structure_ncs_split_between_gatt_service_and_scan_runtime"
    ],
    "pattern_ids": ["10.1"]
  },
  "decision_notes_he": [
    "אין כאן קריאות ישירות ל-bt_scan_*.",
    "ה-policy רק אומר מה הערכים התקפים ומה צריך לעשות אחר כך."
  ],
  "source_ids": [
    "nordic_ncs_sample_shorter_conn_intervals_main",
    "sig_scps_spec_page"
  ]
}
```
```c
#include <string.h>
#include "scps_scan_policy.h"

static struct scps_written_window current_values;
static bool refresh_pending;

void scps_scan_policy_init(void)
{
	memset(&current_values, 0, sizeof(current_values));
	refresh_pending = false;
}

bool scps_scan_policy_accept(const struct scps_written_window *params)
{
	return params && params->window <= params->interval && params->interval != 0U;
}

void scps_scan_policy_store(const struct scps_written_window *params)
{
	if (!params) {
		return;
	}

	current_values = *params;
	refresh_pending = true;
}

const struct scps_written_window *scps_scan_policy_current(void)
{
	return &current_values;
}

bool scps_scan_policy_needs_refresh(void)
{
	return refresh_pending;
}

void scps_scan_policy_mark_refresh_sent(void)
{
	refresh_pending = false;
}
```

```groupb_impl_file
{
  "file_id": "scps_app_adapter_h",
  "filename": "scps_app_adapter.h",
  "relative_path": "samples/bluetooth/group_b/scps/src/scps_app_adapter.h",
  "language": "c",
  "purpose_he": "חוזה האדפטר שמתרגם policy מאושר לפעולה runtime נפרדת.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "scps_logic_scan_parameter_runtime_pattern_from_shorter_conn_intervals"
    ],
    "structure_ids": [
      "scps_structure_ncs_split_between_gatt_service_and_scan_runtime"
    ],
    "pattern_ids": []
  },
  "decision_notes_he": [
    "ה-adapter הוא המקום היחיד שבו מותר לחבר את policy ל-runtime scan."
  ],
  "source_ids": [
    "nordic_ncs_sample_shorter_conn_intervals_main"
  ]
}
```
```c
#ifndef SAMPLES_BLUETOOTH_GROUP_B_SCPS_SRC_SCPS_APP_ADAPTER_H_
#define SAMPLES_BLUETOOTH_GROUP_B_SCPS_SRC_SCPS_APP_ADAPTER_H_

int scps_app_adapter_init(void);
int scps_app_adapter_apply_pending_policy(void);

#endif /* SAMPLES_BLUETOOTH_GROUP_B_SCPS_SRC_SCPS_APP_ADAPTER_H_ */
```

```groupb_impl_file
{
  "file_id": "scps_app_adapter_c",
  "filename": "scps_app_adapter.c",
  "relative_path": "samples/bluetooth/group_b/scps/src/scps_app_adapter.c",
  "language": "c",
  "purpose_he": "החיבור בין service callbacks לבין scan policy והפעלת runtime action מחוץ ל-write handler.",
  "confidence": "medium",
  "derived_from": {
    "logic_ids": [
      "scps_logic_phase1_subset_write_and_refresh_split",
      "scps_logic_scan_parameter_runtime_pattern_from_shorter_conn_intervals"
    ],
    "structure_ids": [
      "scps_structure_phase1_subset_service_and_scan_policy_split"
    ],
    "pattern_ids": []
  },
  "decision_notes_he": [
    "כאן נכון לשים work queue או callback ל-stack.",
    "ב-Phase 1 מספיק entry point אחד של apply_pending_policy."
  ],
  "source_ids": [
    "nordic_ncs_sample_shorter_conn_intervals_main",
    "ti_scanparamservice_doxygen_h"
  ]
}
```
```c
#include "scps_app_adapter.h"
#include "scps_scan_policy.h"
#include "scps_service.h"

static void on_interval_window_written(const struct scps_written_window *params)
{
	if (!scps_scan_policy_accept(params)) {
		return;
	}

	scps_scan_policy_store(params);
}

int scps_app_adapter_init(void)
{
	static const struct scps_service_callbacks callbacks = {
		.interval_window_written = on_interval_window_written,
	};

	scps_scan_policy_init();
	scps_service_init();
	scps_service_register_callbacks(&callbacks);
	return 0;
}

int scps_app_adapter_apply_pending_policy(void)
{
	if (!scps_scan_policy_needs_refresh()) {
		return 0;
	}

	/* Hook the scan runtime or a dedicated work queue in this path. */
	scps_scan_policy_mark_refresh_sent();
	return scps_service_request_refresh(NULL);
}
```

## החלטות מימוש

```groupb_impl_decision
{
  "id": "scps_impl_decision_split_service_and_policy",
  "title_he": "מפרידים בין service ל-scan policy",
  "decision_he": "`scps_service` מטפל רק ב-GATT plumbing וב-refresh notify, ו-`scps_scan_policy` מחזיק את ה-state וה-validation של הערכים.",
  "why_needed_he": "זה מונע write handlers כבדים ומכין קרקע להחלפת runtime policy בלי לשבור את קוד השירות.",
  "pattern_he": "refresh-flow",
  "applies_to_files": ["scps_service_c", "scps_scan_policy_c", "scps_app_adapter_c"],
  "tags": ["separation-of-concerns"],
  "confidence": "high",
  "source_ids": [
    "ti_scanparamservice_doxygen_c",
    "nordic_ncs_sample_shorter_conn_intervals_main"
  ]
}
```

```groupb_impl_decision
{
  "id": "scps_impl_decision_refresh_is_explicit",
  "title_he": "Scan Refresh נשאר trigger מפורש",
  "decision_he": "אין heuristic שמפעיל refresh לבד. הקריאה ל-`scps_service_request_refresh()` נעשית רק מה-adapter כשה-policy קובע שזה הזמן.",
  "why_needed_he": "כך אפשר להבין מי יזם refresh ולמנוע side effects לא צפויים בזמן write.",
  "pattern_he": "server-request",
  "applies_to_files": ["scps_service_h", "scps_service_c", "scps_app_adapter_c"],
  "tags": ["runtime-control", "phase1"],
  "confidence": "high",
  "source_ids": [
    "ti_scanparamservice_doxygen_h",
    "sig_scps_spec_page"
  ]
}
```

## מקורות

- `sig_scps_spec_page`
- `ti_scanparamservice_doxygen_h`
- `ti_scanparamservice_doxygen_c`
- `nordic_ncs_sample_shorter_conn_intervals_main`
