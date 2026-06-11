# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""GitLab platform integration via glab CLI."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.tools import LANG_CI_META, get_format_check_commands, get_tools
from specsmith.vcs.base import CommandResult, PlatformStatus, VCSPlatform


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
        renovate_path = target / "renovate.json"
        renovate_path.write_text(
            '{\n  "$schema": "https://docs.renovatebot.com/renovate-schema.json",\n'
            '  "extends": ["config:recommended"]\n}\n',
            encoding="utf-8",
        )
        return [renovate_path]

    def generate_security_config(self, config: ProjectConfig, target: Path) -> list[Path]:
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
        tools = get_tools(config)
        meta = LANG_CI_META.get(config.language, {})
        image = meta.get("docker_image", "ubuntu:latest")
        install = meta.get("install", "")
        is_python = config.language == "python"

        # Determine stages
        stages: list[str] = []
        if tools.lint or tools.format:
            stages.append("lint")
        if tools.typecheck:
            stages.append("typecheck")
        stages.append("test")
        if tools.security:
            stages.append("security")

        ci = "stages:\n"
        for s in stages:
            ci += f"  - {s}\n"
        ci += "\n"

        # Lint stage
        if tools.lint or tools.format:
            ci += f"lint:\n  stage: lint\n  image: {image}\n  script:\n"
            if install:
                ci += f"    - {install}\n"
            for cmd in tools.lint:
                ci += f"    - {cmd}\n"
            for cmd in get_format_check_commands(tools):
                ci += f"    - {cmd}\n"
            ci += "\n"

        # Typecheck stage
        if tools.typecheck:
            ci += f"typecheck:\n  stage: typecheck\n  image: {image}\n  script:\n"
            if install:
                ci += f"    - {install}\n"
            for cmd in tools.typecheck:
                if cmd == "mypy" and is_python:
                    ci += f"    - mypy src/{config.package_name}/\n"
                else:
                    ci += f"    - {cmd}\n"
            ci += "\n"

        # Test stage
        ci += f"test:\n  stage: test\n  image: {image}\n  script:\n"
        if install:
            ci += f"    - {install}\n"
        for cmd in tools.test:
            if cmd == "pytest" and is_python:
                ci += f"    - pytest --cov={config.package_name} --cov-report=term-missing\n"
            else:
                ci += f"    - {cmd}\n"
        if is_python:
            ci += '  parallel:\n    matrix:\n      - PYTHON_VERSION: ["3.10", "3.12", "3.13"]\n'
        ci += "\n"

        # Security stage
        if tools.security:
            ci += f"security:\n  stage: security\n  image: {image}\n  script:\n"
            if is_python:
                ci += "    - pip install -e .\n"
            elif install:
                ci += f"    - {install}\n"
            for cmd in tools.security:
                if cmd == "pip-audit":
                    ci += "    - pip install pip-audit\n"
                    ci += "    - pip-audit\n"
                elif cmd == "cargo audit":
                    ci += "    - cargo install cargo-audit\n"
                    ci += "    - cargo audit\n"
                elif "govulncheck" in cmd:
                    ci += "    - go install golang.org/x/vuln/cmd/govulncheck@latest\n"
                    ci += f"    - {cmd}\n"
                else:
                    ci += f"    - {cmd}\n"
            ci += "  allow_failure: true\n"

        return ci
