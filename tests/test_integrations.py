# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for specsmith agent integration adapters."""

from __future__ import annotations

from pathlib import Path

import pytest

from specsmith.config import ProjectConfig, ProjectType
from specsmith.integrations import get_adapter, list_adapters
from specsmith.integrations.agent_skill import AgentSkillAdapter
from specsmith.integrations.claude_code import ClaudeCodeAdapter
from specsmith.integrations.copilot import CopilotAdapter
from specsmith.integrations.cursor import CursorAdapter


@pytest.fixture
def config() -> ProjectConfig:
    return ProjectConfig(
        name="test-project",
        type=ProjectType.CLI_PYTHON,
        language="python",
        description="Test project",
        git_init=False,
    )


class TestAdapterRegistry:
    def test_list_adapters(self) -> None:
        adapters = list_adapters()
        assert "agent-skill" in adapters
        assert "claude-code" in adapters
        assert "cursor" in adapters
        assert "copilot" in adapters
        # Legacy aliases are not surfaced as canonical names.
        assert "warp" not in adapters

    def test_get_adapter(self) -> None:
        adapter = get_adapter("agent-skill")
        assert isinstance(adapter, AgentSkillAdapter)

    def test_get_adapter_legacy_alias(self) -> None:
        # Existing scaffold.yml configs that still say `warp` keep working.
        adapter = get_adapter("warp")
        assert isinstance(adapter, AgentSkillAdapter)

    def test_get_unknown_adapter(self) -> None:
        with pytest.raises(ValueError, match="Unknown integration"):
            get_adapter("nonexistent")


class TestAgentSkillAdapter:
    def test_generates_skill(self, config: ProjectConfig, tmp_path: Path) -> None:
        adapter = AgentSkillAdapter()
        files = adapter.generate(config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "SKILL.md"
        # Canonical generated path is .agents/skills/SKILL.md (rebrand from .warp/).
        assert files[0].parent.name == "skills"
        assert files[0].parent.parent.name == ".agents"
        content = files[0].read_text(encoding="utf-8")
        assert "test-project" in content
        assert "AGENTS.md" in content


class TestClaudeCodeAdapter:
    def test_generates_claude_md(self, config: ProjectConfig, tmp_path: Path) -> None:
        adapter = ClaudeCodeAdapter()
        files = adapter.generate(config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "CLAUDE.md"
        content = files[0].read_text(encoding="utf-8")
        assert "CLI tool (Python)" in content


class TestCursorAdapter:
    def test_generates_governance_mdc(self, config: ProjectConfig, tmp_path: Path) -> None:
        adapter = CursorAdapter()
        files = adapter.generate(config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "governance.mdc"
        content = files[0].read_text(encoding="utf-8")
        assert "alwaysApply: true" in content


class TestCopilotAdapter:
    def test_generates_copilot_instructions(self, config: ProjectConfig, tmp_path: Path) -> None:
        adapter = CopilotAdapter()
        files = adapter.generate(config, tmp_path)
        assert len(files) == 1
        assert files[0].name == "copilot-instructions.md"
        content = files[0].read_text(encoding="utf-8")
        assert "AGENTS.md" in content
