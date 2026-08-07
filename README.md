# PowerTracker AI - יומן אימונים חכם וניתוח פאוורליפטינג 🏋️

**PowerTracker AI** היא אפליקציית מעקב אימוני כוח המשלבת יומן אימונים אישי עם **סוכן AI מבוסס Claude** שמנתח את הביצועים שלך ומשווה אותם לנתוני אמת של מעל מיליון תוצאות תחרות מדאטהסט [OpenPowerlifting](https://www.openpowerlifting.org/), באמצעות מודלי **Machine Learning** (KMeans, Random Forest) ו-**RAG** על ChromaDB.

![Status](https://img.shields.io/badge/status-active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.13-blue) ![Next.js](https://img.shields.io/badge/Next.js-16-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.1x-009688)

> 🔗 **דמו חי:** [powertracker-ai.up.railway.app](https://powertracker-ai.up.railway.app/)
> **סיסמה:** `1q2w3e4r`

---

## 📸 מבט על האפליקציה

### פאוורליפטינג — שיאים, מגמות והשוואה לנתוני תחרות

![מסך פאוורליפטינג](docs/powerlifting.png)

הטוטאל ושלושת הליפטים מחושבים אוטומטית מהיומן בנוסחת Epley, עם גרף התקדמות לכל ליפט וקצב אישי ברגרסיה לינארית.

### הסוכן — השוואה מול קבוצת הייחוס

![מסך הצ'אט](docs/chat.png)

הסוכן מסווג את המתאמן לקבוצת ייחוס (KMeans), שולף את תיאור הקבוצה מ-ChromaDB ומשווה אליו — ממוצע, סטיית תקן ומיקום יחסי מתוך נתוני תחרות אמיתיים.

### יומן אימונים

![מסך היומן](docs/journal.png)

לוח שנה עם סימון סוג האימון בכל יום, בנייה מהירה של אימון, ושכפול האימון האחרון מאותו סוג.

---

## 🏛️ Architecture Overview

הפרויקט בנוי כשתי שכבות נפרדות שמתקשרות ב-HTTP: **Next.js** לממשק ו-**FastAPI** ללוגיקה, למודלים ולנתונים.

```
דפדפן ──cookie──> Next.js ──X-API-Key──> FastAPI ──> Postgres / Claude / ChromaDB
                  :3000                  :8000
```

הדפדפן מדבר **רק** עם Next.js. כל קריאה ל-API עוברת דרך Route Handler בצד השרת (`/api/backend/[...path]`) שמוסיף מפתח סודי ומעביר לבאק. כך שהמפתח, הסיסמה וכתובת הבאק לא מגיעים לקוד שרץ בדפדפן, והבאק אינו נגיש ישירות מבחוץ.

### Frontend (`/frontend`) - Next.js 16

- **App Router** עם TypeScript ו-Tailwind v4, בעברית מלאה (RTL ברמת ה-`<html>`).
- שלושה מסכים: יומן אימונים (לוח שנה, טופס בנייה, שכפול, מחיקה), פאוורליפטינג (שיאים, גרפי התקדמות, קצב אישי), וצ'אט עם הסוכן.
- **Auth:** סיסמה גלובלית אחת. `proxy.ts` חוסם כל דף למי שאין לו cookie תקין, `/api/login` מאמת בצד השרת ומנפיק cookie `httpOnly`.
- **מערכת עיצוב** ב-`globals.css`: פלטת הצבעים נגזרת מצבעי דיסקיות מכוילות בפאוורליפטינג (25=אדום, 20=כחול, 15=צהוב, 10=ירוק, 5=לבן), כך שכל צבע נושא משמעות מהענף עצמו — צהוב לפעולות ולשיאים, אדום לפסילה ולמחיקה. טיפוגרפיה: Rubik לעברית, Oswald לספרות בלבד.
- גרפים ב-Recharts, תשובות הסוכן מרונדרות כ-Markdown (`react-markdown` + `remark-gfm`).

### Backend (`/BACK`) - FastAPI

- **`api.py`** - כל ה-endpoints, ולידציה עם Pydantic, ומידלוור שדורש `X-API-Key` בכל בקשה (חוץ מ-`/health`).
- **`database.py`** - שכבת נתונים מול PostgreSQL עם `ThreadedConnectionPool`. `get_all_workouts_full` מחזירה את כל האימונים, התרגילים והסטים בשלוש שאילתות.
- **`agent.py`** - הסוכן: Claude עם **Tool Use** בוחר בעצמו בין שני כלים:
  - `analyze_cluster` - סיווג המתאמן לקבוצת ייחוס (KMeans) והשוואה אליה
  - `predict_progress` - חיזוי קצב התקדמות (Random Forest): איטי / בינוני / מהיר
- **`powerlifting.py`** - חישובי 1RM (נוסחת Epley), התקדמות לפי תאריך, וקצב אישי ברגרסיה לינארית.
- **RAG:** תיאורי הקבוצות (ממוצעים, טווחים, סטיות תקן) מחושבים מראש מטבלאות האימון ונשמרים כ-`cluster_documents.json`. בעליית השרת הם נטענים לתוך **ChromaDB**, ומשם נשלפים כ-context לפרומפט.
- **Observability:** ניטור מלא של קריאות הסוכן באמצעות **Langfuse** + OpenTelemetry.
- **ML Pipelines:** סקריפטים לניקוי הדאטה, בחירת K אופטימלי ואימון המודלים.

### בניית ההקשר לסוכן

הפרונט שולח לסוכן **רק את השאלה**. `build_context` בשרת מצרף אליה שלושה רכיבים: את הפרופיל (מגדר, גיל, משקל), את שיאי ה-1RM לשלושת הליפטים, ואת תמצית שלושת האימונים האחרונים מהיומן. כך פורמט הפרומפט נשאר במקום אחד, ולא משוכפל בין הפרונט לבאק.

השיאים מחושבים מ**כל** ההיסטוריה ולא מהאימונים האחרונים בלבד. בלעדיהם, מתאמן שהסקוואט האחרון שלו קדם לשלושה אימונים מסוג אחר היה מקבל תשובה שאין נתוני סקוואט ביומן — למרות שהם קיימים במסד. הכלים דורשים ערך ליפט מספרי, ולכן הוא חייב להיות בהקשר בכל מצב.

### ארטיפקטים של המודלים

קובצי המודלים בריפו מכילים **רק את מה שנחוץ בזמן ריצה**:

| קובץ | תוכן | גודל |
|---|---|---|
| `cluster_model_slim.pkl` | 8 מודלי KMeans + scalers, בלי טבלאות הדאטה הגולמיות | ~6 MB |
| `cluster_documents.json` | 28 תיאורי הקבוצות ל-RAG, מחושבים מראש | ~10 KB |
| `classification_model_gz.pkl.gz` | 8 מודלי Random Forest, דחוסים ב-gzip | ~24 MB |

הטבלאות הגולמיות (1.4M שורות) שימשו רק לחישוב התיאורים, ולכן אינן נשמרות. התוצאה: הריפו קטן ב-85%, העלייה כמעט מיידית, וצריכת הזיכרון בזמן ריצה מצומצמת לגודל המודלים בלבד.

## 📁 Repository Structure

```
powertracker-ai/
├── docs/                           # צילומי מסך ל-README
│
├── frontend/                       # Next.js 16 (App Router, TS, Tailwind v4)
│   ├── app/
│   │   ├── layout.tsx              # RTL, גופנים, מעטפת
│   │   ├── globals.css             # מערכת העיצוב - טוקנים ומחלקות משותפות
│   │   ├── page.tsx                # הפניה ל-/journal
│   │   ├── components/
│   │   │   ├── Nav.tsx             # ניווט עם מצב עמוד פעיל
│   │   │   └── ProfileCard.tsx     # כרטיס הפרופיל - משותף לצ'אט ולפאוורליפטינג
│   │   ├── journal/page.tsx        # יומן: לוח שנה + טופס אימון
│   │   ├── powerlifting/page.tsx   # שיאים, גרפים, קצב אישי
│   │   ├── chat/page.tsx           # צ'אט עם הסוכן
│   │   ├── login/page.tsx          # מסך כניסה
│   │   └── api/
│   │       ├── login/route.ts      # אימות סיסמה + הנפקת cookie
│   │       ├── logout/route.ts     # מחיקת cookie
│   │       └── backend/[...path]/  # שכבת מעבר לבאק (מוסיפה X-API-Key)
│   ├── proxy.ts                    # חוסם דפים ללא cookie תקין
│   ├── railway.json                # הגדרות פריסה - service הפרונט
│   └── .env.local                  # לא בריפו - ראו Quick Start
│
├── BACK/
│   ├── api.py                      # FastAPI - endpoints + API key middleware
│   ├── database.py                 # PostgreSQL + connection pool
│   ├── agent.py                    # Claude + Tools + ChromaDB + Langfuse
│   ├── powerlifting.py             # 1RM, התקדמות, רגרסיה
│   ├── data_cleaning.py            # ניקוי דאטהסט OpenPowerlifting (IQR outliers)
│   ├── cluster_model/              # אימון KMeans + בחירת K + גרפים
│   ├── classification_model/       # אימון Random Forest + ניסוי max_depth
│   ├── requirements.txt            # תלויות הבאק
│   ├── railway.json                # הגדרות פריסה - service הבאק
│   ├── .python-version             # גרסת Python לסביבת הפריסה
│   └── .env                        # לא בריפו - ראו Quick Start
│
├── start.ps1                       # מרים את שני השרתים מקומית
└── README.md                       # אתם כאן
```

## 🚀 Quick Start Guide

הסעיף מיועד למי שרוצה להריץ עותק עצמאי (מפתחים, בודקים). ההרצה יוצרת מופע נפרד לחלוטין - עם מסד נתונים ומפתחות משלכם. משתמשי קצה יכולים פשוט להשתמש בקישור הדמו למעלה.

### Prerequisites

- Python 3.13
- Node.js 20+
- PostgreSQL מ-[Railway](https://railway.app/) (או מקומי/Docker לבדיקות)
- מפתח API של [Anthropic](https://console.anthropic.com/)
- חשבון [Langfuse](https://cloud.langfuse.com/) (חינמי)

### Environment Configuration 🔑

צריך **שני** קבצי סביבה - אחד לכל שכבה.

**1. `BACK/.env`** (המיקום מחייב - כך הקוד מחפש אותו):

```env
# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-...

# Railway PostgreSQL (obtain from Railway dashboard)
DATABASE_URL=postgresql://user:password@your_host.proxy.rlwy.net:port/railway

# Langfuse (Observability)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# מפתח משותף עם הפרונט - הבאק דוחה כל בקשה בלעדיו
API_KEY=<אותו ערך כמו ב-frontend/.env.local>
```

**2. `frontend/.env.local`:**

```env
# כתובת הבאק. בלי NEXT_PUBLIC_ - נקרא רק בצד השרת
BACKEND_URL=http://localhost:8000

# אותו מפתח שב-BACK/.env
API_KEY=<אותו ערך>

# סיסמת הכניסה לאפליקציה
APP_PASSWORD=your_password_here

# מה שנשמר ב-cookie אחרי אימות. לא הסיסמה עצמה
AUTH_SECRET=<מחרוזת אקראית ארוכה>
```

לייצור `API_KEY` ו-`AUTH_SECRET`:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

> ⚠️ **חשוב:** אף אחד משלושת הסודות (`API_KEY`, `APP_PASSWORD`, `AUTH_SECRET`) לא נושא את הקידומת `NEXT_PUBLIC_`. משתנה עם הקידומת הזאת נארז לתוך ה-JS שנשלח לדפדפן וכל מבקר יכול לקרוא אותו.

> אותו קוד רץ מקומית ובענן - הפונקציה `get_env` בבאק מחפשת קודם ב-`.env` המקומי, ואם לא נמצא - במשתני הסביבה של הפלטפורמה. בפריסה מגדירים את אותם משתנים בדשבורד של Railway.

### Step 1: Install

```bash
# 1. Clone
git clone https://github.com/Tamirariel/powertracker-ai.git
cd powertracker-ai

# 2. Backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r BACK/requirements.txt

# 3. Frontend
cd frontend
npm install
cd ..
```

### Step 2: Run

שני השרתים צריכים לרוץ במקביל. ב-Windows:

```powershell
.\start.ps1
```

או ידנית, בשני טרמינלים:

```bash
# טרמינל 1 - Backend
cd BACK
uvicorn api:app --reload --port 8000

# טרמינל 2 - Frontend
cd frontend
npm run dev
```

היכנסו ל-http://localhost:3000 - טבלאות מסד הנתונים נוצרות אוטומטית בעליית הבאק (`init_db`).

> בהרצה הראשונה בסביבה חדשה, ChromaDB מוריד מודל embedding (~79MB) ושומר אותו במטמון המקומי. ההרצות הבאות מיידיות.

### Step 3 (Optional): Retrain the Models

המודלים המאומנים כבר כלולים בריפו. לאימון מחדש:

```bash
# 1. הורידו את הדאטהסט אל BACK/AGENT_data/openpowerlifting.csv
#    https://openpowerlifting.gitlab.io/opl-csv/

# 2. ניקוי הדאטה (סינון ציוד Raw/Wraps, הסרת חריגים IQR לפי מגדר ומשקל)
python BACK/data_cleaning.py

# 3. בחירת K אופטימלי ואימון מודלי הקלאסטרינג
python BACK/cluster_model/k_finding.py
python BACK/cluster_model/clustering_model_function.py

# 4. אימון מודל הקלאסיפיקציה (+ כיוונון max_depth)
python BACK/classification_model/classification_model.py

# 5. ייצור הארטיפקטים שהאפליקציה טוענת בזמן ריצה
python BACK/build_artifacts.py
```

> שלב 5 מפריד בין תוצרי האימון (שמכילים את טבלאות הדאטה) לבין הארטיפקטים שהאפליקציה באמת צריכה. הוא מחשב את 28 תיאורי הקבוצות ל-RAG, שומר את מודלי הקלאסטרינג בלי הטבלאות, ודוחס את מודלי הקלאסיפיקציה.

## 🔌 API Endpoints

כל ה-endpoints דורשים את הכותרת `X-API-Key`, פרט ל-`/health`.

| Method | Path | תיאור |
|---|---|---|
| GET | `/health` | בדיקת חיים (פתוח) |
| GET | `/profile` | פרופיל המתאמן |
| POST | `/profile` | שמירת פרופיל |
| POST | `/chat` | שאלה לסוכן (ההקשר נבנה בשרת) |
| GET | `/workouts` | רשימת אימונים |
| GET | `/workouts/full` | כל האימונים עם תרגילים וסטים |
| GET | `/workouts/{id}` | אימון בודד |
| POST | `/workouts` | שמירת אימון |
| DELETE | `/workouts/{id}` | מחיקת אימון |
| GET | `/workouts/last/{type}` | האימון האחרון מסוג מסוים (לשכפול) |
| GET | `/exercises/names` | כל שמות התרגילים שהוזנו |
| GET | `/powerlifting/progress` | שיאים, נקודות התקדמות וקצב לשלושת הליפטים |

## ☁️ Deployment

הפרויקט פרוס ב-[Railway](https://railway.app/) כ-**שני services נפרדים מאותו ריפו**, בתוספת PostgreSQL מנוהל:

| Service | Root Directory | Config | חשיפה |
|---|---|---|---|
| `powertracker-ai` (באק) | `BACK` | `/BACK/railway.json` | פנימי בלבד |
| `frontend` | `frontend` | `/frontend/railway.json` | domain ציבורי |

**הבאק אינו נגיש מהאינטרנט.** אין לו domain ציבורי כלל, והפרונט פונה אליו דרך הרשת הפרטית של Railway בכתובת `powertracker-ai.railway.internal:8000`. הרשת הפרטית עובדת על IPv6, ולכן הבאק מאזין ל-`::` בעוד הפרונט מאזין ל-`0.0.0.0` כדי לקבל תעבורה ציבורית.

משתני הסביבה מוגדרים בדשבורד של Railway - אותם שמות כמו בקבצי ה-`.env` המקומיים. `API_KEY` חייב להיות זהה בשני ה-services.

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind v4, Recharts |
| Backend | FastAPI, Pydantic, Uvicorn |
| AI Agent | Anthropic Claude (claude-sonnet-4-6) + Tool Use |
| ML Models | scikit-learn - KMeans, Random Forest |
| Vector DB (RAG) | ChromaDB |
| Database | PostgreSQL (psycopg2 + connection pool) |
| Auth | Password gate, `httpOnly` cookie, Next.js proxy |
| Observability | Langfuse (Tracing) + OpenTelemetry |
| Data | OpenPowerlifting Dataset (1M+ competition results) |
| Deployment | Railway (Railpack) - שני services + רשת פרטית |

## 📖 About This Project

הפרויקט נבנה כפרויקט גמר בקורס **מהנדסי AI** - האקדמיה להייטק מבית "העברית הכשרת מנהלים", האוניברסיטה העברית בירושלים.

הוא מדגים pipeline מלא של מערכת AI: איסוף וניקוי דאטה → אימון מודלי ML → סוכן LLM עם כלים ו-RAG → ניטור → הפרדה לשכבות ופריסה בענן.


פותח על ידי **Tamir Ariel**.

---

*התובנות באפליקציה מבוססות על נתוני תחרויות אמיתיים אך אינן מהוות ייעוץ אימוני מקצועי.*