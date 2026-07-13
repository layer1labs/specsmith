# Verification Procedures

This document outlines the verification procedures that ensure specsmith governance is properly enforced.

## Verification Requirements

### Pre-flight Verification
- All commands must pass preflight checks before execution
- Agent actions must comply with governance rules
- Context window limits must be respected
- Audit logs must be maintained

### Post-execution Verification
- Changes must be traceable to requirements
- Test coverage must be verified
- Compliance checks must pass
- Audit trails must be complete

## Verification Processes

### Requirement Verification
- All requirements must have test coverage
- Traceability between requirements and test cases must be maintained
- Requirement changes must be properly documented

### Test Verification
- All tests must be executed and pass
- Test coverage must meet minimum thresholds
- Test results must be recorded in the audit trail

### Compliance Verification
- All actions must comply with governance rules
- Agent behavior must be monitored and audited
- Evidence quality must be maintained
- Session integrity must be preserved

## Verification Tools

### specsmith verify
- Run verification checks on the project
- Check for duplicate IDs, orphans, coverage gaps
- Validate governance YAML files
- Ensure all requirements have test coverage

### specsmith audit
- Run drift and health checks
- Verify governance health
- Check for any compliance violations
- Ensure machine state matches governance YAML
