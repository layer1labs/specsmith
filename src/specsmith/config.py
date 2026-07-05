# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Project configuration schema for specsmith."""

from __future__ import annotations

from enum import Enum
from typing import Any

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
    FPGA_RTL = "fpga-rtl"  # Generic / open-source flow (Yosys)
    FPGA_RTL_AMD = "fpga-rtl-amd"  # AMD Adaptive Computing (formerly Xilinx) — Vivado
    FPGA_RTL_INTEL = "fpga-rtl-intel"  # Intel/Altera Quartus Prime
    FPGA_RTL_LATTICE = "fpga-rtl-lattice"  # Lattice Diamond / Radiant
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
    # New project types
    EMBEDDED_PYTHON_HMI = "embedded-python-hmi"  # #109: hardware-interfacing kiosk/HMI
    RESEARCH_PYTHON = "research-python"  # #153: experiment/research packages (no CLI)
    SAFETY_CRITICAL = "safety-critical"  # #129: IEC 60204-1/62061/61508 safety-critical
    # IP / Patent
    PATENT_PROSECUTION = "patent-prosecution"  # #177: IP prosecution with USPTO MCP lifecycle
    # Modern web frameworks
    NEXTJS_APP = "nextjs-app"  # Next.js / React full-stack app
    NUXT_APP = "nuxt-app"  # Nuxt.js / Vue full-stack app
    SVELTEKIT_APP = "sveltekit-app"  # SvelteKit app
    REMIX_APP = "remix-app"  # Remix full-stack React app
    ASTRO_SITE = "astro-site"  # Astro static/SSR site
    # AI / LLM / Agents
    LLM_APP = "llm-app"  # LLM-powered app (LangChain / LlamaIndex / custom SDK)
    AGENT_ORCHESTRATION = "agent-orchestration"  # Multi-agent system (AutoGen/CrewAI/LangGraph)
    MCP_SERVER = "mcp-server"  # Model Context Protocol server
    RAG_PIPELINE = "rag-pipeline"  # RAG + embedding pipeline
    MLOPS_PLATFORM = "mlops-platform"  # MLOps platform (MLflow / BentoML / Ray Serve)
    # JVM
    JAVA_SPRING = "java-spring"  # Spring Boot application
    JAVA_LIBRARY = "java-library"  # Java library / SDK
    # Cloud / Infrastructure
    SERVERLESS = "serverless"  # FaaS (Lambda / GCP Functions / Cloudflare Workers)
    KUBERNETES_OPERATOR = "kubernetes-operator"  # K8s controller / operator
    STREAMING_PIPELINE = "streaming-pipeline"  # Kafka / Flink / Beam / Spark Streaming
    DATA_WAREHOUSE = "data-warehouse"  # dbt / Snowflake / BigQuery / Redshift
    # Game development
    GAME_UNITY = "game-unity"  # Unity game project
    GAME_GODOT = "game-godot"  # Godot game project
    # Web3 / blockchain
    SMART_CONTRACT = "smart-contract"  # Solidity / EVM smart contracts
    # Desktop
    DESKTOP_ELECTRON = "desktop-electron"  # Electron desktop app
    DESKTOP_TAURI = "desktop-tauri"  # Tauri desktop app (Rust + WebView)
    # Brief lang — declarative contract-enforced logic language (github.com/Randozart/brief-lang)
    # Version anchor: v0.14.0 @ commit 6a43c4aebcc5c6c774dbc2908445fb19486e8043 (2026-06-14)
    # No release tags exist yet; version string + commit hash are both recorded.
    BRIEF_LANG = "brief-lang"  # .bv/.sbv/.rbv/.ebv project using brief-compiler


class Platform(str, Enum):
    """Target platforms (kept for backward compatibility; ProjectConfig now uses list[str])."""

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
    # str instead of Platform enum so FPGA/embedded/cloud targets (e.g. 'embedded',
    # 'amd-fpga', 'wasm') don't crash pydantic validation. The Platform enum is kept
    # for backward-compatible imports; use its .value strings as defaults.
    platforms: list[str] = Field(
        default=["windows", "linux", "macos"],
        description=(
            "Target build platforms. Standard: windows, linux, macos. "
            "Domain-specific: embedded, cloud, wasm, amd-fpga, intel-fpga, lattice-fpga, etc."
        ),
    )
    language: str = Field(default="python", description="Primary language/runtime")
    spec_version: str = Field(default="0.20.1", description="Spec version to scaffold from")
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
        default="",
        description="Test framework detected by import",
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

    # Explicit type override — suppresses the type-mismatch audit check.
    # Set this when your project uses a custom or research-specific type string
    # that cannot be auto-detected (e.g. 'research-mathematics').  When
    # type_override matches type, check_type_mismatch is suppressed.
    type_override: str = Field(
        default="",
        description=(
            "Explicit type override.  When set to the same value as `type`, "
            "the type-mismatch audit check is suppressed regardless of what "
            "auto-detection infers from the project files."
        ),
    )
    # Fallback type — used when this project type is not yet supported
    # by the installed specsmith version. specsmith silently falls back to
    # this type for scaffolding purposes while still recording the intended type.
    fallback_type: str = Field(
        default="",
        description=(
            "Fallback project type for scaffold generation when `type` is not yet "
            "supported by the installed specsmith version (e.g. 'spec-document' as "
            "fallback for 'patent-prosecution')."
        ),
    )

    # IP prosecution fields (used when type == 'patent-prosecution')
    provisional_app_number: str = Field(
        default="",
        description="USPTO provisional application number (e.g. '63/980,251')",
    )
    provisional_filed_date: str = Field(
        default="",
        description="Date the provisional was filed (YYYY-MM-DD)",
    )
    non_provisional_deadline: str = Field(
        default="",
        description="12-month non-provisional conversion deadline (YYYY-MM-DD)",
    )
    entity_status: str = Field(default="", description="USPTO entity status: small, micro, large")
    assignee: str = Field(default="", description="Patent assignee / rights holder")
    counsel: str = Field(default="", description="Patent counsel firm name")
    inventors: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of inventors with name and role keys",
    )
    ip_families: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "IP patent families. Each entry: {id, name, phase, provisional, themes, "
            "anchor_spec, ...}."
        ),
    )
    claim_themes: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Claim themes for the primary IP family. Each entry: {id, name, description, "
            "risk, primary_comparator, last_par_run}."
        ),
    )
    specs_dir: str = Field(
        default="docs/ip/specs",
        description="Normative specification directory for IP repos",
    )
    prosecution_dir: str = Field(
        default="docs/ip/prosecution",
        description="Prior-art protocol and prosecution planning directory",
    )
    strategy_dir: str = Field(
        default="docs/ip/strategy",
        description="IP strategy documents directory",
    )
    filings_dir: str = Field(
        default="docs/ip/filings",
        description="Immutable filed artifacts directory",
    )

    # FPGA-specific
    fpga_vendor: str = Field(
        default="",
        description="FPGA vendor/toolchain: amd, intel, lattice, gowin (blank = generic/OSS)",
    )

    # Agent integrations
    integrations: list[str] = Field(
        default=["agents-md"],
        description=(
            "Agent integrations to generate (agents-md, agent-skill, claude-code, "
            "cursor, copilot, gemini, windsurf, aider)."
        ),
    )

    # Agent execution profile
    execution_profile: str = Field(
        default="standard",
        description=(
            "Agent execution profile: safe (read-only), standard (default), "
            "open (most commands), admin (no limits)."
        ),
    )
    custom_allowed_commands: list[str] = Field(
        default_factory=list,
        description="Extra allowed command prefixes merged with the active execution profile.",
    )
    custom_blocked_commands: list[str] = Field(
        default_factory=list,
        description="Extra blocked command prefixes merged with the active execution profile.",
    )
    custom_blocked_tools: list[str] = Field(
        default_factory=list,
        description="Agent tool names to always block, regardless of the execution profile.",
    )

    # Audit thresholds (scaffold.yml-configurable) — #124, #145
    agents_md_line_threshold: int = Field(
        default=0,
        description=(
            "Override AGENTS.md line-count audit threshold. 0 = use type-aware default "
            "(200 for standard, 350 for embedded/fpga)."
        ),
    )
    ledger_line_threshold: int = Field(
        default=0,
        description=(
            "Override LEDGER.md line-count audit threshold. 0 = use type-aware default "
            "(500 for standard, 5000 for fpga-rtl)."
        ),
    )

    # Configurable doc filenames — #148
    test_spec_file: str = Field(
        default="docs/TESTS.md",
        description=(
            "Canonical test specification file path. Default: docs/TESTS.md. "
            "Override with e.g. docs/TEST_SPEC.md."
        ),
    )
    requirements_file: str = Field(
        default="docs/REQUIREMENTS.md",
        description="Canonical requirements file path.",
    )

    # Scanner exclusions — #146
    scan_exclude_dirs: list[str] = Field(
        default_factory=list,
        description=(
            "Directories to exclude from specsmith scanning (detection, stats, test discovery). "
            "Auto-populated from .gitignore on import. "
            "e.g. ['external/', 'node_modules/', '.venv/']"
        ),
    )

    # Derived artifacts — #126
    derived_artifacts: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Code-generated files that should not be hand-edited. Each entry: "
            "{source, generator, outputs: [str], do_not_edit: bool}"
        ),
    )

    # Hardware-gated tests — #159
    hardware_gated_test_attr: str = Field(
        default="hardware_gated",
        description=(
            "Attribute name used in TESTS.md to mark tests as hardware-gated "
            "(e.g. 'Hardware-gated: true'). Hardware-gated Pending tests are "
            "not flagged as coverage drift."
        ),
    )

    # Cross-repo dependencies — #161
    cross_repo_dependencies: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Cross-repo requirement traceability. Each entry: "
            "{repo, url, role, req_prefixes: [str]}"
        ),
    )

    # Secrets templates — #162
    secrets_templates: list[dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Required-but-uncommitted secrets files. Each entry: "
            "{path, description, required_keys: [str], never_commit: bool}"
        ),
    )

    # Industrial artifacts (CANopen EDS/XDD) — #163
    industrial_artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Industrial protocol artifacts (e.g. CANopen EDS/XDD). "
            "Structure: {canopen_eds: [{path, device, fw_repo?}]}"
        ),
    )

    # Rate-limit per-bucket concurrency — #120
    rate_limit_concurrency_by_bucket: dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Per-bucket concurrency caps that override the model-level concurrency_cap. "
            "Buckets: reasoning, conversational, longform, background."
        ),
    )

    # Research / publication phases — #156
    publication_phases: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Custom publication gates for research projects. "
            "Keys are gate IDs; values describe required_artifacts and checks."
        ),
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
        description="Enable cryptographic trace vault (ESDB seal_record; REQ-420)",
    )

    @property
    def package_name(self) -> str:
        """Python-safe package name derived from project name."""
        return self.name.replace("-", "_").replace(" ", "_").lower()

    @property
    def platform_names(self) -> list[str]:
        """Human-readable platform names."""

        def _label(p: str) -> str:
            if p.lower() == "macos":
                return "macOS"
            return p.replace("-", " ").title()

        return [_label(str(p)) for p in self.platforms]

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


# ---------------------------------------------------------------------------
# Legacy key normalisation helper
# ---------------------------------------------------------------------------


def _normalize_scaffold_raw(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalise legacy scaffold YAML keys to the current schema.

    Call this before ``ProjectConfig(**raw)`` whenever raw YAML is loaded from
    disk so that projects created by older specsmith versions continue to parse
    correctly after a key rename.

    Migrations handled:
    - ``project`` → ``name``  (renamed in specsmith ≤ 0.9)
    """
    if raw and "project" in raw and "name" not in raw:
        raw = dict(raw)
        raw["name"] = raw.pop("project")
    return raw


# Keys are str (ProjectType enum values) for compatibility now that config.type is str
_TYPE_LABELS: dict[str, str] = {
    ProjectType.BACKEND_FRONTEND: "Python backend + web frontend",
    ProjectType.BACKEND_FRONTEND_TRAY: "Python backend + web frontend + tray",
    ProjectType.CLI_PYTHON: "CLI tool (Python)",
    ProjectType.LIBRARY_PYTHON: "Library / SDK (Python)",
    ProjectType.EMBEDDED_HARDWARE: "Embedded / hardware (C/C++)",
    ProjectType.FPGA_RTL: "FPGA / RTL (generic / OSS flow)",
    ProjectType.FPGA_RTL_AMD: "FPGA / RTL — AMD Adaptive Computing (Vivado)",
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
    # New types
    ProjectType.EMBEDDED_PYTHON_HMI: "Embedded Python HMI / kiosk (hardware-interfacing)",
    ProjectType.RESEARCH_PYTHON: "Research Python (experiments, no CLI distribution)",
    ProjectType.SAFETY_CRITICAL: "Safety-critical embedded (IEC 60204-1/62061/61508)",
    # IP / Patent
    ProjectType.PATENT_PROSECUTION: "Patent prosecution repository (USPTO IP lifecycle)",
    # Modern web frameworks
    ProjectType.NEXTJS_APP: "Next.js application (React + SSR/SSG)",
    ProjectType.NUXT_APP: "Nuxt.js application (Vue + SSR/SSG)",
    ProjectType.SVELTEKIT_APP: "SvelteKit application",
    ProjectType.REMIX_APP: "Remix application (React + full-stack)",
    ProjectType.ASTRO_SITE: "Astro site (static / SSR)",
    # AI / LLM / Agents
    ProjectType.LLM_APP: "LLM-powered application (LangChain / LlamaIndex / custom)",
    ProjectType.AGENT_ORCHESTRATION: "Multi-agent orchestration (AutoGen / CrewAI / LangGraph)",
    ProjectType.MCP_SERVER: "MCP server (Model Context Protocol)",
    ProjectType.RAG_PIPELINE: "RAG / embedding pipeline",
    ProjectType.MLOPS_PLATFORM: "MLOps platform (MLflow / BentoML / Ray Serve)",
    # JVM
    ProjectType.JAVA_SPRING: "Java Spring Boot application",
    ProjectType.JAVA_LIBRARY: "Java library / SDK",
    # Cloud / Infrastructure
    ProjectType.SERVERLESS: "Serverless / FaaS (Lambda / GCP Functions / Cloudflare Workers)",
    ProjectType.KUBERNETES_OPERATOR: "Kubernetes operator / controller",
    ProjectType.STREAMING_PIPELINE: "Streaming data pipeline (Kafka / Flink / Beam)",
    ProjectType.DATA_WAREHOUSE: "Data warehouse (dbt / Snowflake / BigQuery)",
    # Game development
    ProjectType.GAME_UNITY: "Game (Unity)",
    ProjectType.GAME_GODOT: "Game (Godot)",
    # Web3
    ProjectType.SMART_CONTRACT: "Smart contract (Solidity / EVM)",
    # Desktop
    ProjectType.DESKTOP_ELECTRON: "Desktop application (Electron)",
    ProjectType.DESKTOP_TAURI: "Desktop application (Tauri — Rust + WebView)",
    # Brief lang
    ProjectType.BRIEF_LANG: "Brief lang — declarative contract-enforced logic language (v0.14.0)",
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
    # AI / LLM / Agents
    ProjectType.LLM_APP: "17.34",
    ProjectType.AGENT_ORCHESTRATION: "17.35",
    ProjectType.MCP_SERVER: "17.36",
    ProjectType.RAG_PIPELINE: "17.37",
    ProjectType.MLOPS_PLATFORM: "17.38",
    # JVM
    ProjectType.JAVA_SPRING: "17.39",
    ProjectType.JAVA_LIBRARY: "17.40",
    # Cloud / Infrastructure
    ProjectType.SERVERLESS: "17.41",
    ProjectType.KUBERNETES_OPERATOR: "17.42",
    ProjectType.STREAMING_PIPELINE: "17.43",
    ProjectType.DATA_WAREHOUSE: "17.44",
    # Game development
    ProjectType.GAME_UNITY: "17.45",
    ProjectType.GAME_GODOT: "17.46",
    # Web3
    ProjectType.SMART_CONTRACT: "17.47",
    # Desktop
    ProjectType.DESKTOP_ELECTRON: "17.48",
    ProjectType.DESKTOP_TAURI: "17.49",
    # Brief lang
    ProjectType.BRIEF_LANG: "17.50",
}
