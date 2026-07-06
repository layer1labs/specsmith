# SPDX-License-Identifier: MIT
"""Specsmith core command skills - comprehensive skills for all major specsmith commands."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS = [
    SkillEntry(
        slug="specsmith-save",
        name="Specsmith Save",
        description="Save changes through Specsmith, not raw git.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "save", "commit", "specsmith"],
        body="""
# Specsmith Save

## Purpose
Save changes through Specsmith, not raw git.

## Required behavior
* Always use `specsmith save` instead of raw git commands
* Ensure all changes are properly recorded in the Specsmith trace
* Run preflight checks before saving
* Maintain proper commit messages with work item references
* Follow the governed agent loop for all save operations
        """,
    ),
    SkillEntry(
        slug="specsmith-push",
        name="Specsmith Push",
        description="Push changes with Specsmith safety checks.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "push", "commit", "specsmith"],
        body="""
# Specsmith Push

## Purpose
Push changes with Specsmith safety checks.

## Required behavior
* Always use `specsmith push` instead of raw git push
* Run preflight checks before pushing
* Ensure all changes are properly audited
* Follow the governed agent loop for all push operations
* Override safety checks only when explicitly required
        """,
    ),
    SkillEntry(
        slug="specsmith-load",
        name="Specsmith Load",
        description="Load governance state from remote or backup.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "load", "restore", "specsmith"],
        body="""
# Specsmith Load

## Purpose
Load governance state from remote or backup.

## Required behavior
* Always use `specsmith load` instead of raw git pull
* Ensure proper synchronization with remote repository
* Restore ESDB from backup when specified
* Follow the governed agent loop for all load operations
* Validate that loaded state is consistent
        """,
    ),
    SkillEntry(
        slug="specsmith-audit",
        name="Specsmith Audit",
        description="Audit changes and ensure compliance with governance standards.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "audit", "compliance", "verification"],
        body="""
# Specsmith Audit

## Purpose
Audit changes and ensure compliance with governance standards.

## Required behavior
* Run `specsmith audit` to verify compliance
* Check that all requirements are met
* Ensure all tests pass
* Verify that preflight decisions are properly recorded
* Validate that governance rules are followed
        """,
    ),
    SkillEntry(
        slug="specsmith-commit",
        name="Specsmith Commit",
        description="Stage, audit, and commit with governance-aware message.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "commit", "git", "specsmith"],
        body="""
# Specsmith Commit

## Purpose
Stage, audit, and commit with governance-aware message.

## Required behavior
* Run `specsmith commit` instead of raw git commit
* Ensure all changes are properly audited before committing
* Use governance-aware commit messages
* Follow the governed agent loop for all commit operations
* Maintain proper traceability of changes
        """,
    ),
    SkillEntry(
        slug="specsmith-init",
        name="Specsmith Init",
        description="Scaffold a new governed project.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "init", "project", "setup"],
        body="""
# Specsmith Init

## Purpose
Scaffold a new governed project.

## Required behavior
* Run `specsmith init` to create a new governed project
* Follow all Specsmith governance rules during initialization
* Ensure proper project structure and documentation
* Set up governance files and configurations
* Validate that the project is properly configured for governance
        """,
    ),
    SkillEntry(
        slug="specsmith-apply",
        name="Specsmith Apply",
        description="Regenerate CI and agent files from current configuration.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "apply", "configuration", "automation"],
        body="""
# Specsmith Apply

## Purpose
Regenerate CI and agent files from current configuration.

## Required behavior
* Run `specsmith apply` to regenerate configuration files
* Ensure all generated files comply with governance standards
* Maintain consistency between configuration and governance rules
* Validate that generated files are properly formatted
        """,
    ),
    SkillEntry(
        slug="specsmith-sync",
        name="Specsmith Sync",
        description="Sync .specsmith/ machine state from docs/ Markdown.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "sync", "state", "configuration"],
        body="""
# Specsmith Sync

## Purpose
Sync .specsmith/ machine state from docs/ Markdown.

## Required behavior
* Run `specsmith sync` to synchronize governance state
* Ensure consistency between documentation and machine state
* Maintain proper governance compliance during sync operations
* Validate that all sync operations are properly recorded
        """,
    ),
    SkillEntry(
        slug="specsmith-validate",
        name="Specsmith Validate",
        description="Check governance file consistency (req ↔ test ↔ spec).",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "validate", "consistency", "compliance"],
        body="""
# Specsmith Validate

## Purpose
Check governance file consistency (req ↔ test ↔ spec).

## Required behavior
* Run `specsmith validate` to check file consistency
* Ensure requirements, tests, and specifications are aligned
* Identify and report any inconsistencies in governance files
* Follow governance rules during validation
        """,
    ),
    SkillEntry(
        slug="specsmith-phase",
        name="Specsmith Phase",
        description="Track and advance the AEE workflow phase for a project.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "phase", "workflow", "aee"],
        body="""
# Specsmith Phase

## Purpose
Track and advance the AEE workflow phase for a project.

## Required behavior
* Run `specsmith phase` to check current workflow phase
* Follow proper phase advancement procedures
* Ensure all requirements are met for phase advancement
* Maintain proper governance documentation for each phase
        """,
    ),
    SkillEntry(
        slug="specsmith-esdb",
        name="Specsmith ESDB",
        description="Manage the ESDB (Epistemic State Database).",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "esdb", "database", "state"],
        body="""
# Specsmith ESDB

## Purpose
Manage the ESDB (Epistemic State Database).

## Required behavior
* Run `specsmith esdb` commands to manage the epistemic state database
* Ensure proper governance compliance when managing ESDB
* Maintain data integrity and security
* Follow proper backup and restore procedures
        """,
    ),
    SkillEntry(
        slug="specsmith-trace",
        name="Specsmith Trace",
        description="Manage the cryptographic trace vault (STP-inspired).",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "trace", "cryptographic", "vault"],
        body="""
# Specsmith Trace

## Purpose
Manage the cryptographic trace vault (STP-inspired).

## Required behavior
* Run `specsmith trace` commands to manage cryptographic traces
* Ensure all trace operations follow governance rules
* Maintain proper cryptographic security practices
* Follow traceability requirements for all operations
        """,
    ),
    SkillEntry(
        slug="specsmith-session",
        name="Specsmith Session",
        description="Session lifecycle management.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "session", "lifecycle", "agent"],
        body="""
# Specsmith Session

## Purpose
Session lifecycle management.

## Required behavior
* Run `specsmith session` commands to manage agent sessions
* Follow proper session lifecycle procedures
* Ensure all session operations are properly governed
* Maintain session state and traceability
        """,
    ),
    SkillEntry(
        slug="specsmith-workflow",
        name="Specsmith Workflow",
        description="Record, list, and run parameterised command snippets.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "workflow", "automation", "commands"],
        body="""
# Specsmith Workflow

## Purpose
Record, list, and run parameterised command snippets.

## Required behavior
* Run `specsmith workflow` to manage command workflows
* Ensure all workflows follow governance rules
* Maintain proper documentation of workflows
* Validate that workflows execute correctly
        """,
    ),
    SkillEntry(
        slug="specsmith-wi",
        name="Specsmith Work Item",
        description="Manage the lifecycle of Work Items (WIs).",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "work-item", "wi", "tracking"],
        body="""
# Specsmith Work Item

## Purpose
Manage the lifecycle of Work Items (WIs).

## Required behavior
* Run `specsmith wi` commands to manage work items
* Follow proper work item lifecycle procedures
* Ensure all work items are properly tracked and governed
* Maintain traceability of work item progress
        """,
    ),
    SkillEntry(
        slug="specsmith-req",
        name="Specsmith Requirements",
        description="Manage requirements.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "requirements", "req", "tracking"],
        body="""
# Specsmith Requirements

## Purpose
Manage requirements.

## Required behavior
* Run `specsmith req` commands to manage requirements
* Follow proper requirements management procedures
* Ensure all requirements are properly documented and tracked
* Maintain traceability between requirements and tests
        """,
    ),
    SkillEntry(
        slug="specsmith-test",
        name="Specsmith Tests",
        description="Manage test cases.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "tests", "test", "verification"],
        body="""
# Specsmith Tests

## Purpose
Manage test cases.

## Required behavior
* Run `specsmith test` commands to manage test cases
* Follow proper test case management procedures
* Ensure all tests are properly documented and linked to requirements
* Maintain test coverage and quality
        """,
    ),
    SkillEntry(
        slug="specsmith-compliance",
        name="Specsmith Compliance",
        description="EU and North American AI regulation compliance.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "compliance", "ai", "regulation"],
        body="""
# Specsmith Compliance

## Purpose
EU and North American AI regulation compliance.

## Required behavior
* Run `specsmith compliance` to check AI regulation compliance
* Ensure all AI-related activities follow applicable regulations
* Maintain proper documentation of compliance measures
* Report compliance status as required
        """,
    ),
]
