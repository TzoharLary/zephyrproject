/*
 * Copyright (c) 2026 The Zephyr Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_BPS_H_
#define ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_BPS_H_

/**
 * @brief Blood Pressure Service (BPS)
 * @defgroup bt_bps Blood Pressure Service (BPS)
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

/** @brief Blood Pressure Service callback structure. */
struct bt_bps_cb {
	/**
	 * @brief Blood Pressure Measurement indication subscription changed.
	 *
	 * @param enabled True if indications are enabled, false otherwise.
	 */
	void (*bp_meas_ccc_changed)(bool enabled);

	/**
	 * @brief Intermediate Cuff Pressure notification subscription changed.
	 *
	 * @param enabled True if notifications are enabled, false otherwise.
	 */
	void (*intermediate_cuff_pressure_ccc_changed)(bool enabled);

	/**
	 * @brief Blood Pressure Measurement indication completed.
	 *
	 * @param conn Connection used for indication.
	 * @param err ATT status code (0 on success).
	 */
	void (*bp_meas_indicate_done)(struct bt_conn *conn, uint8_t err);

	/** Internal member to form a list of callbacks. */
	sys_snode_t _node;
};

/**
 * @brief Register BPS callbacks.
 *
 * @param cb Pointer to callback structure.
 *
 * @retval 0 If successfully registered.
 * @retval -EINVAL If @p cb is NULL.
 */
int bt_bps_cb_register(struct bt_bps_cb *cb);

/**
 * @brief Unregister BPS callbacks.
 *
 * @param cb Pointer to callback structure.
 *
 * @retval 0 If successfully unregistered.
 * @retval -EINVAL If @p cb is NULL.
 * @retval -ENOENT If @p cb is not registered.
 */
int bt_bps_cb_unregister(struct bt_bps_cb *cb);

/**
 * @brief Set Blood Pressure Feature characteristic value.
 *
 * @param feature Encoded Blood Pressure Feature bitfield.
 *
 * @retval 0 If successful.
 */
int bt_bps_set_feature(uint16_t feature);

/**
 * @brief Get Blood Pressure Feature characteristic value.
 *
 * @return Encoded Blood Pressure Feature bitfield.
 */
uint16_t bt_bps_get_feature(void);

/**
 * @brief Send Blood Pressure Measurement indication.
 *
 * @param conn Connection to indicate to, or NULL for all subscribed peers.
 * @param measurement Pointer to encoded Blood Pressure Measurement payload.
 * @param len Payload length.
 *
 * @retval 0 If indication was queued.
 * @retval -EINVAL If arguments are invalid.
 * @retval -EMSGSIZE If payload length exceeds configured maximum.
 * @retval -EACCES If indications are not enabled.
 * @retval -EBUSY If previous indication has not been confirmed yet.
 * @retval Negative errno from GATT layer on failure.
 */
int bt_bps_indicate(struct bt_conn *conn, const uint8_t *measurement,
		    uint16_t len);

/**
 * @brief Send Intermediate Cuff Pressure notification.
 *
 * @param conn Connection to notify, or NULL for all subscribed peers.
 * @param measurement Pointer to encoded Intermediate Cuff Pressure payload.
 * @param len Payload length.
 *
 * @retval 0 If notification was sent.
 * @retval -EINVAL If arguments are invalid.
 * @retval -EMSGSIZE If payload length exceeds configured maximum.
 * @retval -EACCES If notifications are not enabled.
 * @retval -ENOTSUP If Intermediate Cuff Pressure characteristic is disabled.
 * @retval Negative errno from GATT layer on failure.
 */
int bt_bps_notify_intermediate_cuff(struct bt_conn *conn,
				    const uint8_t *measurement,
				    uint16_t len);

#ifdef __cplusplus
}
#endif

/**
 * @}
 */

#endif /* ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_BPS_H_ */