# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Long-lived agent runtime driving ``specsmith run`` / ``specsmith serve``.

The runner is the bridge between the Click entry points in :mod:`cli` and
the underlying machinery in :mod:`agent.chat_runner`,
:mod:`agent.orchestrator`, :mod:`agent.profiles`, and
:mod:`agent.fallback`.

Why this module exists
----------------------
The VS Code extension's :class:`SpecsmithBridge` (``bridge.ts``) treats a
JSONL ``{type: "ready", ...}`` line as the official handshake — without
that line within 20 s the bridge declares the binary unresponsive and
surfaces *"specsmith not responding"* to the user. Earlier refactors
removed the file that emitted the handshake, so every fresh ``specsmith
run --json-events`` import-errored before producing a single byte. This
module restores the emitter and centralizes the protocol (REQ-145).
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from specsmith.agent.core import AgentState, ModelTier
from specsmith.agent.events import EventEmitter

# These imports are kept lazy in the public API so that a busted optional
# dependency (e.g. ``ag2``) doesn't keep the bridge from emitting ``ready``.
# The import itself happens on the first call that actually needs the
# orchestrator group chat.
__all__ = ["AgentRunner", "_capabilities"]


# ---------------------------------------------------------------------------
# Capability advertising
# ---------------------------------------------------------------------------


def _capabilities() -> list[str]:
    """Return the list of capabilities surfaced by the ``ready`` frame.

    The VS Code extension uses this to show / hide UI affordances (the
    Endpoints tree only renders when ``"endpoints"`` is reported, etc.).
    Best-effort reflection so an old CLI talking to a new extension still
    works without lying.
    """
    caps: list[str] = ["chat", "run"]
    try:
        import importlib

        for mod, name in (
            ("specsmith.agent.endpoints", "endpoints"),
            ("specsmith.agent.profiles", "profiles"),
            ("specsmith.agent.mcp", "mcp"),
            ("specsmith.agent.rules", "rules"),
            ("specsmith.agent.voice", "voice"),
        ):
            try:
                importlib.import_module(mod)
                caps.append(name)
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        pass
    return caps


# ---------------------------------------------------------------------------
# Slash-command dispatch table
# ---------------------------------------------------------------------------


SLASH_COMMANDS: dict[str, str] = {
    "/plan": "[PLAN] Break the request into a step-by-step plan: ",
    "/architect": "[ARCHITECT] Propose an architecture for: ",
    "/ask": "[ASK] Clarify intent and answer: ",
    "/fix": "[FIX] Modify code to fix the following: ",
    "/code": "[CODE] Write code for: ",
    "/refactor": "[REFACTOR] Refactor without changing behaviour: ",
    "/test": "[TEST] Write or run tests for: ",
    "/review": "[REVIEW] Review for correctness, regressions, and risk: ",
    "/why": "[WHY] Explain the rationale and governance trace: ",
    "/audit": "[AUDIT] Audit the change against requirements: ",
    "/commit": "[COMMIT] Stage changes and write a commit message: ",
    "/pr": "[PR] Prepare a pull request body for: ",
    "/undo": "[UNDO] Revert the last action: ",
    "/context": "[CONTEXT] Surface repo context relevant to: ",
    "/search": "[SEARCH] Search the repo and external docs for: ",
}


def _slash_to_activity(line: str) -> str:
    """Map a user input to a routing-table activity key.

    Plain text → ``"chat"`` (the catch-all). Slash commands map to their
    canonical form. Unknown slash commands also fall through to ``"chat"``.
    """
    text = line.strip()
    if not text or not text.startswith("/"):
        return "chat"
    head = text.split(maxsplit=1)[0].lower()
    if head in SLASH_COMMANDS:
        return head
    return "chat"


# ---------------------------------------------------------------------------
# AgentRunner
# ---------------------------------------------------------------------------


class AgentRunner:
    """Top-level controller used by ``specsmith run`` and ``specsmith serve``.

    Construction must succeed even if optional providers are unavailable
    (Ollama down, no API keys, no ``ag2`` installed) — the bridge depends
    on the ``ready`` frame landing regardless of provider state.

    Public surface (consumed by callers we cannot break)
    ----------------------------------------------------
    * :attr:`_state` — read by :class:`specsmith.serve._AgentThread.status`.
    * :attr:`_hard_stop` — set by :meth:`specsmith.serve._AgentThread.stop_turn`.
    * :meth:`_print_banner` — invoked by ``serve`` once the thread spawns.
    * :meth:`_handle_command` — invoked once per inbox message in ``serve``.
    * :meth:`_emit_event` — monkey-patched by ``serve`` to route events
      through its in-process bus.
    * :meth:`run_task` / :meth:`run_interactive` — used by the ``cli.run``
      command.
    """

    def __init__(
        self,
        *,
        project_dir: str,
        provider_name: str | None = None,
        model: str | None = None,
        tier: ModelTier | str | None = ModelTier.BALANCED,
        stream: bool = True,
        optimize: bool = False,
        json_events: bool = False,
        endpoint_id: str | None = None,
        profile_id: str | None = None,
        emitter: EventEmitter | None = None,
    ) -> None:
        self.project_dir = str(Path(project_dir).resolve())
        self.provider_name = (provider_name or "").strip() or "ollama"
        self.model = (model or "").strip()
        self.tier = ModelTier.parse(tier, default=ModelTier.BALANCED)
        self.stream = bool(stream)
        self.optimize = bool(optimize)
        self.json_events = bool(json_events)
        self.endpoint_id = (endpoint_id or "").strip() or None
        self.profile_id = (profile_id or "").strip() or None

        self._emitter = emitter or EventEmitter(stream=sys.stdout)
        self._state = AgentState(
            provider_name=self.provider_name,
            model_name=self.model,
            profile_id=self.profile_id or "",
        )
        self._hard_stop = False
        self._started_at = time.time()
        self._history: list[dict[str, Any]] = []
        self._block_counter = 0

        # Best-effort routing-table load. A missing or invalid file falls
        # back to single-profile behaviour so existing setups keep working.
        self._routing = self._load_routing()

        # Consumers may swap this with a closure that routes through their
        # own bus (see ``serve._AgentThread``). The default writes JSONL.
        self._emit_event: Callable[..., None] = self._default_emit_event

    # ── Public lifecycle ───────────────────────────────────────────────

    def _print_banner(self) -> None:
        """Emit the ``ready`` handshake (or print a plain banner).

        Called exactly once at process start. The bridge waits up to 20 s
        for this frame; when ``json_events`` is False we still emit a
        terminal-friendly banner so interactive ``specsmith run`` users
        see the same boot text they used to.
        """
        version = self._package_version()
        if self.json_events:
            self._emitter.ready(
                agent="nexus",
                version=version,
                project_dir=self.project_dir,
                provider=self.provider_name,
                model=self.model,
                profile_id=self.profile_id or "",
                capabilities=_capabilities(),
                endpoint_id=self.endpoint_id or "",
            )
        else:
            print(
                f"Nexus {version} — Local-first Agentic Development Environment "
                f"(Specsmith-governed)\n"
                f"  project: {self.project_dir}\n"
                f"  provider: {self.provider_name}\n"
                f"  model: {self.model or '(default)'}\n"
                f"  profile: {self.profile_id or '(default)'}\n"
                "Type plain English, or use slash commands "
                "(/plan, /ask, /fix, /test, /commit, /pr, /why, /exit).",
                flush=True,
            )

    def run_interactive(self) -> None:
        """Read stdin lines and dispatch each to :meth:`_handle_command`."""
        self._print_banner()
        try:
            for raw in sys.stdin:
                line = raw.rstrip("\n")
                if not line.strip():
                    continue
                if line.strip().lower() in {"/exit", "/quit"}:
                    break
                self._handle_command(line)
                if self.json_events:
                    self._emit_event(type="turn_done")
                if self._hard_stop:
                    self._hard_stop = False
        except (KeyboardInterrupt, EOFError):
            pass

    def run_task(self, task: str):
        """Execute a single task non-interactively and return the result.

        Mirrors the legacy ``cli.run --task`` shape — returns whatever the
        chat runner produced (plus a synthetic ``TaskResult`` when the
        orchestrator path was used).
        """
        return self._handle_command(task)

    # ── Per-turn dispatch ──────────────────────────────────────────────

    def _handle_command(self, text: str) -> Any:
        """Route a single user line through the right pipeline.

        Order of resolution:
          1. Slash command shortcuts (``/clear``, ``/model``, ``/provider``,
             ``/agent``, ``/exit``).
          2. Activity → profile routing (PR-G). Falls back to the
             single-profile config if no routing table is present.
          3. ``chat_runner.run_chat`` for the actual LLM turn (with
             fallback chain wrapping the call).
        """
        text = (text or "").strip()
        if not text:
            return None

        # Lightweight in-process commands the runner handles itself.
        if text.startswith("/clear"):
            self._history = []
            self._emit_event(type="system", message="History cleared.")
            return None
        if text.startswith("/model "):
            new_model = text.split(maxsplit=1)[1].strip()
            self.model = new_model
            self._state.model_name = new_model
            self._emit_event(type="system", message=f"model = {new_model}")
            return None
        if text.startswith("/provider "):
            new_provider = text.split(maxsplit=1)[1].strip()
            self.provider_name = new_provider
            self._state.provider_name = new_provider
            self._emit_event(type="system", message=f"provider = {new_provider}")
            return None
        if text.startswith("/agent "):
            new_profile = text.split(maxsplit=1)[1].strip()
            self.profile_id = new_profile or None
            self._state.profile_id = new_profile
            self._emit_event(type="system", message=f"profile = {new_profile or '(default)'}")
            return None
        if text.startswith("/endpoint "):
            new_endpoint = text.split(maxsplit=1)[1].strip()
            self.endpoint_id = new_endpoint or None
            self._emit_event(
                type="system", message=f"endpoint = {new_endpoint or '(auto)'}"
            )
            return None

        activity = _slash_to_activity(text)
        prefix = SLASH_COMMANDS.get(activity, "")
        utterance = text[len(activity):].strip() if activity != "chat" else text
        full_prompt = (prefix + utterance) if prefix else utterance

        # Resolve the per-turn profile (PR-G). On any error we degrade to
        # the single-provider path so the user still gets a response.
        profile, endpoint_override = self._resolve_for_activity(activity)
        if profile is not None:
            _ident = f"{profile.provider}/{profile.model}"
            self._emit_event(
                type="system",
                message=f"\u21bb routing {activity} \u2192 {profile.id} ({_ident})",
            )

        block_id = self._next_block_id()
        try:
            from specsmith.agent.chat_runner import run_chat

            result = run_chat(
                full_prompt,
                project_dir=Path(self.project_dir),
                profile=(profile.id if profile is not None else "standard"),
                session_id=str(int(self._started_at)),
                emitter=self._emitter,
                msg_block=block_id,
                history=self._history,
                endpoint_id=(endpoint_override or self.endpoint_id),
            )
        except Exception as exc:  # noqa: BLE001
            self._emit_event(
                type="error",
                message=f"chat turn failed: {exc}",
                recoverable=True,
            )
            return None

        # Aggregate metrics into the session state. ``run_chat`` does not
        # currently surface token counts, so we credit zero — the field is
        # still updated so the TokenMeter chip shows turn counts.
        self._state.credit(
            profile_id=(profile.id if profile is not None else self.profile_id or ""),
            tokens_in=0,
            tokens_out=0,
            cost_usd=0.0,
            tool_calls=0,
        )
        self._state.elapsed_minutes = round((time.time() - self._started_at) / 60.0, 2)

        if result is not None:
            self._history.append({"role": "user", "text": utterance})
            self._history.append({"role": "agent", "text": result.summary})
        return result

    # ── Routing helpers ────────────────────────────────────────────────

    def _resolve_for_activity(self, activity: str):
        """Return ``(Profile, endpoint_id_override)`` or ``(None, None)``.

        Respects an explicit per-session profile / endpoint override so
        the ``--agent`` and ``--endpoint`` CLI flags still win.
        """
        if self.profile_id is None and self._routing is None:
            return (None, None)
        try:
            from specsmith.agent.profiles import ProfileStore

            store = ProfileStore.load()
            if self.profile_id:
                profile = store.get(self.profile_id)
                return (profile, profile.endpoint_id or None)
            target_id = store.routes.get(activity) or store.default_profile_id
            if not target_id:
                return (None, None)
            profile = store.get(target_id)
            return (profile, profile.endpoint_id or None)
        except Exception:  # noqa: BLE001
            return (None, None)

    def _load_routing(self) -> Any | None:
        try:
            from specsmith.agent.profiles import ProfileStore

            store = ProfileStore.load()
            return store if store.profiles else None
        except Exception:  # noqa: BLE001
            return None

    # ── Event plumbing ────────────────────────────────────────────────

    def _default_emit_event(self, **kwargs: Any) -> None:
        if not self.json_events:
            # Non-JSON mode: render a compact human line for ``system``
            # events and ignore protocol-only frames.
            if kwargs.get("type") == "system":
                msg = str(kwargs.get("message") or "")
                if msg:
                    print(msg, flush=True)
            return
        self._emitter.emit({k: v for k, v in kwargs.items() if v is not None})

    def _next_block_id(self) -> str:
        self._block_counter += 1
        return f"blk_run_{self._block_counter:04d}"

    @staticmethod
    def _package_version() -> str:
        try:
            from importlib.metadata import version as _v

            return _v("specsmith")
        except Exception:  # noqa: BLE001
            return "0.0.0"
