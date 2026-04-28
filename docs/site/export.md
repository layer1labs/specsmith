# Export & Compliance

`specsmith export` generates a comprehensive compliance report — useful for audits, stakeholder reviews, and tracking governance maturity.

## Usage

```bash
specsmith export --project-dir ./my-project                    # Print to terminal
specsmith export --project-dir ./my-project --output report.md # Save to file
```

## Report Sections

### Project Summary
From `scaffold.yml`: project name, type label, language, VCS platform, spec version.

### Verification Tools
Complete listing of all 7 tool categories from the [Tool Registry](tool-registry.md): lint, typecheck, test, security, build, format, compliance. Shows the exact tool commands configured for this project type.

### Requirements Coverage Matrix
Cross-references `docs/REQUIREMENTS.md` against `docs/TESTS.md`:

- Scans REQUIREMENTS.md for all `REQ-xxx-NNN` IDs
- Scans TESTS.md for `Covers: REQ-xxx-NNN` references
- Reports: **Coverage: 56/74 (76%)**
- Lists every REQ with ✓ (covered) or ✗ (uncovered)

This is the same check `specsmith audit` performs, but in report format.

### Recent Activity
If a `.git` directory exists:
- Last 10 git commits (hash + message)
- Contributor list with commit counts

### Audit Summary
Runs the full `specsmith audit` check suite inline and reports:
- Passed / Failed / Fixable counts
- Overall status (Healthy or Issues found)
- Each individual check result with message

### Governance File Inventory
Lists all expected governance files with ✓ (exists) or ✗ (missing):
AGENTS.md, LEDGER.md, scaffold.yml, docs/REQUIREMENTS.md, docs/TESTS.md, docs/architecture.md, docs/governance/rules.md, workflow.md, roles.md, verification.md.

## Example Output

```markdown
# Compliance Report — my-project

**Generated:** 2026-04-01

## Project Summary
- **Name**: my-project
- **Type**: CLI tool (Python)
- **Language**: python
- **VCS Platform**: github

## Verification Tools
- **Lint**: ruff check
- **Typecheck**: mypy
- **Test**: pytest
- **Security**: pip-audit
- **Format**: ruff format

## Requirements Coverage Matrix
**Coverage**: 12/12 (100%)
- ✓ REQ-CLI-001
- ✓ REQ-CLI-002
...

## Audit Summary
- **Passed**: 9
- **Failed**: 0
- **Status**: Healthy
```
