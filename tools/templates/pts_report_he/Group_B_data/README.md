# Group B Data (Legacy Location)

קבצי ה-authoring הקנוניים של Group B כבר לא נשמרים כאן.

החל מ-Wave 1 של ארגון ה-data, מקור האמת המקומי עבר ל:
- `data/curated/group_b/profiles/<PROFILE>/logic.md`
- `data/curated/group_b/profiles/<PROFILE>/structure.md`
- `data/curated/group_b/profiles/<PROFILE>/implementation.md`

ה-builder לא אמור יותר לקרוא את `Logic/*.md`, `Structure/*.md` או `Implementation/*.md` מהנתיב הישן הזה כאשר עץ `data/` המקומי זמין.

## למה התיקייה עדיין קיימת

- כדי להשאיר README redirect במקום המוכר הישן
- כדי לאפשר migration הדרגתי של מסמכים/הפניות היסטוריות

## הערות

- `SCPS` הוא ה-canonical ID בקבצים, אך ב-UI יוצג `ScPS`.
- אנגלית מותרת רק למזהים, קוד, paths ו-UUID/API names.
