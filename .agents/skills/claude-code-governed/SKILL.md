# SKILL.md
# Claude Code Governed Profile

## Requirements Covered

### Governance Requirements
- REQ-012: Least-Privilege Agent Permissions
- REQ-217: Agent Permissions Check
- REQ-220: Policy Guardrails
- REQ-244: Context Window Sizing
- REQ-245: Live Context Fill Indicator
- REQ-246: Auto Context Compression
- REQ-247: Hard Context Ceiling

## Core Principle
The claude-code-governed profile is designed for agents operating within the Claude Code environment. It ensures compliance with Specsmith governance while leveraging Claude's specific capabilities and constraints.

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
- claude-code-integration

### Environment-Specific Features
- Claude Code integration capabilities
- Context window optimization for Claude's token limits
- Compliance with Claude's usage policies
- Integration with Claude's code editing features

## Implementation Details

### Claude-Specific Execution
1. Leverage Claude Code's native capabilities for code editing
2. Optimize context windows to fit Claude's token limits
3. Apply Specsmith governance rules within Claude's environment
4. Maintain traceability between Claude actions and Specsmith requirements

### Context Management
- Optimize context for Claude's 100K token limit
- Apply Claude-specific compression techniques
- Ensure context fits within Claude's constraints while maintaining traceability
- Track Claude-specific token usage

## Configuration

### Default Behavior
By default, the claude-code-governed profile:
- Integrates with Claude Code's native editing features
- Optimizes context for Claude's token limits
- Maintains full Specsmith governance compliance
- Tracks Claude-specific usage metrics

### Override Options
- Allow Claude-specific skill overrides
- Support Claude Code environment customization
- Enable Claude-specific context optimization

## Security Considerations
- All Claude Code actions must pass preflight validation
- Claude-specific skill compositions must be traceable
- Claude Code environment compliance must be maintained
- Claude-specific token usage must be tracked

## Compliance Requirements
- Every Claude Code action must be traceable to a valid work item or requirement
- Claude Code integration must comply with Claude's usage policies
- All skill compositions must follow Specsmith governance
- Claude-specific token usage must be reported
