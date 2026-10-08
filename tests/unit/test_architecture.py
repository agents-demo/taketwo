"""Enforce the layered dependency direction (architecture as a test).

Dependencies may only point inward:
    interfaces -> pipeline -> backend -> domain
with ``media`` / ``browser`` / ``forge`` (capability adapters) and ``storage`` /
``reporting`` / ``config`` as neutral leaves.
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "taketwo"

# Layers that are single modules at the package root (not sub-packages).
TOP_LAYERS = {"reporting"}

# For each layer, the app layers it must NOT import.
#   pipeline  = the staged workflow (understand -> reproduce -> repair -> prove -> deliver)
#   media / browser / forge = shared capability adapters (video, Playwright, git/GitHub)
FORBIDDEN: dict[str, set[str]] = {
    "domain": {"pipeline", "media", "browser", "forge", "backend", "storage", "reporting", "interfaces"},
    "backend": {"domain", "pipeline", "media", "browser", "forge", "reporting", "interfaces"},
    "storage": {"domain", "pipeline", "media", "browser", "forge", "backend", "reporting", "interfaces"},
    "reporting": {"pipeline", "media", "browser", "forge", "backend", "interfaces"},
    "media": {"domain", "pipeline", "backend", "reporting", "interfaces"},
    "browser": {"domain", "pipeline", "backend", "reporting", "interfaces"},
    "forge": {"domain", "pipeline", "backend", "reporting", "interfaces"},
    "pipeline": {"interfaces"},
}


def _layer_of(path: Path) -> str | None:
    rel = path.relative_to(PKG)
    if len(rel.parts) == 1:
        return rel.stem if rel.stem in TOP_LAYERS else None
    return rel.parts[0]


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module)
            found.update(f"{node.module}.{alias.name}" for alias in node.names)
    return found


def test_layer_dependencies_point_inward():
    violations: list[str] = []
    for path in PKG.rglob("*.py"):
        layer = _layer_of(path)
        forbidden = FORBIDDEN.get(layer or "")
        if not forbidden:
            continue
        for name in _imports(path):
            for other in forbidden:
                if name == f"taketwo.{other}" or name.startswith(f"taketwo.{other}."):
                    violations.append(f"{path.relative_to(PKG)}: {layer} -> {other} ({name})")
    assert not violations, "layer violations:\n" + "\n".join(violations)


def test_stages_constant_matches_stage_packages():
    from taketwo.pipeline.stages import STAGES

    stages_dir = PKG / "pipeline" / "stages"
    found = {p.name for p in stages_dir.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    assert found == set(STAGES), f"STAGES {STAGES} does not match packages {sorted(found)}"


def test_openjiuwen_confined_to_backend():
    violations: list[str] = []
    for path in PKG.rglob("*.py"):
        if "backend" in path.relative_to(PKG).parts:
            continue
        for name in _imports(path):
            if name.split(".")[0] == "openjiuwen":
                violations.append(f"{path.relative_to(PKG)} imports {name}")
    assert not violations, "openjiuwen must stay inside backend:\n" + "\n".join(violations)


def test_domain_is_pure():
    third_party = (
        "numpy",
        "PIL",
        "imageio",
        "openjiuwen",
        "streamlit",
        "fastapi",
        "mcp",
        "playwright",
        "github",
        "pytesseract",
        "cv2",
        "dotenv",
    )
    violations: list[str] = []
    for path in (PKG / "domain").rglob("*.py"):
        for name in _imports(path):
            root = name.split(".")[0]
            if root in third_party:
                violations.append(f"{path.name}: imports {name}")
    assert not violations, "domain must stay dependency-free:\n" + "\n".join(violations)
