/*
 * Copyright (c) 2026 The Zephyr Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_SPS_H_
#define ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_SPS_H_

/**
 * @brief Scan Parameters Service (SPS)
 * @defgroup bt_sps Scan Parameters Service (SPS)
 * @ingroup bluetooth
 * @{
 *
 * [Experimental] Users should note that the APIs can change
 * as a part of ongoing development.
 */

#include <stdbool.h>
#include <stdint.h>

#include <zephyr/bluetooth/conn.h>
#include <zephyr/sys/slist.h>

#ifdef __cplusplus
extern "C" {
#endif

/** @brief Scan Refresh value used to request re-write of scan parameters. */
#define BT_SPS_SCAN_REFRESH_SERVER_REQUIRES_REFRESH 0x00U

/** @brief Scan Interval Window value container. */
struct bt_sps_scan_interval_window {
	uint16_t interval;
	uint16_t window;
};

/** @brief Scan Parameters Service callback structure. */
struct bt_sps_cb {
	/**
	 * @brief Called when Scan Interval Window is written by a client.
	 *
	 * @param conn Connection that performed the write.
	 * @param scan_interval_window Decoded value.
	 */
	void (*scan_interval_window_written)(struct bt_conn *conn,
					    const struct bt_sps_scan_interval_window
					    *scan_interval_window);

	/**
	 * @brief Called when Scan Refresh notification subscription changes.
	 *
	 * @param enabled True if notifications are enabled, false otherwise.
	 */
	void (*scan_refresh_ccc_changed)(bool enabled);

	/** Internal member to form a list of callbacks. */
	sys_snode_t _node;
};

/**
 * @brief Register SPS callbacks.
 *
 * @param cb Pointer to callback structure.
 *
 * @retval 0 If successfully registered.
 * @retval -EINVAL If @p cb is NULL.
 */
int bt_sps_cb_register(struct bt_sps_cb *cb);

/**
 * @brief Unregister SPS callbacks.
 *
 * @param cb Pointer to callback structure.
 *
 * @retval 0 If successfully unregistered.
 * @retval -EINVAL If @p cb is NULL.
 * @retval -ENOENT If @p cb is not registered.
 */
int bt_sps_cb_unregister(struct bt_sps_cb *cb);

/**
 * @brief Set locally stored Scan Interval Window value.
 *
 * @param scan_interval_window Pointer to value.
 *
 * @retval 0 If successful.
 * @retval -EINVAL If the value is invalid.
 */
int bt_sps_set_scan_interval_window(
	const struct bt_sps_scan_interval_window *scan_interval_window);

/**
 * @brief Get locally stored Scan Interval Window value.
 *
 * @param[out] scan_interval_window Output value pointer.
 *
 * @retval 0 If successful.
 * @retval -EINVAL If @p scan_interval_window is NULL.
 */
int bt_sps_get_scan_interval_window(
	struct bt_sps_scan_interval_window *scan_interval_window);

/**
 * @brief Send Scan Refresh notification.
 *
 * @param conn Connection to notify, or NULL for all subscribed peers.
 *
 * @retval 0 If notification was sent.
 * @retval -EACCES If Scan Refresh notifications are not enabled.
 * @retval -ENOTSUP If Scan Refresh characteristic is disabled.
 * @retval Negative errno from GATT layer on failure.
 */
int bt_sps_refresh_request(struct bt_conn *conn);

#ifdef __cplusplus
}
#endif

/**
 * @}
 */

#endif /* ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_SPS_H_ */
