---
name: testing-coverage-reporting
description: Skill for generating and tracking test coverage reports with specsmith governance
---

# Testing Coverage Reporting

This skill enables specsmith projects to generate and track test coverage reports while maintaining governance compliance.

## Requirements Covered

- REQ-108: Testing Coverage Reporting
- Allows specsmith projects to generate and track test coverage reports with human approval

## Integration Capabilities

### Coverage Features
- Code coverage measurement and reporting
- Coverage threshold enforcement
- Coverage trend analysis
- Coverage report generation in multiple formats
- Integration with coverage tools (pytest-cov, Istanbul, etc.)
- Coverage data storage and retrieval

### Governance Requirements
- Human approval required for coverage reporting
- Configuration management with governance controls
- Approval-based coverage thresholds
- Audit logging of coverage activities

## Usage Examples

```bash
# Initialize coverage reporting
specsmith skill install testing-coverage-reporting

# Configure coverage settings
specsmith test coverage configure --threshold 80 --format html

# Generate coverage report
specsmith test coverage generate --suite e2e-tests --format html
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
coverage:
  threshold: 80
  format: "html"
  include_uncovered: false
  generate_on_success: true
  generate_on_failure: true
  retention_days: 30
```

## Security Considerations

- All coverage reporting requires human approval
- Coverage data must be properly secured
- Access controls for coverage reports must be enforced
- Sensitive code paths must be handled appropriately

## Compliance Requirements

- Follow security best practices for coverage reporting
- Maintain audit logs of all coverage activities
- Ensure proper retention and deletion policies
- Enforce approval-based coverage reporting settings
