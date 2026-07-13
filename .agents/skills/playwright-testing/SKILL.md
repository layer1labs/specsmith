---
name: playwright-testing
description: Skill for using Playwright for end-to-end browser testing with specsmith governance
---

# Playwright Testing Framework

This skill enables specsmith projects to use Playwright for end-to-end browser testing while maintaining governance compliance.

## Requirements Covered

- REQ-101: Playwright Testing Framework
- Allows specsmith projects to use Playwright for end-to-end browser testing with human approval

## Integration Capabilities

### Framework Features
- End-to-end browser testing with Playwright
- Cross-browser testing (Chromium, Firefox, WebKit)
- API testing capabilities
- Screenshot and video capture
- Parallel test execution
- Test reporting and analytics

### Governance Requirements
- Human approval required for all Playwright testing
- Configuration management with governance controls
- Test artifact management with approval
- Reporting and coverage tracking with approval

## Usage Examples

```bash
# Initialize Playwright testing
specsmith skill install playwright-testing

# Configure Playwright settings
specsmith playwright configure --browser chromium --timeout 30000

# Run end-to-end tests
specsmith playwright run --test-suite e2e-tests

# Generate test reports
specsmith playwright report --format html
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
playwright:
  browser: chromium
  timeout: 30000
  headless: true
  parallel: true
  screenshot: "on_failure"
```

## Security Considerations

- All Playwright testing requires human approval
- Test environment isolation must be maintained
- Sensitive data handling in tests must be secured
- Test artifact access controls must be enforced

## Compliance Requirements

- Follow security best practices for testing environments
- Maintain audit logs of all Playwright test executions
- Ensure proper test artifact management and retention
- Generate and track test coverage reports
