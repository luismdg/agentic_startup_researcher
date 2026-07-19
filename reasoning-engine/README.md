# reasoning-engine

3-axis scoring (Founder / Market / Idea-vs-Market, never averaged), memo generation, and
per-claim Trust Scoring for VC Brain. Consumes sourcing records from `src/` (or the live
`frontend_vcBrain` UI) and produces scored, evidence-grounded investment memos.

## Setup

```powershell
cd reasoning-engine
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Then open `.env` and fill in `OPENAI_API_KEY=` with a real key.

## Run

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8001
```

- Dashboard UI: `http://127.0.0.1:8001`
- JSON API (what `frontend_vcBrain` talks to): `http://127.0.0.1:8001/api/startups`

Port 8000 may be taken by something else on your machine — use 8001 or any other free port.

## Testing without spending API credit

Set `LLM_PROVIDER=fake` in `.env` (or `$env:LLM_PROVIDER = "fake"` before running). Every
call returns canned, schema-valid `[FAKE]`-labeled data at $0 — use this to check that
wiring/UI changes work before switching back to `openai` for real output.

## Mac/Linux

Same steps, just `source .venv/bin/activate` instead of `.venv\Scripts\python.exe`, and
`cp .env.example .env` instead of `copy`.
