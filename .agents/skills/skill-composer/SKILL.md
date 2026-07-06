# SKILL.md
# Skill Composer

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
The skill-composer skill enables agents to dynamically compose and manage their skill sets based on the current task, project context, and governance requirements. It ensures that agents only load the necessary skills for their current operation while maintaining compliance with Specsmith's governance framework.

## Skill Composition Rules

### 1. Context-Aware Skill Loading
- Load only skills relevant to the current task
- Dynamically adjust skill set based on project requirements
- Ensure all loaded skills are properly validated and authorized

### 2. Governance Compliance
- All skill compositions must pass preflight checks
- Skills must be from the approved skill catalog
- Any skill composition must be traceable to a work item or requirement

### 3. Performance Optimization
- Minimize memory footprint by loading only necessary skills
- Optimize skill loading order for maximum efficiency
- Cache skill compositions when appropriate

## Implementation Details

### Skill Selection Algorithm
1. Analyze the current task requirements
2. Identify required capabilities from the project's governance rules
3. Select appropriate skills from the available catalog
4. Validate that all selected skills are compliant with current governance
5. Compose the final skill set for execution

### Skill Validation
- Verify that each skill meets its documented requirements
- Ensure skills are compatible with the current project context
- Confirm that skill combinations don't violate governance constraints

## Configuration

### Default Behavior
By default, the skill-composer will:
- Load core governance skills (preflight-gate, governed-agent-loop)
- Select task-specific skills based on the current operation
- Apply context-aware optimization

### Override Options
- Allow manual skill composition for advanced users
- Support skill exclusion for specific scenarios
- Enable temporary skill overrides with proper preflight

## Security Considerations
- All skill compositions must be validated before execution
- Unauthorized skill combinations are blocked
- Skill composition history is tracked for audit purposes

## Compliance Requirements
- Every skill composition must be traceable to a valid work item
- Skill compositions must be reviewed by the preflight-gate
- All skill combinations must comply with the project's permission model
