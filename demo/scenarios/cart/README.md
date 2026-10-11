# Cart — add to cart

A product page. **Bug:** the quantity stepper works, but clicking **Add to cart** throws
`TypeError: Cannot read properties of null (reading 'classList')`.

- `app/index.html` — the buggy site
- `clip.mp4` — a ~5 s recording of the bug
- `scenario.json` — title, bug, steps, proof fix, patch

Run it: `python demo/scripts/serve_app.py cart` then reproduce `clip.mp4`.
