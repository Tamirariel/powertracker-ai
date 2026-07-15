import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import sys, os
from auth import check_password
#הוספת תיקיית BACK ל-sys.path . הקובץ הזה ב-FRONT/pages , שתי רמות מעל זה myapp
PAGE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONT_DIR = os.path.dirname(PAGE_DIR)
APP_ROOT = os.path.dirname(FRONT_DIR)
BACK_DIR = os.path.join(APP_ROOT, 'BACK')
sys.path.append(BACK_DIR)

import database
from agent import ask_full_agent

database.init_db()


#הגדרות עמוד
st.set_page_config(
    page_title="פאוורליפטינג",
    page_icon="🏋️",
    layout="centered",
)
check_password()

#יישור לימין - כל האפליקציה בעברית
st.markdown("""
<style>
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp .stCaption, .stApp label { direction: rtl; text-align: right; }
    [data-testid="stSidebarContent"] * { text-align: right; }
    [data-testid="stExpander"] summary { direction: rtl; }
    .stChatMessage { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)


#שלושת תרגילי הפאוורליפטינג . האיות חייב להתאים בדיוק לרשימה בעמוד היומן
POWER_LIFTS = ['סקוואט', 'בנץ', 'דדליפט']

#מיפוי לשמות העמודות שהמודלים מכירים
LIFT_COLUMN_MAP = {
    'סקוואט': 'Best3SquatKg',
    'בנץ': 'Best3BenchKg',
    'דדליפט': 'Best3DeadliftKg',
}


#הערכת 1RM לפי נוסחת Epley . מתרגם סט עבודה לשווה ערך של הרמה מקסימלית אחת
def epley_1rm(weight, reps):
 if reps == 1:
     return weight
 return weight * (1 + reps / 30)


#בניית טבלת התקדמות לתרגיל . לכל תאריך לוקחים את הסט עם ה1RM המשוער הגבוה ביותר
def build_progress_table(lift_name):
 history = database.get_exercise_history(lift_name)
 if not history:
     return None

 df = pd.DataFrame(history)
 df['est_1rm'] = df.apply(lambda row: epley_1rm(row['weight'], row['reps']), axis=1)

 #השיא המשוער של כל יום אימון
 daily_best = df.groupby('date')['est_1rm'].max().reset_index()
 daily_best['date'] = pd.to_datetime(daily_best['date'])
 daily_best = daily_best.sort_values('date')
 return daily_best


#חישוב קצב התקדמות אישי בקג לחודש . אותה שיטה כמו במודלים - רגרסיה לינארית
def personal_slope(daily_best):
 #צריך לפחות שתי נקודות זמן שונות
 if len(daily_best) < 2:
     return None

 months = (daily_best['date'] - daily_best['date'].min()).dt.days / 30.44
 #אם כל האימונים באותו יום אין שיפוע
 if months.max() == 0:
     return None

 x = months.values.reshape(-1, 1)
 y = daily_best['est_1rm']
 model = LinearRegression()
 model.fit(x, y)
 return model.coef_[0]


st.title("פאוורליפטינג")
st.caption("הנתונים כאן נשלפים אוטומטית מיומן האימונים . כל סט של סקוואט , בנץ או דדליפט שנשמר ביומן מופיע כאן")


#פרופיל משותף עם שאר העמודים . בפעם הראשונה בסשן טוענים מה-DB במקום להתחיל ריק
if "profile" not in st.session_state:
    saved_profile = database.get_profile()
    if saved_profile is not None:
        st.session_state.profile = saved_profile
    else:
        st.session_state.profile = {"sex": None, "age": None, "bodyweight": None}



with st.expander("הפרופיל שלי", expanded=st.session_state.profile["age"] is None):
    #בחירת המגדר השמור כברירת מחדל בתפריט - אחרת הוא תמיד יראה "זכר" גם אם שמרת "נקבה"
    sex_options = ["זכר", "נקבה"]
    saved_sex = st.session_state.profile["sex"]
    sex_index = sex_options.index(saved_sex) if saved_sex in sex_options else 0
    sex = st.radio("מגדר", sex_options, horizontal=True, index=sex_index)
    age = st.number_input("גיל (חובה)", min_value=10, max_value=100, value=st.session_state.profile["age"], placeholder="הזן גיל")
    bodyweight = st.number_input("משקל גוף בקג (חובה)", min_value=30.0, max_value=250.0, value=st.session_state.profile["bodyweight"], step=0.5, placeholder="הזן משקל")

    if st.button("שמור פרופיל", use_container_width=True):
        if age is None or bodyweight is None:
            st.error("חובה להזין גיל ומשקל גוף")
        else:
            st.session_state.profile = {"sex": sex, "age": age, "bodyweight": bodyweight}
            #שמירה גם לDB - כדי שהפרופיל ישרוד סגירת דפדפן
            database.save_profile(sex, age, bodyweight)
            st.success("הפרופיל נשמר")


st.divider()


#מעבר על שלושת הליפטים . לכל אחד : שיא נוכחי , גרף התקדמות , קצב אישי , וכפתורי הסוכן
current_bests = {}

for lift_name in POWER_LIFTS:
    st.header(lift_name)

    daily_best = build_progress_table(lift_name)

    if daily_best is None:
        st.caption(f"עדיין אין אימוני {lift_name} ביומן")
        st.divider()
        continue

    #שיא נוכחי משוער
    best = daily_best['est_1rm'].max()
    current_bests[lift_name] = best
    slope = personal_slope(daily_best)

    col1, col2 = st.columns(2)
    with col1:
        st.metric("שיא משוער (1RM)", f"{best:.1f} קג")
    with col2:
        if slope is not None:
            st.metric("קצב אישי", f"{slope:+.2f} קג/חודש")
        else:
            st.metric("קצב אישי", "צריך עוד אימונים")

    #גרף התקדמות . מוצג רק אם יש יותר מנקודה אחת
    if len(daily_best) > 1:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.plot(daily_best['date'], daily_best['est_1rm'], marker='o')
        ax.set_ylabel('Estimated 1RM (kg)')
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    #כפתורי הסוכן . עובדים רק עם פרופיל שמור
    p = st.session_state.profile
    col_a, col_b = st.columns(2)

    with col_a:
        if st.button(f"השווה אותי לאחרים - {lift_name}", key=f"compare_{lift_name}", use_container_width=True):
            if p["age"] is None:
                st.error("צריך לשמור פרופיל קודם")
            else:
                question = (
                    f"אני {'גבר' if p['sex'] == 'זכר' else 'אישה'} בגיל {p['age']}, "
                    f"שוקל {p['bodyweight']} קג ומרים {best:.0f} קג ב{lift_name} (1RM משוער). "
                    f"איפה אני עומד ביחס לאחרים?"
                )
                with st.spinner("בודק את הנתונים..."):
                    answer = ask_full_agent(question)
                st.markdown(answer)

    with col_b:
        if st.button(f"חזה את הקצב שלי - {lift_name}", key=f"predict_{lift_name}", use_container_width=True):
            if p["age"] is None:
                st.error("צריך לשמור פרופיל קודם")
            else:
                question = (
                    f"אני {'גבר' if p['sex'] == 'זכר' else 'אישה'} בגיל {p['age']}, "
                    f"שוקל {p['bodyweight']} קג ומרים {best:.0f} קג ב{lift_name}. "
                    f"מה קצב ההתקדמות הצפוי שלי?"
                )
                with st.spinner("מחשב..."):
                    answer = ask_full_agent(question)
                st.markdown(answer)

                #השוואה בין החיזוי לקצב האמיתי מהיומן
                if slope is not None:
                    st.info(f"לפי היומן שלך , הקצב האמיתי שלך כרגע הוא {slope:+.2f} קג לחודש")

    st.divider()


#טוטאל . סכום השיאים של שלושת הליפטים . מוצג רק אם יש נתונים בשלושתם
if len(current_bests) == 3:
    total = sum(current_bests.values())
    st.header("טוטאל")
    st.metric("סכום שלושת השיאים", f"{total:.1f} קג")

    p = st.session_state.profile
    if st.button("השווה את הטוטאל שלי לאחרים", use_container_width=True):
        if p["age"] is None:
            st.error("צריך לשמור פרופיל קודם")
        else:
            question = (
                f"אני {'גבר' if p['sex'] == 'זכר' else 'אישה'} בגיל {p['age']}, "
                f"שוקל {p['bodyweight']} קג והטוטאל שלי הוא {total:.0f} קג. "
                f"איפה אני עומד ביחס לאחרים?"
            )
            with st.spinner("בודק את הנתונים..."):
                answer = ask_full_agent(question)
            st.markdown(answer)