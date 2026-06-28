# Requirements & Architecture Completeness Gap Report
Date: 2026-06-28
Scope scanned: `src/specsmith/`, `docs/requirements/*.yml`, `docs/tests/*.yml`
## 1) Feature inventory (major modules)
Top-level module families discovered in `src/specsmith/`:
- Root modules (`src/specsmith/*.py`): 75 files (CLI, governance, sync, migrations orchestration, VCS helpers, session/runtime management)
- `agent/`: 39 files (broker, orchestration, dispatch DAG/events, routing, permissions, tools, safety)
- `commands/`: 3 files (intelligence/issues/reporting command helpers)
- `compliance/`: 5 files (checker/evidence/reporter/regulations)
- `datasources/`: 8 files (citation + patent/publication datasource adapters)
- `epistemic/`: 5 files (belief/certainty/recovery/stress modeling)
- `esdb/`: 3 files (bridge/sqlite store/licensing)
- `eval/`: 2 files (evaluation runners/builtins)
- `gui/`: 11 files (desktop UI app/window/widgets/worker)
- `integrations/`: 9 files (aider/copilot/cursor/gemini/windsurf/claude adapters)
- `migrations/`: 11 files (m001–m010 + runner)
- `skills/`: 17 files (domain skill catalogs)
- `vcs/`: 4 files (GitHub/GitLab/Bitbucket integrations)
## 2) Features without explicit REQ coverage (and suggested REQ stubs)
Coverage check was performed by matching feature/module intents against requirement titles/descriptions across `docs/requirements/*.yml`.
Likely missing explicit REQ coverage:
- Datasource adapter layer (`src/specsmith/datasources/*`)  
  Suggested REQ title: **Datasource adapters must define retrieval contracts, resilience behavior, and citation normalization guarantees**
- GUI surface (`src/specsmith/gui/*`)  
  Suggested REQ title: **GUI commands and views must provide governed parity with core CLI state and error semantics**
- External IDE/tool integrations (`src/specsmith/integrations/*`)  
  Suggested REQ title: **Integration adapters must implement a uniform capability and error-handling contract**
- Plugin lifecycle surface (`specsmith plugin` command + plugin plumbing)  
  Suggested REQ title: **Plugin management must define install/list/remove and compatibility validation requirements**
## 3) REQs without tests (status = planned|implemented)
Cross-reference result (`requirement_id` in `docs/tests/*.yml`):
- **0 REQs** with zero tests.
- Every `planned` or `implemented` REQ currently has at least one TEST entry.
## 4) Planned REQs not yet implemented in `src/specsmith/` (backlog)
`planned` REQs reviewed for concrete implementation presence in `src/specsmith/`:
- `REQ-423` Governed benchmark agents must achieve 100% pass rate across all tasks/conditions
- `REQ-424` CI pipeline must produce zero CodeQL static analysis alerts on every run
- `REQ-425` Governed agents must autonomously resolve preflight needs_clarification without blocking
- `REQ-426` Benchmark harness completion token budget must allow reasoning models to produce tool calls
- `REQ-427` GovernanceBench metrics/report statistical and leaderboard outputs
Notes:
- These are benchmark/CI/harness-oriented and appear primarily script/pipeline scoped rather than fully implemented as core `src/specsmith/` runtime behavior.
- `REQ-428` through `REQ-431` have corresponding implementation signals in core modules (`sync.py`, `cli.py`, `governance_logic.py`) but are still marked `planned`.
## 5) CLI command coverage gaps (`src/specsmith/cli.py`)
Scanned all `@main.command(name=...)` entries (47 commands total). Non-trivial commands with no explicit REQ match in requirements titles/descriptions:
- `plugin`
- `pr`
- `ps`
Suggested REQ titles:
- **CLI plugin command must define governance-safe plugin lifecycle operations**
- **CLI pr command must define governed pull-request creation/update behavior**
- **CLI ps command must define active session/process listing semantics**
## 6) Test-stub additions for uncovered REQs
Requested action: add up to 15 missing TEST stubs for existing uncovered REQs.
Result:
- **0 TEST stubs added**, because no `planned|implemented` REQ lacked test linkage.
- Highest existing TEST ID observed during scan: `TEST-445`.
