# Zephyr BLE GATT Profile Patterns
# ===================================
# Static knowledge base containing pre-researched, permanent knowledge
# about Zephyr BLE GATT profile patterns. This does NOT need to be
# re-researched at runtime — it is loaded once and used for all generation.
#
# Contents:
# 1. Simple Profile Pattern (h + c + Kconfig)
# 2. Complex Profile Pattern
# 3. Characteristic Types Reference
# 4. Kconfig Patterns
# 5. CMakeLists.txt Integration
# 6. UUID Definition Patterns
# 7. Logging Patterns
# 8. Pattern Selection Guide
# 9. Common Mistakes to Avoid
# 10. Phase 1 Discovered Patterns (added from spec analysis of docs/profiles/)

---

## 1. Simple Profile Pattern

A **Simple Profile** has:
- One or a few characteristics
- No persistent state machine
- Straightforward callback structure
- Low–Medium complexity

**Reference implementation:** Heart Rate Service (`hrs.c` / `hrs.h`)

---

### 1.1 Header File Pattern (`.h`)

```c
/*
 * Copyright (c) 20XX <Author>
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * @file
 * @defgroup bt_<profile> Bluetooth <Profile Name> Service API
 * @{
 * @brief API for the Bluetooth <Profile Name> Service (<PROFILE_ID>).
 */

#ifndef ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_<PROFILE>_H_
#define ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_<PROFILE>_H_

#include <stdint.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>

#ifdef __cplusplus
extern "C" {
#endif

/** @brief <Profile Name> Service UUID (0x<XXXX>) */
#define BT_UUID_<PROFILE>_VAL          0x<XXXX>
#define BT_UUID_<PROFILE>              BT_UUID_DECLARE_16(BT_UUID_<PROFILE>_VAL)

/** @brief <Characteristic Name> Characteristic UUID (0x<XXXX>) */
#define BT_UUID_<PROFILE>_<CHAR>_VAL   0x<XXXX>
#define BT_UUID_<PROFILE>_<CHAR>       BT_UUID_DECLARE_16(BT_UUID_<PROFILE>_<CHAR>_VAL)

/**
 * @brief Callback type for <characteristic> changes.
 *
 * @param[in] <param>  Description of parameter.
 */
typedef void (*bt_<profile>_<char>_cb_t)(<param_type> <param>);

/**
 * @brief Register <Profile Name> Service callbacks.
 *
 * @param[in] cb  Pointer to callback structure.
 *
 * @retval 0       If successfully registered.
 * @retval -EINVAL If @p cb is NULL.
 */
int bt_<profile>_cb_register(bt_<profile>_<char>_cb_t cb);

/**
 * @brief Send <characteristic> notification.
 *
 * @param[in] conn  Pointer to connection (NULL for all connected peers).
 * @param[in] value Value to send.
 *
 * @retval 0          If notification sent successfully.
 * @retval -ENOTCONN  If no active connection.
 * @retval -EINVAL    If invalid parameter.
 */
int bt_<profile>_notify(struct bt_conn *conn, uint<N>_t value);

#ifdef __cplusplus
}
#endif

/**
 * @}
 */

#endif /* ZEPHYR_INCLUDE_BLUETOOTH_SERVICES_<PROFILE>_H_ */
```

---

### 1.2 Implementation File Pattern (`.c`) — Notify

```c
/*
 * Copyright (c) 20XX <Author>
 * SPDX-License-Identifier: Apache-2.0
 */

#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/services/<profile>.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(bt_<profile>, CONFIG_BT_<PROFILE>_LOG_LEVEL);

/* Registered user callback */
static bt_<profile>_<char>_cb_t <char>_cb;

/* CCC changed callback — called when client enables/disables notifications */
static void <char>_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    bool notif_enabled = (value == BT_GATT_CCC_NOTIFY);

    LOG_DBG("<Characteristic> notifications %s", notif_enabled ? "enabled" : "disabled");

    if (<char>_cb) {
        <char>_cb(notif_enabled);
    }
}

/* GATT Service Definition */
BT_GATT_SERVICE_DEFINE(bt_<profile>_svc,
    /* Service Declaration */
    BT_GATT_PRIMARY_SERVICE(BT_UUID_<PROFILE>),

    /* <Characteristic> Characteristic — Notify */
    BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_<CHAR>,
                           BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_NONE,
                           NULL, NULL, NULL),
    /* Client Characteristic Configuration Descriptor (CCCD) */
    BT_GATT_CCC(<char>_ccc_cfg_changed,
                BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);

/* Public API */
int bt_<profile>_cb_register(bt_<profile>_<char>_cb_t cb)
{
    if (!cb) {
        return -EINVAL;
    }

    <char>_cb = cb;
    return 0;
}

int bt_<profile>_notify(struct bt_conn *conn, uint<N>_t value)
{
    int rc;

    /* attrs[0]=service decl, attrs[1]=char decl, attrs[2]=char value — target value attr */
    rc = bt_gatt_notify(conn, &bt_<profile>_svc.attrs[2], &value, sizeof(value));
    return rc == -ENOTCONN ? 0 : rc;
}
```

---

### 1.3 Implementation File Pattern (`.c`) — Read Only

```c
/* Read-only characteristic handler */
static ssize_t read_<char>(struct bt_conn *conn,
                            const struct bt_gatt_attr *attr,
                            void *buf, uint16_t len, uint16_t offset)
{
    uint<N>_t value = get_<char>_value();  /* retrieve current value */

    return bt_gatt_attr_read(conn, attr, buf, len, offset, &value, sizeof(value));
}

/* GATT Service Definition — Read Only */
BT_GATT_SERVICE_DEFINE(bt_<profile>_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_<PROFILE>),

    /* <Characteristic> — Read */
    BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_<CHAR>,
                           BT_GATT_CHRC_READ,
                           BT_GATT_PERM_READ,
                           read_<char>, NULL, NULL),
);
```

---

### 1.4 Implementation File Pattern (`.c`) — Write

```c
/* Write characteristic handler */
static ssize_t write_<char>(struct bt_conn *conn,
                             const struct bt_gatt_attr *attr,
                             const void *buf, uint16_t len,
                             uint16_t offset, uint8_t flags)
{
    uint<N>_t value;

    if (offset + len > sizeof(value)) {
        return BT_GATT_ERR(BT_ATT_ERR_INVALID_OFFSET);
    }

    /* Use byte pointer for offset arithmetic — pointer arithmetic on typed pointer
     * is in units of the type size, not bytes, and can silently bypass bounds check */
    uint8_t *dst = (uint8_t *)&value;

    memcpy(dst + offset, buf, len);
    process_<char>_write(value);

    return len;
}

/* GATT Service Definition — Write */
BT_GATT_SERVICE_DEFINE(bt_<profile>_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_<PROFILE>),

    /* <Characteristic> — Write */
    BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_<CHAR>,
                           BT_GATT_CHRC_WRITE | BT_GATT_CHRC_WRITE_WITHOUT_RESP,
                           BT_GATT_PERM_WRITE,
                           NULL, write_<char>, NULL),
);
```

---

### 1.5 Kconfig Pattern — Simple Profile

```kconfig
# <Profile Name> Service
config BT_<PROFILE>
    bool "Bluetooth <Profile Name> Service"
    depends on BT_PERIPHERAL
    help
      Enable the Bluetooth <Profile Name> Service (<PROFILE_ID>).
      This service implements the Bluetooth SIG <Profile Name> Service
      specification (UUID: 0x<XXXX>).

if BT_<PROFILE>

config BT_<PROFILE>_LOG_LEVEL
    int "Log level for <Profile Name> Service"
    depends on LOG
    default 3
    range 0 4
    help
      Set log level for the Bluetooth <Profile Name> Service.
      Levels are:
      - 0: OFF
      - 1: ERR
      - 2: WRN
      - 3: INF
      - 4: DBG

endif # BT_<PROFILE>
```

---

## 2. Complex Profile Pattern

A **Complex Profile** has:
- Multiple characteristics with different properties
- Persistent state machine (connection tracking, operational states)
- CCC handling for multiple characteristics
- Security and permission levels
- Connection/disconnection callbacks

**Reference implementations:**
- HIDS (`hids.c`) — full state machine, boot/report mode
- OTS (`ots.c`) — L2CAP COC, object management state machine

---

### 2.1 State Machine Structure

```c
/* Connection state tracking */
struct bt_<profile>_conn_state {
    struct bt_conn *conn;
    bool <feature>_enabled;
    uint8_t protocol_mode;
    /* ... other per-connection state ... */
};

/* Global service state */
static struct {
    bt_<profile>_<char>_cb_t cb;
    struct bt_<profile>_conn_state conn_state[CONFIG_BT_MAX_CONN];
    bool initialized;
    uint8_t current_<state>;
} bt_<profile>_ctx;

/* Connection management */
static void connected(struct bt_conn *conn, uint8_t err)
{
    struct bt_<profile>_conn_state *state;

    if (err) {
        return;
    }

    state = get_conn_state(conn);
    if (!state) {
        LOG_WRN("No free connection state slot");
        return;
    }

    state->conn = bt_conn_ref(conn);
    /* Initialize connection state */
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    struct bt_<profile>_conn_state *state = get_conn_state(conn);

    if (!state) {
        return;
    }

    bt_conn_unref(state->conn);
    state->conn = NULL;
    /* Reset connection state */
}

BT_CONN_CB_DEFINE(<profile>_conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};
```

---

### 2.2 Multiple Characteristic Handling

```c
/* Multiple characteristics in one service */
BT_GATT_SERVICE_DEFINE(bt_<profile>_svc,
    BT_GATT_PRIMARY_SERVICE(BT_UUID_<PROFILE>),

    /* Characteristic 1 — Read */
    BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_<CHAR1>,
                           BT_GATT_CHRC_READ,
                           BT_GATT_PERM_READ_ENCRYPT,
                           read_<char1>, NULL, NULL),

    /* Characteristic 2 — Notify with CCC */
    BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_<CHAR2>,
                           BT_GATT_CHRC_NOTIFY,
                           BT_GATT_PERM_NONE,
                           NULL, NULL, NULL),
    BT_GATT_CCC(<char2>_ccc_cfg_changed,
                BT_GATT_PERM_READ | BT_GATT_PERM_WRITE_ENCRYPT),

    /* Characteristic 3 — Write with authentication */
    BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_<CHAR3>,
                           BT_GATT_CHRC_WRITE,
                           BT_GATT_PERM_WRITE_AUTHEN,
                           NULL, write_<char3>, NULL),

    /* Characteristic 4 — Indicate with CCC */
    BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_<CHAR4>,
                           BT_GATT_CHRC_INDICATE,
                           BT_GATT_PERM_NONE,
                           NULL, NULL, NULL),
    BT_GATT_CCC(<char4>_ccc_cfg_changed,
                BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);

/* Attribute index constants — track positions for notify/indicate */
enum {
    BT_<PROFILE>_ATTR_SVC,          /* 0: Service declaration */
    BT_<PROFILE>_ATTR_<CHAR1>_CHRC, /* 1: Characteristic declaration */
    BT_<PROFILE>_ATTR_<CHAR1>,      /* 2: Characteristic value */
    BT_<PROFILE>_ATTR_<CHAR2>_CHRC, /* 3 */
    BT_<PROFILE>_ATTR_<CHAR2>,      /* 4 */
    BT_<PROFILE>_ATTR_<CHAR2>_CCC,  /* 5: CCC descriptor */
    /* ... */
    BT_<PROFILE>_ATTR_COUNT,
};
```

---

### 2.3 Indicate Pattern (Acknowledged Notification)

```c
/* Indicate send state */
static struct bt_gatt_indicate_params indicate_params;
static K_SEM_DEFINE(indicate_sem, 0, 1);

/* Indicate complete callback */
static void indicate_cb(struct bt_conn *conn,
                        struct bt_gatt_indicate_params *params,
                        uint8_t err)
{
    LOG_DBG("Indicate %s (err %u)",
            err == 0U ? "success" : "failed", err);
    k_sem_give(&indicate_sem);
}

/* Send indication */
int bt_<profile>_indicate(struct bt_conn *conn, const void *data, size_t len)
{
    int rc;

    indicate_params.attr = &bt_<profile>_svc.attrs[BT_<PROFILE>_ATTR_<CHAR>];
    indicate_params.func = indicate_cb;
    indicate_params.destroy = NULL;
    indicate_params.data = data;
    indicate_params.len = len;

    rc = bt_gatt_indicate(conn, &indicate_params);
    if (rc == 0) {
        k_sem_take(&indicate_sem, K_FOREVER);
    }

    return rc;
}
```

---

### 2.4 Permission Levels Reference

```c
/* No permission required (for notify/indicate value attributes) */
BT_GATT_PERM_NONE

/* Read permission levels */
BT_GATT_PERM_READ              /* Any connected device can read */
BT_GATT_PERM_READ_ENCRYPT      /* Requires encrypted connection */
BT_GATT_PERM_READ_AUTHEN       /* Requires authenticated (bonded) connection */

/* Write permission levels */
BT_GATT_PERM_WRITE             /* Any connected device can write */
BT_GATT_PERM_WRITE_ENCRYPT     /* Requires encrypted connection */
BT_GATT_PERM_WRITE_AUTHEN      /* Requires authenticated (bonded) connection */

/* Prepare write (for long writes) */
BT_GATT_PERM_PREPARE_WRITE
```

---

## 3. Characteristic Types Reference

### 3.1 Read-Only Characteristic

```c
/* Characteristic with static or computed read value */
static ssize_t read_<char>(struct bt_conn *conn,
                            const struct bt_gatt_attr *attr,
                            void *buf, uint16_t len, uint16_t offset)
{
    const void *value = attr->user_data;  /* or compute dynamically */
    uint16_t value_len = sizeof(<type>);

    return bt_gatt_attr_read(conn, attr, buf, len, offset, value, value_len);
}

/* In service definition: */
BT_GATT_CHARACTERISTIC(uuid, BT_GATT_CHRC_READ, BT_GATT_PERM_READ,
                        read_<char>, NULL, &<data>),
```

### 3.2 Write Characteristic

```c
/* Standard write handler */
static ssize_t write_<char>(struct bt_conn *conn,
                             const struct bt_gatt_attr *attr,
                             const void *buf, uint16_t len,
                             uint16_t offset, uint8_t flags)
{
    /* Validate length */
    if (len != sizeof(<expected_type>)) {
        return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
    }

    if (offset != 0) {
        return BT_GATT_ERR(BT_ATT_ERR_INVALID_OFFSET);
    }

    /* Process the write */
    memcpy(&<storage>, buf, len);
    handle_<char>_write(&<storage>);

    return len;
}

/* In service definition: */
BT_GATT_CHARACTERISTIC(uuid, BT_GATT_CHRC_WRITE, BT_GATT_PERM_WRITE,
                        NULL, write_<char>, NULL),
```

### 3.3 Write Without Response Characteristic

```c
/* Write-without-response does not require response,
 * but the write handler still executes */
static ssize_t write_wo_<char>(struct bt_conn *conn,
                                const struct bt_gatt_attr *attr,
                                const void *buf, uint16_t len,
                                uint16_t offset, uint8_t flags)
{
    /* No response expected — just process and return len */
    memcpy(&<storage>, buf, MIN(len, sizeof(<storage>)));
    handle_<char>_write();
    return len;
}

/* In service definition: */
BT_GATT_CHARACTERISTIC(uuid,
                        BT_GATT_CHRC_WRITE_WITHOUT_RESP,
                        BT_GATT_PERM_WRITE,
                        NULL, write_wo_<char>, NULL),
```

### 3.4 Notify Characteristic

```c
/* Notify: server pushes data to client without acknowledgment */

/* CCC changed callback */
static void <char>_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    bool enabled = (value == BT_GATT_CCC_NOTIFY);
    LOG_DBG("Notifications %s", enabled ? "enabled" : "disabled");
    /* Store subscription state per connection if needed */
}

/* In service definition: */
BT_GATT_CHARACTERISTIC(uuid, BT_GATT_CHRC_NOTIFY, BT_GATT_PERM_NONE,
                        NULL, NULL, NULL),
BT_GATT_CCC(<char>_ccc_cfg_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),

/* Sending a notification: */
int send_<char>_notification(struct bt_conn *conn, const void *data, size_t len)
{
    /* Get the characteristic attribute (position after service + chrc_decl) */
    const struct bt_gatt_attr *attr = &bt_<profile>_svc.attrs[<CHAR_ATTR_INDEX>];

    int rc = bt_gatt_notify(conn, attr, data, len);
    return (rc == -ENOTCONN) ? 0 : rc;
}
```

### 3.5 Indicate Characteristic

```c
/* Indicate: server pushes data to client WITH acknowledgment.
 * Client must confirm receipt before next indication can be sent. */

static void <char>_ccc_cfg_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
    bool enabled = (value == BT_GATT_CCC_INDICATE);
    LOG_DBG("Indications %s", enabled ? "enabled" : "disabled");
}

/* In service definition: */
BT_GATT_CHARACTERISTIC(uuid, BT_GATT_CHRC_INDICATE, BT_GATT_PERM_NONE,
                        NULL, NULL, NULL),
BT_GATT_CCC(<char>_ccc_cfg_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
```

### 3.6 Mixed Characteristic (Read + Write + Notify)

```c
/* A characteristic that supports Read, Write, AND Notify */
BT_GATT_CHARACTERISTIC(uuid,
                        BT_GATT_CHRC_READ | BT_GATT_CHRC_WRITE | BT_GATT_CHRC_NOTIFY,
                        BT_GATT_PERM_READ | BT_GATT_PERM_WRITE,
                        read_<char>, write_<char>, &<storage>),
BT_GATT_CCC(<char>_ccc_cfg_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
```

---

## 4. Kconfig Patterns

### 4.1 Simple Enable/Disable

```kconfig
config BT_<PROFILE>
    bool "Bluetooth <Profile Name> Service"
    depends on BT_PERIPHERAL
    help
      Enable support for the Bluetooth <Profile Name> Service.
```

### 4.2 With Log Level

```kconfig
config BT_<PROFILE>
    bool "Bluetooth <Profile Name> Service"
    depends on BT_PERIPHERAL
    help
      Enable support for the Bluetooth <Profile Name> Service.

if BT_<PROFILE>

config BT_<PROFILE>_LOG_LEVEL
    int "Log level for <Profile Name> Service"
    depends on LOG
    default 3
    range 0 4
    help
      0=OFF, 1=ERR, 2=WRN, 3=INF, 4=DBG

endif # BT_<PROFILE>
```

### 4.3 With Feature Flags

```kconfig
config BT_<PROFILE>
    bool "Bluetooth <Profile Name> Service"
    depends on BT_PERIPHERAL
    help
      Enable support for the Bluetooth <Profile Name> Service.

if BT_<PROFILE>

config BT_<PROFILE>_MAX_INSTANCES
    int "Maximum number of <Profile Name> instances"
    default 1
    range 1 10
    help
      Maximum number of concurrent <Profile Name> service instances.

config BT_<PROFILE>_<FEATURE>
    bool "Enable <feature> support in <Profile Name> Service"
    default n
    help
      Enable optional <feature> support.

config BT_<PROFILE>_LOG_LEVEL
    int "Log level for <Profile Name> Service"
    depends on LOG
    default 3
    range 0 4

endif # BT_<PROFILE>
```

### 4.4 With Dependencies

```kconfig
config BT_<PROFILE>
    bool "Bluetooth <Profile Name> Service"
    depends on BT_PERIPHERAL
    depends on BT_GATT_DYNAMIC_DB || BT_GATT_SERVICE_CHANGED
    select BT_<DEPENDENCY>
    help
      Enable support for the Bluetooth <Profile Name> Service.
      Requires BT_<DEPENDENCY> for <reason>.
```

---

## 5. CMakeLists.txt Integration

```cmake
# In subsys/bluetooth/services/CMakeLists.txt
# Add source file when Kconfig symbol is enabled:

zephyr_library_sources_ifdef(CONFIG_BT_<PROFILE>  <profile>.c)

# For profiles with sub-features:
if(CONFIG_BT_<PROFILE>)
    zephyr_library_sources(<profile>.c)
    zephyr_library_sources_ifdef(CONFIG_BT_<PROFILE>_<FEATURE>  <profile>_<feature>.c)
endif()
```

---

## 6. UUID Definition Patterns

### 6.1 16-bit UUID (Standard SIG UUIDs)

```c
/* Service UUID */
#define BT_UUID_<PROFILE>_VAL           0x<XXXX>U
#define BT_UUID_<PROFILE>               BT_UUID_DECLARE_16(BT_UUID_<PROFILE>_VAL)

/* Characteristic UUID */
#define BT_UUID_<PROFILE>_<CHAR>_VAL    0x<XXXX>U
#define BT_UUID_<PROFILE>_<CHAR>        BT_UUID_DECLARE_16(BT_UUID_<PROFILE>_<CHAR>_VAL)
```

### 6.2 128-bit UUID (Custom/Vendor UUIDs)

```c
/* 128-bit UUID — used for custom/vendor-specific profiles */
#define BT_UUID_CUSTOM_SVC_VAL \
    BT_UUID_128_ENCODE(0x12345678, 0x1234, 0x5678, 0x1234, 0x56789abcdef0)

#define BT_UUID_CUSTOM_SVC \
    BT_UUID_DECLARE_128(BT_UUID_CUSTOM_SVC_VAL)
```

---

## 7. Logging Patterns

```c
/* Module registration — place at top of .c file, after includes */
LOG_MODULE_REGISTER(bt_<profile>, CONFIG_BT_<PROFILE>_LOG_LEVEL);

/* Usage in code */
LOG_DBG("Debug: characteristic value = %d", value);
LOG_INF("Connection %p established", (void *)conn);
LOG_WRN("Warning: notify failed with %d", rc);
LOG_ERR("Error: initialization failed: %d", err);
```

---

## 8. Pattern Selection Guide

| Requirement | Use Pattern |
|-------------|-------------|
| Server pushes data, no ACK needed | Notify (1.2) |
| Server pushes data, ACK required | Indicate (2.3) |
| Client reads static info | Read Only (3.1) |
| Client sets a value or command | Write (3.2) |
| Client sends command, no response | Write Without Response (3.3) |
| Both read and write on same char | Mixed (3.6) |
| Multiple connection tracking | State Machine (2.1) |
| Many characteristics, different props | Complex + attr index enum (2.2) |
| Simple single sensor | Simple Notify (1.2) |
| Device metadata | Read Only DIS-style (1.3) |

---

## 9. Common Mistakes to Avoid

1. **Attribute index off-by-one**: Each characteristic declaration adds 2 attrs
   (chrc_decl + value), and each CCC adds 1. Count carefully.

2. **Returning wrong error code**: Always use `BT_GATT_ERR(BT_ATT_ERR_*)` for
   GATT errors in read/write handlers, not raw negative errno.

3. **Missing CCC for notify/indicate**: A notify/indicate characteristic without
   a CCC descriptor will be rejected by BT SIG compliance tests.

4. **bt_gatt_notify with wrong attr pointer**: The attr should point to the
   characteristic VALUE attribute, not the characteristic declaration.

5. **Not handling -ENOTCONN**: `bt_gatt_notify()` returns `-ENOTCONN` when no
   client has subscribed. This is normal — return 0 in this case.

6. **Forgetting to unref bt_conn in disconnected callback**: Always call
   `bt_conn_unref()` for every `bt_conn_ref()` call.

7. **Using fixed-size buffers for variable-length writes**: Check `offset + len`
   vs. maximum expected size and return `BT_ATT_ERR_INVALID_OFFSET` or
   `BT_ATT_ERR_INVALID_ATTRIBUTE_LEN` appropriately.

---

## 10. Phase 1 Discovered Patterns

> These patterns were discovered during Phase 1 validation (analysis of BT SIG spec docs
> in `docs/profiles/` and cross-referencing with the Zephyr service implementations).

### 10.1 Server-Requests-Client-Refresh Pattern (SCPS)

Source: `docs/profiles/SCPS/Scan_Parameters_Service_1.0.pdf`, Section 2.5

The Scan Parameters Service introduces a unique pattern where the **server notifies the
client to re-send its scan parameters**. This is the inverse of normal notify usage:

```
Normal notify:  Server → Client (data push)
SCPS refresh:   Server → Client (notification = "please re-send your scan parameters")
                Client → Server (write_without_response with new scan params)
```

**Implementation pattern:**
```c
/* Server side: notify client to refresh */
static int sps_request_refresh(struct bt_conn *conn)
{
    uint8_t refresh_val = 0x00;  /* "Server requires refresh" */

    return bt_gatt_notify(conn,
                          &bt_sps_svc.attrs[BT_SPS_ATTR_SCAN_REFRESH],
                          &refresh_val, sizeof(refresh_val));
}

/* Client-side write handler (on the server for Scan Interval Window) */
static ssize_t write_scan_interval_window(struct bt_conn *conn,
                                           const struct bt_gatt_attr *attr,
                                           const void *buf, uint16_t len,
                                           uint16_t offset, uint8_t flags)
{
    /* Store client scan parameters for power optimization */
    if (len != sizeof(struct bt_sps_scan_interval_window)) {
        return BT_GATT_ERR(BT_ATT_ERR_INVALID_ATTRIBUTE_LEN);
    }
    memcpy(&scan_params, buf, len);
    LOG_DBG("Client scan params updated: interval=%u window=%u",
            scan_params.le_scan_interval, scan_params.le_scan_window);
    return len;
}
```

**Key rule from SCPS spec (Section 2.6):** When disconnected, the server should assume
the stored values represent the **last known worst-case** client scanning behavior:
- `LE_Scan_Interval`: assume maximum interval
- `LE_Scan_Window`: assume minimum window

**Pattern tag:** `server-requests-refresh`

---

### 10.2 Indicate-Based Measurement Delivery Pattern (BPS, HTS, BCS, WSS)

Source: `docs/profiles/BPS/Blood_Pressure_Service_1.1.1.pdf`, Section 3.1;
`docs/profiles/WSS/Weight_Scale_Service_1.0.1.pdf`, Section 3.2

Medical measurement profiles (BPS, HTS, WSS, BCS) use **Indicate** (not Notify) for
measurement delivery. This is intentional: measurements are clinically significant and
MUST be acknowledged by the collector.

**Key behavioral rules from BPS spec:**
1. When CCC is configured for indications and a measurement is available, the server
   SHALL send an indication
2. The server SHALL NOT send a new indication until the previous one is acknowledged
3. If multiple measurements were buffered while not connected, they are indicated
   one-by-one after reconnection (in order)

**Implementation pattern:**
```c
/* Blood pressure measurement delivery via indicate */
static struct {
    struct bt_gatt_indicate_params params;
    /* measurement data buffer */
    uint8_t data[BPS_MEASUREMENT_MAX_LEN];
    uint8_t len;
    bool pending;
} bps_indicate_ctx;

static void bps_indicate_cb(struct bt_conn *conn,
                             struct bt_gatt_indicate_params *params,
                             uint8_t err)
{
    if (err) {
        LOG_WRN("Blood pressure indication failed: %d", err);
    } else {
        LOG_DBG("Blood pressure indication confirmed");
    }
    bps_indicate_ctx.pending = false;
    /* Check for queued measurements and send next if available */
}

int bt_bps_indicate(struct bt_conn *conn, const uint8_t *data, size_t len)
{
    if (bps_indicate_ctx.pending) {
        return -EBUSY;  /* Previous indication not yet acknowledged */
    }

    memcpy(bps_indicate_ctx.data, data, len);
    bps_indicate_ctx.len = len;
    bps_indicate_ctx.params.attr = &bt_bps_svc.attrs[BT_BPS_ATTR_MEASUREMENT];
    bps_indicate_ctx.params.func = bps_indicate_cb;
    bps_indicate_ctx.params.data = bps_indicate_ctx.data;
    bps_indicate_ctx.params.len = bps_indicate_ctx.len;

    bps_indicate_ctx.pending = true;
    return bt_gatt_indicate(conn, &bps_indicate_ctx.params);
}
```

**Key rule:** Always check if a previous indication is pending before sending a new one.
Use a `pending` flag or semaphore.

---

### 10.3 Conditional Feature Indication Pattern (WSS, BPS Feature Characteristics)

Source: `docs/profiles/WSS/Weight_Scale_Service_1.0.1.pdf`, Table 3.1 footnote;
`docs/profiles/BPS/Blood_Pressure_Service_1.1.1.pdf`, Note C.5

Some "Feature" characteristics (e.g., Weight Scale Feature, Blood Pressure Feature)
support a **conditional Indicate** property:

> "The Indicate property shall be supported for the Feature characteristic if the device
> supports bonding **and** the value of the Feature characteristic can change over the
> lifetime of the device, **otherwise excluded** for this service."

**Pattern:** The feature characteristic is normally read-only, but gains Indicate when
the device supports bonding and the feature value might change.

```c
/* Feature characteristic: Read always + Indicate only when bonding+dynamic
 * Replace <PROFILE> with profile prefix, e.g. BT_UUID_WSS_FEATURE or BT_UUID_BPS_FEATURE */
BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_FEATURE,  /* e.g., BT_UUID_WSS_FEATURE */
                        BT_GATT_CHRC_READ | BT_GATT_CHRC_INDICATE,
                        BT_GATT_PERM_READ,
                        read_feature, NULL, NULL),
BT_GATT_CCC(feature_ccc_cfg_changed,
             BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
```

If bonding is not supported or the feature value is static for device lifetime,
the CCC descriptor can be omitted:
```c
/* Static feature — Read only
 * Replace <PROFILE> with profile prefix, e.g. BT_UUID_BPS_FEATURE */
BT_GATT_CHARACTERISTIC(BT_UUID_<PROFILE>_FEATURE,  /* e.g., BT_UUID_BPS_FEATURE */
                        BT_GATT_CHRC_READ,
                        BT_GATT_PERM_READ,
                        read_feature, NULL, &feature_value),
```

---

### 10.4 Technical Tag Classification Rules (Phase 1 Discovery)

From Phase 1 analysis, these tags reliably predict implementation complexity:

| Tag | Meaning | Complexity Impact |
|-----|---------|------------------|
| `has_control_point` | Profile has RACP, HID CP, or OTS OACP | Always Complex; requires full indicate + state machine |
| `uses_indicate` | Primary data delivery uses Indicate (not Notify) | Add semaphore/pending flag for indication flow control |
| `per_connection_state_required` | Cannot function correctly without per-connection state | Must implement BT_CONN_CB_DEFINE callbacks |
| `server-requests-refresh` | Server sends notification to trigger client action | Inverse of normal notify pattern — document clearly |
| `connection-aware` | Profile behavior changes on connect/disconnect | Always implement connected/disconnected callbacks |

**Profiles by tag:**
- `has_control_point`: HRS, OTS, HIDS, GLS, ANS, UDS, CGMS, RSCS, CSCS, PLXS
- `uses_indicate`: HTS, BPS, OTS, GLS, UDS, BCS, WSS, CGMS, PLXS, RSCS, CSCS
- `per_connection_state_required`: ESS, CTS, OTS, HIDS, GLS, UDS, CGMS
- `server-requests-refresh`: SPS
- `connection-aware`: LLS (alert on link loss)

---

### 10.5 ESS Extended Descriptor Pattern (Environmental Sensing Service)

**Source:** BT SIG Environmental Sensing Service Specification, Section 3.1

ESS characteristics support up to **five additional descriptors** beyond the standard CCC.
These descriptors provide sensor metadata and trigger configuration that are unique to ESS.

**ESS-specific descriptors (per optional characteristic):**

| Descriptor | UUID | Purpose |
|------------|------|---------|
| ES Measurement | 0x290C | Sensor measurement metadata (sampling function, measurement period, update interval, application, measurement uncertainty) |
| ES Trigger Setting | 0x290D | When to trigger a notification (e.g., minimum change, fixed interval, always) |
| ES Configuration | 0x290B | Logical AND/OR combination of multiple trigger settings |
| Valid Range | 0x2906 | Min/max valid sensor value |
| CCC (standard) | 0x2902 | Standard notifications enable/disable |

**Key implementation rules:**
1. Each ESS characteristic that supports Notify SHOULD include a CCC descriptor
2. ES Trigger Setting descriptor controls WHEN notifications are sent — the server
   evaluates the trigger before sending a notification
3. Multiple ES Trigger Setting descriptors can exist per characteristic (up to 3);
   ES Configuration descriptor determines if they are AND'd or OR'd
4. Valid Range descriptor allows the client to know the sensor's operational range

**Simplified ESS pattern (without ES Trigger, just CCC + Valid Range):**

```c
/* Valid Range descriptor — uint16_t lower + uint16_t upper */
struct ess_valid_range {
    int16_t lower;
    int16_t upper;
};

static const struct ess_valid_range temperature_range = {
    .lower = -4000,  /* -40.00°C in 0.01°C units */
    .upper =  8500,  /* +85.00°C */
};

static ssize_t read_valid_range(struct bt_conn *conn,
                                const struct bt_gatt_attr *attr,
                                void *buf, uint16_t len, uint16_t offset)
{
    const struct ess_valid_range *range = attr->user_data;

    return bt_gatt_attr_read(conn, attr, buf, len, offset,
                             range, sizeof(*range));
}

/* In service definition — Temperature with CCC + Valid Range */
BT_GATT_CHARACTERISTIC(BT_UUID_TEMPERATURE,
                        BT_GATT_CHRC_READ | BT_GATT_CHRC_NOTIFY,
                        BT_GATT_PERM_READ,
                        read_temperature, NULL, &temperature_celsius),
BT_GATT_CCC(temperature_ccc_cfg_changed,
             BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
BT_GATT_DESCRIPTOR(BT_UUID_VALID_RANGE,
                    BT_GATT_PERM_READ,
                    read_valid_range, NULL, &temperature_range),
```

**Pattern tag:** `ess-extended-descriptors`
