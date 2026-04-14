/** @file
 *  @brief GATT Blood Pressure Service
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
#include <zephyr/bluetooth/services/bps.h>

#define LOG_LEVEL CONFIG_BT_BPS_LOG_LEVEL
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(bps);

enum bps_attr_index {
	BPS_ATTR_SVC,
	BPS_ATTR_BPM_CHRC,
	BPS_ATTR_BPM,
	BPS_ATTR_BPM_CCC,
#if defined(CONFIG_BT_BPS_INTERMEDIATE_CUFF_PRESSURE)
	BPS_ATTR_ICP_CHRC,
	BPS_ATTR_ICP,
	BPS_ATTR_ICP_CCC,
#endif
	BPS_ATTR_BPF_CHRC,
	BPS_ATTR_BPF,
};

static uint16_t bps_feature;
static bool bp_meas_ind_ccc_enabled;
#if defined(CONFIG_BT_BPS_INTERMEDIATE_CUFF_PRESSURE)
static bool intermediate_cuff_pressure_ntf_ccc_enabled;
#endif
static sys_slist_t bps_cbs = SYS_SLIST_STATIC_INIT(&bps_cbs);

static struct {
	struct bt_gatt_indicate_params params;
	uint8_t value[CONFIG_BT_BPS_MEAS_MAX_LEN];
	bool in_progress;
} bp_meas_ind;

static void bp_meas_ccc_cfg_changed(const struct bt_gatt_attr *attr,
				    uint16_t value)
{
	struct bt_bps_cb *listener;

	ARG_UNUSED(attr);

	bp_meas_ind_ccc_enabled = (value == BT_GATT_CCC_INDICATE);

	LOG_INF("BPS measurement indications %s",
		bp_meas_ind_ccc_enabled ? "enabled" : "disabled");

	SYS_SLIST_FOR_EACH_CONTAINER(&bps_cbs, listener, _node) {
		if (listener->bp_meas_ccc_changed) {
			listener->bp_meas_ccc_changed(bp_meas_ind_ccc_enabled);
		}
	}
}

#if defined(CONFIG_BT_BPS_INTERMEDIATE_CUFF_PRESSURE)
static void intermediate_cuff_pressure_ccc_cfg_changed(const struct bt_gatt_attr *attr,
						uint16_t value)
{
	struct bt_bps_cb *listener;

	ARG_UNUSED(attr);

	intermediate_cuff_pressure_ntf_ccc_enabled = (value == BT_GATT_CCC_NOTIFY);

	LOG_INF("BPS intermediate cuff pressure notifications %s",
		intermediate_cuff_pressure_ntf_ccc_enabled ? "enabled" : "disabled");

	SYS_SLIST_FOR_EACH_CONTAINER(&bps_cbs, listener, _node) {
		if (listener->intermediate_cuff_pressure_ccc_changed) {
			listener->intermediate_cuff_pressure_ccc_changed(
				intermediate_cuff_pressure_ntf_ccc_enabled);
		}
	}
}
#endif

static ssize_t read_bpf(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			     void *buf, uint16_t len, uint16_t offset)
{
	ARG_UNUSED(attr);

	return bt_gatt_attr_read(conn, attr, buf, len, offset, &bps_feature,
				 sizeof(bps_feature));
}

static void bp_meas_indicate_cb(struct bt_conn *conn,
				struct bt_gatt_indicate_params *params,
				uint8_t err)
{
	struct bt_bps_cb *listener;

	ARG_UNUSED(params);

	bp_meas_ind.in_progress = false;

	SYS_SLIST_FOR_EACH_CONTAINER(&bps_cbs, listener, _node) {
		if (listener->bp_meas_indicate_done) {
			listener->bp_meas_indicate_done(conn, err);
		}
	}
}

BT_GATT_SERVICE_DEFINE(bps_svc,
	BT_GATT_PRIMARY_SERVICE(BT_UUID_BPS),
	BT_GATT_CHARACTERISTIC(BT_UUID_GATT_BPM,
			       BT_GATT_CHRC_INDICATE,
			       BT_GATT_PERM_NONE,
			       NULL, NULL, NULL),
	BT_GATT_CCC(bp_meas_ccc_cfg_changed,
		    BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
#if defined(CONFIG_BT_BPS_INTERMEDIATE_CUFF_PRESSURE)
	BT_GATT_CHARACTERISTIC(BT_UUID_GATT_ICP,
			       BT_GATT_CHRC_NOTIFY,
			       BT_GATT_PERM_NONE,
			       NULL, NULL, NULL),
	BT_GATT_CCC(intermediate_cuff_pressure_ccc_cfg_changed,
		    BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
#endif
	BT_GATT_CHARACTERISTIC(BT_UUID_GATT_BPF,
			       BT_GATT_CHRC_READ,
			       BT_GATT_PERM_READ,
			       read_bpf, NULL, NULL),
);

static int bps_init(void)
{
	bps_feature = 0U;
	bp_meas_ind.in_progress = false;
	bp_meas_ind_ccc_enabled = false;
#if defined(CONFIG_BT_BPS_INTERMEDIATE_CUFF_PRESSURE)
	intermediate_cuff_pressure_ntf_ccc_enabled = false;
#endif

	return 0;
}

int bt_bps_cb_register(struct bt_bps_cb *cb)
{
	CHECKIF(cb == NULL) {
		return -EINVAL;
	}

	sys_slist_append(&bps_cbs, &cb->_node);

	return 0;
}

int bt_bps_cb_unregister(struct bt_bps_cb *cb)
{
	CHECKIF(cb == NULL) {
		return -EINVAL;
	}

	if (!sys_slist_find_and_remove(&bps_cbs, &cb->_node)) {
		return -ENOENT;
	}

	return 0;
}

int bt_bps_set_feature(uint16_t feature)
{
	bps_feature = feature;

	return 0;
}

uint16_t bt_bps_get_feature(void)
{
	return bps_feature;
}

int bt_bps_indicate(struct bt_conn *conn, const uint8_t *measurement,
		    uint16_t len)
{
	int rc;

	CHECKIF((measurement == NULL) || (len == 0U)) {
		return -EINVAL;
	}

	if (len > CONFIG_BT_BPS_MEAS_MAX_LEN) {
		return -EMSGSIZE;
	}

	if (!bp_meas_ind_ccc_enabled) {
		return -EACCES;
	}

	if (bp_meas_ind.in_progress) {
		return -EBUSY;
	}

	memcpy(bp_meas_ind.value, measurement, len);

	bp_meas_ind.params.attr = &bps_svc.attrs[BPS_ATTR_BPM];
	bp_meas_ind.params.func = bp_meas_indicate_cb;
	bp_meas_ind.params.destroy = NULL;
	bp_meas_ind.params.data = bp_meas_ind.value;
	bp_meas_ind.params.len = len;

	bp_meas_ind.in_progress = true;
	rc = bt_gatt_indicate(conn, &bp_meas_ind.params);
	if (rc != 0) {
		bp_meas_ind.in_progress = false;
	}

	return rc;
}

int bt_bps_notify_intermediate_cuff(struct bt_conn *conn,
				    const uint8_t *measurement,
				    uint16_t len)
{
#if defined(CONFIG_BT_BPS_INTERMEDIATE_CUFF_PRESSURE)
	int rc;

	CHECKIF((measurement == NULL) || (len == 0U)) {
		return -EINVAL;
	}

	if (len > CONFIG_BT_BPS_ICP_MAX_LEN) {
		return -EMSGSIZE;
	}

	if (!intermediate_cuff_pressure_ntf_ccc_enabled) {
		return -EACCES;
	}

	rc = bt_gatt_notify(conn, &bps_svc.attrs[BPS_ATTR_ICP], measurement, len);

	return rc == -ENOTCONN ? 0 : rc;
#else
	ARG_UNUSED(conn);
	ARG_UNUSED(measurement);
	ARG_UNUSED(len);

	return -ENOTSUP;
#endif
}

SYS_INIT(bps_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
