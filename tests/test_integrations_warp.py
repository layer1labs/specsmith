# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the Warp native integration adapter (REQ-444)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from specsmith.config import ProjectConfig, ProjectType
from specsmith.integrations import get_adapter, list_adapters
from specsmith.integrations.warp import WarpAdapter


@pytest.fixture
def config() -> ProjectConfig:
    return ProjectConfig(
        name="test-project",
        type=ProjectType.CLI_PYTHON,
        language="python",
        description="Test project",
        git_init=False,
    )


class TestWarpAdapterRegistry:
    def test_warp_is_registered(self) -> None:
        assert "warp" in list_adapters()

    def test_get_adapter_returns_warp(self) -> None:
        assert isinstance(get_adapter("warp"), WarpAdapter)

    def test_name_and_description(self) -> None:
        adapter = WarpAdapter()
        assert adapter.name == "warp"
        assert adapter.description


class TestWarpAdapterGenerate:
    def test_generates_expected_files(self, config: ProjectConfig, tmp_path: Path) -> None:
        files = WarpAdapter().generate(config, tmp_path)
        rel = {p.relative_to(tmp_path).as_posix() for p in files}
        assert ".warp/specsmith-mcp.json" in rel
        assert ".warp/launch_configs/specsmith-governed.yaml" in rel
        assert ".agents/skills/SKILL.md" in rel

    def test_mcp_config_is_valid_json(self, config: ProjectConfig, tmp_path: Path) -> None:
        WarpAdapter().generate(config, tmp_path)
        mcp_path = tmp_path / ".warp" / "specsmith-mcp.json"
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        assert "specsmith-governance" in data
        entry = data["specsmith-governance"]
        assert "command" in entry
        assert entry["args"][-1] == "serve"

    def test_mcp_config_matches_shared_builder(self, config: ProjectConfig, tmp_path: Path) -> None:
        from specsmith.mcp_server import build_warp_mcp_config

        WarpAdapter().generate(config, tmp_path)
        mcp_path = tmp_path / ".warp" / "specsmith-mcp.json"
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
        assert data == build_warp_mcp_config()

    def test_launch_config_references_specsmith_run(
        self, config: ProjectConfig, tmp_path: Path
    ) -> None:
        WarpAdapter().generate(config, tmp_path)
        launch = tmp_path / ".warp" / "launch_configs" / "specsmith-governed.yaml"
        content = launch.read_text(encoding="utf-8")
        assert "specsmith run" in content
        assert config.name in content

    def test_skill_file_content(self, config: ProjectConfig, tmp_path: Path) -> None:
        WarpAdapter().generate(config, tmp_path)
        skill = tmp_path / ".agents" / "skills" / "SKILL.md"
        content = skill.read_text(encoding="utf-8")
        assert "test-project" in content
        assert "AGENTS.md" in content

    def test_idempotent(self, config: ProjectConfig, tmp_path: Path) -> None:
        first = WarpAdapter().generate(config, tmp_path)
        first_contents = {p: p.read_text(encoding="utf-8") for p in first}
        second = WarpAdapter().generate(config, tmp_path)
        assert {p.name for p in first} == {p.name for p in second}
        for path, text in first_contents.items():
            assert path.read_text(encoding="utf-8") == text
