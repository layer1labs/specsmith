"""GitHub platform integration via gh CLI."""

from __future__ import annotations

import json
from pathlib import Path

from specsmith.config import ProjectConfig, ProjectType
from specsmith.vcs.base import CommandResult, PlatformStatus, VCSPlatform

_PYTHON_TYPES = (
    ProjectType.CLI_PYTHON,
    ProjectType.LIBRARY_PYTHON,
    ProjectType.BACKEND_FRONTEND,
    ProjectType.BACKEND_FRONTEND_TRAY,
)


class GitHubPlatform(VCSPlatform):
    """GitHub integration via gh CLI."""

    @property
    def name(self) -> str:
        return "github"

    @property
    def cli_name(self) -> str:
        return "gh"

    def generate_ci_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        wf_dir = target / ".github" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)

        ci_path = wf_dir / "ci.yml"
        ci_path.write_text(self._render_ci(config), encoding="utf-8")
        return [ci_path]

    def generate_dependency_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        gh_dir = target / ".github"
        gh_dir.mkdir(parents=True, exist_ok=True)

        dep_path = gh_dir / "dependabot.yml"
        dep_path.write_text(self._render_dependabot(config), encoding="utf-8")
        return [dep_path]

    def generate_security_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        return []

    def check_status(self) -> PlatformStatus:
        status = PlatformStatus()

        ci = self.run_command(["run", "list", "--limit", "1", "--json", "status,conclusion"])
        if ci.success and ci.output:
            try:
                runs = json.loads(ci.output)
                if runs:
                    status.ci_passing = runs[0].get("conclusion") == "success"
                    status.details.append(f"Latest CI: {runs[0].get('conclusion', 'unknown')}")
            except json.JSONDecodeError:
                status.details.append("Could not parse CI status")

        alerts = self.run_command(
            ["api", "repos/{owner}/{repo}/dependabot/alerts", "--jq", "length"]
        )
        if alerts.success and alerts.output.strip().isdigit():
            status.open_alerts = int(alerts.output.strip())
            status.details.append(f"Dependabot alerts: {status.open_alerts}")

        prs = self.run_command(["pr", "list", "--json", "number", "--jq", "length"])
        if prs.success and prs.output.strip().isdigit():
            status.open_prs = int(prs.output.strip())
            status.details.append(f"Open PRs: {status.open_prs}")

        return status

    def list_ci_runs(self, *, limit: int = 5) -> CommandResult:
        return self.run_command(["run", "list", "--limit", str(limit)])

    def list_alerts(self) -> CommandResult:
        return self.run_command(
            [
                "api",
                "repos/{owner}/{repo}/dependabot/alerts",
                "--jq",
                '.[] | "\\(.security_advisory.summary) [\\(.state)]"',
            ]
        )

    def list_secret_scanning(self) -> CommandResult:
        """List secret scanning alerts."""
        return self.run_command(["secret-scanning", "list"])

    def list_code_scanning(self) -> CommandResult:
        """List code scanning alerts."""
        return self.run_command(["code-scanning", "alert", "list"])

    def _render_ci(self, config: ProjectConfig) -> str:
        is_python = config.type in _PYTHON_TYPES
        ci = (
            "name: CI\n\non:\n  push:\n    branches: [main]\n"
            "  pull_request:\n    branches: [main]\n\n"
            "concurrency:\n  group: ci-${{ github.ref }}\n"
            "  cancel-in-progress: true\n\npermissions:\n  contents: read\n\njobs:\n"
        )
        if is_python:
            ci += (
                "  lint:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v6\n"
                "      - uses: actions/setup-python@v6\n"
                '        with:\n          python-version: "3.12"\n          cache: pip\n'
                "      - run: pip install ruff\n"
                "      - run: ruff check src/ tests/\n"
                "      - run: ruff format --check src/ tests/\n\n"
                "  typecheck:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v6\n"
                "      - uses: actions/setup-python@v6\n"
                '        with:\n          python-version: "3.12"\n          cache: pip\n'
                '      - run: pip install -e ".[dev]"\n'
                f"      - run: mypy src/{config.package_name}/\n\n"
                "  test:\n    needs: [lint, typecheck]\n    strategy:\n"
                "      fail-fast: false\n      matrix:\n"
                "        os: [ubuntu-latest, windows-latest, macos-latest]\n"
                '        python-version: ["3.10", "3.12", "3.13"]\n'
                "    runs-on: ${{ matrix.os }}\n    steps:\n"
                "      - uses: actions/checkout@v6\n"
                "      - uses: actions/setup-python@v6\n"
                "        with:\n          python-version: ${{ matrix.python-version }}\n"
                "          cache: pip\n"
                '      - run: pip install -e ".[dev]"\n'
                f"      - run: pytest --cov={config.package_name}"
                " --cov-report=term-missing\n\n"
                "  security:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v6\n"
                "      - uses: actions/setup-python@v6\n"
                '        with:\n          python-version: "3.12"\n          cache: pip\n'
                "      - run: pip install pip-audit\n"
                "      - run: pip install -e .\n"
                "      - run: pip-audit\n"
            )
        else:
            ci += (
                "  build:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v6\n"
                f"      - run: echo 'Add {config.type_label} build steps here'\n"
            )
        return ci

    def _render_dependabot(self, config: ProjectConfig) -> str:
        ecosystems = [
            '  - package-ecosystem: "github-actions"\n'
            '    directory: "/"\n'
            "    schedule:\n"
            '      interval: "weekly"\n'
            "    open-pull-requests-limit: 5\n"
        ]
        if config.type in _PYTHON_TYPES:
            ecosystems.insert(
                0,
                '  - package-ecosystem: "pip"\n'
                '    directory: "/"\n'
                "    schedule:\n"
                '      interval: "weekly"\n'
                "    open-pull-requests-limit: 5\n",
            )
        return "version: 2\nupdates:\n" + "\n".join(ecosystems)
