from fastapi import FastAPI
from pydantic import BaseModel
from agent import ask_full_agent, langfuse
import database
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from fastapi import FastAPI, HTTPException
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    sets: List[SetIn]


class WorkoutIn(BaseModel):
    date: str
    workout_type: str
    exercises: List[ExerciseIn]


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