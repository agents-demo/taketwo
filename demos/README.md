# Demo pack

Self-contained bug demos: a buggy app + a real ~5 s recording for each, so TakeTwo runs
end-to-end with no setup. Adding a demo = adding one folder under `scenarios/`.

```
demos/
├── scenarios/            # one folder per demo
│   ├── booking/          # date-picker bug
│   │   ├── app/index.html
│   │   ├── clip.mp4      # ~5 s screen recording
│   │   ├── scenario.json # title, bug, steps, proof fix, patch
│   │   └── README.md
│   ├── signin/           # login bug  (same shape)
│   └── cart/             # add-to-cart bug  (same shape)
├── serve_scenario.py     # ← run this: serve a scenario's app
├── _scenario.py          # scenario locator (helper)
├── maintenance/          # build the material (not needed to demo)
│   └── record_video.py       # (re)record a scenario's clip
└── README.md
```

## Run one

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"

# 1. serve the app under test
& $PY demos\serve_scenario.py booking                    # http://localhost:3000

# 2. reproduce + fix it from the recording
& $PY -m taketwo.surfaces.cli record demos\scenarios\booking\clip.mp4 --app http://localhost:3000
```

Or open either GUI and pick a demo in the **demo dropdown**, then click **Use this demo**.

## Add a scenario

Create `demos/scenarios/<name>/` with `app/index.html`, `clip.mp4`, and a `scenario.json`
(`title`, `bug`, `steps`, `proof`, `patch`). The scripts pick it up by name — no code changes.
