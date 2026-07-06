# SKILL.md
# Release Governed Profile

## Requirements Covered

### Governance Requirements
- REQ-012: Least-Privilege Agent Permissions
- REQ-217: Agent Permissions Check
- REQ-220: Policy Guardrails
- REQ-244: Context Window Sizing
- REQ-245: Live Context Fill Indicator
- REQ-246: Auto Context Compression
- REQ-247: Hard Context Ceiling
- REQ-065: GitHub Release Creation
- REQ-066: PyPI Deployment
- REQ-067: CI Management
- REQ-068: Pull Request Management
- REQ-069: GitLab and Bitbucket Support
- REQ-070: Repository Management
- REQ-071: Non-GitHub Platform Support

## Core Principle
The release-governed profile is designed for agents operating in release management environments. It ensures compliance with Specsmith governance while managing the complex requirements of software releases across multiple platforms.

## Profile Characteristics

### Required Skills
- preflight-gate
- governed-agent-loop
- requirement-author
- testcase-author
- traceability-auditor
- context-pack-compiler
- token-budget-auditor
- skill-composer
- git
- release
- execution

### Environment-Specific Features
- Release management environment integration
- Context window optimization for release processes
- Compliance with release management policies
- Integration with multiple platform release systems (GitHub, GitLab, Bitbucket, PyPI, etc.)

## Implementation Details

### Release-Specific Execution
1. Leverage release management capabilities for version control and deployment
2. Optimize context windows to fit release process constraints
3. Apply Specsmith governance rules within release environments
4. Maintain traceability between release actions and Specsmith requirements

### Context Management
- Optimize context for release management requirements
- Apply release-specific compression techniques
- Ensure context fits within release constraints while maintaining traceability
- Track release management usage and performance metrics

## Configuration

### Default Behavior
By default, the release-governed profile:
- Integrates with multiple release platforms (GitHub, GitLab, Bitbucket, PyPI)
- Optimizes context for release management processes
- Maintains full Specsmith governance compliance
- Tracks release management metrics

### Override Options
- Allow release-specific skill overrides
- Support release environment customization
- Enable release-specific context optimization

## Security Considerations
- All release management actions must pass preflight validation
- Release-specific skill compositions must be traceable
- Release management environment compliance must be maintained
- Release management usage must be tracked and audited

## Compliance Requirements
- Every release management action must be traceable to a valid work item or requirement
- Release management integration must comply with platform policies
- All skill compositions must follow Specsmith governance
- Release management usage must be reported and audited
