# Scenario: Interrupted Recovery
## Problem statement
Simulate context loss or session interruption during active implementation and recover to completion.

## Workflow steps
1. Start implementation.
2. Interrupt session mid-task.
3. Reconstruct context.
4. Complete implementation and verify.

## Metrics to capture
- recovery time
- recovered trace fidelity
- audit completeness after restart
- final correctness

## Comparison axes
- no governance
- Spec Kit
- OpenSpec
- BMAD
- direct agent
- specsmith governed
