# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Governance REST API logic — shared by CLI commands and HTTP server.

These pure-Python functions implement the /preflight and /verify business
logic without any HTTP or Click dependencies so they can be called from:
  - the existing ``specsmith preflight`` / ``specsmith verify`` CLI commands
  - the ``specsmith governance-serve`` HTTP server (used by Kairos)

All functions are synchronous and return plain dicts suitable for JSON
serialisation.  They never write to stdout/stderr; callers handle I/O.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, cast


def run_preflight(
    utterance: str,
    project_dir: str | Path = ".",
    *,
    predict_only: bool = False,
    escalate_threshold: float | None = None,
) -> dict[str, Any]:
    """Run the governance preflight check and return the decision payload.

    This is the authoritative implementation; the CLI command delegates here.

    Args:
        utterance: Natural-language description of the action to be gated.
        project_dir: Project root directory (resolved to absolute path).
        predict_only: If True, skip work-item allocation and ledger write.
        escalate_threshold: REG-004 confidence floor for human escalation.

    Returns:
        JSON-serialisable dict matching the PreflightDecision schema:
        ``decision``, ``work_item_id``, ``requirement_ids``, ``test_case_ids``,
        ``confidence_target``, ``instruction``, ``intent``, ``ai_disclosure``.
    """
    import json as _json

    from specsmith import __version__
    from specsmith.agent.broker import Intent, classify_intent, infer_scope

    root = Path(project_dir).resolve()
    intent = classify_intent(utterance)
    scope = infer_scope(
        utterance,
        root / "REQUIREMENTS.md",
        repo_index_path=root / ".repo-index" / "files.json",
    )

    requirement_ids = [r.req_id for r in scope.matched_requirements]

    # Resolve test case IDs from machine state
    test_case_ids: list[str] = []
    if requirement_ids:
        tc_json = root / ".specsmith" / "testcases.json"
        if tc_json.is_file():
            try:
                records = _json.loads(tc_json.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                records = []
            req_set = set(requirement_ids)
            for rec in records:
                if (
                    isinstance(rec, dict)
                    and rec.get("requirement_id") in req_set
                    and isinstance(rec.get("id"), str)
                ):
                    test_case_ids.append(rec["id"])

    # Decision policy (deterministic, no LLM)
    decision_str = "accepted"
    instruction = ""
    confidence_target = 0.7

    if intent == Intent.READ_ONLY_ASK:
        decision_str = "accepted"
        instruction = "Read-only ask; no governance changes required."
    elif intent == Intent.DESTRUCTIVE:
        decision_str = "needs_clarification"
        instruction = (
            "Destructive operation detected. "
            "Confirm explicitly which paths or resources should be removed."
        )
        confidence_target = 0.9
    elif intent == Intent.RELEASE:
        decision_str = "needs_clarification"
        instruction = (
            "Release operations require explicit confirmation. "
            "Specify the target version and channel."
        )
        confidence_target = 0.9
    else:  # CHANGE
        if scope.is_known:
            decision_str = "accepted"
            instruction = (
                "Change request matched existing governance scope. "
                "Proceed under Specsmith verification."
            )
            confidence_target = max(0.7, scope.confidence)
        else:
            decision_str = "needs_clarification"
            instruction = (
                "This change does not match an existing requirement. "
                "Could you say in one sentence which behavior you expect?"
            )
            confidence_target = 0.7

    # Config floor (REQ-098)
    cfg_threshold = _read_confidence_threshold(root)
    if cfg_threshold is not None and cfg_threshold > confidence_target:
        confidence_target = cfg_threshold

    work_item_id = (
        f"WI-{uuid.uuid4().hex[:8].upper()}"
        if (decision_str == "accepted" and not predict_only)
        else ""
    )

    payload: dict[str, Any] = {
        "decision": decision_str,
        "work_item_id": work_item_id,
        "requirement_ids": requirement_ids,
        "test_case_ids": test_case_ids,
        "confidence_target": round(confidence_target, 3),
        "instruction": instruction,
        "intent": intent.value,
        "ai_disclosure": {
            "governed_by": "specsmith",
            "governance_gated": True,
            "provider": os.environ.get("SPECSMITH_PROVIDER", "local/heuristic"),
            "model": os.environ.get("SPECSMITH_MODEL", "deterministic-broker"),
            "spec_version": __version__,
        },
    }

    # REG-004: escalation notice
    if escalate_threshold is not None and confidence_target < escalate_threshold:
        payload["escalation_required"] = True
        payload["escalation_reason"] = (
            f"Confidence {confidence_target:.3f} is below escalation threshold "
            f"{escalate_threshold:.3f}. Human review required before execution."
        )

    return payload


def run_verify(
    diff: str = "",
    files_changed: list[str] | None = None,
    test_results: dict[str, Any] | None = None,
    project_dir: str | Path = ".",
    work_item_id: str = "",
    reviewer_comment: str = "",
) -> dict[str, Any]:
    """Run the governance verification check and return the result payload.

    Args:
        diff: Unified diff of changes made.
        files_changed: List of changed file paths.
        test_results: Test results dict (``passed``, ``failed``, ``errors`` keys).
        project_dir: Project root directory.
        work_item_id: Optional work item id to bind this verification to.
        reviewer_comment: Human reviewer comment for retry strategies (REQ-116).

    Returns:
        JSON-serialisable dict matching the VerifyResult schema:
        ``equilibrium``, ``confidence``, ``summary``, ``files_changed``,
        ``test_results``, ``retry_strategy``, ``work_item_id``.
    """
    from specsmith.agent.broker import (
        DEFAULT_RETRY_BUDGET,
        PreflightDecision,
        classify_retry_strategy,
    )

    root = Path(project_dir).resolve()
    files_changed = files_changed or []
    test_results = test_results or {}

    failed = 0
    for key in ("failed", "failures", "errors"):
        try:
            failed += int(test_results.get(key, 0) or 0)
        except (TypeError, ValueError):
            continue
    raw_text = str(test_results.get("raw", "") or "").lower()
    if "failed" in raw_text and not failed:
        failed = 1

    has_changes = bool(files_changed) or bool(diff)
    threshold = _read_confidence_threshold(root) or 0.7
    equilibrium = failed == 0 and has_changes
    confidence = 0.85 if equilibrium else (0.4 if has_changes else 0.0)
    summary = (
        "Equilibrium reached. All tests passed."
        if equilibrium
        else f"{failed} test failure(s) detected."
        if failed
        else "No changes or test signal provided."
    )

    fake_decision = PreflightDecision(
        raw={},
        decision="accepted",
        work_item_id=work_item_id,
        confidence_target=threshold,
    )
    fake_report = {
        "equilibrium": equilibrium,
        "confidence": confidence,
        "summary": summary,
        "test_results": test_results,
    }
    retry_strategy = (
        ""
        if equilibrium and confidence >= threshold
        else classify_retry_strategy(fake_report, fake_decision)
    )

    out: dict[str, Any] = {
        "equilibrium": equilibrium,
        "confidence": round(confidence, 3),
        "summary": summary,
        "files_changed": list(files_changed),
        "test_results": test_results,
        "retry_strategy": retry_strategy,
        "work_item_id": work_item_id,
        "retry_budget": DEFAULT_RETRY_BUDGET,
        "confidence_threshold": threshold,
    }
    if reviewer_comment:
        out["reviewer_comment"] = reviewer_comment
    return out


# ---------------------------------------------------------------------------
# OpenAI-compatible governance proxy (for Kairos BYOE integration)
# ---------------------------------------------------------------------------


def _build_openai_response(
    model: str,
    content: str,
    role: str = "assistant",
    finish_reason: str = "stop",
) -> dict[str, Any]:
    """Build a minimal OpenAI-compatible /v1/chat/completions response."""
    import time
    import uuid

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:20]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": role, "content": content},
                "finish_reason": finish_reason,
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }


def run_chat_proxy(
    messages: list[dict[str, Any]],
    model: str,
    project_dir: str | None = None,
    *,
    real_base_url: str | None = None,
    real_api_key: str | None = None,
    real_model: str | None = None,
) -> dict[str, Any]:
    """OpenAI-compatible governance proxy for Kairos BYOE integration.

    This is called from the ``POST /v1/chat/completions`` endpoint in
    :class:`GovernanceHTTPServer`.  It intercepts every AI request that
    Kairos makes:

    1. Extracts the user's utterance from the message list (last user turn).
    2. Runs :func:`run_preflight` — if not accepted, returns a governance
       refusal response **instead** of forwarding to the real AI.
    3. Forwards the request to the real AI provider (``KAIROS_AI_BASE_URL``).
    4. Runs :func:`run_verify` on the response summary.
    5. Returns the real AI response (with a ``x-kairos-governance`` header in
       the HTTP layer).

    Environment variables used when real provider is not passed explicitly:
    - ``KAIROS_AI_BASE_URL``  — real AI provider base URL
    - ``KAIROS_AI_API_KEY``   — real AI provider API key
    - ``KAIROS_AI_MODEL``     — real AI provider model

    Falls back to a stub response when no real provider is configured
    (useful for local dev / governance-only testing without a real LLM).
    """
    import json as _json
    import os
    import urllib.request

    # ── 1. Extract utterance from last user message ─────────────────────────
    utterance = ""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("role") == "user":
            content = msg.get("content", "")
            utterance = content if isinstance(content, str) else str(content)
            break
    if not utterance:
        utterance = "kairos terminal request"

    # ── 2. Governance preflight gate ───────────────────────────────────
    effective_project = project_dir or os.getcwd()
    preflight = run_preflight(utterance, effective_project)

    if preflight.get("decision") not in ("accepted",):
        # Not accepted — return governance refusal, do NOT forward to AI.
        instruction = preflight.get("instruction", "Request not accepted by governance.")
        refusal = (
            f"⚠ **Kairos Governance Gate**: {instruction}\n\n"
            f"Decision: `{preflight.get('decision', 'needs_clarification')}`  \n"
            f"WI: `{preflight.get('work_item_id', '—')}`  \n"
            f"Confidence target: `{preflight.get('confidence_target', 0.7)}`"
        )
        return _build_openai_response(model, refusal, finish_reason="governance_stop")

    # ── 3. Forward to real AI provider ──────────────────────────────────
    base_url = (real_base_url or os.environ.get("KAIROS_AI_BASE_URL", "")).rstrip("/")
    api_key = real_api_key or os.environ.get("KAIROS_AI_API_KEY", "")
    effective_model = real_model or os.environ.get("KAIROS_AI_MODEL", "") or model

    if not base_url:
        # No real AI configured — return governance-accepted stub.
        stub = (
            f"✓ **Governance ACCEPTED** (WI:`{preflight.get('work_item_id', '')}`).  \n"
            f"No AI provider configured. Set `KAIROS_AI_BASE_URL` to forward requests.  \n"
            f"Utterance: *{utterance[:200]}*"
        )
        return _build_openai_response(effective_model, stub)

    try:
        payload = _json.dumps(
            {
                "model": effective_model,
                "messages": messages,
                "stream": False,
            }
        ).encode()
        headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
        }
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        req = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=payload,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310
            ai_response: dict[str, Any] = cast(dict[str, Any], _json.loads(resp.read()))
    except Exception as exc:  # noqa: BLE001
        # Forward failure — return governance-accepted stub with error note.
        error_stub = (
            f"✓ **Governance ACCEPTED** — AI provider error: `{exc}`.  \n"
            f"Check `KAIROS_AI_BASE_URL` (`{base_url}`) is reachable."
        )
        return _build_openai_response(effective_model, error_stub)

    # ── 4. Post-response verify (best-effort) ─────────────────────────────
    try:
        ai_text = ai_response.get("choices", [{}])[0].get("message", {}).get("content", "")
        run_verify(
            diff=f"[AI response to: {utterance[:100]}]",
            files_changed=[],
            test_results={"raw": f"ai response received, length={len(ai_text)}"},
            project_dir=effective_project,
            work_item_id=preflight.get("work_item_id", ""),
        )
    except Exception:  # noqa: BLE001
        pass  # verify is best-effort; never block the response

    return ai_response


# ---------------------------------------------------------------------------
# Governance REST HTTP server (for Kairos integration)
# ---------------------------------------------------------------------------


def make_governance_server(
    *,
    project_dir: str = ".",
    port: int = 7700,
    host: str = "127.0.0.1",
) -> GovernanceHTTPServer:
    """Build a ``GovernanceHTTPServer`` that handles /health, /preflight, /verify.

    This server is separate from the chat ``specsmith serve`` (port 8421).
    Kairos spawns it via ``specsmith governance-serve --port 7700``.
    """
    return GovernanceHTTPServer(project_dir=project_dir, port=port, host=host)


class GovernanceHTTPServer:
    """Minimal stdlib HTTP server for the Kairos governance REST API.

    Endpoints:
        GET  /health     — liveness probe; returns version JSON
        POST /preflight  — governance preflight gate
        POST /verify     — post-change verification
    """

    def __init__(
        self,
        *,
        project_dir: str = ".",
        port: int = 7700,
        host: str = "127.0.0.1",
    ) -> None:
        self.project_dir = str(Path(project_dir).resolve())
        self.port = port
        self.host = host
        self._server: object | None = None

    def start(self) -> None:
        """Start serving in the foreground (blocks until Ctrl-C)."""
        import sys
        from http.server import BaseHTTPRequestHandler, HTTPServer
        from socketserver import ThreadingMixIn

        project_dir = self.project_dir

        class _ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
            daemon_threads = True
            allow_reuse_address = True

        class _Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: object) -> None:  # noqa: A002
                pass  # suppress default stderr access log

            def _json_ok(self, data: dict[str, Any]) -> None:
                import json

                body = json.dumps(data, ensure_ascii=False).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)

            def _json_err(self, msg: str, code: int = 400) -> None:
                import json

                body = json.dumps({"error": msg}).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read_json(self) -> dict[str, Any]:
                import json

                length = int(self.headers.get("Content-Length", 0))
                if not length:
                    return {}
                try:
                    return cast(dict[str, Any], json.loads(self.rfile.read(length)))
                except (ValueError, OSError):
                    return {}

            def do_GET(self) -> None:  # noqa: N802
                from specsmith import __version__

                if self.path in ("/health", "/api/health"):
                    self._json_ok({"status": "ok", "version": __version__})

                # ── Session ────────────────────────────────────────────
                elif self.path == "/api/session":
                    try:
                        from specsmith.session_init import init_session

                        ctx = init_session(project_dir)
                        self._json_ok(ctx.to_dict())
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)

                # ── Compliance ─────────────────────────────────────────
                elif self.path == "/api/compliance/summary":
                    try:
                        from specsmith.compliance import get_compliance_summary

                        s = get_compliance_summary(project_dir)
                        self._json_ok(s.to_dict())
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)
                elif self.path == "/api/compliance/gaps":
                    try:
                        from specsmith.compliance import get_compliance_summary

                        s = get_compliance_summary(project_dir)
                        self._json_ok(
                            {"uncovered": s.uncovered_requirements, "orphaned": s.orphaned_tests}
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)
                elif self.path == "/api/compliance/trace":
                    try:
                        from specsmith.compliance import get_compliance_summary

                        s = get_compliance_summary(project_dir)
                        self._json_ok({"trace_matrix": s.trace_matrix})
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)

                # ── Governance ─────────────────────────────────────────
                elif self.path == "/api/governance/rules":
                    try:
                        from specsmith.compliance import get_governance_rules_status

                        self._json_ok({"rules": get_governance_rules_status(project_dir)})
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)
                elif self.path == "/api/governance/phase":
                    try:
                        from specsmith.phase import PHASE_MAP, phase_progress_pct, read_phase

                        root = Path(project_dir).resolve()
                        key = read_phase(root)
                        phase = PHASE_MAP[key]
                        self._json_ok(
                            {
                                "phase": key,
                                "label": phase.label,
                                "emoji": phase.emoji,
                                "readiness_pct": phase_progress_pct(phase, root),
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)
                elif self.path == "/api/governance/audit":
                    try:
                        from specsmith.auditor import run_audit

                        report = run_audit(Path(project_dir).resolve())
                        self._json_ok(
                            {
                                "healthy": report.healthy,
                                "passed": report.passed,
                                "failed": report.failed,
                                "results": [
                                    {"passed": r.passed, "message": r.message}
                                    for r in report.results
                                ],
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)

                # ── Providers ──────────────────────────────────────────
                elif self.path == "/api/providers":
                    try:
                        from specsmith.agent.provider_registry import ProviderRegistry

                        reg = ProviderRegistry.load()
                        self._json_ok({"providers": [p.to_public_dict() for p in reg.providers]})
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)

                # ── Profiles ───────────────────────────────────────────
                elif self.path == "/api/profiles":
                    try:
                        from specsmith.agent.execution_profiles import ExecutionProfileStore

                        store = ExecutionProfileStore.load()
                        self._json_ok(
                            {
                                "profiles": [p.to_dict() for p in store.profiles],
                                "default": store.default().id,
                            }
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)

                # ── Model Scores ───────────────────────────────────────
                elif self.path.startswith("/api/models/scores"):
                    try:
                        import urllib.parse as _up

                        from specsmith.agent.model_intelligence import (
                            BASELINE_SCORES,
                            rank_models_for_role,
                        )

                        qs = _up.urlparse(self.path).query
                        params = _up.parse_qs(qs)
                        role = params.get("role", ["coder"])[0]
                        models = list(BASELINE_SCORES.keys())
                        ranked = rank_models_for_role(role, models)
                        self._json_ok(
                            {"role": role, "scores": [{"model": m, "score": s} for m, s in ranked]}
                        )
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)

                # ── Datasources ────────────────────────────────────────
                elif self.path == "/api/datasources":
                    try:
                        sources = [
                            {"id": "patentsview", "name": "PatentsView"},
                            {"id": "ppubs", "name": "Patent Public Search (PPUBS)"},
                            {"id": "odp", "name": "USPTO Open Data Portal"},
                            {"id": "pfw", "name": "Patent File Wrapper"},
                            {"id": "citations", "name": "USPTO Enriched Citations"},
                            {"id": "fpd", "name": "Final Petition Decisions"},
                            {"id": "ptab", "name": "USPTO PTAB"},
                        ]
                        self._json_ok({"datasources": sources})
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)

                else:
                    self.send_error(404)

            def do_POST(self) -> None:  # noqa: N802
                body = self._read_json()
                if self.path == "/preflight":
                    try:
                        result = run_preflight(
                            utterance=body.get("utterance", ""),
                            project_dir=body.get("project_dir") or project_dir,
                        )
                        self._json_ok(result)
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)
                elif self.path == "/verify":
                    try:
                        result = run_verify(
                            diff=body.get("diff", ""),
                            files_changed=body.get("files_changed") or [],
                            test_results=body.get("test_results") or {},
                            project_dir=body.get("project_dir") or project_dir,
                            work_item_id=body.get("work_item_id", ""),
                        )
                        self._json_ok(result)
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)
                elif self.path == "/v1/chat/completions":
                    # Kairos BYOE gateway — intercept, gate, forward.
                    try:
                        # Detect role from request header or infer from system prompt.
                        req_role = self.headers.get("X-Specsmith-Role", "")
                        if not req_role:
                            req_role = _infer_role_from_messages(body.get("messages") or [])

                        result = run_chat_proxy(
                            messages=body.get("messages") or [],
                            model=body.get("model", "kairos"),
                            project_dir=body.get("project_dir") or project_dir,
                        )
                        import json as _j

                        raw = _j.dumps(result, ensure_ascii=False).encode()
                        effective_model = result.get("model", body.get("model", ""))
                        effective_provider = _resolve_provider_name()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(raw)))
                        self.send_header("x-kairos-governance", "gated")
                        self.send_header("X-Specsmith-Role", req_role or "coder")
                        self.send_header("X-Specsmith-Model", effective_model)
                        self.send_header("X-Specsmith-Provider", effective_provider)
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()
                        self.wfile.write(raw)
                    except Exception as exc:  # noqa: BLE001
                        self._json_err(str(exc), code=500)
                else:
                    self.send_error(404)

            def do_OPTIONS(self) -> None:  # noqa: N802
                """CORS preflight."""
                self.send_response(200)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

        self._server = _ThreadedHTTPServer((self.host, self.port), _Handler)
        print(  # noqa: T201
            f"specsmith governance-serve — http://{self.host}:{self.port}\n"
            f"  Project:   {self.project_dir}\n"
            f"  Governance endpoints:\n"
            f"    GET  /health                  liveness probe\n"
            f"    POST /preflight               governance gate\n"
            f"    POST /verify                  post-change verification\n"
            f"  Kairos BYOE gateway:\n"
            f"    POST /v1/chat/completions     OpenAI-compatible proxy\n"
            f"      Gate: preflight → forward to KAIROS_AI_BASE_URL → verify\n"
            f"  Press Ctrl+C to stop.\n",
            file=sys.stderr,
        )
        try:
            self._server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self._server.shutdown()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


# Role keywords used by _infer_role_from_messages to detect intent from system prompts.
_ROLE_KEYWORDS: dict[str, list[str]] = {
    "coder": ["write code", "implement", "code", "function", "diff"],
    "architect": ["design", "architecture", "system", "trade-off"],
    "reviewer": ["review", "feedback", "quality", "pr"],
    "editor": ["edit", "format", "refactor", "fix"],
    "researcher": ["research", "documentation", "lookup", "search"],
    "tester": ["test", "coverage", "assertion", "spec"],
    "classifier": ["classify", "categorize", "intent"],
    "strategist": ["strategy", "business", "competitive", "market"],
    "drafter": ["draft", "specification", "proposal", "report"],
    "ip-analyst": ["patent", "claims", "prior art", "ip", "freedom"],
}


def _infer_role_from_messages(messages: list[dict[str, Any]]) -> str:
    """Best-effort role inference from system prompt keywords."""
    system_text = ""
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "system":
            content = msg.get("content", "")
            system_text += (content if isinstance(content, str) else str(content)).lower()
    if not system_text:
        return "coder"
    best_role = "coder"
    best_count = 0
    for role, keywords in _ROLE_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in system_text)
        if count > best_count:
            best_count = count
            best_role = role
    return best_role


def _resolve_provider_name() -> str:
    """Return the configured AI provider name for attribution headers."""
    provider = os.environ.get("KAIROS_AI_BASE_URL", "")
    if not provider:
        return "specsmith-local"
    if "openai" in provider:
        return "openai"
    if "anthropic" in provider:
        return "anthropic"
    if "localhost" in provider or "127.0.0.1" in provider:
        return "local"
    return "byoe"


def _read_confidence_threshold(root: Path) -> float | None:
    cfg = root / ".specsmith" / "config.yml"
    if not cfg.is_file():
        return None
    try:
        import yaml as _yaml

        raw = _yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return None
    section = raw.get("epistemic") if isinstance(raw, dict) else None
    if not isinstance(section, dict):
        return None
    val = section.get("confidence_threshold")
    try:
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None
