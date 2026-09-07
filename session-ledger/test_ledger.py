"""Tests for the session-ledger transcript parsing and discovery.

Run: cd session-ledger && uv run --with pytest pytest -q
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger  # noqa: E402

CODEX_ID = "01a079ba-21df-7d43-8669-01a775a9b53e"


def _rollout(tmp_path, records, name=None, sid=CODEX_ID):
    day = tmp_path / "sessions" / "2026" / "09" / "06"
    day.mkdir(parents=True, exist_ok=True)
    path = day / (name or "rollout-2026-09-06T19-37-16-%s.jsonl" % sid)
    path.write_text("\n".join(json.dumps(r) for r in records) + "\n")
    return path


def _meta(**over):
    payload = {"id": CODEX_ID, "cwd": "/Users/eric/proj", "originator": "codex-tui",
               "source": "cli", "thread_source": "user"}
    payload.update(over)
    return {"timestamp": "2026-09-07T02:37:16.889Z", "type": "session_meta", "payload": payload}


def _user(text):
    return {"timestamp": "2026-09-07T02:37:20.366Z", "type": "response_item",
            "payload": {"type": "message", "role": "user",
                        "content": [{"type": "input_text", "text": text}]}}


def _assistant(text):
    return {"timestamp": "2026-09-07T02:41:00.000Z", "type": "response_item",
            "payload": {"type": "message", "role": "assistant",
                        "content": [{"type": "output_text", "text": text}]}}


def test_codex_rollout_parses_prompts_reply_cwd_and_id(tmp_path):
    path = _rollout(tmp_path, [
        _meta(),
        _user("<environment_context>\n<cwd>/x</cwd>\n</environment_context>"),
        _user("<recommended_plugins>\n- Airtable\n</recommended_plugins>"),
        _user("Fix the flaky broker test"),
        _assistant("Looking now."),
        _user('<image name=[Image #1] path="/tmp/a.png"> what is wrong here'),
        _assistant("The lock was missing; added it."),
        {"timestamp": "2026-09-07T02:42:00.000Z", "type": "event_msg",
         "payload": {"type": "task_complete", "last_agent_message": "Done: lock added, tests pass."}},
    ])
    info = ledger.parse_session(str(path))
    assert info["tool"] == "codex"
    assert info["session_id"] == CODEX_ID
    assert info["cwd"] == "/Users/eric/proj"
    assert info["prompts"] == ["Fix the flaky broker test", "what is wrong here"]
    assert info["last_assistant"] == "Done: lock added, tests pass."
    assert info["title"] == "Fix the flaky broker test"
    assert info["first_ts"].startswith("2026-09-07T02:37:16")
    assert info["excluded"] is None
    assert ledger.resume_command(info) == "codex resume " + CODEX_ID


@pytest.mark.parametrize("meta", [
    _meta(source="exec", originator="codex_exec"),
    _meta(source={"subagent": "review"}),
    _meta(thread_source={"subagent": {"thread_spawn": {"depth": 1}}}),
])
def test_scripted_and_subagent_codex_runs_are_excluded(tmp_path, meta):
    path = _rollout(tmp_path, [meta, _user("Review this branch"), _assistant("HIGH | x")])
    info = ledger.parse_session(str(path))
    assert info["excluded"]


def test_claude_transcript_still_parses(tmp_path):
    path = tmp_path / "abc.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in [
        {"type": "user", "sessionId": "abc", "cwd": "/Users/eric/repo", "timestamp": "2026-09-01T10:00:00Z",
         "message": {"role": "user", "content": "add a test"}},
        {"type": "assistant", "timestamp": "2026-09-01T10:01:00Z",
         "message": {"role": "assistant", "content": [{"type": "text", "text": "Added."}]}},
    ]) + "\n")
    info = ledger.parse_session(str(path))
    assert info["tool"] == "claude"
    assert info["prompts"] == ["add a test"]
    assert ledger.resume_command(info) == "claude --resume abc"


def test_find_sessions_covers_both_layouts(tmp_path):
    projects = tmp_path / "projects" / "-Users-eric-repo"
    projects.mkdir(parents=True)
    (projects / "claude-1.jsonl").write_text("{}\n")
    (projects / "subagents").mkdir()
    (projects / "subagents" / "sub.jsonl").write_text("{}\n")
    _rollout(tmp_path, [_meta()])
    cfg = {"PROJECTS_DIR": str(tmp_path / "projects"), "CODEX_SESSIONS_DIR": str(tmp_path / "sessions")}
    found = dict(ledger.find_sessions(cfg))
    assert set(found) == {"claude-1", CODEX_ID}
    assert found[CODEX_ID].endswith("rollout-2026-09-06T19-37-16-%s.jsonl" % CODEX_ID)


def test_codex_dir_defaults_and_none(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger, "ENV_FILE", str(tmp_path / "nope.env"))
    monkeypatch.setenv("LEDGER_FILE", str(tmp_path / "l.md"))
    monkeypatch.delenv("CODEX_SESSIONS_DIR", raising=False)
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codexhome"))
    assert ledger.load_config()["CODEX_SESSIONS_DIR"] == str(tmp_path / "codexhome" / "sessions")
    monkeypatch.setenv("CODEX_SESSIONS_DIR", "none")
    assert ledger.load_config()["CODEX_SESSIONS_DIR"] == ""


def test_codex_distill_uses_an_ephemeral_read_only_exec(monkeypatch, tmp_path):
    calls = {}

    def fake_run(argv, **kwargs):
        calls["argv"] = argv
        out_path = argv[argv.index("-o") + 1]
        with open(out_path, "w") as fh:
            fh.write("- Outcome: it worked\n")

        class Proc:
            returncode = 0
            stdout = "codex progress noise"
            stderr = ""
        return Proc()

    monkeypatch.setattr(ledger.subprocess, "run", fake_run)
    monkeypatch.setattr(ledger, "RUNS_DIR", str(tmp_path))
    cfg = {"DISTILL_TOOL": "codex", "CODEX_MODEL": "gpt-5.5", "CODEX_REASONING_EFFORT": "low"}
    out, err = ledger.run_claude("prompt", cfg)
    assert err is None and out == "- Outcome: it worked"
    argv = calls["argv"]
    assert argv[:2] == ["codex", "exec"]
    assert "--ephemeral" in argv and "read-only" in argv and "-m" in argv
    assert not [f for f in os.listdir(str(tmp_path)) if f.startswith(".codex-distill.")]


def test_codex_noise_prompts_are_not_prompts():
    for noise in ("exit", "/exit", "Q", "# AGENTS.md instructions for /Users/x\n<INSTRUCTIONS>",
                  "# Files mentioned by the user:\n## codex-clipboard-1.png"):
        assert ledger._codex_user_prompt(noise) is None
    assert ledger._codex_user_prompt("exit the loop early when the queue is empty") == (
        "exit the loop early when the queue is empty")


def test_never_seen_old_sessions_are_stale_unless_forced():
    import datetime as dt
    old = (dt.date.today() - dt.timedelta(days=45)).isoformat() + "T10:00:00Z"
    fresh = (dt.date.today() - dt.timedelta(days=2)).isoformat() + "T10:00:00Z"
    cfg = {"BACKFILL_MAX_AGE_DAYS": 30}
    assert ledger.session_is_stale({"last_ts": old}, cfg)
    assert not ledger.session_is_stale({"last_ts": fresh}, cfg)
    assert not ledger.session_is_stale({"last_ts": old}, {"BACKFILL_MAX_AGE_DAYS": 0})


def test_dream_accepts_the_legacy_header():
    assert "# Claude Code session ledger" in ledger.LEGACY_LEDGER_HEADERS
    assert ledger.LEDGER_HEADER == "# Coding agent session ledger"
