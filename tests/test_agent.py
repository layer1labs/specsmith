# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Phase 1 — Agent layer smoke tests.

Covers:
- AgentRunner construction and system prompt generation
- Tool registry building and handler dispatch
- Meta-command handling
- OllamaProvider availability and completion (when Ollama is running)
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from specsmith.agent.core import (
    CompletionResponse,
    Message,
    Role,
    Tool,
    ToolParam,
)
from specsmith.agent.runner import AgentRunner, SessionState, build_system_prompt
from specsmith.agent.skills import load_skills
from specsmith.agent.tools import build_tool_registry, get_tool_by_name

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def governed_project(tmp_path: Path) -> Path:
    """Create a minimal governed project directory for testing."""
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# AGENTS.md\n## Test Project\n", encoding="utf-8")
    ledger = tmp_path / "LEDGER.md"
    ledger.write_text("# LEDGER\n", encoding="utf-8")
    scaffold = tmp_path / "scaffold.yml"
    scaffold.write_text(
        yaml.dump({"name": "test", "type": "cli-python", "spec_version": "0.3.10"}),
        encoding="utf-8",
    )
    return tmp_path


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    """Tests for build_tool_registry and tool lookup."""

    def test_registry_returns_tools(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        assert isinstance(tools, list)
        assert len(tools) >= 15  # should have 20+ tools

    def test_each_tool_has_handler(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        for tool in tools:
            assert tool.handler is not None, f"Tool {tool.name} has no handler"

    def test_get_tool_by_name_found(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        audit = get_tool_by_name(tools, "audit")
        assert audit is not None
        assert audit.name == "audit"

    def test_get_tool_by_name_missing(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        result = get_tool_by_name(tools, "nonexistent_tool")
        assert result is None

    def test_tool_schemas_are_valid(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        for tool in tools:
            schema = tool.to_openai_schema()
            assert "type" in schema
            assert schema["type"] == "function"
            assert "function" in schema
            fn = schema["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn


# ---------------------------------------------------------------------------
# Tool Handlers
# ---------------------------------------------------------------------------


class TestToolHandlers:
    """Tests for critical tool handler dispatch."""

    def test_read_file_handler(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        read_file = get_tool_by_name(tools, "read_file")
        assert read_file is not None
        result = read_file.handler(path="AGENTS.md")
        assert "AGENTS.md" in result or "Test Project" in result

    def test_write_file_handler(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        write_file = get_tool_by_name(tools, "write_file")
        assert write_file is not None
        result = write_file.handler(path="test_output.txt", content="hello world")
        assert (
            "wrote" in result.lower()
            or "created" in result.lower()
            or "test_output" in result.lower()
        )
        assert (governed_project / "test_output.txt").read_text(encoding="utf-8") == "hello world"

    def test_run_command_handler(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        run_cmd = get_tool_by_name(tools, "run_command")
        assert run_cmd is not None
        # Use a safe cross-platform command
        result = run_cmd.handler(command="echo hello")
        assert "hello" in result.lower()

    def test_list_dir_handler(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        list_dir = get_tool_by_name(tools, "list_dir")
        assert list_dir is not None
        result = list_dir.handler()
        assert "AGENTS.md" in result or "scaffold.yml" in result

    def test_grep_files_handler(self, governed_project: Path) -> None:
        tools = build_tool_registry(str(governed_project))
        grep = get_tool_by_name(tools, "grep_files")
        assert grep is not None
        result = grep.handler(pattern="AGENTS")
        # Should find AGENTS.md reference or content
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------


class TestSystemPrompt:
    """Tests for system prompt generation."""

    def test_builds_with_agents_md(self, governed_project: Path) -> None:
        skills = load_skills(governed_project)
        prompt = build_system_prompt(str(governed_project), skills)
        assert "Test Project" in prompt
        assert "AEE" in prompt

    def test_builds_without_agents_md(self, tmp_path: Path) -> None:
        skills = load_skills(tmp_path)
        prompt = build_system_prompt(str(tmp_path), skills)
        assert "AGENTS.md not found" in prompt

    def test_includes_tool_error_rule(self, governed_project: Path) -> None:
        skills = load_skills(governed_project)
        prompt = build_system_prompt(str(governed_project), skills)
        assert "TOOL ERROR RULE" in prompt


# ---------------------------------------------------------------------------
# AgentRunner Construction
# ---------------------------------------------------------------------------


class TestAgentRunnerInit:
    """Tests for AgentRunner initialization."""

    def test_creates_with_defaults(self, governed_project: Path) -> None:
        runner = AgentRunner(project_dir=str(governed_project))
        assert runner.project_dir == str(governed_project.resolve())
        assert isinstance(runner._tools, list)
        assert len(runner._tools) >= 15

    def test_creates_with_ollama_provider(self, governed_project: Path) -> None:
        runner = AgentRunner(
            project_dir=str(governed_project),
            provider_name="ollama",
            model="qwen2.5:14b",
        )
        assert runner._provider_name == "ollama"
        assert runner._model == "qwen2.5:14b"


# ---------------------------------------------------------------------------
# SessionState
# ---------------------------------------------------------------------------


class TestSessionState:
    def test_initial_state(self) -> None:
        state = SessionState()
        assert state.session_tokens == 0
        assert state.total_cost_usd == 0.0
        assert state.tool_calls_made == 0

    def test_token_accumulation(self) -> None:
        state = SessionState()
        state.total_input_tokens = 100
        state.total_output_tokens = 50
        assert state.session_tokens == 150


# ---------------------------------------------------------------------------
# Meta Commands
# ---------------------------------------------------------------------------


class TestMetaCommands:
    """Tests for REPL meta-command dispatch."""

    def test_quick_commands_exist(self) -> None:
        assert "start" in AgentRunner.QUICK_COMMANDS
        assert "resume" in AgentRunner.QUICK_COMMANDS
        assert "save" in AgentRunner.QUICK_COMMANDS
        assert "audit" in AgentRunner.QUICK_COMMANDS
        assert "status" in AgentRunner.QUICK_COMMANDS

    def test_quick_command_values_are_strings(self) -> None:
        for key, value in AgentRunner.QUICK_COMMANDS.items():
            assert isinstance(value, str), f"Quick command '{key}' value is not a string"
            assert len(value) > 0


# ---------------------------------------------------------------------------
# Ollama Integration (requires running Ollama)
# ---------------------------------------------------------------------------


class TestOllamaIntegration:
    """Integration tests for OllamaProvider. Skipped if Ollama is not running."""

    @pytest.fixture(autouse=True)
    def _skip_if_no_ollama(self) -> None:
        from specsmith.agent.providers.ollama import OllamaProvider

        provider = OllamaProvider()
        if not provider.is_available():
            pytest.skip("Ollama is not running")

    def test_is_available(self) -> None:
        from specsmith.agent.providers.ollama import OllamaProvider

        p = OllamaProvider()
        assert p.is_available() is True

    def test_text_completion(self) -> None:
        from specsmith.agent.providers.ollama import OllamaProvider

        p = OllamaProvider(model="qwen2.5:14b")
        messages = [Message(role=Role.USER, content="Reply with just the word 'hello'.")]
        resp = p.complete(messages, max_tokens=32)
        assert isinstance(resp, CompletionResponse)
        assert len(resp.content) > 0
        assert resp.model == "qwen2.5:14b"
        assert resp.input_tokens > 0

    def test_tool_calling(self) -> None:
        from specsmith.agent.providers.ollama import OllamaProvider

        p = OllamaProvider(model="qwen2.5:14b")
        tools = [
            Tool(
                name="get_weather",
                description="Get the current weather for a location.",
                params=[ToolParam("location", "The city name", required=True)],
            ),
        ]
        messages = [
            Message(role=Role.USER, content="What's the weather in Paris?"),
        ]
        resp = p.complete(messages, tools=tools, max_tokens=256)
        assert isinstance(resp, CompletionResponse)
        # Model should either call the tool or respond with text
        if resp.has_tool_calls:
            tc = resp.tool_calls[0]
            assert tc["name"] == "get_weather"
            assert "location" in tc["input"]

    def test_provider_protocol(self) -> None:
        from specsmith.agent.core import BaseProvider
        from specsmith.agent.providers.ollama import OllamaProvider

        p = OllamaProvider()
        assert isinstance(p, BaseProvider)
        assert p.provider_name == "ollama"
