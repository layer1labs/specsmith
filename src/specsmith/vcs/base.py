# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Base VCS platform interface."""

from __future__ import annotations

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from specsmith.config import ProjectConfig


@dataclass
class CommandResult:
    """Result of a VCS CLI command."""

    command: str
    success: bool
    output: str
    error: str = ""


@dataclass
class PlatformStatus:
    """Status summary from a VCS platform."""

    ci_passing: bool | None = None
    open_alerts: int = 0
    open_prs: int = 0
    details: list[str] = field(default_factory=list)


class VCSPlatform(ABC):
    """Base class for VCS platform integrations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Platform identifier (e.g. 'github', 'gitlab')."""

    @property
    @abstractmethod
    def cli_name(self) -> str:
        """CLI tool name (e.g. 'gh', 'glab', 'bb')."""

    @abstractmethod
    def generate_ci_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        """Generate CI/CD configuration files."""

    @abstractmethod
    def generate_dependency_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        """Generate dependency management config (dependabot, renovate, etc.)."""

    @abstractmethod
    def generate_security_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        """Generate security scanning config."""

    def generate_dev_release_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        """Generate dev-release workflow for gitflow projects. Override in subclasses."""
        return []

    def generate_all(self, config: ProjectConfig, target: Path) -> list[Path]:
        """Generate all platform-specific files."""
        created: list[Path] = []
        created.extend(self.generate_ci_config(config, target))
        created.extend(self.generate_dependency_config(config, target))
        created.extend(self.generate_security_config(config, target))
        if config.branching_strategy == "gitflow":
            created.extend(self.generate_dev_release_config(config, target))
        return created

    def is_cli_available(self) -> bool:
        """Check if the platform CLI is installed."""
        try:
            result = subprocess.run(
                [self.cli_name, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run_command(self, args: list[str], *, timeout: int = 30) -> CommandResult:
        """Run a CLI command with timeout."""
        cmd = [self.cli_name, *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return CommandResult(
                command=" ".join(cmd),
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip(),
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                command=" ".join(cmd),
                success=False,
                output="",
                error=f"Command timed out after {timeout}s",
            )
        except FileNotFoundError:
            return CommandResult(
                command=" ".join(cmd),
                success=False,
                output="",
                error=f"{self.cli_name} not found. Install it first.",
            )

    @abstractmethod
    def check_status(self) -> PlatformStatus:
        """Check CI, alerts, and PR status."""

    @abstractmethod
    def list_ci_runs(self, *, limit: int = 5) -> CommandResult:
        """List recent CI/CD runs."""

    @abstractmethod
    def list_alerts(self) -> CommandResult:
        """List dependency/security alerts."""
