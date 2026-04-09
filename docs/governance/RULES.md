# Hard Rules and Stop Conditions

## Hard Rules

These rules are non-negotiable. Violation of any hard rule is a stop condition.

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
