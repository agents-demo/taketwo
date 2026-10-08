# Architecture

TakeTwo is layered (hexagonal). Dependencies point **inward** only, enforced by
`tests/unit/test_architecture.py` (an AST check), not by convention.

```
interfaces  ──▶  analysis  ──▶  backend  ──▶  domain
                     │
                     └────▶  storage / reporting / config
```

## Layers

| Layer | Package | Responsibility | May depend on |
|---|---|---|---|
| Domain | `domain/` | Pure rules: submission/repro/fix schemas, timeline math, verify, render, evaluate, compare. No I/O, no third-party. | stdlib only |
| Backend | `backend/` | The single home for openjiuwen: settings, models, agent builder, rails, tools, runner, logs, telemetry. Imports no application module. | stdlib, openjiuwen |
| Primitives | `analysis/media/`, `analysis/browser/`, `analysis/forge/` | Shared capability building blocks (video, browser automation, git/GitHub), used by 2+ stages. | stdlib, third-party, storage, config |
| Analysis | `analysis/stages/`, `analysis/pipeline/` | The pipeline (understand → reproduce → repair → prove → deliver), run by two strategies, over the primitives. | backend, primitives, storage, domain, reporting, config |
| Storage | `storage/` | Runtime path layout, JSON helpers, per-job store, repo cache. | config |
| Reporting | `reporting.py` | Outbound artifacts: `issue.md`, `pr.md`, proof manifest. | domain, storage |
| Interfaces | `interfaces/` | Adapters: CLI, HTTP API / GitHub webhook, MCP, Streamlit UI, service façade, worker. | anything |

## Package map

```
taketwo/
├── __init__.py            # version only (no side effects)
├── bootstrap.py           # runtime dirs + logging; called by entry points
├── config.py              # application settings (sampling, thresholds, toggles)
├── reporting.py           # issue.md / pr.md / proof manifest
├── domain/                # pure: submission, timeline, repro, fix, verify, render, evaluate, compare
├── backend/               # openjiuwen only: settings, logs, agent/, telemetry/
├── analysis/
│   ├── progress.py        # neutral leaf: Progress + tick
│   ├── media/             # shared: frames, cursor, ocr, clips
│   ├── browser/           # shared: Playwright session
│   ├── forge/             # shared: repo clone/search/blame + GitHub issue/PR
│   ├── stages/            # understand, reproduce, repair, prove, deliver
│   └── pipeline/          # params, run_session, strategies/{deterministic, agentic}
├── storage/               # runtime, json_store, jobs, cache
└── interfaces/            # cli, api, service, worker, mcp/, web/
```

## The backend package

`backend/` is the single home for everything under-the-hood of the agentic system: every openjiuwen
import, model/agent access, rails, and telemetry. `config.py` holds only *application* settings.
The façade is small (`build`, `TextParams`/`VisionParams`, `run_agent`, `run_text`, `ConfigError`,
`configure_logging`); everything else is internal.

```
backend/
├── __init__.py            # the façade
├── settings.py            # env: endpoints, keys, model names, timeouts, embeddings, budget/tracing
├── logs.py                # route openjiuwen logging to a directory
├── agent/
│   ├── builder/           # build.py (entry), base.py, params.py (Text/Vision), text.py, vision.py, result.py
│   ├── models/            # build_model(params) (constructs an openjiuwen Model)
│   ├── rails.py           # AgentRail base + TokenBudgetRail + memory_rail() + resolve()
│   ├── tools.py           # make_tool()/make_tools() (openjiuwen tool decoration)
│   └── runner.py          # Runner lifecycle, run_agent(), run_text(), callback bridge
└── telemetry/             # usage, traces, recorder
```

## The analysis package

The pipeline runs five stages in one of two interchangeable strategies. The strategies share a base
class (template method): `analyze` prepares the run (clone repo + understand), calls the
mode-specific `_run`, then finalizes (usage, job patch, exports). Callers obtain a strategy from the
`pipeline` package — they never import a concrete module.

```
analysis/
├── progress.py            # run progress (neutral leaf)
├── agent_reply.py         # run an agent + parse its strict JSON (understand, repair)
├── media/                 # frames, cursor, ocr, clips
├── browser/               # Playwright session (open, act, console, snapshot, record)
├── forge/                 # repo + GitHub (clone, search, blame, publish_branch, open_issue, open_pr)
├── stages/
│   ├── understand/        # recording -> timeline + failure hypothesis
│   ├── reproduce/         # timeline  -> reproduced run + evidence + before clip
│   ├── repair/            # evidence  -> localized cause + patch + test
│   ├── prove/             # patch     -> after clip + before/after proof video
│   └── deliver/           # artifacts -> issue + draft PR
└── pipeline/
    ├── params.py          # Params: request + run state
    ├── run_session.py     # run recorder, browser session, vision agent, media dir
    └── strategies/        # base, resolve_strategy, deterministic, agentic
```

## Boundaries & conventions

- **No import side effects.** `__init__.py` is imports/docstring only; `bootstrap.setup()` creates
  runtime dirs and configures logging (called by every entry point and by `conftest.py`).
- **One façade per framework.** openjiuwen is confined to `backend/`; browser and GitHub are
  capability primitives under `analysis/`, the same way media tools are.
- **Single source of paths.** All generated state lives under `runtime/` via `storage.runtime`.
- **Schema at the boundary.** `domain.*.normalize/validate` runs where artifacts are stored.
- **Never auto-merge.** The pipeline opens a *draft* PR; approval is a human step.

## Data flow

```
recording ─▶ analysis.stages.understand  (media: frames + cursor + ocr)      ─▶ timeline.json
          ─▶ analysis.stages.reproduce   (browser: replay + console + record)─▶ repro.json + before.mp4
          ─▶ analysis.stages.repair      (forge: search + blame; agent patch)─▶ fix.diff + test
          ─▶ analysis.stages.prove       (browser + media: record + stitch)   ─▶ proof.mp4
          ─▶ analysis.stages.deliver     (forge + reporting)                  ─▶ issue + draft PR
```
