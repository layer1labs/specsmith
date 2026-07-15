# SPDX-License-Identifier: MIT
"""Install, validate, and remove portable Specsmith assets for Zoo Code."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import click

MARKER = "specsmith-zoo-assets:v2"
OLD_MARKER = "specsmith-zoo-assets:v1"
MANIFEST = ".specsmith-zoo-code-assets.json"
PROJECT_MANIFEST = ".roo/.specsmith-zoo-code.json"
Scope = Literal["both", "global", "project"]


def managed(title: str, body: str) -> str:
    return f"<!-- {MARKER} -->\n# {title}\n\n{body}\n"


def command(description: str, body: str, mode: str) -> str:
    return (
        "---\n"
        f"description: {description}\n"
        f"mode: {mode}\n"
        "---\n\n"
        f"<!-- {MARKER} -->\n"
        f"{body}\n"
    )


def skill(name: str, description: str, body: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"<!-- {MARKER} -->\n\n"
        f"# {name}\n\n{body}\n"
    )


_RULES = {
    "rules/00-specsmith-source-of-truth.md": (
        "Specsmith source of truth",
        "Treat repository files, Specsmith requirements, evidence, checks, traces, "
        "and ledger artifacts as authoritative. Verify before assuming and separate "
        "verified facts from assumptions.",
    ),
    "rules/10-specsmith-governance.md": (
        "Specsmith governance",
        "Anchor non-trivial work to requirements, constraints, acceptance criteria, "
        "evidence, and verification. Run governance preflight before implementation.",
    ),
    "rules/20-context-continuity.md": (
        "Context continuity",
        "Preserve active work items, decisions, constraints, evidence, risks, changed "
        "files, and the next verification step before condensation or handoff.",
    ),
    "rules/30-security-and-secrets.md": (
        "Secrets and safety",
        "Never expose, commit, or echo secrets. Treat destructive, privileged, and "
        "externally visible actions as explicit approval gates.",
    ),
    "rules/40-context-efficiency.md": (
        "Context efficiency",
        "Search before reading, batch related reads, avoid duplicate context, and "
        "optimize for tokens per verified correct result rather than raw token count.",
    ),
    "rules-architect/10-planning.md": (
        "Architect planning",
        "Define scope, invariants, interfaces, alternatives, risks, acceptance criteria, "
        "and verification before authorizing implementation.",
    ),
    "rules-ask/10-evidence-answers.md": (
        "Evidence-grounded answers",
        "Answer from inspected evidence. Label inference and uncertainty and do not "
        "present guesses as verified project facts.",
    ),
    "rules-code/10-implementation-verification.md": (
        "Governed implementation",
        "Implement only accepted scope, preserve unrelated behavior, run focused "
        "checks, and record evidence before claiming completion.",
    ),
    "rules-debug/10-debug-evidence.md": (
        "Evidence-driven debugging",
        "Reproduce first, form falsifiable hypotheses, inspect focused evidence, and "
        "verify the fix against the original failure and regressions.",
    ),
    "rules-orchestrator/10-specsmith-boomerang.md": (
        "Specsmith orchestration",
        "Delegate bounded tasks with explicit inputs and return contracts. Verify "
        "returned work before accepting dependent actions.",
    ),
    "rules-reviewer/10-review-readiness.md": (
        "Review readiness",
        "Review against requirements, tests, security constraints, and prior decisions. "
        "The authoring model must not be the sole approver.",
    ),
}

_COMMANDS = {
    "commands/specsmith-intake.md": (
        "Start governed work",
        "Identify the outcome, requirements, constraints, ambiguity, evidence, and "
        "smallest bounded work item. Run preflight before edits.",
        "orchestrator",
    ),
    "commands/specsmith-plan.md": (
        "Plan governed work",
        "Create a requirement-linked plan with file scope, risks, tests, and objective "
        "completion criteria.",
        "architect",
    ),
    "commands/specsmith-implement.md": (
        "Implement governed work",
        "Implement accepted scope only, run focused verification, and report evidence, "
        "changed files, and residual risk.",
        "code",
    ),
    "commands/specsmith-debug.md": (
        "Debug with evidence",
        "Reproduce, rank falsifiable hypotheses, gather evidence, apply the smallest "
        "supported fix, and rerun regression checks.",
        "debug",
    ),
    "commands/specsmith-review.md": (
        "Review governed work",
        "Independently review requirement coverage, correctness, regressions, security, "
        "tests, and unsupported claims.",
        "reviewer",
    ),
    "commands/specsmith-checkpoint.md": (
        "Create a durable checkpoint",
        "Preserve active work, facts, assumptions, decisions, files, checks, risks, and "
        "the exact next action.",
        "orchestrator",
    ),
}

_SKILLS = {
    "skills/specsmith-governed-work/SKILL.md": (
        "specsmith-governed-work",
        "Run requirement-bound engineering work through Specsmith governance.",
        "Perform checkpoint, phase and requirement reads, preflight, bounded edits, "
        "verification, and trace sealing.",
    ),
    "skills/specsmith-evidence-debugging/SKILL.md": (
        "specsmith-evidence-debugging",
        "Debug with reproduction evidence and falsifiable hypotheses.",
        "Require reproduction, focused probes, a bounded fix, and regression verification.",
    ),
    "skills/specsmith-context-continuity/SKILL.md": (
        "specsmith-context-continuity",
        "Preserve critical state across condensation and handoff.",
        "Preserve scope, decisions, evidence, risks, changed files, checks, and next "
        "actions without speculative filler.",
    ),
}

GLOBAL = {path: managed(*value) for path, value in _RULES.items()}
GLOBAL.update({path: command(*value) for path, value in _COMMANDS.items()})
GLOBAL.update({path: skill(*value) for path, value in _SKILLS.items()})
LEGACY_PROJECT = {
    path: text.replace(f"<!-- {MARKER} -->\n", "", 1)
    for path, text in GLOBAL.items()
    if path.startswith("rules")
}

MCP: dict[str, Any] = {
    "command": "specsmith",
    "args": ["mcp", "serve", "--project-dir", "."],
    "env": {
        "SPECSMITH_ALLOW_NON_PIPX": "1",
        "SPECSMITH_NO_AUTO_UPDATE": "1",
        "SPECSMITH_PYPI_CHECKED": "1",
    },
}


@dataclass
class Result:
    changed: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    backups: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add(self, other: Result) -> None:
        for name in ("changed", "removed", "backups", "preserved", "errors"):
            getattr(self, name).extend(getattr(other, name))


class ZooCodeAssets:
    """Manage Specsmith-owned Zoo Code assets and project MCP state."""

    def __init__(
        self,
        project: Path,
        global_roo: Path,
        dry_run: bool = False,
        preserve_existing: bool = False,
    ) -> None:
        self.project = project.expanduser().resolve()
        self.global_roo = global_roo.expanduser().resolve()
        self.dry_run = dry_run
        self.preserve_existing = preserve_existing

    def setup(self, scope: Scope = "both") -> Result:
        return self._run(scope, self._setup_global, self._setup_project)

    def doctor(self, scope: Scope = "both") -> Result:
        return self._run(scope, self._doctor_global, self._doctor_project)

    def uninstall(self, scope: Scope = "both") -> Result:
        return self._run(scope, self._uninstall_global, self._uninstall_project)

    @staticmethod
    def _run(scope: Scope, global_action: Any, project_action: Any) -> Result:
        result = Result()
        if scope in {"both", "global"}:
            result.add(global_action())
        if scope in {"both", "project"}:
            result.add(project_action())
        return result

    def _is_managed(self, path: Path) -> bool:
        if not path.is_file():
            return False
        text = path.read_text(encoding="utf-8")
        return MARKER in text or OLD_MARKER in text

    def _write(self, path: Path, text: str) -> None:
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def _write_json(self, path: Path, data: dict[str, Any]) -> None:
        self._write(path, json.dumps(data, indent=2, sort_keys=True) + "\n")

    def _read_json(self, path: Path, result: Result) -> dict[str, Any] | None:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            result.errors.append(f"invalid JSON in {path}: {exc}")
            return None
        if not isinstance(data, dict):
            result.errors.append(f"JSON root must be an object: {path}")
            return None
        return data

    def _manifest(self) -> dict[str, Any]:
        result = Result()
        data = self._read_json(self.global_roo / MANIFEST, result)
        return data or {}

    def _remove(self, path: Path) -> None:
        if not self.dry_run:
            path.unlink(missing_ok=True)

    def _backup(self, path: Path) -> Path:
        suffix = ".before-specsmith-zoo-code"
        backup = path.with_name(path.name + suffix)
        index = 1
        while backup.exists():
            backup = path.with_name(path.name + f"{suffix}.{index}")
            index += 1
        if not self.dry_run:
            shutil.copy2(path, backup)
        return backup

    def _setup_global(self) -> Result:
        result = Result()
        old_files = set(self._manifest().get("files", []))
        for relative in sorted(old_files - set(GLOBAL)):
            path = self.global_roo / relative
            if self._is_managed(path):
                self._remove(path)
                result.removed.append(f"global:{relative}")
            elif path.exists():
                result.preserved.append(f"global:{relative}")

        for relative, expected in GLOBAL.items():
            path = self.global_roo / relative
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current is not None and current != expected and not self._is_managed(path):
                if self.preserve_existing:
                    result.preserved.append(f"global:{relative}")
                    result.errors.append(f"reserved path is unmanaged: {path}")
                    continue
                result.backups.append(str(self._backup(path)))
            if current != expected:
                self._write(path, expected)
                result.changed.append(f"global:{relative}")

        self._write_json(
            self.global_roo / MANIFEST,
            {"schema": 2, "files": sorted(GLOBAL)},
        )
        return result

    def _setup_project(self) -> Result:
        result = Result()
        for relative, legacy in LEGACY_PROJECT.items():
            path = self.project / ".roo" / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if MARKER in text or OLD_MARKER in text or text == legacy:
                self._remove(path)
                result.removed.append(f"project:.roo/{relative}")
            else:
                result.preserved.append(f"project:.roo/{relative}")

        mcp_path = self.project / ".roo" / "mcp.json"
        data = self._read_json(mcp_path, result)
        if data is None:
            return result
        servers = data.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            result.errors.append(f"mcpServers must be an object: {mcp_path}")
            return result
        if servers.get("specsmith-governance") != MCP:
            servers["specsmith-governance"] = MCP
            self._write_json(mcp_path, data)
            result.changed.append("project:.roo/mcp.json")
        self._write_json(
            self.project / PROJECT_MANIFEST,
            {"schema": 2, "mcp_server": MCP},
        )
        return result

    def _doctor_global(self) -> Result:
        result = Result()
        for relative, expected in GLOBAL.items():
            path = self.global_roo / relative
            if not path.is_file():
                result.errors.append(f"missing global asset: {path}")
            elif path.read_text(encoding="utf-8") != expected:
                result.errors.append(f"mismatched global asset: {path}")
        if set(self._manifest().get("files", [])) != set(GLOBAL):
            result.errors.append(f"missing or stale manifest: {self.global_roo / MANIFEST}")
        return result

    def _doctor_project(self) -> Result:
        result = Result()
        for relative, legacy in LEGACY_PROJECT.items():
            path = self.project / ".roo" / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if MARKER in text or OLD_MARKER in text or text == legacy:
                result.errors.append(f"generic asset duplicated in workspace: {path}")

        data = self._read_json(self.project / ".roo" / "mcp.json", result)
        if data is not None:
            servers = data.get("mcpServers")
            if not isinstance(servers, dict) or servers.get("specsmith-governance") != MCP:
                result.errors.append("Specsmith MCP server is missing or mismatched")
        return result

    def _uninstall_global(self) -> Result:
        result = Result()
        candidates = set(self._manifest().get("files", [])) | set(GLOBAL)
        for relative in sorted(candidates):
            path = self.global_roo / relative
            if self._is_managed(path):
                self._remove(path)
                result.removed.append(f"global:{relative}")
            elif path.exists():
                result.preserved.append(f"global:{relative}")
        manifest = self.global_roo / MANIFEST
        if manifest.exists():
            self._remove(manifest)
            result.removed.append(f"global:{MANIFEST}")
        return result

    def _uninstall_project(self) -> Result:
        result = Result()
        path = self.project / ".roo" / "mcp.json"
        data = self._read_json(path, result)
        if data is not None:
            servers = data.get("mcpServers")
            if isinstance(servers, dict) and servers.get("specsmith-governance") == MCP:
                del servers["specsmith-governance"]
                self._write_json(path, data)
                result.changed.append("project:.roo/mcp.json")
            elif isinstance(servers, dict) and "specsmith-governance" in servers:
                result.preserved.append("project:.roo/mcp.json#specsmith-governance")
        manifest = self.project / PROJECT_MANIFEST
        if manifest.exists():
            self._remove(manifest)
            result.removed.append(f"project:{PROJECT_MANIFEST}")
        return result


def global_root(value: Path | None) -> Path:
    configured = os.environ.get("ROO_GLOBAL_DIR")
    return value or (Path(configured) if configured else Path.home() / ".roo")


def emit(action: str, result: Result, dry_run: bool = False) -> None:
    prefix = "would " if dry_run else ""
    click.echo(
        f"Zoo Code {action}: {prefix}changed={len(result.changed)} "
        f"removed={len(result.removed)} backups={len(result.backups)} "
        f"preserved={len(result.preserved)} errors={len(result.errors)}"
    )
    for item in result.backups:
        click.echo(f"backup: {item}")
    for item in result.preserved:
        click.echo(f"preserved: {item}")
    for item in result.errors:
        click.echo(f"error: {item}", err=True)


def manager(
    project: Path,
    global_roo: Path | None,
    dry_run: bool,
    preserve: bool,
) -> ZooCodeAssets:
    return ZooCodeAssets(project, global_root(global_roo), dry_run, preserve)


@click.command("setup")
@click.option("--project-dir", default=".", type=click.Path(path_type=Path), show_default=True)
@click.option("--global-roo", type=click.Path(path_type=Path), default=None)
@click.option("--scope", type=click.Choice(["both", "global", "project"]), default="both")
@click.option("--dry-run", is_flag=True)
@click.option("--preserve-existing", is_flag=True)
def setup(
    project_dir: Path,
    global_roo: Path | None,
    scope: Scope,
    dry_run: bool,
    preserve_existing: bool,
) -> None:
    """Install or migrate reusable Specsmith Zoo Code assets."""
    result = manager(project_dir, global_roo, dry_run, preserve_existing).setup(scope)
    emit("setup", result, dry_run)
    if not result.ok:
        raise SystemExit(2)


@click.command("doctor")
@click.option("--project-dir", default=".", type=click.Path(path_type=Path), show_default=True)
@click.option("--global-roo", type=click.Path(path_type=Path), default=None)
@click.option("--scope", type=click.Choice(["both", "global", "project"]), default="both")
def doctor(project_dir: Path, global_roo: Path | None, scope: Scope) -> None:
    """Validate global assets, workspace deduplication, and MCP configuration."""
    result = manager(project_dir, global_roo, False, True).doctor(scope)
    emit("doctor", result)
    if not result.ok:
        raise SystemExit(2)


@click.command("uninstall")
@click.option("--project-dir", default=".", type=click.Path(path_type=Path), show_default=True)
@click.option("--global-roo", type=click.Path(path_type=Path), default=None)
@click.option("--scope", type=click.Choice(["both", "global", "project"]), default="both")
@click.option("--dry-run", is_flag=True)
def uninstall(
    project_dir: Path,
    global_roo: Path | None,
    scope: Scope,
    dry_run: bool,
) -> None:
    """Remove only files and MCP state managed by this integration."""
    result = manager(project_dir, global_roo, dry_run, True).uninstall(scope)
    emit("uninstall", result, dry_run)
    if not result.ok:
        raise SystemExit(2)


def register_zoo_code_asset_commands() -> None:
    """Attach lifecycle commands to the existing Zoo Code command group."""
    from specsmith.commands.zoo_code import zoo_code_group

    for item in (setup, doctor, uninstall):
        if item.name not in zoo_code_group.commands:
            zoo_code_group.add_command(item)
