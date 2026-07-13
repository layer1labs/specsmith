---
name: release
description: Skill for managing release creation and deployment with specsmith governance
---

# Release Management

This skill enables specsmith projects to manage release creation and deployment across multiple platforms (GitHub, PyPI, CI systems) while maintaining governance compliance across Windows, Linux, and Mac platforms.

## Requirements Covered

- REQ-065: GitHub Release Creation
- REQ-066: PyPI Deployment
- REQ-067: CI Management
- REQ-068: Pull Request Management
- REQ-071: Release Notes Generation
- REQ-072: Release Tag Management
- REQ-073: Artifact Management
- REQ-074: Release Branch Management
- REQ-075: Release Validation
- REQ-076: Release Rollback
- REQ-077: Release Promotion
- REQ-078: Release Metadata Management

## Integration Capabilities

### Platform Features
- Cross-platform release management for GitHub, PyPI, and CI systems
- Release creation, tagging, and deployment
- Pull request and merge management
- Release notes generation and validation
- Artifact management and cleanup
- Release branch management and promotion

### Governance Requirements
- Human approval required for all release operations
- Configuration management with governance controls
- Security best practices enforcement for release processes
- Audit logging of all release activities

## Platform-Specific Considerations

### Windows
- Path handling with Windows-specific conventions
- Windows-specific CI/CD integration
- File system permissions for release artifacts
- Windows-specific deployment considerations

### Linux
- POSIX-compliant path handling
- Linux-specific CI/CD integration
- Package manager integration for deployment
- System service management for release processes

### macOS
- Darwin-specific path handling
- macOS application integration for release tools
- Homebrew and MacPorts package management
- System preferences and security frameworks for release processes

## Usage Examples

```bash
# Initialize release management
specsmith skill install release

# Create a new release
specsmith release create --version 1.2.3 --platform github --notes "Release notes here"

# Deploy to PyPI
specsmith release deploy --platform pypi --package mypackage

# Manage CI workflows
specsmith release ci manage --workflow build-and-test --status enabled

# Create pull request
specsmith release pr create --source feature-branch --target main --title "Release 1.2.3"

# Generate release notes
specsmith release notes generate --from v1.2.0 --to v1.2.3

# Manage release artifacts
specsmith release artifacts upload --file dist/my-package-1.2.3.tar.gz
specsmith release artifacts download --file my-package-1.2.3.tar.gz

# Promote release between environments
specsmith release promote --from staging --to production
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
release:
  default_platform: github
  platforms:
    github:
      token_file: ~/.github_token
      api_endpoint: https://api.github.com
    pypi:
      username_file: ~/.pypi_username
      password_file: ~/.pypi_password
    ci:
      provider: github-actions
      workflow_file: .github/workflows/release.yml
  auto_approve: false
  platform: auto  # windows, linux, mac, or auto
```

## Security Considerations

- All release operations require human approval
- Platform-specific security policies must be enforced
- Artifact storage and management must be secure
- Deployment credentials must be properly handled
- Cross-platform compatibility must not compromise security

## Compliance Requirements

- Follow security best practices for release management
- Maintain audit logs of all release operations
- Ensure proper platform-specific configuration management
- Enforce approval-based release setup
- Support for platform-specific compliance requirements
