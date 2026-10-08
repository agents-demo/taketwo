# Contributing to TakeTwo

Turn a screen recording of a bug into a reproduction, a fix, and a before/after proof video.

## Setup

Use the repo venv (on this machine `python`/`pip` are not on PATH):

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
& $PY -m pip install -r requirements.txt
& $PY -m playwright install chromium     # for the live browser path
```

`.env` holds the model endpoint; copy `.env.example` if you need a fresh one.

## Run

```powershell
& $PY -m streamlit run taketwo/interfaces/web/ui.py     # web console
& $PY -m taketwo.interfaces.cli record                  # CLI
```

## Checks

```powershell
& $PY -m ruff check .
& $PY -m pytest -q
& $PY scripts\evaluate_repros.py         # offline quality gate
& $PY scripts\dogfood.py                 # live: reproduce a real browser bug (needs Playwright)
& $PY scripts\benchmark.py               # live: reproduce rate over seeded apps
```

## Architecture (the one rule that matters)

Layers point **inward** only; `tests/unit/test_architecture.py` enforces it:

```
interfaces  ->  pipeline  ->  backend  ->  domain
                     |
                     +->  storage / reporting / config   (neutral leaves)
```

- **Keep openjiuwen inside `backend/`.** Nothing outside imports it. Reach models/agents only
  through the façade (`build`, `TextParams`/`VisionParams`, `run_agent`, `run_text`).
- **`domain/` stays pure** — stdlib only, no I/O.
- **Stages** live in `pipeline/stages/<name>/` and must not import `pipeline`.
- **Shared within the pipeline** → `pipeline/<x>` (e.g. `forge/`). **Cross-layer** → a neutral
  leaf (`storage`, `config`, `reporting`). A helper used by one stage stays in that stage.
- **`browser/` is confined to the reproduce stage** (the only place Playwright is imported).
- `__init__.py` is imports/docstring only — no side effects. Wiring happens in `bootstrap.setup()`.

## Where to add things

- New **stage**: `pipeline/stages/<name>/` + register in `pipeline/stages/__init__.py` (`STAGES`)
  and call it from `pipeline/strategies/base.py`.
- New **capability** (external system): a module under `pipeline/` (or a stage if single-consumer).
- New **interface**: a module under `interfaces/`; reuse `interfaces/service.py`.
- New **config knob**: application behaviour in `config.py`; endpoint/credentials in
  `backend/settings.py`.

## Front-ends (both under `interfaces/`)

- **`interfaces/reels/`** — the consumer proof feed (vanilla HTML/CSS/JS, no build). Served by the API
  at `/app/`; reads `/scoreboard`, `/runs`, `/jobs`, `/media`. Edit `index.html` / `styles.css` / `app.js`.
- **`interfaces/web/`** — the Streamlit console: `ui.py` (entry) → `app_pages/pages.py` (registry) →
  `app_pages/{runs,detail,scoreboard}.py`, shared helpers in `common.py`, components in `compare.py`.
  Theme lives in `.streamlit/config.toml`.

## Commits & PRs

Concise conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`). Describe the change, list the
checks you ran, and include a screenshot/recording for UI changes.
