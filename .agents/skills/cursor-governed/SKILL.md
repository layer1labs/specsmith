# SKILL.md
# Cursor Governed Profile

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
The cursor-governed profile is designed for agents operating within the Cursor IDE environment. It ensures compliance with Specsmith governance while leveraging Cursor's specific capabilities and constraints.

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
- cursor-integration

### Environment-Specific Features
- Cursor IDE integration capabilities
- Context window optimization for Cursor's IDE constraints
- Compliance with Cursor's IDE environment
- Integration with Cursor's native IDE features

## Implementation Details

### Cursor-Specific Execution
1. Leverage Cursor IDE's native capabilities for code editing
2. Optimize context windows to fit Cursor's IDE constraints
3. Apply Specsmith governance rules within Cursor's environment
4. Maintain traceability between Cursor actions and Specsmith requirements

### Context Management
- Optimize context for Cursor's IDE environment
- Apply Cursor-specific compression techniques
- Ensure context fits within Cursor's constraints while maintaining traceability
- Track Cursor-specific IDE usage

## Configuration

### Default Behavior
By default, the cursor-governed profile:
- Integrates with Cursor IDE's native features
- Optimizes context for Cursor's IDE environment
- Maintains full Specsmith governance compliance
- Tracks Cursor-specific usage metrics

### Override Options
- Allow Cursor-specific skill overrides
- Support Cursor IDE environment customization
- Enable Cursor-specific context optimization

## Security Considerations
- All Cursor IDE actions must pass preflight validation
- Cursor-specific skill compositions must be traceable
- Cursor IDE environment compliance must be maintained
- Cursor-specific IDE usage must be tracked

## Compliance Requirements
- Every Cursor IDE action must be traceable to a valid work item or requirement
- Cursor IDE integration must comply with Cursor's usage policies
- All skill compositions must follow Specsmith governance
- Cursor-specific IDE usage must be reported
