#עמוד הפאוורליפטינג . שיאים משוערים , גרפי התקדמות וקצב אישי
import streamlit as st
import pandas as pd
import requests
from auth import check_password

API_URL = "http://localhost:8000"


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


@st.cache_data(ttl=60, show_spinner=False)
def api_get_cached(path, default=None):
    return api_get(path, default)


def api_post(path, payload, timeout=30):
    try:
        res = requests.post(f"{API_URL}{path}", json=payload, timeout=timeout)
        res.raise_for_status()
        st.cache_data.clear()
        return res.json()
    except requests.exceptions.RequestException as e:
        st.error(f"שגיאה: {e}")
        return None


#שאלת הסוכן . ההקשר (פרופיל + יומן) נבנה בשרת , אז שולחים רק את השאלה
def ask_agent(question):
    result = api_post("/chat", {"question": question}, timeout=120)
    return result["answer"] if result else None


st.set_page_config(
    page_title="פאוורליפטינג",
    page_icon="🏋️",
    layout="centered",
)
check_password()

st.markdown("""
<style>
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp .stCaption, .stApp label { direction: rtl; text-align: right; }
    [data-testid="stSidebarContent"] * { text-align: right; }
    [data-testid="stExpander"] summary { direction: rtl; }
    .stChatMessage { direction: rtl; text-align: right; }
</style>
""", unsafe_allow_html=True)


st.title("פאוורליפטינג")
st.caption("הנתונים כאן נשלפים אוטומטית מיומן האימונים . כל סט של סקוואט , בנץ או דדליפט שנשמר ביומן מופיע כאן")


#פרופיל משותף עם שאר העמודים
if "profile" not in st.session_state:
    st.session_state.profile = api_get(
        "/profile", {"sex": None, "age": None, "bodyweight": None}
    )


with st.expander("הפרופיל שלי", expanded=st.session_state.profile["age"] is None):
    sex_options = ["זכר", "נקבה"]
    saved_sex = st.session_state.profile["sex"]
    sex_index = sex_options.index(saved_sex) if saved_sex in sex_options else 0
    sex = st.radio("מגדר", sex_options, horizontal=True, index=sex_index)
    age = st.number_input("גיל (חובה)", min_value=10, max_value=100,
                          value=st.session_state.profile["age"], placeholder="הזן גיל")
    bodyweight = st.number_input("משקל גוף בקג (חובה)", min_value=30.0, max_value=250.0,
                                 value=st.session_state.profile["bodyweight"],
                                 step=0.5, placeholder="הזן משקל")

    if st.button("שמור פרופיל", use_container_width=True):
        if age is None or bodyweight is None:
            st.error("חובה להזין גיל ומשקל גוף")
        else:
            saved = api_post("/profile", {"sex": sex, "age": age, "bodyweight": bodyweight})
            if saved is not None:
                st.session_state.profile = {"sex": sex, "age": age, "bodyweight": bodyweight}
                st.success("הפרופיל נשמר")


st.divider()


#כל החישובים מגיעים מהשרת בבקשה אחת
data = api_get_cached("/powerlifting/progress", {"lifts": [], "total": None})
p = st.session_state.profile

for lift in data["lifts"]:
    lift_name = lift["name"]
    st.header(lift_name)

    if lift["best_1rm"] is None:
        st.caption(f"עדיין אין אימוני {lift_name} ביומן")
        st.divider()
        continue

    best = lift["best_1rm"]
    slope = lift["slope"]

    col1, col2 = st.columns(2)
    with col1:
        st.metric("שיא משוער (1RM)", f"{best:.1f} קג")
    with col2:
        if slope is not None:
            st.metric("קצב אישי", f"{slope:+.2f} קג/חודש")
        else:
            st.metric("קצב אישי", "צריך עוד אימונים")

    #גרף התקדמות . מוצג רק אם יש יותר מנקודה אחת
    if len(lift["points"]) > 1:
        df = pd.DataFrame(lift["points"])
        st.line_chart(df, x="date", y="est_1rm", height=250)

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button(f"השווה אותי לאחרים - {lift_name}",
                     key=f"compare_{lift_name}", use_container_width=True):
            if p["age"] is None:
                st.error("צריך לשמור פרופיל קודם")
            else:
                with st.spinner("בודק את הנתונים..."):
                    answer = ask_agent(
                        f"אני מרים {best:.0f} קג ב{lift_name} (1RM משוער). "
                        f"איפה אני עומד ביחס לאחרים?"
                    )
                if answer:
                    st.markdown(answer)

    with col_b:
        if st.button(f"חזה את הקצב שלי - {lift_name}",
                     key=f"predict_{lift_name}", use_container_width=True):
            if p["age"] is None:
                st.error("צריך לשמור פרופיל קודם")
            else:
                with st.spinner("מחשב..."):
                    answer = ask_agent(
                        f"אני מרים {best:.0f} קג ב{lift_name}. "
                        f"מה קצב ההתקדמות הצפוי שלי?"
                    )
                if answer:
                    st.markdown(answer)
                    if slope is not None:
                        st.info(f"לפי היומן שלך , הקצב האמיתי שלך כרגע הוא {slope:+.2f} קג לחודש")

    st.divider()


#טוטאל . מוצג רק אם יש נתונים בשלושת הליפטים
if data["total"] is not None:
    st.header("טוטאל")
    st.metric("סכום שלושת השיאים", f"{data['total']:.1f} קג")

    if st.button("השווה את הטוטאל שלי לאחרים", use_container_width=True):
        if p["age"] is None:
            st.error("צריך לשמור פרופיל קודם")
        else:
            with st.spinner("בודק את הנתונים..."):
                answer = ask_agent(
                    f"הטוטאל שלי הוא {data['total']:.0f} קג. איפה אני עומד ביחס לאחרים?"
                )
            if answer:
                st.markdown(answer)