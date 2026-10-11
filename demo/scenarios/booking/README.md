# Booking — date picker

A booking form. **Bug:** clicking a day closes the picker without setting a date and
throws `TypeError: Cannot read properties of null (reading 'value')`.

- `app/index.html` — the buggy site
- `clip.mp4` — a recording of the bug
- `scenario.json` — title, bug, steps, proof fix, patch

Run it: `python demo/scripts/serve_app.py booking` then reproduce `clip.mp4`.
