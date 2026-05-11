# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
"""Tests for Skills Builder and MCP Server Generator."""

from __future__ import annotations

from pathlib import Path


class TestSkillsBuilder:
    def test_build_skill(self, tmp_path: Path) -> None:
        from specsmith.skills_builder import build_skill

        skill = build_skill("Summarize Python files into bullet points", str(tmp_path))
        assert skill.id.startswith("skill-")
        assert skill.name == "Summarize Python files into bullet points"
        assert skill.purpose
        assert len(skill.activation_rules) > 0

    def test_skill_saved_to_disk(self, tmp_path: Path) -> None:
        from specsmith.skills_builder import build_skill

        skill = build_skill("Analyze code complexity", str(tmp_path))
        skill_dir = tmp_path / ".specsmith" / "skills" / skill.id
        assert (skill_dir / "SKILL.md").is_file()
        assert (skill_dir / "skill.json").is_file()
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert "Analyze code complexity" in content

    def test_list_skills_empty(self, tmp_path: Path) -> None:
        from specsmith.skills_builder import list_skills

        assert list_skills(str(tmp_path)) == []

    def test_list_skills_after_build(self, tmp_path: Path) -> None:
        from specsmith.skills_builder import build_skill, list_skills

        build_skill("Skill A", str(tmp_path))
        build_skill("Skill B", str(tmp_path))
        skills = list_skills(str(tmp_path))
        assert len(skills) == 2

    def test_activate_skill(self, tmp_path: Path) -> None:
        from specsmith.skills_builder import activate_skill, build_skill, list_skills

        skill = build_skill("Activatable skill", str(tmp_path))
        assert not skill.active
        assert activate_skill(skill.id, str(tmp_path))
        skills = list_skills(str(tmp_path))
        assert any(s.active for s in skills)

    def test_skill_to_dict(self) -> None:
        from specsmith.skills_builder import SkillSpec

        spec = SkillSpec(id="test", name="Test", purpose="Testing")
        d = spec.to_dict()
        assert d["id"] == "test"
        assert d["name"] == "Test"


class TestMCPGenerator:
    def test_generate_server(self, tmp_path: Path) -> None:
        from specsmith.mcp_generator import generate_mcp_server

        spec = generate_mcp_server("Search USPTO patents by keyword", str(tmp_path))
        assert spec.id.startswith("mcp-")
        assert len(spec.tools) == 1
        assert spec.transport == "stdio"

    def test_server_files_created(self, tmp_path: Path) -> None:
        from specsmith.mcp_generator import generate_mcp_server

        spec = generate_mcp_server("Lookup weather data", str(tmp_path))
        server_dir = tmp_path / ".specsmith" / "mcp-servers" / spec.id
        assert (server_dir / "server.py").is_file()
        assert (server_dir / "tool_schema.json").is_file()
        assert (server_dir / "README.md").is_file()

    def test_server_py_contains_tool(self, tmp_path: Path) -> None:
        from specsmith.mcp_generator import generate_mcp_server

        spec = generate_mcp_server("Calculate BMI", str(tmp_path))
        server_dir = tmp_path / ".specsmith" / "mcp-servers" / spec.id
        content = (server_dir / "server.py").read_text(encoding="utf-8")
        assert "FastMCP" in content
        assert "@mcp.tool()" in content

    def test_list_servers_empty(self, tmp_path: Path) -> None:
        from specsmith.mcp_generator import list_mcp_servers

        assert list_mcp_servers(str(tmp_path)) == []

    def test_list_servers_after_generate(self, tmp_path: Path) -> None:
        from specsmith.mcp_generator import generate_mcp_server, list_mcp_servers

        generate_mcp_server("Tool A", str(tmp_path))
        generate_mcp_server("Tool B", str(tmp_path))
        servers = list_mcp_servers(str(tmp_path))
        assert len(servers) == 2

    def test_http_transport(self, tmp_path: Path) -> None:
        from specsmith.mcp_generator import generate_mcp_server

        spec = generate_mcp_server("HTTP tool", str(tmp_path), transport="http", port=9000)
        assert spec.transport == "http"
        assert spec.port == 9000
        server_dir = tmp_path / ".specsmith" / "mcp-servers" / spec.id
        content = (server_dir / "server.py").read_text(encoding="utf-8")
        assert "streamable-http" in content
