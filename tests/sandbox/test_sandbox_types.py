# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Sandbox tests for non-Python project types, config inheritance, and export."""

from __future__ import annotations

from pathlib import Path

import yaml
from click.testing import CliRunner

from specsmith.cli import main


class TestPatentApplicationScaffold:
    """Scaffold a patent-application project and verify domain-specific content."""

    def test_patent_scaffold(self, tmp_path: Path) -> None:
        config = {
            "name": "my-patent",
            "type": "patent-application",
            "platforms": ["windows", "linux"],
            "language": "markdown",
            "vcs_platform": "github",
            "git_init": False,
        }
        cfg_path = tmp_path / "scaffold.yml"
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        project = tmp_path / "my-patent"

        # Patent-specific directories
        assert (project / "claims" / ".gitkeep").exists()
        assert (project / "specification" / ".gitkeep").exists()
        assert (project / "prior-art" / ".gitkeep").exists()
        assert (project / "figures" / ".gitkeep").exists()
        assert (project / "correspondence" / ".gitkeep").exists()

        # Patent-specific AGENTS.md rules
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "Claims" in agents or "claims" in agents.lower()

        # Patent-specific requirements
        reqs = (project / "docs" / "REQUIREMENTS.md").read_text(encoding="utf-8")
        assert "REQ-CLM-001" in reqs
        assert "REQ-SPEC-001" in reqs

        # Patent-specific test spec
        tests = (project / "docs" / "TESTS.md").read_text(encoding="utf-8")
        assert "TEST-CLM-001" in tests

        # Verification.md has patent tools
        verification = (project / "docs" / "governance" / "VERIFICATION.md").read_text(
            encoding="utf-8"
        )
        assert "vale" in verification
        assert "claim-ref-check" in verification

        # Audit runs
        audit = runner.invoke(main, ["audit", "--project-dir", str(project)])
        assert "AGENTS.md" in audit.output


class TestRustCLIScaffold:
    """Scaffold a Rust CLI project and verify Rust-specific tooling."""

    def test_rust_scaffold_ci(self, tmp_path: Path) -> None:
        config = {
            "name": "my-rust-tool",
            "type": "cli-rust",
            "platforms": ["linux", "macos"],
            "language": "rust",
            "vcs_platform": "github",
            "git_init": False,
        }
        cfg_path = tmp_path / "scaffold.yml"
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
        )
        assert result.exit_code == 0

        project = tmp_path / "my-rust-tool"

        # Rust directories
        assert (project / "src" / ".gitkeep").exists()
        assert (project / "benches" / ".gitkeep").exists()

        # Rust CI
        ci = (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "cargo clippy" in ci
        assert "cargo test" in ci
        assert "cargo audit" in ci
        assert "rust-toolchain" in ci

        # Rust dependabot
        dep = (project / ".github" / "dependabot.yml").read_text(encoding="utf-8")
        assert "cargo" in dep

        # Rust AGENTS.md rules
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "clippy" in agents.lower() or "cargo" in agents.lower()

        # Verification tools
        v = (project / "docs" / "governance" / "VERIFICATION.md").read_text(encoding="utf-8")
        assert "cargo clippy" in v
        assert "cargo test" in v


class TestConfigInheritance:
    """Test scaffold.yml extends field for org-level config inheritance."""

    def test_extends_parent_config(self, tmp_path: Path) -> None:
        # Parent config (org defaults)
        parent = {
            "name": "placeholder",
            "type": "cli-python",
            "platforms": ["linux"],
            "language": "python",
            "vcs_platform": "gitlab",
            "branching_strategy": "trunk-based",
            "require_pr_reviews": True,
            "required_approvals": 2,
            "git_init": False,
        }
        parent_path = tmp_path / "org-defaults.yml"
        with open(parent_path, "w") as f:
            yaml.dump(parent, f)

        # Child config (project overrides name + type)
        child = {
            "extends": str(parent_path),
            "name": "my-child-project",
            "description": "Inherits org defaults",
        }
        child_path = tmp_path / "scaffold.yml"
        with open(child_path, "w") as f:
            yaml.dump(child, f)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init", "--config", str(child_path), "--output-dir", str(tmp_path), "--no-git"],
        )
        assert result.exit_code == 0, f"Init failed: {result.output}"

        project = tmp_path / "my-child-project"
        assert project.exists()

        # Verify child overrides were applied (scaffold now at docs/SPECSMITH.yml)
        saved = project / "docs" / "SPECSMITH.yml"
        if not saved.exists():
            saved = project / "scaffold.yml"  # fallback
        with open(saved) as f:
            cfg = yaml.safe_load(f)
        assert cfg["name"] == "my-child-project"
        assert cfg["description"] == "Inherits org defaults"

        # Verify parent defaults were inherited
        assert cfg["vcs_platform"] == "gitlab"
        assert cfg["branching_strategy"] == "trunk-based"
        assert cfg["required_approvals"] == 2

        # GitLab CI should have been generated (from parent's vcs_platform)
        assert (project / ".gitlab-ci.yml").exists()


class TestLegalComplianceScaffold:
    """Scaffold a legal-compliance project and verify domain content."""

    def test_legal_scaffold(self, tmp_path: Path) -> None:
        config = {
            "name": "acme-compliance",
            "type": "legal-compliance",
            "platforms": ["windows", "linux"],
            "language": "markdown",
            "vcs_platform": "github",
            "git_init": False,
        }
        cfg_path = tmp_path / "scaffold.yml"
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
        )
        assert result.exit_code == 0

        project = tmp_path / "acme-compliance"

        # Legal-specific directories
        assert (project / "contracts" / ".gitkeep").exists()
        assert (project / "policies" / ".gitkeep").exists()
        assert (project / "evidence" / ".gitkeep").exists()
        assert (project / "audit-trail" / ".gitkeep").exists()

        # Legal-specific requirements
        reqs = (project / "docs" / "REQUIREMENTS.md").read_text(encoding="utf-8")
        assert "REQ-CTR-001" in reqs
        assert "REQ-REG-001" in reqs

        # Legal-specific test spec
        tests = (project / "docs" / "TESTS.md").read_text(encoding="utf-8")
        assert "TEST-CTR-001" in tests

        # Legal AGENTS.md rules
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "regulatory" in agents.lower() or "compliance" in agents.lower()

        # Verification has compliance tool
        v = (project / "docs" / "governance" / "VERIFICATION.md").read_text(encoding="utf-8")
        assert "regulation-ref-check" in v


class TestBusinessPlanScaffold:
    """Scaffold a business-plan project and verify domain content."""

    def test_business_scaffold(self, tmp_path: Path) -> None:
        config = {
            "name": "acme-plan",
            "type": "business-plan",
            "platforms": ["windows"],
            "language": "markdown",
            "vcs_platform": "github",
            "git_init": False,
        }
        cfg_path = tmp_path / "scaffold.yml"
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
        )
        assert result.exit_code == 0

        project = tmp_path / "acme-plan"

        # Business-specific directories
        assert (project / "plan" / ".gitkeep").exists()
        assert (project / "financials" / ".gitkeep").exists()
        assert (project / "market-research" / ".gitkeep").exists()

        # Business-specific requirements
        reqs = (project / "docs" / "REQUIREMENTS.md").read_text(encoding="utf-8")
        assert "REQ-EXEC-001" in reqs
        assert "REQ-FIN-001" in reqs

        # Business AGENTS.md rules
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "financial" in agents.lower() or "stakeholder" in agents.lower()


class TestAPISpecScaffold:
    """Scaffold an api-specification project and verify domain content."""

    def test_api_spec_scaffold(self, tmp_path: Path) -> None:
        config = {
            "name": "acme-api",
            "type": "api-specification",
            "platforms": ["linux"],
            "language": "openapi",
            "vcs_platform": "github",
            "git_init": False,
        }
        cfg_path = tmp_path / "scaffold.yml"
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
        )
        assert result.exit_code == 0

        project = tmp_path / "acme-api"

        # API-specific directories
        assert (project / "specs" / ".gitkeep").exists()
        assert (project / "schemas" / ".gitkeep").exists()
        assert (project / "examples" / ".gitkeep").exists()
        assert (project / "generated" / ".gitkeep").exists()

        # API-specific requirements
        reqs = (project / "docs" / "REQUIREMENTS.md").read_text(encoding="utf-8")
        assert "REQ-API-001" in reqs
        assert "REQ-AUTH-001" in reqs

        # API-specific test spec
        tests = (project / "docs" / "TESTS.md").read_text(encoding="utf-8")
        assert "TEST-API-001" in tests

        # CI has spectral
        ci = (project / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        assert "spectral" in ci

        # AGENTS.md has API rules
        agents = (project / "AGENTS.md").read_text(encoding="utf-8")
        assert "api" in agents.lower() or "spectral" in agents.lower()


class TestExportCommand:
    """Test specsmith export generates a compliance report."""

    def test_export_on_scaffolded_project(self, tmp_path: Path) -> None:
        config = {
            "name": "export-test",
            "type": "cli-python",
            "language": "python",
            "vcs_platform": "github",
            "git_init": False,
        }
        cfg_path = tmp_path / "scaffold.yml"
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        runner = CliRunner()
        runner.invoke(
            main,
            ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
        )

        project = tmp_path / "export-test"

        # Run export
        result = runner.invoke(main, ["export", "--project-dir", str(project)])
        assert result.exit_code == 0
        assert "Compliance Report" in result.output
        assert "Verification Tools" in result.output
        assert "ruff" in result.output
        assert "Audit Summary" in result.output
        assert "Governance File Inventory" in result.output

    def test_export_to_file(self, tmp_path: Path) -> None:
        config = {
            "name": "export-file",
            "type": "cli-python",
            "language": "python",
            "git_init": False,
            "vcs_platform": "",
        }
        cfg_path = tmp_path / "scaffold.yml"
        with open(cfg_path, "w") as f:
            yaml.dump(config, f)

        runner = CliRunner()
        runner.invoke(
            main,
            ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
        )

        project = tmp_path / "export-file"
        out_file = tmp_path / "report.md"

        result = runner.invoke(
            main, ["export", "--project-dir", str(project), "--output", str(out_file)]
        )
        assert result.exit_code == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "Compliance Report" in content
