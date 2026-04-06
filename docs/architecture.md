# Architecture — specsmith

## Overview

specsmith is an Applied Epistemic Engineering (AEE) toolkit targeting Windows, Linux, macOS. It scaffolds epistemically-governed projects, stress-tests requirements as BeliefArtifacts, runs cryptographically-sealed trace vaults, and orchestrates AI agents under formal AEE governance. Supports 33 project types (see REQ-CFG-002).

## Components

### CLI (`cli.py`)
Entry point. Click-based command group with 50+ commands (see REQ-CLI-001 through REQ-CLI-013). Includes: scaffold/governance commands, AEE commands (`stress-test`, `epistemic-audit`, `belief-graph`, `trace`, `integrate`), agentic client (`run`, `agent`), and extended commands (`auth`, `workspace`, `watch`, `patent`).

### Config (`config.py`)
Pydantic model validating scaffold.yml (see REQ-CFG-001). 33 project types enum (see REQ-CFG-002), platform enum, type labels, section refs. AEE fields: `enable_epistemic`, `epistemic_threshold`, `enable_trace_vault`.

### Scaffolder (`scaffolder.py`)
Jinja2 template renderer (see REQ-SCF-001 through REQ-SCF-006). Generates governance files, project structure, scripts. Delegates to VCS platforms and agent integrations. Epistemic governance templates for AEE project types (see REQ-SCF-EPI-001).

### Tool Registry (`tools.py`)
Data structure mapping 33 project types to verification tools (see REQ-TLR-001 through REQ-TLR-004). CI metadata per language (see REQ-TLR-002).

### Importer (`importer.py`)
Detection engine: walks directories, detects language/build/test/CI/governance (see REQ-IMP-001 through REQ-IMP-006). Infers ProjectType. Generates overlay files with cross-linked TEST/REQ stubs (see REQ-IMP-007).

### Exporter (`exporter.py`)
Generates compliance reports: REQ coverage matrix, audit summary, tool status, governance inventory (see REQ-EXP-001 through REQ-EXP-005).

### Auditor (`auditor.py`)
Health checks: file existence, REQ↔TEST coverage (see REQ-AUD-001 through REQ-AUD-008), ledger health, governance size, tool configuration, trace chain integrity.

### VCS Platforms (`vcs/`)
GitHub, GitLab, Bitbucket integrations (see REQ-VCS-001 through REQ-VCS-004). Tool-aware CI config generation, dependency management, status checks.

### Agent Integrations (`integrations/`)
7 adapters: Warp, Claude Code, Cursor, Copilot, Gemini, Windsurf, Aider (see REQ-INT-001 through REQ-INT-005).

## Epistemic Layer (`src/epistemic/` + `src/specsmith/agent/`)

### `epistemic` package (standalone library, zero deps)
Co-installed with specsmith. Canonical location for all AEE machinery.
- **`belief.py`** — `BeliefArtifact` dataclass (propositions, boundary, confidence, status, failure_modes, evidence)
- **`stress_tester.py`** — `StressTester` applies 8 adversarial challenge categories; emits `FailureMode` records; detects Logic Knots
- **`failure_graph.py`** — `FailureModeGraph` directed graph; `equilibrium_check()` and `logic_knot_detect()`; Mermaid rendering
- **`recovery.py`** — `RecoveryOperator` emits bounded `RecoveryProposal` objects; never auto-applies; ranked by severity
- **`certainty.py`** — `CertaintyEngine` scores C = base × coverage × freshness; weakest-link propagation through inferential links
- **`session.py`** — `AEESession` facade: `add_belief`, `accept`, `add_evidence`, `run`, `save`, `load`, `seal`
- **`trace.py`** — `TraceVault` SHA-256 append-only chain; STP-inspired decision sealing

### `specsmith.epistemic` (compatibility shim)
Re-exports all symbols from `epistemic`. Allows `from specsmith.epistemic import BeliefArtifact` for backward compat.

### Crypto Audit Chain (`ledger.py`)
`CryptoAuditChain` stores SHA-256 hashes per ledger entry in `.specsmith/ledger-chain.txt`. Each hash chains to the previous, making the ledger tamper-evident.

### Agentic Client (`src/specsmith/agent/`)
- **`core.py`** — `Message`, `Tool`, `CompletionResponse`, `ModelTier`, `BaseProvider` protocol
- **`providers/`** — Anthropic, OpenAI (+ Ollama via compat), Gemini, Ollama (stdlib-only). All optional extras.
- **`tools.py`** — 20 specsmith commands as native LLM-callable tools with epistemic contracts
- **`hooks.py`** — `HookRegistry` with Pre/PostTool, SessionStart, SessionEnd. Built-in H13 check.
- **`skills.py`** — SKILL.md loader with domain priority order
- **`runner.py`** — REPL loop, tool execution, streaming, session state, model routing
- **`profiles/`** — Built-in skill profiles: planner, verifier, epistemic-auditor

## Verification Tools

**Lint:** ruff check
**Typecheck:** mypy
**Test:** pytest
**Security:** pip-audit
**Format:** ruff format
