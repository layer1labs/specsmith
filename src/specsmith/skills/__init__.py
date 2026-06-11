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
        specsmith_skills,
        ssh,
        web_backend,
    )

    return (
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
        # New domains
        + ai_agents.SKILLS
        + software_engineering.SKILLS
        + web_backend.SKILLS
        + data_engineering.SKILLS
        + platform_engineering.SKILLS
    )


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
    results = (
        catalog
        if not needle
        else [
            e
            for e in catalog
            if needle in " ".join([e.slug, e.name, e.description, *e.tags]).lower()
        ]
    )
    if domain is not None:
        results = [e for e in results if e.domain == domain]
    return results


def get(slug: str) -> SkillEntry | None:
    """Return the catalog entry for *slug*, or ``None`` if not found."""
    for entry in _get_catalog():
        if entry.slug == slug:
            return entry
    return None


def by_domain(domain: SkillDomain) -> list[SkillEntry]:
    """Return all skills in *domain*, sorted by slug."""
    return sorted(
        (e for e in _get_catalog() if e.domain == domain),
        key=lambda e: e.slug,
    )


def by_project_type(project_type: str) -> list[SkillEntry]:
    """Return skills applicable to *project_type* (includes all-type skills)."""
    return [e for e in _get_catalog() if not e.project_types or project_type in e.project_types]


def installed_skills(project_dir: Path) -> list[Path]:
    """Return installed skill files under ``.agents/skills/`` (both flat and subdir formats)."""
    base = project_dir / ".agents" / "skills"
    if not base.is_dir():
        return []
    paths: list[Path] = []
    for item in sorted(base.iterdir()):
        if item.is_file() and item.suffix == ".md":  # legacy flat format
            paths.append(item)
        elif item.is_dir() and (item / "SKILL.md").exists():  # subdir format
            paths.append(item / "SKILL.md")
    return sorted(paths)


def install(slug: str, project_dir: Path, *, force: bool = False) -> Path:
    """Copy skill *slug* into ``<project_dir>/.agents/skills/<slug>/SKILL.md``.

    Raises
    ------
    KeyError
        Unknown slug.
    FileExistsError
        Already installed and ``force=False``.
    """
    entry = get(slug)
    if entry is None:
        raise KeyError(f"Unknown skill: {slug!r}")
    base = project_dir / ".agents" / "skills"
    base.mkdir(parents=True, exist_ok=True)
    # Subdirectory format: <slug>/SKILL.md (REQ-360)
    skill_dir = base / slug
    skill_dir.mkdir(exist_ok=True)
    target = skill_dir / "SKILL.md"
    if target.exists() and not force:
        raise FileExistsError(f"Already installed: {target}. Pass force=True to overwrite.")
    target.write_text(entry.body, encoding="utf-8")
    return target


# ---------------------------------------------------------------------------
# Back-compat: expose CATALOG as plain list (not property)
# ---------------------------------------------------------------------------
# Modules that do ``from specsmith.skills import CATALOG`` get this list.
# We populate it lazily on first module access via __getattr__.


def __getattr__(name: str) -> object:  # noqa: N807
    if name == "CATALOG":
        return _get_catalog()
    raise AttributeError(name)
