<div dir="rtl" style="text-align: right;">

# תיעוד מפורט: שינויים לבניית Bluetooth Tester עם Twister

## מטרת המסמך
מסמך זה מתעד את כל השינויים שבוצעו בקוד Zephyr כדי לאפשר בניית ה-Bluetooth Tester עבור הלוח `lp_em_cc2745r10_q1/cc2745r10_q1` באמצעות Twister.

---

## רקע

### מה זה Bluetooth Tester?
ה-Bluetooth Tester הוא אפליקציית בדיקות הנמצאת ב-`zephyr/tests/bluetooth/tester`. היא משמשת להרצת בדיקות אוטומטיות מול מכשירי PTS (Profile Tuning Suite) של Bluetooth SIG.

### מה זה Twister?
Twister הוא כלי הבדיקות והאינטגרציה של Zephyr. הוא יודע לבנות ולהריץ טסטים על פלטפורמות שונות, ומייצר דוחות מפורטים.

### הפקודה הבסיסית
```bash
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 -T zephyr/tests/bluetooth/tester --build-only -v
```

---

## בעיה 0: הלוח לא ברשימת הפלטפורמות המותרות

### תיאור הבעיה
כאשר הרצנו את Twister בפעם הראשונה, הוא דילג על כל הטסטים ולא ניסה לבנות כלל.

### סיבת הבעיה
הקובץ `zephyr/tests/bluetooth/tester/testcase.yaml` מגדיר רשימת `platform_allow` לכל תצורת טסט. הלוח שלנו לא מופיע ברשימה:

```yaml
tests:
  bluetooth.general.tester:
    build_only: true
    platform_allow:
      - qemu_x86
      - native_posix
      - native_sim
      - nrf52840dk/nrf52840
    # הלוח lp_em_cc2745r10_q1 לא כאן!
```

### הפתרון
לא שינינו קוד. השתמשנו בדגל `--force-platform` שמורה ל-Twister להתעלם מהסינון ולנסות לבנות בכל זאת:

```bash
west twister -p lp_em_cc2745r10_q1/cc2745r10_q1 -T zephyr/tests/bluetooth/tester --build-only --force-platform -v
```

### למה זה עוזר
הדגל `--force-platform` אומר ל-Twister: "אני יודע שהלוח לא ברשימה הרשמית, אבל תנסה לבנות בכל זאת". זה מאפשר לנו לבדוק האם הבנייה אפשרית מבחינה טכנית, גם אם הלוח לא נבדק רשמית.

---

## בעיה 1: שגיאת קומפילציה - הצהרת פונקציה חסרה

### תיאור השגיאה
```
zephyr/subsys/bluetooth/host/l2cap.c:876:17: error: implicit declaration of function 'bt_tx_irq_raise' [-Werror=implicit-function-declaration]
```

### מה המשמעות?
הקומפיילר (GCC) נתקל בקריאה לפונקציה `bt_tx_irq_raise()` בתוך הקובץ `l2cap.c`, אבל לא מצא **הצהרה** (declaration) עליה באף קובץ Header.

ב-C, לפני שמשתמשים בפונקציה, צריך להצהיר עליה. ההצהרה אומרת לקומפיילר:
- מה שם הפונקציה
- מה היא מחזירה
- מה הפרמטרים שלה

בלי הצהרה, הקומפיילר לא יודע מה לעשות עם הקריאה לפונקציה.

### ניתוח הבעיה

#### איפה הפונקציה מוגדרת?
הפונקציה מוגדרת בקובץ `zephyr/subsys/bluetooth/host/hci_core.c` בשורה 4683:

```c
void bt_tx_irq_raise(void)
{
    LOG_DBG("kick TX");
    k_work_submit(&tx_work);
}
```

#### למה ההצהרה לא נמצאה?
ההצהרה **לא הייתה** בקובץ `hci_core.h`. במקום זאת, חלק מהקבצים הכלילו הצהרה **מקומית**:

| קובץ | יש הצהרה מקומית? |
|------|-----------------|
| `hci_core.c` | כן (שורה 75) |
| `conn.c` | כן (שורה 81) |
| `l2cap.c` | **לא** ❌ |
| `iso.c` | **לא** ❌ |

#### למה זה צץ דווקא עכשיו?
הקוד בשורה 876 של `l2cap.c` נמצא בתוך בלוק מותנה:

```c
if (atomic_test_bit(conn->flags, BT_CONN_TX_QUEUE_LOW_WATERMARK)) {
    atomic_clear_bit(conn->flags, BT_CONN_TX_QUEUE_LOW_WATERMARK);
    bt_tx_irq_raise();  // <-- השורה הבעייתית
}
```

הקונפיגורציה הספציפית של הלוח + ה-Tester גרמה לקוד הזה להיות מקומפל. בקונפיגורציות אחרות, יתכן שהקוד לא נכלל.

### השינוי שבוצע

#### קובץ ששונה
`zephyr/subsys/bluetooth/host/hci_core.h`

#### מיקום השינוי
שורה 525 (סוף הקובץ, לפני ה-`#endif`)

#### תוכן השינוי
```c
void bt_tx_irq_raise(void);
```

#### ה-Diff המלא
```diff
--- a/zephyr/subsys/bluetooth/host/hci_core.h
+++ b/zephyr/subsys/bluetooth/host/hci_core.h
@@ -522,4 +522,6 @@ bool bt_le_conn_params_valid(const struct bt_le_conn_param *param);
 int bt_le_set_data_len(struct bt_conn *conn, uint16_t tx_octets, uint16_t tx_time);
 int bt_le_set_phy(struct bt_conn *conn, uint8_t all_phys,
                   uint8_t pref_tx_phy, uint8_t pref_rx_phy, uint8_t phy_opts);
+
+void bt_tx_irq_raise(void);
 
 #endif /* __HCI_CORE_H */
```

### למה זה עוזר
כעת כל קובץ שמצרף את `hci_core.h` (כולל `l2cap.c`) יכיר את הפונקציה `bt_tx_irq_raise`. הקומפיילר יודע שהפונקציה קיימת, מה היא מחזירה (`void`), ושהיא לא מקבלת פרמטרים.

---

## בעיה 2: שגיאת לינקר - פונקציית הצפנה חסרה

### תיאור השגיאה
לאחר תיקון הבעיה הקודמת, רוב הטסטים נבנו בהצלחה, אבל תצורת ה-**Mesh** (`bluetooth.general.tester_mesh`) נכשלה:

```
zephyr/subsys/bluetooth/common/rpa.c:48: undefined reference to `ecb_encrypt'
collect2: error: ld returned 1 exit status
```

### מה המשמעות?
זו **שגיאת לינקר**, לא שגיאת קומפילציה. המשמעות:
1. **הקומפילציה הצליחה** - כל קבצי המקור קומפלו ל-object files
2. **הלינקינג נכשל** - כשניסינו לחבר את כל הקבצים לקובץ הרצה אחד, חסרה פונקציה

ההבדל:
- **implicit declaration** = הקומפיילר לא מכיר את הפונקציה
- **undefined reference** = הלינקר לא מוצא את **הגוף** (המימוש) של הפונקציה

### ניתוח הבעיה

#### מה זה `ecb_encrypt`?
זו פונקציית הצפנה ב-ECB mode (Electronic Codebook) שאמורה להגיע מהבקר (Controller) של ה-Bluetooth.

#### איפה נעשה שימוש בה?
בקובץ `zephyr/subsys/bluetooth/common/rpa.c` שורות 26-52:

```c
#if defined(CONFIG_BT_CTLR_CRYPTO) && defined(CONFIG_BT_HOST_CRYPTO)
#include "../controller/util/util.h"
#include "../controller/hal/ecb.h"
#endif

static int internal_encrypt_le(...)
{
#if defined(CONFIG_BT_CTLR_CRYPTO) && defined(CONFIG_BT_HOST_CRYPTO)
    ecb_encrypt(key, plaintext, enc_data, NULL);  // <-- כאן!
    return 0;
#else
    return bt_encrypt_le(key, plaintext, enc_data);
#endif
}
```

#### התנאי הקריטי
הקוד משתמש ב-`ecb_encrypt` **רק אם** שני התנאים הבאים מתקיימים:
1. `CONFIG_BT_CTLR_CRYPTO=y` (הצפנה מהבקר מופעלת)
2. `CONFIG_BT_HOST_CRYPTO=y` (הצפנה מהמארח מופעלת)

#### מה גרם לשני התנאים להתקיים?
קובץ הקונפיגורציה המשותף של לוחות TI LPF3:
`zephyr/boards/ti/lpf3_common/Kconfig.defconfig`

```kconfig
if BT_MESH
    config BT_HOST_CRYPTO_PRNG
        default n

    config BT_CTLR_CRYPTO
        default y

    config BT_HOST_CRYPTO
        default y
endif # BT_MESH
```

כלומר, **כאשר Mesh מופעל**, הקובץ הזה מפעיל את **שניהם**.

#### למה זה בעייתי?
הבקר של TI (שהוא בקר בינארי סגור) **לא מספק** את הפונקציה `ecb_encrypt`. הוא לא חושף ממשק חומרה להצפנת ECB.

### השינוי שבוצע

#### קובץ ששונה
`zephyr/boards/ti/lpf3_common/Kconfig.defconfig`

#### תוכן המקורי
```kconfig
if BT_MESH
    config BT_HOST_CRYPTO_PRNG
        default n

    config BT_CTLR_CRYPTO
        default y

    config BT_HOST_CRYPTO
        default y

if BT_MESH_FRIEND
...
```

#### תוכן לאחר השינוי
```kconfig
if BT_MESH
    config BT_HOST_CRYPTO_PRNG
        default n

if BT_MESH_FRIEND
...
```

#### ה-Diff המלא
```diff
--- a/zephyr/boards/ti/lpf3_common/Kconfig.defconfig
+++ b/zephyr/boards/ti/lpf3_common/Kconfig.defconfig
@@ -13,12 +13,6 @@ if BT_MESH
     config BT_HOST_CRYPTO_PRNG
         default n
 
-    config BT_CTLR_CRYPTO
-        default y
-
-    config BT_HOST_CRYPTO
-        default y
-
 if BT_MESH_FRIEND
```

### למה זה עוזר
הסרנו את הכפייה של שני הדגלים יחד. כעת:
- `BT_CTLR_CRYPTO` לא נכפה ל-`y` (יישאר כברירת המחדל האמיתית)
- `BT_HOST_CRYPTO` לא נכפה ל-`y`

התנאי ב-`rpa.c` כבר לא מתקיים, והקוד משתמש במימוש התוכנתי (`bt_encrypt_le`) במקום לנסות לקרוא ל-`ecb_encrypt`.

---

## סיכום השינויים

| # | קובץ | שינוי | סיבה |
|---|------|-------|------|
| 0 | (אין) | שימוש ב-`--force-platform` | לעקוף את הגבלת הפלטפורמות |
| 1 | `hci_core.h` | הוספת `void bt_tx_irq_raise(void);` | הצהרה חסרה על פונקציה |
| 2 | `lpf3_common/Kconfig.defconfig` | הסרת ברירות מחדל ל-BT_CTLR_CRYPTO ו-BT_HOST_CRYPTO | הבקר לא מספק ecb_encrypt |

---

## הפקודה הסופית לבנייה

```bash
# מתיקיית הפרויקט הראשית
source .venv/bin/activate
west twister \
    -p lp_em_cc2745r10_q1/cc2745r10_q1 \
    -T zephyr/tests/bluetooth/tester \
    --build-only \
    --force-platform \
    -v
```

## תוצאה צפויה
```
INFO - 3 of 4 test configurations passed (100.00%), 0 failed
INFO - 0 test configurations executed on platforms, 3 test configurations were only built.
```

---

## לוחות מושפעים נוספים

השינוי ב-`lpf3_common/Kconfig.defconfig` משפיע גם על לוחות אחרים שיורשים ממנו:
- `lp_em_cc2340r5`
- `lp_em_cc2340r53`
- `lp_em_cc2745r10_q1` (הלוח שלנו)

---

## הערות לעתיד

1. התיקון ב-`hci_core.h` עשוי להתקבל ל-upstream של Zephyr כתיקון באג.
2. התיקון ב-`Kconfig.defconfig` ספציפי ללוחות TI ועשוי לדרוש עדכון עם גרסאות עתידיות של ה-HAL של TI.
3. אם נרצה שהלוח יופיע ברשימות ה-`platform_allow` הרשמיות, צריך לפתוח PR ל-Zephyr.

</div>
