# Quick start

Turn a screen recording of a bug into a reproduction, a fix, and a before/after proof video.

Run every command **from the `taketwo` folder**. On this machine `pip`/`python` are not on PATH, so
use the repo venv's python (or just `.\run.ps1`):

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
```

## 1. Install (once)

```powershell
& $PY -m pip install -r requirements.txt
& $PY -m playwright install chromium      # for real browser reproduction
```

`.env` is filled in with the model endpoint. If you reuse this elsewhere, copy `.env.example`.

## 2. Run

**Web UI (recommended)** — opens http://localhost:8501:

```powershell
& $PY -m streamlit run taketwo/interfaces/web/ui.py
```

**CLI** — record a bug, then reproduce + fix it:

```powershell
# record a bug from a video against a repo/app
& $PY -m taketwo.interfaces.cli record runtime/data/sample_bug.mov --repo owner/name --app http://localhost:3000

# past runs
& $PY -m taketwo.interfaces.cli history
```

No recording handy? Make a synthetic clip and serve the sample buggy app to reproduce against:

```powershell
& $PY scripts\make_sample_bug.py       # writes runtime/data/sample_bug.mov + fixtures
& $PY scripts\serve_sample_app.py      # serves examples/sample_app at http://localhost:3000

# in another terminal:
& $PY -m taketwo.interfaces.cli record runtime/data/sample_bug.mov --app http://localhost:3000
```

## 3. Offline checks (no model calls)

```powershell
& $PY -m pytest -q                 # architecture + pipeline tests
& $PY -m ruff check .
& $PY scripts\evaluate_repros.py   # quality gate against tests/eval/expected.json
```

## 4. App (SvelteKit web UI)

Built assets are committed, so the API serves it directly:

```powershell
& $PY -m uvicorn taketwo.interfaces.api:app --port 8000
# open http://localhost:8000/app/   (Runs · Review · Scoreboard)
```

To develop it (hot reload on http://localhost:5173, calling the API on 8000):

```powershell
cd taketwo\interfaces\app
npm install
npm run dev        # or: npm run build  (writes build/, served at /app/)
```

## 5. Live checks (need Playwright: `python -m playwright install chromium`)

```powershell
& $PY scripts\dogfood.py            # reproduce a real browser bug + before/after proof video
& $PY scripts\benchmark.py          # reproduce-rate over seeded bugs
& $PY scripts\make_sample_video.py  # rebuild the sample's proof from real browser frames
& $PY scripts\seed_reproduced.py    # seed two reproduced scenarios (with proof)
```

See the full [usage guide](docs/USAGE.md), [README.md](README.md), and [docs/architecture.md](docs/architecture.md).
