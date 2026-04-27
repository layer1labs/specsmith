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
- **Description:** Only Specsmith may create, update, or delete the human‑readable governance files `ARCHITECTURE.md`, `REQUIREMENTS.md`, `TEST_SPEC.md`, and `LEDGER.md`.
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

