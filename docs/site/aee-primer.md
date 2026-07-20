# Applied Epistemic Engineering — Complete Primer

This primer takes you from zero knowledge of AEE to being fully productive with specsmith's
epistemic layer. It covers the theory, the formal machinery, the practical workflow, and
real-world examples across multiple domains.

---

## Part 1: What Is Applied Epistemic Engineering?

### The Core Insight

Most software projects treat requirements, decisions, and assumptions as static documents.
They are written, reviewed once, and then slowly become out of date as reality diverges.
AEE treats them as **living knowledge artifacts** — subject to the same engineering
discipline as code: version control, testing, stress-testing, and refactoring.

**The key claim of AEE**: belief systems can be engineered. A claim about what a system
must do is a belief. That belief can be:

- **Codable** — expressed as a structured artifact with explicit propositions
- **Testable** — challenged by adversarial functions that expose failure modes
- **Deployable** — verified, reconstructed, and sealed with cryptographic proof

This is not philosophy. It is engineering discipline applied to epistemology.

### Why This Matters for AI Development

AI agents produce knowledge claims constantly: "This requirement is satisfied," "This
architecture is correct," "This test passes." Without a framework to assess the epistemic
quality of these claims, you cannot know:

- Whether a requirement is vague, compound, or untestable
- Whether two requirements contradict each other (a Logic Knot)
- Whether a critical requirement has any experimental or test coverage
- Whether a decision was made with explicit awareness of its assumptions

AEE provides that framework. When you run `specsmith audit`, you are running
a formal epistemic quality check on everything the project claims to know.

---

## Part 2: The Formal Foundation

### The Five Axioms

AEE is built on five foundational axioms. Every operation in specsmith's epistemic layer
is grounded in one or more of these axioms.

**Axiom 1: Observability**
Every belief must be inspectable. Hidden assumptions are a stop condition. A claim that
cannot be fully stated and examined is not an engineering artifact — it is a liability.

In practice: every `BeliefArtifact` must have an explicit `epistemic_boundary` field
declaring the assumptions and context within which its propositions hold. If the boundary
is missing, the `StressTester` flags a violation.

**Axiom 2: Falsifiability**
Every belief must be challengeable. A claim that cannot be falsified is not knowledge —
it is dogma. This is Karl Popper's criterion of demarcation, applied to engineering artifacts.

In practice: every accepted `BeliefArtifact` must have at least one test that could
potentially disprove it. If no test exists, `StressTester` flags it as a Falsifiability
violation. The missing test is added to the failure-mode graph and a recovery proposal is
generated.

**Axiom 3: Irreducibility**
Beliefs must be decomposed to their primitive propositions. A compound claim — one that
bundles multiple independently falsifiable sub-claims into a single artifact — often hides
Logic Knots (contradictions between its components). Decompose aggressively.

In practice: `StressTester` flags artifacts with more than 3 propositions or with
compound claim patterns (multiple "and" clauses joining large subjects). Recovery
proposals suggest splitting the artifact.

**Axiom 4: Reconstructability**
Every failed belief can be reconstructed into a new belief that satisfies Axioms 1 and 2.
Recovery is always possible — but it may require narrowing the scope. A claim that cannot
be reconstructed under any scope simply cannot be made under AEE.

In practice: `RecoveryOperator` generates bounded recovery proposals for every failure mode.
These proposals are always subject to human approval — the agent cannot reconstruct a belief
autonomously (Hard Rule H2 applies at the epistemic level too).

**Axiom 5: Convergence**
Systematic application of the Stress-Test operator (S) and Recovery operator (R) always
converges to an Equilibrium Point E where S(G) yields no new failure modes.

In practice: `FailureModeGraph.equilibrium_check()` returns True when the system has
reached E. You can confirm this with `specsmith audit`.

### The Key Operators

**S — Stress-Test Operator**
S(B) takes a `BeliefArtifact` B and applies a suite of adversarial challenge functions.
Each challenge attempts to find a breakpoint: a condition under which the belief fails.
The output is a set of `FailureMode` records added to the `FailureModeGraph` G.

**R — Recovery Operator**
R(K) takes a Logic Knot K (or a set of failure modes) and proposes the minimal primitive
modifications needed to resolve it. R never applies changes autonomously — it emits
`RecoveryProposal` objects that require human approval.

**G — Failure-Mode Graph**
G maps stress-test → breakpoint relations. Each node is a `BeliefArtifact`. Each edge
represents a dependency ("artifact A relies on artifact B"). Logic Knots are marked as
bidirectional edges indicating irreducible conflict.

**E — Equilibrium Point**
E is the state where S(G) yields no new failure modes: no unresolved critical failures,
no Logic Knots, all P1 artifacts at MEDIUM confidence or above.

**C — Certainty Score**
C ∈ [0, 1] is computed by `CertaintyEngine` using:

```
C = base_score × coverage_weight × freshness_weight
```

Where:
- `base_score` = ConfidenceLevel.score (UNKNOWN=0.0, LOW=0.25, MEDIUM=0.55, HIGH=0.85)
- `coverage_weight` = 1.0 if test-covered, 0.4 if propositions exist but uncovered, 0.0 if empty
- `freshness_weight` = 1.0 reduced by 0.2 per CRITICAL failure, 0.6 per HIGH, 0.85 per MEDIUM

Confidence propagates through inferential links via the **weakest-link rule**:
if A depends on B (A → B), then A's certainty cannot exceed B's certainty.

---

## Part 3: The Four-Step Core Method

AEE's core method is a feedback loop:

### Frame
Identify and record the claim. What exactly are you asserting? Frame it as a `BeliefArtifact`
with:
- A unique ID (e.g., REQ-CLI-001, HYP-IND-001, DEC-001)
- One or more propositions (atomic, independently falsifiable claims)
- An epistemic boundary (the assumptions/context within which the propositions hold)
- The confidence level (initially UNKNOWN, elevated as evidence accumulates)

### Disassemble
Decompose the claim to its primitive components. Ask:
- What are the sub-claims?
- What are the assumptions that make this claim possible?
- What would have to be true in the world for this claim to be true?
- Are any of these assumptions hidden?

This is where compound claims get split. A requirement that says "The system shall process
requests and validate inputs and return responses" is three claims. Split it.

### Stress-Test
Apply adversarial challenge functions. The `StressTester` does this automatically, but
you can also do it manually: for each proposition, ask "What if the opposite were true?"
"What boundary condition breaks this?" "What would make this falsifiable but currently not?"

The stress-test produces:
- `FailureMode` records (challenge → breakpoint pairs)
- Logic Knots (contradictions between accepted beliefs)
- A `StressTestResult` with `equilibrium: bool`

### Reconstruct
Apply recovery actions to restore equilibrium. For each failure mode:
- VAGUENESS → Quantify: replace imprecise language with measurable criteria
- MISSING TEST → Falsify: add a test that can disprove the claim
- MISSING BOUNDARY → Constrain: declare the scope within which the claim holds
- COMPOUND CLAIM → Decompose: split into independent primitives
- LOGIC KNOT → Resolve: narrow one belief's scope, supersede, or decompose both

After reconstruction, run the stress-test again. Repeat until S(G) yields no new failures.

---

## Part 4: Belief Artifacts in Detail

### The BeliefArtifact Data Model

```python
@dataclass
class BeliefArtifact:
    artifact_id: str              # e.g., "REQ-CLI-001", "HYP-IND-001"
    propositions: list[str]       # atomic, independently falsifiable claims
    epistemic_boundary: list[str] # assumptions/context (the Δ in AEE notation)
    inferential_links: list[str]  # IDs of beliefs this depends on (A → B)
    confidence: ConfidenceLevel   # UNKNOWN / LOW / MEDIUM / HIGH
    status: BeliefStatus          # draft / accepted / stress-tested / reconstructed
    failure_modes: list[FailureMode]  # populated by StressTester
    domain: str                   # e.g., "linguistics", "software", "policy"
    evidence: list[str]           # citations that support this belief
```

### Confidence Levels

| Level | Score | Meaning |
|-------|-------|---------|
| UNKNOWN | 0.0 | New claim, no evidence, not stress-tested |
| LOW | 0.25 | Asserted but not challenged or covered by tests |
| MEDIUM | 0.55 | Stress-tested with minor failures resolved |
| HIGH | 0.85 | Stress-tested, equilibrium reached, evidence present |

### Status Lifecycle

```
DRAFT → ACCEPTED → STRESS_TESTED → RECONSTRUCTED
                                         ↓
                                     DEPRECATED
```

A belief is `ACCEPTED` when the human operator has reviewed and accepted it.
A belief is `STRESS_TESTED` after the StressTester has run and failures have been resolved.
A belief is `RECONSTRUCTED` after it has been rebuilt following a major failure mode.
A belief is `DEPRECATED` when superseded; it is kept for audit trail purposes — never deleted.

### Parsing from REQUIREMENTS.md

specsmith's REQUIREMENTS.md format is designed to be directly parseable as BeliefArtifacts:

```markdown
### REQ-CLI-001 — specsmith init scaffolds a governed project

- **Description**: `specsmith init` generates a complete project scaffold from
  interactive prompts or YAML config, including governance files, CI/CD, and
  agent integration files.
- **Priority**: P1
- **Platform**: all
- **Status**: accepted
- **Test**: TEST-CLI-002
```

Run `specsmith req list` to inspect governed requirements and their identities.

---

## Part 5: Logic Knots

A Logic Knot is an irreducible conflict between two accepted beliefs. It is the AEE
equivalent of a type error: the belief system is internally inconsistent and cannot
proceed until the knot is resolved.

### Detection

The `StressTester._detect_logic_knots()` method uses two heuristics:

1. **Duplicate IDs**: Two accepted beliefs with the same ID
2. **MUST/MUST NOT conflict**: Two accepted beliefs in the same component where one
   uses MUST and the other uses MUST NOT for the same set of subjects

Example of a Logic Knot:
```
REQ-AUTH-001: "The system MUST accept anonymous requests"
REQ-AUTH-002: "The system MUST NOT process unauthenticated requests"
```

These use the same subjects (system, requests, unauthenticated/anonymous) with
contradictory modal operators. This is a Logic Knot.

### Resolution

`RecoveryOperator` generates a `RecoveryProposal` with strategy `RESOLVE`:

Options for resolution:
1. **Narrow the boundary**: REQ-AUTH-001 applies to the public API tier; REQ-AUTH-002
   applies to the admin tier. Different epistemic boundaries → no conflict.
2. **Supersede one**: REQ-AUTH-001 is deprecated; REQ-AUTH-003 replaces it with
   explicit scope.
3. **Decompose both**: Split into four requirements with independent scopes.

The resolution is always a human decision. The agent cannot resolve Logic Knots autonomously.

---

## Part 6: The Certainty Engine

### How Certainty Flows

The `CertaintyEngine` computes a certainty score C ∈ [0, 1] for each belief artifact
and then propagates it through the dependency graph using the **weakest-link rule**.

Consider:
```
REQ-API-003: "The API returns valid JSON" (C = 0.85)
REQ-API-004: "The pagination is correct" (C = 0.25)
REQ-API-005: "The response is fully correct" — depends on REQ-API-003 and REQ-API-004
```

After weakest-link propagation, REQ-API-005's certainty becomes min(0.85, 0.25) = 0.25,
regardless of how well-tested REQ-API-005 itself is. A chain is only as strong as its
weakest link.

This mirrors real-world epistemic practice: if a critical downstream claim depends on an
uncertain upstream claim, the downstream certainty is bounded by the upstream.

### Interpreting the Report

```
Certainty Report
==================================================
Overall score:  0.42 (below threshold 0.70)
Artifacts:      47
Below threshold: 23

By component:
  ✗ CLI          0.38
  ✓ AEE          0.71
  ✗ TRC          0.28
  ✗ ORCH         0.15

Artifacts below threshold:
  ✗ REQ-TRC-001              score=0.10  [LOW]
     No propositions → coverage weight 0.0
  ✗ REQ-ORCH-001             score=0.22  [LOW]
     No test/experiment coverage → coverage weight 0.4
```

A score above the threshold (default 0.7) means the belief is sufficiently well-founded
for the current stage. Below threshold does not mean the belief is wrong — it means the
belief needs more evidence, tests, or stress-testing before it should be relied upon.

---

## Part 7: The Trace Vault

The `TraceVault` provides cryptographic proof of "what was decided, when, and in what
sequence." It is directly inspired by:

- **Sovereign Trace Protocol (STP)** from VERITAS (AionSystem) — the concept of
  permanently sealed epistemic records with tamper-evident hashing
- **BLAKE3 audit chain** from the Auto-Revision Epistemic Engine (ARE) — append-only
  cryptographic chains where each entry references its predecessor

specsmith uses SHA-256 (stdlib, zero dependencies) instead of BLAKE3, but the
structure is identical.

### How It Works

Each `SealRecord` contains:
- `seal_id` — sequential ID (SEAL-0001, SEAL-0002, ...)
- `seal_type` — decision, milestone, audit-gate, logic-knot, stress-test, epistemic
- `description` — human-readable description of what is being sealed
- `content_hash` — SHA-256 of (seal_id + type + description + timestamp)
- `prev_hash` — SHA-256 of the previous SealRecord's `entry_hash`
- `entry_hash` — SHA-256 of (content_hash + prev_hash)

The chain is tamper-evident: modifying any record changes its `entry_hash`, which invalidates
all subsequent records' `prev_hash` references. Verification is O(n) in the number of seals.

### When to Seal

| Event | Seal type |
|-------|-----------|
| Technology decision made | decision |
| Project milestone reached | milestone |
| Epistemic audit passed | audit-gate |
| Logic Knot detected | logic-knot |
| Stress-test run complete | stress-test |
| Any significant epistemic state change | epistemic |

Important decisions become durable evidence when requirements, tests, and work
items are synchronized. Run `specsmith audit` to verify the complete evidence
chain and `specsmith checkpoint` to emit a compact continuity anchor.

---

## Part 8: Practical Workflow

### The AEE Development Loop

1. **Write requirements** in `docs/requirements/*.yml`.
2. **Register tests** in `docs/tests/*.yml` and link every requirement.
3. **Preflight** the intended change before editing.
4. **Implement and run** the repository's native test suite.
5. **Verify** the work item and synchronize governance state.
6. **Audit** the evidence chain and emit a checkpoint.
7. Commit with the repository's native Git tooling.

### Integration with CI/CD

Add to your CI pipeline:
```yaml
- name: Specsmith governance audit
  run: specsmith audit --strict
```

This will fail the build if the belief system falls below 60% overall certainty.
Adjust the threshold based on your project's maturity and risk tolerance.

### Model Routing for AEE Tasks

From ECC's model routing guidance, adapted for AEE:

| Task | Recommended tier |
|------|-----------------|
| Adding new requirements | fast (haiku, gpt-4o-mini) |
| Running stress-test | balanced (sonnet, gpt-4o) |
| Resolving Logic Knots | powerful (opus, o3) |
| Reviewing epistemic audit report | balanced |
| Making technology decisions | powerful |
| Routine ledger entries | fast |

Use `specsmith run --tier fast` for routine tasks, `--tier powerful` for architectural
decisions or Logic Knot resolution.

---

## Part 9: Domain Examples

### Software Engineering

Requirements become BeliefArtifacts. Tests are the falsification mechanism. Audits are
the stress-test cycle. This is the primary use case specsmith was built for.

### Linguistics Research (glossa-lab)

```python
from epistemic import AEESession

session = AEESession("glossa-lab-indus", threshold=0.65)

# Competing decipherment theories as BeliefArtifacts
session.add_belief(
    artifact_id="HYP-IND-001",
    propositions=["The Indus script is logosyllabic"],
    epistemic_boundary=["Mahadevan corpus, 2977 inscriptions, 1977 edition"],
    domain="epigraphy", status=BeliefStatus.ACCEPTED,
)
session.add_belief(
    artifact_id="HYP-IND-002",
    propositions=["Indus script encodes a Dravidian language"],
    epistemic_boundary=["Mahadevan corpus + Parpola linguistic analysis"],
    inferential_links=["HYP-IND-001"],  # depends on logosyllabic hypothesis
    domain="epigraphy", status=BeliefStatus.ACCEPTED,
)

# Evidence from experiments
session.add_evidence("HYP-IND-001", "Rao et al. 2009 — conditional entropy study")
session.mark_covered("HYP-IND-001")

result = session.run()
print(result.summary())

# Resolve competing theory conflicts
for id1, id2, reason in result.stress_result.logic_knots:
    print(f"Theory conflict: {id1} ↔ {id2}")
```

### Patent Prosecution

Patent claims are BeliefArtifacts. Prior art challenges are stress-tests. Independent
claims must be self-contained (no dangling inferential links). The trace vault provides
cryptographic proof of when each claim was first formulated.

### AI Alignment

Model assumptions are BeliefArtifacts. Red-teaming is stress-testing. Hallucination is
a confidence failure (P1 requirement with LOW confidence). The certainty engine tracks
how model capability claims propagate to downstream behavioral claims.

### Compliance

Regulatory requirements are BeliefArtifacts. Audit findings are failure modes. Conflicting
regulations across jurisdictions are Logic Knots. The trace vault provides legally defensible
evidence of when compliance decisions were made.

---

## Part 10: References

The theoretical foundations of AEE draw from multiple fields:

**Primary AEE reference**
- Applied Epistemic Engineering: https://appliedepistemicengineering.com/
  Defines the four-step method, formal primitives, key operators, and five axioms.

**Auto-Revision Epistemic Engine (ARE)**
- https://github.com/organvm-i-theoria/auto-revision-epistemic-engine
  The 8-phase pipeline with human review gates, BLAKE3 audit chain, and ethical axiom
  framework. Inspired specsmith's CryptoAuditChain and TraceVault design.

**VERITAS / CERTUS Engine**
- https://github.com/AionSystem/VERITAS
  Certainty engineering in crisis response. The CERTUS Damage Confidence Index (DCI)
  methodology directly inspired specsmith's CertaintyEngine scoring model.

**AI as Epistemic Technology (Springer)**
- https://doi.org/10.1007/s11948-023-00451-3
  Argues that AI systems are primarily epistemic technologies designed for inquiry and
  knowledge manipulation. Establishes the philosophical foundation for treating AI
  outputs as epistemic artifacts subject to engineering discipline.

**Classic epistemology**
- Karl Popper, *The Logic of Scientific Discovery* (1934) — Falsifiability criterion
- David Hume, *An Enquiry Concerning Human Understanding* (1748) — Inductive skepticism
- Satoshi Nakamoto, Bitcoin whitepaper (2008) — Trustless audit chains (structural inspiration
  for the trace vault's tamper-evidence mechanism)

**Everything Claude Code (ECC)**
- https://github.com/affaan-m/everything-claude-code
  Skills, hooks, subagents, and model routing patterns that inspired specsmith's
  agentic client design.
