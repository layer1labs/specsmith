---
name: testing-configuration
description: Skill for configuring testing frameworks including Playwright, pytest, and others with specsmith governance
---

# Testing Framework Configuration

This skill enables specsmith projects to configure testing frameworks including Playwright, pytest, and others while maintaining governance compliance.

## Requirements Covered

- REQ-102: Testing Framework Configuration
- Allows specsmith projects to configure testing frameworks including Playwright, pytest, and others with human approval

## Integration Capabilities

### Framework Features
- Configuration management for multiple testing frameworks
- Test suite organization and grouping
- Environment-specific configuration
- Integration with CI/CD pipelines
- Test runner customization
- Plugin and extension management

### Governance Requirements
- Human approval required for all testing framework configurations
- Configuration version control with governance
- Approval-based framework selection
- Environment isolation enforcement

## Usage Examples

```bash
# Initialize testing configuration
specsmith skill install testing-configuration

# Configure testing frameworks
specsmith test configure --framework pytest --env test --timeout 60000

# Set up test suite configuration
specsmith test setup --suite e2e --framework playwright --browser chromium
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
testing:
  framework: pytest
  environment: test
  timeout: 60000
  parallel: false
  coverage: true
```

## Security Considerations

- All testing framework configurations require human approval
- Configuration files must be properly secured
- Environment-specific settings must be isolated
- Framework selection must be governed

## Compliance Requirements

- Follow security best practices for testing configurations
- Maintain audit logs of all configuration changes
- Ensure proper version control of configuration files
- Enforce approval-based framework selection
