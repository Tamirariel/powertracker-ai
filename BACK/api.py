from fastapi import FastAPI
from pydantic import BaseModel
from agent import ask_full_agent, langfuse
import database
from fastapi.middleware.cors import CORSMiddleware
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