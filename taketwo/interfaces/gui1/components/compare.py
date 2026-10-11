"""The before/after hero — a Streamlit Custom Component v2 (inline).

A full-bleed, draggable comparison of the same scenario before and after the fix: the
product's signature artifact. Uses Streamlit's ``--st-*`` theme tokens and a violet
accent gradient so it feels at home in light and dark.
"""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

_HTML = """
<div class="hero" tabindex="0" role="slider" aria-label="Before and after comparison" aria-valuemin="0" aria-valuemax="100" aria-valuenow="50">
  <img class="frame after" alt="After the fix" />
  <img class="frame before" alt="Before the fix" />
  <div class="divider"><span class="knob">&#8646;</span></div>
  <span class="chip before-chip">Before</span>
  <span class="chip after-chip">After</span>
  <span class="hint">Drag to compare</span>
</div>
"""

_CSS = """
.hero {
  position: relative; width: 100%; height: 100%; overflow: hidden;
  border-radius: 16px; border: 1px solid var(--st-border-color);
  background:
    radial-gradient(120% 120% at 0% 0%, color-mix(in srgb, var(--st-primary-color) 14%, transparent), transparent 55%),
    var(--st-secondary-background-color);
  cursor: ew-resize; user-select: none; touch-action: none;
}
.frame { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: contain;
         background: var(--st-secondary-background-color); pointer-events: none; }
.before { clip-path: inset(0 50% 0 0); }
.divider { position: absolute; top: 0; bottom: 0; left: 50%; width: 2px; transform: translateX(-1px);
           background: linear-gradient(180deg, transparent, var(--st-primary-color) 12%, var(--st-primary-color) 88%, transparent);
           box-shadow: 0 0 18px color-mix(in srgb, var(--st-primary-color) 55%, transparent); }
.knob { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-size: 20px; color: #fff; background: var(--st-primary-color);
        box-shadow: 0 0 0 6px color-mix(in srgb, var(--st-primary-color) 22%, transparent), 0 10px 30px rgba(0,0,0,.45);
        animation: glow 2.6s ease-in-out infinite; }
@keyframes glow {
  0%, 100% { box-shadow: 0 0 0 6px color-mix(in srgb, var(--st-primary-color) 22%, transparent), 0 10px 30px rgba(0,0,0,.45); }
  50%      { box-shadow: 0 0 0 13px color-mix(in srgb, var(--st-primary-color) 10%, transparent), 0 10px 30px rgba(0,0,0,.45); }
}
.chip { position: absolute; top: 14px; padding: 6px 12px; border-radius: 999px;
        font: 600 11px/1 var(--st-font); letter-spacing: .08em; text-transform: uppercase;
        backdrop-filter: blur(8px); }
.before-chip { left: 14px; color: #FB7185;
               background: color-mix(in srgb, #FB7185 18%, var(--st-secondary-background-color));
               border: 1px solid color-mix(in srgb, #FB7185 45%, transparent); }
.after-chip  { right: 14px; color: #34D399;
               background: color-mix(in srgb, #34D399 18%, var(--st-secondary-background-color));
               border: 1px solid color-mix(in srgb, #34D399 45%, transparent); }
.hint { position: absolute; bottom: 12px; left: 50%; transform: translateX(-50%);
        font: 500 12px/1 var(--st-font); color: var(--st-text-color); opacity: .6; }
"""

_JS = """
export default function (component) {
  const { data, parentElement } = component;
  const hero = parentElement.querySelector(".hero");
  const before = parentElement.querySelector(".before");
  const after = parentElement.querySelector(".after");
  const divider = parentElement.querySelector(".divider");
  if (!hero || !before || !after || !divider) return;

  const b = (data && data.before) || "";
  const a = (data && data.after) || "";
  if (before.getAttribute("src") !== b) before.setAttribute("src", b);
  if (after.getAttribute("src") !== a) after.setAttribute("src", a);

  const setX = (x) => {
    const p = Math.max(0, Math.min(100, Number(x)));
    before.style.clipPath = `inset(0 ${100 - p}% 0 0)`;
    divider.style.left = p + "%";
    hero.setAttribute("aria-valuenow", String(Math.round(p)));
  };
  setX(50);

  const at = (clientX) => {
    const rect = hero.getBoundingClientRect();
    setX(((clientX - rect.left) / rect.width) * 100);
  };

  hero.addEventListener("pointerdown", (event) => {
    hero.setPointerCapture(event.pointerId);
    at(event.clientX);
    const move = (e) => at(e.clientX);
    const up = () => { hero.removeEventListener("pointermove", move); hero.removeEventListener("pointerup", up); };
    hero.addEventListener("pointermove", move);
    hero.addEventListener("pointerup", up);
  });
  hero.addEventListener("keydown", (event) => {
    const current = Number(hero.getAttribute("aria-valuenow")) || 50;
    if (event.key === "ArrowLeft") setX(current - 2);
    if (event.key === "ArrowRight") setX(current + 2);
  });
}
"""

_HERO = st.components.v2.component("taketwo_hero", html=_HTML, css=_CSS, js=_JS)


def _data_url(path: str) -> str:
    file = Path(path)
    ext = file.suffix.lstrip(".").lower() or "png"
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    return f"data:{mime};base64,{base64.b64encode(file.read_bytes()).decode('ascii')}"


def before_after(before: str, after: str, *, height: int = 460, key: str | None = None) -> None:
    """The drag-to-compare hero (renders nothing if either image is missing)."""
    if not (before and after and Path(before).exists() and Path(after).exists()):
        return
    try:
        _HERO(data={"before": _data_url(before), "after": _data_url(after)}, width="stretch", height=height, key=key)
    except Exception:
        # The component registers at import; if unavailable, fall back to static stills.
        st.image([before, after], width="stretch", alt=["Before the fix", "After the fix"])
