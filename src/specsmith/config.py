"""Project configuration schema for specsmith."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    """Supported project types from the spec (Section 17)."""

    BACKEND_FRONTEND = "backend-frontend"
    BACKEND_FRONTEND_TRAY = "backend-frontend-tray"
    CLI_PYTHON = "cli-python"
    LIBRARY_PYTHON = "library-python"
    EMBEDDED_HARDWARE = "embedded-hardware"
    FPGA_RTL = "fpga-rtl"
    YOCTO_BSP = "yocto-bsp"
    PCB_HARDWARE = "pcb-hardware"


class Platform(str, Enum):
    """Target platforms."""

    WINDOWS = "windows"
    LINUX = "linux"
    MACOS = "macos"


class ProjectConfig(BaseModel):
    """Configuration for a specsmith-generated project scaffold.

    This model validates the scaffold.yml input file and interactive prompts.
    """

    name: str = Field(description="Project name (used for directory and package name)")
    type: ProjectType = Field(description="Project type from Section 17")
    platforms: list[Platform] = Field(
        default=[Platform.WINDOWS, Platform.LINUX, Platform.MACOS],
        description="Target platforms",
    )
    language: str = Field(default="python", description="Primary language/runtime")
    spec_version: str = Field(default="0.1.0-alpha.1", description="Spec version to scaffold from")
    description: str = Field(default="", description="Short project description")

    # Options
    services: bool = Field(
        default=False,
        description="Include services.md for daemon/service projects",
    )
    shell_wrappers: bool = Field(default=False, description="Include shell.ps1/shell.sh wrappers")
    exec_shims: bool = Field(default=True, description="Include exec.ps1/exec.sh timeout shims")
    git_init: bool = Field(default=True, description="Initialize git repository")

    # VCS platform
    vcs_platform: str = Field(
        default="github",
        description="VCS platform (github, gitlab, bitbucket)",
    )

    # Agent integrations
    integrations: list[str] = Field(
        default=["agents-md"],
        description="Agent integrations to generate (agents-md, warp, claude-code, cursor, etc.)",
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
        labels = {
            ProjectType.BACKEND_FRONTEND: "Python backend + web frontend",
            ProjectType.BACKEND_FRONTEND_TRAY: "Python backend + web frontend + tray",
            ProjectType.CLI_PYTHON: "CLI tool (Python)",
            ProjectType.LIBRARY_PYTHON: "Library / SDK (Python)",
            ProjectType.EMBEDDED_HARDWARE: "Embedded / hardware",
            ProjectType.FPGA_RTL: "FPGA / RTL",
            ProjectType.YOCTO_BSP: "Yocto / embedded Linux BSP",
            ProjectType.PCB_HARDWARE: "PCB / hardware design",
        }
        return labels[self.type]

    @property
    def section_ref(self) -> str:
        """Spec section reference for this project type."""
        refs = {
            ProjectType.BACKEND_FRONTEND: "17.1",
            ProjectType.BACKEND_FRONTEND_TRAY: "17.2",
            ProjectType.CLI_PYTHON: "17.3",
            ProjectType.LIBRARY_PYTHON: "17.4",
            ProjectType.EMBEDDED_HARDWARE: "17.5",
            ProjectType.FPGA_RTL: "17.6",
            ProjectType.YOCTO_BSP: "17.7",
            ProjectType.PCB_HARDWARE: "17.8",
        }
        return refs[self.type]
