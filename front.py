#ממשק המשתמש בנוגע ליומן האימונים . יצירת האימונים הבאים , עדכון אימונים קודמים . חיבור לקובץ הדטא בייס 




import streamlit as st
from datetime import date
import database

#יצירת הטבלאות אם לא קיימות . בטוח להריץ בכל עליית עמוד
database.init_db()


#הגדרות עמוד
st.set_page_config(
    page_title="יומן אימונים",
    page_icon="📋",
    layout="centered",
)


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


#איחוד הרשימה הבסיסית עם תרגילים שהוזנו ידנית בעבר . ככה תרגיל שהוקלד פעם מופיע מעכשיו ברשימה
saved_names = database.get_all_exercise_names()
EXERCISE_LIST = BASE_EXERCISE_LIST + [name for name in saved_names if name not in BASE_EXERCISE_LIST]
EXERCISE_LIST.append('אחר')


#אתחול האימון הנוכחי שנבנה . רשימת תרגילים במבנה המקונן של הDB
if "current_exercises" not in st.session_state:
    st.session_state.current_exercises = []


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
last_workout = database.get_last_workout_by_type(w_type)
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


#הצגת התרגילים שנוספו . לכל תרגיל אפשר להוסיף ולמחוק סטים . זהו הבריף
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
    #תזכורת בולטת לאן האימון הולך להישמר . מונע שמירה בתאריך לא נכון
    st.info(f"האימון יישמר בתאריך {w_date.strftime('%d/%m/%Y')} כאימון {w_type}")
    col_save, col_clear = st.columns([3, 1])

    with col_save:
        if st.button("שמור אימון", type="primary", use_container_width=True):
            #בדיקה שאין תרגיל בלי סטים
            empty_exercises = [ex['name'] for ex in st.session_state.current_exercises if not ex['sets']]
            if empty_exercises:
                st.error(f"יש תרגילים בלי סטים: {', '.join(empty_exercises)}")
            else:
                workout_id = database.save_workout(str(w_date), w_type, st.session_state.current_exercises)
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


#היסטוריית אימונים . מהחדש לישן
st.header("היסטוריה")

all_workouts = database.get_all_workouts()

if not all_workouts:
    st.caption("עדיין לא נשמרו אימונים")

for w in all_workouts:
    with st.expander(f"{w['date']} | {w['workout_type']}"):
        details = database.get_workout_details(w['id'])
        for exercise in details['exercises']:
            sets_text = " , ".join(f"{s['reps']}x{s['weight']}" for s in exercise['sets'])
            st.text(f"{exercise['name']}: {sets_text}")

        if st.button("מחק אימון", key=f"delete_{w['id']}"):
            database.delete_workout(w['id'])
            st.rerun()