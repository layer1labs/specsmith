# Scenario: Missing Test Detection
## Problem statement
Assess whether workflow catches requirement changes that lack corresponding tests.

## Workflow steps
1. Add requirement without tests.
2. Run verification/audit checks.
3. Observe detection behavior.
4. Add tests and re-run checks.

## Metrics to capture
- missing-test detection rate
- requirement-to-test trace coverage
- audit completeness
- time to remediation

## Comparison axes
- no governance
- Spec Kit
- OpenSpec
- BMAD
- direct agent
- specsmith governed
