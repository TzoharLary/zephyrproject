<div dir="rtl" style="text-align: right;">

# מפרטי בדיקות EDTT (Embedded Device Test Tool) ב-Zephyr

מסמך זה מפרט בהרחבה את כל מפרטי הבדיקות (Test Specs) הקיימים בכלי EDTT המשולב בתוך `babble sim` בפרויקט Zephyr. המידע מבוסס על סריקה וניתוח של קובצי המקור והסקריפטים בנתיבים הרלוונטיים.

---

## 1. סקריפטי אימות (Python Verification Scripts)

הלוגיקה המרכזית של הבדיקות מיושמת בקובצי Python הנמצאים בנתיב:
`tools/edtt/src/tests/`

להלן פירוט של כל סקריפט ותפקידו:

### `ll_verification.py` (Link Layer)
*   **גודל:** ~458KB (הקובץ הגדול/המקיף ביותר)
*   **מטרה:** אימות מלא של שכבת הערוץ (Link Layer). זהו הלב של בדיקות ה-Controller.
*   **תכולה:** מכיל את הלוגיקה עבור עשרות תרחישי בדיקה של פרסום (Advertising), סריקה (Scanning), יצירת חיבור (Initiating), ותפקידי Central/Peripheral.

### `gatt_verification.py` (GATT)
*   **גודל:** ~151KB
*   **מטרה:** אימות פרוטוקול GATT (Generic Attribute Profile).
*   **תכולה:** בדיקות עבור שרת (Server) ולקוח (Client), כולל Discovery של שירותים ומאפיינים, קריאה/כתיבה, התראות (Notifications) ואינדיקציות (Indications).

### `ial_verification.py` (Isochronous Adaptation Layer)
*   **גודל:** ~102KB
*   **מטרה:** בדיקות עבור ערוצים איזוכרוניים (Isochronous Channels), המשמשים בעיקר ל-LE Audio.
*   **תכולה:** אימות של CIS (Connected Isochronous Streams) ו-BIS (Broadcast Isochronous Streams).

### `gap_verification.py` (Generic Access Profile)
*   **גודל:** ~100KB
*   **מטרה:** אימות פרוטוקול GAP שאחראי על גילוי וחיבור ראשוני.
*   **תכולה:** בדיקות של תהליכי Connection, Advertisement, Discovery Modes (General/Limited/Non-Discoverable).

### `hci_verification.py` (Host Controller Interface)
*   **גודל:** ~55KB
*   **מטרה:** אימות ממשק ה-HCI, התקשורת בין ה-Host ל-Controller.
*   **תכולה:** בדיקת שליחת פקודות HCI וקבלת Events תואמים, אימות פורמטים של פקודות וטיפול בשגיאות.

### סקריפטים נוספים
*   **`ll_multiple_connections.py` (~5KB):** בדיקה ספציפית ליכולת ה-Controller לנהל מספר חיבורים במקביל.
*   **`le_transceiver_test.py` (~2KB):** בדיקת שידור/קליטה בסיסית ברמת ה-PHY.
*   **`echo_test.py` (~1KB):** בדיקת Loopback פשוטה לווידאו תקשורת תקינה עם הכלי.
*   **`test_utils.py` (~49KB):** ספריית עזר המכילה פונקציות משותפות לכל הטסטים.

---

## 2. רשימות מקרי הבדיקה (Test Cases Lists)

רשימות הבדיקות הספציפיות מגדירות אילו בדיקות ירוצו בפועל. הן ממוקמות בנתיב:
`zephyr/tests/bsim/bluetooth/ll/edtt/tests_scripts/`

להלן פירוט הבדיקות לפי קטגוריות:

### א. בדיקות Link Layer (LL)

הבדיקות מחולקות לסטים, כאשר `ll.set1.llcp.test_list` מכיל כ-70 בדיקות המכסות את התחומים הבאים:

1.  **Advertising (ADV):**
    *   `LL/CON/ADV/BV-01-C` עד `BV-14-C`: בדיקות שונות של התנהגות המפרסם.

2.  **Initiating (INI):**
    *   `LL/CON/INI/BV-01-C` עד `BV-24-C`: בדיקות של תהליך יצירת החיבור מצד היוזם.

3.  **Central (CEN):**
    *   `LL/CON/CEN/BV-03-C` עד `BV-73-C`: בדיקות מקיפות לתפקיד ה-Central בחיבור פעיל.

4.  **Peripheral (PER):**
    *   `LL/CON/PER/BV-04-C` עד `BV-27-C`: בדיקות מקיפות לתפקיד ה-Peripheral בחיבור פעיל.

*(חלק מהבדיקות מסומנות בהערה `#` ולכן לא רצות כרגע, בדרך כלל עקב באגים ידועים או חוסר תמיכה זמני)*.

### ב. בדיקות HCI

הקובץ `hci.llcp.test_list` מכיל כ-30 בדיקות המתמקדות בפקודות ואירועי HCI:

*   **Controller Configuration (CCO):** בדיקות אתחול והגדרות בקר (`HCI/CCO/BV-07-C`...).
*   **Flow Control (CFC):** בקרת זרימה של מידע (`HCI/CFC/BV-02-C`).
*   **Controller Information (CIN):** קריאת מידע מהבקר (`HCI/CIN/BV-01-C`).
*   **Command Management (CM):** ניהול פקודות (`HCI/CM/BV-01-C`).
*   **Data Information (DDI):** מידע על נתונים (`HCI/DDI/BI-02-C`).
*   **Device Setup (DSU):** הגדרות התקן (`HCI/DSU/BV-02-C`).

### ג. בדיקות GAP

הקובץ `gap.llcp.test_list` מכיל כ-55 בדיקות:

*   **Advertising (ADV):** בדיקות GAP ברמת הפרסום (`GAP/ADV/BV-01-C`...).
*   **Connection Establishment (CONN):**
    *   `ACEP`: Accept Connection Establishment Procedure
    *   `GCEP`: General Connection Establishment Procedure
    *   `CPUP`: Connection Parameter Update Procedure
    *   `NCON`: Non-Connectable modes
    *   `UCON`: Undirected Connectable modes
*   **Discovery (DISC):**
    *   `GENM/GENP`: General Discovery Mode/Procedure
    *   `LIMM/LIMP`: Limited Discovery Mode/Procedure
    *   `NONM`: Non-Discoverable Mode

### ד. בדיקות GATT

הקובץ `gatt.llcp.test_list` מכיל כ-70 בדיקות עבור פרופיל ה-GATT:

*   **Service Request (SR):**
    *   `GAC`: GATT Client functionality
    *   `GAD`: GATT Definition
    *   `GAR`: GATT Request/Response
    *   `GAW`: GATT Write procedures
    *   `GAN`: GATT Notifications
    *   `GAI`: GATT Indications
    *   `GPA`: GATT Profile Architecture

</div>
