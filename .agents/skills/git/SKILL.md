---
name: git
description: Skill for managing Git platform management with specsmith governance
---

# Git Platform Management

This skill enables specsmith projects to manage Git repositories across multiple platforms (GitHub, GitLab, Bitbucket, etc.) while maintaining governance compliance across Windows, Linux, and Mac platforms.

## Requirements Covered

- REQ-079: Git Platform Agnostic Management
- REQ-080: GitHub Platform Management
- REQ-081: GitLab Platform Management
- REQ-082: Bitbucket Platform Management
- REQ-083: Azure DevOps Platform Management
- REQ-084: Git Platform Authentication Management
- REQ-085: Git Platform Configuration Management
- REQ-086: Git Platform Repository Creation
- REQ-087: Git Platform Repository Deletion
- REQ-088: Git Platform Repository Cloning

## Integration Capabilities

### Platform Features
- Cross-platform Git repository management for GitHub, GitLab, Bitbucket, and Azure DevOps
- Platform-specific authentication and credential management
- Repository creation, deletion, and cloning
- Configuration management for multiple Git platforms
- Webhook and integration management

### Governance Requirements
- Human approval required for all Git platform operations
- Configuration management with governance controls
- Security best practices enforcement for Git operations
- Audit logging of all Git platform activities

## Platform-Specific Considerations

### Windows
- Path handling with Windows-specific conventions
- Git client integration with Windows-specific tools
- Windows-specific credential storage and management
- File system permissions for repository access

### Linux
- POSIX-compliant path handling
- Git client integration with standard Linux tools
- Package manager integration for Git tools
- System service management for Git operations

### macOS
- Darwin-specific path handling
- macOS application integration for Git tools
- Homebrew and MacPorts package management
- System preferences and security frameworks

## Usage Examples

```bash
# Initialize Git management
specsmith skill install git

# Configure Git platform settings
specsmith git configure --platform github --token-file ~/.github_token

# Create a new repository
specsmith git repo create --platform github --name my-project --description "My new project"

# Clone a repository
specsmith git repo clone --platform github --url https://github.com/user/repo.git

# Manage authentication
specsmith git auth setup --platform github --token mytoken123

# List repositories
specsmith git repo list --platform github
```

## Configuration

The skill requires the following configuration in `scaffold.yml`:

```yaml
git:
  default_platform: github
  platforms:
    github:
      token_file: ~/.github_token
      api_endpoint: https://api.github.com
    gitlab:
      token_file: ~/.gitlab_token
      api_endpoint: https://gitlab.com/api/v4
    bitbucket:
      token_file: ~/.bitbucket_token
      api_endpoint: https://api.bitbucket.org/2.0
  auto_approve: false
  platform: auto  # windows, linux, mac, or auto
```

## Security Considerations

- All Git platform operations require human approval
- Platform-specific security policies must be enforced
- Credential storage and management must be secure
- Repository access controls must be maintained
- Cross-platform compatibility must not compromise security

## Compliance Requirements

- Follow security best practices for Git platform management
- Maintain audit logs of all Git platform operations
- Ensure proper platform-specific configuration management
- Enforce approval-based Git platform setup
- Support for platform-specific compliance requirements
