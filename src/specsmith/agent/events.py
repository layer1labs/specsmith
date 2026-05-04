# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Block-based JSONL event protocol for `specsmith chat` (REQ-112, REQ-113, REQ-114).

The protocol is the contract between the Specsmith chat backend and any
client (the Nexus REPL itself, the VS Code extension, or future TUIs).
Every event is a single JSON object on its own line with a ``type`` key.

Event kinds
-----------
* ``block_start``      - begins a new block (kinds: ``plan``, ``message``,
                         ``tool_call``, ``tool_result``, ``diff``,
                         ``test_results``, ``verdict``).
* ``block_complete``   - closes the block opened by ``block_start``.
* ``token``            - incremental LLM token within a ``message`` block.
* ``tool_call``        - the LLM has decided to invoke a tool.
* ``tool_request``     - safe-mode permission request (REQ-115).
* ``tool_result``      - completed tool execution.
* ``plan_step``        - status transition for a step in the active plan
                         block (REQ-114).
* ``task_complete``    - final block; carries final summary + profile.
* ``ready``            - emitted exactly once at process start (REQ-145);
                         the VS Code bridge waits up to 20 s for this
                         frame before declaring the agent unresponsive.
"""

from __future__ import annotations

import contextlib
import json
import sys
import time
import uuid
from dataclasses import dataclass, field
from typing import IO, Any


def _now_iso() -> str:
    """Return a UTC ISO-8601 timestamp (second precision)."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _new_block_id() -> str:
    return f"blk_{uuid.uuid4().hex[:12]}"


@dataclass
class EventEmitter:
    """Writes JSONL events to a stream (default stdout).

    Used by the `specsmith chat` CLI and by the test suite. Each event is
    flushed immediately so consumers can react in real time.
    """

    stream: IO[str] = field(default_factory=lambda: sys.stdout)

    def emit(self, event: dict[str, Any]) -> None:
        line = json.dumps(event, ensure_ascii=False)
        self.stream.write(line + "\n")
        # Some test buffers (e.g. capsys) don't support flush; ignore.
        with contextlib.suppress(Exception):
            self.stream.flush()

    # ── Lifecycle helpers ────────────────────────────────────────────────

    def ready(
        self,
        *,
        agent: str = "nexus",
        version: str = "",
        project_dir: str = "",
        provider: str = "",
        model: str = "",
        profile_id: str = "",
        capabilities: list[str] | None = None,
        **extra: Any,
    ) -> None:
        """Emit the bridge handshake frame (REQ-145).

        The VS Code extension's :class:`SpecsmithBridge` keys off this
        single event to flip from ``starting`` → ``waiting`` and to start
        flushing the queued user prompts. Schema is intentionally flat so
        a ``JSON.parse`` line check is enough on the consumer side.
        """
        payload: dict[str, Any] = {
            "type": "ready",
            "timestamp": _now_iso(),
            "agent": agent,
            "version": version,
            "project_dir": project_dir,
            "provider": provider,
            "model": model,
            "profile_id": profile_id,
            "capabilities": list(capabilities or []),
        }
        payload.update(extra)
        self.emit(payload)

    def system(self, message: str, **extra: Any) -> None:
        """Emit a free-form system note (matches bridge.ts handler)."""
        self.emit({"type": "system", "message": message, **extra})

    def turn_done(self, **extra: Any) -> None:
        """Emit the per-turn terminator the bridge uses to clear timers."""
        self.emit({"type": "turn_done", "timestamp": _now_iso(), **extra})

    def error(self, message: str, *, recoverable: bool = False, **extra: Any) -> None:
        """Emit an error frame (recoverable = retry will be offered)."""
        self.emit(
            {
                "type": "error",
                "timestamp": _now_iso(),
                "message": message,
                "recoverable": bool(recoverable),
                **extra,
            }
        )

    # ── Block helpers ────────────────────────────────────────────────────

    def block_start(self, kind: str, *, agent: str = "nexus", **payload: Any) -> str:
        """Open a new block of ``kind`` and return its id."""
        block_id = _new_block_id()
        self.emit(
            {
                "type": "block_start",
                "block_id": block_id,
                "kind": kind,
                "agent": agent,
                "timestamp": _now_iso(),
                "payload": payload,
            }
        )
        return block_id

    def block_complete(self, block_id: str, **payload: Any) -> None:
        self.emit(
            {
                "type": "block_complete",
                "block_id": block_id,
                "timestamp": _now_iso(),
                "payload": payload,
            }
        )

    def token(self, block_id: str, text: str) -> None:
        self.emit(
            {
                "type": "token",
                "block_id": block_id,
                "text": text,
            }
        )

    def tool_call(self, block_id: str, name: str, args: dict[str, Any]) -> None:
        self.emit(
            {
                "type": "tool_call",
                "block_id": block_id,
                "name": name,
                "args": args,
            }
        )

    def tool_request(self, block_id: str, name: str, args: dict[str, Any]) -> None:
        self.emit(
            {
                "type": "tool_request",
                "block_id": block_id,
                "name": name,
                "args": args,
            }
        )

    def tool_result(self, block_id: str, name: str, ok: bool, output: str) -> None:
        self.emit(
            {
                "type": "tool_result",
                "block_id": block_id,
                "name": name,
                "ok": ok,
                "output": output,
            }
        )

    def plan(self, steps: list[dict[str, Any]]) -> str:
        return self.block_start("plan", steps=steps)

    def plan_step(
        self,
        block_id: str,
        step_id: str,
        status: str,
        **payload: Any,
    ) -> None:
        self.emit(
            {
                "type": "plan_step",
                "block_id": block_id,
                "step_id": step_id,
                "status": status,
                "timestamp": _now_iso(),
                "payload": payload,
            }
        )

    def diff(self, path: str, body: str) -> str:
        return self.block_start("diff", path=path, body=body)

    def task_complete(
        self,
        *,
        success: bool,
        confidence: float,
        summary: str,
        profile: str,
        comments: list[dict[str, Any]] | None = None,
        **extra: Any,
    ) -> None:
        self.emit(
            {
                "type": "task_complete",
                "timestamp": _now_iso(),
                "success": success,
                "confidence": confidence,
                "summary": summary,
                "profile": profile,
                "comments": comments or [],
                **extra,
            }
        )


__all__ = ["EventEmitter"]
