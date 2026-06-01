# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith MCP Server — native governance tool server (REQ-363).

Implements the Model Context Protocol (MCP) over stdio (JSON-RPC 2.0).
Any MCP client (Warp/Oz, Cursor, Claude Code) can add specsmith as a
tool server to call governance commands as structured tool calls.

Start with:
    specsmith mcp serve [--project-dir .]

Warp MCP config (Settings → Agents → MCP servers):
    {
      "specsmith-governance": {
        "command": "specsmith",
        "args": ["mcp", "serve"]
      }
    }

Tools exposed
-------------
governance_audit        Run governance audit; returns health + check results.
governance_checkpoint   Emit GOVERNANCE ANCHOR JSON (phase, health, counts).
governance_preflight    Preflight a change intent; returns decision + work_item_id.
governance_phase        Current AEE phase, readiness %, and failing checks.
governance_req_list     List all requirements (id, title, status, covered).
governance_trace_seal   Seal a milestone/decision in the cryptographic trace vault.

Protocol
--------
MCP pin: 2024-11-05 (current stable).
Transport: stdio (newline-delimited JSON-RPC 2.0).
No external dependencies — stdlib only + existing specsmith modules.
"""

from __future__ import annotations

import contextlib
import json
import sys
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# MCP protocol constants
# ---------------------------------------------------------------------------

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "specsmith-governance"
SERVER_VERSION = "0.12.0"

_TOOLS: list[dict[str, Any]] = [
    {
        "name": "governance_audit",
        "description": (
            "Run the specsmith governance audit. Returns health status and a list of "
            "all check results (passed/failed/suppressed). Required before phase advance."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "governance_checkpoint",
        "description": (
            "Emit the GOVERNANCE ANCHOR — a compact JSON snapshot of the current "
            "governance state (phase, health, REQ/TEST counts, ESDB chain, work items). "
            "Include this verbatim in any context summary. Run every 8-10 turns."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "governance_preflight",
        "description": (
            "Run a governance preflight check for a proposed change. "
            "Returns decision ('accepted' / 'needs_clarification' / 'rejected'), "
            "work_item_id, and instruction. "
            "Never make a code change without an accepted preflight."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "description": "One sentence describing the change you intend to make.",
                },
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
            },
            "required": ["intent"],
        },
    },
    {
        "name": "governance_phase",
        "description": (
            "Return the current AEE phase, readiness percentage, and any failing "
            "phase-readiness checks. The 7 phases are: inception → architecture → "
            "requirements → test_spec → implementation → verification → release."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                }
            },
            "required": [],
        },
    },
    {
        "name": "governance_req_list",
        "description": (
            "List all requirements in the project. Returns id, title, status, "
            "and whether the requirement has test coverage."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
                "status_filter": {
                    "type": "string",
                    "description": "Filter by status: 'planned', 'implemented', 'partial', 'deprecated'. Omit for all.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "governance_trace_seal",
        "description": (
            "Seal a milestone, decision, or audit gate in the cryptographic trace vault. "
            "Creates a tamper-evident SealRecord chained to all prior seals. "
            "Required to advance the Release phase to 100%."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "seal_type": {
                    "type": "string",
                    "enum": [
                        "decision",
                        "milestone",
                        "audit-gate",
                        "logic-knot",
                        "stress-test",
                        "epistemic",
                    ],
                    "description": "Type of seal to create.",
                },
                "description": {
                    "type": "string",
                    "description": "Human-readable description of what is being sealed.",
                },
                "project_dir": {
                    "type": "string",
                    "description": "Absolute or relative path to the project root. Defaults to '.'.",
                },
                "author": {
                    "type": "string",
                    "description": "Author of this seal (default: 'specsmith-mcp').",
                },
            },
            "required": ["seal_type", "description"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool handler implementations
# ---------------------------------------------------------------------------


def _resolve_root(args: dict[str, Any]) -> Path:
    raw = args.get("project_dir", ".")
    return Path(str(raw)).resolve()


def _handle_governance_audit(args: dict[str, Any]) -> dict[str, Any]:
    """Run the governance audit and return structured results."""
    root = _resolve_root(args)
    try:
        from specsmith.auditor import run_audit

        report = run_audit(root)
        return {
            "healthy": report.healthy,
            "passed": report.passed,
            "failed": report.failed,
            "fixable": report.fixable,
            "suppressed": report.suppressed_count,
            "checks": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "suppressed": r.suppressed,
                    "message": r.message,
                    "fixable": r.fixable,
                }
                for r in report.results
            ],
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "healthy": False, "passed": 0, "failed": -1, "checks": []}


def _handle_governance_checkpoint(args: dict[str, Any]) -> dict[str, Any]:
    """Emit a compact governance anchor JSON."""
    root = _resolve_root(args)
    import re

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Project name
    project_name = root.name
    try:
        import yaml as _yaml

        from specsmith.paths import find_scaffold

        sp = find_scaffold(root)
        if sp:
            raw = _yaml.safe_load(sp.read_text(encoding="utf-8")) or {}
            project_name = str(raw.get("name", root.name))
    except Exception:  # noqa: BLE001
        pass

    # Phase
    phase_key, phase_label, phase_emoji, phase_pct = "unknown", "Unknown", "", 0
    failing_phase_checks: list[str] = []
    try:
        from specsmith.phase import (  # noqa: PLC0415
            PHASE_MAP,
            phase_failing_checks,
            phase_progress_pct,
            read_phase,
        )

        phase_key = read_phase(root)
        phase = PHASE_MAP.get(phase_key)
        if phase:
            phase_label = phase.label
            phase_emoji = phase.emoji
            phase_pct = phase_progress_pct(phase, root)
            failing_phase_checks = phase_failing_checks(phase, root)
    except Exception:  # noqa: BLE001
        pass

    # Audit health
    health_ok, audit_failed = True, 0
    try:
        from specsmith.auditor import run_audit

        report = run_audit(root)
        health_ok = report.healthy
        audit_failed = report.failed
    except Exception:  # noqa: BLE001
        pass

    # REQ / TEST counts
    req_count, test_count = 0, 0
    try:
        rp = root / ".specsmith" / "requirements.json"
        tp = root / ".specsmith" / "testcases.json"
        if rp.exists():
            req_count = len(json.loads(rp.read_text(encoding="utf-8")))
        if tp.exists():
            test_count = len(json.loads(tp.read_text(encoding="utf-8")))
    except Exception:  # noqa: BLE001
        pass

    # ESDB
    esdb_ok, esdb_records = True, 0
    try:
        from chronomemory import ChronoStore

        wal = root / ".chronomemory" / "events.wal"
        if wal.exists():
            with ChronoStore(root) as store:
                esdb_ok = store.chain_valid()
                esdb_records = store.record_count()
    except Exception:  # noqa: BLE001
        pass

    # Recent work items
    recent_wis: list[str] = []
    try:
        for cand in ["docs/LEDGER.md", "LEDGER.md"]:
            lp = root / cand
            if lp.exists():
                text = lp.read_text(encoding="utf-8", errors="ignore")
                wis = re.findall(r"\bWI-[A-F0-9]{8}\b", text)
                seen: set[str] = set()
                for wi in reversed(wis):
                    if wi not in seen:
                        seen.add(wi)
                        recent_wis.insert(0, wi)
                    if len(seen) >= 3:
                        break
                break
    except Exception:  # noqa: BLE001
        pass

    return {
        "anchor": f"SPECSMITH-ANCHOR-{ts}",
        "ts": ts,
        "project": project_name,
        "phase": phase_key,
        "phase_label": f"{phase_emoji} {phase_label}",
        "phase_pct": phase_pct,
        "phase_failing_checks": failing_phase_checks,
        "health": "clean" if health_ok else f"{audit_failed} issues",
        "audit_failed": audit_failed,
        "req_count": req_count,
        "test_count": test_count,
        "esdb_records": esdb_records,
        "esdb_chain_valid": esdb_ok,
        "recent_work_items": recent_wis,
    }


def _handle_governance_preflight(args: dict[str, Any]) -> dict[str, Any]:
    """Run a governance preflight check for the given intent."""
    intent = str(args.get("intent", "")).strip()
    if not intent:
        return {"decision": "rejected", "instruction": "intent is required", "work_item_id": ""}

    root = _resolve_root(args)
    try:
        from specsmith.governance_logic import run_preflight

        result = run_preflight(intent, project_dir=root)
        return dict(result)
    except Exception as exc:  # noqa: BLE001
        # Fallback: subprocess the CLI so preflight always works even if import path differs
        import subprocess

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "specsmith", "preflight", intent, "--json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(root),
            )
            return json.loads(proc.stdout)
        except Exception as exc2:  # noqa: BLE001
            return {
                "decision": "needs_clarification",
                "instruction": f"preflight unavailable: {exc}; fallback failed: {exc2}",
                "work_item_id": "",
            }


def _handle_governance_phase(args: dict[str, Any]) -> dict[str, Any]:
    """Return the current AEE phase and readiness info."""
    root = _resolve_root(args)
    try:
        from specsmith.phase import PHASE_MAP, phase_progress_pct, read_phase

        phase_key = read_phase(root)
        phase = PHASE_MAP.get(phase_key)
        if not phase:
            return {"phase": phase_key, "label": "Unknown", "pct": 0, "failing_checks": []}

        pct = phase_progress_pct(phase, root)
        # Try to get failing checks
        failing: list[str] = []
        try:
            from specsmith.phase import phase_failing_checks

            failing = phase_failing_checks(phase, root)
        except Exception:  # noqa: BLE001
            pass

        return {
            "phase": phase_key,
            "label": f"{phase.emoji} {phase.label}",
            "pct": pct,
            "description": phase.description,
            "failing_checks": failing,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "phase": "unknown", "pct": 0, "failing_checks": []}


def _handle_governance_req_list(args: dict[str, Any]) -> dict[str, Any]:
    """List requirements from the project."""
    root = _resolve_root(args)
    status_filter = str(args.get("status_filter", "")).strip().lower() or None

    try:
        req_path = root / ".specsmith" / "requirements.json"
        test_path = root / ".specsmith" / "testcases.json"

        if not req_path.exists():
            return {"error": "requirements.json not found — run specsmith sync first", "reqs": []}

        reqs_raw: list[dict[str, Any]] = json.loads(req_path.read_text(encoding="utf-8"))

        # Build set of covered req IDs from testcases.json
        covered: set[str] = set()
        if test_path.exists():
            tests_raw: list[dict[str, Any]] = json.loads(test_path.read_text(encoding="utf-8"))
            for t in tests_raw:
                covers = t.get("covers", t.get("req_id", ""))
                if covers:
                    covered.add(str(covers))

        reqs: list[dict[str, Any]] = []
        for r in reqs_raw:
            rid = str(r.get("id", ""))
            status = str(r.get("status", "")).lower()
            if status_filter and status != status_filter:
                continue
            reqs.append(
                {
                    "id": rid,
                    "title": str(r.get("title", r.get("description", ""))),
                    "status": status,
                    "covered": rid in covered,
                }
            )

        return {
            "total": len(reqs),
            "covered": sum(1 for r in reqs if r["covered"]),
            "reqs": reqs,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "reqs": []}


def _handle_governance_trace_seal(args: dict[str, Any]) -> dict[str, Any]:
    """Create a cryptographic trace vault seal."""
    seal_type = str(args.get("seal_type", "milestone")).strip()
    description = str(args.get("description", "")).strip()
    author = str(args.get("author", "specsmith-mcp")).strip()
    root = _resolve_root(args)

    if not description:
        return {"error": "description is required", "sealed": False}

    try:
        from specsmith.trace import TraceVault

        vault = TraceVault(root)
        record = vault.seal(seal_type=seal_type, description=description, author=author)
        return {
            "sealed": True,
            "seal_id": record.seal_id,
            "seal_type": record.seal_type,
            "description": record.description,
            "timestamp": record.timestamp,
            "entry_hash": record.entry_hash,
        }
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc), "sealed": False}


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------

_HANDLERS = {
    "governance_audit": _handle_governance_audit,
    "governance_checkpoint": _handle_governance_checkpoint,
    "governance_preflight": _handle_governance_preflight,
    "governance_phase": _handle_governance_phase,
    "governance_req_list": _handle_governance_req_list,
    "governance_trace_seal": _handle_governance_trace_seal,
}


# ---------------------------------------------------------------------------
# MCP JSON-RPC 2.0 server loop
# ---------------------------------------------------------------------------


def _send(payload: dict[str, Any]) -> None:
    """Write one JSON-RPC message to stdout."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _error_response(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _ok_response(req_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _text_block(text: str) -> list[dict[str, str]]:
    return [{"type": "text", "text": text}]


def _handle_request(msg: dict[str, Any]) -> dict[str, Any] | None:
    """Process one JSON-RPC request and return a response dict (or None for notifications)."""
    method = str(msg.get("method", ""))
    req_id = msg.get("id")
    params = msg.get("params") or {}

    # Notifications have no id — send no response
    if req_id is None and method.startswith("notifications/"):
        return None

    if method == "initialize":
        return _ok_response(
            req_id,
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    if method == "tools/list":
        return _ok_response(req_id, {"tools": _TOOLS})

    if method == "tools/call":
        tool_name = str(params.get("name", ""))
        tool_args: dict[str, Any] = params.get("arguments") or {}

        handler = _HANDLERS.get(tool_name)
        if handler is None:
            return _ok_response(
                req_id,
                {
                    "isError": True,
                    "content": _text_block(f"Unknown tool: {tool_name}"),
                },
            )
        try:
            result = handler(tool_args)
            content_text = json.dumps(result, indent=2, ensure_ascii=False)
            return _ok_response(
                req_id,
                {"isError": False, "content": _text_block(content_text)},
            )
        except Exception as exc:  # noqa: BLE001
            return _ok_response(
                req_id,
                {"isError": True, "content": _text_block(f"Tool error: {exc}")},
            )

    if method == "ping":
        return _ok_response(req_id, {})

    if req_id is not None:
        return _error_response(req_id, -32601, f"Method not found: {method}")
    return None


def run_server(project_dir: str = ".") -> None:
    """Start the MCP stdio server. Blocks until stdin closes.

    Reads newline-delimited JSON-RPC 2.0 messages from stdin and
    writes responses to stdout. Stderr is used for diagnostic messages.
    The ``project_dir`` is injected into every tool call that doesn't
    supply its own ``project_dir`` argument.
    """
    import os

    # Set working directory so relative paths in tool calls resolve correctly
    if project_dir and project_dir != ".":
        with contextlib.suppress(OSError):
            os.chdir(project_dir)

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            msg = json.loads(raw_line)
        except ValueError as exc:
            _send(_error_response(None, -32700, f"Parse error: {exc}"))
            continue

        if not isinstance(msg, dict):
            _send(_error_response(None, -32600, "Invalid request"))
            continue

        try:
            response = _handle_request(msg)
        except Exception as exc:  # noqa: BLE001
            _send(_error_response(msg.get("id"), -32603, f"Internal error: {exc}"))
            continue

        if response is not None:
            _send(response)


__all__ = ["run_server", "SERVER_NAME", "SERVER_VERSION", "_TOOLS", "_HANDLERS"]
