# PowerTracker AI - יומן אימונים חכם וניתוח פאוורליפטינג 🏋️

**PowerTracker AI** היא אפליקציית מעקב אימוני כוח המשלבת יומן אימונים אישי עם **סוכן AI מבוסס Claude** שמנתח את הביצועים שלך ומשווה אותם לנתוני אמת של מעל מיליון תוצאות תחרות מדאטהסט [OpenPowerlifting](https://www.openpowerlifting.org/), באמצעות מודלי **Machine Learning** (KMeans, Random Forest) ו-**RAG** על ChromaDB.

![Status](https://img.shields.io/badge/status-active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.13-blue) ![Next.js](https://img.shields.io/badge/Next.js-16-black) ![FastAPI](https://img.shields.io/badge/FastAPI-0.1x-009688)

> 🔗 **דמו חי:** [powertracker-ai-production.up.railway.app](https://powertracker-ai-production.up.railway.app/) *(הכניסה מוגנת בסיסמה - פנו אליי לקבלת גישה)*

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
- גרפים ב-Recharts, תשובות הסוכן מרונדרות כ-Markdown (`react-markdown` + `remark-gfm`).

### Backend (`/BACK`) - FastAPI

- **`api.py`** - כל ה-endpoints, ולידציה עם Pydantic, ומידלוור שדורש `X-API-Key` בכל בקשה (חוץ מ-`/health`).
- **`database.py`** - שכבת נתונים מול PostgreSQL עם `ThreadedConnectionPool`. `get_all_workouts_full` מחזירה את כל האימונים, התרגילים והסטים בשלוש שאילתות.
- **`agent.py`** - הסוכן: Claude עם **Tool Use** בוחר בעצמו בין שני כלים:
  - `analyze_cluster` - סיווג המתאמן לקבוצת ייחוס (KMeans) והשוואה אליה
  - `predict_progress` - חיזוי קצב התקדמות (Random Forest): איטי / בינוני / מהיר
- **`powerlifting.py`** - חישובי 1RM (נוסחת Epley), התקדמות לפי תאריך, וקצב אישי ברגרסיה לינארית.
- **RAG:** תיאורי הקבוצות (ממוצעים, טווחים, סטיות תקן) נבנים בעליית השרת ונשמרים ב-**ChromaDB**, ומשם נשלפים כ-context לפרומפט.
- **Observability:** ניטור מלא של קריאות הסוכן באמצעות **Langfuse** + OpenTelemetry.
- **ML Pipelines:** סקריפטים לניקוי הדאטה, בחירת K אופטימלי ואימון המודלים.

### בניית ההקשר לסוכן

הפרונט שולח לסוכן **רק את השאלה**. `build_context` בשרת מצרף אליה את הפרופיל (מגדר, גיל, משקל) ואת תמצית שלושת האימונים האחרונים מהיומן. כך פורמט הפרומפט נשאר במקום אחד, ולא משוכפל בין הפרונט לבאק.

## 📁 Repository Structure

```
powertracker-ai/
├── frontend/                       # Next.js 16 (App Router, TS, Tailwind v4)
│   ├── app/
│   │   ├── layout.tsx              # RTL, ניווט, ערכת נושא כהה
│   │   ├── page.tsx                # הפניה ל-/journal
│   │   ├── journal/page.tsx        # יומן: לוח שנה + טופס אימון
│   │   ├── powerlifting/page.tsx   # שיאים, גרפים, קצב אישי
│   │   ├── chat/page.tsx           # צ'אט עם הסוכן + פרופיל
│   │   ├── login/page.tsx          # מסך כניסה
│   │   └── api/
│   │       ├── login/route.ts      # אימות סיסמה + הנפקת cookie
│   │       ├── logout/route.ts     # מחיקת cookie
│   │       └── backend/[...path]/  # שכבת מעבר לבאק (מוסיפה X-API-Key)
│   ├── proxy.ts                    # חוסם דפים ללא cookie תקין
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
│   └── .env                        # לא בריפו - ראו Quick Start
│
├── requirements.txt                # תלויות הבאק
├── nixpacks.toml                   # הגדרות פריסה ל-Railway
├── start.ps1                       # מרים את שני השרתים מקומית
└── README.md                       # אתם כאן
```

## 🚀 Quick Start Guide

הסעיף מיועד למי שרוצה להריץ עותק עצמאי (מפתחים, בודקים). ההרצה יוצרת מופע נפרד לחלוטין - עם מסד נתונים ומפתחות משלכם. משתמשי קצה יכולים פשוט להשתמש בקישור הדמו למעלה.

### Prerequisites

- Python 3.11+
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
pip install -r requirements.txt

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

> העלייה הראשונה של הבאק לוקחת 10-30 שניות: טעינת המודלים מה-pickle ובניית אוסף ה-ChromaDB.

### Step 3 (Optional): Retrain the Models

המודלים המאומנים כבר כלולים בריפו (`.pkl`). לאימון מחדש:

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
```

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
| Deployment | Railway (Nixpacks) |

## 📖 About This Project

הפרויקט נבנה כפרויקט גמר בקורס **מהנדסי AI** - האקדמיה להייטק מבית "העברית הכשרת מנהלים", האוניברסיטה העברית בירושלים.

הוא מדגים pipeline מלא של מערכת AI: איסוף וניקוי דאטה → אימון מודלי ML → סוכן LLM עם כלים ו-RAG → ניטור → הפרדה לשכבות ופריסה בענן.

הגרסה הראשונה נבנתה כאפליקציית Streamlit אחת, והועברה ל-Next.js + FastAPI כדי להפריד בין שכבת הממשק לשכבת הלוגיקה, לאבטח את הסודות בצד השרת, ולאפשר שליטה מלאה על ה-UI.

פותח על ידי **Tamir Ariel**.

---

*התובנות באפליקציה מבוססות על נתוני תחרויות אמיתיים אך אינן מהוות ייעוץ אימוני מקצועי.*