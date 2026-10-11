"""Outbound artifacts: render a reproduction's issue and PR text to disk.

Pure rendering lives in :mod:`taketwo.domain.render`; this module only decides where
the files go (``runtime/data/exports/``). It also builds the shareable PNG cards
(score card, proof card) used by every front-end.
"""

from __future__ import annotations

import io
from pathlib import Path

from taketwo.domain import evaluate, render
from taketwo.storage import runtime, store


def write(submission: dict, reproduction: dict, fix: dict | None = None, proof: dict | None = None) -> dict[str, str]:
    """Render and write ``issue.md`` (+ ``pr.md``) for a job; return {kind: path}."""
    exports = runtime.DATA_DIR / "exports"
    exports.mkdir(parents=True, exist_ok=True)
    job = render.job_id(submission)

    written: dict[str, str] = {}
    issue_path = exports / f"{job}_issue.md"
    issue_path.write_text(render.issue_markdown(submission, reproduction), encoding="utf-8")
    written["issue"] = str(issue_path)

    if fix:
        pr_path = exports / f"{job}_pr.md"
        pr_path.write_text(render.pr_markdown(submission, reproduction, fix, proof or {}), encoding="utf-8")
        written["pr"] = str(pr_path)

    return written


def proof_dir() -> Path:
    """Directory holding the before/after clips for a job."""
    path = runtime.ARTIFACTS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _font(size: int):
    from PIL import ImageFont

    try:
        return ImageFont.load_default(size=size)
    except Exception:
        return ImageFont.load_default()


def share_card(rows: list[dict]) -> bytes | None:
    """A branded PNG score card (reproduce rate + counts), or ``None``."""
    if not rows:
        return None
    try:
        from PIL import Image, ImageDraw

        rate = sum(1 for r in rows if r["verdict"] == "reproduced") / len(rows)
        verified = sum(1 for r in rows if r["verified"])
        total = len(rows)

        img = Image.new("RGB", (1000, 560), (11, 11, 15))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, 1000, 12], fill=(124, 58, 237))
        draw.rectangle([0, 548, 1000, 560], fill=(52, 211, 153))
        draw.text((60, 70), "TakeTwo", font=_font(40), fill=(236, 236, 242))
        draw.text((60, 170), f"{rate:.0%}", font=_font(120), fill=(167, 139, 250))
        draw.text((60, 320), "reproduce rate", font=_font(34), fill=(156, 163, 175))
        draw.text((60, 390), f"{verified} verified  ·  {total} runs", font=_font(32), fill=(156, 163, 175))
        draw.text((60, 470), "video in  ·  proof out", font=_font(30), fill=(124, 58, 237))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        return None


def proof_card(job: str) -> bytes | None:
    """A square, post-ready PNG (before | after + verdict/score), or ``None``."""
    repro, proof = store.get_repro(job), store.get_proof(job)
    before, after = repro.get("before_clip", ""), proof.get("after_clip", "")
    image = proof.get("proof_path", "")
    if before and after and Path(before).exists() and Path(after).exists():
        sources = [before, after]
    elif image and Path(image).exists():
        sources = [image]
    else:
        return None
    try:
        from PIL import Image, ImageDraw

        width, height = 1080, 1080
        canvas = Image.new("RGB", (width, height), (11, 11, 15))
        draw = ImageDraw.Draw(canvas)
        area_top, area_h = 150, 700

        if len(sources) == 2:
            half = width // 2
            for index, source in enumerate(sources):
                shot = Image.open(source).convert("RGB")
                shot.thumbnail((half - 24, area_h))
                canvas.paste(shot, (index * half + (half - shot.width) // 2, area_top + (area_h - shot.height) // 2))
            draw.rectangle([half - 2, area_top, half + 2, area_top + area_h], fill=(124, 58, 237))
            draw.text((30, area_top + 12), "BEFORE", font=_font(26), fill=(251, 113, 133))
            draw.text((half + 30, area_top + 12), "AFTER", font=_font(26), fill=(52, 211, 153))
        else:
            shot = Image.open(sources[0]).convert("RGB")
            shot.thumbnail((width - 48, area_h))
            canvas.paste(shot, ((width - shot.width) // 2, area_top + (area_h - shot.height) // 2))

        draw.rectangle([0, 0, width, 12], fill=(124, 58, 237))
        draw.text((30, 40), "TakeTwo", font=_font(46), fill=(236, 236, 242))
        draw.text((30, 100), job[:44], font=_font(26), fill=(156, 163, 175))

        verdict = repro.get("verdict", "unclear")
        colour = (52, 211, 153) if verdict == "reproduced" else (251, 113, 133)
        draw.text((30, height - 150), verdict.replace("_", " ").upper(), font=_font(42), fill=colour)
        draw.text((30, height - 90), f"score {evaluate.score(repro)['score']:.2f}", font=_font(30), fill=(156, 163, 175))
        draw.text((width - 340, height - 90), "video in  ·  proof out", font=_font(26), fill=(124, 58, 237))
        buffer = io.BytesIO()
        canvas.save(buffer, format="PNG")
        return buffer.getvalue()
    except Exception:
        return None
