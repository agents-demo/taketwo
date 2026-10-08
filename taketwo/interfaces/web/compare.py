"""A before/after comparison slider (Streamlit Custom Component v2, inline).

The product's proof is "the same scenario, before and after"; this is the drag-to-compare
view of it. Uses Streamlit's ``--st-*`` theme tokens so it follows light/dark automatically.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

_HTML = """
<div class="cmp">
  <img class="after" alt="After the fix" />
  <img class="before" alt="Before the fix" />
  <div class="handle"></div>
  <input class="slider" type="range" min="0" max="100" value="50" aria-label="Compare before and after" />
  <span class="tag left">before</span>
  <span class="tag right">after</span>
</div>
"""

_CSS = """
.cmp { position: relative; width: 100%; height: 100%; overflow: hidden;
       border: 1px solid var(--st-border-color); border-radius: var(--st-base-radius);
       background: var(--st-secondary-background-color); }
.cmp img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain;
           background: var(--st-secondary-background-color); }
.before { z-index: 2; }
.handle { position: absolute; top: 0; bottom: 0; left: 50%; width: 2px;
          background: var(--st-primary-color); z-index: 4; pointer-events: none; }
.handle::after { content: ""; position: absolute; top: 50%; left: 50%; width: 28px; height: 28px;
                 transform: translate(-50%, -50%); border-radius: 50%;
                 background: var(--st-primary-color); border: 2px solid var(--st-background-color); }
.slider { position: absolute; inset: 0; width: 100%; height: 100%; margin: 0; opacity: 0;
          cursor: ew-resize; z-index: 5; }
.tag { position: absolute; top: 8px; z-index: 3; padding: 4px 8px; border-radius: 999px;
       font: 600 11px/1 var(--st-font); letter-spacing: .06em; text-transform: uppercase;
       color: var(--st-text-color); background: var(--st-secondary-background-color);
       border: 1px solid var(--st-border-color); }
.tag.left { left: 8px; }
.tag.right { right: 8px; }
"""

_JS = """
export default function (component) {
  const { data, parentElement } = component;
  const root = parentElement.querySelector(".cmp");
  const before = parentElement.querySelector(".before");
  const after = parentElement.querySelector(".after");
  const slider = parentElement.querySelector(".slider");
  const handle = parentElement.querySelector(".handle");
  if (!root || !before || !after || !slider || !handle) return;

  const b = (data && data.before) || "";
  const a = (data && data.after) || "";
  if (before.getAttribute("src") !== b) before.setAttribute("src", b);
  if (after.getAttribute("src") !== a) after.setAttribute("src", a);

  const setX = (x) => {
    const pct = Math.max(0, Math.min(100, Number(x)));
    before.style.clipPath = `inset(0 ${100 - pct}% 0 0)`;
    handle.style.left = pct + "%";
    slider.value = String(pct);
  };

  slider.oninput = (event) => setX(event.target.value);
  setX(slider.value || 50);
}
"""

_COMPARE = st.components.v2.component("taketwo_compare", html=_HTML, css=_CSS, js=_JS)


def _data_url(path: str) -> str:
    file = Path(path)
    ext = file.suffix.lstrip(".").lower() or "png"
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return f"data:{mime};base64,{base64.b64encode(file.read_bytes()).decode('ascii')}"


def before_after(before: str, after: str, *, height: int = 420, key: str | None = None) -> None:
    """Drag-to-compare slider for a before and after image (renders nothing if either is missing)."""
    if not (before and after and Path(before).exists() and Path(after).exists()):
        return
    _COMPARE(data={"before": _data_url(before), "after": _data_url(after)}, width="stretch", height=height, key=key)
