---
name: zoo-code-integration
description: Skill for integrating with Zoo-Code for enhanced development workflows with specsmith governance
---

# Zoo Code Integration

This skill enables specsmith projects to integrate with Zoo-Code for enhanced development workflows while maintaining governance compliance across Windows, Linux, and Mac platforms.

## Requirements Covered

- Supports the Zoo-Code integration capabilities within specsmith governance
- Enables cross-platform development with platform-specific considerations

## Integration Capabilities

### Platform Features
- Cross-platform integration for Windows, Linux, and macOS
- Platform-specific configuration management
- Unified development experience with Zoo-Code extension
- Custom modes and language support for specsmith workflows
- Benchmarking and performance monitoring capabilities

### Governance Requirements
- Human approval required for Zoo-Code integration setup
- Configuration management with governance controls
- Platform-specific settings with approval requirements
- Audit logging of integration activities

## Platform-Specific Considerations

### Windows
- Path handling with Windows-specific conventions
- PowerShell and CMD integration
- Windows-specific environment variables
- File system permissions and access controls
- Registry and system integration considerations

### Linux
- POSIX-compliant path handling
- Shell integration (bash, zsh, fish)
- Package manager integration (apt, yum, pacman)
- System service management
- File permissions and ownership

### macOS
- Darwin-specific path handling
- macOS application integration
- Homebrew and MacPorts package management
- System preferences and security frameworks
- AppleScript and automation support

## Usage Examples

```bash
# Initialize Zoo-Code integration
specsmith skill install zoo-code-integration

# Configure for specific platform
specsmith zoo-code init --platform windows

# Export custom modes for Zoo-Code
specsmith zoo-code export-modes --output-dir ./zoo-code-config

# Run benchmark suite
specsmith zoo-code benchmark --suite smoke --runtime zoo-code

# Generate metrics report
specsmith zoo-code metrics --by task --metric tpca
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
zoo_code:
  platform: auto  # windows, linux, mac, or auto
  integration_mode: "zoo-code"
  benchmark_suite: "smoke"
  telemetry_enabled: true
  cross_platform_support: true
```

## Platform-Specific Setup

### Windows Setup
```bash
# Windows-specific setup
specsmith zoo-code init --platform windows
# Ensure PowerShell execution policy allows script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Linux Setup
```bash
# Linux-specific setup
specsmith zoo-code init --platform linux
# Install required dependencies
sudo apt-get install -y nodejs npm
```

### macOS Setup
```bash
# macOS-specific setup
specsmith zoo-code init --platform mac
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Security Considerations

- All Zoo-Code integrations require human approval
- Platform-specific security policies must be enforced
- File system access controls must be maintained
- Environment variable handling must be secure
- Cross-platform compatibility must not compromise security

## Compliance Requirements

- Follow security best practices for cross-platform development
- Maintain audit logs of all Zoo-Code integration activities
- Ensure proper platform-specific configuration management
- Enforce approval-based integration setup
- Support for platform-specific compliance requirements
