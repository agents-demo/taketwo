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
- **Run a demo step by step:** [docs/RUN_DEMO.md](docs/RUN_DEMO.md).
- **Full guide:** [docs/USAGE.md](docs/USAGE.md) — setup, surfaces, workflow, API, scripts, settings, troubleshooting.
- **Design:** [docs/architecture.md](docs/architecture.md).

## Two GUIs

Same engine, two identical surfaces:

- **gui1** — a **Streamlit** dashboard (`surfaces/gui1/`):
  `& $PY -m streamlit run taketwo/surfaces/gui1/ui.py` → `http://localhost:8501`.
- **gui2** — the web app (`surfaces/gui2/`): a FastAPI server (`server/`) serving a SvelteKit SPA
  (`client/`) at `/gui2/` (`http://localhost:8000/gui2/`).

## Layout

```
surfaces -> core -> integrations -> domain
```

`tests/unit/test_architecture.py` enforces the direction. `integrations/agents/` is the only place that imports
openjiuwen. See the architecture doc for the full package map, and [CONTRIBUTING.md](CONTRIBUTING.md)
to develop.
