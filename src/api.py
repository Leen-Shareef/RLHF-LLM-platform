# src/api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
from dotenv import load_dotenv
from .two_model_llm import Conversation

load_dotenv()
app = FastAPI(title="Two-Model Live API")

# Allow the Vite dev server (localhost:5173) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sessions: Dict[str, Conversation] = {}

class StartReq(BaseModel):
    system_prompt: str | None = None

class StartResp(BaseModel):
    session_id: str
    degrade_turn: int

class TurnReq(BaseModel):
    session_id: str
    user: str

@app.post("/start", response_model=StartResp)
def start(req: StartReq):
    c = Conversation(system_prompt=req.system_prompt or None)
    sessions[c.id] = c
    return StartResp(session_id=c.id, degrade_turn=c.degrade_turn)

@app.post("/turn")
def turn(req: TurnReq):
    c = sessions.get(req.session_id)
    if not c:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    rec = c.step(req.user)
    return rec

@app.get("/state/{session_id}")
def state(session_id: str):
    c = sessions.get(session_id)
    if not c:
        raise HTTPException(status_code=404, detail="Unknown session_id")
    return {
        "session_id": c.id,
        "turn": c.turn,
        "memory": c.memory.snapshot(),
        "history": c.history,
        "records": c.records,
    }

@app.post("/reset/{session_id}")
def reset(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
    return {"ok": True}
