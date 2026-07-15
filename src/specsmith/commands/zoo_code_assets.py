# SPDX-License-Identifier: MIT
"""Portable Zoo Code integration lifecycle for Specsmith."""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal

import click

MARKER = "specsmith-zoo-assets:v2"
OLD_MARKER = "specsmith-zoo-assets:v1"
MANIFEST = ".specsmith-zoo-code-assets.json"
PROJECT_MANIFEST = ".roo/.specsmith-zoo-code.json"
Scope = Literal["both", "global", "project"]

RULES = {
    "rules/00-specsmith-source-of-truth.md": (
        "Specsmith source of truth",
        "Treat repository files, requirements, evidence, checks, traces, and ledger "
        "artifacts as authoritative. Verify before assuming.",
    ),
    "rules/10-specsmith-governance.md": (
        "Specsmith governance",
        "Anchor non-trivial work to requirements, constraints, acceptance criteria, "
        "evidence, and verification. Run preflight before implementation.",
    ),
    "rules/20-context-continuity.md": (
        "Context continuity",
        "Preserve work items, decisions, constraints, evidence, risks, changed files, "
        "and the next verification step before condensation or handoff.",
    ),
    "rules/30-security-and-secrets.md": (
        "Secrets and safety",
        "Never expose, commit, or echo secrets. Gate destructive, privileged, and "
        "externally visible actions.",
    ),
    "rules/40-context-efficiency.md": (
        "Context efficiency",
        "Search before reading, batch related reads, avoid duplicate context, and "
        "optimize for tokens per verified correct result.",
    ),
    "rules-architect/10-planning.md": (
        "Architect planning",
        "Define scope, invariants, interfaces, alternatives, risks, acceptance criteria, "
        "and verification before implementation.",
    ),
    "rules-ask/10-evidence-answers.md": (
        "Evidence-grounded answers",
        "Answer from inspected evidence. Label inference and uncertainty.",
    ),
    "rules-code/10-implementation-verification.md": (
        "Governed implementation",
        "Implement accepted scope only, preserve unrelated behavior, run focused "
        "checks, and record evidence.",
    ),
    "rules-debug/10-debug-evidence.md": (
        "Evidence-driven debugging",
        "Reproduce first, form falsifiable hypotheses, inspect focused evidence, and "
        "verify the fix and regressions.",
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

COMMANDS = {
    "commands/specsmith-intake.md": ("Start governed work", "orchestrator"),
    "commands/specsmith-plan.md": ("Plan governed work", "architect"),
    "commands/specsmith-implement.md": ("Implement governed work", "code"),
    "commands/specsmith-debug.md": ("Debug with evidence", "debug"),
    "commands/specsmith-review.md": ("Review governed work", "reviewer"),
    "commands/specsmith-checkpoint.md": ("Create a durable checkpoint", "orchestrator"),
}

SKILLS = {
    "skills/specsmith-governed-work/SKILL.md": "Run requirement-bound work through governance.",
    "skills/specsmith-evidence-debugging/SKILL.md": "Debug with evidence and hypotheses.",
    "skills/specsmith-context-continuity/SKILL.md": "Preserve critical state across handoffs.",
}


def rule(title: str, body: str) -> str:
    return f"<!-- {MARKER} -->\n# {title}\n\n{body}\n"


def command(title: str, mode: str) -> str:
    body = (
        f"Execute **{title.lower()}** under Specsmith governance. Inspect authority, "
        "bound scope, preserve evidence, run relevant verification, and report risks."
    )
    return (
        f"---\ndescription: {title}\nmode: {mode}\n---\n\n<!-- {MARKER} -->\n{body}\n"
    )


def skill(path: str, description: str) -> str:
    name = Path(path).parent.name
    return (
        f"---\nname: {name}\ndescription: {description}\n---\n\n"
        f"<!-- {MARKER} -->\n\n# {name}\n\n{description}\n"
    )


GLOBAL = {path: rule(*value) for path, value in RULES.items()}
GLOBAL.update({path: command(*value) for path, value in COMMANDS.items()})
GLOBAL.update({path: skill(path, value) for path, value in SKILLS.items()})
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

    def _run(
        self,
        scope: Scope,
        global_action: Callable[[], Result],
        project_action: Callable[[], Result],
    ) -> Result:
        result = Result()
        if scope in {"both", "global"}:
            result.add(global_action())
        if scope in {"both", "project"}:
            result.add(project_action())
        return result

    def setup(self, scope: Scope = "both") -> Result:
        return self._run(scope, self._setup_global, self._setup_project)

    def doctor(self, scope: Scope = "both") -> Result:
        return self._run(scope, self._doctor_global, self._doctor_project)

    def uninstall(self, scope: Scope = "both") -> Result:
        return self._run(scope, self._uninstall_global, self._uninstall_project)

    def _managed(self, path: Path) -> bool:
        if not path.is_file():
            return False
        text = path.read_text(encoding="utf-8")
        return MARKER in text or OLD_MARKER in text

    def _write(self, path: Path, text: str) -> None:
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def _write_json(self, path: Path, value: dict[str, Any]) -> None:
        self._write(path, json.dumps(value, indent=2, sort_keys=True) + "\n")

    def _read_json(self, path: Path, result: Result) -> dict[str, Any] | None:
        if not path.exists():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            result.errors.append(f"invalid JSON in {path}: {exc}")
            return None
        if not isinstance(value, dict):
            result.errors.append(f"JSON root must be an object: {path}")
            return None
        return value

    def _manifest(self) -> dict[str, Any]:
        return self._read_json(self.global_roo / MANIFEST, Result()) or {}

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
        old = set(self._manifest().get("files", []))
        for relative in sorted(old - set(GLOBAL)):
            path = self.global_roo / relative
            if self._managed(path):
                self._remove(path)
                result.removed.append(f"global:{relative}")
            elif path.exists():
                result.preserved.append(f"global:{relative}")
        for relative, expected in GLOBAL.items():
            path = self.global_roo / relative
            current = path.read_text(encoding="utf-8") if path.exists() else None
            if current is not None and current != expected and not self._managed(path):
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
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if MARKER in text or OLD_MARKER in text or text == legacy:
                    self._remove(path)
                    result.removed.append(f"project:.roo/{relative}")
                else:
                    result.preserved.append(f"project:.roo/{relative}")
        path = self.project / ".roo" / "mcp.json"
        value = self._read_json(path, result)
        if value is None:
            return result
        servers = value.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            result.errors.append(f"mcpServers must be an object: {path}")
            return result
        if servers.get("specsmith-governance") != MCP:
            servers["specsmith-governance"] = MCP
            self._write_json(path, value)
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
            result.errors.append(
                f"missing or stale manifest: {self.global_roo / MANIFEST}"
            )
        return result

    def _doctor_project(self) -> Result:
        result = Result()
        for relative, legacy in LEGACY_PROJECT.items():
            path = self.project / ".roo" / relative
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if MARKER in text or OLD_MARKER in text or text == legacy:
                    result.errors.append(
                        f"generic asset duplicated in workspace: {path}"
                    )
        value = self._read_json(self.project / ".roo" / "mcp.json", result)
        if value is not None:
            servers = value.get("mcpServers")
            if (
                not isinstance(servers, dict)
                or servers.get("specsmith-governance") != MCP
            ):
                result.errors.append("Specsmith MCP server is missing or mismatched")
        return result

    def _uninstall_global(self) -> Result:
        result = Result()
        for relative in sorted(set(self._manifest().get("files", [])) | set(GLOBAL)):
            path = self.global_roo / relative
            if self._managed(path):
                self._remove(path)
                result.removed.append(f"global:{relative}")
            elif path.exists():
                result.preserved.append(f"global:{relative}")
        path = self.global_roo / MANIFEST
        if path.exists():
            self._remove(path)
            result.removed.append(f"global:{MANIFEST}")
        return result

    def _uninstall_project(self) -> Result:
        result = Result()
        path = self.project / ".roo" / "mcp.json"
        value = self._read_json(path, result)
        if value is not None:
            servers = value.get("mcpServers")
            if isinstance(servers, dict) and servers.get("specsmith-governance") == MCP:
                del servers["specsmith-governance"]
                self._write_json(path, value)
                result.changed.append("project:.roo/mcp.json")
            elif isinstance(servers, dict) and "specsmith-governance" in servers:
                result.preserved.append("project:.roo/mcp.json#specsmith-governance")
        path = self.project / PROJECT_MANIFEST
        if path.exists():
            self._remove(path)
            result.removed.append(f"project:{PROJECT_MANIFEST}")
        return result


def root(value: Path | None) -> Path:
    configured = os.environ.get("ROO_GLOBAL_DIR")
    return value or (Path(configured) if configured else Path.home() / ".roo")


def emit(action: str, result: Result, dry_run: bool = False) -> None:
    prefix = "would " if dry_run else ""
    click.echo(
        f"Zoo Code {action}: {prefix}changed={len(result.changed)} "
        f"removed={len(result.removed)} backups={len(result.backups)} "
        f"preserved={len(result.preserved)} errors={len(result.errors)}"
    )
    for label, values in (
        ("backup", result.backups),
        ("preserved", result.preserved),
        ("error", result.errors),
    ):
        for value in values:
            click.echo(f"{label}: {value}", err=label == "error")


def instance(
    project: Path,
    global_roo: Path | None,
    dry_run: bool,
    preserve: bool,
) -> ZooCodeAssets:
    return ZooCodeAssets(project, root(global_roo), dry_run, preserve)


_common = [
    click.option(
        "--project-dir",
        default=".",
        type=click.Path(path_type=Path),
        show_default=True,
    ),
    click.option("--global-roo", type=click.Path(path_type=Path), default=None),
    click.option(
        "--scope",
        type=click.Choice(["both", "global", "project"]),
        default="both",
    ),
]


def options(function: Callable[..., Any]) -> Callable[..., Any]:
    for decorator in reversed(_common):
        function = decorator(function)
    return function


@click.command("setup")
@options
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
    result = instance(project_dir, global_roo, dry_run, preserve_existing).setup(scope)
    emit("setup", result, dry_run)
    if not result.ok:
        raise SystemExit(2)


@click.command("doctor")
@options
def doctor(project_dir: Path, global_roo: Path | None, scope: Scope) -> None:
    """Validate global assets, workspace deduplication, and MCP configuration."""
    result = instance(project_dir, global_roo, False, True).doctor(scope)
    emit("doctor", result)
    if not result.ok:
        raise SystemExit(2)


@click.command("uninstall")
@options
@click.option("--dry-run", is_flag=True)
def uninstall(
    project_dir: Path,
    global_roo: Path | None,
    scope: Scope,
    dry_run: bool,
) -> None:
    """Remove only files and MCP state managed by this integration."""
    result = instance(project_dir, global_roo, dry_run, True).uninstall(scope)
    emit("uninstall", result, dry_run)
    if not result.ok:
        raise SystemExit(2)


def register_zoo_code_asset_commands() -> None:
    """Attach lifecycle commands to the existing Zoo Code command group."""
    from specsmith.commands.zoo_code import zoo_code_group

    for item in (setup, doctor, uninstall):
        if item.name not in zoo_code_group.commands:
            zoo_code_group.add_command(item)
