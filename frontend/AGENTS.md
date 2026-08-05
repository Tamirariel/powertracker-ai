<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

## PowerTracker — מוסכמות הפרויקט

- העברית היא שפת הממשק. `dir="rtl"` מוגדר ברמת ה-`<html>`, אל תוסיפו RTL מקומי.
- כל הצבעים, המרווחים והגופנים מגיעים מ-`app/globals.css`. אין ערכים קשיחים בקומפוננטות.
  השתמשו במחלקות הקיימות: `.page`, `.card`, `.stat`, `.btn-primary`, `.field`, `.chip`, `.empty`.
- הפרונט לא פונה לבאק ישירות. כל קריאה עוברת דרך `/api/backend/[...path]`.
- מספרים מוצגים ב-Oswald דרך `.num` או `.stat-value`, עם `tabular-nums`.
- אין `localStorage` — ה-state נשמר בבאק.