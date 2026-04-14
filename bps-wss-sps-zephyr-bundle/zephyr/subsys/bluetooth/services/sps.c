/** @file
 *  @brief GATT Scan Parameters Service
 */

/*
 * Copyright (c) 2026 The Zephyr Project
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <errno.h>
#include <zephyr/init.h>
#include <zephyr/sys/byteorder.h>
#include <zephyr/sys/check.h>

#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/services/sps.h>

#define LOG_LEVEL CONFIG_BT_SPS_LOG_LEVEL
#include <zephyr/logging/log.h>
LOG_MODULE_REGISTER(sps);

#define BT_SPS_SCAN_INTERVAL_MIN 0x0004U
#define BT_SPS_SCAN_INTERVAL_MAX 0x4000U
#define BT_SPS_SCAN_WINDOW_MIN   0x0004U
#define BT_SPS_SCAN_WINDOW_MAX   0x4000U

enum sps_attr_index {
	SPS_ATTR_SVC,
	SPS_ATTR_SIW_CHRC,
	SPS_ATTR_SIW,
#if defined(CONFIG_BT_SPS_SCAN_REFRESH)
	SPS_ATTR_SR_CHRC,
	SPS_ATTR_SR,
	SPS_ATTR_SR_CCC,
#endif
};

static struct bt_sps_scan_interval_window sps_scan_interval_window;
static sys_slist_t sps_cbs = SYS_SLIST_STATIC_INIT(&sps_cbs);

#if defined(CONFIG_BT_SPS_SCAN_REFRESH)
static bool scan_refresh_ntf_ccc_enabled;
#endif

static bool scan_interval_window_valid(
	const struct bt_sps_scan_interval_window *scan_interval_window)
{
	if ((scan_interval_window->interval < BT_SPS_SCAN_INTERVAL_MIN) ||
	    (scan_interval_window->interval > BT_SPS_SCAN_INTERVAL_MAX)) {
		return false;
	}

	if ((scan_interval_window->window < BT_SPS_SCAN_WINDOW_MIN) ||
	    (scan_interval_window->window > BT_SPS_SCAN_WINDOW_MAX)) {
		return false;
	}

	return scan_interval_window->window <= scan_interval_window->interval;
}

static ssize_t write_siw(struct bt_conn *conn, const struct bt_gatt_attr *attr,
			 const void *buf, uint16_t len, uint16_t offset,
			 uint8_t flags)
{
	const uint8_t *value = buf;
	struct bt_sps_scan_interval_window siw;
	struct bt_sps_cb *listener;

	ARG_UNUSED(attr);
	ARG_UNUSED(flags);

	if (offset != 0U) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_OFFSET);
	}

	if (len != sizeof(siw)) {
		return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
	}

	siw.interval = sys_get_le16(value);
	siw.window = sys_get_le16(value + sizeof(uint16_t));

	if (!scan_interval_window_valid(&siw)) {
		return BT_GATT_ERR(BT_ATT_ERR_VALUE_NOT_ALLOWED);
	}

	sps_scan_interval_window = siw;

	LOG_DBG("SPS SIW update interval=0x%04x window=0x%04x",
		sps_scan_interval_window.interval, sps_scan_interval_window.window);

	SYS_SLIST_FOR_EACH_CONTAINER(&sps_cbs, listener, _node) {
		if (listener->scan_interval_window_written) {
			listener->scan_interval_window_written(conn,
				&sps_scan_interval_window);
		}
	}

	return len;
}

#if defined(CONFIG_BT_SPS_SCAN_REFRESH)
static void scan_refresh_ccc_cfg_changed(const struct bt_gatt_attr *attr,
					 uint16_t value)
{
	struct bt_sps_cb *listener;

	ARG_UNUSED(attr);

	scan_refresh_ntf_ccc_enabled = (value == BT_GATT_CCC_NOTIFY);

	LOG_INF("SPS scan refresh notifications %s",
		scan_refresh_ntf_ccc_enabled ? "enabled" : "disabled");

	SYS_SLIST_FOR_EACH_CONTAINER(&sps_cbs, listener, _node) {
		if (listener->scan_refresh_ccc_changed) {
			listener->scan_refresh_ccc_changed(
				scan_refresh_ntf_ccc_enabled);
		}
	}
}
#endif

BT_GATT_SERVICE_DEFINE(sps_svc,
	BT_GATT_PRIMARY_SERVICE(BT_UUID_SPS),
	BT_GATT_CHARACTERISTIC(BT_UUID_GATT_SIW,
			       BT_GATT_CHRC_WRITE_WITHOUT_RESP,
			       BT_GATT_PERM_WRITE,
			       NULL, write_siw, NULL),
#if defined(CONFIG_BT_SPS_SCAN_REFRESH)
	BT_GATT_CHARACTERISTIC(BT_UUID_GATT_SR,
			       BT_GATT_CHRC_NOTIFY,
			       BT_GATT_PERM_NONE,
			       NULL, NULL, NULL),
	BT_GATT_CCC(scan_refresh_ccc_cfg_changed,
		    BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
#endif
);

static int sps_init(void)
{
	sps_scan_interval_window.interval = BT_SPS_SCAN_INTERVAL_MIN;
	sps_scan_interval_window.window = BT_SPS_SCAN_WINDOW_MIN;
#if defined(CONFIG_BT_SPS_SCAN_REFRESH)
	scan_refresh_ntf_ccc_enabled = false;
#endif

	return 0;
}

int bt_sps_cb_register(struct bt_sps_cb *cb)
{
	CHECKIF(cb == NULL) {
		return -EINVAL;
	}

	sys_slist_append(&sps_cbs, &cb->_node);

	return 0;
}

int bt_sps_cb_unregister(struct bt_sps_cb *cb)
{
	CHECKIF(cb == NULL) {
		return -EINVAL;
	}

	if (!sys_slist_find_and_remove(&sps_cbs, &cb->_node)) {
		return -ENOENT;
	}

	return 0;
}

int bt_sps_set_scan_interval_window(
	const struct bt_sps_scan_interval_window *scan_interval_window)
{
	CHECKIF(scan_interval_window == NULL) {
		return -EINVAL;
	}

	if (!scan_interval_window_valid(scan_interval_window)) {
		return -EINVAL;
	}

	sps_scan_interval_window = *scan_interval_window;

	return 0;
}

int bt_sps_get_scan_interval_window(
	struct bt_sps_scan_interval_window *scan_interval_window)
{
	CHECKIF(scan_interval_window == NULL) {
		return -EINVAL;
	}

	*scan_interval_window = sps_scan_interval_window;

	return 0;
}

int bt_sps_refresh_request(struct bt_conn *conn)
{
#if defined(CONFIG_BT_SPS_SCAN_REFRESH)
	int rc;
	uint8_t scan_refresh = BT_SPS_SCAN_REFRESH_SERVER_REQUIRES_REFRESH;

	if (!scan_refresh_ntf_ccc_enabled) {
		return -EACCES;
	}

	rc = bt_gatt_notify(conn, &sps_svc.attrs[SPS_ATTR_SR],
			    &scan_refresh, sizeof(scan_refresh));

	return rc == -ENOTCONN ? 0 : rc;
#else
	ARG_UNUSED(conn);

	return -ENOTSUP;
#endif
}

SYS_INIT(sps_init, APPLICATION, CONFIG_APPLICATION_INIT_PRIORITY);
