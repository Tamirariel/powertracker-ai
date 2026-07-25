from fastapi import FastAPI
from pydantic import BaseModel
from agent import ask_full_agent

app = FastAPI()

class ChatRequest(BaseModel):
    question: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    answer = ask_full_agent(req.question)
    return {"answer": answer}