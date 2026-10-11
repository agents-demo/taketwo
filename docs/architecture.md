# Architecture

TakeTwo is layered (hexagonal). Dependencies point **inward** only, enforced by
`tests/unit/test_architecture.py` (an AST check), not by convention.

```
surfaces  ──▶  core  ──▶  integrations  ──▶  domain
```

- `domain/` — the pure center (stdlib only).
- `integrations/` — outbound adapters to the outside world (agents, browser, forge, appserver, storage, reporting).
- `core/` — the application / business logic: the workflow, its strategy, the run runtime.
- `surfaces/` — inbound adapters (the way anything drives TakeTwo).

`core/config.py` (application settings) and `core/bootstrap.py` (runtime wiring) live with `core/`;
`surfaces/readiness.py` (environment checks for the GUIs) lives with `surfaces/`.

## Layers

| Layer | Package | Responsibility | May depend on |
|---|---|---|---|
| Domain | `domain/` | Pure rules: submission/repro/fix schemas, timeline math, verify, render, evaluate, compare. No I/O, no third-party. | stdlib only |
| Integrations | `integrations/` | Outbound adapters: `agents/` (openjiuwen), `browser` (Playwright), `forge/` (GitHub), `appserver`, `storage/`, `reporting`. | domain, stdlib, 3rd-party |
| Core | `core/` | The staged workflow (understand → reproduce → repair → prove → deliver) + strategies, the sandboxed `jobs/` runner, and the run/ask `service`. | integrations, domain |
| Surfaces | `surfaces/` | Inbound adapters (one folder per entry point): CLI, MCP, gui1 (Streamlit), gui2 (SvelteKit SPA + its FastAPI server). | anything |

## Package map

```
taketwo/
├── __init__.py            # version only (no side effects)
├── domain/                # pure: submission, timeline, repro, fix, verify, render, evaluate, compare
├── integrations/          # outbound adapters
│   ├── agents/            #   openjiuwen: settings, models, agent builder, rails, telemetry
│   ├── browser.py         #   Playwright (the only playwright import)
│   ├── forge/             #   GitHub: repo clone/search/blame + issue/draft PR
│   ├── appserver.py       #   serve the app under test
│   ├── storage/           #   runtime paths, json_store, job store, repo cache
│   └── reporting.py       #   issue.md / pr.md + share cards
├── core/                  # the workflow + runtime
│   ├── bootstrap.py       #   runtime dirs + logging; called by entry points
│   ├── config.py          #   application settings (sampling, thresholds, toggles)
│   ├── service.py         #   run/ask façade
│   ├── params.py          #   Params: request + run state
│   ├── progress.py        #   run progress
│   ├── run_session.py     #   run recorder, browser session, media dir
│   ├── agent_reply.py     #   run an agent (retry/backoff) + parse its strict JSON
│   ├── jobs/              #   sandboxed runner + worker
│   ├── stages/            #   order is data: core.stages.STAGES
│   └── strategies/        #   deterministic / agentic
└── surfaces/              # entry points: readiness.py, cli/, mcp/, gui1/, gui2/
```

## The integrations package

`integrations/agents/` is the single home for everything under-the-hood of the agentic system: every
openjiuwen import, model/agent access, rails, and telemetry. The façade is small (`build`,
`TextParams`/`VisionParams`, `run_agent`, `run_text`, `ConfigError`, `configure_logging`); everything
else is internal.

```
integrations/agents/
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

## The core package

The workflow runs five stages in one of two interchangeable strategies. The strategies share a base
class (template method): `analyze` prepares the run (validate submission + start session), calls the
mode-specific `_run`, then finalizes (usage, job summary, exports). Callers obtain a strategy from the
`core` package — they never import a concrete module.

```
core/
├── __init__.py            # orchestrator façade: resolve(), get_strategy(), Params, Strategy
├── progress.py            # run progress
├── agent_reply.py         # run an agent (retry/backoff) + parse its strict JSON (understand, repair)
├── params.py              # Params: request + run state
├── run_session.py         # run recorder, browser session, vision agent, media dir
├── service.py             # run/ask façade used by the surfaces
├── jobs/                  # sandboxed runner (runner.py) + worker.py
├── stages/                # order is data: core.STAGES (not folder numbers)
│   ├── understand/        # 01 recording -> timeline + failure hypothesis
│   ├── reproduce/         # 02 timeline  -> reproduced run + evidence + before clip
│   ├── repair/            # 03 evidence  -> localized cause (strings + console traces) + patch + test
│   ├── prove/             # 04 patch     -> after clip + before/after proof video
│   └── deliver/           # 05 artifacts -> issue + draft PR
└── strategies/            # base, resolve_strategy, deterministic, agentic
```

## Boundaries & conventions

- **No import side effects.** `__init__.py` is imports/docstring only; `bootstrap.setup()` creates
  runtime dirs and configures logging (called by every entry point and by `conftest.py`).
- **One façade per framework.** openjiuwen is confined to `integrations/agents/`; Playwright is
  confined to `integrations/browser.py`; GitHub lives in `integrations/forge/`.
- **Single source of paths.** All generated state lives under `runtime/` via `integrations.storage.runtime`.
- **Schema at the boundary.** `domain.*.normalize/validate` runs where artifacts are stored.
- **Never auto-merge.** Delivery opens a *draft* PR; approval is a human step.

## Data flow

```
recording ─▶ core.stages.understand  (frames + cursor + contact sheet)   ─▶ timeline.json
          ─▶ core.stages.reproduce   (browser: replay + console + record)─▶ repro.json + before.png
          ─▶ core.stages.repair      (forge: search/blame + console trace)─▶ fix.diff + test
          ─▶ core.stages.prove       (serve patched app + re-run + stitch)─▶ proof.mp4
          ─▶ core.stages.deliver     (forge + reporting)                  ─▶ issue + draft PR
```

## Surfaces: two GUIs

Both are inbound adapters over the same engine, with the same features; keep them independent.

**gui1** (`surfaces/gui1/`) — a **Streamlit** app:

- `ui.py` — entry point: page config, logo, `st.navigation`.
- `app_pages/` — the pages: `pages.py` (registry), `runs.py`, `detail.py`, `scoreboard.py`.
- `components/` — one widget per file (empty_state, proof, compare, execution, chat, live_job, new_run, readiness, run_summary, runs_table).
- `config.py` / `data.py` / `samples.py` / `session.py` / `share.py` / `charts.py` — helpers.
- Theme lives in `.streamlit/config.toml`.

**gui2** (`surfaces/gui2/`) — the **web app**: a FastAPI server (`server/`) that exposes the JSON
endpoints and serves the bundled **SvelteKit** SPA (`client/`) at `/gui2/` (adapter-static, base
`/gui2`; the `spa()` route falls back to `index.html` for client routes). Run it with
`uvicorn taketwo.surfaces.gui2:app`; develop the SPA with `npm run dev` in `client/` (5173,
CORS-enabled).

## Tools & scripts

- `scripts/samples/make_sample_bug.py` — synthetic fixtures (offline demo + a `_live` variant).
- `scripts/samples/serve_sample_app.py` — serve `demo/booking` for a live reproduction.
- `scripts/check/dogfood.py` — live end-to-end: reproduce a real browser bug → before/after proof.
- `scripts/check/benchmark.py` — reproduce rate over seeded apps (generalization signal).
- `scripts/check/evaluate_repros.py` — offline quality gate against `tests/eval/expected.json`.
