# Demo pack

Two tiny buggy web apps, each with a ready-made screen recording, so TakeTwo can be run
end-to-end with no setup. Both clips are committed on purpose — they never change, so there
is no reason to regenerate them.

| Demo | App | Recording | Planted bug |
|---|---|---|---|
| Booking | `booking/index.html` | `booking/clip.mp4` | the date picker closes without selecting → `TypeError` |
| Sign in | `signin/index.html` | `signin/clip.mp4` | sign-in throws `Cannot read properties of null (reading 'value')` |

## Run

```powershell
$PY = "C:\Workspace\openjiuwen\jiuwenswarm\.venv\Scripts\python.exe"

# 1. serve the app under test
& $PY demo\serve.py            # http://localhost:3000

# 2. reproduce + fix it from the recording
& $PY -m taketwo.surfaces.cli record demo\booking\clip.mp4 --app http://localhost:3000
```

Or open either GUI and hit **Try the sample**.

## Regenerate the clips (optional)

```powershell
& $PY demo\make_clip.py            # booking clip (from real browser frames)
```
