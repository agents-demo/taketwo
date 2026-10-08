# Using TakeTwo

Turn a bug report that is just a **shaky screen recording** and the words *"it's broken"* into a
reproduction, a fix, and a **before/after proof video**. A human maintainer approves the merge.

This guide covers everything a user needs: setup, the interfaces, the workflow, the demo scripts, the
settings, and troubleshooting.

---

## 1. What it does

1. **Understand** — watches the clip, infers the steps taken and where it went wrong.
2. **Reproduce** — replays those steps in a real browser, captures the console/error, records the **before** clip.
3. **Repair** — localizes the cause in the repo and proposes a minimal fix + a regression test.
4. **Prove** — re-runs the same scenario on the patched build, and stitches a **before/after proof**.
5. **Deliver** — opens an issue (steps + evidence) and a **draft** PR. Never auto-merges.

**Vocabulary**
- **Run (job)** — one submission (a clip + optionally a repo/app). Identified by a short id.
- **Reproduction** — the replayed steps, the failure evidence, and the verdict (`reproduced` / `not_reproduced` / `unclear`).
- **Fix** — the proposed diff + regression test.
- **Proof** — the before/after image and video.
- **Review** — a human decision (`approved` / `changes_requested`), with an audit trail.

---

## 2. Setup

On this machine `python`/`pip` are **not on PATH** — use the repo venv. From the `taketwo` folder:

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"

& $PY -m pip install -r requirements.txt
& $PY -m playwright install chromium      # needed for real browser reproduction
```

`.env` holds the model endpoint. If you need a fresh one: copy `.env.example` to `.env` and fill it in.
The required keys are `API_KEY`, `API_BASE`, and `MODEL_NAME` (the vision model defaults to
`deepseek-v4-flash-vision-exp`).

Everything degrades gracefully: with no model configured and no browser, the pipeline still runs on
its deterministic path (fixtures) so you can explore the UI.

---

## 3. The two interfaces (same engine)

### 3a. App — the modern web UI (recommended)

A SvelteKit single-page app served by the API.

```powershell
& $PY -m uvicorn taketwo.interfaces.api:app --port 8000
# open http://localhost:8000/app/
```

Pages:
- **Runs** — submit a clip (or repo/app), see past runs as cards with a thumbnail; live job status.
- **Review** — the before/after **compare slider** (or proof video), the score/verdict/steps, the diff,
  **Approve / Request changes**, and an **Ask** box.
- **Scoreboard** — the reproduce rate, counts, and a per-repo leaderboard.

A **☀️/🌙 toggle** in the header switches light/dark (defaults to your OS).

> Developing the app with hot reload:
> ```powershell
> cd taketwo\interfaces\app
> npm install
> npm run dev      # http://localhost:5173  (CORS is enabled on the API)
> ```
> Built assets live in `taketwo/interfaces/app/build/` and are what the API serves at `/app/`.
> Rebuild after editing source with `npm run build`.

### 3b. Console — the Streamlit dashboard (dense / operators)

```powershell
& $PY -m streamlit run taketwo/interfaces/web/ui.py
# opens http://localhost:8501
```

Submit, watch a live multi-step job, review with tabs (Proof / Fix / Evidence / Review), chat about a
run, and see a scoreboard. Light/dark follows your OS.

---

## 4. End-to-end workflow

1. Open the **App** (or Console).
2. **Submit**: give a recording path (or upload), and optionally `owner/name` + the app URL.
   - If you have `APP_START_COMMAND` set, the pipeline can start the app under test itself.
3. Watch the **live run**: understand → reproduce → repair → prove → deliver.
4. Open the **Review**: scrub the before/after, read the diff, approve or send back.
5. **Approve & merge** — a draft PR/issue is opened for a real repo; the approve step is the human gate.

---

## 5. Command line

```powershell
& $PY -m taketwo.interfaces.cli record runtime/data/sample_bug.mov   # reproduce + fix a clip
& $PY -m taketwo.interfaces.cli history                              # recent runs
& $PY -m taketwo.interfaces.cli show sample_bug                      # a run's issue text
& $PY -m taketwo.interfaces.cli reset                                # clear saved runs
```

Run the analysis in its own process (used by the UI, useful in scripts):

```powershell
& $PY -m taketwo.interfaces.worker runtime/data/sample_bug.mov --progress progress.json --app http://localhost:8130
```

MCP (exposes `reproduce_bug_from_video` to MCP clients):

```powershell
& $PY -m taketwo.interfaces.mcp.server
```

---

## 6. HTTP API

Start with `uvicorn taketwo.interfaces.api:app`. Key routes:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | liveness |
| POST | `/replay` | run synchronously, return the outcome |
| POST | `/replay/async` | enqueue a job → `{job_id}` |
| GET | `/jobs/{id}` | job status + progress |
| GET | `/runs` | all runs (feed) |
| GET | `/runs/{job}` | one run |
| GET | `/runs/{job}/ask?q=…` | ask about a run |
| POST | `/runs/{job}/review/{decision}` | `approved` / `changes_requested` |
| GET | `/scoreboard` | reproduce rate + repos |
| GET | `/media/{job}/{name}` | proof artifacts (`proof.mp4`, `before.png`, `after.png`) |
| POST | `/webhook` | GitHub webhook (HMAC-verified) |
| — | `/app/` | the SvelteKit app |

---

## 7. Demo & dev scripts

```powershell
& $PY scripts\make_sample_bug.py        # synthetic fixtures (clip + sidecars) for the offline demo
& $PY scripts\make_sample_video.py      # rebuild the sample proof from REAL browser frames (needs Playwright)
& $PY scripts\serve_sample_app.py       # serve examples/sample_app at http://localhost:3000
& $PY scripts\seed_feed.py 5            # create several runs so the feed is swipeable
& $PY scripts\dogfood.py                # live end-to-end: reproduce a real bug → before/after proof
& $PY scripts\benchmark.py              # reproduce-rate over seeded apps (generalization)
& $PY scripts\evaluate_repros.py        # offline quality gate (tests/eval/expected.json)
```

Typical first run:

```powershell
& $PY scripts\make_sample_bug.py
& $PY -m taketwo.interfaces.cli record runtime/data/sample_bug.mov
& $PY -m uvicorn taketwo.interfaces.api:app --port 8000
# http://localhost:8000/app/
```

---

## 8. Settings (`.env`)

**Model endpoint** — `MODEL_PROVIDER`, `API_KEY`, `API_BASE`, `MODEL_NAME`, `VISION_MODEL_NAME`,
`LLM_TEMPERATURE`, `VISION_TEMPERATURE`, `LLM_TIMEOUT`, `LLM_RETRIES`, `LLM_SSL_VERIFY`.

**Behaviour** — `AGENTIC_MODE` (let the model drive), `VERIFY_FIX`, `RAILS` (token budget / memory),
`FRAME_FPS`, `MAX_FRAMES`, `CURSOR_MOTION_THRESHOLD`, `PROOF_WIDTH`.

**App under test** — `APP_START_COMMAND` (serve the app from a checkout), `APP_URL`, `PATCHED_APP_URL`,
`TEST_COMMAND` (run the repo's suite to verify the fix).

**Delivery** — `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`.

**Sandbox runner** — `SANDBOX_IMAGE` (Docker image; empty = run in-process), `SANDBOX_CPU`,
`SANDBOX_MEMORY`, `SANDBOX_PIDS`, `RUNNER_WORKERS`.

Full list with defaults: `.env.example`.

---

## 9. Where things live

All generated state is under `runtime/` (gitignored):

```
runtime/
├── logs/                       # openjiuwen logs
└── data/
    ├── <job>_repro.json        # the reproduction
    ├── <job>_fix.json          # the fix
    ├── <job>_proof.json        # the proof (verification)
    ├── <job>_review.json       # review + audit
    ├── repos/                  # shallow clones
    └── artifacts/<job>/        # before.png, after.png, proof.png, proof.mp4, observability
```

---

## 10. Troubleshooting

- **`python`/`pip` not found** → use `$PY` (the repo venv) as above.
- **Port already in use** → pick another (`--port 8099`); Streamlit uses 8501, the app dev server 5173.
- **Review page shows stale media** → artifacts keep the same URL; the API sends `no-store`, so just
  restart the server and hard-refresh (Ctrl+Shift+R).
- **`Playwright not installed` / no browser** → `pip install -r requirements.txt` && `python -m playwright install chromium`.
- **`Missing required environment variables`** → fill `API_KEY`/`API_BASE`/`MODEL_NAME` in `.env`
  (or run offline against the sample fixtures).
- **App looks empty** → run `scripts\seed_feed.py 5` (or `make_sample_bug.py`) to create runs.
- **Changed the SvelteKit app but nothing changed** → `cd taketwo\interfaces\app; npm run build`.
- **`APP_START_COMMAND` set but the fix re-run shows the bug** → the app didn't restart; check
  `PATCHED_APP_URL` and that the command serves the patched checkout.

---

## 11. Going further

- **Architecture & rules**: [`architecture.md`](architecture.md).
- **Contributing** (setup, layers, where to add things): [`../CONTRIBUTING.md`](../CONTRIBUTING.md).
- **Quick reference**: [`../QUICKSTART.md`](../QUICKSTART.md).
