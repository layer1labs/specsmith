# SKILL.md
# Agent Core Profile

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
The agent-core profile defines the fundamental capabilities and governance rules that all Specsmith agents must follow. This profile ensures that agents operate within the bounds of the Specsmith governance framework while maintaining the flexibility to adapt to different project contexts.

## Profile Characteristics

### Minimal Required Skills
- preflight-gate
- governed-agent-loop
- requirement-author
- testcase-author
- traceability-auditor
- context-pack-compiler
- token-budget-auditor
- skill-composer

### Governance Compliance
All agents using this profile must:
1. Run preflight checks before any action that could have side effects
2. Follow the governed-agent-loop execution pattern
3. Maintain traceability between requirements, tests, and code changes
4. Compose skills dynamically based on context
5. Track token usage and budget efficiency

## Implementation Details

### Core Loop Execution
1. Detect Specsmith project context
2. Run session bootstrap procedures
3. Emit governance anchor
4. Classify user intent (read-only, change, release, destructive, research, planning)
5. For non-read-only actions, run preflight
6. Load only required context and skills
7. Execute smallest scoped action
8. Run verification gates
9. Record evidence
10. Save through Specsmith

### Context Management
- Build minimal context packs from project state, requirements, work items, ESDB records, and relevant skills
- Never inject the whole repository when a scoped context is sufficient
- Prefer requirement IDs, test IDs, recent WIs, and relevant files
- Exclude stale, low-confidence, tombstoned, or contradicted ESDB records
- Include stop conditions and known hazards
- Track token budget and context utilization

## Configuration

### Default Behavior
By default, the agent-core profile:
- Enforces strict preflight checks for all non-read-only operations
- Maintains minimal skill set for efficiency
- Applies context-aware optimization
- Tracks all actions for audit purposes

### Override Options
- Allow manual skill composition for advanced users
- Support skill exclusion for specific scenarios
- Enable temporary skill overrides with proper preflight

## Security Considerations
- All actions must pass preflight validation
- Skill compositions must be traceable to valid work items
- Unauthorized skill combinations are blocked
- Skill composition history is tracked for audit purposes

## Compliance Requirements
- Every action must be traceable to a valid work item or requirement
- All skill compositions must comply with the project's permission model
- Token usage must be tracked and reported
- Audit trails must be maintained for all operations
