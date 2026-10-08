"""Pure acceptance for a fix: repro red -> green, tests pass.

No I/O — callers pass the observed run results in.
"""

from __future__ import annotations

from typing import Any


def verify(reproduction: dict[str, Any], fix: dict[str, Any], run: dict[str, Any] | None = None) -> dict[str, Any]:
    """Combine the reproduction verdict, the patched run, and the test result.

    ``run`` is what the prove stage observed on the patched branch:
    ``{"reproduced": bool, "tests_pass": bool}``.
    """
    run = run or {}
    checks = {
        "reproduced_before": reproduction.get("verdict") == "reproduced",
        "fixed_after": run.get("reproduced") is False,
        "tests_pass": bool(run.get("tests_pass", False)),
    }
    reasons: list[str] = []
    if not checks["reproduced_before"]:
        reasons.append("the bug was not reproduced before the fix")
    if not checks["fixed_after"]:
        reasons.append("the scenario still fails after the fix")
    if not checks["tests_pass"]:
        reasons.append("the test suite did not pass")
    ok = all(checks.values()) and not validate_fix(fix)
    return {"ok": ok, "checks": checks, "reasons": reasons}


def validate_fix(fix: dict[str, Any]) -> list[str]:
    from taketwo.domain import fix as fix_mod

    return fix_mod.validate(fix)
