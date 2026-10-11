"""Enforce the layered dependency direction (architecture as a test).

Dependencies may only point inward:

    surfaces -> core -> integrations -> domain

``domain`` is the pure center (stdlib only). ``integrations`` are the outbound
adapters (openjiuwen/agents, browser, forge, appserver, storage, reporting).
``core`` is the application/business logic (workflow, strategies, jobs, service).
``surfaces`` are the inbound adapters (gui1, gui2, cli, mcp).
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "taketwo"

# For each layer, the layers it must NOT import (dependencies point inward only).
FORBIDDEN: dict[str, set[str]] = {
    "domain": {"integrations", "core", "surfaces"},
    "integrations": {"core", "surfaces"},
    "core": {"surfaces"},
}


def _layer_of(path: Path) -> str | None:
    rel = path.relative_to(PKG)
    if len(rel.parts) == 1:
        return None  # top-level modules (config, bootstrap, readiness) are leaves
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
    from taketwo.core.stages import STAGES

    stages_dir = PKG / "core" / "stages"
    found = {p.name for p in stages_dir.iterdir() if p.is_dir() and (p / "__init__.py").exists()}
    assert found == set(STAGES), f"STAGES {STAGES} does not match packages {sorted(found)}"


def test_openjiuwen_confined_to_agents_integration():
    """openjiuwen may only be imported from ``integrations/agents``."""
    violations: list[str] = []
    for path in PKG.rglob("*.py"):
        rel = path.relative_to(PKG)
        if rel.parts[:2] == ("integrations", "agents"):
            continue
        for name in _imports(path):
            if name.split(".")[0] == "openjiuwen":
                violations.append(f"{rel} imports {name}")
    assert not violations, "openjiuwen must stay inside integrations/agents:\n" + "\n".join(violations)


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
