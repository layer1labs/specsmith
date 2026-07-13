# SKILL.md
# Embedded FPGA Governed Profile

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
The embedded-fpga-governed profile is designed for agents operating in embedded FPGA development environments. It ensures compliance with Specsmith governance while managing the unique constraints and requirements of FPGA development.

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
- execution
- git
- release

### Environment-Specific Features
- FPGA development environment integration
- Context window optimization for FPGA constraints
- Compliance with FPGA development policies
- Integration with FPGA development tools and workflows

## Implementation Details

### FPGA-Specific Execution
1. Leverage FPGA development tool capabilities for hardware design
2. Optimize context windows to fit FPGA development constraints
3. Apply Specsmith governance rules within FPGA environments
4. Maintain traceability between FPGA actions and Specsmith requirements

### Context Management
- Optimize context for FPGA development requirements
- Apply FPGA-specific compression techniques
- Ensure context fits within FPGA constraints while maintaining traceability
- Track FPGA development usage and performance metrics

## Configuration

### Default Behavior
By default, the embedded-fpga-governed profile:
- Integrates with FPGA development tools and environments
- Optimizes context for FPGA development constraints
- Maintains full Specsmith governance compliance
- Tracks FPGA development metrics

### Override Options
- Allow FPGA-specific skill overrides
- Support FPGA development environment customization
- Enable FPGA-specific context optimization

## Security Considerations
- All FPGA development actions must pass preflight validation
- FPGA-specific skill compositions must be traceable
- FPGA development environment compliance must be maintained
- FPGA development usage must be tracked and audited

## Compliance Requirements
- Every FPGA development action must be traceable to a valid work item or requirement
- FPGA development integration must comply with development environment policies
- All skill compositions must follow Specsmith governance
- FPGA development usage must be reported and audited
