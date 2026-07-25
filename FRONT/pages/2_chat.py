#עמוד הצאט . שיח עם הסוכן

import streamlit as st
import requests
from auth import check_password

API_URL = "http://localhost:8000"


#הגדרות עמוד
st.set_page_config(
    page_title="צ'אט",
    page_icon="💬",
    layout="centered",
)
check_password()

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

#פרופיל משותף עם שאר העמודים . בפעם הראשונה בסשן טוענים מה-DB במקום להתחיל ריק
if "profile" not in st.session_state:
    try:
        st.session_state.profile = requests.get(f"{API_URL}/profile", timeout=10).json()
    except requests.exceptions.RequestException:
        st.session_state.profile = {"sex": None, "age": None, "bodyweight": None}



#סרגל צד . פרופיל בלבד - היומן עבר לעמוד הראשי
with st.sidebar:
    st.header("הפרופיל שלי")

    #בחירת המגדר השמור כברירת מחדל - אחרת התפריט תמיד יראה "זכר" גם אם שמרת "נקבה"
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
            requests.post(
                f"{API_URL}/profile",
                json={"sex": sex, "age": age, "bodyweight": bodyweight},
                timeout=10,
            )
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
    with st.chat_message("user"):
        st.markdown(question)
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("assistant"):
        with st.spinner("בודק את הנתונים..."):
            try:
                res = requests.post(
                    f"{API_URL}/chat",
                    json={"question": question},
                    timeout=120,
                )
                res.raise_for_status()
                answer = res.json()["answer"]
            except requests.exceptions.RequestException as e:
                answer = f"שגיאה בחיבור לשרת: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})