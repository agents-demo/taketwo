# Run a demo — step by step

This page shows how to run TakeTwo on a demo and get a result. It uses a real model,
a real browser, and the demo bug apps in `demos/scenarios/`.

You can do everything in a GUI. There are two GUIs:

- **gui1** — the Streamlit app (opens in your browser).
- **gui2** — the web app (also opens in your browser).

Pick one. The steps are almost the same.

---

## Before you start

Open a PowerShell window and set the Python path once:

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"
cd C:\Workspace\openjiuwendemos\taketwo
```

Check that `.env` has a model (a real model, not a fake):

```powershell
Get-Content .env | Select-String "API_KEY|API_BASE|MODEL_NAME|VISION_MODEL_NAME"
```

`GITHUB_TOKEN` is optional. Without it, TakeTwo will not open a pull request, but the
analysis still works.

---

## Option A — gui1 (the Streamlit app)

### 1. Start gui1

```powershell
& $PY -m streamlit run taketwo\surfaces\gui1\ui.py
```

Leave this window open.

### 2. Open the GUI

In your browser, open:

```
http://localhost:8501
```

### 3. Check the Readiness line

On the **Runs** page, the small **Readiness** line shows:

```
✅ model · ✅ browser · ⚠️ delivery · ✅ sample
```

`⚠️ delivery` is fine (no GitHub token).

### 4. Start a run

The **New run** box has two tabs: **Try a demo** and **Your own bug**.

- **Try a demo** — pick a demo from the dropdown and click **Run the "…" demo**. It serves the
  demo app and starts the run right away.
- **Your own bug** — upload a recording (or paste a clip path), set the repository / app URL,
  and click **Record & reproduce**.

---

## Option B — gui2 (the web app)

### 1. Start gui2

```powershell
& $PY -m uvicorn taketwo.surfaces.gui2:app --port 8000
```

Leave this window open. It is the server.

### 2. Open the GUI

In your browser, open:

```
http://127.0.0.1:8000/gui2/
```

### 3. Check the Readiness line

On the **Runs** page, find the small line called **Readiness** (it is between
**Latest run** and **New run**). You want:

```
✓ model   ✓ browser   ✓ sample
```

`✗ delivery` is fine. It only means there is no GitHub token.

If you do not see the Readiness line, your server is old. Stop it (Ctrl+C) and start
it again (step 1).

### 4. Start a run

The **New run** box has two tabs: **Try a demo** and **Your own bug**.

- **Try a demo** — pick a demo and click **Run this demo**. gui2 serves the demo app for you.
- **Your own bug** — upload a clip (or paste a path), set the repository / app URL, and click
  **Record & reproduce**.

### 5. Watch the run

A card appears with a **live feed**: understand → reproduce → … . When it is done, the
card stops.

### 6. See the result

Click the finished run. The **Review** page shows:

- the before/after proof (video or compare slider),
- the steps and the evidence,
- the fix,
- **Usage** and **Execution** panels,
- an **Ask** box.

---

## Option C — command line (no GUI)

Start the demo app in one window:

```powershell
& $PY demos\serve_scenario.py booking
```

In a second window, run TakeTwo:

```powershell
& $PY -m taketwo.surfaces.cli record demos\scenarios\booking\clip.mp4 --app http://localhost:3000
```

Other commands:

```powershell
& $PY -m taketwo.surfaces.cli history    # list recent runs
& $PY -m taketwo.surfaces.cli show       # print the latest run's issue text
```

---

## What the run does

TakeTwo runs five stages:

| Stage | What it does |
|---|---|
| understand | the model watches the clip and writes the steps + the failure idea |
| reproduce | it repeats the steps in a real browser and captures the error + a "before" picture |
| repair | it finds the cause and writes a fix (a diff) + a test |
| prove | it runs the fixed app again and builds the "after" proof |
| deliver | it writes the issue and opens a draft pull request |

Add `--agentic` on the CLI (or the **Agentic** switch in a GUI) to let the model drive
the run.

---

## Where the results are

```
runtime/data/<job>_repro.json      # the reproduction
runtime/data/<job>_fix.json        # the fix
runtime/data/<job>_proof.json      # the proof
runtime/data/<job>_summary.json    # the whole run
runtime/data/artifacts/<job>/      # before.png, after.png, proof.png, proof.mp4
runtime/data/exports/<job>_issue.md # the issue text
```

`<job>` is the run id, for example `clip-3f9a1c`.

In the GUI you also see the **Review** page and the **Scoreboard**.

---

## One important thing

**Demos use the model, and still reproduce reliably.**

`understand` runs the **vision model** on the recording (it reads a contact sheet of frames) —
same as for your own clips. If the model's steps miss the bug, TakeTwo falls back to a shipped
**timeline** (`clip.mp4.timeline.json`) with the exact steps, so the browser replay still hits the
bug. The **✅** in the demo dropdown means a demo has that fallback (a **⚠** demo has none).

So on a demo you get the real pipeline — vision understand → browser reproduce. (Demos have no
repository, so there's still no fix/proof/PR; see below.)

The demo apps are single HTML files. They are **not** a git repository. So on a demo you
get:

- understand (the steps),
- reproduce (the error + the "before" picture).

You do **not** get a fix, a proof, or a pull request, because there is no repository to
change.

To get the full run (fix + proof + pull request), point TakeTwo at a real repository:

```powershell
# In .env, set:
#   APP_START_COMMAND="npm run dev"
#   APP_URL=http://localhost:3000
#   TEST_COMMAND="npm test"
#   GITHUB_TOKEN=...

& $PY -m taketwo.surfaces.cli record path\to\bug.mov --repo owner/name --app http://localhost:3000
```

---

## Problems

- **Port 8000 is busy** → use another port: `--port 8011`.
- **The Readiness line is missing** → the server is old. Restart it.
- **The Demo dropdown is empty** → the scenarios are missing; check `demos/scenarios/`.
- **Nothing fills after `Use this demo`** → that scenario's `clip.mp4` is missing.
- **Playwright error** → run:
  ```powershell
  & $PY -m pip install -r requirements.txt
  & $PY -m playwright install chromium
  ```
- **No model** → fill `API_KEY`, `API_BASE`, `MODEL_NAME` in `.env`.
