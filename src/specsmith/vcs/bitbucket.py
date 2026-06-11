# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Bitbucket platform integration."""

from __future__ import annotations

from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.tools import LANG_CI_META, get_format_check_commands, get_tools
from specsmith.vcs.base import CommandResult, PlatformStatus, VCSPlatform


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
        tools = get_tools(config)
        meta = LANG_CI_META.get(config.language, {})
        image = meta.get("docker_image", "ubuntu:latest")
        install = meta.get("install", "")
        bb_cache = meta.get("bb_cache", "")
        is_python = config.language == "python"

        ci = f"image: {image}\n\npipelines:\n  default:\n"

        # Lint step
        if tools.lint or tools.format:
            ci += "    - step:\n        name: Lint\n"
            if bb_cache:
                ci += f"        caches:\n          - {bb_cache}\n"
            ci += "        script:\n"
            if install:
                ci += f"          - {install}\n"
            for cmd in tools.lint:
                ci += f"          - {cmd}\n"
            for cmd in get_format_check_commands(tools):
                ci += f"          - {cmd}\n"

        # Test step
        if tools.test:
            ci += "    - step:\n        name: Test\n"
            if bb_cache:
                ci += f"        caches:\n          - {bb_cache}\n"
            ci += "        script:\n"
            if install:
                ci += f"          - {install}\n"
            for cmd in tools.test:
                if cmd == "pytest" and is_python:
                    ci += (
                        f"          - pytest --cov={config.package_name}"
                        " --cov-report=term-missing\n"
                    )
                else:
                    ci += f"          - {cmd}\n"

        # Security step
        if tools.security:
            ci += "    - step:\n        name: Security\n"
            if bb_cache:
                ci += f"        caches:\n          - {bb_cache}\n"
            ci += "        script:\n"
            if is_python:
                ci += "          - pip install -e .\n"
            elif install:
                ci += f"          - {install}\n"
            for cmd in tools.security:
                if cmd == "pip-audit":
                    ci += "          - pip install pip-audit\n"
                    ci += "          - pip-audit\n"
                elif cmd == "cargo audit":
                    ci += "          - cargo install cargo-audit\n"
                    ci += "          - cargo audit\n"
                else:
                    ci += f"          - {cmd}\n"

        # Fallback
        if not any([tools.lint, tools.test, tools.security, tools.format]):
            ci += (
                "    - step:\n        name: Build\n        script:\n"
                f"          - echo 'Add {config.type_label} build steps here'\n"
            )

        return ci
