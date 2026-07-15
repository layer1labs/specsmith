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


def managed(text: str) -> str:
    return f"<!-- {MARKER} -->\n{text.strip()}\n"


def command(description: str, body: str, mode: str) -> str:
    return (
        f"---\ndescription: {description}\nmode: {mode}\n---\n\n"
        f"<!-- {MARKER} -->\n{body.strip()}\n"
    )


def skill(name: str, description: str, body: str) -> str:
    return (
        f"---\nname: {name}\ndescription: {description}\n---\n\n"
        f"<!-- {MARKER} -->\n\n{body.strip()}\n"
    )


GLOBAL: dict[str, str] = {
    "rules/00-specsmith-source-of-truth.md": managed("""# Specsmith source of truth

Treat repository files, Specsmith requirements, evidence, checks, traces, and ledger artifacts as authoritative. Verify before assuming and separate verified facts from assumptions."""),
    "rules/10-specsmith-governance.md": managed("""# Specsmith governance

Anchor non-trivial work to requirements, constraints, acceptance criteria, evidence, and verification. Run governance preflight before implementation."""),
    "rules/20-context-continuity.md": managed("""# Context continuity

Preserve active work items, decisions, constraints, evidence, risks, changed files, and the next verification step before condensation or handoff."""),
    "rules/30-security-and-secrets.md": managed("""# Secrets and safety

Never expose, commit, or echo secrets. Treat destructive, privileged, and externally visible actions as explicit approval gates."""),
    "rules/40-context-efficiency.md": managed("""# Context efficiency

Search before reading, batch related reads, avoid duplicate context, and optimize for tokens per verified correct result rather than raw token count."""),
    "rules-architect/10-planning.md": managed("""# Architect planning

Define scope, invariants, interfaces, alternatives, risks, acceptance criteria, and verification before authorizing implementation."""),
    "rules-ask/10-evidence-answers.md": managed("""# Evidence-grounded answers

Answer from inspected evidence. Label inference and uncertainty and do not present guesses as verified project facts."""),
    "rules-code/10-implementation-verification.md": managed("""# Governed implementation

Implement only accepted scope, preserve unrelated behavior, run focused checks, and record evidence before claiming completion."""),
    "rules-debug/10-debug-evidence.md": managed("""# Evidence-driven debugging

Reproduce first, form falsifiable hypotheses, inspect focused evidence, and verify the fix against the original failure and regressions."""),
    "rules-orchestrator/10-specsmith-boomerang.md": managed("""# Specsmith orchestration

Delegate bounded tasks with explicit inputs and return contracts. Verify returned work before accepting dependent actions."""),
    "rules-reviewer/10-review-readiness.md": managed("""# Review readiness

Review against requirements, tests, security constraints, and prior decisions. The authoring model must not be the sole approver."""),
    "commands/specsmith-intake.md": command("Start governed work", "Identify the outcome, requirements, constraints, ambiguity, evidence, and smallest bounded work item. Run preflight before edits.", "orchestrator"),
    "commands/specsmith-plan.md": command("Plan governed work", "Create a requirement-linked plan with file scope, risks, tests, and objective completion criteria.", "architect"),
    "commands/specsmith-implement.md": command("Implement governed work", "Implement accepted scope only, run focused verification, and report evidence, changed files, and residual risk.", "code"),
    "commands/specsmith-debug.md": command("Debug with evidence", "Reproduce, rank falsifiable hypotheses, gather evidence, apply the smallest supported fix, and rerun regression checks.", "debug"),
    "commands/specsmith-review.md": command("Review governed work", "Independently review requirement coverage, correctness, regressions, security, tests, and unsupported claims.", "reviewer"),
    "commands/specsmith-checkpoint.md": command("Create a durable checkpoint", "Preserve active work, facts, assumptions, decisions, files, checks, risks, and the exact next action.", "orchestrator"),
    "skills/specsmith-governed-work/SKILL.md": skill("specsmith-governed-work", "Run requirement-bound engineering work through Specsmith governance.", "Perform checkpoint, phase and requirement reads, preflight, bounded edits, verification, and trace sealing."),
    "skills/specsmith-evidence-debugging/SKILL.md": skill("specsmith-evidence-debugging", "Debug with reproduction evidence and falsifiable hypotheses.", "Require reproduction, focused probes, a bounded fix, and regression verification."),
    "skills/specsmith-context-continuity/SKILL.md": skill("specsmith-context-continuity", "Preserve critical state across condensation and handoff.", "Preserve scope, decisions, evidence, risks, changed files, checks, and next actions without speculative filler."),
}

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

    def add(self, other: "Result") -> None:
        for name in ("changed", "removed", "backups", "preserved", "errors"):
            getattr(self, name).extend(getattr(other, name))


class ZooCodeAssets:
    def __init__(self, project: Path, global_roo: Path, dry_run: bool = False, preserve_existing: bool = False) -> None:
        self.project = project.expanduser().resolve()
        self.global_roo = global_roo.expanduser().resolve()
        self.dry_run = dry_run
        self.preserve_existing = preserve_existing

    def setup(self, scope: Scope = "both") -> Result:
        out = Result()
        if scope in {"both", "global"}:
            out.add(self._setup_global())
        if scope in {"both", "project"}:
            out.add(self._setup_project())
        return out

    def doctor(self, scope: Scope = "both") -> Result:
        out = Result()
        if scope in {"both", "global"}:
            out.add(self._doctor_global())
        if scope in {"both", "project"}:
            out.add(self._doctor_project())
        return out

    def uninstall(self, scope: Scope = "both") -> Result:
        out = Result()
        if scope in {"both", "global"}:
            out.add(self._uninstall_global())
        if scope in {"both", "project"}:
            out.add(self._uninstall_project())
        return out

    def _managed(self, path: Path) -> bool:
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
        path = self.global_roo / MANIFEST
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def _remove(self, path: Path) -> None:
        if not self.dry_run:
            path.unlink(missing_ok=True)

    def _backup(self, path: Path) -> Path:
        backup = path.with_name(path.name + ".before-specsmith-zoo-code")
        n = 1
        while backup.exists():
            backup = path.with_name(path.name + f".before-specsmith-zoo-code.{n}")
            n += 1
        if not self.dry_run:
            shutil.copy2(path, backup)
        return backup

    def _setup_global(self) -> Result:
        out = Result()
        old = set(self._manifest().get("files", []))
        for rel in sorted(old - set(GLOBAL)):
            path = self.global_roo / rel
            if self._managed(path):
                self._remove(path)
                out.removed.append(f"global:{rel}")
            elif path.exists():
                out.preserved.append(f"global:{rel}")
        for rel, expected in GLOBAL.items():
            path = self.global_roo / rel
            if path.exists() and path.read_text(encoding="utf-8") != expected and not self._managed(path):
                if self.preserve_existing:
                    out.preserved.append(f"global:{rel}")
                    out.errors.append(f"reserved path is unmanaged: {path}")
                    continue
                out.backups.append(str(self._backup(path)))
            if not path.exists() or path.read_text(encoding="utf-8") != expected:
                self._write(path, expected)
                out.changed.append(f"global:{rel}")
        self._write_json(self.global_roo / MANIFEST, {"schema": 2, "files": sorted(GLOBAL)})
        return out

    def _setup_project(self) -> Result:
        out = Result()
        for rel, legacy in LEGACY_PROJECT.items():
            path = self.project / ".roo" / rel
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            if MARKER in text or OLD_MARKER in text or text == legacy:
                self._remove(path)
                out.removed.append(f"project:.roo/{rel}")
            else:
                out.preserved.append(f"project:.roo/{rel}")
        mcp_path = self.project / ".roo" / "mcp.json"
        data = self._read_json(mcp_path, out)
        if data is None:
            return out
        servers = data.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            out.errors.append(f"mcpServers must be an object: {mcp_path}")
            return out
        if servers.get("specsmith-governance") != MCP:
            servers["specsmith-governance"] = MCP
            self._write_json(mcp_path, data)
            out.changed.append("project:.roo/mcp.json")
        self._write_json(self.project / PROJECT_MANIFEST, {"schema": 2, "mcp_server": MCP})
        return out

    def _doctor_global(self) -> Result:
        out = Result()
        for rel, expected in GLOBAL.items():
            path = self.global_roo / rel
            if not path.is_file():
                out.errors.append(f"missing global asset: {path}")
            elif path.read_text(encoding="utf-8") != expected:
                out.errors.append(f"mismatched global asset: {path}")
        if set(self._manifest().get("files", [])) != set(GLOBAL):
            out.errors.append(f"missing or stale manifest: {self.global_roo / MANIFEST}")
        return out

    def _doctor_project(self) -> Result:
        out = Result()
        for rel, legacy in LEGACY_PROJECT.items():
            path = self.project / ".roo" / rel
            if path.is_file():
                text = path.read_text(encoding="utf-8")
                if MARKER in text or OLD_MARKER in text or text == legacy:
                    out.errors.append(f"generic asset duplicated in workspace: {path}")
        data = self._read_json(self.project / ".roo" / "mcp.json", out)
        if data is not None:
            servers = data.get("mcpServers")
            if not isinstance(servers, dict) or servers.get("specsmith-governance") != MCP:
                out.errors.append("Specsmith MCP server is missing or mismatched")
        return out

    def _uninstall_global(self) -> Result:
        out = Result()
        candidates = set(self._manifest().get("files", [])) | set(GLOBAL)
        for rel in sorted(candidates):
            path = self.global_roo / rel
            if self._managed(path):
                self._remove(path)
                out.removed.append(f"global:{rel}")
            elif path.exists():
                out.preserved.append(f"global:{rel}")
        manifest = self.global_roo / MANIFEST
        if manifest.exists():
            self._remove(manifest)
            out.removed.append(f"global:{MANIFEST}")
        return out

    def _uninstall_project(self) -> Result:
        out = Result()
        path = self.project / ".roo" / "mcp.json"
        data = self._read_json(path, out)
        if data is not None:
            servers = data.get("mcpServers")
            if isinstance(servers, dict) and servers.get("specsmith-governance") == MCP:
                del servers["specsmith-governance"]
                self._write_json(path, data)
                out.changed.append("project:.roo/mcp.json")
            elif isinstance(servers, dict) and "specsmith-governance" in servers:
                out.preserved.append("project:.roo/mcp.json#specsmith-governance")
        manifest = self.project / PROJECT_MANIFEST
        if manifest.exists():
            self._remove(manifest)
            out.removed.append(f"project:{PROJECT_MANIFEST}")
        return out


def global_root(value: Path | None) -> Path:
    return value or Path(os.environ.get("ROO_GLOBAL_DIR", Path.home() / ".roo"))


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


def manager(project: Path, global_roo: Path | None, dry_run: bool, preserve: bool) -> ZooCodeAssets:
    return ZooCodeAssets(project, global_root(global_roo), dry_run, preserve)


@click.command("setup")
@click.option("--project-dir", default=".", type=click.Path(path_type=Path), show_default=True)
@click.option("--global-roo", type=click.Path(path_type=Path), default=None)
@click.option("--scope", type=click.Choice(["both", "global", "project"]), default="both")
@click.option("--dry-run", is_flag=True)
@click.option("--preserve-existing", is_flag=True)
def setup(project_dir: Path, global_roo: Path | None, scope: Scope, dry_run: bool, preserve_existing: bool) -> None:
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
def uninstall(project_dir: Path, global_roo: Path | None, scope: Scope, dry_run: bool) -> None:
    """Remove only files and MCP state managed by this integration."""
    result = manager(project_dir, global_roo, dry_run, True).uninstall(scope)
    emit("uninstall", result, dry_run)
    if not result.ok:
        raise SystemExit(2)


def register_zoo_code_asset_commands() -> None:
    from specsmith.commands.zoo_code import zoo_code_group

    for item in (setup, doctor, uninstall):
        if item.name not in zoo_code_group.commands:
            zoo_code_group.add_command(item)
