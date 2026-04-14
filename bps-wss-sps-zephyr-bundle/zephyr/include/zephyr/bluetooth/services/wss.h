/*
 * Copyright (c) 2026 The Zephyr Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_WSS_H_
#define ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_WSS_H_

/**
 * @brief Weight Scale Service (WSS)
 * @defgroup bt_wss Weight Scale Service (WSS)
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

/** @brief Weight Scale Service callback structure. */
struct bt_wss_cb {
	/**
	 * @brief Weight Measurement indication subscription changed.
	 *
	 * @param enabled True if indications are enabled, false otherwise.
	 */
	void (*weight_meas_ccc_changed)(bool enabled);

	/**
	 * @brief Weight Measurement indication completed.
	 *
	 * @param conn Connection used for indication.
	 * @param err ATT status code (0 on success).
	 */
	void (*weight_meas_indicate_done)(struct bt_conn *conn, uint8_t err);

	/** Internal member to form a list of callbacks. */
	sys_snode_t _node;
};

/**
 * @brief Register WSS callbacks.
 *
 * @param cb Pointer to callback structure.
 *
 * @retval 0 If successfully registered.
 * @retval -EINVAL If @p cb is NULL.
 */
int bt_wss_cb_register(struct bt_wss_cb *cb);

/**
 * @brief Unregister WSS callbacks.
 *
 * @param cb Pointer to callback structure.
 *
 * @retval 0 If successfully unregistered.
 * @retval -EINVAL If @p cb is NULL.
 * @retval -ENOENT If @p cb is not registered.
 */
int bt_wss_cb_unregister(struct bt_wss_cb *cb);

/**
 * @brief Set Weight Scale Feature characteristic value.
 *
 * @param feature Encoded Weight Scale Feature bitfield.
 *
 * @retval 0 If successful.
 */
int bt_wss_set_feature(uint32_t feature);

/**
 * @brief Get Weight Scale Feature characteristic value.
 *
 * @return Encoded Weight Scale Feature bitfield.
 */
uint32_t bt_wss_get_feature(void);

/**
 * @brief Send Weight Measurement indication.
 *
 * @param conn Connection to indicate to, or NULL for all subscribed peers.
 * @param measurement Pointer to encoded Weight Measurement payload.
 * @param len Payload length.
 *
 * @retval 0 If indication was queued.
 * @retval -EINVAL If arguments are invalid.
 * @retval -EMSGSIZE If payload length exceeds configured maximum.
 * @retval -EACCES If indications are not enabled.
 * @retval -EBUSY If previous indication has not been confirmed yet.
 * @retval Negative errno from GATT layer on failure.
 */
int bt_wss_indicate(struct bt_conn *conn, const uint8_t *measurement,
		    uint16_t len);

#ifdef __cplusplus
}
#endif

/**
 * @}
 */

#endif /* ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_WSS_H_ */
