@echo off
REM forge-cli — Windows Run
setlocal

set "PROJECT_ROOT=%~dp0.."
set "VENV_DIR=%PROJECT_ROOT%\.venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Run scripts\setup.cmd first.
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
forge_cli %*
