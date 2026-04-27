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
- **Description:** Only Specsmith may create, update, or delete the human‑readable governance files `ARCHITECTURE.md`, `REQUIREMENTS.md`, `TEST_SPEC.md`, and `LEDGER.md`.
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

