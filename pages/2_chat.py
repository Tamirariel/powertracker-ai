#עמוד הצאט . שיח עם הסוכן 
import streamlit as st
import database
from agent import ask_full_agent

database.init_db()


#הגדרות עמוד
st.set_page_config(
    page_title="צ'אט",
    page_icon="💬",
    layout="centered",
)


#יישור לימין - כל האפליקציה בעברית
st.markdown("""
<style>
    .stChatMessage { direction: rtl; text-align: right; }
    [data-testid="stChatInput"] textarea { direction: rtl; }
    [data-testid="stSidebarContent"] * { text-align: right; }
    .stApp h1, .stApp p, .stApp .stCaption, .stApp label { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)


#אתחול היסטוריית שיחה
if "messages" not in st.session_state:
    st.session_state.messages = []

#פרופיל משותף עם שאר העמודים
if "profile" not in st.session_state:
    st.session_state.profile = {"sex": None, "age": None, "bodyweight": None}


#בניית תמצית מהיומן . שלושת האימונים האחרונים עם התרגילים שלהם
#הסוכן מקבל את זה בהקשר כדי לענות על שאלות כמו "מה עשיתי באימון האחרון"
def build_journal_summary():
 workouts = database.get_all_workouts()
 if not workouts:
     return None

 lines = []
 for w in workouts[:3]:
     details = database.get_workout_details(w['id'])
     exercises_text = " , ".join(
         f"{ex['name']} ({len(ex['sets'])} סטים , שיא {max(s['weight'] for s in ex['sets'])} קג)"
         for ex in details['exercises']
     )
     lines.append(f"{w['date']} אימון {w['workout_type']}: {exercises_text}")

 return " | ".join(lines)


#סרגל צד . פרופיל בלבד - היומן עבר לעמוד הראשי
with st.sidebar:
    st.header("הפרופיל שלי")

    sex = st.radio("מגדר", ["זכר", "נקבה"], horizontal=True)
    age = st.number_input("גיל (חובה)", min_value=10, max_value=100, value=st.session_state.profile["age"], placeholder="הזן גיל")
    bodyweight = st.number_input("משקל גוף בקג (חובה)", min_value=30.0, max_value=250.0, value=st.session_state.profile["bodyweight"], step=0.5, placeholder="הזן משקל")

    if st.button("שמור פרופיל", use_container_width=True):
        if age is None or bodyweight is None:
            st.error("חובה להזין גיל ומשקל גוף")
        else:
            st.session_state.profile = {"sex": sex, "age": age, "bodyweight": bodyweight}
            st.success("הפרופיל נשמר")


#אזור הצאט המרכזי
st.title("PowerTracker - צ'אט")
st.caption("שאל אותי על הביצועים שלך , על האימונים מהיומן , או כל שאלה על פאוורליפטינג")

#הצגת כל היסטוריית השיחה
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

#קליטת שאלה חדשה
question = st.chat_input("לדוגמה: מה עשיתי באימון האחרון? או: אני מרים 140 בסקוואט , כמה אני ביחס לאחרים?")

if question:
    #בניית הקשר מהפרופיל ומהיומן כדי שהסוכן ידע עם מי הוא מדבר
    p = st.session_state.profile
    context_parts = []
    if p["sex"] is not None:
        context_parts.append(f"מגדר: {'גבר' if p['sex'] == 'זכר' else 'אישה'}")
    if p["age"] is not None:
        context_parts.append(f"גיל: {p['age']}")
    if p["bodyweight"] is not None:
        context_parts.append(f"משקל גוף: {p['bodyweight']} קג")

    journal_summary = build_journal_summary()
    if journal_summary is not None:
        context_parts.append(f"אימונים אחרונים מהיומן: {journal_summary}")

    #אם יש הקשר - מצרפים אותו לשאלה
    if context_parts:
        full_question = f"[נתוני המשתמש: {' | '.join(context_parts)}] {question}"
    else:
        full_question = question

    #הצגת הודעת המשתמש ושמירה בהיסטוריה
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    #קריאה לסוכן עם חיווי המתנה
    with st.chat_message("assistant"):
        with st.spinner("בודק את הנתונים..."):
            answer = ask_full_agent(full_question)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})