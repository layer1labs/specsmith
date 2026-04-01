"""GitLab platform integration via glab CLI."""

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


class GitLabPlatform(VCSPlatform):
    """GitLab integration via glab CLI."""

    @property
    def name(self) -> str:
        return "gitlab"

    @property
    def cli_name(self) -> str:
        return "glab"

    def generate_ci_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        ci_path = target / ".gitlab-ci.yml"
        ci_path.write_text(self._render_ci(config), encoding="utf-8")
        return [ci_path]

    def generate_dependency_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        # GitLab uses renovate or built-in dependency scanning
        renovate_path = target / "renovate.json"
        renovate_path.write_text(
            '{\n  "$schema": "https://docs.renovatebot.com/renovate-schema.json",\n'
            '  "extends": ["config:recommended"]\n}\n',
            encoding="utf-8",
        )
        return [renovate_path]

    def generate_security_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        # Security scanning is included in the CI config via templates
        return []

    def check_status(self) -> PlatformStatus:
        status = PlatformStatus()

        pipelines = self.run_command(["ci", "list", "--per-page", "1"])
        if pipelines.success:
            status.details.append(f"Pipelines: {pipelines.output[:200]}")

        mrs = self.run_command(["mr", "list", "--state", "opened"])
        if mrs.success:
            lines = [ln for ln in mrs.output.splitlines() if ln.strip()]
            status.open_prs = len(lines)
            status.details.append(f"Open MRs: {status.open_prs}")

        return status

    def list_ci_runs(self, *, limit: int = 5) -> CommandResult:
        return self.run_command(["ci", "list", "--per-page", str(limit)])

    def list_alerts(self) -> CommandResult:
        return self.run_command(["api", "projects/:id/vulnerability_findings", "--per-page", "20"])

    def _render_ci(self, config: ProjectConfig) -> str:
        is_python = config.type in _PYTHON_TYPES

        ci = "stages:\n  - lint\n  - test\n  - security\n\n"

        if is_python:
            ci += (
                "lint:\n"
                "  stage: lint\n"
                "  image: python:3.12-slim\n"
                "  script:\n"
                "    - pip install ruff\n"
                "    - ruff check src/ tests/\n"
                "    - ruff format --check src/ tests/\n\n"
                "test:\n"
                "  stage: test\n"
                "  image: python:3.12-slim\n"
                "  script:\n"
                '    - pip install -e ".[dev]"\n'
                f"    - pytest --cov={config.package_name}"
                " --cov-report=term-missing\n"
                "  parallel:\n"
                "    matrix:\n"
                '      - PYTHON_VERSION: ["3.10", "3.12", "3.13"]\n\n'
                "security:\n"
                "  stage: security\n"
                "  image: python:3.12-slim\n"
                "  script:\n"
                "    - pip install pip-audit\n"
                "    - pip install -e .\n"
                "    - pip-audit\n"
                "  allow_failure: true\n"
            )
        else:
            ci += (
                "build:\n"
                "  stage: test\n"
                "  script:\n"
                f"    - echo 'Add {config.type_label} build steps here'\n"
            )

        return ci
