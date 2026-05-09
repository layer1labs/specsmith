# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Unit tests for least-privilege agent permissions (REG-012).

Covers:
- AgentPermissions.is_allowed()
- AgentPermissions.gate() (raises PermissionError)
- AgentPermissions.check_and_log() (return value + ledger write)
- load_permissions() from SPECSMITH.yml presets and custom lists
- CLI `specsmith agent permissions` (show profile)
- CLI `specsmith agent permissions-check <tool>` (check + exit codes)
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from specsmith.agent.permissions import (
    AgentPermissions,
    load_permissions,
)
from specsmith.cli import main

# ---------------------------------------------------------------------------
# AgentPermissions.is_allowed
# ---------------------------------------------------------------------------


class TestIsAllowed:
    def test_read_only_tool_allowed_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("read_file") is True

    def test_write_tool_allowed_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("write_file") is True

    def test_shell_tool_allowed_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("run_shell") is True

    def test_git_commit_denied_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("git_commit") is False

    def test_git_push_denied_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("git_push") is False

    def test_git_create_pr_denied_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("git_create_pr") is False

    def test_open_url_denied_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("open_url") is False

    def test_unknown_tool_denied_by_standard(self) -> None:
        perms = AgentPermissions.STANDARD
        assert perms.is_allowed("some_unknown_tool_xyz") is False

    def test_read_only_profile_denies_write(self) -> None:
        perms = AgentPermissions.READ_ONLY
        assert perms.is_allowed("write_file") is False
        assert perms.is_allowed("run_shell") is False

    def test_admin_profile_allows_all_tools(self) -> None:
        perms = AgentPermissions.ADMIN
        assert perms.is_allowed("git_commit") is True
        assert perms.is_allowed("git_push") is True
        assert perms.is_allowed("open_url") is True

    def test_extended_allows_network_tools(self) -> None:
        perms = AgentPermissions.EXTENDED
        assert perms.is_allowed("open_url") is True
        assert perms.is_allowed("search_docs") is True
        # But NOT high-privilege VCS
        assert perms.is_allowed("git_commit") is False

    def test_deny_overrides_allow(self) -> None:
        """When a tool appears in both allow and deny, deny wins."""
        perms = AgentPermissions(
            allow=frozenset({"read_file", "git_commit"}),
            deny=frozenset({"git_commit"}),
            label="test",
        )
        assert perms.is_allowed("read_file") is True
        assert perms.is_allowed("git_commit") is False


# ---------------------------------------------------------------------------
# AgentPermissions.gate
# ---------------------------------------------------------------------------


class TestGate:
    def test_gate_allows_permitted_tool(self) -> None:
        perms = AgentPermissions.STANDARD
        # Should not raise
        perms.gate("read_file")

    def test_gate_raises_for_denied_tool(self) -> None:
        perms = AgentPermissions.STANDARD
        with pytest.raises(PermissionError) as exc_info:
            perms.gate("git_commit")
        msg = str(exc_info.value)
        assert "git_commit" in msg
        assert "standard" in msg
        assert "agent" in msg.lower()

    def test_gate_hint_contains_yaml_snippet(self) -> None:
        perms = AgentPermissions.STANDARD
        with pytest.raises(PermissionError) as exc_info:
            perms.gate("open_url")
        assert "SPECSMITH.yml" in str(exc_info.value)


# ---------------------------------------------------------------------------
# AgentPermissions.check_and_log
# ---------------------------------------------------------------------------


class TestCheckAndLog:
    def test_allowed_returns_true_empty_reason(self, tmp_path: Path) -> None:
        perms = AgentPermissions.STANDARD
        ok, reason = perms.check_and_log("read_file", tmp_path)
        assert ok is True
        assert reason == ""

    def test_denied_returns_false_with_reason(self, tmp_path: Path) -> None:
        perms = AgentPermissions.STANDARD
        ok, reason = perms.check_and_log("git_commit", tmp_path, log_denied=False)
        assert ok is False
        assert "git_commit" in reason

    def test_denial_writes_ledger_entry(self, tmp_path: Path) -> None:
        """A denied check (log_denied=True) appends a permission-denied entry."""
        # Seed a ledger so we have somewhere to write
        ledger = tmp_path / "docs" / "LEDGER.md"
        ledger.parent.mkdir(parents=True)
        ledger.write_text("# Ledger\n", encoding="utf-8")

        perms = AgentPermissions.STANDARD
        ok, _ = perms.check_and_log("git_push", tmp_path, log_denied=True)
        assert ok is False

        content = ledger.read_text(encoding="utf-8")
        assert "permission-denied" in content or "REG-012" in content

    def test_no_log_does_not_write_ledger(self, tmp_path: Path) -> None:
        """When log_denied=False the ledger must not be touched."""
        ledger = tmp_path / "docs" / "LEDGER.md"
        ledger.parent.mkdir(parents=True)
        original = "# Ledger\n"
        ledger.write_text(original, encoding="utf-8")

        perms = AgentPermissions.STANDARD
        perms.check_and_log("git_commit", tmp_path, log_denied=False)

        assert ledger.read_text(encoding="utf-8") == original

    def test_allowed_tool_never_writes_ledger(self, tmp_path: Path) -> None:
        ledger = tmp_path / "docs" / "LEDGER.md"
        ledger.parent.mkdir(parents=True)
        original = "# Ledger\n"
        ledger.write_text(original, encoding="utf-8")

        perms = AgentPermissions.STANDARD
        ok, _ = perms.check_and_log("read_file", tmp_path, log_denied=True)
        assert ok is True
        assert ledger.read_text(encoding="utf-8") == original


# ---------------------------------------------------------------------------
# load_permissions from SPECSMITH.yml
# ---------------------------------------------------------------------------


class TestLoadPermissions:
    def _write_scaffold(self, tmp_path: Path, content: dict) -> Path:
        docs = tmp_path / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        scaffold = docs / "SPECSMITH.yml"
        scaffold.write_text(yaml.dump(content), encoding="utf-8")
        return tmp_path

    def test_no_scaffold_returns_standard(self, tmp_path: Path) -> None:
        perms = load_permissions(tmp_path)
        assert perms.label == "standard"

    def test_scaffold_without_agent_section_returns_standard(self, tmp_path: Path) -> None:
        self._write_scaffold(tmp_path, {"name": "test-proj", "type": "cli-python"})
        perms = load_permissions(tmp_path)
        assert perms.label == "standard"

    def test_preset_read_only(self, tmp_path: Path) -> None:
        self._write_scaffold(
            tmp_path,
            {"name": "test", "agent": {"permissions": {"preset": "read_only"}}},
        )
        perms = load_permissions(tmp_path)
        assert perms.label == "read-only"
        assert perms.is_allowed("write_file") is False

    def test_preset_admin(self, tmp_path: Path) -> None:
        self._write_scaffold(
            tmp_path,
            {"name": "test", "agent": {"permissions": {"preset": "admin"}}},
        )
        perms = load_permissions(tmp_path)
        assert perms.label == "admin"
        assert perms.is_allowed("git_commit") is True

    def test_preset_extended(self, tmp_path: Path) -> None:
        self._write_scaffold(
            tmp_path,
            {"name": "test", "agent": {"permissions": {"preset": "extended"}}},
        )
        perms = load_permissions(tmp_path)
        assert perms.label == "extended"
        assert perms.is_allowed("open_url") is True

    def test_custom_allow_deny_lists(self, tmp_path: Path) -> None:
        self._write_scaffold(
            tmp_path,
            {
                "name": "test",
                "agent": {
                    "permissions": {
                        "allow": ["read_file", "git_commit"],
                        "deny": ["run_shell"],
                    }
                },
            },
        )
        perms = load_permissions(tmp_path)
        assert perms.label == "custom"
        assert perms.is_allowed("git_commit") is True
        assert perms.is_allowed("run_shell") is False

    def test_corrupt_scaffold_returns_standard(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "SPECSMITH.yml").write_text(": }{{{not yaml", encoding="utf-8")
        perms = load_permissions(tmp_path)
        assert perms.label == "standard"


# ---------------------------------------------------------------------------
# summary() helper
# ---------------------------------------------------------------------------


class TestSummary:
    def test_summary_keys(self) -> None:
        summary = AgentPermissions.STANDARD.summary()
        assert "label" in summary
        assert "allow" in summary
        assert "deny" in summary
        assert isinstance(summary["allow"], list)
        assert isinstance(summary["deny"], list)

    def test_summary_allow_sorted(self) -> None:
        summary = AgentPermissions.STANDARD.summary()
        allow = summary["allow"]
        assert allow == sorted(allow)


# ---------------------------------------------------------------------------
# CLI: specsmith agent permissions (show profile)
# ---------------------------------------------------------------------------


class TestCLIPermissionsShow:
    def test_permissions_show_human_readable(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["agent", "permissions", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Permission Profile" in result.output
        assert "standard" in result.output.lower()

    def test_permissions_show_json(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main, ["agent", "permissions", "--project-dir", str(tmp_path), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "label" in data
        assert "allow" in data
        assert "deny" in data

    def test_permissions_respects_preset_in_config(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "SPECSMITH.yml").write_text(
            yaml.dump({"name": "x", "agent": {"permissions": {"preset": "read_only"}}}),
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(
            main, ["agent", "permissions", "--project-dir", str(tmp_path), "--json"]
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["label"] == "read-only"


# ---------------------------------------------------------------------------
# CLI: specsmith agent permissions-check <tool>
# ---------------------------------------------------------------------------


class TestCLIPermissionsCheck:
    def test_allowed_tool_exits_0(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["agent", "permissions-check", "read_file", "--project-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        assert "allowed" in result.output.lower()

    def test_denied_tool_exits_3(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "agent",
                "permissions-check",
                "git_push",
                "--project-dir",
                str(tmp_path),
                "--no-log",
            ],
        )
        assert result.exit_code == 3
        assert "denied" in result.output.lower()

    def test_json_output_allowed(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "agent",
                "permissions-check",
                "grep",
                "--project-dir",
                str(tmp_path),
                "--json",
            ],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["tool"] == "grep"
        assert data["allowed"] is True
        assert data["reason"] == ""

    def test_json_output_denied(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "agent",
                "permissions-check",
                "git_commit",
                "--project-dir",
                str(tmp_path),
                "--json",
                "--no-log",
            ],
        )
        assert result.exit_code == 3
        data = json.loads(result.output)
        assert data["allowed"] is False
        assert "git_commit" in data["reason"]

    def test_denied_tool_logs_to_ledger(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        ledger = docs / "LEDGER.md"
        ledger.write_text("# Ledger\n", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "agent",
                "permissions-check",
                "open_url",
                "--project-dir",
                str(tmp_path),
                # Note: no --no-log, so ledger write should happen
            ],
        )
        assert result.exit_code == 3
        # The ledger should contain a denial entry
        content = ledger.read_text(encoding="utf-8")
        assert "open_url" in content or "REG-012" in content

    def test_no_log_suppresses_ledger_write(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        ledger = docs / "LEDGER.md"
        original = "# Ledger\n"
        ledger.write_text(original, encoding="utf-8")

        runner = CliRunner()
        runner.invoke(
            main,
            [
                "agent",
                "permissions-check",
                "git_push",
                "--project-dir",
                str(tmp_path),
                "--no-log",
            ],
        )
        # Ledger must be unchanged
        assert ledger.read_text(encoding="utf-8") == original

    def test_admin_preset_allows_git_commit(self, tmp_path: Path) -> None:
        docs = tmp_path / "docs"
        docs.mkdir(parents=True)
        (docs / "SPECSMITH.yml").write_text(
            yaml.dump({"name": "x", "agent": {"permissions": {"preset": "admin"}}}),
            encoding="utf-8",
        )
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "agent",
                "permissions-check",
                "git_commit",
                "--project-dir",
                str(tmp_path),
                "--no-log",
            ],
        )
        assert result.exit_code == 0
        assert "allowed" in result.output.lower()
