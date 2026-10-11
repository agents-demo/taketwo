# Demo pack

Self-contained bug demos: a buggy app + a ready recording for each, so TakeTwo runs
end-to-end with no setup. Adding a demo = adding one folder under `scenarios/`.

```
demo/
├── scenarios/            # one folder per demo
│   ├── booking/          # date-picker bug
│   │   ├── app/index.html
│   │   ├── clip.mp4
│   │   ├── scenario.json # title, bug, steps, proof fix, patch
│   │   └── README.md
│   └── signin/           # login bug  (same shape)
├── scripts/              # the drivers — each takes a scenario name
│   ├── serve_app.py          # serve a scenario's app
│   ├── record_clip.py        # (re)record its clip
│   ├── make_proof.py         # build a real before/after proof
│   ├── seed_scenarios.py     # seed reproduced runs for the feed
│   └── run_live.py           # live end-to-end
└── README.md
```

## Run one

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"

# 1. serve the app under test
& $PY demo\scripts\serve_app.py booking                    # http://localhost:3000

# 2. reproduce + fix it from the recording
& $PY -m taketwo.surfaces.cli record demo\scenarios\booking\clip.mp4 --app http://localhost:3000
```

Or open either GUI and hit **Try the sample**.

## Add a scenario

Create `demo/scenarios/<name>/` with `app/index.html`, `clip.mp4`, and a `scenario.json`
(`title`, `bug`, `steps`, `proof`, `patch`). The scripts pick it up by name — no code changes.
