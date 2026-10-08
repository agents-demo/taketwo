"""Compose the before/after proof image via the shared media primitives."""

from __future__ import annotations

from taketwo.analysis.media import clips


def proof(before: str, after: str, out_path: str) -> str | None:
    """Return the path to a labelled ``[before | after]`` image (or ``None``)."""
    if not before or not after:
        return None
    return clips.stitch_side_by_side(before, after, out_path, label=True)


def proof_video(before: str, after: str, out_path: str) -> str | None:
    """Return the path to a labelled ``[before | after]`` mp4 (or ``None``)."""
    if not before or not after:
        return None
    return clips.stitch_video(before, after, out_path)
