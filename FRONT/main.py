#ממשק המשתמש בנוגע ליומן האימונים . יצירת האימונים הבאים , עדכון אימונים קודמים
import streamlit as st
from datetime import date
import calendar
import requests
from auth import check_password

API_URL = "http://localhost:8000"

#עוזר לקריאות מה-API . מחזיר ברירת מחדל אם השרת לא זמין
#עוזר לקריאות מה-API . 404 הוא תשובה תקינה (אין נתון) , שאר השגיאות מוצגות
def api_get(path, default=None):
    try:
        res = requests.get(f"{API_URL}{path}", timeout=30)
        if res.status_code == 404:
            return default
        res.raise_for_status()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"שגיאה בקריאה ל-{path}: {e}")
        return default
#קריאה עם קאש . הסקריפט רץ מחדש בכל לחיצה - בלי זה זו בקשה חדשה בכל פעם
@st.cache_data(ttl=60, show_spinner=False)
def api_get_cached(path, default=None):
    return api_get(path, default)
#קריאות כתיבה . מנקות את הקאש כדי שהתצוגה תתעדכן מיד
def api_post(path, payload):
    try:
        res = requests.post(f"{API_URL}{path}", json=payload, timeout=30)
        res.raise_for_status()
        st.cache_data.clear()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"שגיאה בשמירה: {e}")
        return None


def api_delete(path):
    try:
        res = requests.delete(f"{API_URL}{path}", timeout=30)
        res.raise_for_status()
        st.cache_data.clear()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"שגיאה במחיקה: {e}")
        return False

#הגדרות עמוד
st.set_page_config(
    page_title="יומן אימונים",
    page_icon="📋",
    layout="centered",
)
check_password()

#יישור לימין - כל האפליקציה בעברית
st.markdown("""
<style>
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp .stCaption, .stApp label { direction: rtl; text-align: right; }
    [data-testid="stSidebarContent"] * { text-align: right; }
    [data-testid="stExpander"] summary { direction: rtl; }
</style>
""", unsafe_allow_html=True)


#רשימת תרגילים בסיסית . שלושת הראשונים הם תרגילי הפאוורליפטינג ואסור לשנות את האיות שלהם
BASE_EXERCISE_LIST = [
    'סקוואט', 'בנץ', 'דדליפט',
    'לחיצת רגליים', 'לחיצת כתפיים', 'עליות מתח', 'חתירה',
    'פולי עליון', 'לחיצת חזה בשיפוע', 'כפיפת מרפקים', 'פשיטת מרפקים',
    'לאנג׳ים', 'כפיפת ברכיים', 'הרחקות כתף', 'בטן',
]

WORKOUT_TYPES = ['רגליים', 'חזה', 'גב', 'כתפיים', 'ידיים', 'גוף מלא']

#צבע לכל סוג אימון . לתגית הצבעונית בכרטיס הפרטים
WORKOUT_TYPE_COLORS = {
    'רגליים': '#F2B705',
    'חזה': '#2DD4BF',
    'גב': '#818CF8',
    'כתפיים': '#FB7185',
    'ידיים': '#34D399',
    'גוף מלא': '#F472B6',
}

HEBREW_MONTHS = ['ינואר', 'פברואר', 'מרץ', 'אפריל', 'מאי', 'יוני',
                  'יולי', 'אוגוסט', 'ספטמבר', 'אוקטובר', 'נובמבר', 'דצמבר']


#איחוד הרשימה הבסיסית עם תרגילים שהוזנו ידנית בעבר . ככה תרגיל שהוקלד פעם מופיע מעכשיו ברשימה
saved_names = api_get_cached("/exercises/names", [])
EXERCISE_LIST = BASE_EXERCISE_LIST + [name for name in saved_names if name not in BASE_EXERCISE_LIST]
EXERCISE_LIST.append('אחר')


#אתחול האימון הנוכחי שנבנה . רשימת תרגילים במבנה המקונן של הDB
if "current_exercises" not in st.session_state:
    st.session_state.current_exercises = []

#אתחול לוח השנה . מוצג תמיד החודש הנוכחי בכניסה ראשונה
if "calendar_month" not in st.session_state:
    today = date.today()
    st.session_state.calendar_month = date(today.year, today.month, 1)

#היום שנבחר בלוח השנה . כדי להציג את פרטי האימון שלו למטה
if "selected_day" not in st.session_state:
    st.session_state.selected_day = None


st.title("יומן אימונים")


#בניית אימון חדש
st.header("אימון חדש")

w_date = st.date_input("תאריך", value=date.today())
w_type = st.selectbox("סוג אימון", WORKOUT_TYPES)


#זיהוי שינוי תאריך באמצע הזנת אימון . מונע איחוד שני אימונים בטעות
if st.session_state.current_exercises and "form_started_date" in st.session_state:
    if w_date != st.session_state.form_started_date:
        st.warning(f"שים לב: התחלת את הטופס בתאריך {st.session_state.form_started_date.strftime('%d/%m/%Y')} "
                   f"ועכשיו נבחר {w_date.strftime('%d/%m/%Y')} . כל התרגילים בטופס יישמרו יחד בתאריך החדש . "
                   f"אם התכוונת לאימון נפרד - שמור או נקה את הטופס קודם")


#פיצר השכפול . מוצג רק אם קיים אימון קודם מאותו סוג
last_workout = api_get_cached(f"/workouts/last/{w_type}")
if last_workout is not None:
    if st.button(f"שכפל את אימון ה{w_type} מ-{last_workout['date']}", use_container_width=True):
        #אזהרה אם כבר התחלת להזין אימון . שלא יידרס בטעות
        if st.session_state.current_exercises:
            st.warning("יש כבר תרגילים בטופס . אם אתה רוצה לשכפל בכל זאת נקה קודם עם הכפתור למטה")
        else:
            st.session_state.form_started_date = w_date
            st.session_state.current_exercises = last_workout['exercises']
            st.rerun()


#הוספת תרגיל לאימון הנוכחי
with st.expander("הוסף תרגיל"):
    ex_choice = st.selectbox("תרגיל", EXERCISE_LIST)
    if ex_choice == 'אחר':
        ex_name = st.text_input("שם התרגיל")
    else:
        ex_name = ex_choice

    if st.button("הוסף תרגיל לאימון", use_container_width=True):
        if not ex_name:
            st.error("צריך לבחור או להקליד שם תרגיל")
        else:
            #זכירת התאריך שבו התחיל הטופס . לזיהוי שינוי תאריך באמצע
            if not st.session_state.current_exercises:
                st.session_state.form_started_date = w_date
            st.session_state.current_exercises.append({'name': ex_name, 'sets': []})
            st.rerun()


#הצגת התרגילים שנוספו . התרגיל האחרון שנוסף מוצג ראשון - הפוך מסדר השמירה
for i, exercise in reversed(list(enumerate(st.session_state.current_exercises))):
    st.subheader(exercise['name'])

    #הצגת הסטים הקיימים עם כפתור מחיקה לכל סט
    for j, s in enumerate(exercise['sets']):
        col_text, col_del = st.columns([4, 1])
        with col_text:
            st.text(f"סט {j+1}: {s['reps']} חזרות | {s['weight']} קג")
        with col_del:
            if st.button("מחק", key=f"del_set_{i}_{j}"):
                exercise['sets'].pop(j)
                st.rerun()

    #שורת הוספת סטים . אפשר להוסיף כמה סטים זהים במכה אחת
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    with col1:
        num_sets = st.number_input("סטים", min_value=1, max_value=15, value=1, key=f"num_sets_{i}")
    with col2:
        reps = st.number_input("חזרות", min_value=1, max_value=100, value=8, key=f"reps_{i}")
    with col3:
        weight = st.number_input("משקל (קג)", min_value=0.0, max_value=600.0, value=50.0, step=2.5, key=f"weight_{i}")
    with col4:
        st.write("")
        st.write("")
        if st.button("הוסף", key=f"add_set_{i}"):
            for _ in range(num_sets):
                exercise['sets'].append({'reps': reps, 'weight': weight})
            st.rerun()

    #הסרת תרגיל מהאימון הנוכחי
    if st.button("הסר תרגיל", key=f"remove_ex_{i}"):
        st.session_state.current_exercises.pop(i)
        st.rerun()

    st.divider()


#כפתורי שמירה וניקוי . מוצגים רק אם יש תרגילים בטופס
if st.session_state.current_exercises:
    col_save, col_clear = st.columns([3, 1])

    with col_save:
        if st.button("שמור אימון", type="primary", use_container_width=True):
            #בדיקה שאין תרגיל בלי סטים
            empty_exercises = [ex['name'] for ex in st.session_state.current_exercises if not ex['sets']]
            if empty_exercises:
                st.error(f"יש תרגילים בלי סטים: {', '.join(empty_exercises)}")
            else:
                result = api_post("/workouts", {
                    "date": str(w_date),
                    "workout_type": w_type,
                    "exercises": st.session_state.current_exercises,
                })
                if result is not None:
                    st.session_state.current_exercises = []
                    st.session_state.pop("form_started_date", None)
                    st.success("האימון נשמר!")
                    st.rerun()

    with col_clear:
        if st.button("נקה טופס", use_container_width=True):
            st.session_state.current_exercises = []
            st.session_state.pop("form_started_date", None)
            st.rerun()


st.divider()


#היסטוריה - לוח שנה
st.header("היסטוריה")


#מעבר חודש קודם . מנקה יום נבחר כדי לא לבלבל בין חודשים
def go_prev_month():
    d = st.session_state.calendar_month
    if d.month == 1:
        st.session_state.calendar_month = date(d.year - 1, 12, 1)
    else:
        st.session_state.calendar_month = date(d.year, d.month - 1, 1)
    st.session_state.selected_day = None


#מעבר חודש הבא . מנקה יום נבחר כדי לא לבלבל בין חודשים
def go_next_month():
    d = st.session_state.calendar_month
    if d.month == 12:
        st.session_state.calendar_month = date(d.year + 1, 1, 1)
    else:
        st.session_state.calendar_month = date(d.year, d.month + 1, 1)
    st.session_state.selected_day = None


#בניית מילון תאריך -> רשימת אימונים . לשימוש בצביעת ימים בלוח
#בניית מילון תאריך -> רשימת אימונים . כולל תרגילים וסטים בבקשה אחת
def build_workouts_by_date():
    workouts = api_get_cached("/workouts/full", [])
    by_date = {}
    for w in workouts:
        by_date.setdefault(w['date'], []).append(w)
    return by_date


#כותרת הלוח עם ניווט בין חודשים
#שים לב - עמודות סטרימליט הן LTR באופיין , אז מציבים "הבא" בעמודה הראשונה (משמאל)
#ו"הקודם" בעמודה האחרונה (מימין) - כדי שהניווט ירגיש טבעי בעברית
col_next, col_label, col_prev = st.columns([1, 3, 1])
with col_next:
    if st.button("הבא ›", use_container_width=True):
        go_next_month()
        st.rerun()
with col_label:
    cm = st.session_state.calendar_month
    st.markdown(
        f"<h3 style='text-align:center;'>{HEBREW_MONTHS[cm.month - 1]} {cm.year}</h3>",
        unsafe_allow_html=True
    )
with col_prev:
    if st.button("‹ הקודם", use_container_width=True):
        go_prev_month()
        st.rerun()


#כותרות ימות השבוע . מהופכות מאותה סיבה - כדי שראשון יופיע מימין כמו בלוח שנה עברי
weekdays_rtl = ['ש', 'ו', 'ה', 'ד', 'ג', 'ב', 'א']
header_cols = st.columns(7)
for col, wd in zip(header_cols, weekdays_rtl):
    col.markdown(f"<div style='text-align:center; font-weight:bold; opacity:0.7;'>{wd}</div>", unsafe_allow_html=True)


#בניית רשת הימים . firstweekday=6 אומר שהשבוע מתחיל ביום ראשון (calendar סופר שני=0)
cal = calendar.Calendar(firstweekday=6)
month_days = cal.monthdayscalendar(cm.year, cm.month)
workouts_by_date = build_workouts_by_date()
today = date.today()

for week in month_days:
    #היפוך סדר הימים בשבוע מאותה סיבת LTR - כדי שראשון יהיה מימין
    week_rtl = list(reversed(week))
    day_cols = st.columns(7)
    for col, day_num in zip(day_cols, week_rtl):
        if day_num == 0:
            col.write("")
            continue

        day_date = date(cm.year, cm.month, day_num)
        date_str = day_date.isoformat()
        has_workout = date_str in workouts_by_date

        label = f"{day_num} 🔥" if has_workout else f"{day_num}"
        if day_date == today:
            label += " •"

        btn_type = "primary" if has_workout else "secondary"
        if col.button(label, key=f"day_{date_str}", type=btn_type, use_container_width=True):
            st.session_state.selected_day = date_str
            st.rerun()

st.caption("🔥 = יום עם אימון | • = היום")


#הצגת פרטי היום שנבחר בלוח
if st.session_state.selected_day:
    sel = st.session_state.selected_day
    st.divider()

    workouts_today = workouts_by_date.get(sel, [])
    if workouts_today:
        for w in workouts_today:
            with st.container(border=True):
                color = WORKOUT_TYPE_COLORS.get(w['workout_type'], '#F2B705')
                st.markdown(
                    f"<div style='direction:rtl; text-align:right;'>"
                    f"<span style='background:{color}; color:#12141C; padding:3px 12px; "
                    f"border-radius:999px; font-weight:600; font-size:0.9em;'>{w['workout_type']}</span> "
                    f"&nbsp; <b>{sel}</b></div>",
                    unsafe_allow_html=True
                )
                st.write("")

                for exercise in w['exercises']:
                    sets_text = " , ".join(f"{s['reps']}x{s['weight']}" for s in exercise['sets'])
                    st.write(f"**{exercise['name']}**: {sets_text}")

                if st.button("מחק אימון", key=f"delete_cal_{w['id']}"):
                    if api_delete(f"/workouts/{w['id']}"):
                        st.session_state.selected_day = None
                        st.rerun()
    else:
        st.info(f"אין אימון בתאריך {sel}")