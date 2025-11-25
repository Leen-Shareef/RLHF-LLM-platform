#!/usr/bin/env python3
"""
Two-Model Live Runner (CLI)
- 5 user turns
- memory persists across turns
- weak + strong replies each turn
- soft variability on weak model (higher temperature on one turn)
- save JSONL + CSV logs to ./data

Defaults use OpenRouter free models:
  WEAK_MODEL   = "mistralai/mistral-7b-instruct:free"
  STRONG_MODEL = "meta-llama/llama-3.3-70b-instruct:free"
"""

import os, sys, json, time, uuid, pathlib, random
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv
import pandas as pd

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# ====== Config ======
WEAK_MODEL   = "mistralai/mistral-7b-instruct:free"
STRONG_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

# If set (1..5), degrade weak model on that turn; if 0/unset => random
DEGRADE_TURN = int(os.getenv("WEAK_DEGRADE_TURN", "0"))

TURNS = 5

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
JSONL_LOG = str(DATA_DIR / "conversation_log.jsonl")
CSV_LOG   = str(DATA_DIR / "conversation_log.csv")

BASE_SYSTEM_PROMPT = (
    "You are a helpful assistant. Always answer concisely and correctly. "
    "Remember the user's stated preferences across turns."
)
ENV_SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT")

WEAK_TONE = "Be brief. Avoid long explanations."
STRONG_TONE = "Be precise, verify facts, and ensure correctness."

# ====== Memory ======
class Memory:
    def __init__(self):
        self.user_name: Optional[str] = None
        self.preferences: set[str] = set()

    def update_from_user(self, text: str):
        low = text.lower()
        for key in ("i'm ", "i am "):
            if key in low:
                seg = low.split(key, 1)[1]
                candidate = seg.split()[0].strip(".,!?;")
                if candidate.isalpha() and 1 <= len(candidate) <= 40:
                    self.user_name = candidate.capitalize()
        if "i like" in low:
            prefs = low.split("i like", 1)[1][:80].strip(" .!?:;")
            if prefs:
                self.preferences.add(prefs)

    def system_suffix(self):
        name = self.user_name or "(unknown)"
        prefs = ", ".join(sorted(self.preferences)) if self.preferences else "(none)"
        return f"\n\n[Memory] User name: {name}. Preferences: {prefs}."

    def snapshot(self):
        return {"user_name": self.user_name, "preferences": sorted(self.preferences)}

# ====== API ======
def call_openrouter(model, messages, temperature=0.7, top_p=0.9):
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Missing OPENROUTER_API_KEY. Add it to .env")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://example.com",
        "X-Title": "Live Two-Model Runner"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
    }
    r = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

# ====== Conversation ======
class Conversation:
    def __init__(self, system_prompt=None):
        self.id = str(uuid.uuid4())
        self.memory = Memory()
        self.base_system_prompt = system_prompt or ENV_SYSTEM_PROMPT or BASE_SYSTEM_PROMPT
        self.history = [{"role": "system", "content": self.base_system_prompt}]
        self.turn = 0
        self.records = []
        self.degrade_turn = DEGRADE_TURN if DEGRADE_TURN in range(1, 6) else random.randint(1, 5)
        if os.path.exists(JSONL_LOG):
            os.remove(JSONL_LOG)

    def step(self, user_text):
        self.turn += 1
        self.memory.update_from_user(user_text)

        sys_with_mem = self.base_system_prompt + self.memory.system_suffix()
        degrade_now = (self.turn == self.degrade_turn)

        weak_temp = 1.2 if degrade_now else 0.9
        weak_top_p = 0.95 if degrade_now else 0.9

        weak_ctx = [
            {"role": "system", "content": sys_with_mem + "\n\n[Behavior] " + WEAK_TONE},
            {"role": "user", "content": user_text}
        ]

        strong_ctx = [
            {"role": "system", "content": sys_with_mem + "\n\n[Behavior] " + STRONG_TONE},
            {"role": "user", "content": user_text}
        ]

        t0 = time.time()
        weak = call_openrouter(WEAK_MODEL, weak_ctx, temperature=weak_temp, top_p=weak_top_p)
        weak_lat = time.time() - t0

        t0 = time.time()
        strong = call_openrouter(STRONG_MODEL, strong_ctx, temperature=0.2, top_p=0.9)
        strong_lat = time.time() - t0

        self.history.append({"role": "user", "content": user_text})
        self.history.append({"role": "assistant", "content": strong})

        record = {
            "ts": datetime.utcnow().isoformat()+"Z",
            "session_id": self.id,
            "turn": self.turn,
            "user": user_text,
            "weak_model": WEAK_MODEL,
            "strong_model": STRONG_MODEL,
            "weak_answer": weak,
            "strong_answer": strong,
            "weak_latency_sec": round(weak_lat, 3),
            "strong_latency_sec": round(strong_lat, 3),
            "memory": self.memory.snapshot(),
            "weak_degraded": degrade_now,
            "degrade_turn": self.degrade_turn
        }
        with open(JSONL_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(record)+"\n")
        self.records.append(record)
        return record

    def export_csv(self):
        pd.DataFrame(self.records).to_csv(CSV_LOG, index=False)

def run_cli():
    load_dotenv()
    print("Live Two-Model Runner (5 turns). Press Ctrl+C to exit.\n")
    sp = input("Enter a SYSTEM PROMPT (or press Enter for default): ").strip()
    conv = Conversation(system_prompt=sp or None)
    for i in range(1, TURNS+1):
        user = input(f"Turn {i} - You: ").strip()
        rec = conv.step(user)
        print(f"\nWeak: {rec['weak_answer']}\n")
        print(f"Strong: {rec['strong_answer']}\n")
    conv.export_csv()
    print(f"\nSaved logs:\n- {JSONL_LOG}\n- {CSV_LOG}\n")

if __name__ == "__main__":
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\nBye!")
