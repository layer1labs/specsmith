# specsmith Architect — Epistemic BA Interview Skill

## Purpose
This skill enables an AI agent to conduct or assist with specsmith's epistemic BA interview flow,
producing ARCHITECTURE.md, proposed REQs, and gap analysis reports grounded in real project knowledge.

## When to Use
- A user is starting a new project and needs to capture architecture before writing requirements.
- A user's ARCHITECTURE.md is out of date and needs to be refreshed.
- You need to produce proposed REQs from an architectural discussion.
- A user wants to understand what changed since the last architecture snapshot.

## Commands Reference

```bash
# Start a new BA interview (interactive — asks 9 epistemic questions)
specsmith architect interview --project-dir .

# Run in CI/non-interactive mode (auto-generates synthetic answers)
specsmith architect interview --project-dir . --non-interactive

# Save current ARCHITECTURE.md as a snapshot baseline
specsmith architect gap --project-dir . --save

# Compare current architecture vs snapshot; surface stale REQs + new gaps
specsmith architect gap --project-dir .

# Update architecture with targeted re-interview for low-confidence dimensions
specsmith architect update --project-dir . --non-interactive
```

## Interview Dimensions (9 total)
The interview tracks 9 epistemic dimensions:

| Dimension | Question |
|---|---|
| problem_domain | What problem does this system solve? |
| user_types | Who are the users or personas? |
| key_integrations | What external systems/APIs/data sources? |
| technical_constraints | Platform, language, budget, license? |
| deployment_target | Where will this system be deployed? |
| scale_expectations | Users, TPS, latency SLA? |
| data_model | Primary entities and persistence? |
| security_model | Auth, encryption, compliance? |
| failure_modes | What must never fail; acceptable degradation? |

## Confidence Rubric
Each answer is scored using this rubric:
- Empty/whitespace → +0.05
- 1–15 chars (vague) → +0.10
- 16–60 chars (general) → +0.25
- 61–200 chars (specific) → +0.40
- 200+ chars OR metrics/constraints keywords → +0.50

The interview terminates when ALL dimensions reach ≥ 0.75 confidence, or the user types `done`.

## Outputs

### `specsmith architect interview` produces:
- `docs/ARCHITECTURE.md` — per-section confidence annotations in HTML comments
- `docs/requirements/proposed.yml` — draft REQs (status: proposed, confidence from architecture)
- `.specsmith/arch-interview.json` — crash-safe session state (resume on interruption)

### `specsmith architect gap` produces:
- `docs/requirements/arch-gap.yml` — new REQs for added sections, stale markers for removed ones
- `docs/tests/arch-gap.yml` — proposed test stubs for new REQs

## Epistemic Principles
- **Maximum-uncertainty-first**: always ask about the lowest-confidence dimension next.
- **Crash-safe**: interview state is persisted after every answer.
- **Non-interactive safe**: when stdin is not a TTY or `SPECSMITH_AGENT=1`, synthetic answers
  are auto-generated so the command never blocks CI pipelines.
- **Confidence is visible**: every section in ARCHITECTURE.md has an inline confidence score.

## Agent Guidance
When conducting an interview on behalf of a user:
1. Run `specsmith architect interview --project-dir .` (interactive) to let the user answer.
2. If the user wants you to pre-fill answers: run `--non-interactive`, then edit the generated
   ARCHITECTURE.md to replace synthetic answers with real ones, then run `specsmith sync`.
3. After interview, always run `specsmith audit` to confirm governance health.
4. If architecture changed: run `specsmith architect gap` to surface REQ updates needed.
