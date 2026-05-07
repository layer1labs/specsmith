"""migrate_planned_requirements.py

One-shot migration: assign sequential IDs REQ-129..REQ-210 to the planned
architecture requirements from docs/PLANNED-REQUIREMENTS.md and update all
five governance files:

  REQUIREMENTS.md (root)
  TESTS.md (root)
  .specsmith/requirements.json
  .specsmith/testcases.json
  .specsmith/workitems.json

Safe to re-run: it aborts if REQ-129 already exists in requirements.json.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Planned requirement definitions  (source: docs/PLANNED-REQUIREMENTS.md)
# Each tuple: (domain_id, title, description)
# ---------------------------------------------------------------------------
PLANNED: list[tuple[str, str, str]] = [
    # OPS — Typed Execution Layer
    ("OPS-001", "Typed ProjectOperations Layer",
     "All tool handlers MUST use a typed `ProjectOperations` class for file, git/VCS, "
     "and search operations. Direct raw shell string assembly in tool handlers is prohibited."),
    ("OPS-002", "ProjectOperations File Operations via pathlib",
     "`ProjectOperations` MUST expose file operations (`read_file`, `write_file`, `list_dir`, "
     "`glob`, `search`) implemented via Python `pathlib`/`stdlib` — no subprocess calls."),
    ("OPS-003", "ProjectOperations Git/VCS Operations",
     "`ProjectOperations` MUST expose git/VCS operations (`status`, `log`, `diff`, `add`, "
     "`commit`, `push`, `create_branch`, `create_pr`) returning structured result objects."),
    ("OPS-004", "ProjectOperations Typed Result Objects",
     "All `ProjectOperations` methods MUST return a typed result containing at minimum "
     "`exit_code`, `stdout`, `stderr`, and `elapsed_ms`."),
    ("OPS-005", "executor.py run_tracked Preserved as Narrow Fallback",
     "The existing `executor.py` `run_tracked()` function MUST be preserved as a narrow "
     "fallback for commands that have no Python equivalent."),
    ("OPS-006", "ProjectOperations Cross-Platform",
     "`ProjectOperations` MUST be cross-platform (Windows, Linux, macOS) without "
     "platform-specific code branches in call sites."),

    # CMD — Harness Commands
    ("CMD-001", "Harness Slash Commands Package",
     "The `commands/` package MUST implement all priority harness slash commands available "
     "inside `specsmith run`."),
    ("CMD-002", "Session Management Slash Commands",
     "Session management commands MUST include: `/model`, `/provider`, `/tier`, `/status`, "
     "`/save`, `/clear`, `/compact`, `/export`."),
    ("CMD-003", "Multi-Agent Slash Commands",
     "Multi-agent commands MUST include: `/spawn`, `/team`, `/team-status`, `/worktree`."),
    ("CMD-004", "Continuous Learning Slash Commands",
     "Continuous learning commands MUST include: `/learn`, `/learn-eval`, `/instinct-status`, "
     "`/instinct-import`, `/instinct-export`."),
    ("CMD-005", "Evaluation Slash Commands",
     "Evaluation commands MUST include: `/eval define`, `/eval run`, `/eval report`, "
     "`/eval compare`."),
    ("CMD-006", "Orchestration Slash Commands",
     "Orchestration commands MUST include: `/multi-plan`, `/multi-execute`, `/route`."),
    ("CMD-007", "Hook Control Slash Commands",
     "Hook control commands MUST include: `/hooks-enable`, `/hooks-disable`, `/hook-profile`."),
    ("CMD-008", "MCP Slash Commands",
     "MCP commands MUST include: `/mcp-list`, `/mcp-add`, `/mcp-configure`."),
    ("CMD-009", "Security Slash Commands",
     "Security commands MUST include: `/security-scan`, `/audit-prompt`."),

    # MAS — Multi-Agent Spawning
    ("MAS-001", "AgentTool for Subagent Spawning",
     "The runner MUST provide an `AgentTool` (TaskTool) as a native LLM-callable tool that "
     "spawns subagent instances."),
    ("MAS-002", "Hub-and-Spoke and Agent-Teams Coordination",
     "Subagent spawning MUST support hub-and-spoke and agent-teams (peer-to-peer via filesystem "
     "mailbox) coordination modes."),
    ("MAS-003", "Filesystem Mailbox for Agent Teams",
     "The filesystem mailbox for agent teams MUST be stored at "
     "`.specsmith/teams/{team}/mailbox/{agent}.json`."),
    ("MAS-004", "Git Worktree Isolation for Subagents",
     "When `isolation=worktree`, the spawner MUST create a git worktree at "
     "`.specsmith/worktrees/{agent_id}/`."),
    ("MAS-005", "No Recursive Subagent Nesting",
     "Subagents MUST NOT be able to spawn further subagents (no recursive nesting)."),
    ("MAS-006", "Distilled Summary from Subagents",
     "The parent agent MUST receive a distilled summary from each subagent on completion, "
     "not the full transcript."),
    ("MAS-007", "Agent Teams Feature Flag Gated",
     "Agent team mode MUST be gated behind a feature flag (`SPECSMITH_AGENT_TEAMS=1`)."),

    # ORC — Orchestrator Meta-Agent
    ("ORC-001", "Orchestrator Meta-Agent for Routing",
     "specsmith MUST provide an orchestrator meta-agent for task classification, routing, "
     "and optimization — not execution."),
    ("ORC-002", "Orchestrator Defaults to Local Ollama",
     "The orchestrator MUST default to a small local Ollama model so orchestration incurs "
     "zero cloud API cost."),
    ("ORC-003", "Agent Registry with Capability Metadata",
     "The orchestrator MUST maintain an agent registry with type, model, provider, cost_tier, "
     "capabilities, avg_latency_ms, confidence."),
    ("ORC-004", "Orchestrator Emits One Structured Next-Action",
     "The orchestrator MUST emit exactly one structured next-action per task."),
    ("ORC-005", "Cost-Aware Routing",
     "The orchestrator MUST route cheap tasks to Ollama workers and complex tasks to cloud "
     "providers."),
    ("ORC-006", "Post-Session Self-Evaluation for Routing Thresholds",
     "The orchestrator MUST run a post-session self-evaluation to update routing thresholds."),

    # FLG — Feature Flag System
    ("FLG-001", "Feature Flag System for Tool Schema Visibility",
     "specsmith MUST implement a feature-flag system controlling which tool schemas are sent "
     "to the LLM."),
    ("FLG-002", "Feature Flags via Environment and scaffold.yml",
     "Feature flags MUST be configurable via environment variables and `scaffold.yml` under "
     "`agent.flags`."),
    ("FLG-003", "Agent Teams and Advanced Features Flag-Gated",
     "Agent teams, worktree isolation, KAIROS daemon mode, security scanner, and MCP tools "
     "MUST be flag-gated."),

    # LRN — Instinct / Continuous Learning System
    ("LRN-001", "Instinct Persistence System",
     "specsmith MUST implement an instinct persistence system in `src/specsmith/instinct.py`."),
    ("LRN-002", "Instinct Record Schema",
     "Each instinct record MUST contain: id, trigger_pattern, content, confidence, "
     "project_scope, created, last_used, use_count."),
    ("LRN-003", "SESSION_END Hook Extracts Candidate Instincts",
     "The `SESSION_END` hook MUST extract candidate instincts for user review."),
    ("LRN-004", "/learn Command Promotes Pattern to Instinct",
     "The `/learn` command MUST promote a pattern to an instinct with an initial confidence "
     "score."),
    ("LRN-005", "Instinct Confidence Updated on Application",
     "Instinct confidence MUST be updated based on application success/rejection."),
    ("LRN-006", "Instincts Importable and Exportable as Markdown",
     "Instincts MUST be importable and exportable as `.md` files."),
    ("LRN-007", "/instinct-status Displays Active Instincts",
     "`/instinct-status` MUST display all active instincts sorted by confidence."),

    # EDD — Eval Harness (Eval-Driven Development)
    ("EDD-001", "Eval Harness Module",
     "specsmith MUST implement an eval harness in `src/specsmith/eval/`."),
    ("EDD-002", "Eval Data Model",
     "The eval model MUST define: Task, Trial, Grader, Transcript, Outcome."),
    ("EDD-003", "Eval Tasks Stored as Markdown",
     "Tasks MUST be stored as Markdown at `.specsmith/evals/{feature}.md` with YAML "
     "frontmatter."),
    ("EDD-004", "Three Grader Types",
     "The harness MUST support CodeGrader, ModelGrader, and HumanFlag grader types."),
    ("EDD-005", "pass@k and pass^k Metrics",
     "The harness MUST compute `pass@k` and `pass^k` metrics."),
    ("EDD-006", "Git-Based Outcome Grading by Default",
     "Default grading MUST be git-based outcome grading, not execution-path assertion."),
    ("EDD-007", "/eval run --trials k",
     "`/eval run --trials k` MUST run k independent trials and report results."),
    ("EDD-008", "Capability vs Regression Eval Distinction",
     "The harness MUST distinguish capability evals from regression evals."),

    # MEM — Agent Memory Persistence
    ("MEM-001", "Cross-Session Agent Memory",
     "specsmith MUST implement cross-session agent memory in `src/specsmith/memory.py`."),
    ("MEM-002", "Agent Memory Structured JSON",
     "Agent memory MUST be structured JSON with accumulated patterns, preferred approaches, "
     "known project facts, and failure history."),
    ("MEM-003", "SESSION_START Hook Injects Memories into System Prompt",
     "The `SESSION_START` hook MUST inject relevant memories into the system prompt "
     "(token-budget-aware)."),
    ("MEM-004", "Agent Memory Compatible with Theia AI Convention",
     "Agent memory layout MUST be compatible with Theia AI's "
     "`~/.theia/agent-memory/` convention."),

    # HRK — Hook Runtime Controls
    ("HRK-001", "Runtime Hook Enable/Disable",
     "Hooks MUST be enable/disable-able at runtime without restarting the session."),
    ("HRK-002", "Hook Profiles via /hook-profile",
     "Hook profiles MUST be loadable via `/hook-profile`."),
    ("HRK-003", "New Hook Trigger Events",
     "New triggers: `SUBAGENT_START`, `SUBAGENT_STOP`, `CONTEXT_COMPACT`, `EVAL_PASS`, "
     "`EVAL_FAIL`."),
    ("HRK-004", "SUBAGENT_START Hook Can Block Spawn",
     "`SUBAGENT_START` MUST fire before spawning; a hook MAY block the spawn."),
    ("HRK-005", "SUBAGENT_STOP Hook on Completion",
     "`SUBAGENT_STOP` MUST fire when a subagent completes."),
    ("HRK-006", "CONTEXT_COMPACT Hook Before Trimming",
     "`CONTEXT_COMPACT` MUST fire before context trimming."),

    # SRV — Service / Daemon
    ("SRV-001", "specsmith serve Command",
     "specsmith MUST provide a `specsmith serve` command (already shipped in v0.7.0)."),
    ("SRV-002", "REST Endpoints for Session and Agent Management",
     "REST endpoints: `GET/POST /sessions`, `GET /agents`, `GET /instincts`, `GET /evals`, "
     "`POST /index`, `GET /health`."),
    ("SRV-003", "WebSocket Endpoint for Live Session I/O",
     "WebSocket endpoint at `/ws/session/{id}` for live session I/O using the existing "
     "JSONL event schema."),
    ("SRV-004", "EventSink Protocol for Stdout and WebSocket",
     "`AgentRunner._emit_event()` MUST use an `EventSink` protocol (`StdoutSink` / "
     "`WebSocketSink`)."),
    ("SRV-005", "Kairos Terminal Connects via HTTP/WebSocket",
     "The Kairos terminal MUST connect to `specsmith serve` over HTTP/WebSocket for all "
     "governance operations."),

    # RTR — Retrieval Upgrade
    ("RTR-001", "BM25 Retrieval Ranking",
     "`retrieval.py` MUST be upgraded from term-frequency to BM25 ranking using `rank_bm25`."),
    ("RTR-002", "File-Watcher Based Index Refresh",
     "The retrieval index MUST support file-watcher-based refresh."),
    ("RTR-003", "Token-Counted Retrieval Results",
     "Retrieval results MUST be token-counted before injection to prevent context budget "
     "overruns."),

    # MCP — MCP Management
    ("MCP-001", "MCP Server Configuration Templates",
     "specsmith MUST provide MCP server configuration templates via `/mcp-add` or "
     "`specsmith mcp add`."),
    ("MCP-002", "MCP Server Registry with Status",
     "The MCP server registry MUST list configured servers with status and tool surfaces."),
    ("MCP-003", "MCP Configuration in scaffold.yml",
     "MCP configuration MUST be storable in `scaffold.yml` under `agent.mcp_servers`."),

    # SEC — Security Scan
    ("SEC-001", "/security-scan Command",
     "specsmith MUST provide a `/security-scan` command running a dedicated security "
     "analysis agent."),
    ("SEC-002", "Security Scan Coverage",
     "The security scan MUST check dependency vulnerabilities, OWASP-style code patterns, "
     "and exposed secrets."),
    ("SEC-003", "/audit-prompt for Injection Analysis",
     "`/audit-prompt` MUST analyze a prompt string for injection vectors."),
    ("SEC-004", "Security Scan Results Stored Structurally",
     "Security scan results MUST be structured and stored at "
     "`.specsmith/security-reports/`."),

    # IDE — Theia IDE Application
    ("IDE-001", "specsmith-ide Theia Application",
     "A `specsmith-ide` application MUST be created on Eclipse Theia with `@theia/ai-core`, "
     "`@theia/ai-chat`, `@theia/ai-ide`."),
    ("IDE-002", "specsmith-ide Extension Packages",
     "specsmith-ide MUST ship: `@specsmith/ai-agents`, `@specsmith/epistemic-ui`, "
     "`@specsmith/eval-ui`, `@specsmith/service-client`."),
    ("IDE-003", "specsmith-ide WebSocket Connection to specsmith serve",
     "specsmith-ide MUST connect to `specsmith serve` over WebSocket."),
    ("IDE-004", "specsmith-ide Leverages Theia AI Native Tooling",
     "specsmith-ide MUST leverage Theia AI's existing MCP support, ShellExecutionTool, "
     "and agent skills system."),
    ("IDE-005", "specsmith-ide Electron Desktop Packaging",
     "specsmith-ide MUST be packageable as an Electron desktop application."),
]

START_ID = 130


def main() -> None:
    req_json_path = REPO / ".specsmith" / "requirements.json"
    test_json_path = REPO / ".specsmith" / "testcases.json"
    work_json_path = REPO / ".specsmith" / "workitems.json"
    req_md_path = REPO / "REQUIREMENTS.md"
    tests_md_path = REPO / "TESTS.md"

    # --- Abort if already migrated ---
    existing = json.loads(req_json_path.read_text(encoding="utf-8"))
    if any(r["id"] == f"REQ-{START_ID:03d}" for r in existing):
        print(f"REQ-{START_ID:03d} already exists — migration already applied, aborting.")
        return

    existing_tests = json.loads(test_json_path.read_text(encoding="utf-8"))
    existing_work = json.loads(work_json_path.read_text(encoding="utf-8"))

    new_reqs: list[dict] = []
    new_tests: list[dict] = []
    new_work: list[dict] = []
    req_md_lines: list[str] = []
    test_md_lines: list[str] = []

    for i, (domain_id, title, description) in enumerate(PLANNED):
        n = START_ID + i
        req_id = f"REQ-{n:03d}"
        test_id = f"TEST-{n:03d}"
        work_id = f"WORK-{n:03d}"

        # JSON entries
        new_reqs.append({
            "id": req_id,
            "title": title,
            "description": description,
            "source": f"docs/PLANNED-REQUIREMENTS.md ({domain_id})",
            "status": "defined",
        })
        new_tests.append({
            "id": test_id,
            "title": title,
            "description": description,
            "requirement_id": req_id,
            "type": "unit",
            "verification_method": "evaluator",
            "input": {},
            "expected_behavior": {},
            "confidence": 1.0,
        })
        new_work.append({
            "id": work_id,
            "requirement_id": req_id,
            "test_case_ids": [test_id],
            "status": "pending",
            "attempts": 0,
            "max_attempts": 3,
            "priority": "medium",
        })

        # Markdown entries
        req_md_lines.append(f"\n## {n}. {title}")
        req_md_lines.append(f"- **ID:** {req_id}")
        req_md_lines.append(f"- **Title:** {title}")
        req_md_lines.append(f"- **Description:** {description}")
        req_md_lines.append(f"- **Source:** docs/PLANNED-REQUIREMENTS.md ({domain_id})")
        req_md_lines.append("- **Status:** defined")

        test_md_lines.append(f"\n## {test_id}. {title}")
        test_md_lines.append(f"- **ID:** {test_id}")
        test_md_lines.append(f"- **Title:** {title}")
        test_md_lines.append(f"- **Description:** {description}")
        test_md_lines.append(f"- **Requirement ID:** {req_id}")
        test_md_lines.append("- **Type:** unit")
        test_md_lines.append("- **Verification Method:** evaluator")
        test_md_lines.append("- **Input:** {}")
        test_md_lines.append("- **Expected Behavior:** {}")
        test_md_lines.append("- **Confidence:** 1.0")

    # Write JSON files
    req_json_path.write_text(
        json.dumps(existing + new_reqs, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    test_json_path.write_text(
        json.dumps(existing_tests + new_tests, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    work_json_path.write_text(
        json.dumps(existing_work + new_work, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # Append to Markdown files
    req_md_path.write_text(
        req_md_path.read_text(encoding="utf-8") + "\n" + "\n".join(req_md_lines) + "\n",
        encoding="utf-8",
    )
    tests_md_path.write_text(
        tests_md_path.read_text(encoding="utf-8") + "\n" + "\n".join(test_md_lines) + "\n",
        encoding="utf-8",
    )

    total = len(PLANNED)
    end_id = START_ID + total - 1
    print(f"Migration complete: REQ-{START_ID:03d}..REQ-{end_id:03d} ({total} requirements)")
    print(f"Updated: REQUIREMENTS.md, TESTS.md, requirements.json, testcases.json, workitems.json")


if __name__ == "__main__":
    main()
