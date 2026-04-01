# Ledger — specsmith

## Session 2026-04-01 — Initial CLI implementation

**Status:** Complete
**Scope:** Full CLI tool with 5 commands, 4 agent adapters, CI/CD, tests

### Proposal
Build specsmith CLI tool with: init (scaffold generation), audit (health checks),
validate (consistency), compress (ledger archival), upgrade (spec version migration).
Add agent integration adapters for Warp, Claude Code, Cursor, and Copilot.

Estimated cost: high

### Changes
- `src/specsmith/cli.py` — click CLI with init, audit, validate, compress, upgrade
- `src/specsmith/scaffolder.py` — Jinja2 template renderer with project type logic
- `src/specsmith/config.py` — pydantic ProjectConfig with 8 project types
- `src/specsmith/auditor.py` — governance file checks, REQ↔TEST coverage, ledger health
- `src/specsmith/validator.py` — scaffold.yml, AGENTS.md refs, REQ uniqueness
- `src/specsmith/compressor.py` — ledger archival with configurable thresholds
- `src/specsmith/upgrader.py` — governance template re-rendering on version bump
- `src/specsmith/integrations/` — base adapter + Warp, Claude Code, Cursor, Copilot
- `src/specsmith/templates/` — 30+ Jinja2 templates for governed scaffolds
- `.github/workflows/ci.yml` — lint + typecheck + test matrix + security audit
- `.github/workflows/release.yml` — tag-triggered build → GitHub Release
- `docs/REQUIREMENTS.md` — 37 formal requirements
- `docs/TEST_SPEC.md` — 30 test specifications

### Verification
- 36 tests passing (pytest)
- ruff lint: clean
- ruff format: clean
- mypy strict: clean
- CI: lint ✓, security ✓, typecheck pending (fix pushed)

### Open TODOs
- [ ] Add VCS platform integrations (GitHub/GitLab/Bitbucket CLI)
- [ ] Add Gemini, Windsurf, Aider agent adapters
- [ ] Expand CLI runner test coverage
- [ ] Self-host governance (this file)
