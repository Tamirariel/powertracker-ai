#שער סיסמה בסיסי לאפליקציה . נבדק בתחילת כל עמוד (front.py + כל page) לפני שמציגים תוכן
import streamlit as st
import os
from dotenv import load_dotenv

#auth.py יושב ב-FRONT , וה-.env יושב ב-BACK (תיקייה אחות) . אז בונים את הנתיב במפורש
_FRONT_DIR = os.path.dirname(os.path.abspath(__file__))
_BACK_DIR = os.path.join(os.path.dirname(_FRONT_DIR), 'BACK')
_ENV_PATH = os.path.join(_BACK_DIR, '.env')

#טוען מהנתיב המפורש . אם הקובץ לא קיים (כמו ב-Railway) - לא קורה כלום, וממשיכים ל-os.environ
load_dotenv(_ENV_PATH)


def check_password():
    #אם כבר התחברנו בהצלחה במהלך ה-session הזה - לא מציגים שוב את מסך הסיסמה
    if st.session_state.get("authenticated", False):
        return

    st.title("PowerTracker")
    st.subheader("כניסה")

    correct_password = os.environ.get("APP_PASSWORD")

    if not correct_password:
        st.error("לא הוגדרה סיסמה למערכת (משתנה APP_PASSWORD חסר) . פנה למנהל המערכת")
        st.stop()

    password_input = st.text_input("סיסמה", type="password", key="app_password_input")

    if st.button("כניסה", key="app_password_submit"):
        if password_input == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("סיסמה שגויה")

    #עוצר את הריצה כאן . שום דבר מתחת (יומן, לוח שנה וכו') לא ייטען עד שההתחברות מצליחה
    st.stop()