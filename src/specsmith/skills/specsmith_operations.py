# SPDX-License-Identifier: MIT
"""Specsmith operation skills - skills for using specsmith save, push, and load commands."""

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
]
