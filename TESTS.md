# Test Specification

## TEST-001. Specsmith Must Govern Itself
- **ID:** TEST-001
- **Title:** Specsmith Must Govern Itself
- **Description:** Specsmith must govern its own governance layer and use it for all changes.
- **Requirement ID:** REQ-001
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-002. Governance Files Must Be Owned by Specsmith
- **ID:** TEST-002
- **Title:** Governance Files Must Be Owned by Specsmith
- **Description:** Only Specsmith may create, update, or delete the human‑readable governance files `ARCHITECTURE.md`, `REQUIREMENTS.md`, `TESTS.md`, and `LEDGER.md`.
- **Requirement ID:** REQ-002
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-003. Machine State Must Reflect Governance State
- **ID:** TEST-003
- **Title:** Machine State Must Reflect Governance State
- **Description:** Every machine‑readable state file under `.specsmith/` must be derived from its corresponding human‑readable governance file and remain in sync.
- **Requirement ID:** REQ-003
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-004. Requirements Must Be Derived from Architecture
- **ID:** TEST-004
- **Title:** Requirements Must Be Derived from Architecture
- **Description:** Specsmith must parse `ARCHITECTURE.md` to produce initial requirements.
- **Requirement ID:** REQ-004
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-005. Requirement IDs Must Be Stable
- **ID:** TEST-005
- **Title:** Requirement IDs Must Be Stable
- **Description:** Once assigned, a requirement ID must never change or be reused.
- **Requirement ID:** REQ-005
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-006. Preflight Validation Must Be Performed
- **ID:** TEST-006
- **Title:** Preflight Validation Must Be Performed
- **Description:** Before any governance action, the system must validate inputs and produce structured output with required fields.
- **Requirement ID:** REQ-006
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-007. Test Cases Must Be Generated from Requirements
- **ID:** TEST-007
- **Title:** Test Cases Must Be Generated from Requirements
- **Description:** For each requirement, Specsmith must create or link a test case that can prove the requirement.
- **Requirement ID:** REQ-007
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-008. Each Requirement Must Link to At Least One Test
- **ID:** TEST-008
- **Title:** Each Requirement Must Link to At Least One Test
- **Description:** Each requirement must be traceable to at least one test case.
- **Requirement ID:** REQ-008
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-009. Work Items Must Be Created for Accepted Requirements
- **ID:** TEST-009
- **Title:** Work Items Must Be Created for Accepted Requirements
- **Description:** When a requirement is accepted, a unique work item must be created.
- **Requirement ID:** REQ-009
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-010. Requirements Must Include Priority and Status
- **ID:** TEST-010
- **Title:** Requirements Must Include Priority and Status
- **Description:** Each requirement record must contain `priority` and `status` attributes.
- **Requirement ID:** REQ-010
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-011. Verification Must Include Confidence Scoring
- **ID:** TEST-011
- **Title:** Verification Must Include Confidence Scoring
- **Description:** Every verification run must produce a numeric confidence score along with pass/fail.
- **Requirement ID:** REQ-011
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-012. Equilibrium Must Be Reached Before Finalizing
- **ID:** TEST-012
- **Title:** Equilibrium Must Be Reached Before Finalizing
- **Description:** A work item may be marked finished only when its verification confidence meets or exceeds the configured threshold and no contradictions remain.
- **Requirement ID:** REQ-012
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-013. Retry Recommendations Must Be Provided
- **ID:** TEST-013
- **Title:** Retry Recommendations Must Be Provided
- **Description:** Specsmith must output retry recommendations when verification fails.
- **Requirement ID:** REQ-013
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-014. Retries Must Be Bounded
- **ID:** TEST-014
- **Title:** Retries Must Be Bounded
- **Description:** Each retry mechanism may not exceed a fixed maximum number of attempts.
- **Requirement ID:** REQ-014
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-015. Every Governance Action Must Record a Ledger Event
- **ID:** TEST-015
- **Title:** Every Governance Action Must Record a Ledger Event
- **Description:** All changes are logged to `LEDGER.md` and `.specsmith/ledger.jsonl` with timestamp and type.
- **Requirement ID:** REQ-015
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-016. Trace Chain Must Be Tamper‑Evident
- **ID:** TEST-016
- **Title:** Trace Chain Must Be Tamper‑Evident
- **Description:** The trace chain must use chained cryptographic hashes to provide tamper evidence.
- **Requirement ID:** REQ-016
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-017. OpenCode Must Own Execution and Tools
- **ID:** TEST-017
- **Title:** OpenCode Must Own Execution and Tools
- **Description:** All filesystem operations and tool executions are performed by OpenCode.
- **Requirement ID:** REQ-017
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-018. Specsmith Core Must Be Integration‑Agnostic
- **ID:** TEST-018
- **Title:** Specsmith Core Must Be Integration‑Agnostic
- **Description:** The core logic must run without dependency on any implementation.
- **Requirement ID:** REQ-018
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-019. Verification Must Evaluate Changed Files
- **ID:** TEST-019
- **Title:** Verification Must Evaluate Changed Files
- **Description:** Verification must analyze file changes.
- **Requirement ID:** REQ-019
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-020. Verification Must Evaluate Diff Relevance
- **ID:** TEST-020
- **Title:** Verification Must Evaluate Diff Relevance
- **Description:** Verification must ignore irrelevant diffs.
- **Requirement ID:** REQ-020
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-021. Verification Must Evaluate Test Results
- **ID:** TEST-021
- **Title:** Verification Must Evaluate Test Results
- **Description:** Verification must compare outputs.
- **Requirement ID:** REQ-021
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-022. Verification Must Evaluate Contradictions and Uncertainty
- **ID:** TEST-022
- **Title:** Verification Must Evaluate Contradictions and Uncertainty
- **Description:** Identify contradictions.
- **Requirement ID:** REQ-022
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-023. Requirement Schema Must Include Source Location, Type, Priority, Confidence, Status, and Timestamps
- **ID:** TEST-023
- **Title:** Requirement Schema Must Include Source Location, Type, Priority, Confidence, Status, and Timestamps
- **Description:** Schema must include these.
- **Requirement ID:** REQ-023
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-024. Test Case Model Must Include Required Fields
- **ID:** TEST-024
- **Title:** Test Case Model Must Include Required Fields
- **Description:** All test case records must contain required fields.
- **Requirement ID:** REQ-024
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-025. Work Item Model Must Include Required Fields
- **ID:** TEST-025
- **Title:** Work Item Model Must Include Required Fields
- **Description:** Each work item record must contain required fields.
- **Requirement ID:** REQ-025
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-026. Preflight Output Schema Must Include Decision, Work Item ID, Priority, Requirement IDs, Test Case IDs, Confidence Target
- **ID:** TEST-026
- **Title:** Preflight Output Schema Must Include Decision, Work Item ID, Priority, Requirement IDs, Test Case IDs, Confidence Target
- **Description:** Structured preflight output.
- **Requirement ID:** REQ-026
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-027. Verification Input Must Include Diffs, Tests, Logs, and Changed Files
- **ID:** TEST-027
- **Title:** Verification Input Must Include Diffs, Tests, Logs, and Changed Files
- **Description:** Input contains diffs, logs.
- **Requirement ID:** REQ-027
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-028. Retry Strategy Mapping Must Be Defined
- **ID:** TEST-028
- **Title:** Retry Strategy Mapping Must Be Defined
- **Description:** Map strategies.
- **Requirement ID:** REQ-028
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-029. Integration Adapter Interface Must Provide Capabilities
- **ID:** TEST-029
- **Title:** Integration Adapter Interface Must Provide Capabilities
- **Description:** Provide adapter.
- **Requirement ID:** REQ-029
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-030. Specsmith CLI Commands Must Be Explicitly Defined
- **ID:** TEST-030
- **Title:** Specsmith CLI Commands Must Be Explicitly Defined
- **Description:** Expose commands.
- **Requirement ID:** REQ-030
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-031. Sequencing Rules Must Enforce Valid States
- **ID:** TEST-031
- **Title:** Sequencing Rules Must Enforce Valid States
- **Description:** Bootstrap sequencing.
- **Requirement ID:** REQ-031
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-032. Configuration Settings for Optional Features
- **ID:** TEST-032
- **Title:** Configuration Settings for Optional Features
- **Description:** Read config.
- **Requirement ID:** REQ-032
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-033. Default Enablement of Optional Features
- **ID:** TEST-033
- **Title:** Default Enablement of Optional Features
- **Description:** Enabled by default.
- **Requirement ID:** REQ-033
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-034. Evidence ZIP Archive Generation
- **ID:** TEST-034
- **Title:** Evidence ZIP Archive Generation
- **Description:** Generate evidence ZIP.
- **Requirement ID:** REQ-034
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-035. Evidence Manifest Generation
- **ID:** TEST-035
- **Title:** Evidence Manifest Generation
- **Description:** Generate evidence manifest.
- **Requirement ID:** REQ-035
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-036. Per‑File SHA‑256 Hashing in Evidence
- **ID:** TEST-036
- **Title:** Per‑File SHA‑256 Hashing in Evidence
- **Description:** Hash every file.
- **Requirement ID:** REQ-036
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-037. Final Evidence ZIP SHA‑256 Hash
- **ID:** TEST-037
- **Title:** Final Evidence ZIP SHA‑256 Hash
- **Description:** Hash final zip.
- **Requirement ID:** REQ-037
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-038. Author/Owner Metadata Capture
- **ID:** TEST-038
- **Title:** Author/Owner Metadata Capture
- **Description:** Capture metadata.
- **Requirement ID:** REQ-038
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-039. Git Commit Metadata Inclusion
- **ID:** TEST-039
- **Title:** Git Commit Metadata Inclusion
- **Description:** Include git commit.
- **Requirement ID:** REQ-039
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-040. Ledger Reference Inclusion
- **ID:** TEST-040
- **Title:** Ledger Reference Inclusion
- **Description:** Reference ledger.
- **Requirement ID:** REQ-040
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-041. Trusted Timestamp Token Support
- **ID:** TEST-041
- **Title:** Trusted Timestamp Token Support
- **Description:** Include timestamp token.
- **Requirement ID:** REQ-041
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-042. Legal/IP Disclaimer Requirement
- **ID:** TEST-042
- **Title:** Legal/IP Disclaimer Requirement
- **Description:** Provide disclaimer.
- **Requirement ID:** REQ-042
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-043. Ledger Event Hash Chaining
- **ID:** TEST-043
- **Title:** Ledger Event Hash Chaining
- **Description:** Chain events.
- **Requirement ID:** REQ-043
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-044. Ledger Event on Work Proposal
- **ID:** TEST-044
- **Title:** Ledger Event on Work Proposal
- **Description:** Create event on proposal.
- **Requirement ID:** REQ-044
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-045. Ledger Event on Work Completion
- **ID:** TEST-045
- **Title:** Ledger Event on Work Completion
- **Description:** Create event on completion.
- **Requirement ID:** REQ-045
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-046. README.md Generation and Synchronization
- **ID:** TEST-046
- **Title:** README.md Generation and Synchronization
- **Description:** Generate README.
- **Requirement ID:** REQ-046
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-047. CHANGELOG.md Generation and Synchronization
- **ID:** TEST-047
- **Title:** CHANGELOG.md Generation and Synchronization
- **Description:** Generate CHANGELOG.
- **Requirement ID:** REQ-047
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-048. Keep a Changelog Compliance
- **ID:** TEST-048
- **Title:** Keep a Changelog Compliance
- **Description:** Compliance.
- **Requirement ID:** REQ-048
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-049. Semantic Versioning Support
- **ID:** TEST-049
- **Title:** Semantic Versioning Support
- **Description:** Support semantic versioning.
- **Requirement ID:** REQ-049
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-050. Guided Version Bump Workflow
- **ID:** TEST-050
- **Title:** Guided Version Bump Workflow
- **Description:** Guided bump.
- **Requirement ID:** REQ-050
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-051. Guided Release Strategy Workflow
- **ID:** TEST-051
- **Title:** Guided Release Strategy Workflow
- **Description:** Guided release.
- **Requirement ID:** REQ-051
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-052. Guided Branching Strategy Workflow
- **ID:** TEST-052
- **Title:** Guided Branching Strategy Workflow
- **Description:** Guided branching.
- **Requirement ID:** REQ-052
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-053. Default GitFlow Branching Model
- **ID:** TEST-053
- **Title:** Default GitFlow Branching Model
- **Description:** Default GitFlow.
- **Requirement ID:** REQ-053
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-054. Guided Branching Modification
- **ID:** TEST-054
- **Title:** Guided Branching Modification
- **Description:** Guided branching mod.
- **Requirement ID:** REQ-054
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-055. GitHub License Generation
- **ID:** TEST-055
- **Title:** GitHub License Generation
- **Description:** Generate GitHub license.
- **Requirement ID:** REQ-055
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-056. Commercial License Drafting Guidance
- **ID:** TEST-056
- **Title:** Commercial License Drafting Guidance
- **Description:** Draft commercial license.
- **Requirement ID:** REQ-056
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-057. Local Git Commit After Work
- **ID:** TEST-057
- **Title:** Local Git Commit After Work
- **Description:** Commit after work.
- **Requirement ID:** REQ-057
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-058. Confidence Threshold Configuration
- **ID:** TEST-058
- **Title:** Confidence Threshold Configuration
- **Description:** Configure threshold.
- **Requirement ID:** REQ-058
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-059. Iteration Continuation Until Threshold
- **ID:** TEST-059
- **Title:** Iteration Continuation Until Threshold
- **Description:** Continue until threshold.
- **Requirement ID:** REQ-059
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-060. Indefinite Iteration Default
- **ID:** TEST-060
- **Title:** Indefinite Iteration Default
- **Description:** Indefinite iteration default.
- **Requirement ID:** REQ-060
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-061. Max Iterations Configuration
- **ID:** TEST-061
- **Title:** Max Iterations Configuration
- **Description:** Max iterations config.
- **Requirement ID:** REQ-061
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-062. Token/Cost/Time Limits Configuration
- **ID:** TEST-062
- **Title:** Token/Cost/Time Limits Configuration
- **Description:** Token/Cost/Time limits.
- **Requirement ID:** REQ-062
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-063. Stop‑and‑Align Behavior
- **ID:** TEST-063
- **Title:** Stop‑and‑Align Behavior
- **Description:** Stop‑align behavior.
- **Requirement ID:** REQ-063
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-064. Interactive Correction Workflow
- **ID:** TEST-064
- **Title:** Interactive Correction Workflow
- **Description:** Interactive correction workflow.
- **Requirement ID:** REQ-064
- **Type:** unit
- **Verification Method:** evaluator
- **Input:** {}
- **Expected Behavior:** {}
- **Confidence:** 1.0

## TEST-065. Nexus Runtime Must Not Own Governance
- **ID:** TEST-065
- **Title:** Nexus Runtime Must Not Own Governance
- **Description:** Nexus orchestrator module documents that Specsmith owns governance and Nexus only executes.
- **Requirement ID:** REQ-065
- **Type:** unit
- **Verification Method:** pytest
- **Input:** orchestrator.__doc__
- **Expected Behavior:** Module docstring contains "Specsmith governs" and "Nexus only executes"
- **Confidence:** 1.0

## TEST-066. Nexus Must Provide Required Agent Roles
- **ID:** TEST-066
- **Title:** Nexus Must Provide Required Agent Roles
- **Description:** Orchestrator instantiates Planner, Shell, Code, Reviewer, Memory, Git, HumanProxy, and Executor agents.
- **Requirement ID:** REQ-066
- **Type:** unit
- **Verification Method:** pytest
- **Input:** Mocked Orchestrator
- **Expected Behavior:** All eight agents present.
- **Confidence:** 1.0

## TEST-067. Nexus Tool Layer Must Expose Required Tools
- **ID:** TEST-067
- **Title:** Nexus Tool Layer Must Expose Required Tools
- **Description:** specsmith.agent.tools.AVAILABLE_TOOLS contains the 12 required tools by name.
- **Requirement ID:** REQ-067
- **Type:** unit
- **Verification Method:** pytest
- **Input:** AVAILABLE_TOOLS
- **Expected Behavior:** Names match the canonical Nexus tool list.
- **Confidence:** 1.0

## TEST-068. Nexus Safety Middleware Must Block Unsafe Commands
- **ID:** TEST-068
- **Title:** Nexus Safety Middleware Must Block Unsafe Commands
- **Description:** is_safe_command returns False for unsafe patterns and True for safe ones.
- **Requirement ID:** REQ-068
- **Type:** unit
- **Verification Method:** pytest
- **Input:** sample commands
- **Expected Behavior:** Unsafe blocked; safe allowed.
- **Confidence:** 1.0

## TEST-069. Nexus Tool Arguments Must Be JSON Validated
- **ID:** TEST-069
- **Title:** Nexus Tool Arguments Must Be JSON Validated
- **Description:** validate_json_args raises ValueError for non-serializable arguments.
- **Requirement ID:** REQ-069
- **Type:** unit
- **Verification Method:** pytest
- **Input:** non-JSON-serializable args
- **Expected Behavior:** ValueError raised.
- **Confidence:** 1.0

## TEST-070. Nexus Must Normalize File Paths
- **ID:** TEST-070
- **Title:** Nexus Must Normalize File Paths
- **Description:** normalize_path returns absolute resolved paths.
- **Requirement ID:** REQ-070
- **Type:** unit
- **Verification Method:** pytest
- **Input:** relative paths
- **Expected Behavior:** Absolute resolved Path returned.
- **Confidence:** 1.0

## TEST-071. Nexus Must Index the Repository
- **ID:** TEST-071
- **Title:** Nexus Must Index the Repository
- **Description:** generate_index populates files.json, architecture.md, and conventions.md in .repo-index/.
- **Requirement ID:** REQ-071
- **Type:** unit
- **Verification Method:** pytest
- **Input:** Temporary working directory
- **Expected Behavior:** Index files created.
- **Confidence:** 1.0

## TEST-072. Nexus REPL Must Support Slash Commands
- **ID:** TEST-072
- **Title:** Nexus REPL Must Support Slash Commands
- **Description:** repl.py source defines /plan, /ask, /fix, /test, /commit, /pr, /undo, /context, /exit handlers.
- **Requirement ID:** REQ-072
- **Type:** unit
- **Verification Method:** pytest
- **Input:** repl module source
- **Expected Behavior:** All slash command tokens present.
- **Confidence:** 1.0

## TEST-073. Nexus Output Contract
- **ID:** TEST-073
- **Title:** Nexus Output Contract
- **Description:** Orchestrator.run_task issues an initial message containing the required sections.
- **Requirement ID:** REQ-073
- **Type:** unit
- **Verification Method:** pytest
- **Input:** Orchestrator source
- **Expected Behavior:** Plan, Commands to run, Files changed, Diff, Test results, Next action present.
- **Confidence:** 1.0

## TEST-074. vLLM Image Must Be Pinned
- **ID:** TEST-074
- **Title:** vLLM Image Must Be Pinned
- **Description:** docker-compose.yml uses vllm/vllm-openai:v0.8.5 and does not use :latest.
- **Requirement ID:** REQ-074
- **Type:** unit
- **Verification Method:** pytest
- **Input:** docker-compose.yml
- **Expected Behavior:** Pinned tag present, latest absent.
- **Confidence:** 1.0

## TEST-075. vLLM Must Serve l1-nexus Model
- **ID:** TEST-075
- **Title:** vLLM Must Serve l1-nexus Model
- **Description:** docker-compose.yml configures --served-model-name l1-nexus and --tool-call-parser hermes.
- **Requirement ID:** REQ-075
- **Type:** unit
- **Verification Method:** pytest
- **Input:** docker-compose.yml
- **Expected Behavior:** l1-nexus and hermes tokens present.
- **Confidence:** 1.0

## TEST-076. Nexus Tool Executor Registration Must Be Unique
- **ID:** TEST-076
- **Title:** Nexus Tool Executor Registration Must Be Unique
- **Description:** Orchestrator.register_tools calls executor.register_for_execution exactly once per tool.
- **Requirement ID:** REQ-076
- **Type:** unit
- **Verification Method:** pytest
- **Input:** Mocked AG2 agents
- **Expected Behavior:** register_for_execution call count equals number of tools.
- **Confidence:** 1.0

## TEST-077. Safe Cleanup Defaults to Dry-Run
- **ID:** TEST-077
- **Title:** Safe Cleanup Defaults to Dry-Run
- **Description:** clean_repo(apply=False) must not delete files even if matching targets exist.
- **Requirement ID:** REQ-077
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path with __pycache__ created
- **Expected Behavior:** Directory still exists after dry-run; report.dry_run is True.
- **Confidence:** 1.0

## TEST-078. Safe Cleanup Uses Hard-Coded Target List
- **ID:** TEST-078
- **Title:** Safe Cleanup Uses Hard-Coded Target List
- **Description:** clean_repo enumerates only canonical targets defined in the module CANONICAL_TARGETS constant.
- **Requirement ID:** REQ-078
- **Type:** unit
- **Verification Method:** pytest
- **Input:** cleanup module
- **Expected Behavior:** Only canonical targets considered.
- **Confidence:** 1.0

## TEST-079. Safe Cleanup Protects Governance and Source
- **ID:** TEST-079
- **Title:** Safe Cleanup Protects Governance and Source
- **Description:** clean_repo with apply=True must not delete .git, .specsmith, governance files, pyproject.toml, README.md, LICENSE, CHANGELOG.md, src/, tests/, docs/.
- **Requirement ID:** REQ-079
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path resembling a real repo
- **Expected Behavior:** All protected paths still exist after apply.
- **Confidence:** 1.0

## TEST-080. Safe Cleanup Emits Structured Report
- **ID:** TEST-080
- **Title:** Safe Cleanup Emits Structured Report
- **Description:** clean_repo returns a CleanupReport with removed, skipped, and bytes_reclaimed fields.
- **Requirement ID:** REQ-080
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path
- **Expected Behavior:** Report exposes the required fields.
- **Confidence:** 1.0

## TEST-081. specsmith clean CLI Subcommand
- **ID:** TEST-081
- **Title:** specsmith clean CLI Subcommand
- **Description:** Invoking `specsmith clean` via click's CliRunner returns 0; defaults to dry-run; `--apply` removes targets and appends a `cleanup` ledger event referencing REQ-077..REQ-080. `--json` emits a parseable JSON report.
- **Requirement ID:** REQ-081
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over isolated tmp_path
- **Expected Behavior:** Exit code 0; correct mode flags; ledger entry on apply.
- **Confidence:** 1.0

## TEST-082. UTF-8 Safe Console Factory
- **ID:** TEST-082
- **Title:** UTF-8 Safe Console Factory
- **Description:** make_console returns a rich.console.Console instance with legacy_windows disabled and printing common glyphs (⚠, →, ✓, ✗) to a captured buffer must not raise UnicodeEncodeError.
- **Requirement ID:** REQ-082
- **Type:** unit
- **Verification Method:** pytest
- **Input:** make_console with file=io.StringIO
- **Expected Behavior:** Console.print of the test glyphs returns without error and the captured output contains them.
- **Confidence:** 1.0

## TEST-083. Canonical Test Spec File Is TESTS.md
- **ID:** TEST-083
- **Title:** Canonical Test Spec File Is TESTS.md
- **Description:** The repository must contain `TESTS.md` and `docs/TESTS.md` (not `TEST_SPEC.md`/`TEST-SPECS.md`/`TEST-SPEC.md`); the source tree (excluding `.specsmith/runs/*.patch` historical evidence) must contain no remaining references to the legacy names; the scaffolder, auditor, importer, retrieval, exporter, requirements, phase, recovery, and stress-tester modules must reference `TESTS.md`.
- **Requirement ID:** REQ-083
- **Type:** unit
- **Verification Method:** pytest
- **Input:** repository tree
- **Expected Behavior:** Canonical `TESTS.md` files exist, legacy names absent from active source/docs/templates, key modules reference the new name.
- **Confidence:** 1.0

## TEST-084. Natural-Language Governance Broker
- **ID:** TEST-084
- **Title:** Natural-Language Governance Broker
- **Description:** `specsmith.agent.broker.classify_intent` correctly tags read-only/change/release/destructive utterances; `infer_scope` returns relevant existing REQ IDs from a tmp-path REQUIREMENTS.md; `run_preflight` invokes the Specsmith CLI and parses its JSON; `narrate_plan` renders a plain-language plan that does NOT contain REQ-/TEST-/WI- tokens by default; `execute_with_governance` honors the configured retry budget and escalates with a single clarifying question on stop-and-align.
- **Requirement ID:** REQ-084
- **Type:** unit
- **Verification Method:** pytest
- **Input:** Mocked Specsmith CLI + tmp-path REQUIREMENTS.md
- **Expected Behavior:** Broker classifies, scopes, preflights, narrates without IDs, and bounds retries per REQ-014.
- **Confidence:** 1.0

## TEST-085. specsmith preflight CLI Emits Required JSON
- **ID:** TEST-085
- **Title:** specsmith preflight CLI Emits Required JSON
- **Description:** Invoking `specsmith preflight <utterance> --json --project-dir <tmp_path>` via click's CliRunner returns exit code 0 and a JSON object with all required keys; read-only asks resolve to `accepted`, destructive utterances resolve to `needs_clarification`, and an utterance with no matching scope also resolves to `needs_clarification` with a non-empty `instruction`.
- **Requirement ID:** REQ-085
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over isolated tmp_path
- **Expected Behavior:** JSON parses; required keys present; decisions match intent.
- **Confidence:** 1.0

## TEST-086. REPL Gates Execution on Preflight Acceptance
- **ID:** TEST-086
- **Title:** REPL Gates Execution on Preflight Acceptance
- **Description:** The Nexus REPL source must guard the orchestrator call so that `run_task` is only invoked when the preflight decision is `accepted`; any other decision must short-circuit and return to the prompt.
- **Requirement ID:** REQ-086
- **Type:** unit
- **Verification Method:** pytest
- **Input:** repl module source
- **Expected Behavior:** Source contains a guard checking `decision.accepted` (or equivalent) before `orchestrator.run_task` is invoked from the broker branch.
- **Confidence:** 1.0

## TEST-087. REPL Drives Orchestrator via Bounded-Retry Harness
- **ID:** TEST-087
- **Title:** REPL Drives Orchestrator via Bounded-Retry Harness
- **Description:** The REPL module must invoke `execute_with_governance` from the broker branch, passing the preflight decision and an executor closure built around `orchestrator.run_task`; `orchestrator.run_task` must not be called directly from the broker branch (only via the harness's executor argument).
- **Requirement ID:** REQ-087
- **Type:** unit
- **Verification Method:** pytest
- **Input:** repl module source
- **Expected Behavior:** Source imports `execute_with_governance`, calls it inside the broker branch, and the only `orchestrator.run_task(` call appears inside the executor closure.
- **Confidence:** 1.0

## TEST-088. specsmith preflight Resolves Test Case IDs From Machine State
- **ID:** TEST-088
- **Title:** specsmith preflight Resolves Test Case IDs From Machine State
- **Description:** Invoking `specsmith preflight` over a tmp project that contains a REQUIREMENTS.md (REQ-077) and a matching `.specsmith/testcases.json` (TEST-077 → REQ-077) must emit a JSON payload whose `test_case_ids` includes `TEST-077` when the change is accepted; the CLI must never emit ids absent from machine state.
- **Requirement ID:** REQ-088
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over isolated tmp_path with seeded testcases.json
- **Expected Behavior:** `test_case_ids` is non-empty and contains the joined TEST id; unknown ids never appear.
- **Confidence:** 1.0

## TEST-089. Nexus Live l1-nexus Smoke Test Script
- **ID:** TEST-089
- **Title:** Nexus Live l1-nexus Smoke Test Script
- **Description:** `scripts/nexus_smoke.py` must expose a `smoke_test(base_url=...)` function that POSTs a chat-completions request and returns a dict with `ok`, `content`, and `latency_ms`. A pytest test must skip unless `NEXUS_LIVE=1` is set; when invoked offline, the script must surface a clear error rather than crash. Static checks must confirm the script exists and exposes the expected callable.
- **Requirement ID:** REQ-089
- **Type:** unit
- **Verification Method:** pytest
- **Input:** scripts/nexus_smoke.py
- **Expected Behavior:** Module importable; `smoke_test` callable; integration test skipped offline; live test passes when container is up.
- **Confidence:** 1.0

## TEST-090. Nexus Documentation Surfaces Broker, Preflight, and Gated Execution
- **ID:** TEST-090
- **Title:** Nexus Documentation Surfaces Broker, Preflight, and Gated Execution
- **Description:** `ARCHITECTURE.md` and `README.md` must each contain a 'Nexus' section that mentions the broker, `specsmith preflight`, the REPL execution gate, and the `/why` toggle; the documentation must not contain literal REQ/TEST/WI tokens outside fenced governance examples.
- **Requirement ID:** REQ-090
- **Type:** unit
- **Verification Method:** pytest
- **Input:** ARCHITECTURE.md, README.md
- **Expected Behavior:** Each file mentions the broker concept, the preflight CLI, the gate, and the `/why` toggle.
- **Confidence:** 1.0

## TEST-091. Orchestrator.run_task Returns a Structured TaskResult
- **ID:** TEST-091
- **Title:** Orchestrator.run_task Returns a Structured TaskResult
- **Description:** `orchestrator.run_task` must return a `TaskResult` instance whose attributes include `equilibrium`, `confidence`, `summary`, `files_changed`, and `test_results`. The REPL source must consume that result inside the executor closure (`result.equilibrium`, `result.confidence`) rather than computing equilibrium from `bool(summary)`.
- **Requirement ID:** REQ-091
- **Type:** unit
- **Verification Method:** pytest
- **Input:** orchestrator module + REPL source
- **Expected Behavior:** TaskResult dataclass exposes the required fields; REPL source references `result.equilibrium` and `result.confidence`.
- **Confidence:** 1.0

## TEST-092. specsmith preflight CLI Returns Decision-Specific Exit Codes
- **ID:** TEST-092
- **Title:** specsmith preflight CLI Returns Decision-Specific Exit Codes
- **Description:** Invoking `specsmith preflight` over a tmp project must exit 0 for `accepted` decisions, 2 for `needs_clarification`, and 3 for `blocked`/`rejected`. The JSON payload must continue to be emitted on stdout regardless of exit code.
- **Requirement ID:** REQ-092
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over isolated tmp_path
- **Expected Behavior:** Exit code matches the decision; JSON parses on stdout for both 0 and 2 exits.
- **Confidence:** 1.0

## TEST-093. Accepted preflight Records a Ledger Event
- **ID:** TEST-093
- **Title:** Accepted preflight Records a Ledger Event
- **Description:** When the preflight decision is `accepted` and `LEDGER.md` exists in the tmp project root, invoking the CLI must append a new ledger entry tagged with `REQ-085` and the matched `requirement_ids`. When the decision is `needs_clarification`, the ledger must not gain an entry.
- **Requirement ID:** REQ-093
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner with seeded LEDGER.md
- **Expected Behavior:** LEDGER.md grows on accept; LEDGER.md unchanged on needs_clarification.
- **Confidence:** 1.0

## TEST-094. /why Surfaces Post-Run Governance Block in REPL
- **ID:** TEST-094
- **Title:** /why Surfaces Post-Run Governance Block in REPL
- **Description:** Inspecting the REPL source must show a `[/why]` post-run block guarded by `verbose_governance` after `execute_with_governance` returns; the block must reference `work_item_id`, `requirement_ids`, `test_case_ids`, `confidence`, and `equilibrium`.
- **Requirement ID:** REQ-094
- **Type:** unit
- **Verification Method:** pytest
- **Input:** repl module source
- **Expected Behavior:** Source contains a `[/why]` block guarded by verbose_governance and referencing the required keys.
- **Confidence:** 1.0

## TEST-095. Nexus Live Smoke Evidence Captured
- **ID:** TEST-095
- **Title:** Nexus Live Smoke Evidence Captured
- **Description:** `.specsmith/runs/WI-NEXUS-011/logs.txt` must exist and document either a successful live smoke (`ok: true`) or an honest reason the live container could not be reached.
- **Requirement ID:** REQ-095
- **Type:** unit
- **Verification Method:** pytest
- **Input:** .specsmith/runs/WI-NEXUS-011/logs.txt
- **Expected Behavior:** Log file present and non-empty; mentions either ok=true/false from the smoke script.
- **Confidence:** 1.0

