@echo off
REM forge-cli — Command Execution Shim (Windows)
REM Wraps external commands with PID tracking, timeout enforcement, and abort support.
REM Usage: scripts\exec.cmd "<command>" [timeout_seconds]
REM
REM PID files: .specsmith\pids\<pid>.json (for specsmith ps / specsmith abort)
REM Logs:      .specsmith\logs\exec_<timestamp>.stdout/.stderr
REM Prefer:    specsmith exec "<command>" --timeout <N>  (Python-based, full tracking)

setlocal enabledelayedexpansion

set "COMMAND=%~1"
set "TIMEOUT_SEC=%~2"
if "%TIMEOUT_SEC%"=="" set "TIMEOUT_SEC=120"

set "PROJECT_ROOT=%~dp0.."
set "PID_DIR=%PROJECT_ROOT%\.specsmith\pids"
set "LOG_DIR=%PROJECT_ROOT%\.specsmith\logs"
if not exist "%PID_DIR%" mkdir "%PID_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set "DT=%%I"
set "TIMESTAMP=%DT:~0,4%-%DT:~4,2%-%DT:~6,2%_%DT:~8,2%-%DT:~10,2%-%DT:~12,2%"
set "STDOUT_LOG=%LOG_DIR%\exec_%TIMESTAMP%.stdout"
set "STDERR_LOG=%LOG_DIR%\exec_%TIMESTAMP%.stderr"

echo [exec] Command : %COMMAND%
echo [exec] Timeout : %TIMEOUT_SEC%s

REM Launch command and capture PID
start /b cmd /c "%COMMAND%" > "%STDOUT_LOG%" 2> "%STDERR_LOG%"
for /f "tokens=2" %%P in ('tasklist /fi "imagename eq cmd.exe" /nh ^| findstr /i "cmd"') do (
    set "CMD_PID=%%P"
)

REM Write PID file for tracking
echo {"pid": %CMD_PID%, "command": "%COMMAND%", "timeout": %TIMEOUT_SEC%} > "%PID_DIR%\%CMD_PID%.json"

REM Wait with timeout
set /a ELAPSED=0
:wait_loop
tasklist /fi "PID eq %CMD_PID%" /nh 2>nul | findstr /i "%CMD_PID%" >nul
if errorlevel 1 goto :done
if %ELAPSED% geq %TIMEOUT_SEC% goto :timeout
timeout /t 1 /nobreak >nul
set /a ELAPSED+=1
goto :wait_loop

:timeout
echo [exec] TIMEOUT after %TIMEOUT_SEC%s — killing PID %CMD_PID%
taskkill /F /PID %CMD_PID% /T >nul 2>&1
del "%PID_DIR%\%CMD_PID%.json" >nul 2>&1
exit /b 124

:done
del "%PID_DIR%\%CMD_PID%.json" >nul 2>&1
set "EXIT_CODE=%ERRORLEVEL%"
if %EXIT_CODE% equ 0 (
    echo [exec] OK — exit code 0
) else (
    echo [exec] FAILED — exit code %EXIT_CODE%
)
exit /b %EXIT_CODE%
