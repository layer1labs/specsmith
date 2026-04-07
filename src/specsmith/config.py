# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Project configuration schema for specsmith."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    """Supported project types from the spec (Section 17)."""

    # Python
    BACKEND_FRONTEND = "backend-frontend"
    BACKEND_FRONTEND_TRAY = "backend-frontend-tray"
    CLI_PYTHON = "cli-python"
    LIBRARY_PYTHON = "library-python"
    # Hardware / Embedded — vendor-specific FPGA types
    EMBEDDED_HARDWARE = "embedded-hardware"
    FPGA_RTL = "fpga-rtl"              # Generic / open-source flow (Yosys)
    FPGA_RTL_XILINX = "fpga-rtl-xilinx"   # AMD/Xilinx Vivado / ISE
    FPGA_RTL_INTEL = "fpga-rtl-intel"     # Intel/Altera Quartus Prime
    FPGA_RTL_LATTICE = "fpga-rtl-lattice" # Lattice Diamond / Radiant
    MIXED_FPGA_EMBEDDED = "mixed-fpga-embedded"  # FPGA + embedded C/C++ driver
    MIXED_FPGA_FIRMWARE = "mixed-fpga-firmware"  # FPGA + Python/C verification
    YOCTO_BSP = "yocto-bsp"
    PCB_HARDWARE = "pcb-hardware"
    # Web / JS / TS
    WEB_FRONTEND = "web-frontend"
    FULLSTACK_JS = "fullstack-js"
    # Systems languages
    CLI_RUST = "cli-rust"
    CLI_GO = "cli-go"
    CLI_C = "cli-c"
    LIBRARY_RUST = "library-rust"
    LIBRARY_C = "library-c"
    # Other platforms
    DOTNET_APP = "dotnet-app"
    MOBILE_APP = "mobile-app"
    # Infrastructure / Data
    DEVOPS_IAC = "devops-iac"
    DATA_ML = "data-ml"
    MICROSERVICES = "microservices"
    # Document / Knowledge
    SPEC_DOCUMENT = "spec-document"
    USER_MANUAL = "user-manual"
    RESEARCH_PAPER = "research-paper"
    # Business / Legal
    BUSINESS_PLAN = "business-plan"
    PATENT_APPLICATION = "patent-application"
    LEGAL_COMPLIANCE = "legal-compliance"
    # Project management
    REQUIREMENTS_MGMT = "requirements-mgmt"
    API_SPECIFICATION = "api-specification"
    # More software
    MONOREPO = "monorepo"
    BROWSER_EXTENSION = "browser-extension"
    # Applied Epistemic Engineering
    EPISTEMIC_PIPELINE = "epistemic-pipeline"
    KNOWLEDGE_ENGINEERING = "knowledge-engineering"
    AEE_RESEARCH = "aee-research"


class Platform(str, Enum):
    """Target platforms."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class ProjectConfig(BaseModel):
    """Configuration for a specsmith-generated project scaffold.

    This model validates the scaffold.yml input file and interactive prompts.
    """

    # Config inheritance
    extends: str = Field(
        default="",
        description="Path or URL to parent scaffold.yml to inherit defaults from",
    )

    name: str = Field(description="Project name (used for directory and package name)")
    # str (not ProjectType enum) so scaffold.yml files with custom or vendor-specific
    # types (e.g. 'fpga-rtl-xilinx') don't crash pydantic validation.
    # Use ProjectType enum values as constants when checking the type.
    type: str = Field(
        default=ProjectType.CLI_PYTHON.value,
        description="Project type. Should match a ProjectType value.",
    )
    platforms: list[Platform] = Field(
        default=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
        description="Target platforms",
    )
    language: str = Field(default="python", description="Primary language/runtime")
    spec_version: str = Field(default="0.3.0", description="Spec version to scaffold from")
    description: str = Field(default="", description="Short project description")

    # Options
    services: bool = Field(
        default=False,
        description="Include services.md for daemon/service projects",
    )
    shell_wrappers: bool = Field(default=False, description="Include shell wrapper scripts")
    exec_shims: bool = Field(default=True, description="Include exec.cmd/exec.sh timeout shims")
    git_init: bool = Field(default=True, description="Initialize git repository")

    # VCS platform
    vcs_platform: str = Field(
        default="github",
        description="VCS platform (github, gitlab, bitbucket)",
    )

    # Branching strategy
    branching_strategy: str = Field(
        default="gitflow",
        description="Branching strategy (gitflow, trunk-based, github-flow)",
    )
    default_branch: str = Field(
        default="main",
        description="Default/production branch name",
    )
    develop_branch: str = Field(
        default="develop",
        description="Development integration branch (gitflow only)",
    )
    require_pr_reviews: bool = Field(
        default=True,
        description="Require pull request reviews before merge",
    )
    required_approvals: int = Field(
        default=1,
        description="Number of required PR approvals",
    )
    require_ci_pass: bool = Field(
        default=True,
        description="Require CI checks to pass before merge",
    )
    allow_force_push: bool = Field(
        default=False,
        description="Allow force push to protected branches",
    )
    use_remote_rules: bool = Field(
        default=False,
        description="Accept branch protection rules from remote if already configured",
    )

    # Verification tools (auto-populated from type+language, overridable)
    verification_tools: dict[str, str] = Field(
        default_factory=dict,
        description="Tool overrides by category: lint, typecheck, test, security, build, format",
    )

    # Import detection (populated by specsmith import)
    detected_build_system: str = Field(default="", description="Build system detected by import")
    detected_test_framework: str = Field(
        default="", description="Test framework detected by import"
    )

    # License
    license: str = Field(
        default="MIT",
        description="SPDX license identifier (MIT, Apache-2.0, GPL-3.0-only, etc.)",
    )

    # Community files
    community_files: list[str] = Field(
        default=["contributing", "license", "security", "coc", "pr-template", "issue-templates"],
        description="Community/compliance files to generate",
    )

    # Multi-discipline support
    auxiliary_disciplines: list[str] = Field(
        default=[],
        description=(
            "Additional project disciplines beyond the primary type. "
            "e.g. ['embedded-c', 'cli-python'] for an FPGA project with C drivers "
            "and Python verification. Each discipline generates extra CI jobs and "
            "tool registry entries."
        ),
    )

    # FPGA-specific
    fpga_vendor: str = Field(
        default="",
        description="FPGA vendor/toolchain: xilinx, intel, lattice, gowin (blank = generic/OSS)",
    )

    # Agent integrations
    integrations: list[str] = Field(
        default=["agents-md"],
        description="Agent integrations to generate (agents-md, warp, claude-code, cursor, etc.)",
    )

    # Applied Epistemic Engineering configuration
    enable_epistemic: bool = Field(
        default=False,
        description="Enable AEE epistemic governance layer (belief registry, failure modes, etc.)",
    )
    epistemic_threshold: float = Field(
        default=0.7,
        description="Certainty threshold for epistemic-audit (0.0-1.0; default 0.7)",
    )
    enable_trace_vault: bool = Field(
        default=False,
        description="Enable cryptographic trace vault (.specsmith/trace.jsonl)",
    )

    @property
    def package_name(self) -> str:
        """Python-safe package name derived from project name."""
        return self.name.replace("-", "_").replace(" ", "_").lower()

    @property
    def platform_names(self) -> list[str]:
        """Human-readable platform names."""
        return [p.value.capitalize() if p != Platform.MACOS else "macOS" for p in self.platforms]

    @property
    def is_epistemic_type(self) -> bool:
        """Whether this project type always enables the AEE epistemic layer."""
        return (
            self.type
            in (
                ProjectType.EPISTEMIC_PIPELINE,
                ProjectType.KNOWLEDGE_ENGINEERING,
                ProjectType.AEE_RESEARCH,
            )
            or self.enable_epistemic
        )

    @property
    def needs_services(self) -> bool:
        """Whether this project type typically needs services.md."""
        return (
            self.type
            in (
                ProjectType.BACKEND_FRONTEND,
                ProjectType.BACKEND_FRONTEND_TRAY,
            )
            or self.services
        )

    @property
    def needs_shell_wrappers(self) -> bool:
        """Whether this project type requires shell wrappers."""
        return (
            self.type
            in (
                ProjectType.EMBEDDED_HARDWARE,
                ProjectType.FPGA_RTL,
                ProjectType.YOCTO_BSP,
                ProjectType.PCB_HARDWARE,
            )
            or self.shell_wrappers
        )

    @property
    def type_label(self) -> str:
        """Human-readable project type label."""
        # self.type is now a str; fall back to the type key itself if unknown
        return _TYPE_LABELS.get(self.type, self.type)

    @property
    def section_ref(self) -> str:
        """Spec section reference for this project type."""
        return _SECTION_REFS.get(self.type, "17")

    @property
    def project_type_enum(self) -> ProjectType | None:
        """Return the ProjectType enum member, or None if type is unknown/custom."""
        try:
            return ProjectType(self.type)
        except ValueError:
            return None


# Keys are str (ProjectType enum values) for compatibility now that config.type is str
_TYPE_LABELS: dict[str, str] = {
    ProjectType.BACKEND_FRONTEND: "Python backend + web frontend",
    ProjectType.BACKEND_FRONTEND_TRAY: "Python backend + web frontend + tray",
    ProjectType.CLI_PYTHON: "CLI tool (Python)",
    ProjectType.LIBRARY_PYTHON: "Library / SDK (Python)",
    ProjectType.EMBEDDED_HARDWARE: "Embedded / hardware (C/C++)",
    ProjectType.FPGA_RTL: "FPGA / RTL (generic / OSS flow)",
    ProjectType.FPGA_RTL_XILINX: "FPGA / RTL — AMD Xilinx (Vivado)",
    ProjectType.FPGA_RTL_INTEL: "FPGA / RTL — Intel/Altera (Quartus)",
    ProjectType.FPGA_RTL_LATTICE: "FPGA / RTL — Lattice (Diamond / Radiant)",
    ProjectType.MIXED_FPGA_EMBEDDED: "Mixed: FPGA + Embedded C/C++ drivers",
    ProjectType.MIXED_FPGA_FIRMWARE: "Mixed: FPGA + Python/C verification",
    ProjectType.YOCTO_BSP: "Yocto / embedded Linux BSP",
    ProjectType.PCB_HARDWARE: "PCB / hardware design (KiCad etc.)",
    ProjectType.WEB_FRONTEND: "Web frontend (SPA)",
    ProjectType.FULLSTACK_JS: "Fullstack JS/TS",
    ProjectType.CLI_RUST: "CLI tool (Rust)",
    ProjectType.CLI_GO: "CLI tool (Go)",
    ProjectType.CLI_C: "CLI tool (C/C++)",
    ProjectType.LIBRARY_RUST: "Library / crate (Rust)",
    ProjectType.LIBRARY_C: "Library (C/C++)",
    ProjectType.DOTNET_APP: ".NET / C# application",
    ProjectType.MOBILE_APP: "Mobile app",
    ProjectType.DEVOPS_IAC: "DevOps / IaC",
    ProjectType.DATA_ML: "Data / ML pipeline",
    ProjectType.MICROSERVICES: "Microservices",
    # Document / Knowledge
    ProjectType.SPEC_DOCUMENT: "Technical specification",
    ProjectType.USER_MANUAL: "User manual / documentation",
    ProjectType.RESEARCH_PAPER: "Research paper / white paper",
    # Business / Legal
    ProjectType.BUSINESS_PLAN: "Business plan / proposal",
    ProjectType.PATENT_APPLICATION: "Patent application",
    ProjectType.LEGAL_COMPLIANCE: "Legal / compliance",
    # Project management
    ProjectType.REQUIREMENTS_MGMT: "Requirements management",
    ProjectType.API_SPECIFICATION: "API specification",
    # More software
    ProjectType.MONOREPO: "Monorepo (multi-package)",
    ProjectType.BROWSER_EXTENSION: "Browser extension",
    # Applied Epistemic Engineering
    ProjectType.EPISTEMIC_PIPELINE: "Epistemic pipeline (AEE + ARE 8-phase)",
    ProjectType.KNOWLEDGE_ENGINEERING: "Knowledge engineering / expert system",
    ProjectType.AEE_RESEARCH: "AEE research project",
}

_SECTION_REFS: dict[str, str] = {
    ProjectType.BACKEND_FRONTEND: "17.1",
    ProjectType.BACKEND_FRONTEND_TRAY: "17.2",
    ProjectType.CLI_PYTHON: "17.3",
    ProjectType.LIBRARY_PYTHON: "17.4",
    ProjectType.EMBEDDED_HARDWARE: "17.5",
    ProjectType.FPGA_RTL: "17.6",
    ProjectType.YOCTO_BSP: "17.7",
    ProjectType.PCB_HARDWARE: "17.8",
    ProjectType.WEB_FRONTEND: "17.9",
    ProjectType.FULLSTACK_JS: "17.10",
    ProjectType.CLI_RUST: "17.11",
    ProjectType.CLI_GO: "17.12",
    ProjectType.CLI_C: "17.13",
    ProjectType.LIBRARY_RUST: "17.14",
    ProjectType.LIBRARY_C: "17.15",
    ProjectType.DOTNET_APP: "17.16",
    ProjectType.MOBILE_APP: "17.17",
    ProjectType.DEVOPS_IAC: "17.18",
    ProjectType.DATA_ML: "17.19",
    ProjectType.MICROSERVICES: "17.20",
    ProjectType.SPEC_DOCUMENT: "17.21",
    ProjectType.USER_MANUAL: "17.22",
    ProjectType.RESEARCH_PAPER: "17.23",
    ProjectType.BUSINESS_PLAN: "17.24",
    ProjectType.PATENT_APPLICATION: "17.25",
    ProjectType.LEGAL_COMPLIANCE: "17.26",
    ProjectType.REQUIREMENTS_MGMT: "17.27",
    ProjectType.API_SPECIFICATION: "17.28",
    ProjectType.MONOREPO: "17.29",
    ProjectType.BROWSER_EXTENSION: "17.30",
    ProjectType.EPISTEMIC_PIPELINE: "17.31",
    ProjectType.KNOWLEDGE_ENGINEERING: "17.32",
    ProjectType.AEE_RESEARCH: "17.33",
}
