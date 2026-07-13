# SKILL.md
# Warp Governed Profile

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
The warp-governed profile is designed for agents operating within the Warp Terminal environment. It ensures compliance with Specsmith governance while leveraging Warp's specific capabilities and constraints.

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
- warp-integration

### Environment-Specific Features
- Warp Terminal integration capabilities
- Context window optimization for Warp's terminal constraints
- Compliance with Warp's terminal environment
- Integration with Warp's native terminal features

## Implementation Details

### Warp-Specific Execution
1. Leverage Warp Terminal's native capabilities for terminal operations
2. Optimize context windows to fit Warp's terminal constraints
3. Apply Specsmith governance rules within Warp's environment
4. Maintain traceability between Warp actions and Specsmith requirements

### Context Management
- Optimize context for Warp's terminal environment
- Apply Warp-specific compression techniques
- Ensure context fits within Warp's constraints while maintaining traceability
- Track Warp-specific terminal usage

## Configuration

### Default Behavior
By default, the warp-governed profile:
- Integrates with Warp Terminal's native features
- Optimizes context for Warp's terminal environment
- Maintains full Specsmith governance compliance
- Tracks Warp-specific usage metrics

### Override Options
- Allow Warp-specific skill overrides
- Support Warp Terminal environment customization
- Enable Warp-specific context optimization

## Security Considerations
- All Warp Terminal actions must pass preflight validation
- Warp-specific skill compositions must be traceable
- Warp Terminal environment compliance must be maintained
- Warp-specific terminal usage must be tracked

## Compliance Requirements
- Every Warp Terminal action must be traceable to a valid work item or requirement
- Warp Terminal integration must comply with Warp's usage policies
- All skill compositions must follow Specsmith governance
- Warp-specific terminal usage must be reported
