# Requirements

## REQ-001. Specsmith Must Govern Itself
- **ID:** REQ-001
- **Title:** Specsmith Must Govern Itself
- **Description:** Specsmith must govern its own governance layer and use it for all changes.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-002. Governance Files Must Be Owned by Specsmith
- **ID:** REQ-002
- **Title:** Governance Files Must Be Owned by Specsmith
- **Description:** Only Specsmith may create, update, or delete the human‑readable governance files `ARCHITECTURE.md`, `REQUIREMENTS.md`, `TESTS.md`, and `LEDGER.md`.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-003. Machine State Must Reflect Governance State
- **ID:** REQ-003
- **Title:** Machine State Must Reflect Governance State
- **Description:** Every machine‑readable state file under `.specsmith/` must be derived from its corresponding human‑readable governance file and remain in sync.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-004. Requirements Must Be Derived from Architecture
- **ID:** REQ-004
- **Title:** Requirements Must Be Derived from Architecture
- **Description:** Specsmith must parse `ARCHITECTURE.md` to produce initial requirements.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-005. Requirement IDs Must Be Stable
- **ID:** REQ-005
- **Title:** Requirement IDs Must Be Stable
- **Description:** Once assigned, a requirement ID must never change or be reused.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-006. Preflight Validation Must Be Performed
- **ID:** REQ-006
- **Title:** Preflight Validation Must Be Performed
- **Description:** Before any governance action, the system must validate inputs and produce structured output with required fields.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-007. Test Cases Must Be Generated from Requirements
- **ID:** REQ-007
- **Title:** Test Cases Must Be Generated from Requirements
- **Description:** For each requirement, Specsmith must create or link a test case that can prove the requirement.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-008. Each Requirement Must Link to At Least One Test
- **ID:** REQ-008
- **Title:** Each Requirement Must Link to At Least One Test
- **Description:** Each requirement must be traceable to at least one test case.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-009. Work Items Must Be Created for Accepted Requirements
- **ID:** REQ-009
- **Title:** Work Items Must Be Created for Accepted Requirements
- **Description:** When a requirement is accepted, a unique work item must be created.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-010. Requirements Must Include Priority and Status
- **ID:** REQ-010
- **Title:** Requirements Must Include Priority and Status
- **Description:** Each requirement record must contain `priority` and `status` attributes.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-011. Verification Must Include Confidence Scoring
- **ID:** REQ-011
- **Title:** Verification Must Include Confidence Scoring
- **Description:** Every verification run must produce a numeric confidence score along with pass/fail.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-012. Equilibrium Must Be Reached Before Finalizing
- **ID:** REQ-012
- **Title:** Equilibrium Must Be Reached Before Finalizing
- **Description:** A work item may be marked finished only when its verification confidence meets or exceeds the configured threshold and no contradictions remain.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-013. Retry Recommendations Must Be Provided
- **ID:** REQ-013
- **Title:** Retry Recommendations Must Be Provided
- **Description:** Specsmith must output retry recommendations when verification fails.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-014. Retries Must Be Bounded
- **ID:** REQ-014
- **Title:** Retries Must Be Bounded
- **Description:** Each retry mechanism may not exceed a fixed maximum number of attempts.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-015. Every Governance Action Must Record a Ledger Event
- **ID:** REQ-015
- **Title:** Every Governance Action Must Record a Ledger Event
- **Description:** All changes are logged to `LEDGER.md` and `.specsmith/ledger.jsonl` with timestamp and type.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-016. Trace Chain Must Be Tamper‑Evident
- **ID:** REQ-016
- **Title:** Trace Chain Must Be Tamper‑Evident
- **Description:** The trace chain must use chained cryptographic hashes to provide tamper evidence.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-017. OpenCode Must Own Execution and Tools
- **ID:** REQ-017
- **Title:** OpenCode Must Own Execution and Tools
- **Description:** All filesystem operations and tool executions are performed by OpenCode, not Specsmith directly.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-018. Specsmith Core Must Be Integration‑Agnostic
- **ID:** REQ-018
- **Title:** Specsmith Core Must Be Integration‑Agnostic
- **Description:** The core logic must run without dependency on any particular integration implementation.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-019. Verification Must Evaluate Changed Files
- **ID:** REQ-019
- **Title:** Verification Must Evaluate Changed Files
- **Description:** Verification must analyze which files were changed and only evaluate affected test cases.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-020. Verification Must Evaluate Diff Relevance
- **ID:** REQ-020
- **Title:** Verification Must Evaluate Diff Relevance
- **Description:** Verification must determine whether a diff impacts any requirement or test case and ignore irrelevant changes.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-021. Verification Must Evaluate Test Results
- **ID:** REQ-021
- **Title:** Verification Must Evaluate Test Results
- **Description:** Verification must compare actual output against expected and quantify failures.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-022. Verification Must Evaluate Contradictions and Uncertainty
- **ID:** REQ-022
- **Title:** Verification Must Evaluate Contradictions and Uncertainty
- **Description:** Verification must identify logical contradictions and uncertainty metrics.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-023. Requirement Schema Must Include Source Location, Type, Priority, Confidence, Status, and Timestamps
- **ID:** REQ-023
- **Title:** Requirement Schema Must Include Source Location, Type, Priority, Confidence, Status, and Timestamps
- **Description:** Each requirement record must contain these schema fields.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-024. Test Case Model Must Include Required Fields
- **ID:** REQ-024
- **Title:** Test Case Model Must Include Required Fields
- **Description:** All test case records must contain all required fields.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-025. Work Item Model Must Include Required Fields
- **ID:** REQ-025
- **Title:** Work Item Model Must Include Required Fields
- **Description:** Each work item record must contain required fields such as id, status, priority.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-026. Preflight Output Schema Must Include Decision, Work Item ID, Priority, Requirement IDs, Test Case IDs, Confidence Target
- **ID:** REQ-026
- **Title:** Preflight Output Schema Must Include Decision, Work Item ID, Priority, Requirement IDs, Test Case IDs, Confidence Target
- **Description:** Structured preflight output must list these fields.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-027. Verification Input Must Include Diffs, Tests, Logs, and Changed Files
- **ID:** REQ-027
- **Title:** Verification Input Must Include Diffs, Tests, Logs, and Changed Files
- **Description:** Verification input must contain file diffs, test results, execution logs, and list of changed files.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-028. Retry Strategy Mapping Must Be Defined
- **ID:** REQ-028
- **Title:** Retry Strategy Mapping Must Be Defined
- **Description:** Retries map failures to strategies such as narrow_scope, expand_scope, fix_tests, rollback, and stop.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-029. Integration Adapter Interface Must Provide Required Capabilities
- **ID:** REQ-029
- **Title:** Integration Adapter Interface Must Provide Required Capabilities
- **Description:** Specsmith must provide filesystem and shell execution functions via the integration adapter.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-030. Specsmith CLI Commands Must Be Explicitly Defined
- **ID:** REQ-030
- **Title:** Specsmith CLI Commands Must Be Explicitly Defined
- **Description:** Specsmith CLI must expose commands such as preflight, verify, requirements list/show/accept/reject, tests generate/list, status, and ledger list.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-031. Sequencing Rules Must Enforce Valid States
- **ID:** REQ-031
- **Title:** Sequencing Rules Must Enforce Valid States
- **Description:** Bootstrap and sequence transitions must follow the defined order.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-032. Configuration Settings for Optional Features
- **ID:** REQ-032
- **Title:** Configuration Settings for Optional Features
- **Description:** Specsmith must read optional feature flags from .specsmith/config.yml.
- **Status:** defined
- **Source:** .specsmith/config.yml, ARCHITECTURE.md

## REQ-033. Default Enablement of Optional Features
- **ID:** REQ-033
- **Title:** Default Enablement of Optional Features
- **Description:** All optional Specsmith features must be enabled by default unless overridden.
- **Status:** defined
- **Source:** .specsmith/config.yml, ARCHITECTURE.md

## REQ-034. Evidence ZIP Archive Generation
- **ID:** REQ-034
- **Title:** Evidence ZIP Archive Generation
- **Description:** Specsmith must generate evidence ZIP archive for selected artifacts.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-035. Evidence Manifest Generation
- **ID:** REQ-035
- **Title:** Evidence Manifest Generation
- **Description:** Manifest must list artifacts and metadata in evidence archive.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-036. Per‑File SHA‑256 Hashing in Evidence
- **ID:** REQ-036
- **Title:** Per‑File SHA‑256 Hashing in Evidence
- **Description:** Every file in evidence archive must have a SHA‑256 hash.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-037. Final Evidence ZIP SHA‑256 Hash
- **ID:** REQ-037
- **Title:** Final Evidence ZIP SHA‑256 Hash
- **Description:** The final evidence ZIP archive must have a computed SHA‑256 hash.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-038. Author/Owner Metadata Capture
- **ID:** REQ-038
- **Title:** Author/Owner Metadata Capture
- **Description:** Evidence archive must record author/owner information for each artifact.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-039. Git Commit Metadata Inclusion
- **ID:** REQ-039
- **Title:** Git Commit Metadata Inclusion
- **Description:** Evidence archive must incorporate current git commit hash when available.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-040. Ledger Reference Inclusion
- **ID:** REQ-040
- **Title:** Ledger Reference Inclusion
- **Description:** Evidence archive must reference relevant ledger entries for traceability.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-041. Trusted Timestamp Token Support
- **ID:** REQ-041
- **Title:** Trusted Timestamp Token Support
- **Description:** Evidence archive may include an RFC 3161 trusted timestamp token if enabled.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-042. Legal/IP Disclaimer Requirement
- **ID:** REQ-042
- **Title:** Legal/IP Disclaimer Requirement
- **Description:** Specsmith must provide a disclaimer that evidence does not guarantee legal ownership.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-043. Ledger Event Hash Chaining
- **ID:** REQ-043
- **Title:** Ledger Event Hash Chaining
- **Description:** Each ledger event must be hashed and chained to previous event for tamper evidence.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-044. Ledger Event on Work Proposal
- **ID:** REQ-044
- **Title:** Ledger Event on Work Proposal
- **Description:** Specsmith must create ledger event when a work item is proposed.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-045. Ledger Event on Work Completion
- **ID:** REQ-045
- **Title:** Ledger Event on Work Completion
- **Description:** Specsmith must create ledger event upon completion of each work item or batch.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-046. README.md Generation and Synchronization
- **ID:** REQ-046
- **Title:** README.md Generation and Synchronization
- **Description:** Specsmith must generate README.md if missing and keep it synchronized.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-047. CHANGELOG.md Generation and Synchronization
- **ID:** REQ-047
- **Title:** CHANGELOG.md Generation and Synchronization
- **Description:** Specsmith must generate CHANGELOG.md following Keep a Changelog and keep it updated.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-048. Keep a Changelog Compliance
- **ID:** REQ-048
- **Title:** Keep a Changelog Compliance
- **Description:** CHANGELOG.md must follow Keep a Changelog format.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-049. Semantic Versioning Support
- **ID:** REQ-049
- **Title:** Semantic Versioning Support
- **Description:** Specsmith must understand and support Semantic Versioning for releases.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-050. Guided Version Bump Workflow
- **ID:** REQ-050
- **Title:** Guided Version Bump Workflow
- **Description:** Specsmith must provide a guided workflow for bumping version numbers.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-051. Guided Release Strategy Workflow
- **ID:** REQ-051
- **Title:** Guided Release Strategy Workflow
- **Description:** Specsmith must offer a guided workflow to determine release strategy.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-052. Guided Branching Strategy Workflow
- **ID:** REQ-052
- **Title:** Guided Branching Strategy Workflow
- **Description:** Specsmith must offer a guided workflow for selecting a branching strategy.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-053. Default GitFlow Branching Model
- **ID:** REQ-053
- **Title:** Default GitFlow Branching Model
- **Description:** Specsmith’s default branching model is GitFlow unless overridden.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-054. Guided Branching Modification
- **ID:** REQ-054
- **Title:** Guided Branching Modification
- **Description:** Specsmith must allow guided modifications to the branching model.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-055. GitHub License Generation
- **ID:** REQ-055
- **Title:** GitHub License Generation
- **Description:** Specsmith must generate license files compatible with GitHub/choosealicense.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-056. Commercial License Drafting Guidance
- **ID:** REQ-056
- **Title:** Commercial License Drafting Guidance
- **Description:** Specsmith must provide guidance for drafting commercial licenses, including disclaimer.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-057. Local Git Commit After Work
- **ID:** REQ-057
- **Title:** Local Git Commit After Work
- **Description:** Specsmith should commit local changes after each completed work item or batch.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-058. Confidence Threshold Configuration
- **ID:** REQ-058
- **Title:** Confidence Threshold Configuration
- **Description:** Specsmith must allow configuring epistemic confidence threshold via config file.
- **Status:** defined
- **Source:** .specsmith/config.yml, ARCHITECTURE.md

## REQ-059. Iteration Continuation Until Threshold
- **ID:** REQ-059
- **Title:** Iteration Continuation Until Threshold
- **Description:** Work iterations continue until epistemic confidence reaches threshold.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-060. Indefinite Iteration Default
- **ID:** REQ-060
- **Title:** Indefinite Iteration Default
- **Description:** Specsmith defaults to indefinite iteration unless user sets limits.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-061. Max Iterations Configuration
- **ID:** REQ-061
- **Title:** Max Iterations Configuration
- **Description:** Specsmith must allow configuring maximum iterations.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-062. Token/Cost/Time Limits Configuration
- **ID:** REQ-062
- **Title:** Token/Cost/Time Limits Configuration
- **Description:** Specsmith must allow configuring token spend, session cost, and elapsed time limits.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-063. Stop‑and‑Align Behavior
- **ID:** REQ-063
- **Title:** Stop‑and‑Align Behavior
- **Description:** Specsmith must stop when confidence cannot improve and engage user for alignment.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-064. Interactive Correction Workflow
- **ID:** REQ-064
- **Title:** Interactive Correction Workflow
- **Description:** After stopping, Specsmith should provide an interactive correction workflow.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-065. Nexus Runtime Must Not Own Governance
- **ID:** REQ-065
- **Title:** Nexus Runtime Must Not Own Governance
- **Description:** The Nexus agent runtime must defer preflight, requirement mapping, verification, retry decisions, and ledger writing to Specsmith.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-066. Nexus Must Provide Required Agent Roles
- **ID:** REQ-066
- **Title:** Nexus Must Provide Required Agent Roles
- **Description:** Nexus must instantiate PlannerAgent, ShellAgent, CodeAgent, ReviewerAgent, MemoryAgent, GitAgent, HumanProxyAgent, and an Executor node.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-067. Nexus Tool Layer Must Expose Required Tools
- **ID:** REQ-067
- **Title:** Nexus Tool Layer Must Expose Required Tools
- **Description:** Nexus must expose run_shell, read_file, write_file, patch_file, list_files, grep, git_diff, git_status, run_tests, open_url, search_docs, and remember_project_fact.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-068. Nexus Safety Middleware Must Block Unsafe Commands
- **ID:** REQ-068
- **Title:** Nexus Safety Middleware Must Block Unsafe Commands
- **Description:** The safety middleware must block or require explicit approval for unsafe shell patterns including rm -rf, git push, docker compose down -v, database migrations, deploy commands, and secret reads.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-069. Nexus Tool Arguments Must Be JSON Validated
- **ID:** REQ-069
- **Title:** Nexus Tool Arguments Must Be JSON Validated
- **Description:** All Nexus tool calls must validate that arguments are JSON-serializable before execution.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-070. Nexus Must Normalize File Paths
- **ID:** REQ-070
- **Title:** Nexus Must Normalize File Paths
- **Description:** All file paths supplied to Nexus tools must be normalized to absolute, resolved paths before access.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-071. Nexus Must Index the Repository
- **ID:** REQ-071
- **Title:** Nexus Must Index the Repository
- **Description:** Nexus must populate .repo-index/ with files.json, tags, test_commands.json, architecture.md, and conventions.md as available.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-072. Nexus REPL Must Support Slash Commands
- **ID:** REQ-072
- **Title:** Nexus REPL Must Support Slash Commands
- **Description:** The Nexus REPL must support /plan, /ask, /fix, /test, /commit, /pr, /undo, /context, /exit.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-073. Nexus Output Contract
- **ID:** REQ-073
- **Title:** Nexus Output Contract
- **Description:** Each Nexus task response must include sections Plan, Commands to run, Files changed, Diff, Test results, and Next action.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-074. vLLM Image Must Be Pinned
- **ID:** REQ-074
- **Title:** vLLM Image Must Be Pinned
- **Description:** The Nexus docker-compose.yml must pin the vLLM image to a specific tag (vllm/vllm-openai:v0.8.5) and not use latest.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-075. vLLM Must Serve l1-nexus Model
- **ID:** REQ-075
- **Title:** vLLM Must Serve l1-nexus Model
- **Description:** The Nexus docker-compose.yml must publish the served model as l1-nexus and use the Hermes tool-call parser.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-076. Nexus Tool Executor Registration Must Be Unique
- **ID:** REQ-076
- **Title:** Nexus Tool Executor Registration Must Be Unique
- **Description:** Each Nexus tool must be registered with the AG2 executor exactly once; LLM-side tool signatures may be attached to multiple caller agents but the execution function must not be re-registered to avoid AG2 override warnings.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-077. Safe Cleanup Must Default to Dry-Run
- **ID:** REQ-077
- **Title:** Safe Cleanup Must Default to Dry-Run
- **Description:** The Specsmith safe-cleanup capability must default to dry-run mode and only delete files when an explicit apply flag is provided.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-078. Safe Cleanup Must Use a Hard-Coded Target List
- **ID:** REQ-078
- **Title:** Safe Cleanup Must Use a Hard-Coded Target List
- **Description:** Safe cleanup must only consider the canonical built-in target list and must reject user-supplied arbitrary paths.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-079. Safe Cleanup Must Protect Governance and Source
- **ID:** REQ-079
- **Title:** Safe Cleanup Must Protect Governance and Source
- **Description:** Safe cleanup must refuse to delete .git, .specsmith, governance markdown files, pyproject.toml, README.md, LICENSE, CHANGELOG.md, src/, tests/, docs/, scripts/, .repo-index/, .github/, .vscode/, third-party agent integration directories (such as .agents/), and project configuration dotfiles.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-080. Safe Cleanup Must Emit a Structured Report
- **ID:** REQ-080
- **Title:** Safe Cleanup Must Emit a Structured Report
- **Description:** Safe cleanup must return a report containing the lists of removed paths, skipped paths with reasons, and total bytes reclaimed, suitable for inclusion as ledger evidence.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-081. Safe Cleanup Must Be Exposed via Specsmith CLI
- **ID:** REQ-081
- **Title:** Safe Cleanup Must Be Exposed via Specsmith CLI
- **Description:** The Specsmith CLI must expose the safe cleanup capability as `specsmith clean`, supporting `--apply`, `--json`, and `--project-dir`. When `--apply` is used and `LEDGER.md` exists, the run must be recorded as a `cleanup` ledger event tagged with REQ-077..REQ-080.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-082. CLI Console Must Be UTF-8 Safe Across Platforms
- **ID:** REQ-082
- **Title:** CLI Console Must Be UTF-8 Safe Across Platforms
- **Description:** All Specsmith CLI output (rich Console) must render UTF-8 glyphs (such as warning, arrow, check, cross) without raising UnicodeEncodeError on Windows code pages such as cp1252. The console factory must reconfigure stdout/stderr to UTF-8 and disable rich's legacy_windows renderer.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-083. Canonical Test Specification File Is TESTS.md
- **ID:** REQ-083
- **Title:** Canonical Test Specification File Is TESTS.md
- **Description:** The canonical test specification file is named `TESTS.md` (replacing the legacy names `TEST_SPEC.md`, `TEST-SPEC.md`, and `TEST-SPECS.md`). Specsmith code, governance documents, templates, scaffolder output, importer overlay, auditor checks, retrieval index, exporter, validator, REPL skill files, ReadTheDocs site, and CLI help must all reference `TESTS.md`. Legacy filenames must not be created by new scaffolds, must be auto-renamed by `specsmith migrate-project`, and must not be referenced in user-facing docs.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-084. Natural-Language Governance Broker
- **ID:** REQ-084
- **Title:** Natural-Language Governance Broker
- **Description:** Specsmith must expose a Nexus broker module (`specsmith.agent.broker`) that translates plain-language user utterances into Specsmith-governed work without the user reasoning about REQ IDs, TEST IDs, or work items. The broker must classify intent (read-only ask vs change vs release), infer affected scope from the local `.repo-index` and existing requirements, invoke `specsmith preflight` and `specsmith verify` as the only sources of governance decisions, render plain-language plans and outcomes, hide REQ/TEST/work-item IDs by default (revealed only on `/why`, `/show-governance`, or `--verbose`), bound retries per REQ-014, escalate to a single user clarification on stop-and-align (REQ-063), and never invent governance content (REQ/TEST drafting requires explicit user confirmation).
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-085. specsmith preflight CLI Subcommand
- **ID:** REQ-085
- **Title:** specsmith preflight CLI Subcommand
- **Description:** The Specsmith CLI must expose a `specsmith preflight <utterance>` subcommand that reads `REQUIREMENTS.md` and `.specsmith/` state, classifies intent and infers scope, and emits a JSON object with at least the keys `decision` (one of `accepted`, `needs_clarification`, `blocked`, `rejected`), `work_item_id`, `requirement_ids`, `test_case_ids`, `confidence_target`, and `instruction`. Read-only asks accept by default, destructive intents require clarification, and changes with no matching scope return `needs_clarification` with a one-sentence question. The CLI must support `--project-dir`, `--json`, and `--verbose`.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-086. Nexus REPL Must Gate Execution on Preflight Acceptance
- **ID:** REQ-086
- **Title:** Nexus REPL Must Gate Execution on Preflight Acceptance
- **Description:** When a non-slash utterance flows through the broker, the Nexus REPL must only invoke the AG2 orchestrator's `run_task` if the preflight decision is `accepted`. For any other decision (`needs_clarification`, `blocked`, `rejected`), the REPL must print the broker's plain-language clarification or rejection and return to the prompt without executing.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-087. Nexus REPL Must Drive Execution Through the Bounded-Retry Harness
- **ID:** REQ-087
- **Title:** Nexus REPL Must Drive Execution Through the Bounded-Retry Harness
- **Description:** When the preflight decision is `accepted`, the Nexus REPL must drive the AG2 orchestrator through `specsmith.agent.broker.execute_with_governance`, supplying an executor that wraps `orchestrator.run_task` and synthesizes a result dict (`equilibrium`, `confidence`, `summary`). The harness must honor `DEFAULT_RETRY_BUDGET` (REQ-014), surface the single clarifying question on stop-and-align (REQ-063), and never call `run_task` directly outside the harness.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-088. specsmith preflight Must Resolve Test Case IDs From Machine State
- **ID:** REQ-088
- **Title:** specsmith preflight Must Resolve Test Case IDs From Machine State
- **Description:** The `specsmith preflight` CLI must populate `test_case_ids` in its JSON payload by joining the matched `requirement_ids` against `.specsmith/testcases.json` (or `TESTS.md` when the JSON is unavailable). When the resolved set is non-empty the CLI must include every matching `TEST-NNN` id and must never invent ids not present in machine state.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-089. Nexus Live l1-nexus Smoke Test
- **ID:** REQ-089
- **Title:** Nexus Live l1-nexus Smoke Test
- **Description:** Specsmith must ship a `scripts/nexus_smoke.py` script that POSTs a minimal chat-completions request to a running vLLM `l1-nexus` container at `http://localhost:8000/v1/chat/completions` and reports whether the model responded with a well-formed `choices[0].message.content`. A pytest integration test must invoke the script and skip unless the environment variable `NEXUS_LIVE=1` is set, so the suite stays green offline but is verifiable when the container is up.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-090. Nexus Documentation Must Describe Broker, Preflight, and Gated Execution
- **ID:** REQ-090
- **Title:** Nexus Documentation Must Describe Broker, Preflight, and Gated Execution
- **Description:** `ARCHITECTURE.md`, `README.md`, and `docs/` must describe the natural-language broker (REQ-084), the `specsmith preflight` CLI (REQ-085), the REPL execution gate (REQ-086), and the bounded-retry harness (REQ-087), including the `/why` toggle and an end-to-end example flow. Documentation must not surface REQ/TEST/WI tokens to the user except inside the explicit `/why` block.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-091. Orchestrator Must Return a Structured TaskResult
- **ID:** REQ-091
- **Title:** Orchestrator Must Return a Structured TaskResult
- **Description:** `orchestrator.run_task` must return a `TaskResult` dataclass with at least the fields `equilibrium: bool`, `confidence: float`, `summary: str`, `files_changed: list[str]`, and `test_results: dict`. The Nexus REPL's broker branch must consume this dataclass directly when feeding `execute_with_governance` (REQ-087); the broker must not synthesize `equilibrium` from a boolean cast of the summary string.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-092. specsmith preflight CLI Must Use Decision-Specific Exit Codes
- **ID:** REQ-092
- **Title:** specsmith preflight CLI Must Use Decision-Specific Exit Codes
- **Description:** The `specsmith preflight` CLI must exit `0` for `accepted`, `2` for `needs_clarification`, and `3` for `blocked` or `rejected` decisions, so CI pipelines and shell wrappers can branch on intent without parsing the JSON payload. The JSON payload must continue to print on stdout for both success and non-zero exits.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-093. Accepted preflight Must Record a Ledger Event
- **ID:** REQ-093
- **Title:** Accepted preflight Must Record a Ledger Event
- **Description:** When `specsmith preflight` produces an `accepted` decision and `LEDGER.md` exists in the project root, the CLI must append a `preflight` ledger event tagged with `REQ-085` plus the resolved `requirement_ids`. The event must record the utterance, the assigned `work_item_id`, and the `confidence_target`, so every accepted preflight is traceable end-to-end.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-094. /why Must Surface Post-Run Governance in the REPL
- **ID:** REQ-094
- **Title:** /why Must Surface Post-Run Governance in the REPL
- **Description:** When `verbose_governance` is on (toggled by `/why` or `/show-governance`), after the REPL drives `execute_with_governance` for an accepted utterance it must print a single `[/why]` block summarizing the assigned `work_item_id`, the matched `requirement_ids` and `test_case_ids`, the post-run confidence, and whether the bounded-retry harness reached equilibrium. When verbose mode is off, the post-run governance block must not be emitted.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-095. Nexus Live Smoke Run Must Be Reproducible Evidence
- **ID:** REQ-095
- **Title:** Nexus Live Smoke Run Must Be Reproducible Evidence
- **Description:** A live or honestly-skipped invocation of `scripts/nexus_smoke.py` must be captured under `.specsmith/runs/WI-NEXUS-011/logs.txt` so the project ledger preserves at least one reproducible record of the broker -> preflight -> orchestrator -> vLLM end-to-end path (or a documented reason the live container could not be reached in the current environment).
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-096. Bounded-Retry Harness Must Map Failures to Retry Strategies
- **ID:** REQ-096
- **Title:** Bounded-Retry Harness Must Map Failures to Retry Strategies
- **Description:** When `execute_with_governance` exhausts its retry budget (REQ-014), it must classify the last executor report against the canonical retry strategy mapping (REQ-028): `narrow_scope`, `expand_scope`, `fix_tests`, `rollback`, or `stop`. The classification must be exposed on `RunResult.strategy` and surfaced in the clarifying question (REQ-063) so the user gets one concrete next-action label rather than only a free-form sentence.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-097. specsmith verify CLI Subcommand
- **ID:** REQ-097
- **Title:** specsmith verify CLI Subcommand
- **Description:** The Specsmith CLI must expose a `specsmith verify` subcommand that consumes the verification input contract (REQ-027): file diffs, test results, execution logs, and changed files (paths or `--stdin` JSON). The subcommand must emit a JSON object with at least `equilibrium`, `confidence`, `summary`, `files_changed`, `test_results`, and `retry_strategy`. Exit code 0 on equilibrium with confidence ≥ the configured threshold, 2 when retry is recommended, and 3 when stop-and-align is required.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-098. Confidence Threshold Must Be Read From .specsmith/config.yml
- **ID:** REQ-098
- **Title:** Confidence Threshold Must Be Read From .specsmith/config.yml
- **Description:** Both `specsmith preflight` and the broker's `run_preflight` helper must consult `.specsmith/config.yml` for the `epistemic.confidence_threshold` value (REQ-058) and use it as the floor for the JSON `confidence_target` field whenever it is greater than the heuristic default. When the config file is absent or unparseable, the existing heuristic defaults must continue to apply.
- **Status:** defined
- **Source:** .specsmith/config.yml, ARCHITECTURE.md

## REQ-099. Accepted Preflight Must Record a Distinct work_proposal Event
- **ID:** REQ-099
- **Title:** Accepted Preflight Must Record a Distinct work_proposal Event
- **Description:** When `specsmith preflight` produces an `accepted` decision and assigns a brand-new `work_item_id`, the CLI must append a `work_proposal` ledger event in addition to the existing `preflight` event (REQ-044). The `work_proposal` entry must reference REQ-044 and REQ-085, include the `work_item_id` and matched `requirement_ids`, and must NOT be emitted when the underlying `work_item_id` already appears in `LEDGER.md` (no duplicate proposals).
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-100. Broker Scope Inference May Surface Stress-Test Critical Failures
- **ID:** REQ-100
- **Title:** Broker Scope Inference May Surface Stress-Test Critical Failures
- **Description:** When the user passes `--stress` to `specsmith preflight` and the matched requirements set is non-empty, the CLI must invoke the existing AEE `StressTester` against those belief artifacts and surface any critical failures in the JSON payload as a `stress_warnings` list. The narration (verbose mode) must include a one-sentence plain-English warning when at least one critical failure is found. The flag must default off so unrelated tests continue to pass.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-101. Lint Baseline Must Be Clean
- **ID:** REQ-101
- **Title:** Lint Baseline Must Be Clean
- **Description:** `ruff check src/ tests/` and `ruff format --check src/ tests/` must both exit zero on `develop`. The lint job in `.github/workflows/ci.yml` enforces this contract. Per-file ignores in `pyproject.toml` are reserved for documentation modules whose long lines are intentional (e.g. `toolrules.py`, `tool_installer.py`).
- **Status:** defined
- **Source:** .github/workflows/ci.yml, pyproject.toml

## REQ-102. Type-Check Baseline Must Be Clean
- **ID:** REQ-102
- **Title:** Type-Check Baseline Must Be Clean
- **Description:** `mypy src/specsmith/` must exit zero on `develop`. Strict-mypy is preserved for the historically-typed modules; dynamically-typed modules in `specsmith.agent.*`, `specsmith.console_utils`, `specsmith.serve`, and the agent-orchestrator surface are explicitly enumerated in the `[[tool.mypy.overrides]]` `ignore_errors=true` block of `pyproject.toml` until they are individually annotated.
- **Status:** defined
- **Source:** .github/workflows/ci.yml, pyproject.toml

## REQ-103. Security Baseline Tolerates Unfixed pip Advisory
- **ID:** REQ-103
- **Title:** Security Baseline Tolerates Unfixed pip Advisory
- **Description:** The CI security job must upgrade pip to the latest release before invoking `pip-audit`, and must pass the `--ignore-vuln CVE-2026-3219` flag for the unfixed pip advisory so the runner's own pip version does not block PRs. Specsmith's actual runtime dependencies (click, jinja2, pyyaml, pydantic, rich) must remain pip-audit clean; any new advisory against them must trigger a dependency bump rather than another ignore-flag.
- **Status:** defined
- **Source:** .github/workflows/ci.yml

## REQ-104. Work Items Must Mirror Implemented REQs
- **ID:** REQ-104
- **Title:** Work Items Must Mirror Implemented REQs
- **Description:** `.specsmith/workitems.json` must derive from `.specsmith/requirements.json` and `.specsmith/testcases.json`. For each REQ-N there must be a matching WORK-N entry with `requirement_id=REQ-N`, `test_case_ids` listing every TEST joined by `requirement_id`, and `status=complete` when the REQ is implemented in source. The `scripts/sync_workitems.py` helper is the canonical sync.
- **Status:** defined
- **Source:** scripts/sync_workitems.py, .specsmith/workitems.json

## REQ-105. Live Smoke Evidence Must Be Reproducible Or Honestly Skipped
- **ID:** REQ-105
- **Title:** Live Smoke Evidence Must Be Reproducible Or Honestly Skipped
- **Description:** A live or honestly-skipped invocation of `scripts/nexus_smoke.py` against the configured `l1-nexus` model must be captured under `.specsmith/runs/WI-NEXUS-011/logs.txt`. The skip note must include a fresh probe attempt, a timestamp, and the hardware/environment reason the live container could not be reached.
- **Status:** defined
- **Source:** .specsmith/runs/WI-NEXUS-011/logs.txt, scripts/nexus_smoke.py

## REQ-106. Kairos Must Surface Governance Commands
- **ID:** REQ-106
- **Title:** Kairos Must Surface Governance Commands
- **Description:** The Kairos terminal client must provide UI access to the three primary governance operations: preflight gate, verify, and governance trace (`/why`). These are surfaced via the Governance settings page and the BYOE proxy at `http://127.0.0.1:7700`. *Note: the legacy `specsmith-vscode` commands (`specsmith.runPreflight`, `specsmith.runVerify`, `specsmith.toggleWhy`) are deprecated; Kairos is the flagship client as of v0.10.1.*
- **Status:** defined
- **Source:** app/src/settings_view/governance_page.rs, kairos_governance crate

## REQ-107. ARCHITECTURE.md Must Reflect Current State
- **ID:** REQ-107
- **Title:** ARCHITECTURE.md Must Reflect Current State
- **Description:** `ARCHITECTURE.md` must contain a 'Current State' section listing the realized broker, harness, retry strategies, CI baseline, Kairos governance integration, live-smoke evidence note, and documentation surface. The section is the source of truth for 'the system as built' and must be updated each time a release is cut.
- **Status:** defined
- **Source:** ARCHITECTURE.md

## REQ-108. Real Verifier Signal Must Drive Confidence
- **ID:** REQ-108
- **Title:** Real Verifier Signal Must Drive Confidence
- **Description:** `Orchestrator._build_task_result` must derive `TaskResult.confidence` and `equilibrium` from a real verifier (`src/specsmith/agent/verifier.py`) that inspects test results, ruff output, and mypy output for the changed files. The hardcoded 0.85 / 0.4 / 0.0 placeholder must be removed.
- **Status:** defined
- **Source:** src/specsmith/agent/verifier.py, src/specsmith/agent/orchestrator.py

## REQ-109. Live `l1-nexus` Smoke Overlay Must Produce ok=true on 7B Hardware
- **ID:** REQ-109
- **Title:** Live `l1-nexus` Smoke Overlay Must Produce ok=true on 7B Hardware
- **Description:** Specsmith ships a `docker-compose.smoke.yml` overlay that swaps `l1-nexus` to a 7B GPTQ-Int4 model fitting <=8 GB VRAM, and `.specsmith/runs/WI-NEXUS-029/logs.txt` documents how to capture an `ok: true` smoke result with `NEXUS_LIVE=1` against that overlay.
- **Status:** defined
- **Source:** docker-compose.smoke.yml, .specsmith/runs/WI-NEXUS-029/logs.txt

## REQ-110. End-to-End Nexus Path Must Be Integration-Tested
- **ID:** REQ-110
- **Title:** End-to-End Nexus Path Must Be Integration-Tested
- **Description:** `tests/test_e2e_nexus.py` exercises the broker -> preflight -> harness -> orchestrator -> verifier path with a `FakeOrchestrator` and asserts ledger events, `RunResult.success`, and retry-strategy classification on a scripted failure-then-recovery sequence.
- **Status:** defined
- **Source:** tests/test_e2e_nexus.py

## REQ-111. Mypy Strict Carveout Must Shrink Toward Zero
- **ID:** REQ-111
- **Title:** Mypy Strict Carveout Must Shrink Toward Zero
- **Description:** At least the four newly-annotated dynamic agent modules (`broker`, `safety`, `console_utils`, `indexer`) are fully type-annotated and removed from the `[[tool.mypy.overrides]] ignore_errors=true` block in `pyproject.toml`. The remaining carveout (orchestrator, repl, tools, cleanup, serve) is documented as a 1.x cleanup target.
- **Status:** defined
- **Source:** pyproject.toml, src/specsmith/agent/*.py, src/specsmith/console_utils.py

## REQ-112. Streaming Token Bridge Must Emit JSONL Events
- **ID:** REQ-112
- **Title:** Streaming Token Bridge Must Emit JSONL Events
- **Description:** A new `specsmith chat <utterance> --json-events` CLI subcommand drives the broker + harness end-to-end and emits a JSONL event stream on stdout with at least the event types `block_start`, `token`, `tool_call`, `tool_result`, `block_complete`, and `task_complete`. Each event is a single JSON object on its own line.
- **Status:** defined
- **Source:** src/specsmith/cli.py, src/specsmith/agent/events.py

## REQ-113. Block-Based Output Schema
- **ID:** REQ-113
- **Title:** Block-Based Output Schema
- **Description:** Every `block_start` event carries a `block_id`, `kind` (one of `plan`, `message`, `tool_call`, `tool_result`, `diff`, `test_results`, `verdict`), `agent`, and `timestamp`. The corresponding `block_complete` reuses the same `block_id`. Schema is documented in `docs/site/chat-events.md`.
- **Status:** defined
- **Source:** src/specsmith/agent/events.py, docs/site/chat-events.md

## REQ-114. Plan Block Must Surface Steps
- **ID:** REQ-114
- **Title:** Plan Block Must Surface Steps
- **Description:** When the broker classifies an utterance as a `change` and preflight is `accepted`, the chat stream must emit a `plan` block whose payload is a list of `{step_id, title, status}` items. Status transitions (`pending` -> `running` -> `done` / `failed`) are emitted as `plan_step` events keyed by `step_id`.
- **Status:** defined
- **Source:** src/specsmith/agent/events.py

## REQ-115. Permission/Autonomy Tier Must Be Honored End-to-End
- **ID:** REQ-115
- **Title:** Permission/Autonomy Tier Must Be Honored End-to-End
- **Description:** `specsmith chat` accepts `--profile {safe,standard,open,admin}` (default reads `scaffold.yml`). Under `safe`, every tool call emits a `tool_request` event and waits for an inbound `tool_decision` line on stdin (`{decision: 'approve'|'deny'}`). Under `standard` / `open` the harness proceeds without prompting. The selected profile is recorded in the ledger entry.
- **Status:** defined
- **Source:** src/specsmith/cli.py, src/specsmith/profiles.py

## REQ-116. Inline Diff Review Must Round-Trip Comments
- **ID:** REQ-116
- **Title:** Inline Diff Review Must Round-Trip Comments
- **Description:** `specsmith chat` emits a `diff` block per file changed by the orchestrator; subsequent stdin lines of the form `{type: 'comment', block_id, path, line, body}` are stored in the session memory and surfaced to the bounded-retry harness as additional context on the next attempt. `--comment` flag on `specsmith verify` does the equivalent for non-streaming use.
- **Status:** defined
- **Source:** src/specsmith/agent/events.py, src/specsmith/cli.py

## REQ-117. Predict-Only Preflight Must Not Allocate a Work Item
- **ID:** REQ-117
- **Title:** Predict-Only Preflight Must Not Allocate a Work Item
- **Description:** `specsmith preflight <utterance> --predict-only --json` returns the same JSON shape as the canonical `preflight` (intent, requirement_ids, instruction, etc.) but with `work_item_id == ''`, no ledger event written, and a new `predicted_refinement` field that suggests a tightened utterance. Used by IDE autocomplete.
- **Status:** defined
- **Source:** src/specsmith/cli.py

## REQ-118. Kairos Must Surface specsmith chat Stream
- **ID:** REQ-118
- **Title:** Kairos Must Surface specsmith chat Stream
- **Description:** The Kairos governance proxy (`/v1/chat/completions`) consumes the `specsmith chat --json-events` JSONL stream and exposes it to the agent session. *The deprecated `specsmith-vscode` `specsmith.openChat` command served this purpose for the VS Code extension; it has been superseded by the Kairos BYOE proxy.*
- **Status:** defined
- **Source:** app/src/settings_view/governance_page.rs, kairos_governance crate

## REQ-119. Project Rules Must Auto-Inject Into the System Prompt
- **ID:** REQ-119
- **Title:** Project Rules Must Auto-Inject Into the System Prompt
- **Description:** `src/specsmith/agent/rules.py:load_rules(project_dir)` reads `docs/governance/*_RULES.md` and the H-rules from `AGENTS.md`, returning a single deterministic system-prompt prefix string. The orchestrator prepends this string to every AG2 agent's `system_message` at construction time.
- **Status:** defined
- **Source:** src/specsmith/agent/rules.py, src/specsmith/agent/orchestrator.py

## REQ-120. Persistent Session Memory Must Be Token-Budgeted
- **ID:** REQ-120
- **Title:** Persistent Session Memory Must Be Token-Budgeted
- **Description:** `src/specsmith/agent/memory.py` provides `append_turn(session_id, turn)` and `recent_turns(session_id, max_chars)` that read/write `.specsmith/sessions/<session_id>/turns.jsonl`. `specsmith chat --session-id <id>` injects the most recent N turns (within `max_chars`) into the orchestrator's first message.
- **Status:** defined
- **Source:** src/specsmith/agent/memory.py

## REQ-121. MCP Tool Consumption Must Be Configuration-Driven
- **ID:** REQ-121
- **Title:** MCP Tool Consumption Must Be Configuration-Driven
- **Description:** `src/specsmith/agent/mcp.py:load_mcp_tools(project_dir)` reads `.specsmith/mcp.yml` (a list of `{name, command, args, env}` entries) and returns Nexus-tool wrappers that proxy to each external MCP server via stdio. The Specsmith safety middleware wraps every MCP tool call.
- **Status:** defined
- **Source:** src/specsmith/agent/mcp.py, .specsmith/mcp.yml

## REQ-122. Dynamic Agent/Model Routing Must Be Pluggable
- **ID:** REQ-122
- **Title:** Dynamic Agent/Model Routing Must Be Pluggable
- **Description:** `src/specsmith/agent/router.py:choose_tier(intent, scope, retry_count)` returns one of `{coder, heavy, fast}` based on `.specsmith/config.yml routing:` overrides. The orchestrator builds a model-config map keyed by tier and selects the appropriate `llm_config` per agent.
- **Status:** defined
- **Source:** src/specsmith/agent/router.py, .specsmith/config.yml

## REQ-123. Notebook Capture and Replay
- **ID:** REQ-123
- **Title:** Notebook Capture and Replay
- **Description:** `specsmith notebook record --session-id <id> --slug <name>` writes `docs/notebooks/<slug>.md` with the captured turns; `specsmith notebook replay <slug>` re-runs each utterance through `specsmith chat` (using the recorded `--profile`), re-checking governance gates.
- **Status:** defined
- **Source:** src/specsmith/cli.py, docs/notebooks/

## REQ-124. Performance Baseline Must Be Measured and Tracked
- **ID:** REQ-124
- **Title:** Performance Baseline Must Be Measured and Tracked
- **Description:** `scripts/perf_smoke.py` synthesizes a 1000-REQ `REQUIREMENTS.md` in tmp_path, runs `specsmith preflight` 50 times, and writes p50 / p95 / p99 to `.specsmith/perf/baseline.json`. CI reports the deltas vs the committed baseline as a non-blocking warning.
- **Status:** defined
- **Source:** scripts/perf_smoke.py, .specsmith/perf/baseline.json

## REQ-125. Multi-Session Parallel Agents
- **ID:** REQ-125
- **Title:** Multi-Session Parallel Agents
- **Description:** `specsmith chat` accepts `--parent-session <id>`. When set, the spawned session's `task_complete` event also writes a `sub_session_complete` event into the parent's session log so the parent's plan-block can surface child outcomes.
- **Status:** defined
- **Source:** src/specsmith/cli.py, src/specsmith/agent/memory.py

## REQ-127. Onboarding Path Must Be Verified
- **ID:** REQ-127
- **Title:** Onboarding Path Must Be Verified
- **Description:** `specsmith doctor --onboarding` prints a checklist (CLI installed, env activated, scaffold.yml present, REQUIREMENTS.md present, vLLM endpoint reachable, ledger present) and exits non-zero if any required item is missing. `docs/site/getting-started.md` walks a fresh user from install to first accepted preflight.
- **Status:** defined
- **Source:** src/specsmith/doctor.py, src/specsmith/cli.py, docs/site/getting-started.md

## REQ-128. Cross-Repo Security Sweep
- **ID:** REQ-128
- **Title:** Cross-Repo Security Sweep
- **Description:** The specsmith and kairos repos both run `pip-audit` / `cargo audit` in CI and fail on high-or-critical findings. Dependabot manifests in both repos are reviewed and any open alert at 1.0 release time is documented. *Note: the legacy `specsmith-vscode` npm audit requirement has been retired alongside the extension deprecation.*
- **Status:** defined
- **Source:** .github/workflows/ci.yml, BitConcepts/kairos/.github/workflows/ci.yml

## REQ-129. 1.0 API Stability Commitment
- **ID:** REQ-129
- **Title:** 1.0 API Stability Commitment
- **Description:** `docs/site/api-stability.md` enumerates the public surfaces frozen at 1.0 (CLI subcommands and exit codes, JSON payload schemas for preflight / verify / chat events, broker module API, ledger event schemas, VS Code extension command IDs). The PyPI classifier is bumped to `Development Status :: 5 - Production/Stable` and `pyproject.toml` to `1.0.0`.
- **Status:** defined
- **Source:** docs/site/api-stability.md, pyproject.toml

## REQ-130. Typed ProjectOperations Layer
- **ID:** REQ-130
- **Title:** Typed ProjectOperations Layer
- **Description:** All tool handlers MUST use a typed `ProjectOperations` class for file, git/VCS, and search operations. Direct raw shell string assembly in tool handlers is prohibited.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (OPS-001)

## REQ-131. ProjectOperations File Operations via pathlib
- **ID:** REQ-131
- **Title:** ProjectOperations File Operations via pathlib
- **Description:** `ProjectOperations` MUST expose file operations (`read_file`, `write_file`, `list_dir`, `glob`, `search`) implemented via Python `pathlib`/`stdlib` — no subprocess calls.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (OPS-002)

## REQ-132. ProjectOperations Git/VCS Operations
- **ID:** REQ-132
- **Title:** ProjectOperations Git/VCS Operations
- **Description:** `ProjectOperations` MUST expose git/VCS operations (`status`, `log`, `diff`, `add`, `commit`, `push`, `create_branch`, `create_pr`) returning structured result objects.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (OPS-003)

## REQ-133. ProjectOperations Typed Result Objects
- **ID:** REQ-133
- **Title:** ProjectOperations Typed Result Objects
- **Description:** All `ProjectOperations` methods MUST return a typed result containing at minimum `exit_code`, `stdout`, `stderr`, and `elapsed_ms`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (OPS-004)

## REQ-134. executor.py run_tracked Preserved as Narrow Fallback
- **ID:** REQ-134
- **Title:** executor.py run_tracked Preserved as Narrow Fallback
- **Description:** The existing `executor.py` `run_tracked()` function MUST be preserved as a narrow fallback for commands that have no Python equivalent.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (OPS-005)

## REQ-135. ProjectOperations Cross-Platform
- **ID:** REQ-135
- **Title:** ProjectOperations Cross-Platform
- **Description:** `ProjectOperations` MUST be cross-platform (Windows, Linux, macOS) without platform-specific code branches in call sites.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (OPS-006)

## REQ-136. Harness Slash Commands Package
- **ID:** REQ-136
- **Title:** Harness Slash Commands Package
- **Description:** The `commands/` package MUST implement all priority harness slash commands available inside `specsmith run`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-001)

## REQ-137. Session Management Slash Commands
- **ID:** REQ-137
- **Title:** Session Management Slash Commands
- **Description:** Session management commands MUST include: `/model`, `/provider`, `/tier`, `/status`, `/save`, `/clear`, `/compact`, `/export`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-002)

## REQ-138. Multi-Agent Slash Commands
- **ID:** REQ-138
- **Title:** Multi-Agent Slash Commands
- **Description:** Multi-agent commands MUST include: `/spawn`, `/team`, `/team-status`, `/worktree`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-003)

## REQ-139. Continuous Learning Slash Commands
- **ID:** REQ-139
- **Title:** Continuous Learning Slash Commands
- **Description:** Continuous learning commands MUST include: `/learn`, `/learn-eval`, `/instinct-status`, `/instinct-import`, `/instinct-export`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-004)

## REQ-140. Evaluation Slash Commands
- **ID:** REQ-140
- **Title:** Evaluation Slash Commands
- **Description:** Evaluation commands MUST include: `/eval define`, `/eval run`, `/eval report`, `/eval compare`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-005)

## REQ-141. Orchestration Slash Commands
- **ID:** REQ-141
- **Title:** Orchestration Slash Commands
- **Description:** Orchestration commands MUST include: `/multi-plan`, `/multi-execute`, `/route`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-006)

## REQ-142. Hook Control Slash Commands
- **ID:** REQ-142
- **Title:** Hook Control Slash Commands
- **Description:** Hook control commands MUST include: `/hooks-enable`, `/hooks-disable`, `/hook-profile`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-007)

## REQ-143. MCP Slash Commands
- **ID:** REQ-143
- **Title:** MCP Slash Commands
- **Description:** MCP commands MUST include: `/mcp-list`, `/mcp-add`, `/mcp-configure`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-008)

## REQ-144. Security Slash Commands
- **ID:** REQ-144
- **Title:** Security Slash Commands
- **Description:** Security commands MUST include: `/security-scan`, `/audit-prompt`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (CMD-009)

## REQ-145. AgentTool for Subagent Spawning
- **ID:** REQ-145
- **Title:** AgentTool for Subagent Spawning
- **Description:** The runner MUST provide an `AgentTool` (TaskTool) as a native LLM-callable tool that spawns subagent instances.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MAS-001)

## REQ-146. Hub-and-Spoke and Agent-Teams Coordination
- **ID:** REQ-146
- **Title:** Hub-and-Spoke and Agent-Teams Coordination
- **Description:** Subagent spawning MUST support hub-and-spoke and agent-teams (peer-to-peer via filesystem mailbox) coordination modes.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MAS-002)

## REQ-147. Filesystem Mailbox for Agent Teams
- **ID:** REQ-147
- **Title:** Filesystem Mailbox for Agent Teams
- **Description:** The filesystem mailbox for agent teams MUST be stored at `.specsmith/teams/{team}/mailbox/{agent}.json`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MAS-003)

## REQ-148. Git Worktree Isolation for Subagents
- **ID:** REQ-148
- **Title:** Git Worktree Isolation for Subagents
- **Description:** When `isolation=worktree`, the spawner MUST create a git worktree at `.specsmith/worktrees/{agent_id}/`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MAS-004)

## REQ-149. No Recursive Subagent Nesting
- **ID:** REQ-149
- **Title:** No Recursive Subagent Nesting
- **Description:** Subagents MUST NOT be able to spawn further subagents (no recursive nesting).
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MAS-005)

## REQ-150. Distilled Summary from Subagents
- **ID:** REQ-150
- **Title:** Distilled Summary from Subagents
- **Description:** The parent agent MUST receive a distilled summary from each subagent on completion, not the full transcript.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MAS-006)

## REQ-151. Agent Teams Feature Flag Gated
- **ID:** REQ-151
- **Title:** Agent Teams Feature Flag Gated
- **Description:** Agent team mode MUST be gated behind a feature flag (`SPECSMITH_AGENT_TEAMS=1`).
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MAS-007)

## REQ-152. Orchestrator Meta-Agent for Routing
- **ID:** REQ-152
- **Title:** Orchestrator Meta-Agent for Routing
- **Description:** specsmith MUST provide an orchestrator meta-agent for task classification, routing, and optimization — not execution.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (ORC-001)

## REQ-153. Orchestrator Defaults to Local Ollama
- **ID:** REQ-153
- **Title:** Orchestrator Defaults to Local Ollama
- **Description:** The orchestrator MUST default to a small local Ollama model so orchestration incurs zero cloud API cost.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (ORC-002)

## REQ-154. Agent Registry with Capability Metadata
- **ID:** REQ-154
- **Title:** Agent Registry with Capability Metadata
- **Description:** The orchestrator MUST maintain an agent registry with type, model, provider, cost_tier, capabilities, avg_latency_ms, confidence.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (ORC-003)

## REQ-155. Orchestrator Emits One Structured Next-Action
- **ID:** REQ-155
- **Title:** Orchestrator Emits One Structured Next-Action
- **Description:** The orchestrator MUST emit exactly one structured next-action per task.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (ORC-004)

## REQ-156. Cost-Aware Routing
- **ID:** REQ-156
- **Title:** Cost-Aware Routing
- **Description:** The orchestrator MUST route cheap tasks to Ollama workers and complex tasks to cloud providers.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (ORC-005)

## REQ-157. Post-Session Self-Evaluation for Routing Thresholds
- **ID:** REQ-157
- **Title:** Post-Session Self-Evaluation for Routing Thresholds
- **Description:** The orchestrator MUST run a post-session self-evaluation to update routing thresholds.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (ORC-006)

## REQ-158. Feature Flag System for Tool Schema Visibility
- **ID:** REQ-158
- **Title:** Feature Flag System for Tool Schema Visibility
- **Description:** specsmith MUST implement a feature-flag system controlling which tool schemas are sent to the LLM.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (FLG-001)

## REQ-159. Feature Flags via Environment and scaffold.yml
- **ID:** REQ-159
- **Title:** Feature Flags via Environment and scaffold.yml
- **Description:** Feature flags MUST be configurable via environment variables and `scaffold.yml` under `agent.flags`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (FLG-002)

## REQ-160. Agent Teams and Advanced Features Flag-Gated
- **ID:** REQ-160
- **Title:** Agent Teams and Advanced Features Flag-Gated
- **Description:** Agent teams, worktree isolation, KAIROS daemon mode, security scanner, and MCP tools MUST be flag-gated.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (FLG-003)

## REQ-161. Instinct Persistence System
- **ID:** REQ-161
- **Title:** Instinct Persistence System
- **Description:** specsmith MUST implement an instinct persistence system in `src/specsmith/instinct.py`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (LRN-001)

## REQ-162. Instinct Record Schema
- **ID:** REQ-162
- **Title:** Instinct Record Schema
- **Description:** Each instinct record MUST contain: id, trigger_pattern, content, confidence, project_scope, created, last_used, use_count.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (LRN-002)

## REQ-163. SESSION_END Hook Extracts Candidate Instincts
- **ID:** REQ-163
- **Title:** SESSION_END Hook Extracts Candidate Instincts
- **Description:** The `SESSION_END` hook MUST extract candidate instincts for user review.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (LRN-003)

## REQ-164. /learn Command Promotes Pattern to Instinct
- **ID:** REQ-164
- **Title:** /learn Command Promotes Pattern to Instinct
- **Description:** The `/learn` command MUST promote a pattern to an instinct with an initial confidence score.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (LRN-004)

## REQ-165. Instinct Confidence Updated on Application
- **ID:** REQ-165
- **Title:** Instinct Confidence Updated on Application
- **Description:** Instinct confidence MUST be updated based on application success/rejection.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (LRN-005)

## REQ-166. Instincts Importable and Exportable as Markdown
- **ID:** REQ-166
- **Title:** Instincts Importable and Exportable as Markdown
- **Description:** Instincts MUST be importable and exportable as `.md` files.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (LRN-006)

## REQ-167. /instinct-status Displays Active Instincts
- **ID:** REQ-167
- **Title:** /instinct-status Displays Active Instincts
- **Description:** `/instinct-status` MUST display all active instincts sorted by confidence.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (LRN-007)

## REQ-168. Eval Harness Module
- **ID:** REQ-168
- **Title:** Eval Harness Module
- **Description:** specsmith MUST implement an eval harness in `src/specsmith/eval/`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-001)

## REQ-169. Eval Data Model
- **ID:** REQ-169
- **Title:** Eval Data Model
- **Description:** The eval model MUST define: Task, Trial, Grader, Transcript, Outcome.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-002)

## REQ-170. Eval Tasks Stored as Markdown
- **ID:** REQ-170
- **Title:** Eval Tasks Stored as Markdown
- **Description:** Tasks MUST be stored as Markdown at `.specsmith/evals/{feature}.md` with YAML frontmatter.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-003)

## REQ-171. Three Grader Types
- **ID:** REQ-171
- **Title:** Three Grader Types
- **Description:** The harness MUST support CodeGrader, ModelGrader, and HumanFlag grader types.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-004)

## REQ-172. pass@k and pass^k Metrics
- **ID:** REQ-172
- **Title:** pass@k and pass^k Metrics
- **Description:** The harness MUST compute `pass@k` and `pass^k` metrics.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-005)

## REQ-173. Git-Based Outcome Grading by Default
- **ID:** REQ-173
- **Title:** Git-Based Outcome Grading by Default
- **Description:** Default grading MUST be git-based outcome grading, not execution-path assertion.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-006)

## REQ-174. /eval run --trials k
- **ID:** REQ-174
- **Title:** /eval run --trials k
- **Description:** `/eval run --trials k` MUST run k independent trials and report results.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-007)

## REQ-175. Capability vs Regression Eval Distinction
- **ID:** REQ-175
- **Title:** Capability vs Regression Eval Distinction
- **Description:** The harness MUST distinguish capability evals from regression evals.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (EDD-008)

## REQ-176. Cross-Session Agent Memory
- **ID:** REQ-176
- **Title:** Cross-Session Agent Memory
- **Description:** specsmith MUST implement cross-session agent memory in `src/specsmith/memory.py`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MEM-001)

## REQ-177. Agent Memory Structured JSON
- **ID:** REQ-177
- **Title:** Agent Memory Structured JSON
- **Description:** Agent memory MUST be structured JSON with accumulated patterns, preferred approaches, known project facts, and failure history.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MEM-002)

## REQ-178. SESSION_START Hook Injects Memories into System Prompt
- **ID:** REQ-178
- **Title:** SESSION_START Hook Injects Memories into System Prompt
- **Description:** The `SESSION_START` hook MUST inject relevant memories into the system prompt (token-budget-aware).
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MEM-003)

## REQ-179. Agent Memory Compatible with Theia AI Convention
- **ID:** REQ-179
- **Title:** Agent Memory Compatible with Theia AI Convention
- **Description:** Agent memory layout MUST be compatible with Theia AI's `~/.theia/agent-memory/` convention.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MEM-004)

## REQ-180. Runtime Hook Enable/Disable
- **ID:** REQ-180
- **Title:** Runtime Hook Enable/Disable
- **Description:** Hooks MUST be enable/disable-able at runtime without restarting the session.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (HRK-001)

## REQ-181. Hook Profiles via /hook-profile
- **ID:** REQ-181
- **Title:** Hook Profiles via /hook-profile
- **Description:** Hook profiles MUST be loadable via `/hook-profile`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (HRK-002)

## REQ-182. New Hook Trigger Events
- **ID:** REQ-182
- **Title:** New Hook Trigger Events
- **Description:** New triggers: `SUBAGENT_START`, `SUBAGENT_STOP`, `CONTEXT_COMPACT`, `EVAL_PASS`, `EVAL_FAIL`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (HRK-003)

## REQ-183. SUBAGENT_START Hook Can Block Spawn
- **ID:** REQ-183
- **Title:** SUBAGENT_START Hook Can Block Spawn
- **Description:** `SUBAGENT_START` MUST fire before spawning; a hook MAY block the spawn.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (HRK-004)

## REQ-184. SUBAGENT_STOP Hook on Completion
- **ID:** REQ-184
- **Title:** SUBAGENT_STOP Hook on Completion
- **Description:** `SUBAGENT_STOP` MUST fire when a subagent completes.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (HRK-005)

## REQ-185. CONTEXT_COMPACT Hook Before Trimming
- **ID:** REQ-185
- **Title:** CONTEXT_COMPACT Hook Before Trimming
- **Description:** `CONTEXT_COMPACT` MUST fire before context trimming.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (HRK-006)

## REQ-186. specsmith serve Command
- **ID:** REQ-186
- **Title:** specsmith serve Command
- **Description:** specsmith MUST provide a `specsmith serve` command (already shipped in v0.7.0).
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SRV-001)

## REQ-187. REST Endpoints for Session and Agent Management
- **ID:** REQ-187
- **Title:** REST Endpoints for Session and Agent Management
- **Description:** REST endpoints: `GET/POST /sessions`, `GET /agents`, `GET /instincts`, `GET /evals`, `POST /index`, `GET /health`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SRV-002)

## REQ-188. WebSocket Endpoint for Live Session I/O
- **ID:** REQ-188
- **Title:** WebSocket Endpoint for Live Session I/O
- **Description:** WebSocket endpoint at `/ws/session/{id}` for live session I/O using the existing JSONL event schema.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SRV-003)

## REQ-189. EventSink Protocol for Stdout and WebSocket
- **ID:** REQ-189
- **Title:** EventSink Protocol for Stdout and WebSocket
- **Description:** `AgentRunner._emit_event()` MUST use an `EventSink` protocol (`StdoutSink` / `WebSocketSink`).
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SRV-004)

## REQ-190. Kairos Terminal Connects via HTTP/WebSocket
- **ID:** REQ-190
- **Title:** Kairos Terminal Connects via HTTP/WebSocket
- **Description:** The Kairos terminal MUST connect to `specsmith serve` over HTTP/WebSocket for all governance operations.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SRV-005)

## REQ-191. BM25 Retrieval Ranking
- **ID:** REQ-191
- **Title:** BM25 Retrieval Ranking
- **Description:** `retrieval.py` MUST be upgraded from term-frequency to BM25 ranking using `rank_bm25`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (RTR-001)

## REQ-192. File-Watcher Based Index Refresh
- **ID:** REQ-192
- **Title:** File-Watcher Based Index Refresh
- **Description:** The retrieval index MUST support file-watcher-based refresh.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (RTR-002)

## REQ-193. Token-Counted Retrieval Results
- **ID:** REQ-193
- **Title:** Token-Counted Retrieval Results
- **Description:** Retrieval results MUST be token-counted before injection to prevent context budget overruns.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (RTR-003)

## REQ-194. MCP Server Configuration Templates
- **ID:** REQ-194
- **Title:** MCP Server Configuration Templates
- **Description:** specsmith MUST provide MCP server configuration templates via `/mcp-add` or `specsmith mcp add`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MCP-001)

## REQ-195. MCP Server Registry with Status
- **ID:** REQ-195
- **Title:** MCP Server Registry with Status
- **Description:** The MCP server registry MUST list configured servers with status and tool surfaces.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MCP-002)

## REQ-196. MCP Configuration in scaffold.yml
- **ID:** REQ-196
- **Title:** MCP Configuration in scaffold.yml
- **Description:** MCP configuration MUST be storable in `scaffold.yml` under `agent.mcp_servers`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (MCP-003)

## REQ-197. /security-scan Command
- **ID:** REQ-197
- **Title:** /security-scan Command
- **Description:** specsmith MUST provide a `/security-scan` command running a dedicated security analysis agent.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SEC-001)

## REQ-198. Security Scan Coverage
- **ID:** REQ-198
- **Title:** Security Scan Coverage
- **Description:** The security scan MUST check dependency vulnerabilities, OWASP-style code patterns, and exposed secrets.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SEC-002)

## REQ-199. /audit-prompt for Injection Analysis
- **ID:** REQ-199
- **Title:** /audit-prompt for Injection Analysis
- **Description:** `/audit-prompt` MUST analyze a prompt string for injection vectors.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SEC-003)

## REQ-200. Security Scan Results Stored Structurally
- **ID:** REQ-200
- **Title:** Security Scan Results Stored Structurally
- **Description:** Security scan results MUST be structured and stored at `.specsmith/security-reports/`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (SEC-004)

## REQ-201. specsmith-ide Theia Application
- **ID:** REQ-201
- **Title:** specsmith-ide Theia Application
- **Description:** A `specsmith-ide` application MUST be created on Eclipse Theia with `@theia/ai-core`, `@theia/ai-chat`, `@theia/ai-ide`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (IDE-001)

## REQ-202. specsmith-ide Extension Packages
- **ID:** REQ-202
- **Title:** specsmith-ide Extension Packages
- **Description:** specsmith-ide MUST ship: `@specsmith/ai-agents`, `@specsmith/epistemic-ui`, `@specsmith/eval-ui`, `@specsmith/service-client`.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (IDE-002)

## REQ-203. specsmith-ide WebSocket Connection to specsmith serve
- **ID:** REQ-203
- **Title:** specsmith-ide WebSocket Connection to specsmith serve
- **Description:** specsmith-ide MUST connect to `specsmith serve` over WebSocket.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (IDE-003)

## REQ-204. specsmith-ide Leverages Theia AI Native Tooling
- **ID:** REQ-204
- **Title:** specsmith-ide Leverages Theia AI Native Tooling
- **Description:** specsmith-ide MUST leverage Theia AI's existing MCP support, ShellExecutionTool, and agent skills system.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (IDE-004)

## REQ-205. specsmith-ide Electron Desktop Packaging
- **ID:** REQ-205
- **Title:** specsmith-ide Electron Desktop Packaging
- **Description:** specsmith-ide MUST be packageable as an Electron desktop application.
- **Status:** defined
- **Source:** docs/PLANNED-REQUIREMENTS.md (IDE-005)

## REQ-206. Tamper-Evident Agent Action Log
- **ID:** REQ-206
- **Title:** Tamper-Evident Agent Action Log
- **Description:** specsmith MUST maintain a tamper-evident, append-only agent action log capturing every governance decision, tool invocation, input, and output. The log chain MUST use SHA-256 chaining so any modification is detectable. Satisfies EU AI Act Art. 12 (logging obligations) and NIST AI RMF (GO-6).
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-001]

## REQ-207. Explanation Artifacts for Governance Decisions
- **ID:** REQ-207
- **Title:** Explanation Artifacts for Governance Decisions
- **Description:** Every governance decision (preflight, verify, classify) MUST produce an 'explanation artifact' recording: what data was used, which requirements were matched, why the decision was reached, and the confidence score. Satisfies EU AI Act Art. 13 (transparency), CFPB adverse-action requirements.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-002]

## REQ-208. Action Log Replay and Export
- **ID:** REQ-208
- **Title:** Action Log Replay and Export
- **Description:** specsmith MUST support structured replay and export of agent action logs for external audit, regulatory submission, or incident investigation. Export format MUST be machine-readable (JSONL) and human-readable (Markdown). Satisfies OMB M-24-10 (AI use case inventories) and EU AI Act post-market monitoring.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-003]

## REQ-209. Human Escalation Threshold
- **ID:** REQ-209
- **Title:** Human Escalation Threshold
- **Description:** specsmith MUST provide a configurable human-escalation threshold. When preflight confidence is below the threshold, or when a destructive/release intent is detected, execution MUST pause and route to human review. Satisfies NIST AI RMF (GO-4), OMB M-24-10 human-in-the-loop requirements.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-004]

## REQ-210. Emergency Kill-Switch and Circuit-Breaker
- **ID:** REQ-210
- **Title:** Emergency Kill-Switch and Circuit-Breaker
- **Description:** specsmith MUST implement an emergency kill-switch that immediately halts agent activity when: (a) the user invokes a stop command, (b) an anomaly detector triggers, or (c) the retry budget is exhausted. The kill-switch MUST be reachable from both the CLI and the REST API. Satisfies EU AI Act Art. 14 (human oversight), NIST AI RMF.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-005]

## REQ-211. Post-Market Behavioral Monitoring and Alerting
- **ID:** REQ-211
- **Title:** Post-Market Behavioral Monitoring and Alerting
- **Description:** specsmith MUST monitor agent behavior across sessions and alert when anomalous patterns are detected: unexpected confidence regression, unusual tool usage rates, or systematic requirement mismatches. Satisfies EU AI Act Art. 72 (post-market monitoring) and OMB M-24-10.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-006]

## REQ-212. One-Click Rollback for File-Modifying Actions
- **ID:** REQ-212
- **Title:** One-Click Rollback for File-Modifying Actions
- **Description:** Every agent action that modifies governance files MUST create a timestamped backup before overwriting, and MUST expose a rollback command that restores the pre-action state. Satisfies NIST AI GenAI Profile (rollback and compensation), CFPB.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-007]

## REQ-213. Safe Append-Only Write for New Governance Entries
- **ID:** REQ-213
- **Title:** Safe Append-Only Write for New Governance Entries
- **Description:** All new entries appended to governance files (LEDGER.md, REQUIREMENTS.md, TESTS.md) MUST use append-only mode — never truncating or overwriting existing content. Protects against data loss from agent errors. Satisfies EU AI Act technical controls and data integrity requirements.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-008]

## REQ-214. AI Disclosure Metadata in Agent Outputs
- **ID:** REQ-214
- **Title:** AI Disclosure Metadata in Agent Outputs
- **Description:** Outputs generated by specsmith agents MUST include AI disclosure metadata when surfaced to end-users: which model was used, provider, confidence level, and whether the output was governance-gated. Satisfies FTC Operation AI Comply, Utah SB149 (2024) disclosure requirements.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-009]

## REQ-215. Regulatory Compliance Export Report
- **ID:** REQ-215
- **Title:** Regulatory Compliance Export Report
- **Description:** specsmith MUST generate a structured compliance export report covering: AI system inventory, risk classification, human oversight controls, audit log summary, and incident history. Satisfies OMB M-24-10, Colorado SB24-205 impact assessments, EU AI Act technical docs.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-010]

## REQ-216. Agent Risk Classification Before Deployment
- **ID:** REQ-216
- **Title:** Agent Risk Classification Before Deployment
- **Description:** Before activating a governance profile or agent session, specsmith MUST classify the intended use case against EU AI Act risk tiers (prohibited, high-risk Annex III, GPAI systemic-risk, or minimal-risk). High-risk use cases MUST require additional confirmation. Satisfies EU AI Act Art. 6 risk-based approach.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-011]

## REQ-217. Least-Privilege Agent Permissions
- **ID:** REQ-217
- **Title:** Least-Privilege Agent Permissions
- **Description:** Every agent session MUST operate with the minimum permissions required. Agent capabilities MUST be explicitly declared, and sensitive operations (commit, push, create PR, external calls) MUST be individually gated. Satisfies EU AI Act agent registration, NIST AI RMF least-privilege principle.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-012]

## REQ-218. Self-Optimization Bounded by Iteration Budget
- **ID:** REQ-218
- **Title:** Self-Optimization Bounded by Iteration Budget
- **Description:** All self-improvement loops (agent improve, eval harness, continuous learning) MUST be bounded by a configurable iteration budget. Unbounded recursion or runaway optimisation MUST be prevented. Satisfies EU AI Act systemic risk controls (GPAISR) and credit spend governance.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-013]

## REQ-219. Local-First Model Routing for Governance Tasks
- **ID:** REQ-219
- **Title:** Local-First Model Routing for Governance Tasks
- **Description:** Governance classification tasks (preflight, verify, classify_intent) MUST default to a local Ollama model (zero cloud cost) and only escalate to cloud APIs when local confidence is below threshold. Reduces credit spend and avoids unnecessary data transfer to third parties.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-014]

## REQ-220. Policy Guardrails at the Interface Layer
- **ID:** REQ-220
- **Title:** Policy Guardrails at the Interface Layer
- **Description:** specsmith MUST enforce allow/deny lists for tool categories and data access patterns at the agent interface layer — not just within prompts. Agents MUST NOT access live production databases or unmanaged data sources. Satisfies EU AI Act technical controls, California ADMT data governance requirements.
- **Status:** defined
- **Source:** BTWS-2027 AI Governance Report [REG-015]

## REQ-244. GPU-Aware Context Window Sizing
- **ID:** REQ-244
- **Title:** GPU-Aware Context Window Sizing
- **Description:** Before starting an Ollama agent session, specsmith MUST detect available GPU VRAM (NVIDIA via nvidia-smi, AMD via rocm-smi) and recommend a num_ctx value. VRAM tiers: <6 GB → 4096, 6-12 GB → 8192, 12-20 GB → 16384, >=20 GB → 32768. CPU-only defaults to 4096. The function MUST never raise on any platform.
- **Status:** defined
- **Source:** Plan 0ca40db4 [CTX-001]

## REQ-245. Live Context Fill Indicator
- **ID:** REQ-245
- **Title:** Live Context Fill Indicator
- **Description:** Every active agent conversation MUST track and emit context fill events with schema: {type: context_fill, used: int, limit: int, pct: float}. The fill percentage MUST be surfaced in the terminal UI as a compact progress bar (green 0-60%, yellow 60-80%, orange 80-90%, red >90%).
- **Status:** defined
- **Source:** Plan 0ca40db4 [CTX-002]

## REQ-246. Auto Context Compression at Configurable Threshold
- **ID:** REQ-246
- **Title:** Auto Context Compression at Configurable Threshold
- **Description:** When context fill reaches the configurable compression threshold (default 80%, range 50-95%), specsmith MUST automatically trigger context summarization. Compression MUST emit a context_compressed event with before/after token counts. Auto-compression MUST be togglable; when off, only a warning is surfaced.
- **Status:** defined
- **Source:** Plan 0ca40db4 [CTX-003]

## REQ-247. Hard Context Reservation — Never 100% Fill
- **ID:** REQ-247
- **Title:** Hard Context Reservation — Never 100% Fill
- **Description:** The context window MUST NEVER be allowed to reach 100% fill. A hard reservation of 15% (or MIN_FREE_TOKENS=2048, whichever is more restrictive) MUST remain free. When fill reaches the hard ceiling (default 85%), ContextFullError MUST be raised and emergency compression triggered regardless of the auto-compress toggle.
- **Status:** defined
- **Source:** Plan 0ca40db4 [CTX-004]

## REQ-248. Dev/Stable Update Channel Persistence
- **ID:** REQ-248
- **Title:** Dev/Stable Update Channel Persistence
- **Description:** specsmith MUST persist a user-chosen update channel (stable or dev) to ~/.specsmith/channel. specsmith channel set {stable|dev} writes the file; channel clear removes it. effective_channel_with_source() MUST return (channel, source) where source is user when the file exists, otherwise
- **Status:** implemented
- **Source:** ARCHITECTURE.md [Update Channel Selection]

## REQ-249. ESDB JSON Export Command
- **ID:** REQ-249
- **Title:** ESDB JSON Export Command
- **Description:** specsmith esdb export [--output PATH] [--json] MUST dump all ESDB records (requirements and testcases) to a versioned JSON payload at the specified path, or default to <project>/.specsmith/esdb_export.json. Output includes esdb_version, ackend,
- **Status:** implemented
- **Source:** ARCHITECTURE.md [ESDB Extended Management]

## REQ-250. ESDB JSON Import Command
- **ID:** REQ-250
- **Title:** ESDB JSON Import Command
- **Description:** specsmith esdb import <source> [--json] MUST validate a JSON export file (checking for
- **Status:** implemented
- **Source:** ARCHITECTURE.md [ESDB Extended Management]

## REQ-251. ESDB Timestamped Backup Command
- **ID:** REQ-251
- **Title:** ESDB Timestamped Backup Command
- **Description:** specsmith esdb backup [--dir DIR] [--json] MUST create a timestamped snapshot at <dir>/esdb_backup_<YYYYMMDDTHHMMSSZ>.json (default dir: .specsmith/backups/). The snapshot payload MUST include esdb_version, 	imestamp, ackend,
- **Status:** implemented
- **Source:** ARCHITECTURE.md [ESDB Extended Management]

## REQ-252. ESDB WAL Rollback Command
- **ID:** REQ-252
- **Title:** ESDB WAL Rollback Command
- **Description:** specsmith esdb rollback [--steps N] [--json] MUST report the number of WAL events that would be undone. In stub mode (ChronoMemory native engine not linked) it MUST return {ok: true, steps_requested: N, records_before: N, note: "..."} without modifying state.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [ESDB Extended Management]

## REQ-253. ESDB WAL Compact Command
- **ID:** REQ-253
- **Title:** ESDB WAL Compact Command
- **Description:** specsmith esdb compact [--json] MUST request WAL compaction. In stub mode it MUST return {ok: true, backend: "...", records: N, note: "..."} without error.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [ESDB Extended Management]

## REQ-254. Skills Deactivate Command
- **ID:** REQ-254
- **Title:** Skills Deactivate Command
- **Description:** specsmith skills deactivate <skill-id> [--project-dir DIR] MUST set ctive: false in the skill's skill.json, return True on success, and exit non-zero with an error message if the skill is not found.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [AI Skills Builder]

## REQ-255. Skills Delete Command
- **ID:** REQ-255
- **Title:** Skills Delete Command
- **Description:** specsmith skills delete <skill-id> [--project-dir DIR] [--yes] MUST prompt for confirmation unless --yes is provided, then permanently remove the skill directory under .specsmith/skills/. Returns non-zero if the skill is not found.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [AI Skills Builder]

## REQ-256. MCP Server Config Generation Command
- **ID:** REQ-256
- **Title:** MCP Server Config Generation Command
- **Description:** specsmith mcp generate <description> [--json] MUST produce a deterministic MCP server configuration stub with id,
- **Status:** implemented
- **Source:** ARCHITECTURE.md [MCP Server Generator]

## REQ-257. Agent Ask Keyword Dispatcher
- **ID:** REQ-257
- **Title:** Agent Ask Keyword Dispatcher
- **Description:** specsmith agent ask <prompt> [--project-dir DIR] [--json-output] MUST route prompts to the appropriate subsystem by keyword matching (compliance, audit, skill, esdb, mcp, session) without requiring an LLM. It MUST return {reply, action, prompt} and print human-readable output unless --json-output is set.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [Agent Ask Dispatcher]

## REQ-258. Kairos ESDB Settings Page
- **ID:** REQ-258
- **Title:** Kairos ESDB Settings Page
- **Description:** The Kairos settings sidebar MUST include an ESDB page under the Specsmith umbrella group. The page MUST display current ESDB status (record count, backend, chain validity) and provide action buttons for Refresh, Export JSON, Import, Backup, Rollback, and Compact.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [Kairos Settings Extensions]

## REQ-259. Kairos Skills Settings Page
- **ID:** REQ-259
- **Title:** Kairos Skills Settings Page
- **Description:** The Kairos settings sidebar MUST include a Skills page under the Specsmith umbrella group. The page MUST display a description of the Skills system and instructions for using specsmith skills build and related commands.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [Kairos Settings Extensions]

## REQ-260. Kairos Eval Settings Page
- **ID:** REQ-260
- **Title:** Kairos Eval Settings Page
- **Description:** The Kairos settings sidebar MUST include an Eval page under the Specsmith umbrella group. The page MUST describe the evaluation tracking system and direct users to specsmith eval run for generating reports.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [Kairos Settings Extensions]

## REQ-261. Kairos AI Providers Table Without Column Overflow
- **ID:** REQ-261
- **Title:** Kairos AI Providers Table Without Column Overflow
- **Description:** The Kairos Agents > Providers settings page MUST display AI models in a table with fixed-width columns (Name: 200px, Model ID: 220px, Context: 80px, Output: 80px) using ConstrainedBox + Clipped elements. Long model names such as o4-mini-deep-research MUST NOT overflow into adjacent columns.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [Kairos Settings Extensions]

## REQ-262. Kairos MCP AI Builder Card
- **ID:** REQ-262
- **Title:** Kairos MCP AI Builder Card
- **Description:** The Kairos Agents > MCP servers list page MUST include a collapsible AI Builder card that accepts a natural-language server description, calls specsmith mcp generate <description> --json, displays the generated JSON stub, and offers an 'Add to ~/.specsmith/mcp.json' button that appends the stub to the user's MCP config file.
- **Status:** implemented
- **Source:** ARCHITECTURE.md [Kairos Settings Extensions]

## REQ-263. HuggingFace Open LLM Leaderboard Sync
- **ID:** REQ-263
- **Title:** HuggingFace Open LLM Leaderboard Sync
- **Description:** specsmith MUST implement `src/specsmith/agent/hf_leaderboard.py` that fetches model benchmark data from the HuggingFace Datasets Server (`datasets-server.huggingface.co/rows?dataset=open-llm-leaderboard/contents`). The sync MUST be paginated (100 rows/page) and persist results to `~/.specsmith/model_scores.json` under a `bucket_scores` key.
- **Status:** defined
- **Source:** ARCHITECTURE.md §21 [HF-001]

## REQ-264. HF Leaderboard Rate-Limit Handling
- **ID:** REQ-264
- **Title:** HF Leaderboard Rate-Limit Handling
- **Description:** The HF leaderboard sync MUST handle HTTP 429 with exponential-backoff retry (up to 4 attempts). It MUST parse the `RateLimit: "api";r=X;t=Y` header to extract the exact reset window and wait accordingly. A +1 s safety margin MUST be added to the `t=` value.
- **Status:** defined
- **Source:** ARCHITECTURE.md §21 [HF-002]

## REQ-265. HF API Token Support
- **ID:** REQ-265
- **Title:** HF API Token Support
- **Description:** When `SPECSMITH_HF_TOKEN` or `hf_api_token` is configured, the HF sync MUST include an `Authorization: Bearer <token>` header. The CLI `specsmith model-intel test-hf` MUST validate the token via `huggingface.co/api/whoami-v2` and report whether the Datasets Server is reachable.
- **Status:** defined
- **Source:** ARCHITECTURE.md §21 [HF-003]

## REQ-266. HF Leaderboard Static Fallback
- **ID:** REQ-266
- **Title:** HF Leaderboard Static Fallback
- **Description:** When HF is unreachable (network error, 5xx, or zero parseable rows), specsmith MUST load built-in static benchmark scores covering at least 40 models (OpenAI GPT-4o/mini, Claude 3.5 sonnet/haiku, Gemini 2.x, Mistral, Qwen, Llama, DeepSeek, Phi). The fallback MUST be transparent to callers.
- **Status:** defined
- **Source:** ARCHITECTURE.md §21 [HF-004]

## REQ-267. Bucket Scoring Engine
- **ID:** REQ-267
- **Title:** Bucket Scoring Engine
- **Description:** specsmith MUST compute three task-bucket scores from raw benchmark values (0–100 scale): Reasoning = 0.35×MATH + 0.30×GPQA + 0.25×BBH + 0.10×IFEval; Conversational = 0.40×IFEval + 0.35×MMLU-PRO + 0.25×BBH; Longform = 0.35×MUSR + 0.35×IFEval + 0.30×MMLU-PRO. Scores MUST be rounded to 2 decimal places.
- **Status:** defined
- **Source:** ARCHITECTURE.md §22 [BKT-001]

## REQ-268. Model Intelligence Recommendations
- **ID:** REQ-268
- **Title:** Model Intelligence Recommendations
- **Description:** `specsmith model-intel recommendations [--bucket reasoning|conversational|longform]` MUST return the top-10 models sorted by the requested bucket score. The governance HTTP server MUST expose `GET /api/model-intel/recommendations?bucket=<name>` returning the same data.
- **Status:** defined
- **Source:** ARCHITECTURE.md §22 [BKT-002]

## REQ-269. Model Intelligence CLI Commands
- **ID:** REQ-269
- **Title:** Model Intelligence CLI Commands
- **Description:** specsmith MUST provide a `model-intel` CLI group with subcommands: `sync` (run HF sync), `scores [--model NAME]` (list/get cached scores), `recommendations [--bucket NAME]` (top-10 per bucket), `test-hf` (connectivity probe). All commands MUST support `--json` flag.
- **Status:** defined
- **Source:** ARCHITECTURE.md §21 [HF-005]

## REQ-270. Model Capability Profiles
- **ID:** REQ-270
- **Title:** Model Capability Profiles
- **Description:** specsmith MUST implement `src/specsmith/agent/model_profiles.py` with a `ModelProfile` TypedDict containing `max_tokens`, `temperature`, `ctx_budget`, `action_capable`, `prompt_style` fields. A `get_profile(model)` function MUST resolve by prefix matching (longest key first) over ≥40 known models.
- **Status:** defined
- **Source:** ARCHITECTURE.md §23 [PRF-001]

## REQ-271. Context History Trimmer
- **ID:** REQ-271
- **Title:** Context History Trimmer
- **Description:** `trim_history(messages, budget_chars)` in `model_profiles.py` MUST trim conversation history to fit within `budget_chars`. Oldest turns MUST be summarised into a compact `[Earlier conversation summary — N turns condensed]` assistant message rather than silently dropped. System messages MUST always be preserved.
- **Status:** defined
- **Source:** ARCHITECTURE.md §23 [PRF-002]

## REQ-272. AI Model Pacer EMA Utilisation
- **ID:** REQ-272
- **Title:** AI Model Pacer EMA Utilisation
- **Description:** The `ModelRateLimitScheduler` MUST track RPM and TPM utilisation as exponentially-weighted moving averages (alpha=0.25) and expose them in `snapshot()` as `rpm_ema` and `tpm_ema` fields.
- **Status:** defined
- **Source:** ARCHITECTURE.md §24 [PCR-001]

## REQ-273. AI Model Pacer Adaptive Concurrency
- **ID:** REQ-273
- **Title:** AI Model Pacer Adaptive Concurrency
- **Description:** `on_rate_limit(model, error, attempt)` MUST decrease `dynamic_concurrency` by 1 (minimum=1) and set `reduced_until` to now+120 s. Concurrency MUST restore incrementally (1 step per 60 s) once `reduced_until` has passed. The method MUST return a float delay for the caller to sleep.
- **Status:** defined
- **Source:** ARCHITECTURE.md §24 [PCR-002]

## REQ-274. AI Model Pacer Image Token Estimation
- **ID:** REQ-274
- **Title:** AI Model Pacer Image Token Estimation
- **Description:** `estimate_request_tokens()` MUST accept an `image_count` parameter and include `image_count × image_token_estimate` tokens in the reservation. The default `image_token_estimate` MUST be 4096.
- **Status:** defined
- **Source:** ARCHITECTURE.md §24 [PCR-003]

## REQ-275. Multi-Provider LLM Client with Fallback
- **ID:** REQ-275
- **Title:** Multi-Provider LLM Client with Fallback
- **Description:** specsmith MUST implement `src/specsmith/agent/llm_client.py` with a `LLMProvider` ABC and `LLMClient` that tries providers in order, falling back on HTTP 401/403/429/5xx. Concrete providers MUST cover Mistral, OpenAI, Google Gemini, and Ollama. A `MockProvider` MUST be available for tests.
- **Status:** defined
- **Source:** ARCHITECTURE.md §25 [LLM-001]

## REQ-276. LLM Client O-Series Translation
- **ID:** REQ-276
- **Title:** LLM Client O-Series Translation
- **Description:** When the model name starts with `o1`, `o3`, or `o4`, or contains `-o1-`/`-o3-`/`-o4-`, the LLM client MUST use `max_completion_tokens` instead of `max_tokens`, force temperature to 1, and rename `system` role messages to `developer`.
- **Status:** defined
- **Source:** ARCHITECTURE.md §25 [LLM-002]

## REQ-277. LLM Client vLLM Guided-JSON Mode
- **ID:** REQ-277
- **Title:** LLM Client vLLM Guided-JSON Mode
- **Description:** When a JSON schema is provided and the provider type is `byoe` or `huggingface`, the request MUST include `guided_json` and `chat_template_kwargs: {"enable_thinking": false}` to suppress chain-of-thought tokens and enforce structured output.
- **Status:** defined
- **Source:** ARCHITECTURE.md §25 [LLM-003]

## REQ-278. Endpoint Preset Registry
- **ID:** REQ-278
- **Title:** Endpoint Preset Registry
- **Description:** `src/specsmith/agent/provider_registry.py` MUST export `ENDPOINT_PRESETS` — a list of built-in connection presets for at least: vLLM (localhost:8000), LM Studio (localhost:1234), llama.cpp (localhost:8080), OpenRouter, Together AI, Groq, Fireworks, DeepInfra, Perplexity, and Azure OpenAI. Each preset MUST include `id`, `label`, `base_url`, `endpoint_kind`, and `needs_key`.
- **Status:** defined
- **Source:** ARCHITECTURE.md §26 [PRE-001]

## REQ-279. Endpoint Probe Enriched Metadata
- **ID:** REQ-279
- **Title:** Endpoint Probe Enriched Metadata
- **Description:** `probe_openai_compatible()` MUST return a `models_detail` list where each entry includes `id`, `owner`, `context_length` (from `max_model_len` on vLLM, `context_length` or `context_window` otherwise), and `description`. The cap MUST be 200 models.
- **Status:** defined
- **Source:** ARCHITECTURE.md §26 [PRE-002]

## REQ-280. Suggested Profile Generation
- **ID:** REQ-280
- **Title:** Suggested Profile Generation
- **Description:** `specsmith agent suggest-profiles` MUST inspect available backends (cloud env vars, installed Ollama models, saved BYOE endpoints) and propose ready-to-add `ProviderEntry` suggestions with role-tuned temperature and max_tokens for the reasoning/conversational/longform AEE buckets. Suggestions MUST be inert (not auto-saved).
- **Status:** defined
- **Source:** ARCHITECTURE.md §27 [SGP-001]

## REQ-281. Kairos AI Settings Bucket Score Display
- **ID:** REQ-281
- **Title:** Kairos AI Settings Bucket Score Display
- **Description:** The Kairos Agents > Providers settings page MUST display bucket scores (reasoning, conversational, longform) retrieved from `GET /api/model-intel/scores/{model}` for each configured provider. Scores MUST be shown as compact numeric badges. A Sync button MUST call `POST /api/model-intel/sync`.
- **Status:** defined
- **Source:** ARCHITECTURE.md §20–21 [KAI-001]

