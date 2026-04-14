/** @file
 *  @brief GATT Weight Scale Service
 */

/*
 * Copyright (c) 2026 The Zephyr Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <errno.h>
#include <string.h>
#include <zephyr/init.h>
#include <zephyr/sys/check.h>

#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/services/wss.h>

#define LOG_LEVEL CONFIG_BT_WSS_LOG_LEVEL
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(wss);

enum wss_attr_index {
	WSS_ATTR_SVC,
	WSS_ATTR_WM_CHRC,
	WSS_ATTR_WM,
	WSS_ATTR_WM_CCC,
	WSS_ATTR_WSF_CHRC,
	WSS_ATTR_WSF,
};

static uint32_t wss_feature;
static bool weight_meas_ind_ccc_enabled;
static sys_slist_t wss_cbs = SYS_SLIST_STATIC_INIT(&wss_cbs);

static struct {
	struct bt_gatt_indicate_params params;
	uint8_t value[CONFIG_BT_WSS_MEAS_MAX_LEN];
	bool in_progress;
} weight_meas_ind;

static void weight_meas_ccc_cfg_changed(const struct bt_gatt_attr *attr,
					uint16_t value)
{
	struct bt_wss_cb *listener;

	ARG_UNUSED(attr);

	weight_meas_ind_ccc_enabled = (value == BT_GATT_CCC_INDICATE);

	LOG_INF("WSS measurement indications %s",
		weight_meas_ind_ccc_enabled ? "enabled" : "disabled");

	SYS_SLIST_FOR_EACH_CONTAINER(&wss_cbs, listener, _node) {
		if (listener->weight_meas_ccc_changed) {
			listener->weight_meas_ccc_changed(weight_meas_ind_ccc_enabled);
		}
	}
}

static ssize_t read_wsf(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			     void *buf, uint16_t len, uint16_t offset)
{
	ARG_UNUSED(attr);

	return bt_gatt_attr_read(conn, attr, buf, len, offset, &wss_feature,
				 sizeof(wss_feature));
}

static void weight_meas_indicate_cb(struct bt_conn *conn,
				    struct bt_gatt_indicate_params *params,
				    uint8_t err)
{
	struct bt_wss_cb *listener;

	ARG_UNUSED(params);

	weight_meas_ind.in_progress = false;

	SYS_SLIST_FOR_EACH_CONTAINER(&wss_cbs, listener, _node) {
		if (listener->weight_meas_indicate_done) {
			listener->weight_meas_indicate_done(conn, err);
		}
	}
}

BT_GATT_SERVICE_DEFINE(wss_svc,
	BT_GATT_PRIMARY_SERVICE(BT_UUID_WSS),
	BT_GATT_CHARACTERISTIC(BT_UUID_GATT_WM,
			       BT_GATT_CHRC_INDICATE,
			       BT_GATT_PERM_NONE,
			       NULL, NULL, NULL),
	BT_GATT_CCC(weight_meas_ccc_cfg_changed,
		    BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
	BT_GATT_CHARACTERISTIC(BT_UUID_GATT_WSF,
			       BT_GATT_CHRC_READ,
			       BT_GATT_PERM_READ,
			       read_wsf, NULL, NULL),
);

static int wss_init(void)
{
	wss_feature = 0U;
	weight_meas_ind.in_progress = false;
	weight_meas_ind_ccc_enabled = false;

	return 0;
}

int bt_wss_cb_register(struct bt_wss_cb *cb)
{
	CHECKIF(cb == NULL) {
		return -EINVAL;
	}

	sys_slist_append(&wss_cbs, &cb->_node);

	return 0;
}

int bt_wss_cb_unregister(struct bt_wss_cb *cb)
{
	CHECKIF(cb == NULL) {
		return -EINVAL;
	}

	if (!sys_slist_find_and_remove(&wss_cbs, &cb->_node)) {
		return -ENOENT;
	}

	return 0;
}

int bt_wss_set_feature(uint32_t feature)
{
	wss_feature = feature;

	return 0;
}

uint32_t bt_wss_get_feature(void)
{
	return wss_feature;
}

int bt_wss_indicate(struct bt_conn *conn, const uint8_t *measurement,
		    uint16_t len)
{
	int rc;

	CHECKIF((measurement == NULL) || (len == 0U)) {
		return -EINVAL;
	}

	if (len > CONFIG_BT_WSS_MEAS_MAX_LEN) {
		return -EMSGSIZE;
	}

	if (!weight_meas_ind_ccc_enabled) {
		return -EACCES;
	}

	if (weight_meas_ind.in_progress) {
		return -EBUSY;
	}

	memcpy(weight_meas_ind.value, measurement, len);

	weight_meas_ind.params.attr = &wss_svc.attrs[WSS_ATTR_WM];
	weight_meas_ind.params.func = weight_meas_indicate_cb;
	weight_meas_ind.params.destroy = NULL;
	weight_meas_ind.params.data = weight_meas_ind.value;
	weight_meas_ind.params.len = len;

	weight_meas_ind.in_progress = true;
	rc = bt_gatt_indicate(conn, &weight_meas_ind.params);
	if (rc != 0) {
		weight_meas_ind.in_progress = false;
	}

	return rc;
}

SYS_INIT(wss_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
