# CLI Commands

specsmith has 50+ commands. Every command that operates on a project accepts `--project-dir PATH` (default: current directory).

## `specsmith preflight`

Classify a natural-language utterance under Specsmith governance and emit a deterministic JSON payload (REQ-085, REQ-088, REQ-092, REQ-093, REQ-099, REQ-100).

```bash
specsmith preflight "fix the cleanup dry-run regression" --json
specsmith preflight "delete the dist directory" --json
specsmith preflight "refactor the broker" --stress --verbose --json
```

**Options:**

- `--project-dir PATH` \u2014 project root (default: `.`).
- `--json` \u2014 emit the decision as JSON on stdout.
- `--verbose` \u2014 include a plain-language narration block alongside the JSON payload.
- `--stress` \u2014 run an AEE stress-test pass over matched requirements; surfaces critical failures as `stress_warnings`.

**JSON payload keys:** `decision` (one of `accepted`, `needs_clarification`, `blocked`, `rejected`), `work_item_id`, `requirement_ids`, `test_case_ids`, `confidence_target`, `instruction`, `intent`. Optional: `stress_warnings`, `narration`.

**Exit codes (REQ-092):** `0` for `accepted`, `2` for `needs_clarification`, `3` for `blocked`/`rejected`. The JSON payload still prints to stdout for non-zero exits so CI scripts can branch on intent without re-parsing the entire output.

**Ledger side-effects:** when the decision is `accepted` and `LEDGER.md` exists, the CLI appends a `preflight` entry tagged with `REQ-085` plus the resolved `requirement_ids`. Brand-new `work_item_id` values also get a distinct `work_proposal` entry tagged with `REQ-044,REQ-085` (REQ-099).

## `specsmith verify`

Verify a Specsmith-governed change set per the verification input contract (REQ-027, REQ-097).

```bash
echo '{"diff":"...","files_changed":["src/foo.py"],"test_results":{"passed":5,"failed":0}}' | \
  specsmith verify --stdin

specsmith verify --diff change.patch --tests test-results.json --logs run.log
```

**Options:**

- `--project-dir PATH` \u2014 project root (default: `.`).
- `--stdin` \u2014 read the verification input as a single JSON object from stdin.
- `--diff PATH` / `--tests PATH` / `--logs PATH` \u2014 file-based alternatives to `--stdin`.
- `--changed a,b,c` \u2014 comma-separated list of changed file paths.
- `--work-item-id ID` \u2014 optional work item id to bind the verification to.

**JSON payload keys:** `equilibrium`, `confidence`, `summary`, `files_changed`, `test_results`, `retry_strategy` (one of `narrow_scope`, `expand_scope`, `fix_tests`, `rollback`, `stop`, or empty when equilibrium is reached), `work_item_id`, `retry_budget`, `confidence_threshold`.

**Exit codes (REQ-097):** `0` when equilibrium is reached and confidence \u2265 the configured threshold; `2` when retry is recommended; `3` when stop-and-align is required.

## Agentic REPL (`specsmith run`)

```bash
specsmith run                            # AEE-integrated REPL (auto-detects provider)
specsmith run --provider ollama          # force local Ollama
specsmith run --task "fix lint errors"  # non-interactive single task
```

The broker classifies intent, infers scope from `docs/REQUIREMENTS.md`, calls `specsmith
preflight`, and gates execution: only `accepted` decisions proceed. Toggle `/why` in the REPL
to reveal the underlying `work_item_id`, `requirement_ids`, and `test_case_ids` Specsmith assigned.
## `specsmith chat`

Run a single chat turn that emits the JSONL block protocol on stdout (REQ-112, REQ-113, REQ-114, REQ-115, REQ-116). This is the wire format consumed by IDE clients (e.g. the VS Code extension's `ChatPanel`).

```bash
specsmith chat "add a hello world greeter" --project-dir .
specsmith chat "refactor the broker" --profile safe --interactive --decision-timeout 120
```

**Options:**

- `--project-dir PATH` \u2014 project root (default: `.`).
- `--session-id ID` \u2014 reuse an existing session id; persisted turns under `.specsmith/sessions/<id>/turns.jsonl` are replayed as prior context (REQ-120).
- `--parent-session ID` \u2014 mark this run as a sub-session of the given parent (REQ-125).
- `--profile {safe,standard,yolo}` \u2014 permission tier (REQ-115). `safe` emits a `tool_request` event and waits before executing.
- `--comment TEXT` \u2014 reviewer comment fed into the next retry (REQ-116).
- `--json-events` \u2014 emit JSONL block events (on by default).
- `--interactive` \u2014 read decision events from stdin (`tool_decision` and `diff_decision`). Used by IDE consumers to drive safe-mode approval and inline diff review.
- `--decision-timeout SECONDS` \u2014 maximum wait for a stdin decision (default `120.0`).

**Event protocol (selected types):** `block_start` / `block_complete` (kinds: `plan`, `message`, `tool_call`, `tool_result`, `diff`), `token`, `tool_call`, `tool_request`, `tool_result`, `plan_step`, `task_complete`. Each event is a single JSON object on its own line.

**Stdin decision protocol** (only with `--interactive`):

```
{"type":"tool_decision","decision":"approve"}
{"type":"tool_decision","decision":"deny","reason":"unsafe path"}
{"type":"diff_decision","decision":"accept"}
{"type":"diff_decision","decision":"reject","comment":"use uppercase greeting"}
```

A non-accept `diff_decision` with a `comment` field is folded into the persisted turn's `reviewer_comment` so the next harness retry can consume it (REQ-116).

**Real LLM backend.** When `chat` runs, the command first attempts a real model turn through `specsmith.agent.chat_runner`, which selects the first available provider in this order: a local Ollama daemon (default `http://127.0.0.1:11434`, model `qwen2.5:7b`), then the `anthropic`, `openai`, and `google-genai` SDKs (each gated on the matching `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GOOGLE_API_KEY` env var and the SDK being installed). If no provider is reachable the runner returns ``None`` and the command falls back to a deterministic stub so tests and offline workflows stay green. Set `SPECSMITH_DISABLE_REAL_CHAT=1` to force the deterministic path.
## `specsmith skill`

Discover and install built-in agent skills.

```bash
specsmith skill list
specsmith skill search verifier
specsmith skill install diff-reviewer --project-dir ./my-project
```

**Subcommands:**

- `list` \u2014 print the built-in catalog (`verifier`, `planner`, `diff-reviewer`, `onboarding-coach`, `release-pilot`).
- `search QUERY` \u2014 fuzzy-match the catalog by slug, name, or description.
- `install SLUG` \u2014 write the skill's `SKILL.md` to `.agents/skills/<slug>/SKILL.md` so the local Nexus runtime picks it up at session start. Existing files are preserved unless `--force` is passed.

## `specsmith init`

Scaffold a new governed project.

```bash
specsmith init                                    # Interactive prompts
specsmith init --config scaffold.yml              # From config file
specsmith init --config scaffold.yml --guided     # + architecture definition
specsmith init --config scaffold.yml --no-git     # Skip git init
specsmith init --output-dir /path/to/parent       # Custom output location
```

**Options:**

- `--config PATH` — Path to scaffold.yml. If omitted, runs interactive prompts for project name, type, platforms, VCS, branching, and integrations.
- `--output-dir PATH` — Parent directory for the new project (default: `.`). The project is created as a subdirectory named after `name` in the config.
- `--no-git` — Skip running `git init` in the new project.
- `--guided` — After scaffolding, prompts for component names and generates REQUIREMENTS.md with `REQ-{COMPONENT}-001/002` stubs, TESTS.md with linked tests, and architecture.md with component descriptions.

**What it generates:** AGENTS.md, LEDGER.md, modular governance, project docs, type-specific directories, CI config, dependency management, agent integration files, scripts, and scaffold.yml.

**Exit codes:** 0 on success, 1 if the output directory already exists and is not empty.

## `specsmith import`

Adopt an existing project by detecting its structure and generating governance overlay.

```bash
specsmith import --project-dir ./my-project
specsmith import --project-dir ./my-project --force
specsmith import --project-dir ./my-project --guided
```

**Options:**

- `--project-dir PATH` — Project root to analyze (default: `.`).
- `--force` — Overwrite existing governance files. Without this flag, existing files (AGENTS.md, LEDGER.md, etc.) are preserved.
- `--guided` — After generating overlay, prompts for component names and generates richer REQ/TEST stubs.

**Merge behavior:** Import only generates files that don't already exist. This means you can safely run `import` on a project that already has a hand-crafted AGENTS.md — it will add the missing pieces (scaffold.yml, docs/governance/, REQUIREMENTS.md) without touching what's already there.

**Detection:** Language (by file extension counts), build system (pyproject.toml, Cargo.toml, etc.), test framework, CI platform, VCS remote, modules, entry points, test files, existing governance. See [Importing Projects](importing.md) for full details.

## `specsmith sync`

Sync `.specsmith/` machine-state JSON from `docs/` Markdown (REQ-003).

```bash
specsmith sync                            # regenerate requirements.json + testcases.json
specsmith sync --check                    # CI: exit 1 if out of sync, no writes
specsmith sync --json                     # emit result as JSON
```

Markdown files in `docs/` are always the source of truth; the JSON files are a derived cache
that tools like `preflight` and `verify` read for fast machine-state lookup. Run `sync` after
any edit to `docs/REQUIREMENTS.md` or `docs/TESTS.md`.

## `specsmith governance-serve`

Start the governance REST API server for Kairos (REQ-001 Kairos side).

```bash
specsmith governance-serve --port 7700   # default port for Kairos integration
specsmith governance-serve --port 7700 --project-dir ./my-project
```

Endpoints:
- `GET  /health`    — liveness probe; returns `{"status": "ok", "version": "..."}`
- `POST /preflight` — governance gate; returns a PreflightDecision JSON
- `POST /verify`    — post-change verification; returns a VerifyResult JSON

This is **separate** from `specsmith serve` (port 8421, chat/SSE for IDE clients). Architecture
invariant I2 enforced: host must be localhost (127.0.0.1 / ::1). External hosts are rejected.

## `specsmith agent permissions`

Show the active least-privilege permission profile for this project (REG-012).

```bash
specsmith agent permissions                  # human-readable profile
specsmith agent permissions --json           # JSON summary
specsmith agent permissions-check git_push   # check specific tool (exit 0=ok, 3=denied)
specsmith agent permissions-check git_push --no-log  # dry-run, no ledger write
```

Configure in `docs/SPECSMITH.yml`:
```yaml
agent:
  permissions:
    preset: standard       # read_only | standard | extended | admin
    allow: [read_file, write_file, run_shell, git_status, git_diff]
    deny:  [git_commit, git_push, git_create_pr, open_url]
```

Denied tool attempts are logged to `docs/LEDGER.md` as `permission-denied` entries (REG-012 audit trail).

## `specsmith audit`

Run drift detection and health checks.

```bash
specsmith audit --project-dir ./my-project
specsmith audit --fix --project-dir ./my-project
```

**Checks performed:**

1. **Required files** — AGENTS.md and LEDGER.md must exist
2. **Modular governance** — If AGENTS.md exceeds 200 lines, docs/governance/*.md must exist
3. **REQ↔TEST coverage** — Every requirement ID in REQUIREMENTS.md must have a `Covers:` reference in TESTS.md
4. **Ledger health** — LEDGER.md must be under 500 lines; open TODOs must be under 20
5. **Governance size** — Individual governance files must not exceed their line thresholds
6. **Tool configuration** — CI config must reference the expected verification tools for the project type (reads scaffold.yml to determine type)

**`--fix` auto-repairs:**

- Creates stub AGENTS.md and LEDGER.md if missing
- Creates stub modular governance files if missing
- Compresses oversized ledger via `specsmith compress`
- Generates CI config from the tool registry if missing or incomplete

**Exit codes:** 0 if healthy, 1 if issues found.

## `specsmith validate`

Check governance file consistency.

```bash
specsmith validate --project-dir ./my-project
```

**Checks:** scaffold.yml structure and required fields, AGENTS.md local file references resolve, requirement ID uniqueness across REQUIREMENTS.md, architecture.md references at least one requirement.

**Exit codes:** 0 if valid, 1 if issues found.

## `specsmith compress`

Archive old ledger entries when LEDGER.md grows too large.

```bash
specsmith compress --project-dir ./my-project
specsmith compress --threshold 300 --keep-recent 20 --project-dir ./my-project
```

**Options:**

- `--threshold INT` — Only compress if LEDGER.md exceeds this many lines (default: 500).
- `--keep-recent INT` — Keep the N most recent entries in LEDGER.md (default: 10).

Archived entries are moved to `docs/ledger-archive.md`. This is non-destructive — the full history is preserved, just split across files.

## `specsmith upgrade`

Update governance files to a newer spec version.

```bash
specsmith upgrade --spec-version 0.3.0 --project-dir ./my-project
```

Re-renders all governance templates (docs/governance/*.md) using the current scaffold.yml config and the new version. Updates scaffold.yml with the new `spec_version`. Does not touch AGENTS.md, LEDGER.md, or project source code.

## `specsmith status`

Show CI, alerts, and PR status from the VCS platform CLI.

```bash
specsmith status --project-dir ./my-project
```

**Requires:** `gh` (GitHub), `glab` (GitLab), or `bb` (Bitbucket) CLI installed and authenticated. Reads `scaffold.yml` to determine which platform to use.

**Shows:** Latest CI run status, Dependabot/security alert count, open PR/MR count.

## `specsmith diff`

Compare current governance files against what specsmith templates would generate.

```bash
specsmith diff --project-dir ./my-project
```

For each governance file, reports: ✓ (matches template), ~ (differs from template), or ✗ (missing). Useful after manual edits to see what's drifted from the spec.

## `specsmith export`

Generate a compliance and coverage report.

```bash
specsmith export --project-dir ./my-project                    # Print to terminal
specsmith export --project-dir ./my-project --output report.md # Save to file
```

**Report sections:** Project summary, verification tools, REQ↔TEST coverage matrix (with percentage), audit summary (pass/fail/fixable), recent git activity (last 10 commits, contributors), governance file inventory.

See [Export & Compliance](export.md) for a detailed breakdown.

## `specsmith doctor`

Check if the verification tools for your project type are installed locally.

```bash
specsmith doctor --project-dir ./my-project
```

Reads scaffold.yml, looks up the ToolSet for the project type, and checks if each tool is available on PATH. Reports installed (with version) or missing for each tool across all 7 categories (lint, typecheck, test, security, build, format, compliance).

See [Doctor](doctor.md) for details.

## `specsmith architect`

Generate or enrich architecture documentation by scanning the project and interviewing you.

```bash
specsmith architect --project-dir ./my-project
specsmith architect --project-dir ./my-project --non-interactive
```

**What it does:** Scans for modules, languages, dependencies, git history, and existing architecture docs. In interactive mode, prompts for component names, purposes, interfaces, data flow, and deployment notes. Generates a rich `docs/ARCHITECTURE.md`.

**Options:**

- `--non-interactive` — Skip prompts, auto-generate from scan data only.

## `specsmith self-update`

Update specsmith itself.

```bash
specsmith self-update                       # Auto-detect channel
specsmith self-update --channel dev          # Force dev channel
specsmith self-update --version 0.1.3        # Pin specific version
```

Auto-detects whether you're on stable or dev and upgrades accordingly.

## `specsmith credits`

AI credit/token spend tracking and analysis.

```bash
specsmith credits summary                                # Spend overview
specsmith credits summary --month 2026-04                # Monthly view
specsmith credits record --model claude-sonnet \          # Record usage
  --provider anthropic --tokens-in 5000 --tokens-out 2000 --task "import"
specsmith credits report --output credits-report.md      # Markdown report
specsmith credits analyze                                # Optimization insights
specsmith credits budget --cap 50 --alert-pct 80         # Set budget
```

**Subcommands:**

- `summary` — Aggregate spend by model, provider, task. Shows budget alerts.
- `record` — Log a credit usage entry (model, provider, tokens, task, cost).
- `report` — Generate markdown credit report.
- `analyze` — Detect model inefficiency, token waste, cost trends. Recommendations.
- `budget` — View/set monthly cap, alert threshold, watermark levels.

Credit data stored locally at `.specsmith/credits.json` (gitignored).

## `specsmith exec`

Execute a command with PID tracking and timeout enforcement.

```bash
specsmith exec "pytest tests/" --timeout 300
specsmith exec "make build" --timeout 120 --project-dir ./my-project
```

**Options:**

- `--timeout INT` — Maximum seconds to wait (default: 120). Process is killed when deadline fires.
- `--project-dir PATH` — Project root (default: `.`). PID and log files go under `.specsmith/`.

Tracks the process in `.specsmith/pids/<pid>.json` and logs stdout/stderr to `.specsmith/logs/`. Works on Windows (taskkill), Linux, and macOS (SIGTERM → SIGKILL).

**Exit codes:** Mirrors the child process exit code. Returns 124 on timeout.

## `specsmith ps`

List tracked running processes.

```bash
specsmith ps --project-dir ./my-project
```

Shows PID, time remaining to timeout, and command for every tracked process. Prunes stale PID files for processes that already exited.

## `specsmith abort`

Kill tracked process(es).

```bash
specsmith abort --pid 12345
specsmith abort --all
```

**Options:**

- `--pid INT` — Kill a specific tracked PID.
- `--all` — Kill every tracked process.

Without `--pid` or `--all`, prints the current process list and instructions.

## `specsmith commit`

Governance-aware commit: checks ledger, optionally audits, then commits.

```bash
specsmith commit -m "feat: add export command"
specsmith commit --no-audit --auto-push
```

**Options:**

- `-m / --message TEXT` — Override the commit message (default: last ledger entry heading).
- `--no-audit` — Skip the pre-commit audit check.
- `--auto-push` — Push after a successful commit.

Warns if `LEDGER.md` was not updated since the last commit.

## `specsmith push`

Push the current branch with safety checks.

```bash
specsmith push
specsmith push --force
```

**Options:**

- `--force` — Skip branch-protection checks.

## `specsmith pull`

Pull latest and warn about governance conflicts.

```bash
specsmith pull --project-dir ./my-project
```

Runs `git pull` and checks for conflicts in governance files (AGENTS.md, LEDGER.md, docs/governance/*).

## `specsmith branch`

Strategy-aware branch management.

```bash
specsmith branch create feature/my-feature
specsmith branch list
```

**Subcommands:**

- `create NAME` — Create a branch following the configured branching strategy (gitflow / trunk-based / GitHub Flow). Reads strategy from `scaffold.yml`.
- `list` — List branches with their role annotation (main, develop, feature, hotfix, etc.).

## `specsmith pr`

Create a PR with governance context in the body.

```bash
specsmith pr --title "Add export command"
specsmith pr --draft
```

**Options:**

- `--title TEXT` — PR title.
- `--draft` — Create as a draft PR.

Appends the first 2000 characters of `specsmith export` output to the PR body. Requires `gh` (GitHub), `glab` (GitLab), or `bb` (Bitbucket) CLI.

## `specsmith session-end`

Run the end-of-session checklist.

```bash
specsmith session-end --project-dir ./my-project
```

Checks: uncommitted changes, ledger updated, open TODOs count, audit health. Reports items that need action before ending the session.

## `specsmith update`

Check for updates and optionally install the latest version + migrate the project.

```bash
specsmith update
specsmith update --check            # Check only, don't install
specsmith update --yes              # Skip confirmation prompt
```

**Options:**

- `--check` — Print available version and exit without installing.
- `--yes` — Auto-confirm update and migration prompts.

Auto-detects channel (stable vs dev) from the installed version. Runs `migrate-project` if the project scaffold needs migration after the update.

## `specsmith apply`

Regenerate CI and agent integration files from the current `scaffold.yml`.

```bash
specsmith apply --project-dir ./my-project
```

Re-renders GitHub Actions / GitLab CI / Bitbucket Pipelines config and agent integration files (CLAUDE.md, GEMINI.md, `.agents/skills/SKILL.md`, etc.). Safe: never overwrites AGENTS.md, LEDGER.md, or user-authored docs.

## `specsmith migrate-project`

Migrate project scaffold to the current specsmith version.

```bash
specsmith migrate-project --project-dir ./my-project
specsmith migrate-project --dry-run
```

**Options:**

- `--dry-run` — Show what would change without writing.

## `specsmith release`

Bump the version string everywhere and scan for stale references.

```bash
specsmith release 0.3.0
specsmith release 0.3.0 --project-dir ./my-project
```

Updates version in `pyproject.toml`, `Cargo.toml`, `package.json`, `src/**/__init__.py`, README badges, and CHANGELOG. Scans for references to the old version that may need updating. Prints the next manual steps (CHANGELOG, git tag, push).

## `specsmith verify-release`

Post-release smoke check: verify PyPI, RTD, and GitHub release are live.

```bash
specsmith verify-release
```

Checks that the installed version is published on PyPI, that the RTD site is reachable, and that the GitHub Release tag exists. Requires `gh` CLI for the GitHub check.

## `specsmith ledger`

Structured ledger management.

```bash
specsmith ledger add "Implemented export command" --type feature --reqs REQ-CLI-005
specsmith ledger list --since 2026-03-01
specsmith ledger stats
```

**Subcommands:**

- `add DESCRIPTION` — Append a structured entry. Options: `--type` (task/feature/fix/migration), `--author`, `--reqs` (comma-separated REQ IDs).
- `list` — List ledger entries. Option: `--since YYYY-MM-DD`.
- `stats` — Show entry count and per-author breakdown.

## `specsmith req`

Requirements management.

```bash
specsmith req list
specsmith req add REQ-CLI-010 --component cli --priority high --description "Add export"
specsmith req trace
specsmith req gaps
specsmith req orphans
```

**Subcommands:**

- `list` — List all requirements with status, priority, and description.
- `add REQ_ID` — Add a new requirement stub to `docs/REQUIREMENTS.md`.
- `trace` — Show REQ → TEST traceability matrix (which tests cover each requirement).
- `gaps` — List requirements that have no test coverage.
- `orphans` — List tests that reference non-existent requirement IDs.

## `specsmith plugin`

List installed specsmith plugins.

```bash
specsmith plugin
```

Plugins extend project types and tool registries. They register via `pyproject.toml` entry points under `specsmith.types`. Shows each plugin's load status and any import errors.

## `specsmith serve`

Start the local API server for the web dashboard (placeholder).

```bash
specsmith serve --port 8910
```

Not yet fully implemented. See project roadmap for the planned REST API.

## `specsmith credits limits`

Manage persisted per-model RPM/TPM rate-limit profiles.

```bash
specsmith credits limits list
specsmith credits limits set --provider openai --model gpt-4o --rpm 500 --tpm 30000000
specsmith credits limits status --provider openai --model gpt-4o
specsmith credits limits defaults
specsmith credits limits defaults --install
```

**Subcommands:**

- `list` — Print all locally saved profiles (provider, model, RPM, TPM, utilization target, concurrency).
- `set` — Create or replace a local profile. Options: `--provider`, `--model`, `--rpm`, `--tpm`, `--target FLOAT` (default 0.70), `--concurrency INT` (default 1).
- `status` — Show the rolling-window snapshot for a model: requests and tokens used in the current 60-second window, concurrency, moving averages.
- `defaults` — List built-in profiles for common OpenAI, Anthropic, and Google models. Use `--install` to merge them into the local project config (existing overrides are preserved).

Profiles are stored at `.specsmith/model-rate-limits.json` (gitignored). The scheduler uses these to pace requests before dispatch and to apply exponential backoff after a 429.

## `specsmith phase`

Track and advance the AEE workflow phase. Phase is persisted as `aee_phase` in `scaffold.yml`.

```bash
specsmith phase                     # show current phase and checklist (alias: phase show)
specsmith phase show                # show current phase, readiness %, and recommended commands
specsmith phase next                # advance to next phase (checks prerequisites)
specsmith phase next --force        # advance without checks
specsmith phase set requirements    # explicitly set phase
specsmith phase set implementation --force  # set without checks
specsmith phase list                # list all 7 phases in order
specsmith phase status              # one-line status for CI/IDE: 'requirements 📋 Requirements 60%'
```

**Phases:**

1. `inception` 🌱 — Governance scaffold, AGENTS.md, project type established
2. `architecture` 🏗 — ARCHITECTURE.md, components, key decisions sealed
3. `requirements` 📋 — REQUIREMENTS.md populated, stress-tested, equilibrium reached
4. `test_spec` ✅ — TESTS.md covers all P1 requirements (≥80%)
5. `implementation` ⚙ — Development cycle: code, commit, audit, ledger
6. `verification` 🔬 — Epistemic audit passes, trace vault sealed
7. `release` 🚀 — CHANGELOG updated, tag created, compliance report filed

Each phase has a checklist of file/command prerequisites. `phase next` runs the checklist before advancing.

## `specsmith ollama`

Manage Ollama local LLM models. Requires Ollama running at `localhost:11434`.

```bash
specsmith ollama list                       # list installed models
specsmith ollama available                  # catalog with VRAM filter and install status
specsmith ollama available --task code      # filter by task type
specsmith ollama gpu                        # detect GPU and VRAM tier
specsmith ollama pull qwen2.5:14b          # download a model (streams progress)
specsmith ollama suggest requirements      # suggest best installed models for a task
```

**Task types for `available` and `suggest`:** `code`, `requirements`, `architecture`, `chat`, `analysis`, `reasoning`

**Curated catalog (9 models):**

| Model | VRAM | Best for |
|-------|------|----------|
| llama3.2:latest | 2 GB | chat, quick tasks |
| mistral:latest | 4.5 GB | chat, writing |
| qwen2.5:7b | 5 GB | coding, analysis |
| qwen2.5-coder:7b | 4.8 GB | code generation |
| gemma3:12b | 8 GB | general, analysis |
| phi4:latest | 9 GB | reasoning, requirements |
| qwen2.5:14b | 9 GB | AEE workflows (recommended) |
| deepseek-coder-v2 | 11 GB | code generation, review |
| qwen2.5:32b | 20 GB | complex reasoning |

## `specsmith workspace`

Manage multi-project workspaces.

```bash
specsmith workspace init my-org ./backend ./frontend ./shared-lib
specsmith workspace audit --dir ./my-org
specsmith workspace export --dir ./my-org --output compliance.md
```

**Subcommands:**

- `init NAME [PROJECTS...]` — Create `workspace.yml`. `PROJECTS` are relative paths.
- `audit` — Run `specsmith audit` across all projects and report aggregate health.
- `export` — Generate combined compliance report for all projects.

## `specsmith --version`

```bash
specsmith --version
# specsmith, version {{ version }}
```

## `specsmith channel` (REQ-248)

Manage the specsmith update channel. The channel controls whether `specsmith self-update` targets stable releases or dev/pre-release builds. Persisted to `~/.specsmith/channel`.

```bash
specsmith channel get              # show effective channel + source
specsmith channel get --json       # JSON: {"channel": "stable", "source": "version"}
specsmith channel set stable       # pin to stable releases
specsmith channel set dev          # opt in to dev/pre-release builds
specsmith channel clear            # remove persisted preference (revert to auto-detect)
```

**Source values:** `user` when a preference file exists; `version` when inferred from the installed version string (`.devN` suffix ? dev, otherwise stable).

## `specsmith esdb` � Extended ESDB Lifecycle (REQ-249..253)

Full lifecycle management for the ChronoMemory Epistemic State Database. All new commands accept `--json` for machine-readable output.

```bash
# Existing commands
specsmith esdb status [--json]           # status and record counts
specsmith esdb migrate                   # validate flat JSON ? ESDB migration
specsmith esdb replay                    # verify WAL chain integrity

# New commands (REQ-249..253)
specsmith esdb export [--output PATH] [--json]
  # Dump all records to <project>/.specsmith/esdb_export.json (or --output).
  # Payload: {esdb_version, backend, record_count, requirements[], testcases[]}

specsmith esdb import <source> [--json]
  # Validate a JSON export and stage it at .specsmith/esdb_import.json.
  # Exits non-zero for missing or invalid files.

specsmith esdb backup [--dir DIR] [--json]
  # Create a timestamped snapshot at .specsmith/backups/esdb_backup_<UTC>.json.
  # Payload includes: esdb_version, timestamp, backend, record_count, requirements[], testcases[]

specsmith esdb rollback [--steps N] [--json]
  # Report WAL events that would be undone (stub mode � does not modify state).
  # JSON: {ok, steps_requested, records_before, note}

specsmith esdb compact [--json]
  # Request WAL compaction (stub mode). JSON: {ok, backend, records, note}
```

## `specsmith skills` � Full Lifecycle (REQ-254..255)

```bash
# Existing commands
specsmith skills build <description>     # generate skill from natural-language description
specsmith skills list [--json]           # list skills with active/inactive badge
specsmith skills test <skill-id>         # dry-run validation
specsmith skills activate <skill-id>     # set active=true

# New commands (REQ-254..255)
specsmith skills deactivate <skill-id>   # set active=false in skill.json
specsmith skills delete <skill-id> [--yes]  # permanently remove skill directory
```

**Notes:**
- `deactivate` exits non-zero if the skill is not found.
- `delete` prompts for confirmation unless `--yes` is passed.
- Sibling skills are unaffected by `delete`.

## `specsmith mcp generate` (REQ-256)

Generate a deterministic MCP server configuration stub from a natural-language description.

```bash
specsmith mcp generate "Search USPTO patents by keyword"
specsmith mcp generate "Calculate BMI" --json
```

**JSON output schema:**
```json
{
  "server": {
    "id": "mcp-calculate-bmi-<hex>",
    "name": "calculate-bmi",
    "command": "node",
    "args": ["/usr/local/lib/mcp-calculate-bmi-<hex>/index.js"],
    "description": "Calculate BMI",
    "env": {}
  },
  "note": "Generated stub � review and adjust before use."
}
```

The generated stub can be appended to `~/.specsmith/mcp.json` for use with the Kairos AI Builder card.

## `specsmith agent ask` (REQ-257)

Keyword-based routing dispatcher that answers settings and status queries without requiring an LLM. Useful for IDE integrations and the Kairos settings agent widget.

```bash
specsmith agent ask "show esdb status" --json-output
specsmith agent ask "build skill for summarizing" --project-dir .
specsmith agent ask "check compliance gaps" --json-output
```

**Routing table:**

| Keywords | Action | Subsystem called |
|---|---|---|
| compliance / coverage / gaps / trace | `compliance_summary` | `get_compliance_summary()` |
| audit / health / governance / drift | `audit` | `run_audit()` |
| skill / build skill / create skill | `skills_hint` | hint to `skills build` |
| esdb / database / backup / export / records | `esdb_status` | `EsdbBridge.status()` |
| mcp / server / tool server | `mcp_hint` | hint to `mcp generate` |
| session / phase / status / project | `session_info` | `init_session()` |
| (no match) | `unknown` | help text |

**JSON output:** `{"reply": "...", "action": "...", "prompt": "..."}`

**Exit code:** always 0 (the dispatcher is best-effort).
