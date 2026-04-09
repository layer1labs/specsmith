@echo off
REM specsmith — Windows Setup
setlocal

set "PROJECT_ROOT=%~dp0.."
set "VENV_DIR=%PROJECT_ROOT%\.venv"

echo specsmith setup (Windows)

where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+.
    exit /b 1
)

if not exist "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"
pip install -e "%PROJECT_ROOT%"
echo Setup complete.
