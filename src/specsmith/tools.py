# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Verification tool registry — maps project types to lint/test/security/build tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from specsmith.config import ProjectConfig

from specsmith.config import ProjectType

# ---------------------------------------------------------------------------
# Brief lang version anchor — no release tags exist; both identifiers are kept.
# Update both when a new Brief version is adopted.
# ---------------------------------------------------------------------------
BRIEF_LANG_VERSION: str = "v0.14.0"
BRIEF_LANG_COMMIT: str = "6a43c4aebcc5c6c774dbc2908445fb19486e8043"


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
        test=["kas-container", "bitbake -c testimage"],
        build=["kas build", "kas-container build", "bitbake"],
        security=[],
        compliance=["yocto-check-layer"],
    ),
    ProjectType.PCB_HARDWARE: ToolSet(
        # KiCad CLI for automated DRC/ERC + Gerber generation
        lint=["kicad-cli pcb drc"],
        test=["kicad-cli sch erc"],
        build=["kicad-cli pcb export gerbers"],
        compliance=["kicad-cli sch export bom"],
    ),
    ProjectType.EMBEDDED_HARDWARE: ToolSet(
        # Detects Zephyr/west projects at runtime; generic C/C++ fallback.
        lint=["clang-tidy", "cppcheck"],
        typecheck=["cppcheck"],
        # west twister for Zephyr; ctest for bare CMake; unity for bare FreeRTOS
        test=["west twister", "ctest", "unity"],
        build=["west build", "cmake", "make"],
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
    # Mobile (Flutter / React Native / iOS native / Android native)
    ProjectType.MOBILE_APP: ToolSet(
        # Flutter is the common cross-platform case; xcodebuild for iOS-only;
        # ./gradlew for Android-only; jest/jest-expo for RN
        lint=["flutter analyze", "dart analyze", "ktlint"],
        typecheck=["flutter analyze"],
        test=["flutter test", "jest"],
        build=["flutter build", "xcodebuild", "./gradlew assembleRelease"],
        security=["mobsfscan"],
        format=["dart format"],
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
    # New project types
    ProjectType.EMBEDDED_PYTHON_HMI: ToolSet(
        # Hardware-interfacing Python kiosk — Qt/PySide6 + hardware comms
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
        build=["python -m build"],
    ),
    ProjectType.RESEARCH_PYTHON: ToolSet(
        # Experiment/research packages — no CLI, data integrity checks
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    ProjectType.SAFETY_CRITICAL: ToolSet(
        # IEC 60204-1/62061/61508 safety-critical embedded
        lint=["clang-tidy", "cppcheck"],
        test=["west twister", "ctest"],
        security=["flawfinder"],
        build=["cmake --build .", "make"],
        format=["clang-format"],
        compliance=["misra-c", "polyspace"],
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
    # --- Modern web frameworks ---
    ProjectType.NEXTJS_APP: ToolSet(
        lint=["eslint", "next lint"],
        typecheck=["tsc"],
        test=["jest", "vitest", "playwright"],
        security=["npm audit"],
        build=["next build"],
        format=["prettier"],
    ),
    ProjectType.NUXT_APP: ToolSet(
        lint=["eslint"],
        typecheck=["tsc"],
        test=["vitest", "playwright"],
        security=["npm audit"],
        build=["nuxt build"],
        format=["prettier"],
    ),
    ProjectType.SVELTEKIT_APP: ToolSet(
        lint=["eslint"],
        typecheck=["tsc"],
        test=["vitest", "playwright"],
        security=["npm audit"],
        build=["vite build"],
        format=["prettier"],
    ),
    ProjectType.REMIX_APP: ToolSet(
        lint=["eslint"],
        typecheck=["tsc"],
        test=["vitest", "playwright"],
        security=["npm audit"],
        build=["remix vite:build"],
        format=["prettier"],
    ),
    ProjectType.ASTRO_SITE: ToolSet(
        lint=["eslint"],
        typecheck=["tsc"],
        test=["vitest", "playwright"],
        security=["npm audit"],
        build=["astro build"],
        format=["prettier"],
    ),
    # --- IP / Patent prosecution ---
    ProjectType.PATENT_PROSECUTION: ToolSet(
        lint=["vale", "cspell"],
        format=["prettier"],
        build=["pandoc"],
        compliance=["specsmith trace verify", "claim-ref-check"],
        test=["markdown-link-check"],
    ),
    # --- AI / LLM / Agents ---
    ProjectType.LLM_APP: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    ProjectType.AGENT_ORCHESTRATION: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    ProjectType.MCP_SERVER: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    ProjectType.RAG_PIPELINE: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
    ),
    ProjectType.MLOPS_PLATFORM: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
        build=["python -m build"],
    ),
    # --- JVM ---
    ProjectType.JAVA_SPRING: ToolSet(
        lint=["checkstyle", "pmd"],
        typecheck=["javac"],
        test=["mvn test", "./gradlew test"],
        security=["owasp-dependency-check"],
        build=["mvn package", "./gradlew build"],
        format=["google-java-format"],
    ),
    ProjectType.JAVA_LIBRARY: ToolSet(
        lint=["checkstyle"],
        typecheck=["javac"],
        test=["mvn test", "./gradlew test"],
        security=["owasp-dependency-check"],
        build=["mvn package"],
        format=["google-java-format"],
    ),
    # --- Cloud / Infrastructure ---
    ProjectType.SERVERLESS: ToolSet(
        lint=["eslint", "ruff check"],
        typecheck=["tsc"],
        test=["jest", "pytest"],
        security=["npm audit", "pip-audit"],
        build=["serverless deploy --dry-run", "sam build"],
    ),
    ProjectType.KUBERNETES_OPERATOR: ToolSet(
        lint=["golangci-lint run"],
        typecheck=["go vet"],
        test=["go test ./..."],
        security=["govulncheck ./..."],
        build=["go build", "docker build ."],
        format=["gofmt"],
        compliance=["kubeconform"],
    ),
    ProjectType.STREAMING_PIPELINE: ToolSet(
        lint=["ruff check"],
        typecheck=["mypy"],
        test=["pytest"],
        security=["pip-audit"],
        format=["ruff format"],
        build=["docker compose build"],
    ),
    ProjectType.DATA_WAREHOUSE: ToolSet(
        lint=["sqlfluff lint"],
        test=["dbt test"],
        build=["dbt build"],
        format=["sqlfluff fix"],
    ),
    # --- Game development ---
    ProjectType.GAME_UNITY: ToolSet(
        lint=[],
        test=["unity-test-runner"],
        build=["unity -batchmode -buildLinux64Player"],
    ),
    ProjectType.GAME_GODOT: ToolSet(
        lint=["gdlint"],
        test=["godot --headless --script res://tests/run_all.gd"],
        build=["godot --export-release"],
        format=["gdformat"],
    ),
    # --- Web3 ---
    ProjectType.SMART_CONTRACT: ToolSet(
        lint=["solhint"],
        typecheck=["tsc"],
        test=["hardhat test", "forge test"],
        security=["slither", "mythril"],
        build=["hardhat compile", "forge build"],
        format=["prettier"],
    ),
    # --- Desktop ---
    ProjectType.DESKTOP_ELECTRON: ToolSet(
        lint=["eslint"],
        typecheck=["tsc"],
        test=["jest", "playwright"],
        security=["npm audit", "electronegativity"],
        build=["electron-builder"],
        format=["prettier"],
    ),
    ProjectType.DESKTOP_TAURI: ToolSet(
        lint=["cargo clippy", "eslint"],
        typecheck=["cargo check", "tsc"],
        test=["cargo test", "vitest"],
        security=["cargo audit", "npm audit"],
        build=["cargo tauri build"],
        format=["cargo fmt", "prettier"],
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
    # --- Brief lang (v0.14.0 @ 6a43c4ae, github.com/Randozart/brief-lang) ---
    # brief-compiler check      — type-checker + contract verifier (normal mode)
    # brief-compiler check --strict — proof engine; hard errors on incomplete contracts
    # cargo test --lib          — compiler-internal tests (Cargo.toml must exist)
    # brief-compiler rust       — primary software build target
    # brief-compiler llvm       — compile to LLVM IR
    # brief-compiler lsp        — start LSP server for editor integration
    ProjectType.BRIEF_LANG: ToolSet(
        lint=["brief-compiler check"],
        typecheck=["brief-compiler check --strict"],
        test=["cargo test --lib"],
        build=["brief-compiler rust", "brief-compiler llvm"],
        security=[],
        format=[],
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
    # Brief lang — compiler is built from source (Rust), no pre-built binary yet
    "brief": {
        "gh_setup": "      - uses: dtolnay/rust-toolchain@stable\n",
        "docker_image": "rust:latest",
        "install": "cargo build --release",
        "brief_compiler": "./target/release/brief-compiler",
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
