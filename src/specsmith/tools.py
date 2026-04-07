# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Verification tool registry — maps project types to lint/test/security/build tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specsmith.config import ProjectConfig

from specsmith.config import ProjectType


@dataclass(frozen=True)
class ToolSet:
    """Verification tools for a project type."""

    lint: list[str] = field(default_factory=list)
    typecheck: list[str] = field(default_factory=list)
    test: list[str] = field(default_factory=list)
    security: list[str] = field(default_factory=list)
    build: list[str] = field(default_factory=list)
    format: list[str] = field(default_factory=list)
    compliance: list[str] = field(default_factory=list)


# Default tool sets per project type
_TOOL_REGISTRY: dict[ProjectType, ToolSet] = {
    # Python
    ProjectType.CLI_PYTHON: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    ProjectType.LIBRARY_PYTHON: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    ProjectType.BACKEND_FRONTEND: ToolSet(
        lint=["ruff check", "eslint"],
        typecheck=["mypy", "tsc"],
        test=["pytest", "vitest"],
        security=["pip-audit", "npm audit"],
        format=["ruff format", "prettier"],
    ),
    ProjectType.BACKEND_FRONTEND_TRAY: ToolSet(
        lint=["ruff check", "eslint"],
        typecheck=["mypy", "tsc"],
        test=["pytest", "vitest"],
        security=["pip-audit", "npm audit"],
        format=["ruff format", "prettier"],
    ),
    # Hardware / Embedded
    ProjectType.FPGA_RTL: ToolSet(
        lint=["vsg", "verilator --lint-only"],
        test=["ghdl", "cocotb", "iverilog"],
        build=["vivado -mode batch", "quartus_sh"],
        format=[],
    ),
    ProjectType.YOCTO_BSP: ToolSet(
        lint=["oelint-adv"],
        test=["bitbake -c testimage"],
        build=["kas build", "bitbake"],
        security=[],
        compliance=["yocto-check-layer"],
    ),
    ProjectType.PCB_HARDWARE: ToolSet(
        lint=[],
        test=["drc-check", "erc-check"],
        build=["kicad-cli"],
        compliance=["bom-validate"],
    ),
    ProjectType.EMBEDDED_HARDWARE: ToolSet(
        lint=["clang-tidy", "cppcheck"],
        typecheck=["cppcheck"],
        test=["ctest", "unity"],
        build=["cmake", "make"],
        security=["flawfinder"],
        format=["clang-format"],
        compliance=["misra-c"],
    ),
    # Web / JS / TS
    ProjectType.WEB_FRONTEND: ToolSet(
        lint=["eslint"],
        typecheck=["tsc"],
        test=["vitest"],
        security=["npm audit"],
        format=["prettier"],
    ),
    ProjectType.FULLSTACK_JS: ToolSet(
        lint=["eslint"],
        typecheck=["tsc"],
        test=["vitest", "jest"],
        security=["npm audit"],
        format=["prettier"],
    ),
    # Rust
    ProjectType.CLI_RUST: ToolSet(
        lint=["cargo clippy"],
        typecheck=["cargo check"],
        test=["cargo test"],
        security=["cargo audit"],
        build=["cargo build"],
        format=["cargo fmt"],
    ),
    ProjectType.LIBRARY_RUST: ToolSet(
        lint=["cargo clippy"],
        typecheck=["cargo check"],
        test=["cargo test"],
        security=["cargo audit"],
        build=["cargo build"],
        format=["cargo fmt"],
    ),
    # Go
    ProjectType.CLI_GO: ToolSet(
        lint=["golangci-lint run"],
        typecheck=["go vet"],
        test=["go test ./..."],
        security=["govulncheck ./..."],
        build=["go build"],
        format=["gofmt"],
    ),
    # C / C++
    ProjectType.CLI_C: ToolSet(
        lint=["clang-tidy"],
        typecheck=["cppcheck"],
        test=["ctest"],
        security=["flawfinder"],
        build=["cmake --build ."],
        format=["clang-format"],
        compliance=["misra-c"],
    ),
    ProjectType.LIBRARY_C: ToolSet(
        lint=["clang-tidy"],
        typecheck=["cppcheck"],
        test=["ctest"],
        security=["flawfinder"],
        build=["cmake --build ."],
        format=["clang-format"],
    ),
    # .NET
    ProjectType.DOTNET_APP: ToolSet(
        lint=["dotnet format --verify-no-changes"],
        test=["dotnet test"],
        security=["dotnet list package --vulnerable"],
        build=["dotnet build"],
        format=["dotnet format"],
    ),
    # Mobile
    ProjectType.MOBILE_APP: ToolSet(
        lint=["flutter analyze", "eslint"],
        test=["flutter test", "jest"],
        build=["flutter build"],
    ),
    # DevOps / IaC
    ProjectType.DEVOPS_IAC: ToolSet(
        lint=["tflint", "ansible-lint"],
        test=["terratest"],
        security=["tfsec", "checkov"],
    ),
    # Data / ML
    ProjectType.DATA_ML: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    # Microservices
    ProjectType.MICROSERVICES: ToolSet(
        lint=["ruff check", "eslint"],
        test=["pytest", "jest"],
        security=["pip-audit", "npm audit"],
        build=["docker compose build"],
    ),
    # --- Document / Knowledge ---
    ProjectType.SPEC_DOCUMENT: ToolSet(
        lint=["vale", "markdownlint", "cspell"],
        format=["prettier"],
        build=["pandoc", "mkdocs build"],
        test=["markdown-link-check"],
    ),
    ProjectType.USER_MANUAL: ToolSet(
        lint=["vale", "markdownlint", "cspell"],
        format=["prettier"],
        build=["sphinx-build", "mkdocs build"],
        test=["markdown-link-check"],
    ),
    ProjectType.RESEARCH_PAPER: ToolSet(
        lint=["vale", "cspell", "chktex"],
        format=["latexindent"],
        build=["pdflatex", "bibtex"],
    ),
    # --- Business / Legal ---
    ProjectType.BUSINESS_PLAN: ToolSet(
        lint=["vale", "cspell"],
        format=["prettier"],
        build=["pandoc"],
    ),
    ProjectType.PATENT_APPLICATION: ToolSet(
        lint=["vale", "cspell"],
        format=["prettier"],
        build=["pandoc"],
        compliance=["claim-ref-check"],
    ),
    ProjectType.LEGAL_COMPLIANCE: ToolSet(
        lint=["vale", "cspell"],
        format=["prettier"],
        build=["pandoc"],
        compliance=["regulation-ref-check"],
    ),
    # --- Project management ---
    ProjectType.REQUIREMENTS_MGMT: ToolSet(
        lint=["vale", "markdownlint"],
        format=["prettier"],
        test=["req-trace"],
    ),
    ProjectType.API_SPECIFICATION: ToolSet(
        lint=["spectral", "buf lint"],
        test=["schemathesis", "dredd"],
        build=["openapi-generator", "protoc"],
        format=["prettier"],
    ),
    # --- More software ---
    ProjectType.MONOREPO: ToolSet(
        lint=["eslint", "ruff check"],
        test=["nx test", "turbo test"],
        build=["nx build", "turbo build"],
        security=["npm audit", "pip-audit"],
    ),
    ProjectType.BROWSER_EXTENSION: ToolSet(
        lint=["eslint", "web-ext lint"],
        typecheck=["tsc"],
        test=["vitest", "jest"],
        build=["web-ext build"],
        format=["prettier"],
        security=["npm audit"],
    ),
    # --- New FPGA vendor-specific types (same tools as generic fpga-rtl) ---
    ProjectType.FPGA_RTL_AMD: ToolSet(
        lint=["vsg", "verilator --lint-only"],
        test=["ghdl", "cocotb", "iverilog"],
        build=["vivado -mode batch"],  # AMD Vivado
        format=[],
    ),
    ProjectType.FPGA_RTL_INTEL: ToolSet(
        lint=["vsg", "verilator --lint-only"],
        test=["ghdl", "cocotb", "iverilog"],
        build=["quartus_sh --flow compile"],  # Intel/Altera Quartus
        format=[],
    ),
    ProjectType.FPGA_RTL_LATTICE: ToolSet(
        lint=["vsg", "verilator --lint-only"],
        test=["ghdl", "cocotb", "iverilog"],
        build=["diamondc"],  # Lattice Diamond
        format=[],
    ),
    ProjectType.MIXED_FPGA_EMBEDDED: ToolSet(
        lint=["vsg", "clang-tidy"],
        typecheck=["cppcheck"],
        test=["ghdl", "ctest"],
        build=["vivado -mode batch", "cmake"],
        format=["clang-format"],
    ),
    ProjectType.MIXED_FPGA_FIRMWARE: ToolSet(
        lint=["vsg", "ruff check"],
        typecheck=["mypy"],
        test=["ghdl", "pytest"],
        build=["vivado -mode batch"],
        format=["ruff format"],
    ),
    # --- AEE / Epistemic project types ---
    ProjectType.EPISTEMIC_PIPELINE: ToolSet(
        lint=["ruff check", "specsmith stress-test"],
        typecheck=["mypy"],
        test=["pytest", "specsmith epistemic-audit"],
        format=["ruff format"],
        compliance=["specsmith trace verify"],
    ),
    ProjectType.KNOWLEDGE_ENGINEERING: ToolSet(
        lint=["ruff check", "specsmith stress-test"],
        typecheck=["mypy"],
        test=["pytest", "specsmith epistemic-audit"],
        format=["ruff format"],
        compliance=["specsmith trace verify"],
    ),
    ProjectType.AEE_RESEARCH: ToolSet(
        lint=["vale", "specsmith stress-test"],
        test=["pytest", "specsmith epistemic-audit"],
        format=["prettier"],
        compliance=["specsmith trace verify"],
    ),
}


def get_tools(config: ProjectConfig) -> ToolSet:
    """Get the verification tool set for a project config.

    Uses the tool registry defaults, overridden by any explicit verification_tools.
    """
    # config.type is str; _TOOL_REGISTRY has ProjectType keys (which extend str).
    # Convert via ProjectType() with a fallback to avoid KeyError on custom types.
    try:
        pt = ProjectType(config.type)
    except ValueError:
        pt = ProjectType.CLI_PYTHON
    base = _TOOL_REGISTRY.get(pt, ToolSet())

    if not config.verification_tools:
        return base

    # Merge overrides
    overrides = config.verification_tools
    return ToolSet(
        lint=overrides.get("lint", " ").split(",") if "lint" in overrides else base.lint,
        typecheck=(
            overrides.get("typecheck", "").split(",")
            if "typecheck" in overrides
            else base.typecheck
        ),
        test=overrides.get("test", "").split(",") if "test" in overrides else base.test,
        security=(
            overrides.get("security", "").split(",") if "security" in overrides else base.security
        ),
        build=overrides.get("build", "").split(",") if "build" in overrides else base.build,
        format=overrides.get("format", "").split(",") if "format" in overrides else base.format,
        compliance=(
            overrides.get("compliance", "").split(",")
            if "compliance" in overrides
            else base.compliance
        ),
    )


def list_tools_for_type(project_type: ProjectType) -> ToolSet:
    """Get default tools for a project type."""
    return _TOOL_REGISTRY.get(project_type, ToolSet())


# ---------------------------------------------------------------------------
# CI environment metadata per language
# ---------------------------------------------------------------------------

LANG_CI_META: dict[str, dict[str, str]] = {
    "python": {
        "gh_setup": (
            "      - uses: actions/setup-python@v6\n"
            '        with:\n          python-version: "3.12"\n          cache: pip\n'
        ),
        "docker_image": "python:3.12-slim",
        "install": 'pip install -e ".[dev]"',
        "bb_cache": "pip",
    },
    "rust": {
        "gh_setup": "      - uses: dtolnay/rust-toolchain@stable\n",
        "docker_image": "rust:latest",
        "install": "",
    },
    "go": {
        "gh_setup": (
            '      - uses: actions/setup-go@v5\n        with:\n          go-version: "1.22"\n'
        ),
        "docker_image": "golang:1.22",
        "install": "",
    },
    "javascript": {
        "gh_setup": (
            "      - uses: actions/setup-node@v4\n"
            '        with:\n          node-version: "20"\n          cache: npm\n'
        ),
        "docker_image": "node:20",
        "install": "npm ci",
        "bb_cache": "node",
    },
    "typescript": {
        "gh_setup": (
            "      - uses: actions/setup-node@v4\n"
            '        with:\n          node-version: "20"\n          cache: npm\n'
        ),
        "docker_image": "node:20",
        "install": "npm ci",
        "bb_cache": "node",
    },
    "csharp": {
        "gh_setup": "      - uses: actions/setup-dotnet@v4\n",
        "docker_image": "mcr.microsoft.com/dotnet/sdk:8.0",
        "install": "dotnet restore",
    },
    "dart": {
        "gh_setup": "      - uses: subosito/flutter-action@v2\n",
        "docker_image": "ghcr.io/cirruslabs/flutter:latest",
        "install": "flutter pub get",
    },
    "c": {
        "gh_setup": "",
        "docker_image": "gcc:latest",
        "install": "",
    },
    "cpp": {
        "gh_setup": "",
        "docker_image": "gcc:latest",
        "install": "",
    },
    "terraform": {
        "gh_setup": "      - uses: hashicorp/setup-terraform@v3\n",
        "docker_image": "hashicorp/terraform:latest",
        "install": "terraform init",
    },
    "vhdl": {
        "gh_setup": "",
        "docker_image": "ghdl/ghdl:latest",
        "install": "",
    },
    "verilog": {
        "gh_setup": "",
        "docker_image": "verilator/verilator:latest",
        "install": "",
    },
    "systemverilog": {
        "gh_setup": "",
        "docker_image": "verilator/verilator:latest",
        "install": "",
    },
    "bitbake": {
        "gh_setup": "",
        "docker_image": "crops/poky:latest",
        "install": "pip install oelint-adv",
    },
    "devicetree": {
        "gh_setup": "",
        "docker_image": "gcc:latest",
        "install": "",
    },
    "markdown": {
        "gh_setup": (
            "      - uses: actions/setup-python@v6\n"
            '        with:\n          python-version: "3.12"\n'
        ),
        "docker_image": "pandoc/core:latest",
        "install": "pip install vale mkdocs markdownlint-cli2 cspell",
    },
    "latex": {
        "gh_setup": "",
        "docker_image": "texlive/texlive:latest",
        "install": "",
    },
    "openapi": {
        "gh_setup": (
            "      - uses: actions/setup-node@v4\n"
            '        with:\n          node-version: "20"\n          cache: npm\n'
        ),
        "docker_image": "node:20",
        "install": "npm ci",
        "bb_cache": "node",
    },
    "protobuf": {
        "gh_setup": "",
        "docker_image": "namely/protoc:latest",
        "install": "",
    },
}

# Map format tool → CI check-mode command
_FORMAT_CHECK_MAP: dict[str, str] = {
    "ruff format": "ruff format --check .",
    "cargo fmt": "cargo fmt -- --check",
    "prettier": "npx prettier --check .",
    "gofmt": 'test -z "$(gofmt -l .)"',
    "clang-format": "clang-format --dry-run --Werror",
    "dotnet format": "dotnet format --verify-no-changes",
}


def get_format_check_commands(tools: ToolSet) -> list[str]:
    """Convert format commands to CI check-mode equivalents."""
    checks: list[str] = []
    for cmd in tools.format:
        for prefix, check_cmd in _FORMAT_CHECK_MAP.items():
            if cmd.startswith(prefix):
                checks.append(check_cmd)
                break
    return checks
