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
& $PY -m streamlit run taketwo/surfaces/gui1/ui.py     # gui1
& $PY -m taketwo.surfaces.cli record                  # CLI
```

## Checks

```powershell
& $PY -m ruff check .
& $PY -m pytest -q
& $PY tests\integration\evaluate_repros.py         # offline quality gate
& $PY tests\integration\check_reproduce.py                 # live: reproduce a real browser bug (needs Playwright)
& $PY tests\integration\benchmark_reproduce.py               # live: reproduce rate over seeded apps
```

## Architecture (the one rule that matters)

Layers point **inward** only; `tests/unit/test_architecture.py` enforces it:

```
surfaces  ->  core  ->  integrations  ->  domain
```

- **Keep openjiuwen inside `integrations/agents/`.** Nothing outside imports it. Reach models/agents
  only through the façade (`build`, `TextParams`/`VisionParams`, `run_agent`, `run_text`).
- **`domain/` stays pure** — stdlib only, no I/O.
- **`integrations/`** are the outbound adapters: agents, browser (Playwright), forge (GitHub),
  appserver, storage, reporting.
- **Stages** live in `core/stages/<name>/`; the workflow + strategies live in `core/`.
- **`browser.py` is confined to `integrations/`** (the only place Playwright is imported).
- `__init__.py` is imports/docstring only — no side effects. Wiring happens in `core/bootstrap.setup()`.

## Where to add things

- New **stage**: `core/stages/<name>/` + register in `core/stages/__init__.py` (`STAGES`)
  and call it from `core/strategies/base.py`.
- New **capability** (external system): a module under `integrations/`.
- New **surface**: a package under `surfaces/`; reuse the shared façade `core/service.py`.
- New **config knob**: application behaviour in `core/config.py`; endpoint/credentials in
  `integrations/agents/settings.py`.

## The two GUIs (both under `surfaces/`)

- **`surfaces/gui1/`** — the Streamlit GUI: `ui.py` (entry) → `app_pages/pages.py` (registry) →
  `app_pages/{runs,detail,scoreboard}.py`, shared helpers in `common.py`, components in `compare.py`.
  Theme lives in `.streamlit/config.toml`.
- **`surfaces/gui2/`** — the web app: `server/` (FastAPI `app.py` + read model `runs.py`) serving
  `client/` (the SvelteKit SPA, built into `client/build/`) at `/gui2/`. Edit `client/src/` and rebuild
  with `npm run build` inside `client/`.

## Commits & PRs

Concise conventional commits (`feat:`, `fix:`, `refactor:`, `docs:`). Describe the change, list the
checks you ran, and include a screenshot/recording for UI changes.
