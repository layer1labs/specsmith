# AGENTS.md — specsmith

## Identity
- **Project**: specsmith
- **Type**: CLI tool (Python) + AEE library — Spec Section 17.3
- **Spec version**: 0.10.1
- **Language**: Python 3.10+
- **Platforms**: Windows, Linux, macOS
- **Role**: Governance engine for AI-assisted development. Governance backend for **Kairos** — the epistemically-governed terminal (BitConcepts/kairos).

## Purpose
Applied Epistemic Engineering toolkit for AI-assisted development. Treats belief systems
like code: codable, testable, deployable. Co-installs the `epistemic` standalone library.
Includes the Nexus runtime — a plain-English, governance-gated agentic REPL backed by
local vLLM (`l1-nexus`, Qwen2.5-Coder-32B). Serves as the governance
backend for the Kairos terminal project (BitConcepts/kairos) via `specsmith serve`.

## Quick Commands
- `py -m specsmith audit` — governance health check
- `py -m specsmith validate` — requirement/test consistency
- `py -m specsmith preflight "<utterance>"` — classify + approve a change
- `py -m specsmith verify` — post-change confidence check
- `py -m specsmith run` — Nexus REPL
- `py -m specsmith serve` — REST + WebSocket API server
- `py -m specsmith phase` — show AEE workflow phase
- `py -m specsmith compress` — archive LEDGER.md when over threshold
- `py -m specsmith migrate-project` — upgrade scaffold to current spec version
- `scripts/dev/lint.ps1` — ruff check + format
- `scripts/dev/test.ps1` — pytest
- `py -m mypy src/specsmith/` — typecheck

## Session Start
1. Read `LEDGER.md` — check last session state and open TODOs
2. Read `docs/governance/RULES.md` — hard rules and stop conditions
3. Run `py -m specsmith audit --project-dir .` — check governance health

## Workflow
All changes follow: **propose → check → execute → verify → record**.
- Every code change requires a ledger entry before execution
- Run `py -m specsmith preflight "<description>"` before any change
- Run `py -m specsmith verify` after changes, before marking complete
- Never commit without checking documentation (H14)

## File Registry
- `src/specsmith/` — CLI package
- `src/specsmith/agent/` — Nexus runtime (broker, repl, orchestrator, tools, safety)
- `src/specsmith/agent/broker.py` — natural-language intent classifier + preflight bridge
- `src/specsmith/agent/repl.py` — Nexus REPL with `/why` toggle and execution gate
- `src/specsmith/agent/orchestrator.py` — AG2 PlannerAgent/ShellAgent/CodeAgent pipeline
- `src/specsmith/agent/profiles.py` — agent profiles, routing table, BYOE endpoints
- `src/specsmith/paths.py` — canonical path constants (docs/specsmith.yml, docs/LEDGER.md …)
- `src/specsmith/safe_write.py` — append-only + backup-protected governance file writes
- `src/specsmith/serve.py` — HTTP/SSE server (specsmith serve)
- `src/specsmith/cli.py` — 50+ CLI commands
- `src/epistemic/` — standalone AEE library (canonical)
- `src/specsmith/epistemic/` — compatibility shim
- `src/specsmith/integrations/` — agent platform adapters (agent-skill)
- `src/specsmith/templates/` — Jinja2 scaffold templates
- `tests/` — 448 tests (pytest)
- **All governance files live in `docs/`** (except AGENTS.md at root):
- `docs/specsmith.yml` — project scaffold config (canonical; was scaffold.yml)
- `docs/ARCHITECTURE.md` — architecture reference
- `docs/REQUIREMENTS.md` — formal requirements (REQ-001..REQ-220, machine-authoritative)
- `docs/TESTS.md` — test specifications (machine-authoritative)
- `docs/LEDGER.md` — session ledger
- `.specsmith/` — machine state (config.yml, requirements.json, testcases.json, workitems.json)
- `docker-compose.yml` — vLLM l1-nexus model server
- `docs/site/` — Read the Docs user manual
- `docs/governance/` — modular governance rules

## Governance (Hard Rules)
- **H11** — Every loop/blocking wait must have a timeout, fallback exit, and diagnostic message
- **H12** — Windows multi-step automation goes into `.cmd` files, not inline shell invocations
- **H13** — Agent tools must declare epistemic contracts
- **H14** — Documentation updates are mandatory in the same commit as code changes
- AGENTS.md must remain under 200 lines
- All agent-invoked commands must have timeouts
- Record every session in LEDGER.md

## Tech Stack
- CLI: click | Templates: jinja2 | Config: pydantic + pyyaml | Output: rich
- Lint: ruff | Types: mypy (strict) | Tests: pytest + pytest-cov
- CI: GitHub Actions (3 OS × 3 Python) | Docs: specsmith.readthedocs.io
- Agent runtime: AG2 0.12.0 + Ollama / vLLM (BYOE endpoints)
- Kairos terminal (Rust, Warp BYOE fork — BitConcepts/kairos) — uses `specsmith serve` as governance backend

## AI Providers
| Role | Primary | Fallback chain |
|------|---------|----------------|
| coder* | openai/gpt-4.1 | gpt-4.1-mini → home-vllm (32B) → ollama 7b |
| architect | gemini/gemini-2.5-pro | openai/gpt-4o → ollama 32b |
| reviewer | gemini/gemini-2.5-flash | openai/gpt-4o-mini → ollama |
| editor | openai/gpt-4.1-mini | ollama 7b |
| researcher | gemini/gemini-2.5-pro | ollama 14b |
| tester | openai/gpt-4.1-mini | ollama 14b |
| classifier | ollama/qwen2.5:3b | (local only, zero cost) |

**API keys** (set once, stored in OS keyring):
- `py -m specsmith auth set openai` — prompts for `OPENAI_API_KEY`
- `py -m specsmith auth set google` — prompts for Gemini API key

**Home machine vLLM** (BYOE endpoint `home-vllm`):
- URL: `http://192.168.1.100:8000/v1` — update with actual IP via:
  `py -m specsmith endpoints add --id home-vllm --base-url http://<IP>:8000/v1 --replace`
- Runs Qwen2.5-Coder-32B-Instruct-GPTQ-Int8 via `docker-compose up` in this repo
- Activates automatically as coder fallback when the home machine is reachable

## Shorthand Commands
When user says `commit`: `py -m specsmith commit --project-dir .`
When user says `push`: `py -m specsmith push --project-dir .`
When user says `sync`: `py -m specsmith sync --project-dir .`
When user says `pr`: `py -m specsmith pr --project-dir .`
When user says `audit`: `py -m specsmith audit --project-dir .`
When user says `session-end`: `py -m specsmith session-end --project-dir .`

## Sister Repos
specsmith and kairos are **sister repos** — always located in the same parent directory.
Use relative paths to reference each other across machines (absolute paths vary):
- kairos: `../kairos/`

**Session management**: Both repos are currently governed from this specsmith chat session
and Warp context. When opening kairos, treat the specsmith session as the authoritative
agent context. This arrangement holds until kairos has its own stable Warp session/agent
setup. Changes to kairos made in this session are recorded in this specsmith LEDGER.md
until kairos carries its own session ledger independently.

## Credit Tracking
At session end, record token usage:
`py -m specsmith credits record --model <model> --provider <provider> --tokens-in <N> --tokens-out <N> --task "<desc>"`
Check budget: `py -m specsmith credits summary`
