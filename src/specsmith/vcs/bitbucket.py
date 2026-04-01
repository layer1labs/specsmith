"""Bitbucket platform integration."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig, ProjectType
from specsmith.vcs.base import CommandResult, PlatformStatus, VCSPlatform

_PYTHON_TYPES = (
    ProjectType.CLI_PYTHON,
    ProjectType.LIBRARY_PYTHON,
    ProjectType.BACKEND_FRONTEND,
    ProjectType.BACKEND_FRONTEND_TRAY,
)


class BitbucketPlatform(VCSPlatform):
    """Bitbucket integration."""

    @property
    def name(self) -> str:
        return "bitbucket"

    @property
    def cli_name(self) -> str:
        return "bb"

    def generate_ci_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        ci_path = target / "bitbucket-pipelines.yml"
        ci_path.write_text(self._render_pipelines(config), encoding="utf-8")
        return [ci_path]

    def generate_dependency_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        # Bitbucket uses renovate for dependency management
        renovate_path = target / "renovate.json"
        if not renovate_path.exists():
            renovate_path.write_text(
                '{\n  "$schema": "https://docs.renovatebot.com/renovate-schema.json",\n'
                '  "extends": ["config:recommended"]\n}\n',
                encoding="utf-8",
            )
            return [renovate_path]
        return []

    def generate_security_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        return []

    def check_status(self) -> PlatformStatus:
        status = PlatformStatus()
        pipelines = self.run_command(["pipelines", "list", "--limit", "1"])
        if pipelines.success:
            status.details.append(f"Pipelines: {pipelines.output[:200]}")

        prs = self.run_command(["pr", "list", "--state", "OPEN"])
        if prs.success:
            lines = [ln for ln in prs.output.splitlines() if ln.strip()]
            status.open_prs = len(lines)
            status.details.append(f"Open PRs: {status.open_prs}")

        return status

    def list_ci_runs(self, *, limit: int = 5) -> CommandResult:
        return self.run_command(["pipelines", "list", "--limit", str(limit)])

    def list_alerts(self) -> CommandResult:
        return CommandResult(
            command="bb alerts",
            success=True,
            output="Bitbucket does not have a native dependency alert CLI. Use Renovate.",
        )

    def _render_pipelines(self, config: ProjectConfig) -> str:
        is_python = config.type in _PYTHON_TYPES

        if is_python:
            return (
                "image: python:3.12-slim\n\n"
                "pipelines:\n"
                "  default:\n"
                "    - step:\n"
                "        name: Lint\n"
                "        caches:\n"
                "          - pip\n"
                "        script:\n"
                "          - pip install ruff\n"
                "          - ruff check src/ tests/\n"
                "          - ruff format --check src/ tests/\n"
                "    - step:\n"
                "        name: Test\n"
                "        caches:\n"
                "          - pip\n"
                "        script:\n"
                '          - pip install -e ".[dev]"\n'
                f"          - pytest --cov={config.package_name}"
                " --cov-report=term-missing\n"
                "    - step:\n"
                "        name: Security\n"
                "        caches:\n"
                "          - pip\n"
                "        script:\n"
                "          - pip install pip-audit\n"
                "          - pip install -e .\n"
                "          - pip-audit\n"
            )
        return (
            "pipelines:\n"
            "  default:\n"
            "    - step:\n"
            "        name: Build\n"
            "        script:\n"
            f"          - echo 'Add {config.type_label} build steps here'\n"
        )
