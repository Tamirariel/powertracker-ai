# PowerTracker AI - יומן אימונים חכם וניתוח פאוורליפטינג 🏋️

**PowerTracker AI** היא אפליקציית מעקב אימוני כוח המשלבת יומן אימונים אישי עם **סוכן AI מבוסס Claude** שמנתח את הביצועים שלך ומשווה אותם לנתוני אמת של מעל מיליון תוצאות תחרות מדאטהסט [OpenPowerlifting](https://www.openpowerlifting.org/), באמצעות מודלי **Machine Learning** (KMeans, Random Forest) ו-**RAG** על ChromaDB.

![License](https://img.shields.io/badge/license-MIT-green) ![Status](https://img.shields.io/badge/status-active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.59-FF4B4B)

> 🔗 **דמו חי:** [powertracker-ai-production.up.railway.app](https://powertracker-ai-production.up.railway.app/) *(הכניסה מוגנת בסיסמה - פנו אליי לקבלת גישה)*

---

## 🏛️ Architecture Overview

הפרויקט בנוי כאפליקציית **Streamlit** אחת עם הפרדה לוגית בין שכבת הממשק לשכבת הלוגיקה:

1. **Frontend** ( `/FRONT` )
   - שלושה עמודי Streamlit בעברית מלאה (RTL): יומן אימונים, פאוורליפטינג, צ'אט.
   - שער כניסה מבוסס סיסמה (`auth.py`) הנבדק בכל עמוד.
   - חישובי 1RM (נוסחת Epley), גרפי התקדמות וקצב אישי (רגרסיה לינארית).

2. **Backend** ( `/BACK` )
   - **Database Layer:** PostgreSQL בענן (Railway) - אימונים, תרגילים, סטים ופרופיל.
   - **AI Agent:** Claude (Anthropic API) עם **Tool Use** - הסוכן בוחר בעצמו בין שני כלים:
     - `analyze_cluster` - סיווג המתאמן לקבוצת ייחוס (KMeans) והשוואה אליה
     - `predict_progress` - חיזוי קצב התקדמות (Random Forest): איטי / בינוני / מהיר
   - **RAG:** תיאורי הקבוצות (ממוצעים, טווחים, סטיות תקן) מאוחסנים ב-**ChromaDB** ונשלפים כ-context לפרומפט.
   - **Observability:** ניטור מלא של קריאות הסוכן באמצעות **Langfuse** + OpenTelemetry.
   - **ML Pipelines:** סקריפטים לניקוי הדאטה, בחירת K אופטימלי ואימון המודלים.

## 📁 Repository Structure

```
powertracker-ai/
├── FRONT/                          # Streamlit UI (עברית, RTL)
│   ├── main.py                     # עמוד ראשי - יומן אימונים + לוח שנה
│   ├── auth.py                     # שער סיסמה לאפליקציה
│   └── pages/
│       ├── 1_powerlifting.py       # מעקב ליפטים, 1RM, גרפים וקצב אישי
│       └── 2_chat.py               # צ'אט עם הסוכן
│
├── BACK/
│   ├── database.py                 # שכבת נתונים - PostgreSQL
│   ├── agent.py                    # הסוכן - Claude + Tools + ChromaDB + Langfuse
│   ├── data_cleaning.py            # ניקוי דאטהסט OpenPowerlifting (IQR outliers)
│   ├── .env                        # משתני סביבה (לא בריפו - ראו Quick Start)
│   ├── cluster_model/              # אימון KMeans + בחירת K + גרפים
│   └── classification_model/       # אימון Random Forest + ניסוי max_depth
│
├── streamlit/config.toml           # ערכת נושא כהה מותאמת
├── nixpacks.toml                   # הגדרות פריסה ל-Railway
├── requirements.txt
└── README.md                       # אתם כאן
```

## 🚀 Quick Start Guide

הסעיף מיועד למי שרוצה להריץ עותק עצמאי (מפתחים, בודקים). ההרצה יוצרת מופע נפרד לחלוטין - עם מסד נתונים ומפתחות משלכם. משתמשי קצה יכולים פשוט להשתמש בקישור הדמו למעלה.

### Prerequisites

- Python 3.11+
- PostgreSQL מ-[Railway](https://railway.app/) (או מקומי/Docker לבדיקות)
- מפתח API של [Anthropic](https://console.anthropic.com/)
- חשבון [Langfuse](https://cloud.langfuse.com/) (חינמי)

### Environment Configuration 🔑

לפני ההרצה יש ליצור קובץ `.env` **בתוך תיקיית `BACK/`** (המיקום מחייב - כך הקוד מחפש אותו):

```env
# BACK/.env

# Anthropic API Key
ANTHROPIC_API_KEY=sk-ant-...

# Railway PostgreSQL (obtain from Railway dashboard)
DATABASE_URL=postgresql://user:password@your_host.proxy.rlwy.net:port/railway

# Langfuse (Observability)
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# סיסמת הכניסה לאפליקציה
APP_PASSWORD=your_password_here
```

> ⚠️ **חשוב:** אותו קוד רץ מקומית ובענן - הפונקציה `get_env` מחפשת קודם ב-`.env` המקומי, ואם לא נמצא - במשתני הסביבה של הפלטפורמה (Railway). בפריסה מגדירים את אותם משתנים בדשבורד של Railway.

### Step 1: Install & Run

```bash
# 1. Clone
git clone https://github.com/Tamirariel/powertracker-ai.git
cd powertracker-ai

# 2. Virtual environment + dependencies
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# 3. Run
streamlit run FRONT/main.py
```

היכנסו ל-http://localhost:8501 - טבלאות מסד הנתונים נוצרות אוטומטית בעלייה הראשונה (`init_db`).

### Step 2 (Optional): Retrain the Models

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

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit 1.59 (Hebrew RTL, Custom Dark Theme) |
| AI Agent | Anthropic Claude (claude-sonnet-4-6) + Tool Use |
| ML Models | scikit-learn - KMeans, Random Forest, Linear Regression |
| Vector DB (RAG) | ChromaDB |
| Database | PostgreSQL (psycopg2) |
| Observability | Langfuse (Tracing) + OpenTelemetry |
| Data | OpenPowerlifting Dataset (1M+ competition results) |
| Deployment | Railway (Nixpacks) |

## 📖 About This Project

הפרויקט נבנה כפרויקט גמר בקורס **מהנדסי AI** - האקדמיה להייטק מבית "העברית הכשרת מנהלים", האוניברסיטה העברית בירושלים.

הוא מדגים pipeline מלא של מערכת AI: איסוף וניקוי דאטה → אימון מודלי ML → סוכן LLM עם כלים ו-RAG → ניטור → פריסה בענן.

פותח על ידי **Tamir Ariel**.

---

*התובנות באפליקציה מבוססות על נתוני תחרויות אמיתיים אך אינן מהוות ייעוץ אימוני מקצועי.*