"""
Core governance skills for Specsmith.
This module contains the fundamental governance skills that control agent behavior
and ensure proper governance compliance.
"""

from specsmith.skills import SkillDomain, SkillEntry

# preflight-gate skill implementation
def preflight_gate():
    """
    Purpose:
    Force every agent to run Specsmith preflight before any write, code change,
    command with side effects, dependency change, branch operation, release,
    or destructive operation.

    Required behavior:
    Before action:
      specsmith preflight "<intended action>" --json

    If decision == accepted:
      proceed with work_item_id in scope

    If decision == needs_clarification:
      stop and surface clarification to user

    If decision == rejected:
      stop and explain why

    If no preflight was run:
      do not modify files
    """
    pass  # Implementation would be in the CLI/command layer


# governed-agent-loop skill implementation
def governed_agent_loop():
    """
    Purpose:
    Define the default execution loop for any agent operating inside a Specmith project.

    Loop:
    inspect -> anchor -> classify -> preflight -> retrieve context -> act -> verify -> record -> save

    Detailed flow:
    1. Detect Specsmith project.
    2. Run session bootstrap.
    3. Emit governance anchor.
    4. Classify user intent:
       - read_only_ask
       - change
       - release
       - destructive
       - research
       - planning
    5. For non-read-only actions, run preflight.
    6. Load only the required context and skills.
    7. Execute the smallest scoped action.
    8. Run verification gates.
    9. Record evidence.
    10. Save through Specsmith, not raw git.
    """
    pass  # Implementation would be in the agent core


# requirement-author skill implementation
def requirement_author():
    """
    Purpose:
    Convert vague user intent into atomic, testable Specsmith requirements.

    Rules:
    * One requirement should express one obligation.
    * Every requirement must have a stable ID.
    * Every requirement must include rationale.
    * Every requirement must include acceptance criteria.
    * Every requirement must be linkable to one or more tests.
    * Avoid large umbrella requirements.
    * Split ambiguous requirements before implementation.
    """
    pass  # Implementation would be in the requirements system


# testcase-author skill implementation
def testcase_author():
    """
    Purpose:
    Create test cases that trace directly to requirements.

    Rules:
    * Every new behavior requirement needs at least one test case.
    * Every test case must reference requirement IDs.
    * Every test case must define expected behavior.
    * Every regression fix should include a regression test unless impossible.
    * If a test cannot be automated, mark it as manual and explain why.
    """
    pass  # Implementation would be in the test system


# traceability-auditor skill implementation
def traceability_auditor():
    """
    Purpose:
    Detect weak or broken trace chains.

    Check for:
    * Requirements with no tests.
    * Tests with no requirements.
    * Work items with no requirements.
    * Code changes with no accepted preflight.
    * Requirements without acceptance criteria.
    * Requirements whose tests do not actually verify the stated behavior.
    * Generated docs out of sync with canonical YAML.
    * Suppressed warnings that should be rechecked.
    """
    pass  # Implementation would be in the audit system


# context-pack-compiler skill implementation
def context_pack_compiler():
    """
    Purpose:
    Build minimal context packs for agents from the project state, requirements,
    work items, ESDB records, and relevant skills.

    Rules:
    * Never inject the whole repo when a scoped context pack is enough.
    * Prefer requirement IDs, test IDs, recent WIs, and relevant files.
    * Exclude stale, low-confidence, tombstoned, or contradicted ESDB records.
    * Include stop conditions and known hazards.
    * Track token budget and context utilization.
    """
    pass  # Implementation would be in the context system


# token-budget-auditor skill implementation
def token_budget_auditor():
    """
    Purpose:
    Measure token efficiency by outcome, not raw usage.

    Track:
    * Tokens per accepted preflight.
    * Tokens per completed work item.
    * Tokens per passing verification.
    * Tokens per successful release.
    * Tokens wasted on rejected/clarification loops.
    * Tool calls per success.
    * Cost-of-pass by model/provider/profile.

    This should support Specsmith's claim that governance reduces total cost per correct answer.
    """
    pass  # Implementation would be in the metrics system


# Define the SKILLS list for the governance domain
SKILLS = [
    SkillEntry(
        slug="preflight-gate",
        name="Preflight Gate",
        description="Force every agent to run Specsmith preflight before any write, code change, or destructive operation.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "security", "preflight", "validation"],
        body="""
# Preflight Gate

## Purpose
Force every agent to run Specsmith preflight before any write, code change, command with side effects, dependency change, branch operation, release, or destructive operation.

## Required behavior
Before action:
  specsmith preflight "<intended action>" --json

If decision == accepted:
  proceed with work_item_id in scope

If decision == needs_clarification:
  stop and surface clarification to user

If decision == rejected:
  stop and explain why

If no preflight was run:
  do not modify files
        """,
    ),
    SkillEntry(
        slug="governed-agent-loop",
        name="Governed Agent Loop",
        description="Define the default execution loop for any agent operating inside a Specsmith project.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "agent", "loop", "execution"],
        body="""
# Governed Agent Loop

## Purpose
Define the default execution loop for any agent operating inside a Specmith project.

## Loop
inspect -> anchor -> classify -> preflight -> retrieve context -> act -> verify -> record -> save

## Detailed flow
1. Detect Specsmith project.
2. Run session bootstrap.
3. Emit governance anchor.
4. Classify user intent:
   - read_only_ask
   - change
   - release
   - destructive
   - research
   - planning
5. For non-read-only actions, run preflight.
6. Load only the required context and skills.
7. Execute the smallest scoped action.
8. Run verification gates.
9. Record evidence.
10. Save through Specsmith, not raw git.
        """,
    ),
    SkillEntry(
        slug="requirement-author",
        name="Requirement Author",
        description="Convert vague user intent into atomic, testable Specsmith requirements.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "requirements", "authoring"],
        body="""
# Requirement Author

## Purpose
Convert vague user intent into atomic, testable Specsmith requirements.

## Rules
* One requirement should express one obligation.
* Every requirement must have a stable ID.
* Every requirement must include rationale.
* Every requirement must include acceptance criteria.
* Every requirement must be linkable to one or more tests.
* Avoid large umbrella requirements.
* Split ambiguous requirements before implementation.
        """,
    ),
    SkillEntry(
        slug="testcase-author",
        name="Test Case Author",
        description="Create test cases that trace directly to requirements.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "testing", "test-cases"],
        body="""
# Test Case Author

## Purpose
Create test cases that trace directly to requirements.

## Rules
* Every new behavior requirement needs at least one test case.
* Every test case must reference requirement IDs.
* Every test case must define expected behavior.
* Every regression fix should include a regression test unless impossible.
* If a test cannot be automated, mark it as manual and explain why.
        """,
    ),
    SkillEntry(
        slug="traceability-auditor",
        name="Traceability Auditor",
        description="Detect weak or broken trace chains.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "traceability", "auditing"],
        body="""
# Traceability Auditor

## Purpose
Detect weak or broken trace chains.

## Check for
* Requirements with no tests.
* Tests with no requirements.
* Work items with no requirements.
* Code changes with no accepted preflight.
* Requirements without acceptance criteria.
* Requirements whose tests do not actually verify the stated behavior.
* Generated docs out of sync with canonical YAML.
* Suppressed warnings that should be rechecked.
        """,
    ),
    SkillEntry(
        slug="context-pack-compiler",
        name="Context Pack Compiler",
        description="Build minimal context packs for agents from the project state, requirements, work items, ESDB records, and relevant skills.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "context", "packs", "optimization"],
        body="""
# Context Pack Compiler

## Purpose
Build minimal context packs for agents from the project state, requirements,
work items, ESDB records, and relevant skills.

## Rules
* Never inject the whole repo when a scoped context pack is enough.
* Prefer requirement IDs, test IDs, recent WIs, and relevant files.
* Exclude stale, low-confidence, tombstoned, or contradicted ESDB records.
* Include stop conditions and known hazards.
* Track token budget and context utilization.
        """,
    ),
    SkillEntry(
        slug="token-budget-auditor",
        name="Token Budget Auditor",
        description="Measure token efficiency by outcome, not raw usage.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "tokens", "efficiency", "cost"],
        body="""
# Token Budget Auditor

## Purpose
Measure token efficiency by outcome, not raw usage.

## Track
* Tokens per accepted preflight.
* Tokens per completed work item.
* Tokens per passing verification.
* Tokens per successful release.
* Tokens wasted on rejected/clarification loops.
* Tool calls per success.
* Cost-of-pass by model/provider/profile.

This should support Specsmith's claim that governance reduces total cost per correct answer.
        """,
    ),
    SkillEntry(
        slug="improvement-reporter",
        name="Improvement Reporter",
        description="Report improvements to the Specsmith system and suggest enhancements.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "improvement", "reporting"],
        body="""
# Improvement Reporter

## Purpose
Report improvements to the Specsmith system and suggest enhancements.

## Required behavior
* Detect when a user has completed a task successfully
* Identify potential improvements in the process or system
* Generate a structured report with:
  - What was done
  - What worked well
  - What could be improved
  - Suggested improvements
* Suggest improvements to the system itself
* Provide actionable feedback to the Specsmith team
        """,
    ),
    SkillEntry(
        slug="agent-flow-controller",
        name="Agent Flow Controller",
        description="Control the flow of agent execution and manage agent interactions.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "agent", "flow", "control"],
        body="""
# Agent Flow Controller

## Purpose
Control the flow of agent execution and manage agent interactions.

## Required behavior
* Manage agent execution order
* Coordinate agent interactions
* Handle agent failures gracefully
* Ensure proper resource allocation
* Maintain agent state consistency
* Implement flow control mechanisms
        """,
    ),
    SkillEntry(
        slug="model-runtime-optimizer",
        name="Model Runtime Optimizer",
        description="Optimize agent behavior based on model characteristics and runtime environment.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "model", "optimization", "runtime"],
        body="""
# Model Runtime Optimizer

## Purpose
Optimize agent behavior based on model characteristics and runtime environment.

## Required behavior
* Detect the current model and runtime environment
* Apply appropriate optimizations based on model profile
* Adjust temperature, context length, and other parameters
* Select optimal prompting strategies for the model
* Handle model-specific limitations and capabilities
* Provide runtime-aware recommendations
        """,
    ),
]
