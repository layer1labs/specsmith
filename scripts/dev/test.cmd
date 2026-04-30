@echo off
rem SPDX-License-Identifier: MIT
rem Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
rem
rem cmd.exe wrapper for pytest that switches the current console to UTF-8
rem (code page 65001) and forces Python's stdout/stderr to UTF-8 so the
rem test reporter doesn't render as mojibake. Use the PowerShell wrapper
rem if you're on pwsh.

chcp 65001 > NUL
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
py -m pytest %*
exit /b %ERRORLEVEL%
