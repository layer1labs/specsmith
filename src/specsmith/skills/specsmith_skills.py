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

from specsmith.skills import SkillEntry

SKILLS: list[SkillEntry] = []
