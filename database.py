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


#יצירת שלוש הטבלאות אם הן לא קיימות . רץ בכל עליית אפליקציה
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

 conn.commit()
 conn.close()


#שמירת אימון שלם . מקבל תאריך , סוג , ורשימת תרגילים במבנה מקונן :
#exercises_data = [ {'name': 'סקוואט', 'sets': [ {'reps': 5, 'weight': 120}, ... ]}, ... ]
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


#שליפת כל שמות התרגילים שהוזנו אי פעם . לרשימה הדינמית בטופס
def get_all_exercise_names():
 conn = get_connection()
 rows = conn.execute("SELECT DISTINCT name FROM exercises ORDER BY name").fetchall()
 conn.close()
 return [row['name'] for row in rows]