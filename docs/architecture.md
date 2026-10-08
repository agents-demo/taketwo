# Architecture

TakeTwo is layered (hexagonal). Dependencies point **inward** only, enforced by
`tests/unit/test_architecture.py` (an AST check), not by convention.

```
interfaces  ──▶  pipeline  ──▶  backend  ──▶  domain
                     │
                     └────▶  storage / reporting / config   (neutral leaves)
```

The pipeline also owns its **capability adapters** — `pipeline/media`, `pipeline/forge`, and the
reproduce stage's `pipeline/stages/reproduce/browser`; they are used only inside the pipeline, so
they live under it rather than as separate top-level layers.

## Layers

| Layer | Package | Responsibility | May depend on |
|---|---|---|---|
| Domain | `domain/` | Pure rules: submission/repro/fix schemas, timeline math, verify, render, evaluate, compare. No I/O, no third-party. | stdlib only |
| Backend | `backend/` | The single home for openjiuwen: settings, models, agent builder, rails, tools, runner, logs, telemetry. Imports no application module. | stdlib, openjiuwen |
| Pipeline | `pipeline/` | The staged workflow (understand → reproduce → repair → prove → deliver), run by two strategies, plus its capability adapters (`media/`, `forge/`; the browser lives inside the reproduce stage). | backend, storage, domain, reporting, config |
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
├── pipeline/              # the staged workflow + its capability adapters (see below)
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

## The pipeline package

The pipeline runs five stages in one of two interchangeable strategies. The strategies share a base
class (template method): `analyze` prepares the run (validate submission + start session), calls the
mode-specific `_run`, then finalizes (usage, job summary, exports). Callers obtain a strategy from
the `pipeline` package — they never import a concrete module.

```
pipeline/
├── __init__.py            # orchestrator façade: resolve(), get_strategy(), Params, Strategy
├── progress.py            # run progress (neutral leaf)
├── agent_reply.py         # run an agent + parse its strict JSON (understand, repair)
├── params.py              # Params: request + run state
├── run_session.py         # run recorder, browser session, vision agent, media dir
├── media/                 # adapter: frames, cursor, ocr, clips
├── forge/                 # adapter: repo clone/search/blame + publish/PR
├── stages/                # order is data: pipeline.STAGES (not folder numbers)
│   ├── understand/        # 01 recording -> timeline + failure hypothesis
│   ├── reproduce/         # 02 timeline  -> reproduced run + evidence + before clip
│   │   └── browser/       #    the stage's Playwright session (only playwright import)
│   ├── repair/            # 03 evidence  -> localized cause + patch + test
│   ├── prove/             # 04 patch     -> after clip + before/after proof video
│   └── deliver/           # 05 artifacts -> issue + draft PR
└── strategies/            # base, resolve_strategy, deterministic, agentic
```

## Boundaries & conventions

- **No import side effects.** `__init__.py` is imports/docstring only; `bootstrap.setup()` creates
  runtime dirs and configures logging (called by every entry point and by `conftest.py`).
- **One façade per framework.** openjiuwen is confined to `backend/`; GitHub is a pipeline adapter
  (`pipeline/forge`) and the browser is confined to the reproduce stage
  (`pipeline/stages/reproduce/browser`, the only place Playwright is imported).
- **Single source of paths.** All generated state lives under `runtime/` via `storage.runtime`.
- **Schema at the boundary.** `domain.*.normalize/validate` runs where artifacts are stored.
- **Never auto-merge.** The pipeline opens a *draft* PR; approval is a human step.

## Data flow

```
recording ─▶ pipeline.stages.understand  (media: frames + cursor + ocr)      ─▶ timeline.json
          ─▶ pipeline.stages.reproduce   (browser: replay + console + record)─▶ repro.json + before.mp4
          ─▶ pipeline.stages.repair      (forge: search + blame; agent patch)─▶ fix.diff + test
          ─▶ pipeline.stages.prove       (browser + media: record + stitch)   ─▶ proof.mp4
          ─▶ pipeline.stages.deliver     (forge + reporting)                  ─▶ issue + draft PR
```
