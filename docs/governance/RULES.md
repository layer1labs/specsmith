# Hard Rules and Stop Conditions

## Hard Rules

These rules are non-negotiable. Violation of any hard rule is a stop condition.

> **Research basis for H15–H22:** Rules H15 through H22 were derived from and
> empirically validated by the study *"Ontology-Epistemic-Agentic (OEA) Recursive
> Generative Stability: A Unified Framework for Preventing Hallucination and Drift in
> Large Language Models"* (BitConcepts Research, 2026). The OEA framework validated
> that calibration direction, epistemic scope bounding, retrieval filtering, and
> recursion guard controls are the primary levers for suppressing hallucination and
> semantic drift in production AI systems. specsmith encodes these findings as
> enforceable governance rules rather than aspirational guidelines.

### H1 — Ledger required
No ledger entry = work not done.

### H2 — Proposal required
No proposal = no execution.

### H3 — Cross-platform awareness
All work must consider every target platform (Windows, Linux, macOS). If a platform is unsupported or deferred, that must be stated explicitly.

### H4 — Environment isolation
No system-dependent assumptions. Virtual environments required. No reliance on global interpreters or system packages.

### H5 — Explicit startup
No hidden service logic. All startup behavior must be documented and inspectable.

### H6 — No silent scope expansion
If the task grows beyond the proposal, stop and re-propose.

### H7 — No undocumented state changes
Every file creation, modification, or deletion must be traceable to a proposal and recorded in the ledger.

### H8 — Documentation is implementation
Architecture-affecting changes MUST update relevant docs in the same work cycle.

### H9 — Execution timeout required
All agent-invoked commands MUST have a timeout. No command may run indefinitely. If a command hangs, it must be killed, recorded in the ledger, and escalated after one retry.

### H10 — No hardcoded versions
Version strings MUST NOT be hardcoded in documentation, tests, or source code outside of `pyproject.toml`. Use `importlib.metadata.version()` at runtime. Use `{{ version }}` placeholders in documentation resolved at build time.

### H11 — No unbounded loops or blocking I/O without a deadline
Every loop or blocking wait in agent-written scripts and automation MUST have:

- An explicit deadline or iteration cap (e.g. a `deadline` timestamp, a `max_attempts` counter, or a `timeout` parameter).
- A fallback exit path that executes when the deadline is reached.
- A diagnostic message emitted if the timeout fires (self-diagnosing failures).

Examples of violating patterns: `while True:` / `while ($true)` / `for (;;)` with no deadline guard; serial-port or I/O polling loops with no deadline; `sleep` inside a loop with no termination condition. `specsmith validate` checks scripts under `scripts/` for these patterns.

### H12 — Windows multi-step automation via .cmd files
On Windows, multi-step or heavily-quoted automation sequences MUST be written to a temporary `.cmd` file and executed from there. Do NOT emit these as inline shell invocations or as `.ps1` files unless there is a concrete PowerShell-only requirement. Inline multi-line quoting on Windows is fragile and causes avoidable hangs.

### H13 — Epistemic Boundaries Required
All proposals MUST state their epistemic boundaries. A proposal without explicit assumptions is a stop condition, not a warning. Before executing, ask:
- What BeliefArtifact IDs does this proposal rely on?
- What are the hidden assumptions?
- What adversarial challenge could break this proposal?
- Are any P1 requirements in scope and at LOW confidence?

Hidden assumptions are not acceptable. Declare all epistemic boundaries in the `Assumptions:` field of every proposal.

### H14 — Documentation Freshness Required
Whenever a user-facing command, CLI option, or behaviour is added, changed, or removed, the
agent MUST update the relevant documentation in the **same work cycle** — not in a follow-up:

- **README.md** — if the change affects user-visible CLI behaviour, quick-start examples,
  or the feature list
- **docs/site/** pages — specifically `commands.md` when any command is added or changed;
  `governance.md` / `configuration.md` when governance model changes
- **CHANGELOG.md** — always, for any user-facing change, following Keep a Changelog format

This rule exists because you, the agent, are the only one maintaining these files.
The human operator will never need to read a README file or touch RTD pages — specsmith
must keep them current automatically. Failure to update documentation is a H7 violation
(undocumented state change) and a stop condition.

---

## Anti-Hallucination and Epistemic Stability Rules (H15–H22)

These rules implement the **OEA Recursive Generative Stability** framework. They address
the root causes of hallucination and semantic drift that the OEA study identified across
multiple LLM families: uncalibrated confidence, unbounded generation recursion, unfiltered
retrieval injection, and implicit model assumptions leaking into agent outputs.

See also: `docs/governance/EPISTEMIC-AXIOMS.md` and `docs/ARCHITECTURE.md §OEA Layer`.

### H15 — Epistemic Scope Bounding
The agent MUST NOT make factual claims outside its verified knowledge domain.
When asked about something outside its scope, it MUST respond with an explicit
acknowledgement of uncertainty ("I don't know", "I cannot verify this") rather than
producing a plausible-sounding but unverified answer.

Violating patterns: stating version numbers, dates, or API details not present in the
current context; extending extrapolated trends as factual assertions; treating training
data as live ground truth.

`specsmith epistemic-audit` checks for accepted requirements that lack observable evidence,
which is the structural proxy for out-of-scope claims in governance artifacts.

### H16 — Anti-Drift Recursion Guard
Multi-step generation chains MUST have a finite iteration limit. No agent output may
become the sole input to a subsequent generation step without a human checkpoint or a
structured validation gate between steps.

- Maximum chain depth: 5 autonomous generation steps before a human review point.
- Recursive self-refinement loops ("improve this output → feed back into the same model")
  are only permitted when gated by a confidence score above the project threshold.
- Unbound recursion is a stop condition; record in LEDGER.md and escalate.

Rationale: the OEA study showed that recursive generation without external anchoring
produces exponentially diverging semantic drift, even in high-accuracy models.

### H17 — Calibration Direction
Agent outputs MUST express uncertainty proportional to evidence quality. False confidence
is a harder failure than acknowledged uncertainty.

- If confidence in a claim is below MEDIUM, the output MUST include a hedging phrase.
- Confidence tokens (`MUST`, `SHOULD`, `MAY`, `PROBABLY`) map to AEE confidence levels
  and MUST be used consistently with their RFC 2119 meanings.
- An output with HIGH confidence and insufficient evidence is a stop condition.
- `specsmith preflight` enforces this by injecting an escalation flag when
  `confidence < escalate_threshold`.

### H18 — RAG Retrieval Filtering
Any context retrieved from external sources (vector search, database lookup, web search,
file read) MUST pass relevance validation before being included in an agent prompt.

- Chunks with cosine similarity < 0.6 (or equivalent relevance score) MUST be discarded.
- Retrieved content MUST be tagged with its source, timestamp, and confidence tier.
- Including unvalidated retrieved content in a governed prompt is a stop condition.

Rationale: the OEA study found that low-relevance retrieval is a primary hallucination
trigger — models fill the incoherence gap between query and retrieved context by
fabricating connecting content.

### H19 — Synthetic Contamination Prevention
Synthetically generated data MUST NOT be silently mixed with real ground-truth data in
evaluation, fine-tuning, or benchmark pipelines.

- Every dataset entry MUST carry a `source_type` tag: `real | synthetic | augmented`.
- Evaluation metrics MUST be reported separately for real and synthetic subsets.
- CI pipelines that combine both without explicit separation are a stop condition.
- `specsmith validate --strict` checks that eval YAML files declare `source_type`.

### H20 — Falsifiability Required
All factual claims made by an agent in governance artifacts MUST either cite a verifiable
source or be explicitly flagged as unverified hypotheses.

- **Verifiable source**: a URL, file path + line range, test ID, or external publication.
- **Unverified hypothesis**: prefixed with `[HYPOTHESIS]` or placed in an
  `## Assumptions` block with explicit justification for why verification was deferred.
- Unflagged factual claims without sources are a H7 violation (undocumented state change).

### H21 — No Undisclosed Model Assumptions
Any model-specific behaviour that an agent or proposal relies on MUST be explicitly stated.

Required disclosures when relevant:
- Context window size and the fill headroom available for this task
- Instruction format expected (plain, sections, XML, chat roles)
- Whether the model supports tool calls / structured output
- Temperature and sampling settings used
- Provider and model version (captured in every `ai_disclosure` block)

Failing to disclose these is a stop condition when the behaviour would affect correctness
or reproducibility of the output.

### H22 — Cross-Platform CI Enforcement
CI pipelines MUST run on Linux (or macOS) AND Windows. A green result on one platform
does NOT constitute cross-platform coverage.

- `.github/workflows/ci.yml` MUST include at least one `ubuntu-latest` or `macos-latest`
  runner AND at least one `windows-latest` runner for any non-trivial project.
- Platform-specific failures on one runner MUST block the PR even if the other runner passes.
- Automation scripts MUST use the platform-appropriate shell (sh/bash on Unix;
  `.cmd` / `.ps1` on Windows) per H12.
- `specsmith validate --strict` checks for the presence of a `.github/workflows/*.yml`
  file and emits a warning (H22) when none is found.

---

## Governance Invariants for ESDB and Context Management

These invariants complement the hard rules above and enforce robustness guarantees for
data persistence and context integrity.

**I-ESDB-1:** ESDB MUST be per-project. Shared or global ESDB instances are not permitted.

**I-ESDB-2:** Optimization (compression, eviction, summarization) MUST NEVER delete records
from the WAL. It affects only the in-context representation. The WAL is append-only.

**I-SES-1:** Session state (context, conversation history) MUST survive a restart. Any
work that was in progress MUST be resumable from the last saved state.

**I-CTX-1:** Context window MUST auto-optimize before reaching the hard ceiling. Tier 1
optimization fires at 60%, Tier 2 at 80%, Tier 3 (emergency) at 85%. The ceiling MUST
never be breached without triggering emergency compression first.

**I-CI-1:** CI automation state MUST be recorded in `.specsmith/config.yml` so it
survives session restarts and is reproducible across machines.

---

## Stop Conditions

Agents MUST stop and request clarification if ANY of the following are true:

- Missing inputs (files, context, or dependencies not available)
- Unclear state (ledger is inconsistent or missing)
- Undocumented platform assumptions
- No proposal has been approved
- No ledger path exists (LEDGER.md missing or unwritable)
- Requirement-without-test detected
- Test-without-requirement detected
- Architecture contradicts requirements
- Proposed work would violate a hard rule
- Proposed work would silently expand scope
- **Logic Knot detected** (conflicting accepted requirements without a resolution path)
- **P1 belief artifact below MEDIUM confidence** (H13 stop condition)
- **Trace chain integrity failure** (run `specsmith trace verify`)
