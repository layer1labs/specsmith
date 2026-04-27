# epistemic Library

The `epistemic` package is a standalone Python library co-installed with specsmith.
It has **zero external dependencies** beyond Python 3.10+ and can be used in any project.

## Installation

```bash
pip install specsmith    # installs both specsmith and epistemic
```

After installation:

```python
from epistemic import AEESession          # high-level facade
from epistemic import BeliefArtifact      # core data model
from epistemic import StressTester        # adversarial challenges
from epistemic import CertaintyEngine     # confidence scoring
from epistemic import FailureModeGraph    # failure mapping
from epistemic import RecoveryOperator    # recovery proposals
from epistemic.trace import TraceVault    # cryptographic sealing
```

## Quick Start

The simplest pattern is 3 lines:

```python
from epistemic import AEESession

session = AEESession("my-project")
session.add_belief("HYP-001", ["My hypothesis is correct"],
                   epistemic_boundary=["Context: phase 1 only"])
result = session.run()
print(result.summary())
```

## AEESession Reference

`AEESession` is the primary entry point. It bundles all AEE machinery into one object.

### Constructor

```python
AEESession(
    project_name: str,
    threshold: float = 0.7,         # certainty threshold (0.0-1.0)
    state_file: Path | None = None, # for JSON persistence
    trace_dir: Path | None = None,  # for cryptographic sealing
)
```

### Belief Management

```python
# Add a belief artifact
artifact = session.add_belief(
    artifact_id="REQ-001",
    propositions=["The system returns HTTP 200 for valid requests"],
    epistemic_boundary=["Platform: all", "Auth: JWT required"],
    domain="software",
    status=BeliefStatus.DRAFT,
    confidence=ConfidenceLevel.UNKNOWN,
    priority="P1",
)

# Accept a belief (enables stress-testing requirements)
session.accept("REQ-001")

# Add evidence (elevates confidence)
session.add_evidence("REQ-001", "Integration test suite passes")

# Mark as having experimental/test coverage
session.mark_covered("REQ-001")

# Load from specsmith REQUIREMENTS.md
count = session.load_from_requirements(Path("docs/REQUIREMENTS.md"))

# Load from dicts (JSON/YAML/database)
count = session.load_from_dicts([
    {"artifact_id": "HYP-001", "propositions": [...], ...}
])
```

### Running the AEE Pipeline

```python
# Full pipeline: stress-test + failure graph + certainty + recovery
result = session.run(accepted_only=False)

# Inspect results
result.is_healthy()                           # True if at equilibrium + above threshold
result.stress_result.equilibrium              # True if no new failures
result.stress_result.total_failures           # total failure modes found
result.stress_result.logic_knots              # [(id1, id2, reason), ...]
result.certainty_report.overall_score         # 0.0-1.0
result.certainty_report.below_threshold       # [artifact_ids...]
result.proposals                              # [RecoveryProposal, ...]
result.graph.render_mermaid()                 # Mermaid diagram
print(result.summary())                       # formatted report

# Individual phases
stress = session.stress_test()
certainty = session.score()
equilibrium = session.equilibrium_check()     # quick check, no graph build
```

### Persistence

```python
# Save/load JSON state
session.save(Path("beliefs.json"))
session.load(Path("beliefs.json"))

# Or configure on init
session = AEESession(
    "my-project",
    state_file=Path(".epistemic/beliefs.json"),
)
session.load()
# ... work ...
session.save()
```

### Trace Vault

```python
session = AEESession(
    "my-project",
    trace_dir=Path(".epistemic"),   # enables sealing
)

# Seal a decision
session.seal("decision", "Adopted microservices architecture")

# Seal an audit result
session.seal("audit-gate", "Phase 1 epistemic audit passed",
             artifact_ids=["REQ-001", "REQ-002"])

# Verify chain integrity
valid, errors = session.verify_trace()
if not valid:
    print(f"Chain violation: {errors}")
```

## Low-Level API

For fine-grained control, use the individual components directly.

### BeliefArtifact

```python
from epistemic import BeliefArtifact, BeliefStatus, ConfidenceLevel

artifact = BeliefArtifact(
    artifact_id="HYP-001",
    propositions=["Claim A", "Claim B"],
    epistemic_boundary=["Corpus: X", "Period: Y"],
    inferential_links=["HYP-000"],   # this depends on HYP-000
    confidence=ConfidenceLevel.LOW,
    status=BeliefStatus.ACCEPTED,
    domain="linguistics",
)

artifact.add_evidence("Rao et al. 2009")
artifact.is_accepted        # True
artifact.has_failures       # False (until stress-tested)
artifact.unresolved_failures  # []
```

### StressTester

```python
from epistemic import StressTester, StressTestResult

tester = StressTester(
    req_path=Path("docs/REQUIREMENTS.md"),  # for test coverage detection
    test_path=Path("docs/TESTS.md"),
)
result: StressTestResult = tester.run(artifacts)

result.equilibrium          # True if no critical failures
result.total_failures       # int
result.critical_count       # int
result.logic_knots          # [(id1, id2, reason), ...]
result.has_logic_knots      # bool
```

### CertaintyEngine

```python
from epistemic import CertaintyEngine, CertaintyReport

engine = CertaintyEngine(threshold=0.7)
report: CertaintyReport = engine.run(
    artifacts,
    covered_reqs={"REQ-001", "REQ-002"},  # IDs with test/experiment coverage
)

report.overall_score                # 0.0-1.0
report.below_threshold              # [artifact_ids]
report.component_averages           # {"CLI": 0.8, "API": 0.4, ...}
report.scores                       # [ArtifactCertainty, ...]
print(report.format_text())
```

### FailureModeGraph

```python
from epistemic import FailureModeGraph

graph = FailureModeGraph()
graph.build(artifacts, stress_result)

graph.equilibrium_check()           # bool
graph.logic_knot_detect()           # [(id1, id2, reason), ...]
graph.nodes_with_failures()         # [GraphNode, ...]
graph.summary_stats()               # {"total_nodes": N, ...}
print(graph.render_text(all_failure_modes=all_fms))
print(graph.render_mermaid())
```

### RecoveryOperator

```python
from epistemic import RecoveryOperator, RecoveryProposal

operator = RecoveryOperator()
proposals: list[RecoveryProposal] = operator.propose(artifacts, stress_result)

for p in proposals:
    print(f"[{p.strategy.value}] {p.artifact_id}: {p.description}")
    print(f"  Change: {p.suggested_change}")

print(operator.format_proposals(proposals))
```

### TraceVault (direct use)

```python
from epistemic.trace import TraceVault, SealType, SealRecord
from pathlib import Path

vault = TraceVault(Path(".epistemic"))
seal: SealRecord = vault.seal(
    seal_type=SealType.DECISION,
    description="Adopted event sourcing",
    artifact_ids=["DEC-001"],
)
print(f"Sealed: {seal.seal_id} — {seal.entry_hash[:16]}...")

valid, errors = vault.verify()
print(vault.format_log(limit=10))
```

## Integration Examples

### glossa-lab (Linguistics Research)

```python
from epistemic import AEESession, ConfidenceLevel, BeliefStatus
from pathlib import Path

session = AEESession(
    "glossa-lab-indus",
    threshold=0.65,
    state_file=Path(".epistemic/indus.json"),
    trace_dir=Path(".epistemic"),
)
session.load()

session.add_belief(
    artifact_id="HYP-IND-001",
    propositions=["The Indus script is logosyllabic"],
    epistemic_boundary=["Mahadevan corpus, 2977 inscriptions, 1977"],
    domain="epigraphy",
    status=BeliefStatus.ACCEPTED,
    confidence=ConfidenceLevel.LOW,
)

session.add_evidence("HYP-IND-001", "Rao et al. 2009 — conditional entropy")
session.mark_covered("HYP-IND-001")

result = session.run()
for id1, id2, reason in result.stress_result.logic_knots:
    print(f"Theory conflict: {id1} ↔ {id2}")

session.seal("stress-test", "Indus hypothesis stress-test v2")
session.save()
```

### Compliance Pipeline

```python
from epistemic import AEESession, BeliefStatus

session = AEESession("gdpr-compliance", threshold=0.8)

session.add_belief(
    artifact_id="COMP-GDPR-001",
    propositions=["Personal data is encrypted at rest"],
    epistemic_boundary=["EU users only", "PostgreSQL storage layer"],
    priority="P1",
    status=BeliefStatus.ACCEPTED,
)

session.add_evidence("COMP-GDPR-001", "Security audit Q4 2025")
session.mark_covered("COMP-GDPR-001")

result = session.run()
if not result.is_healthy():
    print(f"Compliance gaps: {result.certainty_report.below_threshold}")
```

### FastAPI Integration (epistemic middleware pattern)

```python
from epistemic import AEESession
from pathlib import Path

# Load session at app startup
epistemic_session = AEESession(
    "my-api",
    state_file=Path(".epistemic/api-beliefs.json"),
)
epistemic_session.load()

# In your route handlers, assert epistemic status
@app.get("/api/health")
async def health():
    result = epistemic_session.run(accepted_only=True)
    return {
        "epistemic_equilibrium": result.stress_result.equilibrium,
        "certainty": result.certainty_report.overall_score,
        "logic_knots": len(result.stress_result.logic_knots),
    }
```
