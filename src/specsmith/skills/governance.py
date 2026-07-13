"""
Core governance skills for Specsmith.
This module contains the fundamental governance skills that control agent behavior
and ensure proper governance compliance.
"""

from specsmith.skills import SkillDomain, SkillEntry


# preflight-gate skill implementation
def preflight_gate() -> None:
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
def governed_agent_loop() -> None:
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
def requirement_author() -> None:
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
def testcase_author() -> None:
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
def traceability_auditor() -> None:
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
def context_pack_compiler() -> None:
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
def token_budget_auditor() -> None:
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
    SkillEntry(
        slug="codity-ai-review",
        name="Codity AI Review",
        description="Perform AI code review using Codity AI integration.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "ai", "review", "codity", "ai-review", "pre-commit"],
        body="""
# Codity AI Review

## Purpose
Perform AI code review using Codity AI integration.

## Required behavior
* Run `codity review --staged` to review staged changes
* Run `codity login` to authenticate with Codity
* Run `codity init` to initialize the Codity configuration
* Run `codity scan --staged` to scan for security issues
* Run `codity test-gen --staged` to generate tests for staged changes
* Run `codity doctor` to diagnose issues with the Codity setup
* Run `specsmith integrate codity` to integrate Codity with Specsmith
* Configure HIGH severity for critical issues
* Configure MEDIUM severity for medium issues
* Set up PAT for GitLab with `set-pat --provider gitlab`
* Set up PAT for Azure with `set-pat --provider azure`
        """,
    ),
    SkillEntry(
        slug="verifier",
        name="Verifier",
        description="Verify code changes and ensure compliance with governance standards.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "verification", "compliance"],
        body="""# Verifier Skill

## Purpose
Verify code changes and ensure compliance with governance standards.

## Required behavior
* Check code changes against governance rules
* Ensure compliance with project standards
* Validate that all requirements are met
* Report any violations or issues
* Provide feedback for improvements
        """,
    ),
    SkillEntry(
        slug="planner",
        name="Planner",
        description="Plan and organize work items and tasks for the project.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "planning", "organization"],
        body="""
# Planner

## Purpose
Plan and organize work items and tasks for the project.

## Required behavior
* Break down complex tasks into manageable work items
* Prioritize tasks based on project goals
* Estimate effort and resources needed
* Create clear task descriptions
* Track progress and milestones
        """,
    ),
    SkillEntry(
        slug="diff-reviewer",
        name="Diff Reviewer",
        description="Review code changes and provide feedback on diffs.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "review", "diff"],
        body="""
# Diff Reviewer

## Purpose
Review code changes and provide feedback on diffs.

## Required behavior
* Analyze code changes in context
* Identify potential issues or improvements
* Provide constructive feedback
* Ensure changes align with project standards
* Suggest refactoring opportunities
        """,
    ),
    SkillEntry(
        slug="onboarding-coach",
        name="Onboarding Coach",
        description="Guide new team members through the onboarding process.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "onboarding", "training"],
        body="""
# Onboarding Coach

## Purpose
Guide new team members through the onboarding process.

## Required behavior
* Provide orientation to project tools and processes
* Explain governance and compliance requirements
* Set up development environment
* Assign initial tasks and mentorship
* Track onboarding progress
        """,
    ),
    SkillEntry(
        slug="release-pilot",
        name="Release Pilot",
        description="Manage the release process and ensure successful deployments.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "release", "deployment"],
        body="""
# Release Pilot

## Purpose
Manage the release process and ensure successful deployments.

## Required behavior
* Coordinate release activities and timelines
* Ensure all quality gates are met
* Manage release artifacts and documentation
* Handle rollback procedures if needed
* Communicate release status to stakeholders
        """,
    ),
]
