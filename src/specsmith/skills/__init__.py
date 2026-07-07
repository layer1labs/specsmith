# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith Skills — modular agent skill catalog.

Architecture
------------
Every skill is a ``SkillEntry`` belonging to a ``SkillDomain``.  Skills live in
domain-specific sub-modules that are imported lazily the first time the catalog
is accessed.  The public API mirrors the original ``specsmith.skills`` module so
existing code continues to work without changes.

Domain modules
~~~~~~~~~~~~~~
  governance        — project governance, verification, review, release workflows
  specsmith_skills  — specsmith self-referential skills (save, audit, reference)
  embedded          — RTOS/BSP: Zephyr, Yocto, FreeRTOS, NuttX, Buildroot, Azure RTOS …
  hardware          — EDA: KiCad, Altium, Vivado, Quartus, GTKWave, OpenOCD, JTAG
  mobile            — iOS (Xcode/Swift/TestFlight), Android (Gradle/ADB), Flutter, RN
  cloud             — AWS CLI, Azure CLI, GCP, GitHub CLI (gh)
  devops            — Docker, Kubernetes, Terraform, CI/CD pipelines
  ssh               — SSH key management, remote-dev, WSL2
  cross_platform    — CMake/vcpkg/conan, package managers, cross-OS CI
  productivity      — Email, presentations, Gamma.ai, MS Office, LibreOffice
  corporate         — Budgets, project mgmt, HR, fundraising, marketing, sales, legal

Usage
~~~~~
  from specsmith.skills import search, get, install, CATALOG
  matches = search("zephyr")
  skill   = get("zephyr-rtos")
  specsmith.skills.install("ios-dev", Path("."))
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# ---------------------------------------------------------------------------
# Domain taxonomy
# ---------------------------------------------------------------------------

class SkillDomain(str, Enum):
    """Top-level grouping for all skill entries."""

    GOVERNANCE = "governance"
    EMBEDDED = "embedded"
    HARDWARE = "hardware"
    MOBILE = "mobile"
    CLOUD = "cloud"
    DEVOPS = "devops"
    SSH = "ssh"
    CROSS_PLATFORM = "cross-platform"
    PRODUCTIVITY = "productivity"
    CORPORATE = "corporate"
    DOCS = "docs"  # documentation systems — H23/H24
    # New domains
    AI_AGENTS = "ai-agents"  # LLM/agent development, RAG, MCP, MLOps
    SOFTWARE_ENGINEERING = "software-engineering"  # code review, TDD, debugging, security
    WEB_BACKEND = "web-backend"  # frontend, REST, GraphQL, databases, caching
    DATA_ENGINEERING = "data-engineering"  # ETL, dbt, Spark, data quality
    PLATFORM_ENGINEERING = "platform-engineering"  # K8s, observability, GitOps, secrets


# ---------------------------------------------------------------------------
# Base entry
# ---------------------------------------------------------------------------


@dataclass
class SkillEntry:
    """A single skill catalog entry.

    Attributes
    ----------
    slug:
        URL-safe identifier used as filename (``<slug>.md``).
    name:
        Human-readable display name shown in ``specsmith skill list``.
    description:
        One-sentence summary shown in search results.
    domain:
        Which :class:`SkillDomain` this belongs to.
    tags:
        Free-text search tokens (OS, tool names, workflow verbs …).
    project_types:
        ``ProjectType`` values this skill applies to.  Empty list = all types.
    platforms:
        ``"windows"``, ``"linux"``, ``"macos"`` this skill is relevant for.
        Empty list = all platforms.
    prerequisites:
        Executables / packages that must exist before the skill runs
        (surfaced by ``specsmith doctor`` if missing).
    body:
        Markdown SKILL.md content written to disk by ``install()``.

    """

    slug: str
    name: str
    description: str
    domain: SkillDomain
    tags: list[str] = field(default_factory=list)
    project_types: list[str] = field(default_factory=list)
    platforms: list[str] = field(default_factory=list)
    prerequisites: list[str] = field(default_factory=list)
    body: str = ""


# ---------------------------------------------------------------------------
# Lazy-loaded registry
# ---------------------------------------------------------------------------

_CATALOG: list[SkillEntry] | None = None


def _build_catalog() -> list[SkillEntry]:
    """Import every domain module and concatenate their SKILLS lists."""
    from specsmith.skills import (  # noqa: PLC0415
        ai_agents,
        cloud,
        corporate,
        cross_platform,
        data_engineering,
        devops,
        docs,
        embedded,
        governance,
        hardware,
        mobile,
        platform_engineering,
        productivity,
        software_engineering,
        specsmith_core_commands,
        # specsmith_operations,  # unused import
        specsmith_skills,
        ssh,
        web_backend,
    )

    entries = (
        governance.SKILLS
        + embedded.SKILLS
        + hardware.SKILLS
        + mobile.SKILLS
        + cloud.SKILLS
        + devops.SKILLS
        + ssh.SKILLS
        + cross_platform.SKILLS
        + productivity.SKILLS
        + corporate.SKILLS
        + docs.SKILLS
        + specsmith_skills.SKILLS
        + specsmith_core_commands.SKILLS
        # New domains
        + ai_agents.SKILLS
        + software_engineering.SKILLS
        + web_backend.SKILLS
        + data_engineering.SKILLS
        + platform_engineering.SKILLS
    )
    by_slug: dict[str, SkillEntry] = {}
    for entry in entries:
        by_slug[entry.slug] = entry
    return list(by_slug.values())


def _get_catalog() -> list[SkillEntry]:
    """Return the full catalog, building it on first call (lazy)."""
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = _build_catalog()
    return _CATALOG


# ---------------------------------------------------------------------------
# Module-level CATALOG attribute — built lazily on first access via __getattr__
# ---------------------------------------------------------------------------
# ``skills.CATALOG`` and ``from specsmith.skills import CATALOG`` both work
# because __getattr__ is called for any name not found in the module namespace.


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def search(query: str, *, domain: SkillDomain | None = None) -> list[SkillEntry]:
    """Case-insensitive search across slug, name, description, and tags.

    Parameters
    ----------
    query:
        Search string (empty = return all entries, or filtered by domain).
    domain:
        Optional :class:`SkillDomain` to restrict results.

    """
    catalog = _get_catalog()
    needle = query.strip().lower()
    if not needle:
        return catalog
    if domain is not None:
        catalog = [entry for entry in catalog if entry.domain == domain]
    matches = []
    for entry in catalog:
        if needle in entry.slug.lower() or needle in entry.name.lower() or needle in entry.description.lower() or any(needle in tag.lower() for tag in entry.tags):
            matches.append(entry)
    return matches


def get(slug: str) -> SkillEntry | None:
    """Return a skill by slug, or None if not found."""
    catalog = _get_catalog()
    for entry in catalog:
        if entry.slug == slug:
            return entry
    return None


def by_domain(domain: SkillDomain) -> list[SkillEntry]:
    """Return all skills in a domain."""
    catalog = _get_catalog()
    return [entry for entry in catalog if entry.domain == domain]


def installed_skills(project_dir: Path) -> list[Path]:
    """Return list of installed skill files in the project."""
    # from specsmith.skills import get as get_skill  # Unused import

    skills_dir = project_dir / ".agents" / "skills"
    if not skills_dir.exists():
        return []
    installed = []
    for path in skills_dir.rglob("*.md"):
        # Skip subdirectory format (e.g., "ai-agents/xyz.md")
        if path.parent.name != "skills":
            continue
        installed.append(path)
    return installed


def install(slug: str, project_dir: Path, *, force: bool = False) -> Path:
    """Install a skill into the project's .agents/skills/ directory.

    Parameters
    ----------
    slug:
        The skill slug to install.
    project_dir:
        The project root directory.
    force:
        If True, overwrite existing files.

    Returns
    -------
    Path:
        The path to the installed skill file.

    Raises
    ------
    KeyError:
        If the skill slug is not found in the catalog.

    """
    from specsmith.skills import get as get_skill

    skill = get_skill(slug)
    if skill is None:
        raise KeyError(f"Skill {slug!r} not found in catalog")
    skills_dir = project_dir / ".agents" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    # Use subdirectory format for domain-specific skills
    skill_dir = skills_dir / skill.domain.value
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_path = skill_dir / f"{skill.slug}.md"
    if not force and skill_path.exists():
        raise FileExistsError(f"Skill {slug!r} already installed at {skill_path}")
    skill_path.write_text(skill.body)
    return skill_path


def __getattr__(name: str) -> object:
    """Lazy-load the catalog on first access to any attribute."""
    if name == "CATALOG":
        return _get_catalog()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
