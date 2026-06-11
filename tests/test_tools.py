# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for the verification tool registry."""

from __future__ import annotations

from specsmith.config import ProjectConfig, ProjectType
from specsmith.tools import (
    LANG_CI_META,
    ToolSet,
    get_format_check_commands,
    get_tools,
    list_tools_for_type,
)


class TestToolRegistry:
    def test_python_cli_has_ruff(self) -> None:
        ts = list_tools_for_type(ProjectType.CLI_PYTHON)
        assert "ruff check" in ts.lint
        assert "mypy" in ts.typecheck
        assert "pytest" in ts.test
        assert "pip-audit" in ts.security
        assert "ruff format" in ts.format

    def test_rust_cli_has_clippy(self) -> None:
        ts = list_tools_for_type(ProjectType.CLI_RUST)
        assert "cargo clippy" in ts.lint
        assert "cargo check" in ts.typecheck
        assert "cargo test" in ts.test
        assert "cargo audit" in ts.security
        assert "cargo fmt" in ts.format

    def test_go_cli_tools(self) -> None:
        ts = list_tools_for_type(ProjectType.CLI_GO)
        assert "golangci-lint run" in ts.lint
        assert "go test ./..." in ts.test
        assert "govulncheck ./..." in ts.security

    def test_web_frontend_tools(self) -> None:
        ts = list_tools_for_type(ProjectType.WEB_FRONTEND)
        assert "eslint" in ts.lint
        assert "tsc" in ts.typecheck
        assert "vitest" in ts.test

    def test_fpga_tools(self) -> None:
        ts = list_tools_for_type(ProjectType.FPGA_RTL)
        assert "vsg" in ts.lint
        assert "ghdl" in ts.test
        assert "vivado -mode batch" in ts.build

    def test_embedded_hardware_tools(self) -> None:
        ts = list_tools_for_type(ProjectType.EMBEDDED_HARDWARE)
        assert "clang-tidy" in ts.lint
        assert "misra-c" in ts.compliance

    def test_dotnet_tools(self) -> None:
        ts = list_tools_for_type(ProjectType.DOTNET_APP)
        assert "dotnet test" in ts.test
        assert "dotnet build" in ts.build

    def test_unknown_type_returns_empty(self) -> None:
        # Enum members always have a registry entry, but verify default behavior
        ts = ToolSet()
        assert ts.lint == []
        assert ts.test == []

    def test_all_types_have_entries(self) -> None:
        """All project types must have at least one tool registered.

        We now have 33 types (30 original + 3 AEE types added in 0.3.0).
        """
        types = list(ProjectType)
        # Reflect actual count — update this when new types are added
        assert len(types) >= 30, f"Too few types: {len(types)}"
        for pt in types:
            ts = list_tools_for_type(pt)
            # Every type should have at least one tool category populated
            has_any = bool(
                ts.lint
                or ts.typecheck
                or ts.test
                or ts.security
                or ts.build
                or ts.format
                or ts.compliance
            )
            assert has_any, f"{pt.value} has no tools registered"


class TestGetTools:
    def test_default_from_type(self) -> None:
        cfg = ProjectConfig(
            name="t",
            type=ProjectType.CLI_PYTHON,
            language="python",
            git_init=False,
        )
        ts = get_tools(cfg)
        assert "ruff check" in ts.lint

    def test_override_lint(self) -> None:
        cfg = ProjectConfig(
            name="t",
            type=ProjectType.CLI_PYTHON,
            language="python",
            git_init=False,
            verification_tools={"lint": "flake8,pylint"},
        )
        ts = get_tools(cfg)
        assert ts.lint == ["flake8", "pylint"]
        # Non-overridden categories should keep defaults
        assert "mypy" in ts.typecheck


class TestFormatCheckCommands:
    def test_ruff_format(self) -> None:
        ts = ToolSet(format=["ruff format"])
        checks = get_format_check_commands(ts)
        assert "ruff format --check ." in checks

    def test_cargo_fmt(self) -> None:
        ts = ToolSet(format=["cargo fmt"])
        checks = get_format_check_commands(ts)
        assert "cargo fmt -- --check" in checks

    def test_prettier(self) -> None:
        ts = ToolSet(format=["prettier"])
        checks = get_format_check_commands(ts)
        assert "npx prettier --check ." in checks

    def test_empty_format(self) -> None:
        ts = ToolSet()
        assert get_format_check_commands(ts) == []


class TestLangCIMeta:
    def test_python_meta(self) -> None:
        meta = LANG_CI_META["python"]
        assert "setup-python" in meta["gh_setup"]
        assert meta["docker_image"] == "python:3.12-slim"

    def test_rust_meta(self) -> None:
        meta = LANG_CI_META["rust"]
        assert "rust-toolchain" in meta["gh_setup"]

    def test_go_meta(self) -> None:
        meta = LANG_CI_META["go"]
        assert "setup-go" in meta["gh_setup"]

    def test_js_meta(self) -> None:
        meta = LANG_CI_META["javascript"]
        assert "setup-node" in meta["gh_setup"]
        assert meta["install"] == "npm ci"

    def test_all_languages_have_docker_image(self) -> None:
        for lang, meta in LANG_CI_META.items():
            assert "docker_image" in meta, f"{lang} missing docker_image"
