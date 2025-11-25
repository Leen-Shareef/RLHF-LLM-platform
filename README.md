# Live Two-Model Runner (Python)

Runs a 5-turn conversation with two models each turn:
- Weak (free): `mistralai/mistral-7b-instruct:free`
- Strong (free): `meta-llama/llama-3.3-70b-instruct:free`

Features:
- One system prompt for the whole conversation (asked at startup)
- Memory (simple name + preferences) carried across turns
- Force one wrong weak answer on turn 3 (configurable)
- Logs to `data/conversation_log.jsonl` and `data/conversation_log.csv`
- Optional FastAPI server for the frontend: `/start`, `/turn`, `/state/{id}`, `/reset/{id}`

## Setup
```bash
pip install -r requirements.txt
echo "OPENROUTER_API_KEY=sk-or-..." > .env
