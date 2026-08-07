#קובץ הדטא של הפרויקט . שומר אימונים , בניית האימונים הבאים 

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
import os
from dotenv import dotenv_values

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_env(key):
    return config.get(key) or os.environ.get(key)


config = dotenv_values(os.path.join(BASE_DIR, '.env'))
DATABASE_URL = get_env('DATABASE_URL')


#בריכת חיבורים . פתיחת חיבור לענן לוקחת מאות מילישניות - שומרים אותם פתוחים ומשאילים
POOL = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL,
    cursor_factory=RealDictCursor,
)


#שאילת חיבור מהבריכה
def get_connection():
 return POOL.getconn()


#החזרת חיבור לבריכה . מחליף את release(conn) - החיבור נשאר פתוח לשימוש הבא
def release(conn):
 POOL.putconn(conn)


#יצירת כל הטבלאות אם הן לא קיימות . רץ בכל עליית אפליקציה
def init_db():
 conn = get_connection()
 cursor = conn.cursor()

 cursor.execute("""
 CREATE TABLE IF NOT EXISTS workouts (
     id SERIAL PRIMARY KEY,
     date TEXT NOT NULL,
     workout_type TEXT NOT NULL
 )
 """)

 cursor.execute("""
 CREATE TABLE IF NOT EXISTS exercises (
     id SERIAL PRIMARY KEY,
     workout_id INTEGER NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
     name TEXT NOT NULL
 )
 """)

 cursor.execute("""
 CREATE TABLE IF NOT EXISTS sets (
     id SERIAL PRIMARY KEY,
     exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE,
     set_number INTEGER NOT NULL,
     reps INTEGER NOT NULL,
     weight REAL NOT NULL
 )
 """)

 #טבלת הפרופיל . בכוונה יש בה תמיד רק שורה אחת (id=1) כי יש רק פרופיל אחד - אני
 cursor.execute("""
 CREATE TABLE IF NOT EXISTS profile (
     id INTEGER PRIMARY KEY CHECK (id = 1),
     sex TEXT,
     age INTEGER,
     bodyweight REAL
 )
 """)

 conn.commit()
 cursor.close()
 release(conn)


#שמירת אימון שלם . מקבל תאריך , סוג , ורשימת תרגילים במבנה מקונן :
#exercises_data = [ {'name': 'סקוואט', 'sets': [ {'reps': 5, 'weight': 120}, ... ]}, ... ]
def save_workout(date, workout_type, exercises_data):
 conn = get_connection()
 cursor = conn.cursor()

 #שמירת האימון וקבלת הid שלו . בPostgres צריך RETURNING id כי אין lastrowid
 cursor.execute(
     "INSERT INTO workouts (date, workout_type) VALUES (%s, %s) RETURNING id",
     (date, workout_type)
 )
 workout_id = cursor.fetchone()['id']

 #שמירת כל תרגיל והסטים שלו
 for exercise in exercises_data:
     cursor.execute(
         "INSERT INTO exercises (workout_id, name) VALUES (%s, %s) RETURNING id",
         (workout_id, exercise['name'])
     )
     exercise_id = cursor.fetchone()['id']

     for i, s in enumerate(exercise['sets'], start=1):
         cursor.execute(
             "INSERT INTO sets (exercise_id, set_number, reps, weight) VALUES (%s, %s, %s, %s)",
             (exercise_id, i, s['reps'], s['weight'])
         )

 conn.commit()
 cursor.close()
 release(conn)
 return workout_id


#שליפת רשימת כל האימונים . מהחדש לישן
def get_all_workouts():
 conn = get_connection()
 cursor = conn.cursor()
 cursor.execute(
     "SELECT id, date, workout_type FROM workouts ORDER BY date DESC, id DESC"
 )
 rows = cursor.fetchall()
 cursor.close()
 release(conn)
 return [dict(row) for row in rows]


#שליפת אימון שלם לפי id . מחזיר את אותו מבנה מקונן כמו בשמירה
def get_workout_details(workout_id):
 conn = get_connection()
 cursor = conn.cursor()

 cursor.execute(
     "SELECT id, date, workout_type FROM workouts WHERE id = %s",
     (workout_id,)
 )
 workout = cursor.fetchone()

 if workout is None:
     cursor.close()
     release(conn)
     return None

 result = dict(workout)
 result['exercises'] = []

 cursor.execute(
     "SELECT id, name FROM exercises WHERE workout_id = %s ORDER BY id",
     (workout_id,)
 )
 exercises = cursor.fetchall()

 for exercise in exercises:
     cursor.execute(
         "SELECT set_number, reps, weight FROM sets WHERE exercise_id = %s ORDER BY set_number",
         (exercise['id'],)
     )
     sets = cursor.fetchall()

     result['exercises'].append({
         'name': exercise['name'],
         'sets': [{'reps': s['reps'], 'weight': s['weight']} for s in sets]
     })

 cursor.close()
 release(conn)
 return result


#שליפת האימון האחרון מסוג מסוים . בשביל פיצר השכפול
#before מגביל לאימונים שקדמו לתאריך - כדי שעדכון רטרואקטיבי יציע את האימון הנכון
def get_last_workout_by_type(workout_type, before=None):
 conn = get_connection()
 cursor = conn.cursor()

 if before:
     cursor.execute(
         "SELECT id FROM workouts WHERE workout_type = %s AND date < %s ORDER BY date DESC, id DESC LIMIT 1",
         (workout_type, before)
     )
 else:
     cursor.execute(
         "SELECT id FROM workouts WHERE workout_type = %s ORDER BY date DESC, id DESC LIMIT 1",
         (workout_type,)
     )

 row = cursor.fetchone()
 cursor.close()
 release(conn)

 if row is None:
     return None
 return get_workout_details(row['id'])

#שליפת כל הסטים של תרגיל מסוים לאורך זמן . בשביל דף הפאוורליפטינג
#מחזיר שורות של : תאריך , חזרות , משקל
def get_exercise_history(exercise_name):
 conn = get_connection()
 cursor = conn.cursor()
 cursor.execute("""
     SELECT w.date, s.reps, s.weight
     FROM sets s
     JOIN exercises e ON s.exercise_id = e.id
     JOIN workouts w ON e.workout_id = w.id
     WHERE e.name = %s
     ORDER BY w.date, s.set_number
 """, (exercise_name,))
 rows = cursor.fetchall()
 cursor.close()
 release(conn)
 return [dict(row) for row in rows]


#מחיקת אימון שלם . הCASCADE מוחק אוטומטית גם את התרגילים והסטים שלו
def delete_workout(workout_id):
 conn = get_connection()
 cursor = conn.cursor()
 cursor.execute("DELETE FROM workouts WHERE id = %s", (workout_id,))
 conn.commit()
 cursor.close()
 release(conn)


#שליפת כל שמות התרגילים שהוזנו אי פעם . לרשימה הדינמית בטופס ביומן
def get_all_exercise_names():
 conn = get_connection()
 cursor = conn.cursor()
 cursor.execute("SELECT DISTINCT name FROM exercises ORDER BY name")
 rows = cursor.fetchall()
 cursor.close()
 release(conn)
 return [row['name'] for row in rows]


#שמירת פרופיל המשתמש . פעם ראשונה = הכנסה חדשה , בפעם הבאה = עדכון אותה שורה (upsert)
def save_profile(sex, age, bodyweight):
 conn = get_connection()
 cursor = conn.cursor()
 cursor.execute("""
     INSERT INTO profile (id, sex, age, bodyweight) VALUES (1, %s, %s, %s)
     ON CONFLICT (id) DO UPDATE SET sex=excluded.sex, age=excluded.age, bodyweight=excluded.bodyweight
 """, (sex, age, bodyweight))
 conn.commit()
 cursor.close()
 release(conn)


#שליפת פרופיל המשתמש . מחזיר מילון עם המידע , או None אם עדיין לא נשמר פרופיל בכלל
def get_profile():
 conn = get_connection()
 cursor = conn.cursor()
 cursor.execute("SELECT sex, age, bodyweight FROM profile WHERE id = 1")
 row = cursor.fetchone()
 cursor.close()
 release(conn)
 if row is None:
     return None
 return dict(row)

#שליפת כל האימונים עם התרגילים והסטים . שלוש שאילתות בלבד במקום שאילתה לכל אימון
def get_all_workouts_full():
 conn = get_connection()
 cursor = conn.cursor()

 cursor.execute("SELECT id, date, workout_type FROM workouts ORDER BY date DESC, id DESC")
 workouts = [dict(r) for r in cursor.fetchall()]

 cursor.execute("SELECT id, workout_id, name FROM exercises ORDER BY id")
 exercises = [dict(r) for r in cursor.fetchall()]

 cursor.execute("SELECT exercise_id, reps, weight FROM sets ORDER BY exercise_id, set_number")
 sets = [dict(r) for r in cursor.fetchall()]

 cursor.close()
 release(conn)

 #קיבוץ הסטים לפי תרגיל
 sets_by_exercise = {}
 for s in sets:
     sets_by_exercise.setdefault(s['exercise_id'], []).append(
         {'reps': s['reps'], 'weight': s['weight']}
     )

 #קיבוץ התרגילים לפי אימון
 exercises_by_workout = {}
 for e in exercises:
     exercises_by_workout.setdefault(e['workout_id'], []).append({
         'name': e['name'],
         'sets': sets_by_exercise.get(e['id'], [])
     })

 #חיבור הכל
 for w in workouts:
     w['exercises'] = exercises_by_workout.get(w['id'], [])

 return workouts

#בדיקה עצמית . רץ רק כשמריצים את הקובץ ישירות ולא באימפורט
if __name__ == '__main__':
    print("מתחבר ל-Postgres...")
    print("יוצר טבלאות...")
    init_db()

    print("שומר אימון לדוגמה...")
    test_workout = [
        {'name': 'סקוואט', 'sets': [{'reps': 5, 'weight': 100}, {'reps': 5, 'weight': 110}]},
        {'name': 'לחיצת רגליים', 'sets': [{'reps': 10, 'weight': 180}]},
    ]
    workout_id = save_workout('2026-07-14', 'רגליים', test_workout)
    print(f"נשמר אימון עם id={workout_id}")

    print("\nכל האימונים:")
    for w in get_all_workouts():
        print(f"  {w['id']} | {w['date']} | {w['workout_type']}")

    print("\nפרטי האימון שנשמר:")
    details = get_workout_details(workout_id)
    for ex in details['exercises']:
        print(f"  {ex['name']}: {ex['sets']}")

    print("\nהיסטוריית סקוואט:")
    for row in get_exercise_history('סקוואט'):
        print(f"  {row['date']} | {row['reps']} חזרות | {row['weight']} קג")

    print("\nמוחק את אימון הבדיקה...")
    delete_workout(workout_id)
    print(f"נשארו {len(get_all_workouts())} אימונים")

    print("\nבודק פרופיל...")
    print(f"פרופיל לפני שמירה: {get_profile()}")
    save_profile('זכר', 25, 80.0)
    print(f"פרופיל אחרי שמירה: {get_profile()}")
    save_profile('זכר', 26, 82.0)
    print(f"פרופיל אחרי עדכון: {get_profile()}")

    print("\nהכל עובד! מחובר בהצלחה לPostgres בענן")