/*
 * Copyright (c) 2026 The Zephyr Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_SCPS_H_
#define ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_SCPS_H_

/**
 * @brief Scan Parameters Service compatibility aliases (SCPS -> SPS)
 * @defgroup bt_scps Scan Parameters Service compatibility aliases
 * @ingroup bluetooth
 * @{
 */

#include <zephyr/bluetooth/services/sps.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef struct bt_sps_scan_interval_window bt_scps_scan_interval_window;
typedef struct bt_sps_cb bt_scps_cb;

#define BT_UUID_SCPS_VAL BT_UUID_SPS_VAL
#define BT_UUID_SCPS BT_UUID_SPS
#define BT_UUID_SCPS_SCAN_INTERVAL_WINDOW BT_UUID_GATT_SIW
#define BT_UUID_SCPS_SCAN_REFRESH BT_UUID_GATT_SR

#define BT_SCPS_SCAN_REFRESH_SERVER_REQUIRES_REFRESH \
	BT_SPS_SCAN_REFRESH_SERVER_REQUIRES_REFRESH

#define bt_scps_cb_register bt_sps_cb_register
#define bt_scps_cb_unregister bt_sps_cb_unregister
#define bt_scps_set_scan_interval_window bt_sps_set_scan_interval_window
#define bt_scps_get_scan_interval_window bt_sps_get_scan_interval_window
#define bt_scps_refresh_request bt_sps_refresh_request

#ifdef __cplusplus
}
#endif

/**
 * @}
 */

#endif /* ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_SCPS_H_ */
