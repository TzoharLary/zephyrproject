# Group B Data (Source of Truth)

קבצים אלה הם שכבת האחסון (authoring) עבור הידע של Group B:
- `Logic/*.md`
- `Structure/*.md`

האתר **לא מציג אותם כ-Markdown ישיר**.
במקום זאת, ה-builder מחלץ מהם בלוקים מובנים ומציג UI מסונתז.

## מבנה כל קובץ

1. YAML front matter
2. סעיפים קבועים (`##`)
3. fenced blocks מובנים:
- `groupb_finding`
- `groupb_source_observation`
- `groupb_method`
- `groupb_open_question`

## הערות

- `SCPS` הוא ה-canonical ID בקבצים, אך ב-UI יוצג `ScPS`.
- אנגלית מותרת רק למזהים, קוד, paths ו-UUID/API names.
