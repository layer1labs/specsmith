# Session Protocol — Lifecycle, Proposal Format, and Ledger Format

## Session Types

### NEW SESSION (start)
Load AGENTS.md, governance docs (per load timing), and recent LEDGER.md.
Output: system understanding, ledger state, open TODOs, suggested next task. Then produce a Proposal.

### RESUME SESSION (resume)
Load AGENTS.md and LEDGER.md. Summarize last task, current objective, open TODOs, risks. Propose next bounded task.

### SAVE SESSION (save)
Prepare LEDGER.md entry: what changed, what was verified, what remains, next step. Do not invent results.

### GIT COMMIT (commit)
Prepare commit summary: what changed, why, files touched, checks performed. Generate commit message.

### GIT UPDATE (sync)
Check status, pull changes, summarize, identify conflicts.

### AUDIT (audit)
Run all drift/health checks from drift-metrics.md. Report pass/fail per signal with recommendations.

### Session boundary rules
- A new conversation is a new session, NOT a new project
- All governance rules persist across sessions
- Agents rely on on-disk documents, not past chat messages

---

## Proposal Format

Before any non-trivial work, produce a proposal using exactly this structure:

```
## Proposal

Objective:      <what this task accomplishes>
Scope:          <included and excluded>
Inputs:         <context, files, or state this depends on>
Outputs:        <files, artifacts, or state changes>
Files touched:  <explicit list>
Checks:         <what verification will be performed>
Risks:          <what could go wrong>
Rollback:       <how to undo>
Estimated cost: <low | medium | high>
Decision request: <what the human must approve>
```

Rules:
- No non-trivial work without a proposal
- No execution without human approval
- Proposals must be bounded to one task
- If scope changes during execution, stop and re-propose

---

## Ledger Entry Format

```markdown
## [YYYY-MM-DD] Entry — <short title>

Objective:
What was done:
Files changed:
Checks run:
Results:
Token estimate: <low | medium | high>
Open TODOs:
Risks:
Next step:
```

Rules:
- Entries are append-only
- "What was done" = actual outcomes only
- "Checks run" = actual checks or explicitly "none"
- "Results" = pass/fail/unknown — never claim success without evidence
- "Open TODOs" = complete canonical list. Use `- [ ]` / `- [x]`
- "Next step" = recommended starting point for next session
