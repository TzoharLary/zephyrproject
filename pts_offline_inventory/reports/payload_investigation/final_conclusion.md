# Final Conclusion

## מסקנה
**ב) ה-setup לא מכיל ETS; הוא מתקין תשתית/Prerequisites בלבד, ו-ETS צפוי להגיע מחבילת ETS Update נפרדת.**
- בטבלאות MSI שנפרסו אין רכיבי ETS/Test Suite; ה-MSI שנמצא הוא `MSXML 4.0 redist`.
- ב-CAB וב-MSI שחולצו לא נמצאו קבצי `.ets`/`.xml` שמייצגים מאגר ETS של PTS.
- בסריקות מחרוזות לא נמצאו עקבות נתיב ETS קלאסיים (`Bluetooth\Ets`, `\Ets\`, `*.ets`).

## ראיות תומכות
- MSI summary: `pts_offline_inventory/reports/payload_investigation/msi_tables_summary.md`
- CAB inventory: `pts_offline_inventory/reports/payload_investigation/cab_inventory_top_files.md`
- ETS string hits: `pts_offline_inventory/reports/payload_investigation/string_hits_ets_and_paths.tsv`
- Download indicators: `pts_offline_inventory/reports/payload_investigation/burn_download_indicators.tsv`

## אינדיקציות Download/External packages
- URL hits: **67**
- keyword hits (download/payload/package/cache/container/...): **1152**
- payload_file hits (מתוך BurnManifest): **54**
- container_file hits (מתוך BurnManifest): **2**
- MsiPackage IDs: **4**, MsuPackage IDs: **8**
- DownloadUrl attributes ב-BurnManifest: **0**
- לא נמצאו `DownloadUrl=` מפורשים במניפסטים שנחצבו מתוך ה-bundle.
- קיימים קבצי bootstrapper פנימיים (`NDP481-Web.exe`, `vcredist/VC_redist`), מה שמחזק מודל של prerequisites ולא מאגר ETS.

## מה חסר כדי להפיק inventory אמיתי של TCIDs על mac
1. חבילת ETS Update עצמה (קובץ/ארכיון ETS) או תיקיית ETS לאחר עדכון על Windows.
2. אם אפשר, Snapshot של תיקיית ETS מותקנת בפועל ממכונת PTS לאחר Apply ETS Updates.
3. לאחר קבלת החבילה/תיקייה: להריץ את סורק ה-TCID הקיים על הקבצים האלה בלבד ולהפיק רשימת Prefix/TCID מלאה.