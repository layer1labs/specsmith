# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Sandbox smoke tests: every ProjectType must scaffold and audit cleanly.

Two test classes:
  TestAllTypesSmoke        — parametrized over all 63 types; init + audit must pass,
                             AGENTS.md and LEDGER.md must be present.
  TestAITypesDomainContent — verifies the 16 new AI/modern project types from
                             v0.13.0 scaffold their domain-specific directory
                             structures (functions/, contracts/, models/, etc.).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from specsmith.cli import main
from specsmith.config import ProjectType

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Types whose default language is NOT python
_LANG_MAP: dict[str, str] = {
    "cli-rust": "rust",
    "library-rust": "rust",
    "fpga-rtl": "vhdl",
    "fpga-rtl-amd": "vhdl",
    "fpga-rtl-intel": "verilog",
    "fpga-rtl-lattice": "verilog",
    "mixed-fpga-embedded": "vhdl",
    "mixed-fpga-firmware": "c",
    "embedded-hardware": "c",
    "library-c": "c",
    "cli-c": "c",
    "cli-go": "go",
    "kubernetes-operator": "go",
    "dotnet-app": "csharp",
    "game-unity": "csharp",
    "java-spring": "java",
    "java-library": "java",
    "smart-contract": "solidity",
}

ALL_TYPES: list[str] = [t.value for t in ProjectType]


def _scaffold(tmp_path: Path, project_type: str, name: str = "smoke-test") -> Path:
    """Scaffold a minimal project of the given type and return the project dir."""
    lang = _LANG_MAP.get(project_type, "python")
    config = {
        "name": name,
        "type": project_type,
        "platforms": ["linux"],
        "language": lang,
        "vcs_platform": "github",
        "git_init": False,
    }
    cfg_path = tmp_path / "scaffold.yml"
    with open(cfg_path, "w") as fh:
        yaml.dump(config, fh, default_flow_style=False, sort_keys=False)

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["init", "--config", str(cfg_path), "--output-dir", str(tmp_path), "--no-git"],
    )
    assert result.exit_code == 0, (
        f"init failed for {project_type!r}:\n{result.output}"
    )
    return tmp_path / name


# ---------------------------------------------------------------------------
# TestAllTypesSmoke
# ---------------------------------------------------------------------------


class TestAllTypesSmoke:
    """Every project type must scaffold without error and pass 'specsmith audit'."""

    @pytest.mark.parametrize("project_type", ALL_TYPES)
    def test_scaffold_succeeds(self, tmp_path: Path, project_type: str) -> None:
        project = _scaffold(tmp_path, project_type)
        assert project.is_dir(), f"project dir not created for {project_type!r}"

    @pytest.mark.parametrize("project_type", ALL_TYPES)
    def test_governance_files_present(self, tmp_path: Path, project_type: str) -> None:
        project = _scaffold(tmp_path, project_type)
        assert (project / "AGENTS.md").exists(), f"{project_type}: AGENTS.md missing"
        assert (project / "LEDGER.md").exists(), f"{project_type}: LEDGER.md missing"
        # Modular governance dir
        gov = project / "docs" / "governance"
        assert gov.is_dir(), f"{project_type}: docs/governance/ dir missing"
        for fname in (
            "RULES.md",
            "SESSION-PROTOCOL.md",
            "LIFECYCLE.md",
            "ROLES.md",
            "CONTEXT-BUDGET.md",
            "VERIFICATION.md",
            "DRIFT-METRICS.md",
        ):
            assert (gov / fname).exists(), f"{project_type}: docs/governance/{fname} missing"

    @pytest.mark.parametrize("project_type", ALL_TYPES)
    def test_audit_passes(self, tmp_path: Path, project_type: str) -> None:
        project = _scaffold(tmp_path, project_type)
        runner = CliRunner()
        result = runner.invoke(main, ["audit", "--project-dir", str(project)])
        assert result.exit_code == 0, (
            f"audit failed for {project_type!r}:\n{result.output}"
        )
        assert "Healthy" in result.output, (
            f"audit not Healthy for {project_type!r}:\n{result.output}"
        )

    @pytest.mark.parametrize("project_type", ALL_TYPES)
    def test_validate_passes(self, tmp_path: Path, project_type: str) -> None:
        project = _scaffold(tmp_path, project_type)
        runner = CliRunner()
        result = runner.invoke(main, ["validate", "--project-dir", str(project)])
        assert result.exit_code == 0, (
            f"validate failed for {project_type!r}:\n{result.output}"
        )

    @pytest.mark.parametrize("project_type", ALL_TYPES)
    def test_all_scaffold_files_non_empty(self, tmp_path: Path, project_type: str) -> None:
        """No scaffold template should produce an empty file (except .gitkeep)."""
        project = _scaffold(tmp_path, project_type)
        for f in project.rglob("*"):
            if f.is_file() and f.name != ".gitkeep":
                assert f.stat().st_size > 0, (
                    f"{project_type}: scaffold produced empty file {f.relative_to(project)}"
                )


# ---------------------------------------------------------------------------
# TestAITypesDomainContent
# ---------------------------------------------------------------------------


class TestAITypesDomainContent:
    """Verify the 16 new AI/modern project types scaffold domain-specific dirs."""

    @pytest.mark.parametrize(
        "project_type, expected_dirs",
        [
            ("llm-app",            ["src", "tests"]),
            ("agent-orchestration", ["src", "examples"]),
            ("mcp-server",         ["src", "tests"]),
            ("rag-pipeline",       ["src", "data"]),
            ("mlops-platform",     ["pipelines", "models", "experiments", "serving"]),
            ("serverless",         ["functions", "infrastructure"]),
            ("kubernetes-operator", ["controllers", "api", "cmd", "config"]),
            ("streaming-pipeline", ["src", "deploy"]),
            ("data-warehouse",     ["models", "macros", "seeds", "analyses"]),
            ("game-unity",         ["Assets", "tests"]),
            ("game-godot",         ["scenes", "assets"]),
            ("smart-contract",     ["contracts", "deployments"]),
            ("desktop-electron",   ["src", "build"]),
            ("desktop-tauri",      ["src", "src-tauri"]),
            # Web frameworks from 0.13.0 — no domain-specific dirs, just governance
            # (tested via TestAllTypesSmoke; listed here to confirm they scaffold OK)
            ("nextjs-app",         ["docs", "scripts", "tests"]),
            ("nuxt-app",           ["docs", "scripts", "tests"]),
            ("sveltekit-app",      ["docs", "scripts", "tests"]),
        ],
    )
    def test_domain_dirs_present(
        self, tmp_path: Path, project_type: str, expected_dirs: list[str]
    ) -> None:
        project = _scaffold(tmp_path, project_type)
        actual_dirs = {p.name for p in project.iterdir() if p.is_dir()}
        for d in expected_dirs:
            assert d in actual_dirs, (
                f"{project_type}: expected dir '{d}' not found; got {sorted(actual_dirs)}"
            )

    def test_llm_app_agents_mentions_llm(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "llm-app", "llm-test")
        content = (project / "AGENTS.md").read_text(encoding="utf-8").lower()
        assert any(kw in content for kw in ("llm", "model", "prompt", "ai")), (
            "llm-app AGENTS.md should mention LLM or AI concepts"
        )

    def test_mcp_server_agents_mentions_mcp(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "mcp-server", "mcp-test")
        content = (project / "AGENTS.md").read_text(encoding="utf-8").lower()
        assert any(kw in content for kw in ("mcp", "model context", "tool", "server")), (
            "mcp-server AGENTS.md should mention MCP or tool concepts"
        )

    def test_agent_orchestration_agents_mentions_agents(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "agent-orchestration", "agents-test")
        content = (project / "AGENTS.md").read_text(encoding="utf-8").lower()
        assert any(kw in content for kw in ("agent", "orchestrat", "workflow", "ai")), (
            "agent-orchestration AGENTS.md should mention agents or orchestration"
        )

    def test_smart_contract_has_contracts_dir(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "smart-contract", "contract-test")
        assert (project / "contracts").is_dir(), "smart-contract must have contracts/ dir"
        assert (project / "deployments").is_dir(), "smart-contract must have deployments/ dir"

    def test_kubernetes_operator_has_controller_structure(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "kubernetes-operator", "k8s-test")
        assert (project / "controllers").is_dir()
        assert (project / "api").is_dir()

    def test_serverless_has_functions_dir(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "serverless", "sls-test")
        assert (project / "functions").is_dir()
        assert (project / "infrastructure").is_dir()

    def test_data_warehouse_has_dbt_structure(self, tmp_path: Path) -> None:
        """data-warehouse projects should have a dbt-style dir layout."""
        project = _scaffold(tmp_path, "data-warehouse", "dw-test")
        for d in ("models", "macros", "seeds", "analyses"):
            assert (project / d).is_dir(), (
                f"data-warehouse missing dbt dir: {d}"
            )

    def test_game_unity_has_assets_dir(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "game-unity", "unity-test")
        assert (project / "Assets").is_dir(), "game-unity must have Assets/ dir"

    def test_game_godot_has_scenes_dir(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "game-godot", "godot-test")
        assert (project / "scenes").is_dir(), "game-godot must have scenes/ dir"

    def test_desktop_tauri_has_src_tauri(self, tmp_path: Path) -> None:
        project = _scaffold(tmp_path, "desktop-tauri", "tauri-test")
        assert (project / "src-tauri").is_dir(), "desktop-tauri must have src-tauri/ dir"
