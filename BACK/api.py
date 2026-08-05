from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import ask_full_agent, langfuse, get_env
import database
import powerlifting

API_KEY = get_env("API_KEY")

app = FastAPI()

#כל בקשה חייבת לשאת את המפתח . הפרונט מוסיף אותו בשרת , הדפדפן לא רואה אותו
@app.middleware("http")
async def require_api_key(request: Request, call_next):
    open_paths = ("/health", "/docs", "/openapi.json")
    if request.url.path in open_paths:
        return await call_next(request)

    if not API_KEY:
        return JSONResponse({"detail": "API_KEY לא הוגדר בשרת"}, status_code=500)

    if request.headers.get("X-API-Key") != API_KEY:
        return JSONResponse({"detail": "לא מורשה"}, status_code=401)

    return await call_next(request)

database.init_db()


class ChatRequest(BaseModel):
    question: str


class Profile(BaseModel):
    sex: str | None = None
    age: int | None = None
    bodyweight: float | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/profile")
def read_profile():
    p = database.get_profile()
    if p is None:
        return {"sex": None, "age": None, "bodyweight": None}
    return p


@app.post("/profile")
def write_profile(p: Profile):
    database.save_profile(p.sex, p.age, p.bodyweight)
    return {"status": "saved"}


# תמצית שלושת האימונים האחרונים - עבר לכאן מ-2_chat.py
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


# שיאי הפאוורליפטינג - מחושבים מכל ההיסטוריה, לא רק מהאימונים האחרונים
def build_lifts_summary():
    try:
        progress = powerlifting.all_progress()
    except Exception:
        return None

    parts = [
        f"{lift['name']} {lift['best_1rm']} קג"
        for lift in progress.get("lifts", [])
        if lift.get("best_1rm") is not None
    ]
    if not parts:
        return None

    text = " , ".join(parts)
    if progress.get("total") is not None:
        text += f" , טוטאל {progress['total']} קג"
    return text


# בניית ההקשר לסוכן - הפרונט לא צריך לדעת על פורמט הפרומפט
def build_context(question):
    p = database.get_profile() or {}
    parts = []

    if p.get("sex"):
        parts.append(f"מגדר: {'גבר' if p['sex'] == 'זכר' else 'אישה'}")
    if p.get("age"):
        parts.append(f"גיל: {p['age']}")
    if p.get("bodyweight"):
        parts.append(f"משקל גוף: {p['bodyweight']} קג")
    lifts = build_lifts_summary()
    if lifts:
        parts.append(f"שיאים משוערים (1RM) מכל ההיסטוריה: {lifts}")
    summary = build_journal_summary()
    if summary:
        parts.append(f"אימונים אחרונים מהיומן: {summary}")

    if parts:
        return f"[נתוני המשתמש: {' | '.join(parts)}] {question}"
    return question


@app.post("/chat")
def chat(req: ChatRequest):
    answer = ask_full_agent(build_context(req.question))
    langfuse.flush()
    return {"answer": answer}



class SetIn(BaseModel):
    reps: int
    weight: float


class ExerciseIn(BaseModel):
    name: str
    sets: list[SetIn]


class WorkoutIn(BaseModel):
    date: str
    workout_type: str
    exercises: list[ExerciseIn]

@app.get("/workouts")
def list_workouts():
    return database.get_all_workouts()


# החודש כולו בבקשה אחת - במקום לולאה של בקשות מלוח השנה
@app.get("/workouts/full")
def list_workouts_full():
    return database.get_all_workouts_full()


@app.get("/workouts/{workout_id}")
def read_workout(workout_id: int):
    w = database.get_workout_details(workout_id)
    if w is None:
        raise HTTPException(status_code=404, detail="אימון לא נמצא")
    return w


@app.post("/workouts")
def create_workout(w: WorkoutIn):
    exercises = [
        {"name": ex.name, "sets": [{"reps": s.reps, "weight": s.weight} for s in ex.sets]}
        for ex in w.exercises
    ]
    workout_id = database.save_workout(w.date, w.workout_type, exercises)
    return {"id": workout_id}


@app.delete("/workouts/{workout_id}")
def remove_workout(workout_id: int):
    database.delete_workout(workout_id)
    return {"status": "deleted"}


@app.get("/workouts/last/{workout_type}")
def last_by_type(workout_type: str):
    w = database.get_last_workout_by_type(workout_type)
    if w is None:
        raise HTTPException(status_code=404, detail="אין אימון קודם מסוג זה")
    return w


@app.get("/exercises/names")
def exercise_names():
    return database.get_all_exercise_names()

@app.get("/powerlifting/progress")
def powerlifting_progress():
    return powerlifting.all_progress()