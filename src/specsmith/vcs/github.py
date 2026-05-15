# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""GitHub platform integration via gh CLI."""

from __future__ import annotations

import json
from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.tools import LANG_CI_META, ToolSet, get_format_check_commands, get_tools
from specsmith.vcs.base import CommandResult, PlatformStatus, VCSPlatform

# Language → Dependabot package ecosystem
_LANG_ECOSYSTEM: dict[str, str] = {
    "python": "pip",
    "javascript": "npm",
    "typescript": "npm",
    "rust": "cargo",
    "go": "gomod",
    "csharp": "nuget",
    "dart": "pub",
}


def _needs_node_setup(tools: ToolSet) -> bool:
    """Check if any tools require Node.js runtime."""
    all_cmds = " ".join(tools.lint + tools.typecheck + tools.test + tools.security + tools.format)
    return any(t in all_cmds for t in ("eslint", "tsc", "vitest", "jest", "npm", "prettier"))


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

    def generate_dev_release_config(self, config: ProjectConfig, target: Path) -> list[Path]:
        """Generate dev-release workflow for gitflow Python projects."""
        if config.language != "python":
            return []
        wf_dir = target / ".github" / "workflows"
        wf_dir.mkdir(parents=True, exist_ok=True)
        path = wf_dir / "dev-release.yml"
        develop = config.develop_branch or "develop"
        path.write_text(
            f"""name: Dev Release

on:
  push:
    branches: [{develop}]
  workflow_dispatch:

permissions:
  contents: read

jobs:
  dev-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip

      - name: Install build tools
        run: pip install build

      - name: Set dev version
        run: |
          BASE=$(grep 'version = ' pyproject.toml | head -1 | sed 's/version = "\\(.*\\)"/\1/')
          MAJOR=$(echo $BASE | cut -d. -f1)
          MINOR=$(echo $BASE | cut -d. -f2)
          PATCH=$(echo $BASE | cut -d. -f3)
          NP=$((PATCH + 1))
          TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo HEAD~100)
          NC=$(git rev-list --count HEAD ^$TAG 2>/dev/null || echo 0)
          DV="${{MAJOR}}.${{MINOR}}.${{NP}}.dev${{NC}}"
          echo "DEV_VERSION=${{DV}}" >> $GITHUB_ENV
          sed -i "s/version = \"${{BASE}}\"/version = \"${{DV}}\"/" pyproject.toml
          echo "Building version: ${{DV}}"

      - run: python -m build

      - name: Upload build artifacts
        uses: actions/upload-artifact@v4
        with:
          name: dev-dist
          path: dist/

  pypi-dev-publish:
    needs: dev-build
    runs-on: ubuntu-latest
    environment: pypi
    permissions:
      id-token: write
    continue-on-error: true
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: dev-dist
          path: dist/
      - name: Publish dev release to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
""",
            encoding="utf-8",
        )
        return [path]

    def _render_ci(self, config: ProjectConfig) -> str:
        tools = get_tools(config)
        meta = LANG_CI_META.get(config.language, {})
        gh_setup = meta.get("gh_setup", "")
        install = meta.get("install", "")
        is_python = config.language == "python"
        needs_node = _needs_node_setup(tools) and config.language not in (
            "javascript",
            "typescript",
            "jsx",
            "tsx",
        )

        ci = (
            "name: CI\n\non:\n  push:\n    branches: [main]\n"
            "  pull_request:\n    branches: [main]\n\n"
            "concurrency:\n  group: ci-${{ github.ref }}\n"
            "  cancel-in-progress: true\n\npermissions:\n  contents: read\n\njobs:\n"
        )

        needs: list[str] = []

        # Lint job
        if tools.lint or tools.format:
            needs.append("lint")
            ci += (
                "  lint:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v4\n"
            )
            if gh_setup:
                ci += gh_setup
            if needs_node:
                ci += LANG_CI_META.get("javascript", {}).get("gh_setup", "")
            if install:
                ci += f"      - run: {install}\n"
            if needs_node and install != "npm ci":
                ci += "      - run: npm ci\n"
            for cmd in tools.lint:
                ci += f"      - run: {cmd}\n"
            for cmd in get_format_check_commands(tools):
                ci += f"      - run: {cmd}\n"
            ci += "\n"

        # Typecheck job
        if tools.typecheck:
            needs.append("typecheck")
            ci += (
                "  typecheck:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v4\n"
            )
            if gh_setup:
                ci += gh_setup
            if install:
                ci += f"      - run: {install}\n"
            for cmd in tools.typecheck:
                if cmd == "mypy" and is_python:
                    ci += f"      - run: mypy src/{config.package_name}/\n"
                else:
                    ci += f"      - run: {cmd}\n"
            ci += "\n"

        # Test job
        if tools.test:
            needs_str = ", ".join(needs) if needs else ""
            ci += "  test:\n"
            if needs:
                ci += f"    needs: [{needs_str}]\n"
            if is_python:
                ci += (
                    "    strategy:\n"
                    "      fail-fast: false\n      matrix:\n"
                    "        os: [ubuntu-latest, windows-latest, macos-latest]\n"
                    '        python-version: ["3.10", "3.12", "3.13"]\n'
                    "    runs-on: ${{ matrix.os }}\n    steps:\n"
                    "      - uses: actions/checkout@v4\n"
                    "      - uses: actions/setup-python@v5\n"
                    "        with:\n          python-version: ${{ matrix.python-version }}\n"
                    "          cache: pip\n"
                )
            else:
                ci += "    runs-on: ubuntu-latest\n    steps:\n"
                ci += "      - uses: actions/checkout@v4\n"
                if gh_setup:
                    ci += gh_setup
            if install:
                ci += f"      - run: {install}\n"
            if needs_node and not is_python:
                ci += "      - run: npm ci\n"
            for cmd in tools.test:
                if cmd == "pytest" and is_python:
                    ci += (
                        f"      - run: pytest --cov={config.package_name}"
                        " --cov-report=term-missing\n"
                    )
                else:
                    ci += f"      - run: {cmd}\n"
            ci += "\n"

        # Security job
        if tools.security:
            ci += (
                "  security:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v4\n"
            )
            if gh_setup:
                ci += gh_setup
            if is_python:
                ci += "      - run: pip install -e .\n"
            elif install:
                ci += f"      - run: {install}\n"
            for cmd in tools.security:
                if cmd == "pip-audit":
                    ci += "      - run: pip install pip-audit\n"
                    ci += "      - run: pip-audit\n"
                elif cmd == "cargo audit":
                    ci += "      - run: cargo install cargo-audit\n"
                    ci += "      - run: cargo audit\n"
                elif "govulncheck" in cmd:
                    ci += "      - run: go install golang.org/x/vuln/cmd/govulncheck@latest\n"
                    ci += f"      - run: {cmd}\n"
                else:
                    ci += f"      - run: {cmd}\n"

        # Fallback if no tools at all
        if not any([tools.lint, tools.typecheck, tools.test, tools.security, tools.format]):
            ci += (
                "  build:\n    runs-on: ubuntu-latest\n    steps:\n"
                "      - uses: actions/checkout@v4\n"
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
        lang_eco = _LANG_ECOSYSTEM.get(config.language)
        if lang_eco:
            ecosystems.insert(
                0,
                f'  - package-ecosystem: "{lang_eco}"\n'
                '    directory: "/"\n'
                "    schedule:\n"
                '      interval: "weekly"\n'
                "    open-pull-requests-limit: 5\n",
            )
        return "version: 2\nupdates:\n" + "\n".join(ecosystems)
