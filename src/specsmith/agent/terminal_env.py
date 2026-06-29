# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Terminal-environment detection for specsmith (REQ-444).

Lets the interactive REPL (``specsmith run``) and standalone CLI commands
detect when they are running inside Warp and which CLI agent REPL is active.
Detection is based on:
  * ``TERM_PROGRAM=WarpTerminal`` / any ``WARP_*`` env var — Warp host
  * ``SPECSMITH_RUN_ACTIVE=1``     — set by ``specsmith run`` on REPL start
  * ``AIDER_MODEL`` / ``AIDER_CONFIG``  — set by aider at session start
  * ``CLAUDE_CODE_ENTRYPOINT``     — set by Claude Code CLI
  * ``CODEX_CLI_SESSION``          — set by OpenAI Codex CLI
  * ``GEMINI_CLI``                 — set by Gemini CLI
  * ``CURSOR_TRACE_ID``            — set by Cursor CLI

All detection is read-only and purely best-effort.
"""

from __future__ import annotations

import os
import sys
from dataclasses import asdict, dataclass

# ---------------------------------------------------------------------------
# Known CLI-agent env-var signals.
# Keys are canonical agent IDs; values are lists of env vars that
# confirm the agent is (or recently was) active in this shell session.
# Warp natively supports: claude, codex, gemini, cursor.
# specsmith and aider are NOT natively supported — users add them via the
# custom toolbar regex in Warp Settings → Agents → Third party CLI agents.
# ---------------------------------------------------------------------------
_AGENT_ENV_SIGNALS: dict[str, list[str]] = {
    "specsmith": ["SPECSMITH_RUN_ACTIVE"],
    "aider": ["AIDER_MODEL", "AIDER_CONFIG", "AIDER_CHAT_LANGUAGE"],
    "claude": ["CLAUDE_CODE_ENTRYPOINT", "ANTHROPIC_CLAUDE_CODE_SESSION"],
    "codex": ["CODEX_CLI_SESSION", "OPENAI_CODEX_CLI"],
    "gemini": ["GEMINI_CLI", "GEMINI_CLI_SESSION"],
    "cursor": ["CURSOR_TRACE_ID", "CURSOR_SESSION_ID"],
    "copilot": ["GITHUB_COPILOT_CLI", "GH_COPILOT_SESSION"],
    "windsurf": ["WINDSURF_SESSION", "CODEIUM_SESSION"],
}


@dataclass(frozen=True)
class TerminalInfo:
    """Information about the host terminal and active CLI agent REPL."""

    is_warp: bool
    program: str
    version: str
    #: Canonical agent ID when a known CLI agent REPL is detected, else "".
    #: Examples: ``"specsmith"``, ``"aider"``, ``"claude"``, ``"codex"``.
    active_agent: str = ""

    def as_dict(self) -> dict[str, object]:
        """Return a flat dict suitable for the ``ready`` event frame."""
        return asdict(self)


def detect_terminal(env: dict[str, str] | None = None) -> TerminalInfo:
    """Detect the host terminal and active CLI agent from environment variables.

    Warp sets ``TERM_PROGRAM=WarpTerminal`` (and ``TERM_PROGRAM_VERSION``).
    As a fallback we also treat the presence of any ``WARP_*`` variable as a
    Warp signal.  Pass *env* to override ``os.environ`` (used by tests).
    """
    source = os.environ if env is None else env
    program = (source.get("TERM_PROGRAM") or "").strip()
    version = (source.get("TERM_PROGRAM_VERSION") or "").strip()
    is_warp = program == "WarpTerminal" or any(k.startswith("WARP_") for k in source)
    if is_warp and not program:
        program = "WarpTerminal"

    # Detect the active CLI-agent REPL by checking known signal env vars.
    # First match wins; order matters (specsmith checked before generic agents).
    active_agent = ""
    for agent, signals in _AGENT_ENV_SIGNALS.items():
        if any(source.get(sig) for sig in signals):
            active_agent = agent
            break

    return TerminalInfo(
        is_warp=is_warp,
        program=program,
        version=version,
        active_agent=active_agent,
    )


# ---------------------------------------------------------------------------
# OSC 9 terminal notification (Warp, iTerm2, Windows Terminal)
# ---------------------------------------------------------------------------


def emit_warp_notification(message: str, *, stream=None) -> None:
    """Emit an OSC 9 terminal notification that Warp (and compatible terminals)
    surfaces as a desktop notification.

    The escape sequence ``ESC ] 9 ; <message> BEL`` is the standard notification
    protocol supported by Warp, iTerm2, and Windows Terminal.  When *stream* is
    ``None`` (the default), the function skips silently if stdout is not a TTY
    (e.g. captured in tests or CI).  Pass an explicit *stream* to override.

    This is always safe to call — it is a no-op outside Warp and raises no
    exceptions.
    """
    out = stream if stream is not None else sys.stdout
    try:
        # When using the default stdout and it's not a tty, skip silently
        # to avoid polluting captured output in tests or piped commands.
        if stream is None and hasattr(out, "isatty") and not out.isatty():
            return
        out.write(f"\033]9;{message}\007")
        if hasattr(out, "flush"):
            out.flush()
    except Exception:  # noqa: BLE001  # intentional: notification is best-effort
        pass
