---
name: execution
description: Skill for managing local command execution and environment management with specsmith governance
---

# Local Execution Management

This skill enables specsmith projects to manage local command execution and environment management while maintaining governance compliance across Windows, Linux, and Mac platforms.

## Requirements Covered

- REQ-089: Local Command Execution Policy
- REQ-090: Local Command Whitelist Management
- REQ-091: Local Command Blacklist Management
- REQ-092: Local Command Override Capability
- REQ-093: Pip Execution Override
- REQ-094: Pip Execution Safety Checks
- REQ-095: Virtual Environment Creation
- REQ-096: Virtual Environment Management
- REQ-097: Virtual Environment Validation
- REQ-098: Virtual Environment Warning System
- REQ-099: Local Environment Isolation
- REQ-100: Execution Policy Configuration

## Integration Capabilities

### Platform Features
- Cross-platform command execution with platform-specific considerations
- Local environment isolation and management
- Virtual environment creation and management
- Pip execution safety with workspace-local enforcement
- Whitelist and blacklist management for commands
- Override capability with human approval

### Governance Requirements
- Human approval required for all local command execution
- Configuration management with governance controls
- Security best practices enforcement for execution
- Resource monitoring and logging for execution activities

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
# Initialize execution management
specsmith skill install execution

# Configure execution policy
specsmith execution configure --default-permissive true --whitelist "git,python,pip"

# Execute a command with approval
specsmith execution run --command "pip install requests"

# Create a virtual environment
specsmith execution venv create --name myproject

# Manage virtual environments
specsmith execution venv list
specsmith execution venv activate --name myproject
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
execution:
  default_permissive: true
  whitelist:
    - git
    - python
    - pip
  blacklist: []
  pip_override_enabled: false
  venv_auto_create: true
  platform: auto  # windows, linux, mac, or auto
```

## Security Considerations

- All local command executions require human approval
- Platform-specific security policies must be enforced
- File system access controls must be maintained
- Environment variable handling must be secure
- Cross-platform compatibility must not compromise security
- Pip execution must only use local pip from workspace environment

## Compliance Requirements

- Follow security best practices for local execution
- Maintain audit logs of all local command executions
- Ensure proper virtual environment management and validation
- Enforce approval-based execution setup
- Support for platform-specific compliance requirements
