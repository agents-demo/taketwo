"""Offline tests for the pure domain and the deterministic pipeline (no model calls)."""

from __future__ import annotations

from taketwo.analysis import agent_reply, pipeline
from taketwo.bootstrap import run
from taketwo.domain import evaluate
from taketwo.domain import repro as repro_mod
from taketwo.domain import timeline as timeline_mod
from taketwo.domain import verify as verify_mod
from taketwo.domain.submission import job_id


def test_submission_job_id_prefers_repo():
    assert job_id({"repo": "openJiuwen/agent-core", "base_branch": "main"}) == "openJiuwen__agent-core@main"
    assert job_id({"video_path": "runtime/data/bug.mov"}) == "bug"


def test_timeline_normalize_coerces_actions():
    tl = timeline_mod.normalize({"steps": [{"action": "CLICK", "target": "#go"}, {"action": "jump"}]})
    assert tl["steps"][0]["action"] == "click"
    assert tl["steps"][1]["action"] == "unknown"
    assert "1." in timeline_mod.describe(tl)


def test_verify_requires_red_then_green():
    repro = repro_mod.normalize(
        {"verdict": "reproduced", "evidence": {"summary": "TypeError: x is null"}, "steps": [{"action": "click"}]}
    )
    fix = {"diff": "--- a\n+++ b\n", "test": "def test_x(): ..."}
    bad = verify_mod.verify(repro, fix, {"reproduced": True, "tests_pass": True})
    good = verify_mod.verify(repro, fix, {"reproduced": False, "tests_pass": True})
    assert bad["ok"] is False
    assert good["ok"] is True


def test_evaluate_flags_ungrounded_reproduced():
    repro = repro_mod.normalize({"verdict": "reproduced", "steps": [{"action": "click"}]})
    score = evaluate.score(repro)
    assert score["has_signal"] is False
    assert score["flags"]


def test_agent_reply_extracts_json_from_prose():
    assert agent_reply.extract_json('here you go: {"steps": [{"action": "click"}]} thanks') == {
        "steps": [{"action": "click"}]
    }
    assert agent_reply.extract_json("no json here") == {}
    assert agent_reply.reply_text({"output": "hi"}) == "hi"


def test_understand_uses_the_agent_when_present(tmp_path, monkeypatch):
    from taketwo.analysis.stages.understand import understand

    async def fake_ask(agent, prompt):  # noqa: ARG001
        return 'prose... {"steps": [{"action": "click", "target": "#go", "timestamp": 1.0}], "failure": {}} ...'

    monkeypatch.setattr("taketwo.analysis.agent_reply.ask", fake_ask)

    video = tmp_path / "bug.mov"
    video.write_bytes(b"not a real recording")
    timeline = run(understand(str(video), agent=object()))

    assert timeline["steps"][0]["target"] == "#go"


def test_deterministic_pipeline_runs_offline(tmp_path):
    video = tmp_path / "bug.mov"
    video.write_bytes(b"not a real recording")
    strategy = pipeline.resolve()
    outcome = run(strategy.analyze(pipeline.Params(video_path=str(video))))

    assert outcome["job"]
    assert outcome["reproduction"]["verdict"] in repro_mod.VERDICTS
    assert "result" in outcome and "fix" in outcome and "proof" in outcome
