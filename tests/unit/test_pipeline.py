"""Offline tests for the pure domain and the deterministic pipeline (no model calls)."""

from __future__ import annotations

from taketwo import pipeline
from taketwo.bootstrap import run
from taketwo.domain import evaluate
from taketwo.domain import repro as repro_mod
from taketwo.domain import timeline as timeline_mod
from taketwo.domain import verify as verify_mod
from taketwo.domain.submission import job_id
from taketwo.pipeline import agent_reply


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
    from taketwo.pipeline.stages.understand import understand

    async def fake_ask(agent, prompt):  # noqa: ARG001
        return 'prose... {"steps": [{"action": "click", "target": "#go", "timestamp": 1.0}], "failure": {}} ...'

    monkeypatch.setattr("taketwo.pipeline.agent_reply.ask", fake_ask)

    video = tmp_path / "bug.mov"
    video.write_bytes(b"not a real recording")
    timeline = run(understand(str(video), agent=object()))

    assert timeline["steps"][0]["target"] == "#go"


def test_forge_verify_signature():
    import hashlib
    import hmac

    from taketwo.pipeline.forge import verify_signature

    body = b'{"action": "opened"}'
    secret = "s3cret"
    good = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(secret, body, good) is True
    assert verify_signature(secret, body, "sha256=deadbeef") is False
    assert verify_signature(secret, body, "") is False
    assert verify_signature("", body, "") is True  # no secret => dev mode


def test_runner_command_local_and_docker(monkeypatch):
    import sys

    from taketwo.interfaces.runner import Runner

    runner = Runner(max_workers=1)
    job = {
        "video_path": "v.mov",
        "progress_path": "p.json",
        "repo": "o/n",
        "base_branch": "main",
        "app_url": "",
        "agentic": False,
    }

    monkeypatch.delenv("SANDBOX_IMAGE", raising=False)
    local = runner._command(job)
    assert local[0] == sys.executable and local[1:3] == ["-m", "taketwo.interfaces.worker"]

    monkeypatch.setenv("SANDBOX_IMAGE", "taketwo:latest")
    docker = runner._command(job)
    assert docker[0] == "docker" and "taketwo:latest" in docker


def test_forge_run_tests_reports_pass_and_fail(tmp_path):
    import sys

    from taketwo.pipeline.forge import repo as forge_repo

    ok = forge_repo.run_tests(tmp_path, f'"{sys.executable}" -c "import sys; sys.exit(0)"')
    bad = forge_repo.run_tests(tmp_path, f'"{sys.executable}" -c "import sys; sys.exit(1)"')
    skipped = forge_repo.run_tests(tmp_path, "")

    assert ok["ran"] and ok["passed"]
    assert bad["ran"] and not bad["passed"]
    assert skipped["ran"] is False


def test_forge_publish_branch_commits_and_dry_runs(tmp_path, monkeypatch):
    import subprocess

    from taketwo.pipeline.forge import repo as forge_repo

    monkeypatch.setattr("taketwo.pipeline.forge.auth.token", lambda: "")  # force dry-run, never push in tests

    work = tmp_path / "r"
    work.mkdir()

    def git(*args):
        subprocess.run(["git", *args], cwd=work, capture_output=True, text=True, check=True)

    git("init")
    (work / "f.txt").write_text("old\n", encoding="utf-8")
    git("add", "-A")
    git("commit", "-m", "init")

    diff = "--- a/f.txt\n+++ b/f.txt\n@@ -1 +1 @@\n-old\n+new\n"
    out = forge_repo.publish_branch(work, branch="taketwo/fix", diff=diff, message="fix: scenario", repo="")

    assert out["branch"] == "taketwo/fix"
    assert out["commit"]
    assert out["pushed"] is False and out["dry_run"] is True
    assert (work / "f.txt").read_text(encoding="utf-8") == "new\n"
    branch = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=work, capture_output=True, text=True)
    assert branch.stdout.strip() == "taketwo/fix"


def test_deterministic_pipeline_runs_offline(tmp_path):
    video = tmp_path / "bug.mov"
    video.write_bytes(b"not a real recording")
    strategy = pipeline.resolve()
    outcome = run(strategy.analyze(pipeline.Params(video_path=str(video))))

    assert outcome["job"]
    assert outcome["reproduction"]["verdict"] in repro_mod.VERDICTS
    assert "result" in outcome and "fix" in outcome and "proof" in outcome
