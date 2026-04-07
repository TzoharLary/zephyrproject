# Extend Canonical Data Migration To Raw Specs And PTS Artifact Data

- Date: 2026-04-07
- Group: tools
- Status: done

## Context
מיפוי ה-data בפרויקט כבר הושלם, ונקבע מבנה יעד קנוני של `data/raw`, `data/catalog`, `data/curated`, `data/derived` ו-`state/`.

עד לשינוי הזה, המיגרציה שבוצעה בפועל כיסתה רק catalogs ו-authoring של Group B, בעוד ששני מקורות data חשובים עדיין נשארו מחוץ ל-`data/`:
- `docs/profiles/**` עם artifacts רשמיים של Bluetooth SIG
- מקורות חקירת PTS הישנים עם artifacts גולמיים, curated findings, derived reports ו-scratch workspace

המטרה בעבודה הזאת היתה להשלים גם את החלקים האלה, אבל בלי לשבור builders, dashboards, checks או scripts קיימים.

## Changes
- הועברו קבצי catalog של Group B ו-AutoPTS מ-`tools/data/` אל `data/catalog/...`.
- הועברו מסמכי `Logic` / `Structure` / `Implementation` של Group B אל `data/curated/group_b/profiles/<PROFILE>/`.
- הועבר manifest של PTS build plans אל `data/curated/pts/build_plans/`.
- הועברו כל artifacts הרשמיים מ-`docs/profiles/**` אל `data/raw/bluetooth_sig/profiles/**`.
- הועברו datasets שימושיים ממקורות חקירת PTS הישנים אל:
  - `data/raw/pts_artifacts/**`
  - `data/curated/pts/artifact_analysis/**`
  - `data/derived/pts/artifact_analysis/**`
- הועברו סקריפטי המחקר הנותרים אל `tools/pts_artifact_analysis/**`.
- הועבר scratch/log/workspace זמני אל `tmp/pts_artifact_analysis/**`.
- הוסר לחלוטין הנתיב הישן של מקורות חקירת PTS מהריפו.
- נוקה `.gitignore` מהפניות legacy ל-`pts_offline_inventory/**`, והתווסף ignore מפורש גם ל-`group-b-test-notes-state.json`.
- עודכנו `docs/README.md` ו-`data/README.md` כך שישקפו ש-`docs/` היא שכבת תיעוד אנושי בלבד, בעוד ה-artifacts הרשמיים וה-data הקנוני חיים תחת `data/`.
- נוקה `tmp/` מכל scratch artifacts ומסמכי עבודה מקומיים שהפסיקו להיות נחוצים אחרי סיום המיגרציה.
- עודכנו הצרכנים הישירים ב-`tools/group_b_hub_data.py`, `tools/autopts_guide_data.py`, `tools/build_pts_report_bundle.py`, `tools/check_group_b_hub.py` וב-scripts של `tools/pts_artifact_analysis/`.
- עודכן `group_b_profile_map.json` כך שיפנה לנתיבי ה-authoring החדשים, כולל `group_b_implementation_md`.
- עודכנו `.github/data/profiles-db.yaml`, `.github/data/profile-patterns.md` ו-`.github/workflows/pts-hub-check.yml` כך שהקטלוג וה-CI יצביעו לנתיבי ה-raw החדשים.
- התווסף `data/README.md`, ו-`tools/templates/pts_report_he/Group_B_data/README.md` הומר ל-redirect שמסביר שהמקור הקנוני עבר.
- בוצע rebuild ל-`dashboards/pts_report_he/autopts/data/hub-data.js` על בסיס הנתיבים החדשים.

## Why
בלי המהלך הזה, חלק מהידע הרשמי והחקירתי החשוב ביותר בריפו עדיין היה מפוזר מחוץ ל-`data/`, והקטלוגים/בדיקות היו ממשיכים להפנות לנתיבים ישנים שכבר לא מייצגים את המבנה הקנוני החדש.

ההשלמה הזאת סוגרת את הפער בין היעד הארכיטקטוני לבין המצב בפועל: גם raw Bluetooth SIG docs וגם PTS artifact data קיבלו בית ברור תחת `data/`, בזמן ש-runtime scratch, tooling ו-history נשארו מחוץ ל-`data/` בכוונה.

## Impact
- Users: אין שינוי מוצרי ישיר, אבל ה-Hub, ה-builders וה-checks נשענים עכשיו על נתיבי data מסודרים ואחידים יותר.
- Devs: המקורות הקנוניים הפעילים מפוצלים עכשיו באופן ברור ל-`data/raw`, `data/catalog`, `data/curated` ו-`data/derived`. `docs/` נשארת שכבת docs בלבד, `tmp/` חזר להיות scratch ריק, ומקורות חקירת PTS הישנים כבר לא אמורים לשמש כיעדי צריכה ראשיים.

## References
- Commit: pending (no commit in this task)
- Files:
  - data/README.md
  - data/raw/bluetooth_sig/profiles/
  - data/raw/pts_artifacts/
  - data/curated/pts/artifact_analysis/
  - data/derived/pts/artifact_analysis/
  - data/catalog/group_b/registries/group_b_profile_map.json
  - data/catalog/autopts/sources/autopts_official_sources.json
  - data/curated/group_b/profiles/BPS/logic.md
  - data/curated/group_b/profiles/WSS/structure.md
  - data/curated/group_b/profiles/SCPS/implementation.md
  - data/curated/pts/build_plans/pts_profile_build_plans.json
  - .github/data/profiles-db.yaml
  - .github/data/profile-patterns.md
  - .github/workflows/pts-hub-check.yml
  - .gitignore
  - docs/README.md
  - data/README.md
  - tools/group_b_hub_data.py
  - tools/autopts_guide_data.py
  - tools/build_pts_report_bundle.py
  - tools/check_group_b_hub.py
  - tools/pts_artifact_analysis/scan_pts_tcids.py
  - tools/pts_artifact_analysis/investigate_wix_payloads.py
  - tools/pts_artifact_analysis/analyze_pts_setup_distribution.py
  - tools/templates/pts_report_he/Group_B_data/README.md

## Notes
הקבוצה הראשית נשארת `tools`, אבל המשימה כוללת גם שינוי משני ב-`infra` דרך `.github/workflows/pts-hub-check.yml` וקטלוגי `.github/data/*`.

אחרי ההשלמה הזאת, מה שנשאר מחוץ ל-`data/` הוא כבר לא “data קנוני שנשכח”, אלא בעיקר tooling, runtime scratch, history ו-generated outputs שמכוון נשארו במיקומם.
