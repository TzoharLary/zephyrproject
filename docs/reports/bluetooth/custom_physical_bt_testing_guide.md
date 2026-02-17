<div dir="rtl" style="text-align: right;">

# מדריך: בניית אפליקציות בדיקה על חומרה פיזית

## השאלה שלך

> האם אני יכול לבנות משהו מעל Zephyr, בלי לשנות דברים בתוך, ולהשתמש באותם טסטים ש-BabbleSim משתמש - אבל על חומרה פיזית אמיתית?

## התשובה הקצרה

**לא ישירות.** הטסטים של BabbleSim משתמשים בספריית `babblekit` שתלויה בסימולציה ולא יכולה לרוץ על חומרה פיזית.

**אבל יש דרך אחרת:** Zephyr מספקת ספריית `testlib` עם פונקציות עזר **שכן עובדות על חומרה פיזית**, ואתה יכול לבנות אפליקציית בדיקה מותאמת אישית מחוץ לתיקיית Zephyr.

---

## מה ההבדל?

```
┌─────────────────────────────────────────────────────────────────┐
│                    בדיקות BabbleSim                              │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐      │
│  │ babblekit     │──▶│ bs_trace_*    │──▶│ BabbleSim     │      │
│  │ (TEST_PASS,   │   │ bs_*          │   │ (סימולציה)    │      │
│  │  TEST_FAIL)   │   │               │   │               │      │
│  └───────────────┘   └───────────────┘   └───────────────┘      │
│         ❌ לא עובד על חומרה פיזית!                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    ספריית testlib                               │
│  ┌───────────────┐   ┌───────────────┐   ┌───────────────┐      │
│  │ testlib       │──▶│ Zephyr BT API │──▶│ Real HW       │      │
│  │ (bt_testlib_  │   │ (bt_conn_*,   │   │ (nRF52840)    │      │
│  │  connect...)  │   │  bt_scan_*)   │   │               │      │
│  └───────────────┘   └───────────────┘   └───────────────┘      │
│         ✅ עובד על חומרה פיזית!                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## ספריית testlib - מה היא מספקת?

ספריית `testlib` נמצאת ב:
```
zephyr/tests/bluetooth/common/testlib/
```

### פונקציות עיקריות

| פונקציה | תיאור |
|---------|-------|
| `bt_testlib_connect()` | חיבור סינכרוני - ממתין עד שהחיבור מצליח או נכשל |
| `bt_testlib_disconnect()` | ניתוק סינכרוני - ממתין עד שהניתוק מושלם |
| `bt_testlib_wait_connected()` | המתנה למצב מחובר |
| `bt_testlib_wait_disconnected()` | המתנה למצב מנותק |
| `bt_testlib_scan_find_name()` | סריקה וחיפוש לפי שם |
| `bt_testlib_adv_conn()` | פרסום עם אפשרות חיבור |
| `bt_testlib_secure()` | הפעלת אבטחה |

### דוגמה מהקוד

```c
// מתוך testlib - זה הקוד שמריץ חיבור סינכרוני
int bt_testlib_connect(const bt_addr_le_t *peer, struct bt_conn **connp)
{
    int err;
    
    // יוצר חיבור עם הפרמטרים הסטנדרטיים של Zephyr
    err = bt_conn_le_create(peer, BT_CONN_LE_CREATE_CONN, 
                            BT_LE_CONN_PARAM_DEFAULT, connp);
    
    if (!err) {
        // ממתין לאירוע connected
        k_condvar_wait(&ctx.conn_cb_connected_match, &g_ctx_lock, K_FOREVER);
    }
    
    return err;
}
```

**מקור:** [connect.c](file:///Users/tzoharlary/zephyrproject/zephyr/tests/bluetooth/common/testlib/src/connect.c)

---

## איך לבנות אפליקציה מחוץ ל-Zephyr?

### מבנה פרויקט מומלץ

```
my_bt_test_app/
├── CMakeLists.txt
├── prj.conf
├── boards/
│   └── nrf52840dk_nrf52840.conf    # (אופציונלי)
└── src/
    ├── main.c
    ├── central_test.c               # תרחיש Central
    └── peripheral_test.c            # תרחיש Peripheral
```

### CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.20.0)

# מציאת Zephyr - לא משנה דבר בתוך Zephyr!
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(my_bt_test)

# קבצי המקור שלך
target_sources(app PRIVATE
    src/main.c
    src/central_test.c
    src/peripheral_test.c
)

# שימוש ב-testlib מ-Zephyr (ללא שינוי ל-Zephyr)
add_subdirectory(${ZEPHYR_BASE}/tests/bluetooth/common/testlib testlib)
target_link_libraries(app PRIVATE testlib)
```

### prj.conf

```ini
CONFIG_BT=y
CONFIG_BT_CENTRAL=y
CONFIG_BT_PERIPHERAL=y
CONFIG_BT_SMP=y
CONFIG_BT_GATT_CLIENT=y
CONFIG_LOG=y
CONFIG_BT_DEBUG_LOG=y

# הגדרות לניהול חיבורים
CONFIG_BT_MAX_CONN=2
CONFIG_BT_MAX_PAIRED=2
```

### src/main.c - תרחיש Central

```c
#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <testlib/conn.h>
#include <testlib/scan.h>

#define PERIPHERAL_NAME "MyPeripheral"

int main(void)
{
    int err;
    struct bt_conn *conn = NULL;
    bt_addr_le_t peer_addr;
    
    printk("=== Central Test Started ===\n");
    
    // אתחול Bluetooth
    err = bt_enable(NULL);
    if (err) {
        printk("Bluetooth init failed (err %d)\n", err);
        return err;
    }
    printk("Bluetooth initialized\n");
    
    // סריקה וחיפוש Peripheral לפי שם
    printk("Scanning for '%s'...\n", PERIPHERAL_NAME);
    err = bt_testlib_scan_find_name(&peer_addr, PERIPHERAL_NAME, 10000);
    if (err) {
        printk("Failed to find peripheral (err %d)\n", err);
        return err;
    }
    printk("Found peripheral!\n");
    
    // ==== תרחיש הבדיקה ====
    
    // חיבור ראשון
    printk("Connecting (attempt 1)...\n");
    err = bt_testlib_connect(&peer_addr, &conn);
    if (err) {
        printk("Connect failed (err %d)\n", err);
        return err;
    }
    printk("Connected!\n");
    
    k_sleep(K_SECONDS(2));
    
    // ניתוק
    printk("Disconnecting...\n");
    err = bt_testlib_disconnect(&conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
    if (err) {
        printk("Disconnect failed (err %d)\n", err);
        return err;
    }
    printk("Disconnected!\n");
    
    k_sleep(K_SECONDS(1));
    
    // חיבור שני
    printk("Connecting (attempt 2)...\n");
    err = bt_testlib_connect(&peer_addr, &conn);
    if (err) {
        printk("Connect failed (err %d)\n", err);
        return err;
    }
    printk("Connected again!\n");
    
    // ניתוק סופי
    printk("Disconnecting...\n");
    bt_testlib_disconnect(&conn, BT_HCI_ERR_REMOTE_USER_TERM_CONN);
    
    printk("=== TEST PASSED ===\n");
    return 0;
}
```

### src/peripheral_test.c - תרחיש Peripheral

```c
#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/conn.h>
#include <testlib/adv.h>
#include <testlib/conn.h>

static struct bt_conn *current_conn = NULL;

static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        printk("Connection failed (err %u)\n", err);
    } else {
        printk("Connected\n");
        current_conn = bt_conn_ref(conn);
    }
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    printk("Disconnected (reason %u)\n", reason);
    if (current_conn) {
        bt_conn_unref(current_conn);
        current_conn = NULL;
    }
}

BT_CONN_CB_DEFINE(conn_callbacks) = {
    .connected = connected,
    .disconnected = disconnected,
};

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA(BT_DATA_NAME_COMPLETE, "MyPeripheral", sizeof("MyPeripheral") - 1),
};

int main(void)
{
    int err;
    
    printk("=== Peripheral Test Started ===\n");
    
    err = bt_enable(NULL);
    if (err) {
        printk("Bluetooth init failed (err %d)\n", err);
        return err;
    }
    printk("Bluetooth initialized\n");
    
    // התחלת פרסום
    err = bt_le_adv_start(BT_LE_ADV_CONN, ad, ARRAY_SIZE(ad), NULL, 0);
    if (err) {
        printk("Advertising failed (err %d)\n", err);
        return err;
    }
    printk("Advertising started - waiting for connections...\n");
    
    // השרת רץ לנצח
    while (1) {
        k_sleep(K_SECONDS(10));
        printk("Still running...\n");
    }
    
    return 0;
}
```

---

## איך להריץ?

### שלב 1: בניה
```bash
cd my_bt_test_app

# בניית Central
west build -b nrf52840dk/nrf52840 -d build_central -- -DCONFIG_BT_CENTRAL=y

# בניית Peripheral  
west build -b nrf52840dk/nrf52840 -d build_peripheral -- -DCONFIG_BT_PERIPHERAL=y
```

### שלב 2: Flash
```bash
# Board 1 (Peripheral)
west flash -d build_peripheral --dev-id <SERIAL_1>

# Board 2 (Central)
west flash -d build_central --dev-id <SERIAL_2>
```

### שלב 3: צפייה בלוגים
```bash
# Terminal 1
minicom -D /dev/ttyACM0

# Terminal 2
minicom -D /dev/ttyACM1
```

---

## למה לא להשתמש ישירות בטסטים של BabbleSim?

הטסטים של BabbleSim (בתיקייה `tests/bsim/bluetooth/`) משתמשים ב:

1. **babblekit** - ספרייה עם מאקרואים כמו `TEST_PASS`, `TEST_FAIL`, `TEST_ASSERT`
2. **bstests.h** - Framework לניהול הטסטים
3. **bs_trace_*** - פונקציות לוגים שתלויות בסימולטור
4. **bs_2G4_phy_v1** - סימולציית הרדיו

כל אלו **תלויים בתשתית BabbleSim** ולא יתקמפלו ללוח פיזי.

**מקור:** [testcase.h](file:///Users/tzoharlary/zephyrproject/zephyr/tests/bsim/babblekit/include/babblekit/testcase.h)

---

## סיכום

| שאלה | תשובה |
|------|-------|
| האם אפשר להריץ טסטים של bsim על חומרה? | ❌ לא ישירות |
| האם אפשר לבנות אפליקציה מחוץ ל-Zephyr? | ✅ כן |
| האם אפשר להשתמש ב-testlib? | ✅ כן, היא פורטבילית |
| האם צריך לשנות קוד בתוך Zephyr? | ❌ לא |

### ההמלצה שלי

בנה אפליקציה מותאמת אישית מחוץ ל-Zephyr:
1. השתמש ב-`testlib` לפונקציות עזר
2. כתוב את הלוגיקה של הבדיקה בעצמך
3. הפלט יהיה דרך `printk()` או Logging subsystem

</div>
