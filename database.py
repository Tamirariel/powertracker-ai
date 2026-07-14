#קובץ הדטא של הפרויקט . שומר אימונים , בניית האימונים הבאים 

import sqlite3
import os

#התיקייה שבה הסקריפט הזה יושב (myapp)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'powertracker.db')


#פתיחת חיבור למסד הנתונים . כל פונקציה פותחת וסוגרת חיבור משלה
def get_connection():
 conn = sqlite3.connect(DB_PATH)
 #מאפשר גישה לעמודות לפי שם ולא רק לפי מיקום
 conn.row_factory = sqlite3.Row
 #אכיפת מפתחות זרים . בsqlite זה כבוי כברירת מחדל
 conn.execute("PRAGMA foreign_keys = ON")
 return conn


#יצירת כל הטבלאות אם הן לא קיימות . רץ בכל עליית אפליקציה
def init_db():
 conn = get_connection()

 conn.execute("""
 CREATE TABLE IF NOT EXISTS workouts (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     date TEXT NOT NULL,
     workout_type TEXT NOT NULL
 )
 """)

 conn.execute("""
 CREATE TABLE IF NOT EXISTS exercises (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     workout_id INTEGER NOT NULL,
     name TEXT NOT NULL,
     FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE
 )
 """)

 conn.execute("""
 CREATE TABLE IF NOT EXISTS sets (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     exercise_id INTEGER NOT NULL,
     set_number INTEGER NOT NULL,
     reps INTEGER NOT NULL,
     weight REAL NOT NULL,
     FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
 )
 """)

 #טבלת הפרופיל . בכוונה יש בה תמיד רק שורה אחת (id=1) כי יש רק פרופיל אחד - אני
 #ה-CHECK מונע הכנסת שורה עם id אחר בטעות
 conn.execute("""
 CREATE TABLE IF NOT EXISTS profile (
     id INTEGER PRIMARY KEY CHECK (id = 1),
     sex TEXT,
     age INTEGER,
     bodyweight REAL
 )
 """)

 conn.commit()
 conn.close()


#שמירת אימון שלם . מקבל תאריך , סוג , ורשימת תרגילים במבנה מקונן :
def save_workout(date, workout_type, exercises_data):
 conn = get_connection()
 cursor = conn.cursor()

 #שמירת האימון וקבלת הid שלו
 cursor.execute(
     "INSERT INTO workouts (date, workout_type) VALUES (?, ?)",
     (date, workout_type)
 )
 workout_id = cursor.lastrowid

 #שמירת כל תרגיל והסטים שלו
 for exercise in exercises_data:
     cursor.execute(
         "INSERT INTO exercises (workout_id, name) VALUES (?, ?)",
         (workout_id, exercise['name'])
     )
     exercise_id = cursor.lastrowid

     for i, s in enumerate(exercise['sets'], start=1):
         cursor.execute(
             "INSERT INTO sets (exercise_id, set_number, reps, weight) VALUES (?, ?, ?, ?)",
             (exercise_id, i, s['reps'], s['weight'])
         )

 conn.commit()
 conn.close()
 return workout_id


#שליפת רשימת כל האימונים . מהחדש לישן
def get_all_workouts():
 conn = get_connection()
 rows = conn.execute(
     "SELECT id, date, workout_type FROM workouts ORDER BY date DESC, id DESC"
 ).fetchall()
 conn.close()
 return [dict(row) for row in rows]


#שליפת אימון שלם לפי id . מחזיר את אותו מבנה מקונן כמו בשמירה
def get_workout_details(workout_id):
 conn = get_connection()

 workout = conn.execute(
     "SELECT id, date, workout_type FROM workouts WHERE id = ?",
     (workout_id,)
 ).fetchone()

 if workout is None:
     conn.close()
     return None

 result = dict(workout)
 result['exercises'] = []

 exercises = conn.execute(
     "SELECT id, name FROM exercises WHERE workout_id = ? ORDER BY id",
     (workout_id,)
 ).fetchall()

 for exercise in exercises:
     sets = conn.execute(
         "SELECT set_number, reps, weight FROM sets WHERE exercise_id = ? ORDER BY set_number",
         (exercise['id'],)
     ).fetchall()

     result['exercises'].append({
         'name': exercise['name'],
         'sets': [{'reps': s['reps'], 'weight': s['weight']} for s in sets]
     })

 conn.close()
 return result


#שליפת האימון האחרון מסוג מסוים . בשביל פיצר השכפול
def get_last_workout_by_type(workout_type):
 conn = get_connection()
 row = conn.execute(
     "SELECT id FROM workouts WHERE workout_type = ? ORDER BY date DESC, id DESC LIMIT 1",
     (workout_type,)
 ).fetchone()
 conn.close()

 if row is None:
     return None
 return get_workout_details(row['id'])


#שליפת כל הסטים של תרגיל מסוים לאורך זמן . בשביל דף הפאוורליפטינג
#מחזיר שורות של : תאריך , חזרות , משקל
def get_exercise_history(exercise_name):
 conn = get_connection()
 rows = conn.execute("""
     SELECT w.date, s.reps, s.weight
     FROM sets s
     JOIN exercises e ON s.exercise_id = e.id
     JOIN workouts w ON e.workout_id = w.id
     WHERE e.name = ?
     ORDER BY w.date
 """, (exercise_name,)).fetchall()
 conn.close()
 return [dict(row) for row in rows]


#מחיקת אימון שלם . הCASCADE מוחק אוטומטית גם את התרגילים והסטים שלו
def delete_workout(workout_id):
 conn = get_connection()
 conn.execute("DELETE FROM workouts WHERE id = ?", (workout_id,))
 conn.commit()
 conn.close()


#שליפת כל שמות התרגילים שהוזנו אי פעם . לרשימה הדינמית בטופס ביומן
def get_all_exercise_names():
 conn = get_connection()
 rows = conn.execute("SELECT DISTINCT name FROM exercises ORDER BY name").fetchall()
 conn.close()
 return [row['name'] for row in rows]


#שמירת פרופיל המשתמש . פעם ראשונה = הכנסה חדשה , בפעם הבאה = עדכון אותה שורה
#זה נקרא upsert - INSERT שהופך ל-UPDATE אם השורה כבר קיימת (בזכות ON CONFLICT)
def save_profile(sex, age, bodyweight):
 conn = get_connection()
 conn.execute("""
     INSERT INTO profile (id, sex, age, bodyweight) VALUES (1, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET sex=excluded.sex, age=excluded.age, bodyweight=excluded.bodyweight
 """, (sex, age, bodyweight))
 conn.commit()
 conn.close()


#שליפת פרופיל המשתמש . מחזיר מילון עם המידע , או None אם עדיין לא נשמר פרופיל בכלל
def get_profile():
 conn = get_connection()
 row = conn.execute("SELECT sex, age, bodyweight FROM profile WHERE id = 1").fetchone()
 conn.close()
 if row is None:
     return None
 return dict(row)


#בדיקה עצמית . רץ רק כשמריצים את הקובץ ישירות ולא באימפורט
if __name__ == '__main__':
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

    print("\nהכל עובד!")

