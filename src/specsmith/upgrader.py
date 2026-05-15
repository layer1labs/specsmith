# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Upgrader — update governance files to match a newer spec version."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import yaml
from jinja2 import Environment, PackageLoader, select_autoescape

from specsmith import __version__
from specsmith.config import ProjectConfig


@dataclass
class UpgradeResult:
    """Result of an upgrade operation."""

    updated_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    message: str = ""


# Governance templates that get regenerated on upgrade
_GOVERNANCE_TEMPLATES: list[tuple[str, str]] = [
    ("governance/rules.md.j2", "docs/governance/RULES.md"),
    ("governance/session-protocol.md.j2", "docs/governance/SESSION-PROTOCOL.md"),
    ("governance/lifecycle.md.j2", "docs/governance/LIFECYCLE.md"),
    ("governance/roles.md.j2", "docs/governance/ROLES.md"),
    ("governance/context-budget.md.j2", "docs/governance/CONTEXT-BUDGET.md"),
    ("governance/verification.md.j2", "docs/governance/VERIFICATION.md"),
    ("governance/drift-metrics.md.j2", "docs/governance/DRIFT-METRICS.md"),
]

# Migration: old lowercase filenames → new uppercase filenames
_LEGACY_RENAMES: list[tuple[str, str]] = [
    ("docs/governance/rules.md", "docs/governance/RULES.md"),
    ("docs/governance/workflow.md", "docs/governance/SESSION-PROTOCOL.md"),
    ("docs/governance/WORKFLOW.md", "docs/governance/SESSION-PROTOCOL.md"),
    ("docs/governance/roles.md", "docs/governance/ROLES.md"),
    ("docs/governance/context-budget.md", "docs/governance/CONTEXT-BUDGET.md"),
    ("docs/governance/verification.md", "docs/governance/VERIFICATION.md"),
    ("docs/governance/drift-metrics.md", "docs/governance/DRIFT-METRICS.md"),
    ("docs/architecture.md", "docs/ARCHITECTURE.md"),
]


def _get_env_and_ctx(
    config: ProjectConfig,
) -> tuple[Environment, dict[str, object]]:
    """Create Jinja env and template context from config."""
    from specsmith.phase import PHASE_MAP
    from specsmith.tools import get_tools

    env = Environment(
        loader=PackageLoader("specsmith", "templates"),
        autoescape=select_autoescape([]),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    # Phase context defaults — caller (run_upgrade) overrides with actual phase
    phase_key = "inception"
    phase_obj = PHASE_MAP[phase_key]
    ctx: dict[str, object] = {
        "project": config,
        "today": date.today().isoformat(),
        "package_name": config.package_name,
        "tools": get_tools(config),
        "aee_phase": phase_key,
        "aee_phase_label": phase_obj.label,
        "aee_phase_emoji": phase_obj.emoji,
    }
    return env, ctx


def run_upgrade(
    root: Path,
    *,
    target_version: str | None = None,
    full: bool = False,
) -> UpgradeResult:
    """Upgrade governance files to a newer spec version.

    Args:
        root: Project root directory.
        target_version: Target spec version. If None, uses the current specsmith version.
        full: If True, also regenerate exec shims, agent integrations, CI configs,
              and create missing community/RTD files. Safe: never overwrites
              AGENTS.md, LEDGER.md, REQUIREMENTS.md, TESTS.md, or user docs.

    Returns:
        UpgradeResult with details of the operation.
    """
    from specsmith.paths import find_scaffold

    scaffold_path = find_scaffold(root)

    if not scaffold_path or not scaffold_path.exists():
        return UpgradeResult(
            message=(
                "No scaffold config found (docs/SPECSMITH.yml or scaffold.yml)."
                " Cannot determine project configuration for upgrade."
            )
        )

    with open(scaffold_path) as f:
        raw = yaml.safe_load(f)

    try:
        config = ProjectConfig(**raw)
    except Exception as e:
        return UpgradeResult(message=f"Invalid scaffold.yml: {e}")

    new_version = target_version or __version__
    old_version = config.spec_version

    # For --full, allow syncing even when version matches
    if old_version == new_version and not full:
        return UpgradeResult(message=f"Already at spec version {new_version}. Nothing to upgrade.")

    config.spec_version = new_version
    env, ctx = _get_env_and_ctx(config)

    # Override phase context with actual project phase
    from specsmith.phase import PHASE_MAP, read_phase

    phase_key = read_phase(root)
    phase_obj = PHASE_MAP.get(phase_key, PHASE_MAP["inception"])
    ctx["aee_phase"] = phase_key
    ctx["aee_phase_label"] = phase_obj.label
    ctx["aee_phase_emoji"] = phase_obj.emoji

    result = UpgradeResult()

    # ESDB auto-migration: if .specsmith/ exists but .chronomemory/ does not,
    # migrate flat JSON to ChronoStore WAL automatically.
    specsmith_dir = root / ".specsmith"
    chronomemory_wal = root / ".chronomemory" / "events.wal"
    if specsmith_dir.is_dir() and not chronomemory_wal.exists():
        try:
            from specsmith.esdb.store import ChronoStore

            with ChronoStore(root) as store:
                counts = store.migrate_from_json(specsmith_dir)
            reqs_m = counts.get("requirements", 0)
            tests_m = counts.get("testcases", 0)
            if reqs_m + tests_m > 0:
                result.updated_files.append(
                    f".chronomemory/events.wal (migrated {reqs_m} reqs + {tests_m} tests from JSON)"
                )
        except Exception:  # noqa: BLE001
            pass  # Non-fatal — JSON fallback still works

    # Migrate legacy filenames (including WORKFLOW.md → SESSION-PROTOCOL.md)
    _migrate_legacy_filenames(root, result)

    # Remove obsolete docs/WORKFLOW.md (replaced by phase system + LIFECYCLE.md)
    obsolete_workflow = root / "docs" / "WORKFLOW.md"
    if obsolete_workflow.exists():
        obsolete_workflow.unlink()
        result.updated_files.append("docs/WORKFLOW.md (removed — replaced by LIFECYCLE.md)")

    # Regenerate governance templates (always overwritten — they're spec-managed).
    # REG-007: safe_overwrite creates a timestamped .bak before each write.
    from specsmith.safe_write import safe_overwrite as _safe_overwrite

    for template_name, output_rel in _GOVERNANCE_TEMPLATES:
        output_path = root / output_rel
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tmpl = env.get_template(template_name)
        content = tmpl.render(**ctx)
        _safe_overwrite(output_path, content, reason=f"upgrade {output_rel}")
        result.updated_files.append(output_rel)

    # Update scaffold config with new version (at canonical or legacy location)
    raw["spec_version"] = new_version
    with open(scaffold_path, "w") as f:
        yaml.dump(raw, f, default_flow_style=False, sort_keys=False)
    result.updated_files.append(str(scaffold_path.relative_to(root)))

    # Initialize credit tracking if not present
    specsmith_dir = root / ".specsmith"
    if not specsmith_dir.exists():
        from specsmith.credits import CreditBudget, save_budget

        save_budget(root, CreditBudget())
        result.updated_files.append(".specsmith/credit-budget.json")

    # Full sync: regenerate shims, CI, agent files, create missing community files
    if full:
        result.updated_files.extend(_sync_full(root, config, env, ctx))

    # Run pending migrations (versioned, auto-apply, droppable)
    # Drop path: remove migrations/ package + this block for v1.0 release
    try:
        from specsmith.migrations.runner import MigrationRunner

        runner = MigrationRunner(root)
        migration_results = runner.run_pending()
        for mr in migration_results:
            if mr.success and mr.files_created:
                result.updated_files.extend(
                    f"[migration v{mr.version}] {f}" for f in mr.files_created
                )
    except Exception:  # noqa: BLE001
        pass  # Migrations are non-critical

    result.message = (
        f"Upgraded from {old_version} to {new_version}. "
        f"{len(result.updated_files)} files updated, {len(result.skipped_files)} skipped."
    )

    return result


# Files that are NEVER overwritten by --full sync (user-owned content)
_USER_OWNED: set[str] = {
    "AGENTS.md",
    "LEDGER.md",
    "README.md",
    "docs/REQUIREMENTS.md",
    "docs/TESTS.md",
    "docs/ARCHITECTURE.md",
}


def _sync_full(
    root: Path,
    config: ProjectConfig,
    env: Environment,
    ctx: dict[str, object],
) -> list[str]:
    """Full sync: regenerate infrastructure files, create missing community files.

    Safe rules:
    - User-owned docs (AGENTS.md, LEDGER.md, etc.) are NEVER touched
    - Exec shims are ALWAYS regenerated (they carry security/abort logic)
    - CI configs are regenerated (tool-aware, reflects current specsmith version)
    - Agent integrations are regenerated
    - Community/RTD files are created only if missing
    """
    synced: list[str] = []

    from specsmith.scaffolder import _build_community_files

    # 1. Exec shims — always regenerate (carries PID tracking / abort fixes)
    shim_templates = [
        ("scripts/exec.cmd.j2", "scripts/exec.cmd"),
        ("scripts/exec.sh.j2", "scripts/exec.sh"),
        ("scripts/setup.cmd.j2", "scripts/setup.cmd"),
        ("scripts/setup.sh.j2", "scripts/setup.sh"),
        ("scripts/run.cmd.j2", "scripts/run.cmd"),
        ("scripts/run.sh.j2", "scripts/run.sh"),
    ]
    for tmpl_name, output_rel in shim_templates:
        out = root / output_rel
        out.parent.mkdir(parents=True, exist_ok=True)
        tmpl = env.get_template(tmpl_name)
        out.write_text(tmpl.render(**ctx), encoding="utf-8")
        synced.append(output_rel)

    # 2. Agent integrations — regenerate
    for integration_name in config.integrations:
        if integration_name == "agents-md":
            continue
        try:
            from specsmith.integrations import get_adapter

            adapter = get_adapter(integration_name)
            files = adapter.generate(config, root)
            for f in files:
                synced.append(str(f.relative_to(root)))
        except ValueError:
            pass

    # 3. VCS CI configs — create only if missing (never overwrite user CI)
    if config.vcs_platform:
        ci_exists = (
            (
                list((root / ".github" / "workflows").glob("*.yml"))
                if (root / ".github" / "workflows").is_dir()
                else []
            )
            or (root / ".gitlab-ci.yml").exists()
            or (root / "bitbucket-pipelines.yml").exists()
        )
        if not ci_exists:
            try:
                from specsmith.vcs import get_platform

                platform = get_platform(config.vcs_platform)
                files = platform.generate_all(config, root)
                for f in files:
                    synced.append(str(f.relative_to(root)) + " (created)")
            except ValueError:
                pass

    # 4. Community files — create only if missing
    for tmpl_name, output_rel in _build_community_files(config):
        out = root / output_rel
        if not out.exists():
            out.parent.mkdir(parents=True, exist_ok=True)
            tmpl = env.get_template(tmpl_name)
            out.write_text(tmpl.render(**ctx), encoding="utf-8")
            synced.append(f"{output_rel} (created)")

    # 5. Config files — create only if missing (.editorconfig, .gitattributes)
    config_templates = [
        ("editorconfig.j2", ".editorconfig"),
        ("gitattributes.j2", ".gitattributes"),
    ]
    for tmpl_name, output_rel in config_templates:
        out = root / output_rel
        if not out.exists():
            tmpl = env.get_template(tmpl_name)
            out.write_text(tmpl.render(**ctx), encoding="utf-8")
            synced.append(f"{output_rel} (created)")

    # 6. Essential docs — create stubs only if truly missing (check alternate paths)
    has_ledger = (root / "LEDGER.md").exists() or (root / "docs" / "LEDGER.md").exists()
    if not has_ledger:
        (root / "LEDGER.md").write_text("# Ledger\n\nNo entries yet.\n", encoding="utf-8")
        synced.append("LEDGER.md (created)")

    has_arch = (root / "docs" / "ARCHITECTURE.md").exists()
    if not has_arch and (root / "docs").is_dir():
        # Check subdirectories (e.g. docs/architecture/CPSC-RE-ARCHITECTURE.md)
        has_arch = bool(
            list((root / "docs").glob("**/architecture*"))
            + list((root / "docs").glob("**/ARCHITECTURE*"))
        )
    if not has_arch:
        try:
            from specsmith.architect import generate_architecture

            generate_architecture(root)
            synced.append("docs/ARCHITECTURE.md (generated from scan)")
        except Exception:  # noqa: BLE001
            arch_path = root / "docs" / "ARCHITECTURE.md"
            arch_path.parent.mkdir(parents=True, exist_ok=True)
            arch_path.write_text(
                f"# Architecture \u2014 {config.name}\n\n[Run `specsmith architect` to populate]\n",
                encoding="utf-8",
            )
            synced.append("docs/ARCHITECTURE.md (stub created)")
    specsmith_dir = root / ".specsmith"
    credit_budget = specsmith_dir / "credit-budget.json"
    if not credit_budget.exists():
        from specsmith.credits import CreditBudget, save_budget

        save_budget(root, CreditBudget())
        synced.append(".specsmith/credit-budget.json (created)")

    return synced


def _migrate_legacy_filenames(root: Path, result: UpgradeResult) -> None:
    """Rename legacy lowercase governance files to uppercase.

    Handles both case-sensitive (Linux) and case-insensitive (Windows/macOS)
    filesystems. On case-insensitive FS, uses a two-step rename via a
    temporary name to avoid conflicts.

    Also updates references in AGENTS.md so the hub links stay valid.
    """
    import shutil

    renamed: list[tuple[str, str]] = []

    for old_rel, new_rel in _LEGACY_RENAMES:
        old_path = root / old_rel
        new_path = root / new_rel
        if not old_path.exists():
            continue
        if old_path == new_path:
            continue  # Already correct
        # Case-insensitive FS: old and new resolve to the same inode.
        # Use a temp name to force the rename.
        if new_path.exists() and old_path.samefile(new_path):
            tmp_path = old_path.with_suffix(".md.migrating")
            shutil.move(str(old_path), str(tmp_path))
            shutil.move(str(tmp_path), str(new_path))
        elif not new_path.exists():
            new_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_path), str(new_path))
        else:
            continue  # Both exist as truly separate files — skip
        renamed.append((old_rel, new_rel))
        result.updated_files.append(f"{old_rel} → {new_rel}")

    # Update references in user-owned docs that point to renamed files
    if renamed:
        _update_references(root, renamed, result)


def _update_references(
    root: Path,
    renames: list[tuple[str, str]],
    result: UpgradeResult,
) -> None:
    """Rewrite old paths to new paths in AGENTS.md and other hub files.

    Only performs safe string replacement of exact path references.
    """
    docs_to_patch = [
        "AGENTS.md",
        "CLAUDE.md",
        "GEMINI.md",
        # Canonical post-0.5.0 path for the agent-skill adapter.
        ".agents/skills/SKILL.md",
        # Legacy path for projects scaffolded before 0.5.0 (still patched
        # so reference rewrites continue to work after rename).
        ".warp/skills/SKILL.md",
        ".cursor/rules/governance.mdc",
        ".windsurfrules",
        ".aider.conf.yml",
    ]

    for doc_name in docs_to_patch:
        doc_path = root / doc_name
        if not doc_path.exists():
            continue
        content = doc_path.read_text(encoding="utf-8")
        original = content
        for old_rel, new_rel in renames:
            content = content.replace(old_rel, new_rel)
        if content != original:
            doc_path.write_text(content, encoding="utf-8")
            result.updated_files.append(f"{doc_name} (references updated)")
