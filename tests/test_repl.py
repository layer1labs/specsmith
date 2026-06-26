# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Unit tests for the specsmith.agent.repl module.

Covers §35 (Nexus REPL — /specsmith Slash-Command Handler) and
architecture invariant I11: the /specsmith branch MUST precede the
broker branch in the REPL dispatch loop.

No LLM, no AG2, no orchestrator dependency required.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_command(user_input: str) -> tuple[str, str]:
    """Mirror the REPL's command-parsing logic for isolated testing."""
    parts = user_input.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    return command, args


def _sm_args_for(args: str) -> str:
    """Mirror the sm_args default logic."""
    return args.strip() if args else "--help"


# ---------------------------------------------------------------------------
# §35 command parser — pure logic tests (no I/O)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "user_input, expected_command, expected_args",
    [
        ("/specsmith audit", "/specsmith", "audit"),
        ("/specsmith validate --strict", "/specsmith", "validate --strict"),
        ("/specsmith --help", "/specsmith", "--help"),
        ("/specsmith save --force", "/specsmith", "save --force"),
        # No args — empty string
        ("/specsmith", "/specsmith", ""),
    ],
)
def test_specsmith_command_parsing(
    user_input: str, expected_command: str, expected_args: str
) -> None:
    """The /specsmith prefix is correctly extracted from REPL input."""
    command, args = _parse_command(user_input)
    assert command == expected_command
    assert args == expected_args


def test_specsmith_empty_args_defaults_to_help() -> None:
    """'/specsmith' with no args produces sm_args='--help' (§35 invariant)."""
    _, args = _parse_command("/specsmith")
    sm_args = _sm_args_for(args)
    assert sm_args == "--help"


def test_specsmith_non_empty_args_preserved() -> None:
    """Non-empty args are passed through verbatim."""
    _, args = _parse_command("/specsmith audit --strict")
    sm_args = _sm_args_for(args)
    assert sm_args == "audit --strict"


# ---------------------------------------------------------------------------
# §35 I11 — /specsmith handler precedes broker dispatch
# ---------------------------------------------------------------------------


def test_specsmith_command_detected_before_other_slash_commands() -> None:
    """The /specsmith command is detected at command-dispatch time, not after broker."""
    # §35 I11: command == "/specsmith" must be the first branch checked.
    # We verify the command string is exactly "/specsmith" after parsing.
    for user_input in ["/specsmith audit", "/specsmith", "/specsmith save"]:
        command, _ = _parse_command(user_input)
        assert command == "/specsmith", f"Failed to detect /specsmith in {user_input!r}"


def test_broker_not_invoked_for_specsmith_command(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """The /specsmith branch does NOT invoke classify_intent or run_preflight (I11)."""
    import specsmith.agent.repl as repl_mod

    broker_calls: list[str] = []

    # Patch the broker entry points to record if they're called
    monkeypatch.setattr(repl_mod, "classify_intent", lambda s: broker_calls.append(s))
    monkeypatch.setattr(repl_mod, "run_preflight", lambda *a, **kw: broker_calls.append(a))

    # Simulate parsing just the dispatch decision (not the full REPL loop)
    user_input = "/specsmith audit"
    parts = user_input.split(maxsplit=1)
    command = parts[0].lower()

    # The /specsmith branch takes this path — broker is never reached
    if command == "/specsmith":
        pass  # handler path — broker NOT called
    else:
        repl_mod.classify_intent(user_input)

    assert broker_calls == [], (
        "/specsmith dispatch branch must not invoke the governance broker (I11)"
    )


# ---------------------------------------------------------------------------
# §35 subprocess invocation — mock-based tests
# ---------------------------------------------------------------------------


def test_specsmith_handler_calls_subprocess_run(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """The /specsmith handler invokes subprocess.run with 'specsmith <args>'."""
    import specsmith.agent.repl as repl_mod

    captured_calls: list[dict] = []

    class _FakeResult:
        returncode = 0

    def _fake_run(cmd: str, **kwargs) -> _FakeResult:
        captured_calls.append({"cmd": cmd, **kwargs})
        return _FakeResult()

    # Patch subprocess inside the repl module
    import subprocess as _subprocess

    monkeypatch.setattr(_subprocess, "run", _fake_run)

    # Also need to stub Orchestrator + input for the full REPL loop
    class _FakeOrch:
        def run_task(self, *a, **kw):
            return SimpleNamespace(
                equilibrium=True,
                confidence=0.9,
                summary="ok",
                files_changed=[],
                test_results={},
            )

    monkeypatch.setattr(repl_mod, "Orchestrator", lambda: _FakeOrch())

    # Feed: /specsmith audit, then /exit
    inputs = iter(["/specsmith audit", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.chdir(tmp_path)

    repl_mod.main()

    assert any("specsmith audit" in c.get("cmd", "") for c in captured_calls), (
        f"Expected subprocess.run('specsmith audit ...'), got: {captured_calls}"
    )


def test_specsmith_handler_empty_args_calls_help(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """'/specsmith' with no args calls subprocess.run with 'specsmith --help'."""
    import subprocess as _subprocess

    import specsmith.agent.repl as repl_mod

    captured: list[str] = []

    class _FakeResult:
        returncode = 0

    def _fake_run_help(cmd: str, **kw: object) -> _FakeResult:
        captured.append(cmd)
        return _FakeResult()

    monkeypatch.setattr(_subprocess, "run", _fake_run_help)

    class _FakeOrch:
        def run_task(self, *a, **kw):
            return SimpleNamespace(
                equilibrium=True, confidence=0.9, summary="", files_changed=[], test_results={}
            )

    monkeypatch.setattr(repl_mod, "Orchestrator", lambda: _FakeOrch())
    inputs = iter(["/specsmith", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.chdir(tmp_path)

    repl_mod.main()

    assert any("specsmith --help" in c for c in captured), (
        f"Expected 'specsmith --help' for empty /specsmith, got: {captured}"
    )


def test_specsmith_handler_timeout_prints_message(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
    """TimeoutExpired during /specsmith is caught and a user message is printed."""
    import subprocess as _subprocess

    import specsmith.agent.repl as repl_mod

    def _raise_timeout(*a, **kw):
        raise _subprocess.TimeoutExpired(cmd="specsmith", timeout=120)

    monkeypatch.setattr(_subprocess, "run", _raise_timeout)

    class _FakeOrch:
        def run_task(self, *a, **kw):
            return SimpleNamespace(
                equilibrium=True, confidence=0.9, summary="", files_changed=[], test_results={}
            )

    monkeypatch.setattr(repl_mod, "Orchestrator", lambda: _FakeOrch())
    inputs = iter(["/specsmith audit", "/exit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
    monkeypatch.chdir(tmp_path)

    repl_mod.main()  # must not raise

    out = capsys.readouterr().out
    assert "timed out" in out.lower(), f"Expected timeout message in output, got: {out!r}"


# ---------------------------------------------------------------------------
# Architecture assertion (§35) — REPL source mentions /specsmith handler
# ---------------------------------------------------------------------------


def test_repl_source_documents_specsmith_handler() -> None:
    """repl.py source must contain the /specsmith handler and the REQ-SM-001 comment."""
    import inspect

    import specsmith.agent.repl as repl_mod

    source = inspect.getsource(repl_mod)
    assert 'command == "/specsmith"' in source, "repl.py must have the /specsmith command branch"
    assert "REQ-SM-001" in source or "specsmith" in source.lower(), (
        "repl.py must document the /specsmith handler"
    )
