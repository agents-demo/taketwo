# Sign in — login

A login form. **Bug:** clicking **Sign in** throws
`TypeError: Cannot read properties of null (reading 'value')`.

- `app/index.html` — the buggy site
- `clip.mp4` — a recording of the bug
- `scenario.json` — title, bug, steps, proof fix, patch

Run it: `python demo/scripts/serve_app.py signin` then reproduce `clip.mp4`.
