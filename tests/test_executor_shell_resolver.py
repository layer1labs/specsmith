# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for cross-platform shell resolver (REQ-313).

Named tests:
- EXECSHELL-001: Default resolution prefers pwsh on Windows
- EXECSHELL-002: Default resolution prefers bash on POSIX
- EXECSHELL-003: SPECSMITH_SHELL environment override
- EXECSHELL-004: Explicit shell override parameter
- EXECSHELL-005: Shell family classification
- EXECSHELL-006: Version detection
- EXECSHELL-007: Cached resolver result
- EXECSHELL-008: No shell available diagnostic
- EXECSHELL-009: run_tracked uses resolved shell
- EXECSHELL-010: PowerShell non-interactive flags
"""

# ruff: noqa: SIM117

from __future__ import annotations

import os
import sys
from pathlib import Path
from subprocess import TimeoutExpired
from unittest.mock import MagicMock, patch

import pytest

# Import the module to access _resolver_cache directly (not a stale reference)
import specsmith.executor as _executor_mod
from specsmith.executor import (
    _classify_shell,
    _detect_shell_version,
    _resolve_posix_shell,
    _resolve_shell,
    _resolve_windows_shell,
    run_tracked,
)


def _clear_cache() -> None:
    """Clear the module-level resolver cache."""
    _executor_mod._resolver_cache = None


# ---------------------------------------------------------------------------
# EXECSHELL-001: Default resolution prefers pwsh on Windows
# ---------------------------------------------------------------------------


class TestEXECSHELL001DefaultWindowsResolution:
    """Default shell resolution on Windows prefers pwsh.exe."""

    def test_resolves_pwsh_when_available(self, tmp_path: Path) -> None:
        """When pwsh.exe is in PATH, resolver returns pwsh family."""
        with patch.object(sys, "platform", "win32"):
            with patch("shutil.which", return_value="C:/Program Files/PowerShell/7/pwsh.exe"):
                result = _resolve_windows_shell()

        assert result.shell_family == "pwsh"
        assert result.source == "windows-preferred"
        assert result.executable == "C:/Program Files/PowerShell/7/pwsh.exe"
        assert "-NoProfile" in result.argv_prefix
        assert "-NonInteractive" in result.argv_prefix
        assert "-Command" in result.argv_prefix

    def test_falls_back_to_powershell_when_no_pwsh(self, tmp_path: Path) -> None:
        """When pwsh.exe is absent but powershell.exe exists, resolver returns powershell."""
        with patch.object(sys, "platform", "win32"):
            # Mock which to return None for pwsh variants, then powershell.exe
            which_side_effect = MagicMock(
                side_effect=[
                    None,  # pwsh.exe → not found
                    None,  # pwsh → not found
                    # powershell.exe found
                    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                ]
            )
            with patch("shutil.which", side_effect=which_side_effect):
                result = _resolve_windows_shell()

        assert result.shell_family == "powershell"
        assert result.source == "windows-fallback"

    def test_falls_back_to_cmd_when_no_powershell(self, tmp_path: Path) -> None:
        """When neither pwsh nor powershell exist, resolver returns cmd.exe."""
        with patch.object(sys, "platform", "win32"):
            which_side_effect = MagicMock(
                side_effect=[None, None, None, None, "C:/Windows/System32/cmd.exe"]
            )
            with patch("shutil.which", side_effect=which_side_effect):
                result = _resolve_windows_shell()

        assert result.shell_family == "cmd"
        assert result.source == "windows-fallback"
        assert "/c" in result.argv_prefix


# ---------------------------------------------------------------------------
# EXECSHELL-002: Default resolution prefers bash on POSIX
# ---------------------------------------------------------------------------


class TestEXECSHELL002DefaultPOSIXResolution:
    """Default shell resolution on POSIX prefers bash."""

    def test_resolves_bash_when_available(self, tmp_path: Path) -> None:
        """When bash is in PATH, resolver returns bash family."""
        with patch.object(sys, "platform", "linux"):
            with patch("shutil.which", return_value="/usr/bin/bash"):
                result = _resolve_posix_shell()

        assert result.shell_family == "bash"
        assert result.source == "posix-default"
        assert result.executable == "/usr/bin/bash"
        assert "-c" in result.argv_prefix

    def test_falls_back_to_sh_when_no_bash(self, tmp_path: Path) -> None:
        """When bash is absent but sh exists, resolver returns sh."""
        with patch.object(sys, "platform", "linux"):
            which_side_effect = MagicMock(
                side_effect=[
                    None,  # bash → not found
                    "/bin/sh",  # sh → found
                ]
            )
            with patch("shutil.which", side_effect=which_side_effect):
                result = _resolve_posix_shell()

        assert result.shell_family == "sh"
        assert result.source == "posix-default"

    def test_no_shell_returns_diagnostic(self, tmp_path: Path) -> None:
        """When neither bash nor sh exist, resolver returns diagnostic."""
        with patch.object(sys, "platform", "linux"):
            with patch("shutil.which", return_value=None):
                result = _resolve_posix_shell()

        assert result.source == "none"
        assert "No supported shell" in result.diagnostic
        assert result.executable == ""


# ---------------------------------------------------------------------------
# EXECSHELL-003: SPECSMITH_SHELL environment override
# ---------------------------------------------------------------------------


class TestEXECSHELL003EnvOverride:
    """SPECSMITH_SHELL environment variable overrides default resolution."""

    def test_env_override_uses_specified_shell(self, tmp_path: Path) -> None:
        """SPECSMITH_SHELL=bash returns bash even on Windows."""
        with patch.dict(os.environ, {"SPECSMITH_SHELL": "bash"}):
            with patch.object(sys, "platform", "win32"):
                with patch("shutil.which", return_value="/usr/bin/bash"):
                    result = _resolve_shell()

        assert result.shell_family == "bash"
        assert result.source == "env"

    def test_env_override_invalid_shell(self, tmp_path: Path) -> None:
        """SPECSMITH_SHELL=nonexistent returns diagnostic with source=env."""
        _clear_cache()
        with patch.dict(os.environ, {"SPECSMITH_SHELL": "/nonexistent/shell"}):
            with patch("shutil.which", return_value=None):
                result = _resolve_shell()

        assert result.source == "env"
        assert "not found" in result.diagnostic

    def test_env_override_clears_cache(self, tmp_path: Path) -> None:
        """Changing SPECSMITH_SHELL invalidates cached result."""
        _clear_cache()

        with patch.dict(os.environ, {"SPECSMITH_SHELL": "bash"}):
            with patch("shutil.which", return_value="/usr/bin/bash"):
                result1 = _resolve_shell()

        # Clear cache
        _clear_cache()

        with patch.dict(os.environ, {"SPECSMITH_SHELL": "pwsh"}):
            with patch("shutil.which", return_value="C:/pwsh.exe"):
                result2 = _resolve_shell()

        assert result1.shell_family == "bash"
        assert result2.shell_family == "pwsh"


# ---------------------------------------------------------------------------
# EXECSHELL-004: Explicit shell override parameter
# ---------------------------------------------------------------------------


class TestEXECSHELL004ExplicitOverride:
    """Explicit shell parameter overrides all other resolution."""

    def test_explicit_shell_parameter(self, tmp_path: Path) -> None:
        """Passing shell='pwsh' returns pwsh family."""
        with patch("shutil.which", return_value="C:/pwsh.exe"):
            result = _resolve_shell(executable="pwsh")

        assert result.shell_family == "pwsh"
        assert result.source == "explicit"

    def test_explicit_shell_not_found(self, tmp_path: Path) -> None:
        """Passing nonexistent shell returns diagnostic."""
        result = _resolve_shell(executable="/nonexistent/shell")

        assert result.source == "explicit"
        assert "not found" in result.diagnostic


# ---------------------------------------------------------------------------
# EXECSHELL-005: Shell family classification
# ---------------------------------------------------------------------------


class TestEXECSHELL005ShellClassification:
    """Shell family classification is correct for all known shells."""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("pwsh", "pwsh"),
            ("pwsh.exe", "pwsh"),
            ("powershell", "powershell"),
            ("powershell.exe", "powershell"),
            ("ps", "powershell"),
            ("cmd", "cmd"),
            ("cmd.exe", "cmd"),
            ("bash", "bash"),
            ("sh", "sh"),
            ("zsh", "unknown"),
            ("fish", "unknown"),
        ],
    )
    def test_classify_shell(self, name: str, expected: str) -> None:
        """_classify_shell returns correct family for known shell names."""
        assert _classify_shell(name) == expected


# ---------------------------------------------------------------------------
# EXECSHELL-006: Version detection
# ---------------------------------------------------------------------------


class TestEXECSHELL006VersionDetection:
    """Shell version detection extracts version from --version output."""

    def test_detects_pwsh_version(self, tmp_path: Path) -> None:
        """PowerShell 7 version is detected from --version output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "PowerShell 7.4.0\r\nCopyright..."
            mock_run.return_value.stderr = ""

            version = _detect_shell_version("pwsh")

        assert "7.4.0" in version
        mock_run.assert_called_once_with(
            ["pwsh", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_detects_bash_version(self, tmp_path: Path) -> None:
        """Bash version is detected from --version output."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "GNU bash, version 5.1.16\n"
            mock_run.return_value.stderr = ""

            version = _detect_shell_version("/usr/bin/bash")

        assert "5.1.16" in version

    def test_version_detection_timeout_returns_empty(self, tmp_path: Path) -> None:
        """Timeout during version detection returns empty string."""
        with patch("subprocess.run", side_effect=TimeoutExpired("pwsh", 5)):
            version = _detect_shell_version("pwsh")

        assert version == ""


# ---------------------------------------------------------------------------
# EXECSHELL-007: Cached resolver result
# ---------------------------------------------------------------------------


class TestEXECSHELL007Cache:
    """Resolver result is cached for performance."""

    def test_cache_returns_same_result(self, tmp_path: Path) -> None:
        """Multiple calls without override return cached result."""
        _clear_cache()

        with patch("shutil.which", return_value="/usr/bin/bash"):
            with patch.object(sys, "platform", "linux"):
                result1 = _resolve_shell()
                # Verify cache is set
                assert _executor_mod._resolver_cache is not None
                result2 = _resolve_shell()

        # Both should be the same cached object
        assert result1 is result2
        assert result1 is _executor_mod._resolver_cache

    def test_cache_invalidated_by_override(self, tmp_path: Path) -> None:
        """Explicit override returns new result, not cached."""
        _clear_cache()

        with patch("shutil.which", return_value="/usr/bin/bash"):
            with patch.object(sys, "platform", "linux"):
                result1 = _resolve_shell()
                result2 = _resolve_shell(executable="pwsh")

        assert result1 is not result2


# ---------------------------------------------------------------------------
# EXECSHELL-008: No shell available diagnostic
# ---------------------------------------------------------------------------


class TestEXECSHELL008NoShellDiagnostic:
    """Diagnostic message is actionable when no shell is available."""

    def test_posix_no_shell_diagnostic(self, tmp_path: Path) -> None:
        """POSIX no-shell diagnostic mentions installing bash or sh."""
        _clear_cache()
        with patch.object(sys, "platform", "linux"):
            with patch("shutil.which", return_value=None):
                result = _resolve_shell()

        assert "Install bash or sh" in result.diagnostic
        assert "SPECSMITH_SHELL" in result.diagnostic


# ---------------------------------------------------------------------------
# EXECSHELL-009: run_tracked uses resolved shell
# ---------------------------------------------------------------------------


class TestEXECSHELL009RunTracked:
    """run_tracked() uses the resolved shell and records provenance."""

    def test_run_tracked_records_shell_family(self, tmp_path: Path) -> None:
        """ExecResult includes shell_family and shell_path."""
        _clear_cache()
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.returncode = 0

        # Use side_effect so pwsh.exe and powershell.exe return None (not found),
        # but cmd.exe returns the cmd path. This prevents real pwsh.exe from being found.
        which_side_effect = MagicMock(
            side_effect=[
                None,  # pwsh.exe → not found
                None,  # pwsh → not found
                None,  # powershell.exe → not found
                None,  # powershell → not found
                "C:/Windows/System32/cmd.exe",  # cmd.exe → found
            ]
        )
        with patch("shutil.which", side_effect=which_side_effect):
            with patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = mock_proc
                # Also mock subprocess.run for version detection
                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = TimeoutExpired("cmd", 5)
                    result = run_tracked(tmp_path, "echo hello", timeout=5)

        assert result.shell_family == "cmd"
        assert result.shell_path == "C:/Windows/System32/cmd.exe"
        assert result.exit_code == 0

    def test_run_tracked_with_explicit_shell(self, tmp_path: Path) -> None:
        """run_tracked with shell='bash' uses specified shell."""
        _clear_cache()
        mock_proc = MagicMock()
        mock_proc.pid = 12345
        mock_proc.returncode = 0

        with patch("shutil.which", return_value="/usr/bin/bash"):
            with patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = mock_proc
                with patch("subprocess.run") as mock_run:
                    mock_run.side_effect = TimeoutExpired("bash", 5)
                    result = run_tracked(tmp_path, "echo hello", timeout=5, shell="bash")

        assert result.shell_family == "bash"

    def test_run_tracked_no_shell_raises(self, tmp_path: Path) -> None:
        """run_tracked raises when no shell is available."""
        _clear_cache()
        with patch.object(sys, "platform", "linux"):
            with patch("shutil.which", return_value=None):
                with pytest.raises(RuntimeError, match="No supported shell"):
                    run_tracked(tmp_path, "echo hello", timeout=5)


# ---------------------------------------------------------------------------
# EXECSHELL-010: PowerShell non-interactive flags
# ---------------------------------------------------------------------------


class TestEXECSHELL010PowerShellFlags:
    """PowerShell invocations use non-interactive, non-profile behavior."""

    def test_pwsh_argv_prefix(self, tmp_path: Path) -> None:
        """pwsh argv prefix includes -NoProfile, -NonInteractive, -Command."""
        with patch.object(sys, "platform", "win32"):
            with patch("shutil.which", return_value="C:/pwsh.exe"):
                result = _resolve_windows_shell()

        assert "-NoProfile" in result.argv_prefix
        assert "-NonInteractive" in result.argv_prefix
        assert "-Command" in result.argv_prefix


def test_configured_shell_precedes_environment() -> None:
    _clear_cache()
    with (
        patch.dict(os.environ, {"SPECSMITH_SHELL": "bash"}),
        patch("shutil.which", return_value="C:/pwsh.exe"),
    ):
        result = _resolve_shell(config_shell="pwsh")
    assert result.source == "config"
    assert result.shell_family == "pwsh"


def test_direct_argv_bypasses_shell(tmp_path: Path) -> None:
    result = run_tracked(tmp_path, [sys.executable, "--version"], timeout=10)
    assert result.exit_code == 0
    assert result.shell_family == "direct"
    assert result.shell_path == sys.executable

    def test_powershell_argv_prefix(self, tmp_path: Path) -> None:
        """powershell argv prefix includes -NoProfile, -NonInteractive, -Command."""
        with patch.object(sys, "platform", "win32"):
            which_side_effect = MagicMock(
                side_effect=[
                    None,  # pwsh.exe → not found
                    None,  # pwsh → not found
                    # powershell.exe found
                    "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
                ]
            )
            with patch("shutil.which", side_effect=which_side_effect):
                result = _resolve_windows_shell()

        assert "-NoProfile" in result.argv_prefix
        assert "-NonInteractive" in result.argv_prefix
        assert "-Command" in result.argv_prefix
