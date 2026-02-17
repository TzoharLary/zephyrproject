<div dir="rtl" style="text-align: right;">

# מיקומי בדיקות BabbleSim בפרויקט Zephyr

להלן רשימה מפורטת של כל המיקומים בהם נמצאים הטסטים שמשתמשים ב-BabbleSim בתוך עץ הפרויקט `zephyr`. כל הנתיבים הם יחסיים לתיקיית `zephyr/tests/bsim/bluetooth`.

## 1. בדיקות HOST (שכבת היישום והפרוטוקולים העליונים)
נמצא ב: `zephyr/tests/bsim/bluetooth/host`

### פרסום וסריקה
*   `adv/chain`: בדיקות Advertising Chaining
*   `adv/periodic`: בדיקות Periodic Advertising
*   `adv/extended`: בדיקות Extended Advertising
*   `adv/long_ad`: בדיקות פרסום עם מידע ארוך
*   `adv/encrypted`: בדיקות Encrypted Advertising Data (EAD)

### פרוטוקול ATT/GATT (העברת נתונים)
*   `att/eatt`: Enhanced ATT (EATT) - ערוצים מקבילים
*   `att/eatt_notif`: התראות דרך EATT
*   `att/long_read`: קריאת נתונים ארוכים
*   `att/mtu_update`: עדכון גודל חבילה (MTU)
*   `gatt/notify`: התראות (Notifications)
*   `gatt/notify_multiple`: התראות מרובות
*   `gatt/caching`: בדיקות GATT Caching
*   `gatt/authorization`: בדיקות הרשאות גישה
*   `gatt/settings`: שמירת הגדרות GATT

### פרוטוקול L2CAP (ערוצים לוגיים)
*   `l2cap/ecred`: Enhanced Credit Based Flow Control
*   `l2cap/credits`: ניהול קרדיטים בערוצים
*   `l2cap/split`: פיצול חבילות (Segmentation/Reassembly)
*   `l2cap/stress`: בדיקות עומס

### אבטחה (Security/SMP)
*   `security/bond_overwrite_allowed`: דריסת צימודים (Pairing)
*   `security/bond_per_connection`: צימוד לכל חיבור
*   `security/id_addr_update`: עדכון כתובות זהות (Identity Address)

### שמע (ISO - LE Audio)
*   `host/iso/bis`: Broadcast Isochronous Streams
*   `host/iso/cis`: Connected Isochronous Streams

---

## 2. בדיקות Link Layer (שכבת הרדיו והתזמון)
נמצא ב: `zephyr/tests/bsim/bluetooth/ll`

*   `conn`: בדיקות חיבור בסיסיות (Link Layer Connection)
*   `cis`: בדיקות Connected Isochronous Streams ברמת ה-Link Layer
*   `bis`: בדיקות Broadcast Isochronous Streams ברמת ה-Link Layer

---

## 3. בדיקות Mesh (רשת מושתתת)
נמצא ב: `zephyr/tests/bsim/bluetooth/mesh`

*   `src`: קוד המקור של הטסטים
*   `tests_scripts`: סקריפטים להרצת תרחישי Mesh מורכבים

---

## 4. בדיקות Audio (אפליקציות LE Audio מלאות)
נמצא ב: `zephyr/tests/bsim/bluetooth/audio`

*   `src`: קוד מקור לבדיקות אודיו מלאות
*   `test_scripts`: סקריפטים להרצת תרחישי אודיו

---

## 5. דוגמאות כלליות
נמצא ב: `zephyr/tests/bsim/bluetooth/samples`

* בדיקות המבוססות על דוגמאות הקוד (Samples) הרגילות של Zephyr, מותאמות ל-BabbleSim.

</div>
