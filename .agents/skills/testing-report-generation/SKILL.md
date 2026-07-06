---
name: testing-report-generation
description: Skill for automatically generating test reports with specsmith governance
---

# Testing Report Generation

This skill enables specsmith projects to automatically generate test reports while maintaining governance compliance.

## Requirements Covered

- REQ-105: Testing Report Generation
- Allows specsmith projects to automatically generate test reports with human approval

## Integration Capabilities

### Report Features
- Automated test report generation
- Multiple report formats (HTML, JSON, XML)
- Coverage reporting and analytics
- Test summary and detailed results
- Historical report comparison
- Integration with CI/CD pipelines

### Governance Requirements
- Human approval required for report generation
- Configuration management with governance controls
- Approval-based report formats
- Audit logging of report generation activities

## Usage Examples

```bash
# Initialize report generation
specsmith skill install testing-report-generation

# Generate test report
specsmith test report generate --format html --suite e2e-tests

# Configure report settings
specsmith test report configure --format html --include-coverage true --retention-days 60
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
reporting:
  format: "html"
  include_coverage: true
  include_screenshots: false
  retention_days: 60
  generate_on_success: true
  generate_on_failure: true
```

## Security Considerations

- All report generation requires human approval
- Report content must be properly secured
- Access controls for reports must be enforced
- Sensitive data in reports must be handled appropriately

## Compliance Requirements

- Follow security best practices for report generation
- Maintain audit logs of all report generation activities
- Ensure proper retention and deletion policies
- Enforce approval-based report generation
