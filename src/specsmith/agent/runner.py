# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Long-lived agent runtime driving ``specsmith run`` / ``specsmith serve``.

The runner is the bridge between the Click entry points in :mod:`cli` and
the underlying machinery in :mod:`agent.chat_runner`,
:mod:`agent.orchestrator`, :mod:`agent.profiles`, and
:mod:`agent.fallback`.

Why this module exists
----------------------
Kairos (and compatible IDE clients) treats a
JSONL ``{type: "ready", ...}`` line as the official handshake — without
that line within 20 s the client declares the binary unresponsive.
Earlier refactors removed the file that emitted the handshake, so every
fresh ``specsmith run --json-events`` import-errored before producing a
single byte. This module restores the emitter and centralizes the
protocol (REQ-145).
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from specsmith.agent.core import AgentState, ModelTier
from specsmith.agent.events import EventEmitter, PlainTextEmitter

# These imports are kept lazy in the public API so that a busted optional
# dependency (e.g. ``ag2``) doesn't keep the bridge from emitting ``ready``.
# The import itself happens on the first call that actually needs the
# orchestrator group chat.
__all__ = ["AgentRunner", "ProviderStatus", "_capabilities", "check_providers"]


# ---------------------------------------------------------------------------
# Provider health check
# ---------------------------------------------------------------------------


from dataclasses import dataclass


@dataclass
class ProviderStatus:
    """Health snapshot for a single LLM provider."""

    name: str
    available: bool
    model: str = ""  # resolved model name (empty when unavailable)
    note: str = ""  # human-readable reason (error or extra context)
    model_count: int = 0  # number of installed models (Ollama only)

    @property
    def icon(self) -> str:
        return "\u2713" if self.available else "\u2717"


def check_providers() -> list[ProviderStatus]:
    """Probe every supported LLM provider and return a status list.

    Safe to call at any time — never raises, never blocks for more than
    a couple of seconds.  Used by ``_print_banner`` and ``specsmith run
    --check``.
    """
    import importlib
    import os

    from specsmith.agent.chat_runner import (
        _OLLAMA_MODEL_PREFERENCE,
        DEFAULT_OLLAMA_HOST,
        DEFAULT_OLLAMA_MODEL,
        _ollama_alive,
    )

    results: list[ProviderStatus] = []

    # ── Ollama ───────────────────────────────────────────────────────────
    host = os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")
    if _ollama_alive(host):
        try:
            import json
            from urllib.request import urlopen

            with urlopen(f"{host}/api/tags", timeout=2) as resp:  # noqa: S310
                data = json.loads(resp.read())
            installed = [m["name"] for m in data.get("models", []) if m.get("name")]
            installed_set = set(installed)
            model = os.environ.get("SPECSMITH_OLLAMA_MODEL", "").strip()
            source = "env"
            if not model:
                source = "auto"
                for candidate in _OLLAMA_MODEL_PREFERENCE:
                    if candidate in installed_set:
                        model = candidate
                        break
                if not model and installed:
                    model = sorted(installed_set)[0]
                if not model:
                    model = DEFAULT_OLLAMA_MODEL
            note = f"{source}, {len(installed)} installed"
            results.append(
                ProviderStatus(
                    name="ollama",
                    available=True,
                    model=model,
                    note=note,
                    model_count=len(installed),
                ),
            )
        except Exception as exc:  # noqa: BLE001
            results.append(
                ProviderStatus(name="ollama", available=False, note=f"error reading tags: {exc}"),
            )
    else:
        results.append(
            ProviderStatus(
                name="ollama",
                available=False,
                note=f"not running at {host} — start with: ollama serve",
            ),
        )

    # ── Anthropic ────────────────────────────────────────────────────────
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        results.append(
            ProviderStatus(name="anthropic", available=False, note="no ANTHROPIC_API_KEY"),
        )
    elif importlib.util.find_spec("anthropic") is None:
        results.append(
            ProviderStatus(
                name="anthropic",
                available=False,
                note="key set but SDK missing — run: pipx inject specsmith anthropic",
            ),
        )
    else:
        model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
        results.append(
            ProviderStatus(name="anthropic", available=True, model=model, note="key configured"),
        )

    # ── OpenAI ───────────────────────────────────────────────────────────
    key = os.environ.get("OPENAI_API_KEY", "")
    if not key:
        results.append(ProviderStatus(name="openai", available=False, note="no OPENAI_API_KEY"))
    elif importlib.util.find_spec("openai") is None:
        results.append(
            ProviderStatus(
                name="openai",
                available=False,
                note="key set but SDK missing — run: pipx inject specsmith openai",
            ),
        )
    else:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        results.append(
            ProviderStatus(name="openai", available=True, model=model, note="key configured"),
        )

    # ── Gemini ───────────────────────────────────────────────────────────
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        results.append(ProviderStatus(name="gemini", available=False, note="no GOOGLE_API_KEY"))
    elif importlib.util.find_spec("google.genai") is None:
        results.append(
            ProviderStatus(
                name="gemini",
                available=False,
                note="key set but SDK missing — run: pipx inject specsmith google-genai",
            ),
        )
    else:
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        results.append(
            ProviderStatus(name="gemini", available=True, model=model, note="key configured"),
        )

    return results


# ---------------------------------------------------------------------------
# Capability advertising
# ---------------------------------------------------------------------------


def _capabilities() -> list[str]:
    """Return the list of capabilities surfaced by the ``ready`` frame.

    Kairos uses this to show / hide UI affordances (the Endpoints tree
    only renders when ``"endpoints"`` is reported, etc.).
    Best-effort reflection so an old CLI version still works without lying.
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
    "/help": "",
    "/status": "",
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
    "/models": "",  # handled inline — shows the multi-model routing table
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

        # Host-terminal detection (REQ-444): when running inside Warp the
        # banner/ready frame advertises native integration. Read-only.
        # Set SPECSMITH_RUN_ACTIVE so any child specsmith command (audit,
        # preflight, checkpoint, etc.) can detect they are running inside
        # the Grace REPL and report context-aware governance notifications.
        import os as _os_init

        _os_init.environ.setdefault("SPECSMITH_RUN_ACTIVE", "1")

        from specsmith.agent.terminal_env import detect_terminal

        self.terminal = detect_terminal()

        # Use a plain-text emitter in interactive mode so LLM tokens render
        # as readable prose instead of raw JSONL frames on the terminal.
        if emitter is not None:
            self._emitter = emitter
        elif json_events:
            self._emitter = EventEmitter(stream=sys.stdout)
        else:
            self._emitter = PlainTextEmitter(stream=sys.stdout)
        self._state = AgentState(
            provider_name=self.provider_name,
            model_name=self.model,
            profile_id=self.profile_id or "",
        )
        self._hard_stop = False
        self._started_at = time.time()
        self._block_counter = 0

        # Epistemic continuity (REQ-307): seed history from the previous
        # session so the agent never starts blind.  Assembled from:
        #   • session-state.json  (health, phase, compliance snapshot)
        #   • conversation-history.jsonl  (recent prior turns)
        #   • LEDGER.md  (last 30 governance entries)
        #   • ESDB ChronoRecords  (last 5 epistemic facts)
        # Best-effort: failure silently yields an empty seed so the agent
        # still starts even with a corrupt / missing state store.
        self._history: list[dict[str, Any]] = self._build_context_seed()
        self._context_compressed = False
        self._compression_stats: dict[str, Any] = {}

        # Best-effort routing-table load. A missing or invalid file falls
        # back to single-profile behaviour so existing setups keep working.
        self._routing = self._load_routing()

        # Multi-model router (REQ-389). Loaded from .specsmith/local-models.yml
        # if present; falls back to None (single-model mode) on any error.
        self._model_router = self._load_model_router()

        # Consumers may swap this with a closure that routes through their
        # own bus (see ``serve._AgentThread``). The default writes JSONL.
        self._emit_event: Callable[..., None] = self._default_emit_event

    # ── Public lifecycle ───────────────────────────────────────────────

    def _print_banner(self) -> None:
        """Emit the ``ready`` handshake (or print a plain banner.

        Called exactly once at process start. The bridge waits up to 20 s
        for this frame; when ``json_events`` is False we print a human-
        readable provider status table so the user knows exactly what will
        respond to their commands before they type anything.
        """
        version = self._package_version()
        if self.json_events:
            # When a model/provider was explicitly set (e.g. via CLI flag or test),
            # use those.  Only probe check_providers() when no model was pinned.
            if self.model:
                provider_for_ready = self.provider_name
                model_for_ready = self.model
            else:
                statuses = check_providers()
                active = next((s for s in statuses if s.available), None)
                provider_for_ready = active.name if active else self.provider_name
                model_for_ready = active.model if active else ""
            self._emitter.ready(
                agent="grace",
                version=version,
                project_dir=self.project_dir,
                provider=provider_for_ready,
                model=model_for_ready,
                profile_id=self.profile_id or "",
                capabilities=_capabilities(),
                endpoint_id=self.endpoint_id or "",
                terminal=self.terminal.as_dict(),
            )
        else:
            statuses = check_providers()
            active_count = sum(1 for s in statuses if s.available)
            lines = [
                f"Grace {version} — specsmith run",
                f"  project : {self.project_dir}",
                f"  profile : {self.profile_id or '(default)'}",
                "",
                "  LLM providers:",
            ]
            if self.terminal.is_warp:
                ver = f" {self.terminal.version}" if self.terminal.version else ""
                lines.insert(3, f"  terminal: Warp{ver} \u2014 native integration active")
                # Emit OSC 9 desktop notification so Warp surfaces a popup.
                from specsmith.agent.terminal_env import emit_warp_notification

                proj = Path(self.project_dir).name
                emit_warp_notification(f"specsmith run | {proj} | governance active")
            for s in statuses:
                if s.available:
                    lines.append(
                        f"    {s.icon} {s.name:<10} \u2713 ready   model: {s.model}  ({s.note})",
                    )
                else:
                    lines.append(f"    {s.icon} {s.name:<10} \u2717 {s.note}")
            lines.append("")
            if active_count == 0:
                lines.append(
                    "  \u26a0  No provider available \u2014 commands will return no response.",
                )
            else:
                # Show multi-model routing if the router is configured (REQ-389).
                if self._model_router is not None:
                    lines.append(self._model_router.table())
                    lines.append("")
                lines.append(
                    "  Local fallback REPL ready. Type /help for commands or plain English.",
                )
            print("\n".join(lines), flush=True)

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
                # Ensure streamed tokens are followed by a newline so the
                # next input prompt doesn't bleed onto the response line.
                if not self.json_events:
                    print(flush=True)
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
            self._context_compressed = False
            self._compression_stats = {}
            self._emit_event(type="system", message="History cleared.")
            return None
        if text.strip() == "/help":
            self._emit_event(
                type="system",
                message=(
                    "Grace is the optional local fallback; host-agent integrations and MCP "
                    "remain the preferred workflow.\n\n"
                    "Core: /status /models /model NAME /provider NAME /clear /exit\n"
                    "Work: /ask /plan /fix /code /test /review /why /context\n"
                    "AEE: changes are requirement-scoped, test-gated, and evidence-backed."
                ),
            )
            return None
        if text.strip() == "/status":
            self._emit_event(
                type="system",
                message=(
                    f"provider={self.provider_name} model={self.model or '(auto)'} "
                    f"history_turns={len(self._history)} "
                    f"context_compressed={self._context_compressed}"
                ),
            )
            return None
        if text.strip() == "/models":
            msg = (
                self._model_router.table()
                if self._model_router is not None
                else "  (multi-model routing not configured — run: specsmith local-model setup)"
            )
            self._emit_event(type="system", message=msg)
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
            # G4: pin the profile choice into the project trace vault so the
            # decision “I explicitly asked for profile X here” is
            # cryptographically chained into the audit trail. Best-effort:
            # missing TraceVault dependency / read-only filesystem must not
            # break the chat loop.
            if new_profile:
                self._seal_profile_pin(new_profile)
            return None
        if text.startswith("/endpoint "):
            new_endpoint = text.split(maxsplit=1)[1].strip()
            self.endpoint_id = new_endpoint or None
            self._emit_event(type="system", message=f"endpoint = {new_endpoint or '(auto)'}")
            return None

        activity = _slash_to_activity(text)
        prefix = SLASH_COMMANDS.get(activity, "")
        utterance = text[len(activity) :].strip() if activity != "chat" else text
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

        # ── Multi-model routing (REQ-389) ──────────────────────────────────
        # Ask the router which Ollama model best fits this utterance, then
        # temporarily set SPECSMITH_OLLAMA_MODEL so _run_ollama picks it up.
        # The env var is restored (or removed) after the turn completes.
        import os as _os

        _prev_ollama_model = _os.environ.get("SPECSMITH_OLLAMA_MODEL")
        if self._model_router is not None:
            routed_model, switched = self._model_router.route(text)
            if routed_model:
                _os.environ["SPECSMITH_OLLAMA_MODEL"] = routed_model
                if switched:
                    role = self._model_router.active_role or "?"
                    self._emit_event(
                        type="system",
                        message=f"\u21bb model \u2192 {routed_model} (role: {role})",
                    )
        # ──────────────────────────────────────────────────────────────────

        try:
            from specsmith.agent.chat_runner import (
                DEFAULT_OLLAMA_HOST,
                _ollama_alive,
                _pick_ollama_model,
                run_chat,
            )

            self._compress_context_if_needed()
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
        finally:
            # Restore SPECSMITH_OLLAMA_MODEL to its pre-turn state (REQ-389).
            if _prev_ollama_model is None:
                _os.environ.pop("SPECSMITH_OLLAMA_MODEL", None)
            else:
                _os.environ["SPECSMITH_OLLAMA_MODEL"] = _prev_ollama_model

        if result is None:
            # All providers failed — give the user an actionable explanation
            # rather than silent emptiness.
            host = _os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")
            if _ollama_alive(host):
                model = _pick_ollama_model(host)
                hint = (
                    f"Ollama is running but returned no response "
                    f"(model: {model}). "
                    "Try: ollama run " + model
                )
            else:
                hint = (
                    "No LLM provider available. Options:\n"
                    "  • Start Ollama: ollama serve\n"
                    "  • Set ANTHROPIC_API_KEY / OPENAI_API_KEY / GOOGLE_API_KEY"
                )
            self._emit_event(type="system", message=hint)
            return None

        # Aggregate metrics into the session state (C1).
        # ``run_chat`` now reports tokens_in / tokens_out / cost_usd off the
        # provider response (Ollama prompt_eval_count + eval_count, OpenAI
        # streaming usage, Anthropic final_message.usage, Gemini
        # usage_metadata) with a 4-chars-per-token fallback when the SDK
        # omits them. The TokenMeter chip therefore shows real numbers
        # instead of staying pinned at zero.
        tokens_in = int(getattr(result, "tokens_in", 0) or 0) if result is not None else 0
        tokens_out = int(getattr(result, "tokens_out", 0) or 0) if result is not None else 0
        cost_usd = float(getattr(result, "cost_usd", 0.0) or 0.0) if result is not None else 0.0
        self._state.credit(
            profile_id=(profile.id if profile is not None else self.profile_id or ""),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost_usd,
            tool_calls=0,
        )
        self._state.elapsed_minutes = round((time.time() - self._started_at) / 60.0, 2)

        # Write token_metric to ESDB (REQ-410) — best-effort, never blocks.
        if tokens_in or tokens_out:
            model_name = str(getattr(result, "provider", "") if result else "")
            try:
                from specsmith.esdb_writer import write_token_metric

                write_token_metric(
                    self.project_dir,
                    input_tokens=tokens_in,
                    output_tokens=tokens_out,
                    cost_usd=cost_usd,
                    model=model_name,
                    command_source=activity or "chat",
                    work_item_id=str(getattr(self._state, "active_work_item_id", "") or ""),
                )
            except Exception:  # noqa: BLE001
                pass
            # Flush token usage to session_metrics.jsonl (REQ-436)
            try:
                from specsmith.project_metrics import flush_session_metrics  # noqa: PLC0415

                flush_session_metrics(
                    Path(self.project_dir),
                    work_item_id=str(getattr(self._state, "active_work_item_id", "") or ""),
                    model=model_name,
                    input_tokens=tokens_in,
                    output_tokens=tokens_out,
                    cost_usd=cost_usd,
                    command=activity or "chat",
                )
            except Exception:  # noqa: BLE001
                pass

        if result is not None:
            self._history.append({"role": "user", "text": utterance})
            self._history.append({"role": "agent", "text": result.summary})
        return result

    def _compress_context_if_needed(self) -> dict[str, Any]:
        """Compress old epistemic context before it enters the paid token path."""
        import os

        from specsmith.agent.context_compressor import compress_history_elements, should_compress

        try:
            threshold = int(os.environ.get("SPECSMITH_CONTEXT_COMPRESS_CHARS", "10000"))
        except ValueError:
            threshold = 10000
        if not should_compress(self._history, threshold_chars=max(1, threshold)):
            return {"ok": True, "skipped": True, "reason": "below threshold"}

        compressed, stats = compress_history_elements(
            self._history,
            project_dir=self.project_dir,
            target_pct=70.0,
        )
        self._compression_stats = stats
        if stats.get("ok") and not stats.get("skipped"):
            self._history = compressed
            self._context_compressed = True
            saved = stats.get("space_saved_pct", 0)
            self._emit_event(type="system", message=f"context compressed ({saved}% saved)")
        return stats

    # ── Routing helpers ────────────────────────────────────────────────

    def _resolve_for_activity(self, activity: str):
        """Return ``(Profile, endpoint_id_override)`` or ``(None, None)``.

        Respects an explicit per-session profile / endpoint override so
        the ``--agent`` and ``--endpoint`` CLI flags still win.

        When an execution profile is active, the resolved agent profile's
        provider is checked against the execution profile's allowed
        provider types / IDs. If not allowed, the profile's fallback
        chain is tried. This ensures a "local-only" execution profile
        never routes to a cloud provider.
        """
        if self.profile_id is None and self._routing is None:
            return (None, None)
        try:
            from specsmith.agent.profiles import ProfileStore

            store = ProfileStore.load()
            if self.profile_id:
                profile = store.get(self.profile_id)
                profile = self._filter_by_execution_profile(profile, store)
                return (profile, profile.endpoint_id or None) if profile else (None, None)
            target_id = store.routes.get(activity) or store.default_profile_id
            if not target_id:
                return (None, None)
            profile = store.get(target_id)
            profile = self._filter_by_execution_profile(profile, store)
            return (profile, profile.endpoint_id or None) if profile else (None, None)
        except Exception:  # noqa: BLE001
            return (None, None)

    def _filter_by_execution_profile(self, profile, store) -> Any:
        """Check if a profile's provider is allowed by the active execution profile.

        If not allowed, try fallback chain entries. Returns the original
        profile if no execution profile is loaded (graceful degradation).
        """
        try:
            from specsmith.agent.execution_profiles import ExecutionProfileStore

            ep_store = ExecutionProfileStore.load()
            exec_profile = ep_store.default()

            # Check if the primary profile's provider is allowed.
            if exec_profile.allows_provider(profile.provider, profile.provider):
                return profile

            # Try fallback chain entries.
            for fallback_str in profile.fallback_chain or []:
                parts = fallback_str.split("/", 1)
                fb_provider = parts[0] if parts else ""
                if exec_profile.allows_provider(fb_provider, fb_provider):
                    # Create a modified profile using the fallback.
                    from specsmith.agent.profiles import Profile

                    fb_model = parts[1] if len(parts) > 1 else ""
                    return Profile(
                        id=f"{profile.id}-fallback",
                        role=profile.role,
                        provider=fb_provider,
                        model=fb_model,
                        endpoint_id=profile.endpoint_id,
                        capabilities=profile.capabilities,
                        fallback_chain=[],
                    )

            # No allowed provider found — return None so caller degrades.
            self._emit_event(
                type="system",
                message=(
                    f"\u26a0 execution profile '{exec_profile.id}' blocks "
                    f"provider '{profile.provider}' and all fallbacks"
                ),
            )
            return None
        except Exception:  # noqa: BLE001 — graceful degradation
            return profile  # no execution profile loaded → allow everything

    def _load_routing(self) -> Any | None:
        try:
            from specsmith.agent.profiles import ProfileStore

            store = ProfileStore.load()
            return store if store.profiles else None
        except Exception:  # noqa: BLE001
            return None

    def _load_model_router(self) -> Any | None:
        """Load ModelRouter from .specsmith/local-models.yml (REQ-389).

        Returns ``None`` when no multi-role config is found, preserving
        single-model behaviour for existing setups.
        """
        try:
            from specsmith.agent.model_router import ModelRouter
            from specsmith.local_model import load_local_models_config

            roles = load_local_models_config(self.project_dir)
            if not roles:
                return None
            return ModelRouter(roles)
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

    def _build_context_seed(self) -> list[dict[str, Any]]:
        """Load prior session context for epistemic continuity (REQ-307).

        Returns an empty list if there is no prior state or if the project
        directory is not a governed project.  Never raises.
        """
        try:
            from specsmith.agent.context_seed import build_context_seed

            return build_context_seed(self.project_dir)
        except Exception:  # noqa: BLE001
            return []

    def _seal_profile_pin(self, profile_id: str) -> None:
        """Append a TraceVault decision seal recording the ``/agent`` pin (G4).

        Wrapped in best-effort try/except so an unwriteable ESDB store
        (read-only fs, missing project root, etc.) never breaks the chat loop.
        The seal is persisted as an ESDB ``seal_record`` (REQ-420). The seal
        type is ``decision`` because a profile pin is an explicit governance
        choice the user made.
        """
        try:
            from specsmith.trace import SealType, TraceVault

            vault = TraceVault(Path(self.project_dir))
            vault.seal(
                seal_type=SealType.DECISION,
                description=f"agent profile pinned via /agent: {profile_id}",
                author="runner",
                artifact_ids=[f"profile:{profile_id}"],
            )
        except Exception:  # noqa: BLE001 — trace sealing is best-effort
            return
