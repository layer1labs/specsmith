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

## TEST-096. execute_with_governance Maps Failures to Retry Strategies
- **ID:** TEST-096
- **Title:** execute_with_governance Maps Failures to Retry Strategies
- **Description:** When the executor never reaches equilibrium, `execute_with_governance` must populate `RunResult.strategy` with one of the canonical labels: `narrow_scope`, `expand_scope`, `fix_tests`, `rollback`, or `stop`. The clarifying question must mention the chosen label.
- **Requirement ID:** REQ-096
- **Type:** unit
- **Verification Method:** pytest
- **Input:** mocked executor returning failure reports
- **Expected Behavior:** `result.strategy` is a canonical label; `result.clarifying_question` references it.
- **Confidence:** 1.0

## TEST-097. specsmith verify CLI Emits Required JSON
- **ID:** TEST-097
- **Title:** specsmith verify CLI Emits Required JSON
- **Description:** Invoking `specsmith verify --stdin --json` with a JSON verification payload via click's CliRunner must return a JSON object containing `equilibrium`, `confidence`, `summary`, `files_changed`, `test_results`, and `retry_strategy`. Exit code is 0 when equilibrium and confidence ≥ threshold, 2 when retry is recommended, and 3 on stop-and-align.
- **Requirement ID:** REQ-097
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner with stdin JSON
- **Expected Behavior:** JSON parses; required keys present; exit code matches verification outcome.
- **Confidence:** 1.0

## TEST-098. Confidence Threshold Read From .specsmith/config.yml
- **ID:** TEST-098
- **Title:** Confidence Threshold Read From .specsmith/config.yml
- **Description:** When `.specsmith/config.yml` sets `epistemic.confidence_threshold: 0.95` (well above the heuristic default), invoking `specsmith preflight` over a tmp project must return `confidence_target >= 0.95`. When the config file is absent, the heuristic default still applies.
- **Requirement ID:** REQ-098
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over tmp_path with seeded config.yml
- **Expected Behavior:** confidence_target floor matches the config when present; falls back to heuristic when absent.
- **Confidence:** 1.0

## TEST-099. Accepted Preflight Records work_proposal Event Once
- **ID:** TEST-099
- **Title:** Accepted Preflight Records work_proposal Event Once
- **Description:** When the preflight decision is `accepted` and the assigned `work_item_id` is not already in `LEDGER.md`, the CLI must emit BOTH a `preflight` ledger entry AND a `work_proposal` ledger entry tagged with `REQ-044` and `REQ-085`. A subsequent invocation that surfaces a different work_item_id must emit a second work_proposal entry.
- **Requirement ID:** REQ-099
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over tmp_path with LEDGER.md
- **Expected Behavior:** LEDGER.md contains a `work_proposal` entry referencing REQ-044, REQ-085, and the work_item_id; subsequent acceptance with a different id appends another work_proposal.
- **Confidence:** 1.0

## TEST-100. Broker Scope Inference Surfaces Stress Warnings Under --stress
- **ID:** TEST-100
- **Title:** Broker Scope Inference Surfaces Stress Warnings Under --stress
- **Description:** Invoking `specsmith preflight "fix the cleanup bug" --stress` over a tmp project that has matched requirements with at least one synthetic critical failure must include a non-empty `stress_warnings` list in the JSON payload. Without `--stress`, the field is absent (or empty).
- **Requirement ID:** REQ-100
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over tmp_path with seeded REQUIREMENTS.md
- **Expected Behavior:** `stress_warnings` populated under --stress when StressTester reports critical failures; absent or empty otherwise.
- **Confidence:** 1.0
## TEST-101. Lint Baseline Is Clean on develop
- **ID:** TEST-101
- **Title:** Lint Baseline Is Clean on develop
- **Description:** `ruff check src/ tests/` and `ruff format --check src/ tests/` both exit zero on `develop`. The CI workflow's `lint` job is the canonical gate; running both commands locally produces "All checks passed!" and "112 files already formatted" (or equivalent for the current file count).
- **Requirement ID:** REQ-101
- **Type:** integration
- **Verification Method:** ci
- **Input:** working tree on develop
- **Expected Behavior:** Both ruff invocations exit 0; CI lint job is green on PRs targeting develop.
- **Confidence:** 1.0
## TEST-102. Type-Check Baseline Is Clean on develop
- **ID:** TEST-102
- **Title:** Type-Check Baseline Is Clean on develop
- **Description:** `mypy src/specsmith/` exits zero on `develop`. The CI workflow's `typecheck` job is the canonical gate. Modules added to the `ignore_errors=true` overrides in `pyproject.toml` (REQ-102) must remain enumerated; new modules must justify any addition with a comment.
- **Requirement ID:** REQ-102
- **Type:** integration
- **Verification Method:** ci
- **Input:** working tree on develop
- **Expected Behavior:** mypy exits 0; CI typecheck job is green on PRs targeting develop.
- **Confidence:** 1.0
## TEST-103. Security Job Passes With pip-audit ignore-vuln
- **ID:** TEST-103
- **Title:** Security Job Passes With pip-audit ignore-vuln
- **Description:** The CI security job upgrades pip to the latest release, installs `pip-audit`, installs specsmith with its runtime dependencies, then runs `pip-audit --ignore-vuln CVE-2026-3219`. The job exits zero on `develop`.
- **Requirement ID:** REQ-103
- **Type:** integration
- **Verification Method:** ci
- **Input:** working tree on develop
- **Expected Behavior:** pip-audit exits 0 under the documented ignore-vuln flag; CI security job is green on PRs targeting develop.
- **Confidence:** 1.0
## TEST-104. workitems.json Mirrors Implemented REQs
- **ID:** TEST-104
- **Title:** workitems.json Mirrors Implemented REQs
- **Description:** Running `python scripts/sync_workitems.py` produces a `.specsmith/workitems.json` whose count matches the REQ count, every entry has `status=complete`, and every entry's `test_case_ids` lists the TEST ids that share the matching `requirement_id`.
- **Requirement ID:** REQ-104
- **Type:** integration
- **Verification Method:** script
- **Input:** developer workstation
- **Expected Behavior:** Sync prints `Synced N work items (N complete, 0 pending)` where N == REQ count.
- **Confidence:** 1.0
## TEST-105. Live Smoke Logs Document Skip Reason
- **ID:** TEST-105
- **Title:** Live Smoke Logs Document Skip Reason
- **Description:** `.specsmith/runs/WI-NEXUS-011/logs.txt` contains a fresh `nexus_smoke.py` probe output (with `"ok": false` or `"ok": true`), a UTC timestamp, the host's docker + GPU info, and a documented reason if the container could not be reached.
- **Requirement ID:** REQ-105
- **Type:** unit
- **Verification Method:** pytest
- **Input:** .specsmith/runs/WI-NEXUS-011/logs.txt
- **Expected Behavior:** Logs file references either ok=true or ok=false / NEXUS_LIVE; documents the skip reason when applicable.
- **Confidence:** 1.0
## TEST-106. VS Code Extension Registers Broker Commands
- **ID:** TEST-106
- **Title:** VS Code Extension Registers Broker Commands
- **Description:** `specsmith-vscode/package.json` declares `specsmith.runPreflight`, `specsmith.runVerify`, and `specsmith.toggleWhy`; `src/extension.ts` registers each with `vscode.commands.registerCommand`; `npm run lint` (`tsc --noEmit`) exits zero.
- **Requirement ID:** REQ-106
- **Type:** integration
- **Verification Method:** npm
- **Input:** specsmith-vscode repo
- **Expected Behavior:** Three new commands visible in the command palette; tsc emits no errors.
- **Confidence:** 1.0
## TEST-107. ARCHITECTURE.md Has Current State Section
- **ID:** TEST-107
- **Title:** ARCHITECTURE.md Has Current State Section
- **Description:** `ARCHITECTURE.md` contains a heading whose text begins with 'Current State' and whose body references the broker, retry strategies, CI baseline, VS Code extension parity, live-smoke evidence, and documentation surface.
- **Requirement ID:** REQ-107
- **Type:** unit
- **Verification Method:** pytest
- **Input:** ARCHITECTURE.md
- **Expected Behavior:** Section present and references all six post-WI-NEXUS-023 facets.
- **Confidence:** 1.0
## TEST-108. Verifier Scores Confidence From Tests/Lint/Type Outputs
- **ID:** TEST-108
- **Title:** Verifier Scores Confidence From Tests/Lint/Type Outputs
- **Description:** `verifier.score(report)` returns higher confidence when test_results report 0 failures, ruff_errors=0, mypy_errors=0; lower confidence when failures > 0; equilibrium=True only when all three gates are clean and confidence >= target.
- **Requirement ID:** REQ-108
- **Type:** unit
- **Verification Method:** pytest
- **Input:** synthetic verifier reports
- **Expected Behavior:** confidence and equilibrium reflect inputs deterministically.
- **Confidence:** 1.0
## TEST-109. Smoke Overlay File Pins 7B Q4 Model
- **ID:** TEST-109
- **Title:** Smoke Overlay File Pins 7B Q4 Model
- **Description:** `docker-compose.smoke.yml` exists and references a 7B GPTQ-Int4 model + `--served-model-name l1-nexus`. Evidence file `.specsmith/runs/WI-NEXUS-029/logs.txt` exists and references the overlay.
- **Requirement ID:** REQ-109
- **Type:** unit
- **Verification Method:** pytest
- **Input:** docker-compose.smoke.yml
- **Expected Behavior:** Overlay present; file references 7B + Int4 + l1-nexus.
- **Confidence:** 1.0
## TEST-110. End-to-End Nexus Path Reaches Equilibrium
- **ID:** TEST-110
- **Title:** End-to-End Nexus Path Reaches Equilibrium
- **Description:** Driving a `FakeOrchestrator` through `execute_with_governance` with scripted attempt-1 failure and attempt-2 success yields `RunResult.success=True`, ledger gains a preflight + work_proposal entry, and retry strategy is empty.
- **Requirement ID:** REQ-110
- **Type:** integration
- **Verification Method:** pytest
- **Input:** tmp_path with REQUIREMENTS.md + LEDGER.md + FakeOrchestrator
- **Expected Behavior:** end-to-end success; ledger written.
- **Confidence:** 1.0
## TEST-111. Mypy Strict Carveout Reduced
- **ID:** TEST-111
- **Title:** Mypy Strict Carveout Reduced
- **Description:** `pyproject.toml`'s `[[tool.mypy.overrides]] ignore_errors=true` block does NOT include `specsmith.agent.broker`, `specsmith.agent.safety`, `specsmith.console_utils`, or `specsmith.agent.indexer`. `mypy src/specsmith/` exits zero.
- **Requirement ID:** REQ-111
- **Type:** integration
- **Verification Method:** pytest
- **Input:** pyproject.toml
- **Expected Behavior:** Listed modules absent from carveout.
- **Confidence:** 1.0
## TEST-112. Streaming Chat Emits Required JSONL Event Types
- **ID:** TEST-112
- **Title:** Streaming Chat Emits Required JSONL Event Types
- **Description:** Invoking `specsmith chat <utterance> --json-events --project-dir <tmp>` (against a stub orchestrator) emits at least one `block_start`, one `block_complete`, and one `task_complete` event on stdout.
- **Requirement ID:** REQ-112
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner over tmp_path with stub orchestrator
- **Expected Behavior:** Required event kinds present in JSONL output.
- **Confidence:** 1.0
## TEST-113. Block Schema Has block_id, kind, agent, timestamp
- **ID:** TEST-113
- **Title:** Block Schema Has block_id, kind, agent, timestamp
- **Description:** Every emitted `block_start` event has all four required keys; the matching `block_complete` event reuses the same `block_id` value.
- **Requirement ID:** REQ-113
- **Type:** unit
- **Verification Method:** pytest
- **Input:** stub event stream
- **Expected Behavior:** Schema satisfied.
- **Confidence:** 1.0
## TEST-114. Plan Block Surfaces Steps with Status Transitions
- **ID:** TEST-114
- **Title:** Plan Block Surfaces Steps with Status Transitions
- **Description:** When the broker classifies a `change` and the orchestrator runs, a `plan` block is emitted with at least one step; subsequent `plan_step` events reference the step by id and end with `status=done` or `status=failed`.
- **Requirement ID:** REQ-114
- **Type:** unit
- **Verification Method:** pytest
- **Input:** stub orchestrator emitting plan steps
- **Expected Behavior:** plan event present; step transitions emitted.
- **Confidence:** 1.0
## TEST-115. --profile Flag Is Honored And Recorded
- **ID:** TEST-115
- **Title:** --profile Flag Is Honored And Recorded
- **Description:** Passing `--profile safe` to `specsmith chat` causes the chat-event stream to include a `profile` field on the `task_complete` event matching `safe`. Passing `--profile open` gives `profile: open`.
- **Requirement ID:** REQ-115
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner
- **Expected Behavior:** Selected profile reflected in stream.
- **Confidence:** 1.0
## TEST-116. Inline Diff Round-Trip
- **ID:** TEST-116
- **Title:** Inline Diff Round-Trip
- **Description:** `specsmith verify --comment 'fix the off-by-one'` records the comment in `task_complete.comments` (or, in chat mode, the next harness retry surfaces it via memory).
- **Requirement ID:** REQ-116
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner verify with --comment
- **Expected Behavior:** Comment persisted.
- **Confidence:** 1.0
## TEST-117. Predict-Only Preflight Does Not Allocate Work Item
- **ID:** TEST-117
- **Title:** Predict-Only Preflight Does Not Allocate Work Item
- **Description:** `specsmith preflight 'fix the cleanup' --predict-only --json` returns `work_item_id == ''`, includes a `predicted_refinement` field, and does NOT modify `LEDGER.md`.
- **Requirement ID:** REQ-117
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner preflight with --predict-only
- **Expected Behavior:** No work_item_id, no ledger writes, predicted_refinement present.
- **Confidence:** 1.0
## TEST-118. Extension Declares specsmith.openChat Command
- **ID:** TEST-118
- **Title:** Extension Declares specsmith.openChat Command
- **Description:** `specsmith-vscode/package.json` declares the `specsmith.openChat` command; `src/extension.ts` registers a handler for it. Sister-repo gate.
- **Requirement ID:** REQ-118
- **Type:** integration
- **Verification Method:** static-check
- **Input:** specsmith-vscode repo
- **Expected Behavior:** Command declared and registered; package.json version >= 0.4.0.
- **Confidence:** 1.0
## TEST-119. Rules Loader Returns Project Rules As System-Prompt Prefix
- **ID:** TEST-119
- **Title:** Rules Loader Returns Project Rules As System-Prompt Prefix
- **Description:** `rules.load_rules(tmp_path)` reads the seeded `docs/governance/RULES.md` plus AGENTS.md H-rules and returns a non-empty string that contains the rule body verbatim.
- **Requirement ID:** REQ-119
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path with seeded governance docs
- **Expected Behavior:** Returned string contains the seeded rule text.
- **Confidence:** 1.0
## TEST-120. Memory Append/Read Round-Trip
- **ID:** TEST-120
- **Title:** Memory Append/Read Round-Trip
- **Description:** `memory.append_turn(session_id, turn)` followed by `memory.recent_turns(session_id, max_chars=10000)` returns the appended turn's content; capping by `max_chars` truncates oldest first.
- **Requirement ID:** REQ-120
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path session
- **Expected Behavior:** Round-trip works; cap honored.
- **Confidence:** 1.0
## TEST-121. MCP Loader Reads .specsmith/mcp.yml
- **ID:** TEST-121
- **Title:** MCP Loader Reads .specsmith/mcp.yml
- **Description:** `mcp.load_mcp_tools(tmp_path)` reads a seeded `.specsmith/mcp.yml` with one entry and returns one tool wrapper whose name matches the configured server.
- **Requirement ID:** REQ-121
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path with mcp.yml
- **Expected Behavior:** Loader returns one tool; safety wrapper applied.
- **Confidence:** 1.0
## TEST-122. Router Picks Tier From Intent
- **ID:** TEST-122
- **Title:** Router Picks Tier From Intent
- **Description:** `router.choose_tier('change', scope, retry_count=0)` returns `coder`; `choose_tier('release', ...)` returns `heavy`; `choose_tier('read_only_ask', ...)` returns `fast`. Override via `.specsmith/config.yml routing:` is honored.
- **Requirement ID:** REQ-122
- **Type:** unit
- **Verification Method:** pytest
- **Input:** synthetic intents + config
- **Expected Behavior:** Tier matches mapping; override wins.
- **Confidence:** 1.0
## TEST-123. Notebook Record Writes docs/notebooks/<slug>.md
- **ID:** TEST-123
- **Title:** Notebook Record Writes docs/notebooks/<slug>.md
- **Description:** `specsmith notebook record --session-id S --slug demo --project-dir <tmp>` reads `.specsmith/sessions/S/turns.jsonl` and writes a markdown notebook to `docs/notebooks/demo.md` containing each turn.
- **Requirement ID:** REQ-123
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path with seeded session
- **Expected Behavior:** Notebook file written with turns.
- **Confidence:** 1.0
## TEST-124. Perf Smoke Writes Baseline JSON
- **ID:** TEST-124
- **Title:** Perf Smoke Writes Baseline JSON
- **Description:** Running `scripts/perf_smoke.py --runs 3 --reqs 50 --output <tmp>/baseline.json` writes a JSON file with `p50`, `p95`, `p99` numeric keys.
- **Requirement ID:** REQ-124
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path output
- **Expected Behavior:** File written; required keys present.
- **Confidence:** 1.0
## TEST-125. Multi-Session Parent/Child Wiring
- **ID:** TEST-125
- **Title:** Multi-Session Parent/Child Wiring
- **Description:** `specsmith chat ... --session-id child --parent-session parent` causes the `task_complete` event to also write a `sub_session_complete` line into the parent session's turns.jsonl.
- **Requirement ID:** REQ-125
- **Type:** unit
- **Verification Method:** pytest
- **Input:** tmp_path with parent + child sessions
- **Expected Behavior:** Parent session log contains sub_session_complete entry.
- **Confidence:** 1.0
## TEST-127. Onboarding Doctor Has Required Checks
- **ID:** TEST-127
- **Title:** Onboarding Doctor Has Required Checks
- **Description:** `specsmith doctor --onboarding --project-dir <tmp>` prints a checklist that includes lines for 'CLI installed', 'scaffold.yml', 'REQUIREMENTS.md', and 'LEDGER.md'.
- **Requirement ID:** REQ-127
- **Type:** unit
- **Verification Method:** pytest
- **Input:** click.testing.CliRunner doctor --onboarding
- **Expected Behavior:** Required check labels appear in stdout.
- **Confidence:** 1.0
## TEST-128. specsmith-vscode CI Runs npm audit
- **ID:** TEST-128
- **Title:** specsmith-vscode CI Runs npm audit
- **Description:** `specsmith-vscode/.github/workflows/ci.yml` includes a step running `npm audit --omit=dev --audit-level=high`. Sister-repo gate.
- **Requirement ID:** REQ-128
- **Type:** integration
- **Verification Method:** static-check
- **Input:** specsmith-vscode CI workflow
- **Expected Behavior:** Step present.
- **Confidence:** 1.0
## TEST-129. API Stability Doc Enumerates Frozen Surface
- **ID:** TEST-129
- **Title:** API Stability Doc Enumerates Frozen Surface
- **Description:** `docs/site/api-stability.md` exists and enumerates: CLI subcommands, exit codes, JSON payload schemas, broker module API, ledger event schemas, VS Code extension command IDs. `pyproject.toml` version is `1.0.0` and classifier is `Production/Stable`.
- **Requirement ID:** REQ-129
- **Type:** unit
- **Verification Method:** pytest
- **Input:** docs/site/api-stability.md, pyproject.toml
- **Expected Behavior:** All six API surfaces enumerated; version+classifier match.
- **Confidence:** 1.0

