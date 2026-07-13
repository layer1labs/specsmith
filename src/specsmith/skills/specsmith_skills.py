# SPDX-License-Identifier: MIT
"""Specsmith self-referential skills -- how to USE specsmith in any project.

These skills teach AI agents (Warp, Claude Code, Codex, Cursor, etc.) the
core specsmith governance workflows. Install in any project via:

    specsmith skill install specsmith
    specsmith skill install specsmith-save
    specsmith skill install specsmith-audit
    specsmith skill install specsmith-session-governance
    specsmith skill install preflight-gate

NOTE: The canonical ``specsmith``, ``specsmith-save``, ``specsmith-audit``,
``specsmith-session-governance``, and related operational skill entries live
in ``governance.py``.  This module is intentionally empty so the deduplicated
catalog (``_build_catalog`` in ``__init__.py``) does not silently shadow the
richer ``governance.py`` bodies.

To add *new* non-duplicate specsmith skills with unique slugs, add them here.
The entries that previously lived here (slug="specsmith", "specsmith-save",
"specsmith-audit") were removed in v0.17.0 -- see governance.py for the
canonical, fully-featured versions.
"""

from __future__ import annotations

from specsmith.skills import SkillDomain, SkillEntry

SKILLS = [
    SkillEntry(
        slug="specsmith",
        name="Specsmith Governance",
        description="Core Specsmith governance workflows and compliance.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "specsmith", "compliance"],
        body="""
# Specsmith Governance

## Purpose
Core Specsmith governance workflows and compliance.

## Required behavior
* Follow all Specsmith governance rules and processes
* Ensure compliance with project standards and requirements
* Maintain proper governance documentation and traceability
* Run preflight checks before any significant changes
* Follow the governed agent loop execution model
        """,
    ),
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
        slug="specsmith-session-governance",
        name="Specsmith Session Governance",
        description="Govern session behavior and ensure proper governance compliance.",
        domain=SkillDomain.GOVERNANCE,
        tags=["governance", "session", "compliance", "execution"],
        body="""
# Specsmith Session Governance

## Purpose
Govern session behavior and ensure proper governance compliance.

## Required behavior
* Run session bootstrap procedures
* Emit governance anchor at session start
* Follow the governed agent loop execution model
* Ensure all actions are properly preflighted
* Maintain session state and traceability
        """,
    ),
]
