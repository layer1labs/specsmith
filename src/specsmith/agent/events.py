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
