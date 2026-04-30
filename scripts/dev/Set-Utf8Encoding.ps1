# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
#
# Set the current PowerShell session to UTF-8 input/output encoding so child
# processes (Python, pytest, ruff, mypy, ...) that emit UTF-8 text don't
# render as mojibake (e.g. `ΓêÜ` instead of `✓`, `ΓÇö` instead of `—`,
# `Γåô` instead of `→`).
#
# Why this is needed:
#   PowerShell on Windows defaults `[Console]::OutputEncoding` to the active
#   OEM code page (cp437 / cp1252). When pytest writes UTF-8 bytes to its
#   stdout, PowerShell decodes them with that legacy code page and the
#   multi-byte sequences appear as garbage. PowerShell 7.4+ improves this
#   only for `$OutputEncoding` (the encoding PowerShell uses to *send* data
#   to children); the receive path still respects the active code page.
#
# What this script does:
#   * Switches the active code page to 65001 (UTF-8) via `chcp` so console
#     APIs and child cmd.exe invocations agree on UTF-8.
#   * Sets `[Console]::OutputEncoding` and `[Console]::InputEncoding` to
#     UTF-8 so PowerShell decodes incoming child stdout/stderr as UTF-8.
#   * Sets `$OutputEncoding` (used when piping into native commands) to
#     UTF-8 too. Modern PowerShell already defaults this to UTF-8 but we
#     re-assert it for older 5.1 sessions.
#   * Sets `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` so Python sub-shells
#     emit UTF-8 regardless of the locale settings.
#
# Usage:
#   PS> . .\scripts\dev\Set-Utf8Encoding.ps1
#   PS> py -m pytest        # ✓ / ✗ / — render correctly
#
# This is dot-sourced (note the leading `.`) so the encoding changes apply
# to the calling shell. Running it without dot-sourcing affects only the
# child PowerShell process and is a no-op for the caller.
#
# Idempotent: re-running when already in UTF-8 mode is a no-op.

$null = & chcp.com 65001 2>&1

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
$OutputEncoding           = [System.Text.UTF8Encoding]::new()

# Python UTF-8 mode — Python 3.7+ honours both env vars. PYTHONUTF8=1
# enables UTF-8 mode globally; PYTHONIOENCODING covers stdin/stdout/stderr
# specifically and is older / more widely supported.
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'

if ($Host.UI.RawUI -and -not [Environment]::CommandLine.Contains('-NonInteractive')) {
  Write-Host "[utf8] active code page: 65001 ; PYTHONUTF8=1" -ForegroundColor DarkGreen
}
