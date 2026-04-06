# Requirements — specsmith

## CLI

- **REQ-CLI-001**: `specsmith init` scaffolds a governed project from interactive prompts or YAML config
- **REQ-CLI-002**: `specsmith audit` runs health and drift checks against a governed project
- **REQ-CLI-003**: `specsmith validate` checks governance file consistency (req ↔ test ↔ arch)
- **REQ-CLI-004**: `specsmith compress` archives old ledger entries when LEDGER.md exceeds threshold
- **REQ-CLI-005**: `specsmith upgrade` regenerates governance files for a newer spec version
- **REQ-CLI-006**: All commands accept `--project-dir` to target a specific project root
- **REQ-CLI-007**: `specsmith --version` displays the current version
- **REQ-CLI-008**: `specsmith import` detects an existing project and generates governance overlay
- **REQ-CLI-009**: `specsmith init --guided` runs interactive architecture definition session
- **REQ-CLI-010**: `specsmith status` shows CI status, alerts, and PRs from VCS platform CLI
- **REQ-CLI-011**: `specsmith diff` compares governance files against spec templates
- **REQ-CLI-012**: `specsmith export` generates compliance report with REQ coverage matrix, audit summary, tool status
- **REQ-CLI-013**: `specsmith import --guided` runs architecture definition after import detection

## Scaffolding

- **REQ-SCF-001**: Scaffolder generates all governance files (AGENTS.md, LEDGER.md, modular docs)
- **REQ-SCF-002**: Scaffolder generates project-type-specific files (pyproject.toml for Python, etc.)
- **REQ-SCF-003**: Scaffolder creates .gitkeep files in expected empty directories
- **REQ-SCF-004**: Scaffolder optionally runs `git init` in the target directory
- **REQ-SCF-005**: Scaffolder saves scaffold.yml config for re-runs and upgrades
- **REQ-SCF-006**: Scaffolder generates agent integration files based on config.integrations list

## Configuration

- **REQ-CFG-001**: ProjectConfig validates scaffold.yml input with pydantic
- **REQ-CFG-002**: ProjectConfig supports 30 project types covering Python, Rust, Go, C/C++, JS/TS, .NET, mobile, DevOps, data/ML, microservices, documents, business, legal, and project management
- **REQ-CFG-003**: ProjectConfig derives package_name from project name (hyphen → underscore)
- **REQ-CFG-004**: ProjectConfig supports verification_tools overrides per tool category
- **REQ-CFG-005**: ProjectConfig stores detected_build_system and detected_test_framework from import

## Audit

- **REQ-AUD-001**: Audit checks for required governance files (AGENTS.md, LEDGER.md)
- **REQ-AUD-002**: Audit checks modular governance files when AGENTS.md exceeds 200 lines
- **REQ-AUD-003**: Audit checks REQ ↔ TEST coverage consistency
- **REQ-AUD-004**: Audit checks ledger size against threshold (default 500 lines)
- **REQ-AUD-005**: Audit checks open TODO count in ledger
- **REQ-AUD-006**: Audit checks governance file sizes against bloat thresholds
- **REQ-AUD-007**: Audit checks CI config references expected verification tools for project type
- **REQ-AUD-008**: `audit --fix` generates missing CI configs from tool registry

## Validation

- **REQ-VAL-001**: Validate checks scaffold.yml structure and required fields
- **REQ-VAL-002**: Validate checks AGENTS.md local file references resolve
- **REQ-VAL-003**: Validate checks requirement ID uniqueness
- **REQ-VAL-004**: Validate checks architecture.md references requirements

## Compression

- **REQ-CMP-001**: Compress archives entries older than keep_recent threshold
- **REQ-CMP-002**: Compress writes archived entries to docs/ledger-archive.md
- **REQ-CMP-003**: Compress only runs when ledger exceeds line threshold

## Upgrade

- **REQ-UPG-001**: Upgrade reads scaffold.yml for current config
- **REQ-UPG-002**: Upgrade re-renders governance templates with new spec version
- **REQ-UPG-003**: Upgrade updates scaffold.yml with new spec version

## Integrations

- **REQ-INT-001**: Warp adapter generates .warp/skills/SKILL.md
- **REQ-INT-002**: Claude Code adapter generates CLAUDE.md
- **REQ-INT-003**: Cursor adapter generates .cursor/rules/governance.mdc
- **REQ-INT-004**: Copilot adapter generates .github/copilot-instructions.md
- **REQ-INT-005**: Adapter registry allows listing and instantiating adapters by name

## Tool Registry

- **REQ-TLR-001**: Tool registry maps each project type to lint, typecheck, test, security, build, format, and compliance tools
- **REQ-TLR-002**: Tool registry provides CI metadata per language (GitHub Actions setup, Docker images, cache keys)
- **REQ-TLR-003**: Tool registry supports user overrides via verification_tools config field
- **REQ-TLR-004**: Format tools have CI check-mode equivalents (e.g., ruff format → ruff format --check)

## Import

- **REQ-IMP-001**: Importer detects primary language from file extension counts
- **REQ-IMP-002**: Importer detects build system from marker files (pyproject.toml, Cargo.toml, etc.)
- **REQ-IMP-003**: Importer detects test framework from indicator files
- **REQ-IMP-004**: Importer detects existing CI and VCS platform
- **REQ-IMP-005**: Importer detects existing governance files and modules/entry points
- **REQ-IMP-006**: Importer infers correct ProjectType from detection results
- **REQ-IMP-007**: Overlay generation creates AGENTS.md, LEDGER.md, REQUIREMENTS.md, TEST_SPEC.md, architecture.md
- **REQ-IMP-008**: Overlay generation skips existing files unless --force is specified

## VCS Platforms

- **REQ-VCS-001**: GitHub, GitLab, and Bitbucket platforms generate tool-aware CI configs from the registry
- **REQ-VCS-002**: CI config generation supports all 30 project types with correct tool commands
- **REQ-VCS-003**: Dependabot/Renovate config uses correct package ecosystem per language
- **REQ-VCS-004**: Mixed-language projects (e.g., Python+JS) get multi-runtime CI setup

## Export

- **REQ-EXP-001**: Export generates project summary from scaffold.yml
- **REQ-EXP-002**: Export generates REQ↔TEST coverage matrix with percentage
- **REQ-EXP-003**: Export includes audit summary with pass/fail/fixable counts
- **REQ-EXP-004**: Export includes governance file inventory
- **REQ-EXP-005**: Export supports --output flag for file output

## Templates

- **REQ-TPL-001**: Governance templates include type-specific verification tool listings
- **REQ-TPL-002**: Requirements template generates domain-specific starters (patent, legal, business, API, research)
- **REQ-TPL-003**: Test spec template generates domain-specific test stubs
- **REQ-TPL-004**: Architecture template includes verification tools section

## Git VCS Commands

- **REQ-GIT-001**: specsmith commit generates message from last ledger entry
- **REQ-GIT-002**: specsmith commit refuses if LEDGER.md not updated since last commit
- **REQ-GIT-003**: specsmith commit runs audit as pre-commit validation
- **REQ-GIT-004**: specsmith push pushes current branch with safety checks
- **REQ-GIT-005**: specsmith push refuses direct push to main from feature branches
- **REQ-GIT-006**: specsmith branch create enforces naming and base branch per strategy
- **REQ-GIT-007**: specsmith branch list shows branches with strategy context
- **REQ-GIT-008**: specsmith pr generates PR with governance summary in description
- **REQ-GIT-009**: specsmith pr sets correct base branch per branching strategy
- **REQ-GIT-010**: specsmith sync pulls and warns on governance file conflicts

## Self-Update and Migration

- **REQ-UPD-001**: specsmith update checks PyPI for newer version and reports comparison
- **REQ-UPD-002**: specsmith update --yes installs latest version without confirmation
- **REQ-UPD-003**: specsmith update triggers migrate-project after successful update
- **REQ-UPD-004**: specsmith migrate-project compares scaffold.yml spec_version to installed version
- **REQ-UPD-005**: specsmith migrate-project regenerates governance templates for new version
- **REQ-UPD-006**: specsmith migrate-project reports deprecated features and breaking changes
- **REQ-UPD-007**: specsmith migrate-project --dry-run shows changes without writing
- **REQ-UPD-008**: Agent adapter files instruct agent to run update --check at session start
- **REQ-UPD-009**: specsmith migrate-project appends migration entry to LEDGER.md
- **REQ-UPD-010**: specsmith migrate-project preserves all existing REQs, TESTs, and ledger entries

## Workflow Logic

- **REQ-WFL-001**: Agent proposes commit after successful verification + ledger save
- **REQ-WFL-002**: Agent proposes push before session end if unpushed commits exist
- **REQ-WFL-003**: Agent refuses to work on main/develop directly for gitflow projects
- **REQ-WFL-004**: Agent proposes branch creation when starting a new task
- **REQ-WFL-005**: Agent proposes PR when feature branch TODOs are complete and audit passes
- **REQ-WFL-006**: Agent runs sync at session start before any work
- **REQ-WFL-007**: Agent runs update --check at session start and proposes update if outdated
- **REQ-WFL-008**: Agent checks current branch matches task type (feature vs hotfix vs release)
- **REQ-WFL-009**: specsmith commit --auto-push option to commit and push in one step
- **REQ-WFL-010**: specsmith session-end provides checklist (unpushed commits, open TODOs, dirty files)

## Credit Tracking

- **REQ-CRD-001**: `specsmith credits record` stores token usage entry with model, provider, tokens, task, and estimated cost
- **REQ-CRD-002**: `specsmith credits summary` shows aggregate spend by model, provider, and task
- **REQ-CRD-003**: `specsmith credits report` generates markdown credit report
- **REQ-CRD-004**: `specsmith credits analyze` detects model inefficiency, token waste, and cost trends
- **REQ-CRD-005**: `specsmith credits budget` configures monthly cap, alert threshold, and watermark levels
- **REQ-CRD-006**: Credit tracking auto-initialized on init, import, and upgrade with unlimited default
- **REQ-CRD-007**: `.specsmith/` directory gitignored by default in generated projects
- **REQ-CRD-008**: Session-end checklist includes credit summary and budget alerts
- **REQ-CRD-009**: Agent adapters (Warp, Claude) include credit recording instructions

## Architecture Generation

- **REQ-ARC-001**: `specsmith architect` scans project for modules, languages, dependencies, git history
- **REQ-ARC-002**: `specsmith architect` runs interactive interview for components, data flow, deployment
- **REQ-ARC-003**: `specsmith architect --non-interactive` auto-generates without prompts
- **REQ-ARC-004**: `audit --fix` generates architecture.md from project scan when missing

## Self-Update

- **REQ-SLF-001**: `specsmith self-update` auto-detects channel (stable/dev) from installed version
- **REQ-SLF-002**: `specsmith self-update --channel dev` forces dev channel
- **REQ-SLF-003**: `specsmith self-update --version X.Y.Z` pins to specific version

## Templates

- **REQ-TPL-005**: .gitattributes template includes type-specific patterns for all 30 project types
- **REQ-TPL-006**: .gitignore template includes type-specific patterns for all 30 project types
- **REQ-TPL-007**: .editorconfig template includes type-specific indent/EOL settings
- **REQ-TPL-008**: Yocto/bitbake language detection includes .bbclass, .inc, .dts, .dtsi

## Cross-Platform

- **REQ-XPL-001**: All CLI commands work on Windows, Linux, and macOS
- **REQ-XPL-002**: Generated scripts include both .cmd and .sh variants

## Applied Epistemic Engineering (AEE)

- **REQ-AEE-001**: `BeliefArtifact` model captures id, propositions, epistemic boundary, confidence, and status
- **REQ-AEE-002**: Requirements in `REQUIREMENTS.md` are parseable as `BeliefArtifact` instances via `parse_requirements_as_beliefs()`
- **REQ-AEE-003**: `beliefs_from_dicts()` constructs BeliefArtifacts from plain dicts (JSON/YAML/DB)
- **REQ-AEE-004**: `BeliefArtifact.add_evidence()` adds citation and elevates confidence from UNKNOWN to LOW
- **REQ-AEE-005**: `BeliefArtifact.to_dict()` serialises to a JSON-compatible dict

## Stress Testing

- **REQ-STR-001**: `specsmith stress-test` applies adversarial challenges to all requirements and reports failure modes
- **REQ-STR-002**: `StressTester` applies 8 challenge categories: vagueness, missing test, missing boundary, compound claim, no propositions, P1 confidence, circular links, logic knots
- **REQ-STR-003**: `StressTester` detects Logic Knots (conflicting accepted requirements) via MUST/MUST NOT heuristic
- **REQ-STR-004**: `StressTester` detects duplicate requirement IDs as Logic Knots
- **REQ-STR-005**: `StressTestResult.equilibrium` is True when no critical failures and no logic knots

## Failure-Mode Graph

- **REQ-FMG-001**: `FailureModeGraph` maps stress-test results to breakpoints with severity and recovery paths
- **REQ-FMG-002**: `specsmith belief-graph` renders dependency graph as text tree or Mermaid diagram
- **REQ-FMG-003**: `FailureModeGraph.equilibrium_check()` returns True when S(G) yields no new failure modes
- **REQ-FMG-004**: `FailureModeGraph.logic_knot_detect()` returns all detected Logic Knots
- **REQ-FMG-005**: `FailureModeGraph` builds edges from `BeliefArtifact.inferential_links`

## Certainty and Confidence

- **REQ-CRT-001**: `CertaintyEngine` scores belief artifacts C = base × coverage × freshness ∈ [0, 1]
- **REQ-CRT-002**: `CertaintyEngine` propagates confidence via weakest-link rule through inferential links
- **REQ-CRT-003**: `CertaintyReport.component_averages` groups scores by component code
- **REQ-CRT-004**: `specsmith epistemic-audit` reports per-artifact confidence and equilibrium status
- **REQ-CRT-005**: `CertaintyEngine` threshold is configurable (default 0.7, overridable via `scaffold.yml`)

## Trace Vault

- **REQ-TRC-001**: `SealRecord` captures type, content hash, timestamp, and prev hash
- **REQ-TRC-002**: `specsmith trace verify` validates full trace chain integrity
- **REQ-TRC-003**: Ledger entries include `entry_hash` for tamper detection (CryptoAuditChain)
- **REQ-TRC-004**: `TraceVault` stores seals in `.specsmith/trace.jsonl` (append-only)
- **REQ-TRC-005**: `specsmith trace seal` creates a SealRecord for decisions, milestones, audit gates

## Recovery

- **REQ-RCV-001**: `RecoveryOperator` generates bounded `RecoveryProposal` objects for all failure modes
- **REQ-RCV-002**: `RecoveryProposal` objects are never auto-applied; they require human approval
- **REQ-RCV-003**: Recovery proposals are ranked by severity (CRITICAL=1, HIGH=2, MEDIUM=3, LOW=4)
- **REQ-RCV-004**: `RecoveryOperator` generates proposals for Logic Knots with RESOLVE or DEPRECATE strategy

## Agentic Client

- **REQ-AGT-001**: `specsmith run` starts an interactive AEE-integrated REPL
- **REQ-AGT-002**: `specsmith run --task` executes a single task non-interactively
- **REQ-AGT-003**: Agentic client auto-detects LLM provider from environment variables
- **REQ-AGT-004**: Agentic client supports Anthropic, OpenAI, Gemini, and Ollama providers
- **REQ-AGT-005**: All LLM providers are optional extras (`pip install specsmith[anthropic]` etc.)
- **REQ-AGT-006**: specsmith commands are registered as native agent tools
- **REQ-AGT-007**: Skill files (SKILL.md) are loaded from project and built-in profiles
- **REQ-AGT-008**: Hook system fires on PreTool, PostTool, SessionStart, SessionEnd events
- **REQ-AGT-009**: H13 hook warns when AEE tools are called without epistemic boundary
- **REQ-AGT-010**: `specsmith agent providers` shows available LLM providers and status

## epistemic Library

- **REQ-EPI-001**: `from epistemic import AEESession` works from any Python 3.10+ project after `pip install specsmith`
- **REQ-EPI-002**: `epistemic` package has zero external dependencies beyond stdlib
- **REQ-EPI-003**: `AEESession` bundles the full AEE pipeline in one object (add_belief, run, save, seal)
- **REQ-EPI-004**: `AEESession.run()` executes Frame→Disassemble→Stress-Test→Failure-Graph→Certainty→Recovery
- **REQ-EPI-005**: `AEESession.save()`/`load()` persists belief state as JSON
- **REQ-EPI-006**: `specsmith.epistemic` module re-exports everything from `epistemic` (backward compat)
- **REQ-EPI-007**: `epistemic` package includes `py.typed` marker for mypy support

## Auth (#37)

- **REQ-AUTH-001**: `specsmith auth set <platform>` stores API tokens securely (keyring > file; never logged)
- **REQ-AUTH-002**: `specsmith auth list` shows configured platforms with masked token values
- **REQ-AUTH-003**: `specsmith auth remove <platform>` deletes stored credentials
- **REQ-AUTH-004**: `specsmith auth check` validates all required tokens for configured integrations
- **REQ-AUTH-005**: Token resolution priority: env vars → OS keyring → encrypted file
- **REQ-AUTH-006**: Token values NEVER written to logs, ledger, governance files, or CLI output

## Workspace (#17)

- **REQ-WRK-001**: `specsmith workspace init` creates workspace.yml governing multiple projects
- **REQ-WRK-002**: `specsmith workspace audit` runs health checks across all workspace projects
- **REQ-WRK-003**: `specsmith workspace export` generates combined compliance report
- **REQ-WRK-004**: workspace.yml supports project list with paths and org-level defaults

## Watch (#16)

- **REQ-WCH-001**: `specsmith watch` monitors project directory and alerts on governance drift
- **REQ-WCH-002**: Watch alerts when LEDGER.md not updated after code changes
- **REQ-WCH-003**: Watch uses polling fallback when watchdog is not installed

## Patent (#10)

- **REQ-PAT-001**: `specsmith patent search <query>` searches USPTO ODP API for patents
- **REQ-PAT-002**: `specsmith patent prior-art <claim>` analyzes prior art with key-term extraction
- **REQ-PAT-003**: Patent commands require USPTO_API_KEY or `specsmith auth set uspto`
- **REQ-PAT-004**: Prior art reports saved to prior-art/ directory with markdown format

## Auto-Update

- **REQ-AUP-001**: Every specsmith command checks scaffold.yml spec_version vs installed version
- **REQ-AUP-002**: If outdated, prompt Y/n to migrate project (calls migrate-project)
- **REQ-AUP-003**: Auto-update prompt skippable via SPECSMITH_NO_AUTO_UPDATE=1 env var
- **REQ-AUP-004**: Meta-commands (update, self-update, migrate-project) skip the version check

## Credit Hard Cap (#52)

- **REQ-CHC-001**: CreditBudget has enforcement_mode field: soft (warn) | hard (block)
- **REQ-CHC-002**: `specsmith credits check` shows spend vs budget with visual bar
- **REQ-CHC-003**: Hard cap mode exits with code 2 when cap is exceeded
- **REQ-CHC-004**: `specsmith credits budget --enforcement hard` enables hard cap mode

## Scaffolder Epistemic

- **REQ-SCF-EPI-001**: `specsmith init` for epistemic project types renders 4 epistemic governance templates
- **REQ-SCF-EPI-002**: `enable_epistemic=true` adds epistemic governance to any project type
- **REQ-SCF-EPI-003**: Epistemic project types get domain-specific directory structures

## Token & Credit Optimization

- **REQ-OPT-001**: `TokenEstimator` estimates token count from text using per-model character ratios, and estimates cost in USD from token counts and provider pricing tables
- **REQ-OPT-002**: `ResponseCache` stores LLM responses keyed by SHA-256 hash of (provider, model, serialised messages); returns cached response on hit and records savings
- **REQ-OPT-003**: `ResponseCache` supports configurable TTL (default 1 h) and optional JSON persistence to `.specsmith/response-cache.json`
- **REQ-OPT-004**: `ContextManager.trim()` implements a sliding window that drops oldest non-system messages when total estimated tokens exceed `context_max_tokens`
- **REQ-OPT-005**: `ContextManager` triggers a summarisation recommendation when history token count exceeds `summarize_threshold`
- **REQ-OPT-006**: `ModelRouter.classify()` assigns a complexity tier (FAST/BALANCED/POWERFUL) to a user message using keyword and length heuristics, with no external API call
- **REQ-OPT-007**: `ModelRouter.suggest_model()` returns the cheapest default model for a given (provider, tier) pair from a built-in pricing table
- **REQ-OPT-008**: `ToolFilter.select()` scores available tools against task text and returns only the top-N relevant tools, reducing tool-schema token overhead
- **REQ-OPT-009**: `OptimizationEngine.pre_call()` applies caching, context trim, model routing, and tool filtering before each LLM call; returns transformed messages, selected model, and an `OptimizationHint`
- **REQ-OPT-010**: `OptimizationEngine.post_call()` records tokens saved, cache hit/miss, and model routing decision to running `OptimizationReport`
- **REQ-OPT-011**: `AnthropicProvider` adds `cache_control: {"type": "ephemeral"}` to the system message when `prompt_caching=True`, enabling Anthropic’s 90% cached-read discount
- **REQ-OPT-012**: `specsmith optimize` CLI command reads `.specsmith/` usage data and emits an `OptimizationReport` with concrete recommendations and projected monthly savings
- **REQ-OPT-013**: `OptimizationConfig` is serialisable and can be embedded in `scaffold.yml` under `optimization:` to persist settings per project

## GUI Workbench

- **REQ-GUI-001**: `specsmith gui` launches a cross-platform Qt6 desktop workbench (Windows, Linux, macOS)
- **REQ-GUI-002**: Workbench supports multiple independent agent sessions as tabs, each with its own project directory, provider, model, and conversation history
- **REQ-GUI-003**: Chat view renders user, assistant, tool call, and system messages in visually distinct styles
- **REQ-GUI-004**: Token meter displays context window fill percentage, input/output token counts, and estimated cost in real time
- **REQ-GUI-005**: Optimization banner appears at 70% context fill with actionable suggestions (clear history, compress ledger, summarize session)
- **REQ-GUI-006**: Tool panel provides one-click access to all specsmith tools (audit, validate, doctor, stress-test, epistemic-audit, belief-graph, export, trace-verify, req-list, req-gaps) with pass/fail indicators
- **REQ-GUI-007**: File upload injects text files as inline context; images and PDFs are routed through Mistral OCR
- **REQ-GUI-008**: URL injection fetches page content and injects it as context prefix
- **REQ-GUI-009**: Background update checker silently installs newer specsmith versions on startup and shows a status bar notification
- **REQ-GUI-010**: Provider and model can be switched per tab without restarting the session
- **REQ-GUI-011**: Agent calls run in a background QThread so the UI never blocks
- **REQ-GUI-012**: Epistemic status strip shows current certainty score, last audit result, and last validate result
- **REQ-GUI-013**: Input bar supports keyboard shortcut (Ctrl+Enter) to send and drag-and-drop of files
