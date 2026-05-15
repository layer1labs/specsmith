# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""CI/CD Manager — enable, monitor, and watch CI/CD for any git platform.

Supports GitHub (gh CLI), GitLab (glab CLI), and Bitbucket (bb CLI).
Degrades gracefully when the platform CLI is not installed.

REQ-309: CI automation must be togglable per project via specsmith config
and Kairos Settings → Governance.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CiRunResult:
    """Status of the most recent CI/CD run."""

    platform: str = "unknown"
    ci_available: bool = False
    ci_passing: bool | None = None
    last_run_status: str = "unknown"  # "success" | "failure" | "pending" | "unknown"
    last_run_url: str = ""
    last_run_name: str = ""
    open_dep_alerts: int = 0
    open_security_alerts: int = 0
    open_prs: int = 0
    details: list[str] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "ci_available": self.ci_available,
            "ci_passing": self.ci_passing,
            "last_run_status": self.last_run_status,
            "last_run_url": self.last_run_url,
            "last_run_name": self.last_run_name,
            "open_dep_alerts": self.open_dep_alerts,
            "open_security_alerts": self.open_security_alerts,
            "open_prs": self.open_prs,
            "details": self.details,
            "error": self.error,
        }


def _detect_platform(root: Path) -> str:
    """Detect the git platform from remote URL or config files."""
    # Try git remote
    import subprocess

    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=str(root),
        )
        url = result.stdout.strip().lower()
        if "github.com" in url:
            return "github"
        if "gitlab.com" in url or "gitlab" in url:
            return "gitlab"
        if "bitbucket.org" in url or "bitbucket" in url:
            return "bitbucket"
    except Exception:  # noqa: BLE001
        pass

    # Fall back to config file presence
    if (root / ".github").is_dir():
        return "github"
    if (root / ".gitlab-ci.yml").exists():
        return "gitlab"
    if (root / "bitbucket-pipelines.yml").exists():
        return "bitbucket"

    return "github"  # default assumption


def _get_platform_instance(platform_name: str):  # type: ignore[return]
    """Return a VCSPlatform instance for the given platform name."""
    from specsmith.vcs import get_platform

    return get_platform(platform_name)


class CiManager:
    """High-level CI/CD orchestrator for a specsmith-governed project."""

    def __init__(self, project_dir: str = ".") -> None:
        self.root = Path(project_dir).resolve()
        self._platform_name: str | None = None

    @property
    def platform_name(self) -> str:
        if self._platform_name is None:
            self._platform_name = _detect_platform(self.root)
        return self._platform_name

    def enable(
        self,
        *,
        platform: str | None = None,
        force: bool = False,
    ) -> list[str]:
        """Generate / update CI, Dependabot, and security configs.

        Args:
            platform: Override platform detection. One of 'github', 'gitlab', 'bitbucket'.
            force: If True, overwrite existing CI config. Default skips if CI exists.

        Returns:
            List of file paths created or updated.
        """
        from specsmith.config import ProjectConfig
        from specsmith.paths import find_scaffold

        scaffold_path = find_scaffold(self.root)
        if not scaffold_path or not scaffold_path.exists():
            raise RuntimeError(
                "No scaffold.yml found. Run 'specsmith init' or 'specsmith import' first."
            )

        import yaml

        raw = yaml.safe_load(scaffold_path.read_text(encoding="utf-8")) or {}
        try:
            config = ProjectConfig(**raw)
        except Exception as exc:
            raise RuntimeError(f"Invalid scaffold.yml: {exc}") from exc

        p_name = platform or _detect_platform(self.root)
        self._platform_name = p_name

        try:
            platform_obj = _get_platform_instance(p_name)
        except ValueError as exc:
            raise RuntimeError(f"Unsupported platform '{p_name}': {exc}") from exc

        created: list[str] = []

        # CI config
        ci_exists = bool(
            list((self.root / ".github" / "workflows").glob("*.yml"))
            if (self.root / ".github" / "workflows").is_dir()
            else []
        ) or (self.root / ".gitlab-ci.yml").exists() or (
            self.root / "bitbucket-pipelines.yml"
        ).exists()

        if force or not ci_exists:
            files = platform_obj.generate_ci_config(config, self.root)
            created.extend(str(f.relative_to(self.root)) for f in files)

        # Dependabot / dependency config (always regenerate — idempotent)
        dep_files = platform_obj.generate_dependency_config(config, self.root)
        created.extend(str(f.relative_to(self.root)) for f in dep_files)

        # Security config
        sec_files = platform_obj.generate_security_config(config, self.root)
        created.extend(str(f.relative_to(self.root)) for f in sec_files)

        # CodeQL for GitHub Python/JS/TS/Go projects
        if p_name == "github" and config.language in (
            "python",
            "javascript",
            "typescript",
            "go",
        ):
            codeql_path = _write_codeql_workflow(config, self.root)
            if codeql_path:
                created.append(str(codeql_path.relative_to(self.root)))

        # Persist setting to .specsmith/config.yml
        _set_ci_automation_enabled(self.root, enabled=True, platform=p_name)

        return created

    def status(self) -> CiRunResult:
        """Poll the current CI/CD status for this project."""
        result = CiRunResult(platform=self.platform_name)

        try:
            platform_obj = _get_platform_instance(self.platform_name)
        except ValueError:
            result.error = f"Unsupported platform: {self.platform_name}"
            return result

        if not platform_obj.is_cli_available():
            result.error = f"{platform_obj.cli_name} CLI not found. Install it to enable CI status polling."
            return result

        result.ci_available = True

        try:
            ps = platform_obj.check_status()
            result.ci_passing = ps.ci_passing
            result.open_dep_alerts = ps.open_alerts
            result.open_prs = ps.open_prs
            result.details = ps.details

            # Derive last_run_status from ci_passing
            if ps.ci_passing is True:
                result.last_run_status = "success"
            elif ps.ci_passing is False:
                result.last_run_status = "failure"
            else:
                result.last_run_status = "unknown"

            # Try to get the last run URL for GitHub
            if self.platform_name == "github":
                run_info = platform_obj.run_command(
                    ["run", "list", "--limit", "1", "--json", "url,name,status,conclusion"]
                )
                if run_info.success and run_info.output:
                    try:
                        runs = json.loads(run_info.output)
                        if runs:
                            result.last_run_url = runs[0].get("url", "")
                            result.last_run_name = runs[0].get("name", "")
                    except json.JSONDecodeError:
                        pass

                # Security alerts
                sec = platform_obj.run_command(
                    [
                        "api",
                        "repos/{owner}/{repo}/code-scanning/alerts",
                        "--jq",
                        "[.[] | select(.state==\"open\")] | length",
                    ]
                )
                if sec.success and sec.output.strip().isdigit():
                    result.open_security_alerts = int(sec.output.strip())

        except Exception as exc:  # noqa: BLE001
            result.error = f"Error polling CI status: {exc}"

        return result

    def watch(
        self,
        *,
        timeout: int = 300,
        poll_interval: int = 15,
        on_event=None,  # Callable[[dict], None] | None
    ) -> CiRunResult:
        """Poll CI status until the run completes or timeout fires.

        Args:
            timeout: Max seconds to wait (default 300 = 5 min).
            poll_interval: Seconds between polls (default 15).
            on_event: Optional callback called with each status dict.

        Returns:
            Final CiRunResult.
        """
        deadline = time.monotonic() + timeout
        last_result = CiRunResult(platform=self.platform_name)

        while time.monotonic() < deadline:
            result = self.status()
            last_result = result

            event = {
                "type": "ci_status",
                "status": result.last_run_status,
                "passing": result.ci_passing,
                "dep_alerts": result.open_dep_alerts,
                "security_alerts": result.open_security_alerts,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }

            if on_event:
                on_event(event)

            if result.last_run_status in ("success", "failure"):
                break  # Run complete

            time.sleep(poll_interval)

        return last_result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_codeql_workflow(config: Any, root: Path) -> Path | None:
    """Write a CodeQL workflow if one doesn't already exist."""
    from specsmith.config import ProjectConfig  # type: ignore[attr-defined]

    wf_dir = root / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    codeql_path = wf_dir / "codeql.yml"

    if codeql_path.exists():
        return None  # Don't overwrite existing CodeQL config

    lang = getattr(config, "language", "python")
    content = f"""\
name: CodeQL

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
  schedule:
    - cron: '30 2 * * 1'  # Weekly Monday 02:30 UTC

permissions:
  actions: read
  contents: read
  security-events: write

jobs:
  analyze:
    name: Analyze ({lang})
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: {lang}
          queries: security-extended,security-and-quality

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
        with:
          category: "/language:{lang}"
"""
    codeql_path.write_text(content, encoding="utf-8")
    return codeql_path


def _set_ci_automation_enabled(root: Path, *, enabled: bool, platform: str) -> None:
    """Persist ci_automation setting to .specsmith/config.yml."""
    import yaml

    config_path = root / ".specsmith" / "config.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any] = {}
    if config_path.exists():
        try:
            existing = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        except Exception:  # noqa: BLE001
            existing = {}

    existing["ci_automation_enabled"] = enabled
    existing["ci_platform"] = platform

    config_path.write_text(yaml.dump(existing, default_flow_style=False), encoding="utf-8")


def get_ci_automation_status(root: Path) -> tuple[bool, str]:
    """Return (enabled, platform) from .specsmith/config.yml."""
    import yaml

    config_path = root / ".specsmith" / "config.yml"
    if not config_path.exists():
        return False, "github"

    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return bool(data.get("ci_automation_enabled", False)), str(
            data.get("ci_platform", "github")
        )
    except Exception:  # noqa: BLE001
        return False, "github"
