# Governance expansion

`specsmith quickstart` now supports a **Lite** governance mode that generates only the minimum set of governance files needed to start work quickly:

- `AGENTS.md`
- `LEDGER.md`
- `docs/REQUIREMENTS.md`
- `docs/TESTS.md`
- `docs/ARCHITECTURE.md`

Use Lite mode when you want low setup overhead while iterating on early project requirements.

## Expanding governance

As project complexity or compliance scope grows, expand governance in-place:

```bash
specsmith expand --to team
specsmith expand --to regulated
```

### `--to team`
Adds team-collaboration governance documents under `docs/governance/`:

- `RULES.md`
- `SESSION-PROTOCOL.md`
- `LIFECYCLE.md`
- `ROLES.md`

### `--to regulated`
Includes all Team files plus additional compliance-oriented governance docs:

- `CONTEXT-BUDGET.md`
- `VERIFICATION.md`
- `DRIFT-METRICS.md`

This lets projects start small and progressively adopt stricter governance controls without re-initializing the repo.
