# Export & Compliance

`specsmith export` generates a comprehensive compliance report for your governed project.

## Usage

```bash
# Print to terminal
specsmith export --project-dir ./my-project

# Save to file
specsmith export --project-dir ./my-project --output report.md
```

## Report Sections

### Project Summary

Project name, type, language, VCS platform, and spec version from `scaffold.yml`.

### Verification Tools

Complete listing of lint, typecheck, test, security, build, format, and compliance tools from the [Tool Registry](tool-registry.md) for the project type.

### Requirements Coverage Matrix

Cross-references `docs/REQUIREMENTS.md` against `docs/TEST_SPEC.md`:

- Lists every REQ-ID found in requirements
- Checks which REQs have corresponding `Covers: REQ-xxx` in tests
- Shows coverage percentage (e.g., "12/15 (80%)")
- Marks each REQ as ✓ (covered) or ✗ (uncovered)

### Audit Summary

Runs the full `specsmith audit` check suite and reports:

- Passed / Failed / Fixable counts
- Overall status (Healthy or Issues found)
- Individual check results with messages

### Governance File Inventory

Lists all expected governance files and whether they exist:

- AGENTS.md, LEDGER.md, scaffold.yml
- docs/REQUIREMENTS.md, docs/TEST_SPEC.md, docs/architecture.md
- docs/governance/rules.md, workflow.md, roles.md, verification.md
