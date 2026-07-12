import streamlit as st
from datetime import date
from APIֹ_key import ask_full_agent


#הגדרות עמוד
st.set_page_config(
    page_title="PowerTracker",
    page_icon="🏋️",
    layout="centered",
)


#יישור לימין - כל האפליקציה בעברית
st.markdown("""
<style>
    .stChatMessage { direction: rtl; text-align: right; }
    [data-testid="stChatInput"] textarea { direction: rtl; }
    [data-testid="stSidebarContent"] * { text-align: right; }
    .stApp h1, .stApp p, .stApp .stCaption { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)


#אתחול היסטוריית שיחה
if "messages" not in st.session_state:
    st.session_state.messages = []

#אתחול פרופיל משתמש - נשמר בין שאלות
if "profile" not in st.session_state:
    st.session_state.profile = {"sex": None, "age": None, "bodyweight": None}

#אתחול יומן אימונים - רשימה של אימונים שהוזנו
if "workouts" not in st.session_state:
    st.session_state.workouts = []


#סרגל צד
with st.sidebar:
    st.header("הפרופיל שלי")

    #נתוני משתמש . גיל ומשקל בלי ברירת מחדל כדי שהמשתמש יזין אותם בעצמו
    sex = st.radio("מגדר", ["זכר", "נקבה"], horizontal=True)
    age = st.number_input("גיל (חובה)", min_value=10, max_value=100, value=None, placeholder="הזן גיל")
    bodyweight = st.number_input("משקל גוף בקג (חובה)", min_value=30.0, max_value=250.0, value=None, step=0.5, placeholder="הזן משקל")

    #שמירת הפרופיל רק אם הוזנו גיל ומשקל . המודלים חייבים אותם
    if st.button("שמור פרופיל", use_container_width=True):
        if age is None or bodyweight is None:
            st.error("חובה להזין גיל ומשקל גוף")
        else:
            st.session_state.profile = {"sex": sex, "age": age, "bodyweight": bodyweight}
            st.success("הפרופיל נשמר")

    st.divider()

    #הוספת אימון ליומן
    st.header("יומן אימונים")

    with st.expander("הוסף אימון"):
        w_lift = st.selectbox("תרגיל", ["סקוואט", "בנץ", "דדליפט"])
        w_value = st.number_input("משקל (קג)", min_value=1.0, max_value=600.0, value=100.0, step=2.5)
        w_date = st.date_input("תאריך", value=date.today())
        if st.button("הוסף", use_container_width=True):
            st.session_state.workouts.append({
                "lift": w_lift,
                "value": w_value,
                "date": w_date.strftime("%d/%m/%Y"),
            })
            st.success("האימון נוסף")

    #הצגת 5 האימונים האחרונים מהחדש לישן
    if st.session_state.workouts:
        st.caption("אימונים אחרונים:")
        for w in reversed(st.session_state.workouts[-5:]):
            st.text(f"{w['date']} | {w['lift']} | {w['value']} קג")
    else:
        st.caption("עדיין לא הוזנו אימונים")

    st.divider()

    #חישוב קצב התקדמות צפוי לפי הפרופיל והאימון האחרון
    st.header("קצב התקדמות")
    if st.button("חשב קצב צפוי", use_container_width=True):
        p = st.session_state.profile
        if p["age"] is None or not st.session_state.workouts:
            st.warning("צריך פרופיל שמור ולפחות אימון אחד")
        else:
            last = st.session_state.workouts[-1]
            progress_q = (
             f"אני {'גבר' if p['sex'] == 'זכר' else 'אישה'} בגיל {p['age']}, "
             f"שוקל {p['bodyweight']} קג ומרים {last['value']} קג ב{last['lift']}. "
             f"מה קצב ההתקדמות הצפוי שלי?"
             )
            with st.spinner("מחשב..."):
                answer = ask_full_agent(progress_q)
            st.session_state.messages.append({"role": "user", "content": progress_q})
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.rerun()


#אזור הצאט המרכזי
st.title("PowerTracker")
st.caption("שאל אותי על הביצועים שלך — השוואה למתאמנים אחרים, קצב התקדמות, או כל שאלה על פאוורליפטינג")

#הצגת כל היסטוריית השיחה
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

#קליטת שאלה חדשה
question = st.chat_input("לדוגמה: אני מרים 140 בסקוואט, כמה אני ביחס לאחרים?")

if question:
    #בניית הקשר מהפרופיל כדי שהמשתמש לא יצטרך לחזור על הנתונים שלו
    p = st.session_state.profile
    context_parts = []
    if p["sex"] is not None:
        context_parts.append(f"מגדר: {'גבר' if p['sex'] == 'זכר' else 'אישה'}")
    if p["age"] is not None:
        context_parts.append(f"גיל: {p['age']}")
    if p["bodyweight"] is not None:
        context_parts.append(f"משקל גוף: {p['bodyweight']} קג")

    #אם יש פרופיל שמור מצרפים אותו לשאלה
    if context_parts:
        full_question = f"[נתוני המשתמש: {', '.join(context_parts)}] {question}"
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