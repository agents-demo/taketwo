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

**gui1 (Streamlit, recommended)** — opens http://localhost:8501:

```powershell
& $PY -m streamlit run taketwo/surfaces/gui1/ui.py
```

**CLI** — record a bug, then reproduce + fix it:

```powershell
# record a bug from a video against a repo/app
& $PY -m taketwo.surfaces.cli record runtime/data/sample_bug.mov --repo owner/name --app http://localhost:3000

# past runs
& $PY -m taketwo.surfaces.cli history
```

No recording handy? Make a synthetic clip and serve the sample buggy app to reproduce against:

```powershell
& $PY scripts\make_sample_bug.py       # writes runtime/data/sample_bug.mov + fixtures
& $PY demo\serve_scenario.py      # serves demo/scenarios/booking/app at http://localhost:3000

# in another terminal:
& $PY -m taketwo.surfaces.cli record runtime/data/sample_bug.mov --app http://localhost:3000
```

## 3. Offline checks (no model calls)

```powershell
& $PY -m pytest -q                 # architecture + pipeline tests
& $PY -m ruff check .
& $PY scripts\evaluate_repros.py   # quality gate against tests/eval/expected.json
```

## 4. gui2 (web app: FastAPI server + SvelteKit SPA)

Built assets are committed, so the server serves the UI directly:

```powershell
& $PY -m uvicorn taketwo.surfaces.gui2:app --port 8000
# open http://localhost:8000/gui2/   (Runs · Review · Scoreboard)
```

To develop the SPA (hot reload on http://localhost:5173, calling the server on 8000):

```powershell
cd taketwo\surfaces\gui2\client
npm install
npm run dev        # or: npm run build  (writes client/build/, served at /gui2/)
```

## 5. Live checks (need Playwright: `python -m playwright install chromium`)

```powershell
& $PY demo\maintenance\check_reproduce.py            # reproduce a real browser bug + before/after proof video
& $PY scripts\benchmark.py          # reproduce-rate over seeded bugs
```

See the full [usage guide](docs/USAGE.md), [README.md](README.md), and [docs/architecture.md](docs/architecture.md).
