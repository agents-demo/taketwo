# TakeTwo

Turn a bug report that is just a **shaky screen recording** and the words *"it's broken"* into a
reproduction, a fix, and a **before/after proof video**. Built on [openjiuwen](https://github.com/openJiuwen-ai/agent-core).

- **In:** a screen recording (or screenshots) and the repo.
- **Out:** an issue with reproduction steps, a **draft** PR, and a before/after video. A human
  maintainer approves the merge.

## What it does

1. **Understand.** Extract frames, detect the cursor and clicks, OCR the visible labels, and infer
   the ordered steps the reporter took and where it went wrong.
2. **Reproduce.** Replay those steps in a real sandboxed browser, capturing the console/network at
   the failure, and record the **before** clip.
3. **Repair.** Localize the cause in the repo and propose a minimal patch plus a regression test.
4. **Prove.** Re-run the same steps on the patched branch, record the **after** clip, and stitch a
   labelled before/after video.
5. **Deliver.** Open an issue (steps + evidence) and a draft PR (diff + test + proof).

- **New here?** [QUICKSTART.md](QUICKSTART.md) — the fast path.
- **Full guide:** [docs/USAGE.md](docs/USAGE.md) — setup, interfaces, workflow, API, scripts, settings, troubleshooting.
- **Design:** [docs/architecture.md](docs/architecture.md).

## Two front-ends

Same engine, two surfaces:

- **App** — a **SvelteKit** web app (`interfaces/app/`), served by the API at `/app/`
  (`http://localhost:8000/app/`). Runs, review, scoreboard, with the before/after compare.
- **Console** — a Streamlit dashboard for maintainers/operators (submit, review, scoreboard).

## Layout

```
interfaces -> pipeline -> backend -> domain      (forge, storage, reporting, config are leaves)
```

`tests/unit/test_architecture.py` enforces the direction. `backend/` is the only place that imports
openjiuwen. See the architecture doc for the full package map, and [CONTRIBUTING.md](CONTRIBUTING.md)
to develop.
