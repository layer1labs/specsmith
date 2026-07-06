---
name: testing-artifact-management
description: Skill for managing test artifacts including screenshots, videos, and logs with specsmith governance
---

# Testing Artifact Management

This skill enables specsmith projects to manage test artifacts including screenshots, videos, and logs while maintaining governance compliance.

## Requirements Covered

- REQ-104: Testing Artifact Management
- Allows specsmith projects to manage test artifacts including screenshots, videos, and logs with human approval

## Integration Capabilities

### Artifact Features
- Screenshot capture and management
- Video recording and storage
- Log file handling and archiving
- Artifact metadata tracking
- Artifact retention policies
- Artifact sharing and access control

### Governance Requirements
- Human approval required for artifact management
- Configuration management with governance controls
- Approval-based artifact retention
- Audit logging of artifact access

## Usage Examples

```bash
# Initialize artifact management
specsmith skill install testing-artifact-management

# Configure artifact settings
specsmith test artifact configure --capture-screenshots on_failure --retention-days 30

# Manage test artifacts
specsmith test artifact manage --action archive --suite e2e-tests
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
artifact_management:
  capture_screenshots: "on_failure"
  capture_videos: "never"
  log_level: "info"
  retention_days: 30
  storage_location: "/var/test-artifacts"
```

## Security Considerations

- All artifact management requires human approval
- Sensitive data in artifacts must be handled securely
- Artifact access controls must be enforced
- Storage location security must be maintained

## Compliance Requirements

- Follow security best practices for artifact management
- Maintain audit logs of all artifact activities
- Ensure proper retention and deletion policies
- Enforce approval-based artifact access
