# Plain-English Glossary

This glossary translates core SpecSmith terms into practical language.

## Minimum vocabulary needed to start

If you only remember six terms, start with these:

- Work Item
- Requirement ID
- Preflight
- Verify
- Audit Chain
- Governance Phase

These six terms are enough to run a governed change end-to-end.

## Terminology table

| SpecSmith term | Plain-English meaning | Why it matters | Example |
|---|---|---|---|
| Work Item | A tracked unit of intended change. | Gives each change a lifecycle and audit trail. | `WI-3A9F1C02` tracks a bug fix from acceptance to closure. |
| Requirement ID | A stable label for an expected behavior. | Connects implementation and tests to explicit intent. | `REQ-042` says retries are required for transient failures. |
| Preflight | Governance check before making a change. | Prevents uncontrolled or unclear edits. | `specsmith preflight "add retries"` returns `accepted`. |
| AEE | Applied Epistemic Engineering method in SpecSmith. | Defines how assumptions are tested and refined. | Frame → Stress-test → Reconstruct decisions for a feature. |
| ESDB | Epistemic State Database storing governance state/events. | Preserves durable, queryable governance history. | Work items and trace references are persisted in ESDB records. |
| OEA | Ontology-Epistemic-Agentic anti-drift framework concepts. | Improves model behavior transparency and reliability controls. | OEA metadata fields record confidence and boundary context. |
| Equilibrium | Verified state where requirements, tests, and evidence align. | Indicates the change is governed and stable enough to proceed. | `specsmith verify` reports equilibrium reached. |
| Belief Artifact | Formalized assumption/claim treated as an engineering artifact. | Makes assumptions testable instead of implicit. | “API always returns JSON” is stress-tested as an artifact. |
| TraceVault | Tamper-evident chained record of actions/decisions. | Supports post-hoc audit and integrity checks. | `trace.jsonl` contains hash-linked events. |
| WAL | Write-ahead log used for append-only durability. | Enables recovery and tamper-evidence workflows. | ChronoStore writes events to WAL before snapshot update. |
| ChronoStore | Commercial ESDB backend with advanced durability controls. | Adds enterprise tamper-evidence/performance features. | Organization enables ChronoStore+ for regulated workloads. |
| Epistemic Boundary | What is inside vs outside validated knowledge scope. | Prevents over-claiming and drift beyond evidence. | Agent marks unknowns outside the boundary as unresolved. |
| Governance Phase | Current lifecycle stage in AEE workflow. | Gives objective readiness expectations per stage. | Project moves from Requirements to Test Spec phase. |
| Audit Chain | Linked evidence path from decision to outcome. | Proves how and why a change happened. | Preflight decision links to implementation and verify records. |

