# Architecture

TakeTwo is layered (hexagonal). Dependencies point **inward** only, enforced by
`tests/unit/test_architecture.py` (an AST check), not by convention.

```
interfaces  ──▶  pipeline  ──▶  backend  ──▶  domain
                     │
                     └────▶  storage / reporting / config   (neutral leaves)
```

The pipeline owns its **capability adapter** `pipeline/forge` (git/GitHub) and confines the browser to
the reproduce stage (`pipeline/stages/reproduce/browser.py`); video/image helpers live with the stage
that uses them. All of these are pipeline-only, so none is a separate top-level layer.

## Layers

| Layer | Package | Responsibility | May depend on |
|---|---|---|---|
| Domain | `domain/` | Pure rules: submission/repro/fix schemas, timeline math, verify, render, evaluate, compare. No I/O, no third-party. | stdlib only |
| Backend | `backend/` | The single home for openjiuwen: settings, models, agent builder, rails, tools, runner, logs, telemetry. Imports no application module. | stdlib, openjiuwen |
| Pipeline | `pipeline/` | The staged workflow (understand → reproduce → repair → prove → deliver), run by two strategies, plus its capability adapter `forge/`; the browser lives inside the reproduce stage. | backend, storage, domain, reporting, config |
| Storage | `storage/` | Runtime path layout, JSON helpers, per-job store, repo cache. | config |
| Reporting | `reporting.py` | Outbound artifacts: `issue.md`, `pr.md`, proof manifest. | domain, storage |
| Interfaces | `interfaces/` | Adapters: CLI, HTTP API / GitHub webhook, MCP, Streamlit web console, service façade, sandboxed job runner, worker. | anything |

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
└── interfaces/            # cli, api, service, worker, runner (sandbox queue), mcp/, web/
                           #   web/: ui.py (entry) + app_pages/{runs,detail,scoreboard} + common + compare
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
├── agent_reply.py         # run an agent (retry/backoff) + parse its strict JSON (understand, repair)
├── params.py              # Params: request + run state
├── run_session.py         # run recorder, browser session, vision agent, media dir
├── appserver.py           # start/stop the app under test (prologue + prove)
├── forge/                 # adapter: repo clone/search/blame + publish/PR
├── stages/                # order is data: pipeline.STAGES (not folder numbers)
│   ├── understand/        # 01 recording -> timeline + failure hypothesis
│   ├── reproduce/         # 02 timeline  -> reproduced run + evidence + before clip
│   │   └── browser.py     #    the stage's Playwright session (only playwright import)
│   ├── repair/            # 03 evidence  -> localized cause (strings + console traces) + patch + test
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
recording ─▶ pipeline.stages.understand  (frames + cursor + contact sheet)   ─▶ timeline.json
          ─▶ pipeline.stages.reproduce   (browser: replay + console + record)─▶ repro.json + before.png
          ─▶ pipeline.stages.repair      (forge: search/blame + console trace)─▶ fix.diff + test
          ─▶ pipeline.stages.prove       (serve patched app + re-run + stitch)─▶ proof.mp4
          ─▶ pipeline.stages.deliver     (forge + reporting)                  ─▶ issue + draft PR
```

## Interfaces: two front-ends

Both are inbound adapters over the same engine; keep them independent.

**App** (`interfaces/app/`) — a **SvelteKit** single-page app, served by the API at `/app/`
(adapter-static, base `/app`; the FastAPI `spa()` route falls back to `index.html` for client
routes). Uses `/scoreboard`, `/runs`, `/jobs`, `/media`. `npm run dev` (5173) is CORS-enabled by the
API for development. This is the consumer surface.

**Console** (`interfaces/web/`) — a Streamlit app for maintainers/operators:


- `ui.py` — entry point: page config, logo, `st.navigation`.
- `app_pages/pages.py` — the `st.Page` registry (single source of truth for nav + links).
- `app_pages/runs.py` — submit (upload or one-tap live sample), a live `st.status(type="step")`
  job feed with cancel/retry, the runs table + drawer.
- `app_pages/detail.py` — proof hero (autoplay video / drag-compare), fix, evidence timeline,
  review + audit, and a grounded follow-up chat.
- `app_pages/scoreboard.py` — public reproduce rate, hall of fame, per-repo leaderboard.
- `common.py` / `compare.py` — shared helpers and the CCv2 components (compare slider, share cards).

Theming is native via `.streamlit/config.toml` (no injected CSS). The engine it drives is unchanged.

## Tools & scripts

- `scripts/make_sample_bug.py` — synthetic fixtures (offline demo + a `_live` variant).
- `scripts/serve_sample_app.py` — serve `examples/sample_app` for a live reproduction.
- `scripts/dogfood.py` — live end-to-end: reproduce a real browser bug → before/after proof.
- `scripts/benchmark.py` — reproduce rate over seeded apps (generalization signal).
- `scripts/evaluate_repros.py` — offline quality gate against `tests/eval/expected.json`.
