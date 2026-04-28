# Requirements

## 1. Specsmith Must Govern Itself
- **ID:** REQ-001
- **Title:** Specsmith Must Govern Itself
- **Description:** Specsmith must govern its own governance layer and use it for all changes.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 2. Governance Files Must Be Owned by Specsmith
- **ID:** REQ-002
- **Title:** Governance Files Must Be Owned by Specsmith
- **Description:** Only Specsmith may create, update, or delete the human‑readable governance files `ARCHITECTURE.md`, `REQUIREMENTS.md`, `TESTS.md`, and `LEDGER.md`.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 3. Machine State Must Reflect Governance State
- **ID:** REQ-003
- **Title:** Machine State Must Reflect Governance State
- **Description:** Every machine‑readable state file under `.specsmith/` must be derived from its corresponding human‑readable governance file and remain in sync.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 4. Requirements Must Be Derived from Architecture
- **ID:** REQ-004
- **Title:** Requirements Must Be Derived from Architecture
- **Description:** Specsmith must parse `ARCHITECTURE.md` to produce initial requirements.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 5. Requirement IDs Must Be Stable
- **ID:** REQ-005
- **Title:** Requirement IDs Must Be Stable
- **Description:** Once assigned, a requirement ID must never change or be reused.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 6. Preflight Validation Must Be Performed
- **ID:** REQ-006
- **Title:** Preflight Validation Must Be Performed
- **Description:** Before any governance action, the system must validate inputs and produce structured output with required fields.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 7. Test Cases Must Be Generated from Requirements
- **ID:** REQ-007
- **Title:** Test Cases Must Be Generated from Requirements
- **Description:** For each requirement, Specsmith must create or link a test case that can prove the requirement.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 8. Each Requirement Must Link to At Least One Test
- **ID:** REQ-008
- **Title:** Each Requirement Must Link to At Least One Test
- **Description:** Each requirement must be traceable to at least one test case.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 9. Work Items Must Be Created for Accepted Requirements
- **ID:** REQ-009
- **Title:** Work Items Must Be Created for Accepted Requirements
- **Description:** When a requirement is accepted, a unique work item must be created.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 10. Requirements Must Include Priority and Status
- **ID:** REQ-010
- **Title:** Requirements Must Include Priority and Status
- **Description:** Each requirement record must contain `priority` and `status` attributes.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 11. Verification Must Include Confidence Scoring
- **ID:** REQ-011
- **Title:** Verification Must Include Confidence Scoring
- **Description:** Every verification run must produce a numeric confidence score along with pass/fail.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 12. Equilibrium Must Be Reached Before Finalizing
- **ID:** REQ-012
- **Title:** Equilibrium Must Be Reached Before Finalizing
- **Description:** A work item may be marked finished only when its verification confidence meets or exceeds the configured threshold and no contradictions remain.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 13. Retry Recommendations Must Be Provided
- **ID:** REQ-013
- **Title:** Retry Recommendations Must Be Provided
- **Description:** Specsmith must output retry recommendations when verification fails.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 14. Retries Must Be Bounded
- **ID:** REQ-014
- **Title:** Retries Must Be Bounded
- **Description:** Each retry mechanism may not exceed a fixed maximum number of attempts.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 15. Every Governance Action Must Record a Ledger Event
- **ID:** REQ-015
- **Title:** Every Governance Action Must Record a Ledger Event
- **Description:** All changes are logged to `LEDGER.md` and `.specsmith/ledger.jsonl` with timestamp and type.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 16. Trace Chain Must Be Tamper‑Evident
- **ID:** REQ-016
- **Title:** Trace Chain Must Be Tamper‑Evident
- **Description:** The trace chain must use chained cryptographic hashes to provide tamper evidence.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 17. OpenCode Must Own Execution and Tools
- **ID:** REQ-017
- **Title:** OpenCode Must Own Execution and Tools
- **Description:** All filesystem operations and tool executions are performed by OpenCode, not Specsmith directly.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 18. Specsmith Core Must Be Integration‑Agnostic
- **ID:** REQ-018
- **Title:** Specsmith Core Must Be Integration‑Agnostic
- **Description:** The core logic must run without dependency on any particular integration implementation.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 19. Verification Must Evaluate Changed Files
- **ID:** REQ-019
- **Title:** Verification Must Evaluate Changed Files
- **Description:** Verification must analyze which files were changed and only evaluate affected test cases.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 20. Verification Must Evaluate Diff Relevance
- **ID:** REQ-020
- **Title:** Verification Must Evaluate Diff Relevance
- **Description:** Verification must determine whether a diff impacts any requirement or test case and ignore irrelevant changes.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 21. Verification Must Evaluate Test Results
- **ID:** REQ-021
- **Title:** Verification Must Evaluate Test Results
- **Description:** Verification must compare actual output against expected and quantify failures.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 22. Verification Must Evaluate Contradictions and Uncertainty
- **ID:** REQ-022
- **Title:** Verification Must Evaluate Contradictions and Uncertainty
- **Description:** Verification must identify logical contradictions and uncertainty metrics.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 23. Requirement Schema Must Include Source Location, Type, Priority, Confidence, Status, and Timestamps
- **ID:** REQ-023
- **Title:** Requirement Schema Must Include Source Location, Type, Priority, Confidence, Status, and Timestamps
- **Description:** Each requirement record must contain these schema fields.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 24. Test Case Model Must Include Required Fields
- **ID:** REQ-024
- **Title:** Test Case Model Must Include Required Fields
- **Description:** All test case records must contain all required fields.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 25. Work Item Model Must Include Required Fields
- **ID:** REQ-025
- **Title:** Work Item Model Must Include Required Fields
- **Description:** Each work item record must contain required fields such as id, status, priority.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 26. Preflight Output Schema Must Include Decision, Work Item ID, Priority, Requirement IDs, Test Case IDs, Confidence Target
- **ID:** REQ-026
- **Title:** Preflight Output Schema Must Include Decision, Work Item ID, Priority, Requirement IDs, Test Case IDs, Confidence Target
- **Description:** Structured preflight output must list these fields.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 27. Verification Input Must Include Diffs, Tests, Logs, and Changed Files
- **ID:** REQ-027
- **Title:** Verification Input Must Include Diffs, Tests, Logs, and Changed Files
- **Description:** Verification input must contain file diffs, test results, execution logs, and list of changed files.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 28. Retry Strategy Mapping Must Be Defined
- **ID:** REQ-028
- **Title:** Retry Strategy Mapping Must Be Defined
- **Description:** Retries map failures to strategies such as narrow_scope, expand_scope, fix_tests, rollback, and stop.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 29. Integration Adapter Interface Must Provide Required Capabilities
- **ID:** REQ-029
- **Title:** Integration Adapter Interface Must Provide Required Capabilities
- **Description:** Specsmith must provide filesystem and shell execution functions via the integration adapter.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 30. Specsmith CLI Commands Must Be Explicitly Defined
- **ID:** REQ-030
- **Title:** Specsmith CLI Commands Must Be Explicitly Defined
- **Description:** Specsmith CLI must expose commands such as preflight, verify, requirements list/show/accept/reject, tests generate/list, status, and ledger list.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 31. Sequencing Rules Must Enforce Valid States
- **ID:** REQ-031
- **Title:** Sequencing Rules Must Enforce Valid States
- **Description:** Bootstrap and sequence transitions must follow the defined order.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 32. Configuration Settings for Optional Features
- **ID:** REQ-032
- **Title:** Configuration Settings for Optional Features
- **Description:** Specsmith must read optional feature flags from .specsmith/config.yml.
- **Source:** .specsmith/config.yml, ARCHITECTURE.md
- **Status:** defined

## 33. Default Enablement of Optional Features
- **ID:** REQ-033
- **Title:** Default Enablement of Optional Features
- **Description:** All optional Specsmith features must be enabled by default unless overridden.
- **Source:** .specsmith/config.yml, ARCHITECTURE.md
- **Status:** defined

## 34. Evidence ZIP Archive Generation
- **ID:** REQ-034
- **Title:** Evidence ZIP Archive Generation
- **Description:** Specsmith must generate evidence ZIP archive for selected artifacts.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 35. Evidence Manifest Generation
- **ID:** REQ-035
- **Title:** Evidence Manifest Generation
- **Description:** Manifest must list artifacts and metadata in evidence archive.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 36. Per‑File SHA‑256 Hashing in Evidence
- **ID:** REQ-036
- **Title:** Per‑File SHA‑256 Hashing in Evidence
- **Description:** Every file in evidence archive must have a SHA‑256 hash.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 37. Final Evidence ZIP SHA‑256 Hash
- **ID:** REQ-037
- **Title:** Final Evidence ZIP SHA‑256 Hash
- **Description:** The final evidence ZIP archive must have a computed SHA‑256 hash.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 38. Author/Owner Metadata Capture
- **ID:** REQ-038
- **Title:** Author/Owner Metadata Capture
- **Description:** Evidence archive must record author/owner information for each artifact.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 39. Git Commit Metadata Inclusion
- **ID:** REQ-039
- **Title:** Git Commit Metadata Inclusion
- **Description:** Evidence archive must incorporate current git commit hash when available.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 40. Ledger Reference Inclusion
- **ID:** REQ-040
- **Title:** Ledger Reference Inclusion
- **Description:** Evidence archive must reference relevant ledger entries for traceability.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 41. Trusted Timestamp Token Support
- **ID:** REQ-041
- **Title:** Trusted Timestamp Token Support
- **Description:** Evidence archive may include an RFC 3161 trusted timestamp token if enabled.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 42. Legal/IP Disclaimer Requirement
- **ID:** REQ-042
- **Title:** Legal/IP Disclaimer Requirement
- **Description:** Specsmith must provide a disclaimer that evidence does not guarantee legal ownership.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 43. Ledger Event Hash Chaining
- **ID:** REQ-043
- **Title:** Ledger Event Hash Chaining
- **Description:** Each ledger event must be hashed and chained to previous event for tamper evidence.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 44. Ledger Event on Work Proposal
- **ID:** REQ-044
- **Title:** Ledger Event on Work Proposal
- **Description:** Specsmith must create ledger event when a work item is proposed.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 45. Ledger Event on Work Completion
- **ID:** REQ-045
- **Title:** Ledger Event on Work Completion
- **Description:** Specsmith must create ledger event upon completion of each work item or batch.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 46. README.md Generation and Synchronization
- **ID:** REQ-046
- **Title:** README.md Generation and Synchronization
- **Description:** Specsmith must generate README.md if missing and keep it synchronized.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 47. CHANGELOG.md Generation and Synchronization
- **ID:** REQ-047
- **Title:** CHANGELOG.md Generation and Synchronization
- **Description:** Specsmith must generate CHANGELOG.md following Keep a Changelog and keep it updated.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 48. Keep a Changelog Compliance
- **ID:** REQ-048
- **Title:** Keep a Changelog Compliance
- **Description:** CHANGELOG.md must follow Keep a Changelog format.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 49. Semantic Versioning Support
- **ID:** REQ-049
- **Title:** Semantic Versioning Support
- **Description:** Specsmith must understand and support Semantic Versioning for releases.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 50. Guided Version Bump Workflow
- **ID:** REQ-050
- **Title:** Guided Version Bump Workflow
- **Description:** Specsmith must provide a guided workflow for bumping version numbers.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 51. Guided Release Strategy Workflow
- **ID:** REQ-051
- **Title:** Guided Release Strategy Workflow
- **Description:** Specsmith must offer a guided workflow to determine release strategy.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 52. Guided Branching Strategy Workflow
- **ID:** REQ-052
- **Title:** Guided Branching Strategy Workflow
- **Description:** Specsmith must offer a guided workflow for selecting a branching strategy.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 53. Default GitFlow Branching Model
- **ID:** REQ-053
- **Title:** Default GitFlow Branching Model
- **Description:** Specsmith’s default branching model is GitFlow unless overridden.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 54. Guided Branching Modification
- **ID:** REQ-054
- **Title:** Guided Branching Modification
- **Description:** Specsmith must allow guided modifications to the branching model.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 55. GitHub License Generation
- **ID:** REQ-055
- **Title:** GitHub License Generation
- **Description:** Specsmith must generate license files compatible with GitHub/choosealicense.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 56. Commercial License Drafting Guidance
- **ID:** REQ-056
- **Title:** Commercial License Drafting Guidance
- **Description:** Specsmith must provide guidance for drafting commercial licenses, including disclaimer.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 57. Local Git Commit After Work
- **ID:** REQ-057
- **Title:** Local Git Commit After Work
- **Description:** Specsmith should commit local changes after each completed work item or batch.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 58. Confidence Threshold Configuration
- **ID:** REQ-058
- **Title:** Confidence Threshold Configuration
- **Description:** Specsmith must allow configuring epistemic confidence threshold via config file.
- **Source:** .specsmith/config.yml, ARCHITECTURE.md
- **Status:** defined

## 59. Iteration Continuation Until Threshold
- **ID:** REQ-059
- **Title:** Iteration Continuation Until Threshold
- **Description:** Work iterations continue until epistemic confidence reaches threshold.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 60. Indefinite Iteration Default
- **ID:** REQ-060
- **Title:** Indefinite Iteration Default
- **Description:** Specsmith defaults to indefinite iteration unless user sets limits.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 61. Max Iterations Configuration
- **ID:** REQ-061
- **Title:** Max Iterations Configuration
- **Description:** Specsmith must allow configuring maximum iterations.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 62. Token/Cost/Time Limits Configuration
- **ID:** REQ-062
- **Title:** Token/Cost/Time Limits Configuration
- **Description:** Specsmith must allow configuring token spend, session cost, and elapsed time limits.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 63. Stop‑and‑Align Behavior
- **ID:** REQ-063
- **Title:** Stop‑and‑Align Behavior
- **Description:** Specsmith must stop when confidence cannot improve and engage user for alignment.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 64. Interactive Correction Workflow
- **ID:** REQ-064
- **Title:** Interactive Correction Workflow
- **Description:** After stopping, Specsmith should provide an interactive correction workflow.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 65. Nexus Runtime Must Not Own Governance
- **ID:** REQ-065
- **Title:** Nexus Runtime Must Not Own Governance
- **Description:** The Nexus agent runtime must defer preflight, requirement mapping, verification, retry decisions, and ledger writing to Specsmith.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 66. Nexus Must Provide Required Agent Roles
- **ID:** REQ-066
- **Title:** Nexus Must Provide Required Agent Roles
- **Description:** Nexus must instantiate PlannerAgent, ShellAgent, CodeAgent, ReviewerAgent, MemoryAgent, GitAgent, HumanProxyAgent, and an Executor node.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 67. Nexus Tool Layer Must Expose Required Tools
- **ID:** REQ-067
- **Title:** Nexus Tool Layer Must Expose Required Tools
- **Description:** Nexus must expose run_shell, read_file, write_file, patch_file, list_files, grep, git_diff, git_status, run_tests, open_url, search_docs, and remember_project_fact.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 68. Nexus Safety Middleware Must Block Unsafe Commands
- **ID:** REQ-068
- **Title:** Nexus Safety Middleware Must Block Unsafe Commands
- **Description:** The safety middleware must block or require explicit approval for unsafe shell patterns including rm -rf, git push, docker compose down -v, database migrations, deploy commands, and secret reads.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 69. Nexus Tool Arguments Must Be JSON Validated
- **ID:** REQ-069
- **Title:** Nexus Tool Arguments Must Be JSON Validated
- **Description:** All Nexus tool calls must validate that arguments are JSON-serializable before execution.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 70. Nexus Must Normalize File Paths
- **ID:** REQ-070
- **Title:** Nexus Must Normalize File Paths
- **Description:** All file paths supplied to Nexus tools must be normalized to absolute, resolved paths before access.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 71. Nexus Must Index the Repository
- **ID:** REQ-071
- **Title:** Nexus Must Index the Repository
- **Description:** Nexus must populate .repo-index/ with files.json, tags, test_commands.json, architecture.md, and conventions.md as available.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 72. Nexus REPL Must Support Slash Commands
- **ID:** REQ-072
- **Title:** Nexus REPL Must Support Slash Commands
- **Description:** The Nexus REPL must support /plan, /ask, /fix, /test, /commit, /pr, /undo, /context, /exit.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 73. Nexus Output Contract
- **ID:** REQ-073
- **Title:** Nexus Output Contract
- **Description:** Each Nexus task response must include sections Plan, Commands to run, Files changed, Diff, Test results, and Next action.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 74. vLLM Image Must Be Pinned
- **ID:** REQ-074
- **Title:** vLLM Image Must Be Pinned
- **Description:** The Nexus docker-compose.yml must pin the vLLM image to a specific tag (vllm/vllm-openai:v0.8.5) and not use latest.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 75. vLLM Must Serve l1-nexus Model
- **ID:** REQ-075
- **Title:** vLLM Must Serve l1-nexus Model
- **Description:** The Nexus docker-compose.yml must publish the served model as l1-nexus and use the Hermes tool-call parser.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 76. Nexus Tool Executor Registration Must Be Unique
- **ID:** REQ-076
- **Title:** Nexus Tool Executor Registration Must Be Unique
- **Description:** Each Nexus tool must be registered with the AG2 executor exactly once; LLM-side tool signatures may be attached to multiple caller agents but the execution function must not be re-registered to avoid AG2 override warnings.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 77. Safe Cleanup Must Default to Dry-Run
- **ID:** REQ-077
- **Title:** Safe Cleanup Must Default to Dry-Run
- **Description:** The Specsmith safe-cleanup capability must default to dry-run mode and only delete files when an explicit apply flag is provided.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 78. Safe Cleanup Must Use a Hard-Coded Target List
- **ID:** REQ-078
- **Title:** Safe Cleanup Must Use a Hard-Coded Target List
- **Description:** Safe cleanup must only consider the canonical built-in target list and must reject user-supplied arbitrary paths.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 79. Safe Cleanup Must Protect Governance and Source
- **ID:** REQ-079
- **Title:** Safe Cleanup Must Protect Governance and Source
- **Description:** Safe cleanup must refuse to delete .git, .specsmith, governance markdown files, pyproject.toml, README.md, LICENSE, CHANGELOG.md, src/, tests/, docs/, scripts/, .repo-index/, .github/, .warp/, .vscode/, and project configuration dotfiles.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 80. Safe Cleanup Must Emit a Structured Report
- **ID:** REQ-080
- **Title:** Safe Cleanup Must Emit a Structured Report
- **Description:** Safe cleanup must return a report containing the lists of removed paths, skipped paths with reasons, and total bytes reclaimed, suitable for inclusion as ledger evidence.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 81. Safe Cleanup Must Be Exposed via Specsmith CLI
- **ID:** REQ-081
- **Title:** Safe Cleanup Must Be Exposed via Specsmith CLI
- **Description:** The Specsmith CLI must expose the safe cleanup capability as `specsmith clean`, supporting `--apply`, `--json`, and `--project-dir`. When `--apply` is used and `LEDGER.md` exists, the run must be recorded as a `cleanup` ledger event tagged with REQ-077..REQ-080.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 82. CLI Console Must Be UTF-8 Safe Across Platforms
- **ID:** REQ-082
- **Title:** CLI Console Must Be UTF-8 Safe Across Platforms
- **Description:** All Specsmith CLI output (rich Console) must render UTF-8 glyphs (such as warning, arrow, check, cross) without raising UnicodeEncodeError on Windows code pages such as cp1252. The console factory must reconfigure stdout/stderr to UTF-8 and disable rich's legacy_windows renderer.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 83. Canonical Test Specification File Is TESTS.md
- **ID:** REQ-083
- **Title:** Canonical Test Specification File Is TESTS.md
- **Description:** The canonical test specification file is named `TESTS.md` (replacing the legacy names `TEST_SPEC.md`, `TEST-SPEC.md`, and `TEST-SPECS.md`). Specsmith code, governance documents, templates, scaffolder output, importer overlay, auditor checks, retrieval index, exporter, validator, REPL skill files, ReadTheDocs site, and CLI help must all reference `TESTS.md`. Legacy filenames must not be created by new scaffolds, must be auto-renamed by `specsmith migrate-project`, and must not be referenced in user-facing docs.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 84. Natural-Language Governance Broker
- **ID:** REQ-084
- **Title:** Natural-Language Governance Broker
- **Description:** Specsmith must expose a Nexus broker module (`specsmith.agent.broker`) that translates plain-language user utterances into Specsmith-governed work without the user reasoning about REQ IDs, TEST IDs, or work items. The broker must classify intent (read-only ask vs change vs release), infer affected scope from the local `.repo-index` and existing requirements, invoke `specsmith preflight` and `specsmith verify` as the only sources of governance decisions, render plain-language plans and outcomes, hide REQ/TEST/work-item IDs by default (revealed only on `/why`, `/show-governance`, or `--verbose`), bound retries per REQ-014, escalate to a single user clarification on stop-and-align (REQ-063), and never invent governance content (REQ/TEST drafting requires explicit user confirmation).
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 85. specsmith preflight CLI Subcommand
- **ID:** REQ-085
- **Title:** specsmith preflight CLI Subcommand
- **Description:** The Specsmith CLI must expose a `specsmith preflight <utterance>` subcommand that reads `REQUIREMENTS.md` and `.specsmith/` state, classifies intent and infers scope, and emits a JSON object with at least the keys `decision` (one of `accepted`, `needs_clarification`, `blocked`, `rejected`), `work_item_id`, `requirement_ids`, `test_case_ids`, `confidence_target`, and `instruction`. Read-only asks accept by default, destructive intents require clarification, and changes with no matching scope return `needs_clarification` with a one-sentence question. The CLI must support `--project-dir`, `--json`, and `--verbose`.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 86. Nexus REPL Must Gate Execution on Preflight Acceptance
- **ID:** REQ-086
- **Title:** Nexus REPL Must Gate Execution on Preflight Acceptance
- **Description:** When a non-slash utterance flows through the broker, the Nexus REPL must only invoke the AG2 orchestrator's `run_task` if the preflight decision is `accepted`. For any other decision (`needs_clarification`, `blocked`, `rejected`), the REPL must print the broker's plain-language clarification or rejection and return to the prompt without executing.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 87. Nexus REPL Must Drive Execution Through the Bounded-Retry Harness
- **ID:** REQ-087
- **Title:** Nexus REPL Must Drive Execution Through the Bounded-Retry Harness
- **Description:** When the preflight decision is `accepted`, the Nexus REPL must drive the AG2 orchestrator through `specsmith.agent.broker.execute_with_governance`, supplying an executor that wraps `orchestrator.run_task` and synthesizes a result dict (`equilibrium`, `confidence`, `summary`). The harness must honor `DEFAULT_RETRY_BUDGET` (REQ-014), surface the single clarifying question on stop-and-align (REQ-063), and never call `run_task` directly outside the harness.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 88. specsmith preflight Must Resolve Test Case IDs From Machine State
- **ID:** REQ-088
- **Title:** specsmith preflight Must Resolve Test Case IDs From Machine State
- **Description:** The `specsmith preflight` CLI must populate `test_case_ids` in its JSON payload by joining the matched `requirement_ids` against `.specsmith/testcases.json` (or `TESTS.md` when the JSON is unavailable). When the resolved set is non-empty the CLI must include every matching `TEST-NNN` id and must never invent ids not present in machine state.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 89. Nexus Live l1-nexus Smoke Test
- **ID:** REQ-089
- **Title:** Nexus Live l1-nexus Smoke Test
- **Description:** Specsmith must ship a `scripts/nexus_smoke.py` script that POSTs a minimal chat-completions request to a running vLLM `l1-nexus` container at `http://localhost:8000/v1/chat/completions` and reports whether the model responded with a well-formed `choices[0].message.content`. A pytest integration test must invoke the script and skip unless the environment variable `NEXUS_LIVE=1` is set, so the suite stays green offline but is verifiable when the container is up.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 90. Nexus Documentation Must Describe Broker, Preflight, and Gated Execution
- **ID:** REQ-090
- **Title:** Nexus Documentation Must Describe Broker, Preflight, and Gated Execution
- **Description:** `ARCHITECTURE.md`, `README.md`, and `docs/` must describe the natural-language broker (REQ-084), the `specsmith preflight` CLI (REQ-085), the REPL execution gate (REQ-086), and the bounded-retry harness (REQ-087), including the `/why` toggle and an end-to-end example flow. Documentation must not surface REQ/TEST/WI tokens to the user except inside the explicit `/why` block.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 91. Orchestrator Must Return a Structured TaskResult
- **ID:** REQ-091
- **Title:** Orchestrator Must Return a Structured TaskResult
- **Description:** `orchestrator.run_task` must return a `TaskResult` dataclass with at least the fields `equilibrium: bool`, `confidence: float`, `summary: str`, `files_changed: list[str]`, and `test_results: dict`. The Nexus REPL's broker branch must consume this dataclass directly when feeding `execute_with_governance` (REQ-087); the broker must not synthesize `equilibrium` from a boolean cast of the summary string.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 92. specsmith preflight CLI Must Use Decision-Specific Exit Codes
- **ID:** REQ-092
- **Title:** specsmith preflight CLI Must Use Decision-Specific Exit Codes
- **Description:** The `specsmith preflight` CLI must exit `0` for `accepted`, `2` for `needs_clarification`, and `3` for `blocked` or `rejected` decisions, so CI pipelines and shell wrappers can branch on intent without parsing the JSON payload. The JSON payload must continue to print on stdout for both success and non-zero exits.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 93. Accepted preflight Must Record a Ledger Event
- **ID:** REQ-093
- **Title:** Accepted preflight Must Record a Ledger Event
- **Description:** When `specsmith preflight` produces an `accepted` decision and `LEDGER.md` exists in the project root, the CLI must append a `preflight` ledger event tagged with `REQ-085` plus the resolved `requirement_ids`. The event must record the utterance, the assigned `work_item_id`, and the `confidence_target`, so every accepted preflight is traceable end-to-end.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 94. /why Must Surface Post-Run Governance in the REPL
- **ID:** REQ-094
- **Title:** /why Must Surface Post-Run Governance in the REPL
- **Description:** When `verbose_governance` is on (toggled by `/why` or `/show-governance`), after the REPL drives `execute_with_governance` for an accepted utterance it must print a single `[/why]` block summarizing the assigned `work_item_id`, the matched `requirement_ids` and `test_case_ids`, the post-run confidence, and whether the bounded-retry harness reached equilibrium. When verbose mode is off, the post-run governance block must not be emitted.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 95. Nexus Live Smoke Run Must Be Reproducible Evidence
- **ID:** REQ-095
- **Title:** Nexus Live Smoke Run Must Be Reproducible Evidence
- **Description:** A live or honestly-skipped invocation of `scripts/nexus_smoke.py` must be captured under `.specsmith/runs/WI-NEXUS-011/logs.txt` so the project ledger preserves at least one reproducible record of the broker -> preflight -> orchestrator -> vLLM end-to-end path (or a documented reason the live container could not be reached in the current environment).
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 96. Bounded-Retry Harness Must Map Failures to Retry Strategies
- **ID:** REQ-096
- **Title:** Bounded-Retry Harness Must Map Failures to Retry Strategies
- **Description:** When `execute_with_governance` exhausts its retry budget (REQ-014), it must classify the last executor report against the canonical retry strategy mapping (REQ-028): `narrow_scope`, `expand_scope`, `fix_tests`, `rollback`, or `stop`. The classification must be exposed on `RunResult.strategy` and surfaced in the clarifying question (REQ-063) so the user gets one concrete next-action label rather than only a free-form sentence.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 97. specsmith verify CLI Subcommand
- **ID:** REQ-097
- **Title:** specsmith verify CLI Subcommand
- **Description:** The Specsmith CLI must expose a `specsmith verify` subcommand that consumes the verification input contract (REQ-027): file diffs, test results, execution logs, and changed files (paths or `--stdin` JSON). The subcommand must emit a JSON object with at least `equilibrium`, `confidence`, `summary`, `files_changed`, `test_results`, and `retry_strategy`. Exit code 0 on equilibrium with confidence ≥ the configured threshold, 2 when retry is recommended, and 3 when stop-and-align is required.
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 98. Confidence Threshold Must Be Read From .specsmith/config.yml
- **ID:** REQ-098
- **Title:** Confidence Threshold Must Be Read From .specsmith/config.yml
- **Description:** Both `specsmith preflight` and the broker's `run_preflight` helper must consult `.specsmith/config.yml` for the `epistemic.confidence_threshold` value (REQ-058) and use it as the floor for the JSON `confidence_target` field whenever it is greater than the heuristic default. When the config file is absent or unparseable, the existing heuristic defaults must continue to apply.
- **Source:** .specsmith/config.yml, ARCHITECTURE.md
- **Status:** defined

## 99. Accepted Preflight Must Record a Distinct work_proposal Event
- **ID:** REQ-099
- **Title:** Accepted Preflight Must Record a Distinct work_proposal Event
- **Description:** When `specsmith preflight` produces an `accepted` decision and assigns a brand-new `work_item_id`, the CLI must append a `work_proposal` ledger event in addition to the existing `preflight` event (REQ-044). The `work_proposal` entry must reference REQ-044 and REQ-085, include the `work_item_id` and matched `requirement_ids`, and must NOT be emitted when the underlying `work_item_id` already appears in `LEDGER.md` (no duplicate proposals).
- **Source:** ARCHITECTURE.md
- **Status:** defined

## 100. Broker Scope Inference May Surface Stress-Test Critical Failures
- **ID:** REQ-100
- **Title:** Broker Scope Inference May Surface Stress-Test Critical Failures
- **Description:** When the user passes `--stress` to `specsmith preflight` and the matched requirements set is non-empty, the CLI must invoke the existing AEE `StressTester` against those belief artifacts and surface any critical failures in the JSON payload as a `stress_warnings` list. The narration (verbose mode) must include a one-sentence plain-English warning when at least one critical failure is found. The flag must default off so unrelated tests continue to pass.
- **Source:** ARCHITECTURE.md
- **Status:** defined
## 101. Lint Baseline Must Be Clean
- **ID:** REQ-101
- **Title:** Lint Baseline Must Be Clean
- **Description:** `ruff check src/ tests/` and `ruff format --check src/ tests/` must both exit zero on `develop`. The lint job in `.github/workflows/ci.yml` enforces this contract. Per-file ignores in `pyproject.toml` are reserved for documentation modules whose long lines are intentional (e.g. `toolrules.py`, `tool_installer.py`).
- **Source:** .github/workflows/ci.yml, pyproject.toml
- **Status:** defined
## 102. Type-Check Baseline Must Be Clean
- **ID:** REQ-102
- **Title:** Type-Check Baseline Must Be Clean
- **Description:** `mypy src/specsmith/` must exit zero on `develop`. Strict-mypy is preserved for the historically-typed modules; dynamically-typed modules in `specsmith.agent.*`, `specsmith.console_utils`, `specsmith.serve`, and the agent-orchestrator surface are explicitly enumerated in the `[[tool.mypy.overrides]]` `ignore_errors=true` block of `pyproject.toml` until they are individually annotated.
- **Source:** .github/workflows/ci.yml, pyproject.toml
- **Status:** defined
## 103. Security Baseline Tolerates Unfixed pip Advisory
- **ID:** REQ-103
- **Title:** Security Baseline Tolerates Unfixed pip Advisory
- **Description:** The CI security job must upgrade pip to the latest release before invoking `pip-audit`, and must pass the `--ignore-vuln CVE-2026-3219` flag for the unfixed pip advisory so the runner's own pip version does not block PRs. Specsmith's actual runtime dependencies (click, jinja2, pyyaml, pydantic, rich) must remain pip-audit clean; any new advisory against them must trigger a dependency bump rather than another ignore-flag.
- **Source:** .github/workflows/ci.yml
- **Status:** defined

