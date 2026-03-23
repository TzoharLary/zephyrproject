# Refine Group B Implementation View

- Date: 2026-03-23
- Group: tools
- Status: done

## Context
לשונית `מימוש` ב-Hub של Group B הציגה section כפול של `קוד מימוש`, ה-code blocks ירשו RTL מהעמוד כולו, והופיעו במסכים שונים אינדיקציות `confidence` שלא היו רצויות למשתמש. בנוסף, בקוד המימוש עצמו נשארו comments בודדים בעברית.

## Changes
- הסרתי את section `קוד מימוש` המיותר מהתבנית, כך שלשונית `מימוש` נשענת רק על רשימת הקבצים, החלטות המימוש ופירוט המקורות.
- הוספתי layout חדש לכל קובץ מימוש: code pane משמאל ב-`LTR` קבוע, ו-side panel מימין עם הסבר עברי על imports, אחריות הקובץ והחלטות המימוש.
- הסרתי תצוגות `confidence` מה-UI הגלוי וסיננתי אותן גם מ-preview/debug JSON ו-Markdown שמוצגים ב-Hub.
- תיקנתי comments בעברית בתוך implementation code samples ל-English-only.
- בניתי מחדש את bundle של ה-Hub ואימתתי ב-smoke QA שהעמוד נטען, הלשוניות פועלות, והקונסול נקי מלבד `favicon.ico 404` הצפוי.

## Why
השינוי מיישר את לשונית `מימוש` לתצוגה אחת ברורה: קובץ, קוד והסבר צמוד. כך נמנעת כפילות, הקוד נשאר קריא גם בעמוד RTL, והמשתמש מקבל הסבר מיידי בלי לפתוח עוד לשוניות או לראות metadata שלא תורם כרגע לזרימת העבודה.

## Impact
- Users: לשונית `מימוש` קריאה יותר, ממוקדת יותר, וללא טקסטי `confidence`; כל קובץ מימוש מקבל הסבר עברי צמוד בלי לפגוע בכיווניות הקוד.
- Devs: תבנית ה-Hub תומכת כעת בהסבר implementation inline ובסינון confidence מהתצוגה, וה-build ממשיך להפיק assets תואמים מתוך `tools/templates`.

## References
- Commit: 53ca9b9
- Files:
  - tools/templates/pts_report_he/autopts/report.js
  - tools/templates/pts_report_he/autopts/report.css
  - dashboards/pts_report_he/autopts/assets/report.js
  - dashboards/pts_report_he/autopts/assets/report.css
  - dashboards/pts_report_he/autopts/data/hub-data.js

## Notes
קבוצת משנה משנית: `dashboard` עבור ה-assets שנבנו מחדש תחת `dashboards/pts_report_he/autopts/`.
