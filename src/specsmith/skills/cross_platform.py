# SPDX-License-Identifier: MIT
"""Cross-platform build and tooling skills — CMake, vcpkg, package managers."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="terminal-awareness",
        name="Terminal Awareness — PowerShell 5/7, cmd.exe, bash/zsh/fish, spawn+PID, cleanup",
        description=(
            "Full cross-platform shell guide: detect the active shell, use correct syntax "
            "per shell, spawn subprocesses with PID tracking, prevent hanging processes, "
            "and clean up reliably on Windows, Linux, and macOS."
        ),
        domain=SkillDomain.CROSS_PLATFORM,
        tags=[
            "powershell",
            "pwsh",
            "cmd",
            "bash",
            "zsh",
            "fish",
            "shell",
            "terminal",
            "pid",
            "subprocess",
            "cleanup",
            "cross-platform",
            "windows",
            "linux",
            "macos",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=[],
        body="""\
# Terminal Awareness Skill

## Rule: Always match syntax to the active shell
Never run PowerShell cmdlets in bash. Never run bash-isms in cmd.exe.
Detect first, then adapt.

## Shell detection

### From Python (most reliable in agent code)
```python
import os, sys

def detect_shell() -> str:
    # Explicit override
    shell = os.environ.get("SHELL", "")          # /bin/bash, /bin/zsh, /usr/bin/fish
    comspec = os.environ.get("ComSpec", "")       # C:\\Windows\\System32\\cmd.exe
    psver = os.environ.get("PSVersionTable", "")  # set by PowerShell
    if os.environ.get("__CFBundleIdentifier", ""):  # macOS Terminal.app
        pass
    if shell.endswith("fish"):   return "fish"
    if shell.endswith("zsh"):    return "zsh"
    if shell.endswith("bash"):   return "bash"
    if comspec:                  return "cmd"
    if os.environ.get("PSModulePath"): return "powershell"  # pwsh or ps5
    return "unknown"
```

### From the shell itself
```bash
echo $0                  # bash: bash or -bash; zsh: -zsh; fish: fish
ps -p $$                 # Linux/macOS: show parent process
```
```pwsh
$PSVersionTable.PSVersion   # PowerShell version (5.x or 7.x)
$PSVersionTable.PSEdition   # Desktop (PS5) vs Core (PS7)
```
```bat
echo %ComSpec%              # cmd.exe: C:\\Windows\\System32\\cmd.exe
```

## PowerShell 5 (Desktop) vs PowerShell 7 (Core) — critical differences

| Feature | PS5 (Windows only) | PS7 (cross-platform) |
|---|---|---|
| Invoke | `powershell.exe` | `pwsh.exe` / `pwsh` |
| Edition | `Desktop` | `Core` |
| Null coalescing | NOT available | `$a ??= $b` |
| Ternary | NOT available | `$a ? $b : $c` |
| Pipelines | `ForEach-Object` | `ForEach-Object -Parallel` |
| Import-Module | Single-threaded | Thread-safe |
| `-ErrorAction` | Limited | Full `Stop`/`SilentlyContinue` |
| Encoding default | UTF-16 LE | UTF-8 |
| `&&` / `\\|\\|` | NOT available | Available (PS7.1+) |
| Out-File encoding | UTF-16 | UTF-8 (use `-Encoding utf8NoBOM`) |
| `$env:PATH` sep | `;` | `;` (Windows) / `:` (Linux/macOS) |

```pwsh
# Safe version guard
if ($PSVersionTable.PSVersion.Major -lt 7) {
    Write-Error "This script requires PowerShell 7+"; exit 1
}

# PS7-only: parallel foreach
1..10 | ForEach-Object -Parallel { Start-Process "task$_" } -ThrottleLimit 4

# Both: null coalescing the safe way
$val = if ($null -ne $x) { $x } else { "default" }  # PS5+PS7
$val = $x ?? "default"                               # PS7 only

# Encoding — always explicit
"content" | Out-File -FilePath file.txt -Encoding utf8NoBOM  # PS7
[System.IO.File]::WriteAllText("file.txt", "content")        # PS5 safe UTF-8
```

## cmd.exe rules
```bat
:: Variables: %VAR% not $VAR
set MYVAR=hello
echo %MYVAR%

:: No pipelines to non-exe targets
:: WRONG: dir | Select-String    <-- Select-String is PowerShell
:: RIGHT: dir | findstr pattern

:: Conditionals
if exist file.txt (echo found) else (echo missing)
if %ERRORLEVEL% NEQ 0 (echo failed)

:: Multiline — use ^ for continuation
copy /Y src\file.txt ^\n  dest\file.txt

:: Spawn and wait
start /wait myprogram.exe arg1
call script.bat              :: blocks until done

:: Get PID of last background process — cmd has no native $!
:: Use wmic or PowerShell from within cmd:
powershell -Command "$proc = Start-Process myapp -PassThru; $proc.Id"
```

## bash / zsh / fish
```bash
# bash/zsh: spawn in background, capture PID
myprogram &
BG_PID=$!
wait $BG_PID           # blocks until done
echo "Exit: $?"

# With timeout (bash 4+)
timeout 30s myprogram || echo "timed out or failed"

# fish: no $!, use fish_pid
set bg_pid (myprogram &; echo $last_pid)

# Trap for cleanup on exit (bash/zsh)
trap 'kill $BG_PID 2>/dev/null' EXIT INT TERM

# Check if process is still running
kill -0 $BG_PID 2>/dev/null && echo "running" || echo "dead"
```

## Subprocess spawn with PID tracking

### Python (cross-platform, preferred in agent tooling)
```python
import subprocess, signal, os, sys

# Spawn and track
proc = subprocess.Popen(
    ["myprogram", "--arg"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    # Windows: CREATE_NEW_PROCESS_GROUP for clean Ctrl+C forwarding
    **({"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
       if sys.platform == "win32" else {}),
)
pid = proc.pid

# Wait with timeout
try:
    stdout, stderr = proc.communicate(timeout=60)
except subprocess.TimeoutExpired:
    proc.kill()                          # force-kill on timeout
    stdout, stderr = proc.communicate()  # drain pipes
    raise

# Ensure cleanup
def kill_proc(p: subprocess.Popen) -> None:
    if p.poll() is None:          # still running
        if sys.platform == "win32":
            p.send_signal(signal.CTRL_BREAK_EVENT)  # Windows
        else:
            p.terminate()         # SIGTERM
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()              # SIGKILL fallback
```

### PowerShell spawn + PID
```pwsh
# Start-Process returns a System.Diagnostics.Process object
$proc = Start-Process -FilePath "myprogram" -ArgumentList "--arg" -PassThru -NoNewWindow
$pid  = $proc.Id

# Wait with timeout (ms)
$done = $proc.WaitForExit(30000)   # 30 s
if (-not $done) {
    Stop-Process -Id $pid -Force
    throw "Timed out"
}
Write-Host "Exit code: $($proc.ExitCode)"

# Cleanup on script exit
try {
    # ... do work ...
} finally {
    if ($proc -and -not $proc.HasExited) { Stop-Process -Id $pid -Force }
}
```

## Preventing hanging processes

### Root causes and fixes
| Cause | Fix |
|---|---|
| stdout/stderr pipe full | Always use `communicate()` or `DEVNULL` — never `Popen.wait()` with pipes |
| stdin waiting for input | Pass `stdin=subprocess.DEVNULL` or `input=b""` |
| Zombie child (POSIX) | Call `proc.wait()` after `proc.kill()` |
| Windows job object leak | Use `CREATE_NEW_PROCESS_GROUP` + `GenerateConsoleCtrlEvent` |
| Timeout not enforced | Always set `timeout=` in `communicate()` — never bare `wait()` |

```python
# Safe subprocess runner (Python, all platforms)
def run_safe(cmd: list[str], timeout: int = 60) -> tuple[int, str, str]:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.DEVNULL,   # never hang waiting for input
    )
    try:
        out, err = proc.communicate(timeout=timeout)
        return proc.returncode, out.decode(errors="replace"), err.decode(errors="replace")
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.communicate()  # drain to avoid zombie
        return -1, "", f"Timed out after {timeout}s"
```

## Cross-platform command equivalents

| Intent | bash/zsh | PowerShell | cmd.exe |
|---|---|---|---|
| Print text | `echo text` | `Write-Host text` | `echo text` |
| Set variable | `VAR=val` | `$var = 'val'` | `set VAR=val` |
| Read variable | `$VAR` | `$var` | `%VAR%` |
| Check exit code | `echo $?` | `$LASTEXITCODE` | `echo %ERRORLEVEL%` |
| List directory | `ls` / `dir` | `Get-ChildItem` / `dir` | `dir` |
| Copy file | `cp src dst` | `Copy-Item src dst` | `copy src dst` |
| Move file | `mv src dst` | `Move-Item src dst` | `move src dst` |
| Delete file | `rm file` | `Remove-Item file` | `del file` |
| Make dir | `mkdir dir` | `New-Item -Type Directory` | `mkdir dir` |
| Current dir | `pwd` | `$PWD` / `Get-Location` | `cd` |
| Change dir | `cd path` | `Set-Location path` | `cd path` |
| Environment var | `export K=V` | `$env:K = 'V'` | `set K=V` |
| Command exists | `which cmd` | `Get-Command cmd -EA SilentlyContinue` | `where cmd` |
| Kill process | `kill -9 PID` | `Stop-Process -Id PID -Force` | `taskkill /F /PID PID` |
| List processes | `ps aux` | `Get-Process` | `tasklist` |
| Sleep | `sleep 5` | `Start-Sleep 5` | `timeout /t 5` |
| Null device | `/dev/null` | `$null` / `NUL` | `NUL` |
| Script exit | `exit 1` | `exit 1` | `exit /b 1` |
| And-chain | `cmd1 && cmd2` | `cmd1; if ($?) { cmd2 }` (PS5) / `cmd1 && cmd2` (PS7) | `cmd1 && cmd2` |
| Or-fallback | `cmd1 \\|\\| cmd2` | `cmd1; if (-not $?) { cmd2 }` (PS5) / `cmd1 \\|\\| cmd2` (PS7) | `cmd1 \\|\\| cmd2` |

## macOS-specific notes
- Default shell since Catalina (10.15): **zsh** (`/bin/zsh`)
- bash is `/bin/bash` (3.2 — ancient; install brew bash for 5.x)
- `brew install coreutils` for GNU equivalents (`gls`, `gcp`, etc.)
- `launchctl list` replaces `systemctl` for service management
- Gatekeeper: new binaries need `xattr -d com.apple.quarantine <bin>`

## Cleanup checklist (before ending any session that spawned processes)
1. `kill $BG_PID` (bash) / `Stop-Process $proc.Id` (pwsh) — signal first
2. `wait $BG_PID` / `$proc.WaitForExit(5000)` — confirm termination
3. `kill -9 $BG_PID` / `Stop-Process -Force` — force if still alive
4. Remove `.specsmith/pids/<pid>.json` via `specsmith abort --all`
5. Verify: `specsmith ps` / `ps aux | grep myprogram` / `tasklist | findstr myprogram`
""",
    ),
    SkillEntry(
        slug="cmake-cross-platform",
        name="CMake — cross-platform builds, vcpkg, conan, presets",
        description=(
            "CMake cross-platform build system: modern target-based configuration, "
            "vcpkg/conan dependency management, CMake presets, and CI integration."
        ),
        domain=SkillDomain.CROSS_PLATFORM,
        tags=[
            "cmake",
            "vcpkg",
            "conan",
            "cross-platform",
            "c",
            "cpp",
            "build",
            "ninja",
            "presets",
            "windows",
            "linux",
            "macos",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=["cmake", "ninja"],
        body="""\
# CMake Cross-Platform Skill

## Modern CMakeLists.txt (target-based)
```cmake
cmake_minimum_required(VERSION 3.25)
project(myapp VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)   # for clangd / clang-tidy

add_executable(myapp
    src/main.cpp
    src/engine.cpp)

target_include_directories(myapp
    PRIVATE src/include
    PUBLIC  include)

target_compile_options(myapp PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W4 /WX>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Werror>)

target_link_libraries(myapp
    PRIVATE fmt::fmt spdlog::spdlog)
```

## CMake Presets (CMakePresets.json)
```json
{
  "version": 6,
  "configurePresets": [
    {
      "name": "linux-release",
      "generator": "Ninja",
      "binaryDir": "build/linux-release",
      "cacheVariables": {
        "CMAKE_BUILD_TYPE": "Release",
        "CMAKE_TOOLCHAIN_FILE": "$env{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
      }
    },
    {
      "name": "windows-msvc",
      "generator": "Visual Studio 17 2022",
      "binaryDir": "build/windows-msvc",
      "architecture": {"value": "x64", "strategy": "set"},
      "cacheVariables": {
        "CMAKE_TOOLCHAIN_FILE": "$env{VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
      }
    }
  ],
  "buildPresets": [
    {"name": "linux-release", "configurePreset": "linux-release"},
    {"name": "windows-release", "configurePreset": "windows-msvc", "configuration": "Release"}
  ]
}
```
```bash
cmake --preset linux-release
cmake --build --preset linux-release
cmake --list-presets               # list all presets
```

## vcpkg dependency management
```bash
# Bootstrap vcpkg
git clone https://github.com/microsoft/vcpkg $HOME/vcpkg
$HOME/vcpkg/bootstrap-vcpkg.sh      # Linux/macOS
%USERPROFILE%\\vcpkg\\bootstrap-vcpkg.bat  # Windows

# Install packages (manifest mode — recommended)
# vcpkg.json in project root:
{
  "name": "myapp",
  "version": "1.0.0",
  "dependencies": [
    "fmt", "spdlog",
    {"name": "boost-filesystem", "version>=": "1.83.0"}
  ]
}
# Set VCPKG_ROOT and use CMAKE_TOOLCHAIN_FILE=.../vcpkg.cmake
cmake --preset linux-release   # auto-installs from vcpkg.json

vcpkg search boost              # search packages
vcpkg list                      # show installed
vcpkg install fmt:x64-windows   # manual install (classic mode)
```

## Conan 2 dependency management
```bash
pip install conan
conan profile detect            # auto-detect host profile
# conanfile.txt:
[requires]
fmt/10.2.1
spdlog/1.13.0
[generators]
CMakeDeps
CMakeToolchain

conan install . --build=missing  # install + generate CMake files
cmake -B build -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake
cmake --build build
```

## Cross-compilation with CMake toolchain
```cmake
# toolchain-aarch64-linux.cmake
set(CMAKE_SYSTEM_NAME Linux)
set(CMAKE_SYSTEM_PROCESSOR aarch64)
set(CMAKE_C_COMPILER aarch64-linux-gnu-gcc)
set(CMAKE_CXX_COMPILER aarch64-linux-gnu-g++)
set(CMAKE_FIND_ROOT_PATH /opt/sysroot-aarch64)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
```
```bash
cmake -B build-arm -DCMAKE_TOOLCHAIN_FILE=toolchain-aarch64-linux.cmake
cmake --build build-arm
```

## Common pitfalls
- CMake 3.25+: use `cmake --preset`; older: pass `-G Ninja -B build`.
- MSVC: open "Developer Command Prompt" or use `vcvarsall.bat x64`.
- vcpkg: set `VCPKG_ROOT` env var system-wide; don't hardcode paths.
- `compile_commands.json`: generated by Ninja/Make, not MSVC
  (use `CMAKE_EXPORT_COMPILE_COMMANDS=ON`).
""",
    ),
    SkillEntry(
        slug="package-managers",
        name="Package Managers — brew, winget, scoop, apt, nix (cross-platform)",
        description=(
            "Cross-platform package manager workflows: Homebrew (macOS/Linux), "
            "winget/scoop/choco (Windows), apt/dnf (Linux), and Nix for reproducibility."
        ),
        domain=SkillDomain.CROSS_PLATFORM,
        tags=[
            "homebrew",
            "brew",
            "winget",
            "scoop",
            "chocolatey",
            "apt",
            "dnf",
            "nix",
            "package-manager",
            "cross-platform",
        ],
        platforms=["windows", "linux", "macos"],
        prerequisites=[],
        body="""\
# Cross-Platform Package Managers Skill

## macOS — Homebrew
```bash
# Install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

brew install git cmake ninja python@3.12 node
brew install --cask visual-studio-code docker
brew upgrade                    # upgrade all packages
brew outdated                   # list outdatable packages
brew cleanup                    # remove old versions
brew leaves                     # show top-level installed packages
brew bundle dump                # export Brewfile
brew bundle install             # install from Brewfile

# Brewfile (commit to repo for team consistency)
tap "homebrew/cask"
brew "git"
brew "cmake"
brew "ninja"
cask "docker"
cask "visual-studio-code"
```

## Linux — apt (Debian/Ubuntu)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git cmake ninja-build python3 python3-pip nodejs npm
sudo apt install -y build-essential gcc g++ clang clang-tidy clang-format

# Add third-party repo (example: GitHub CLI)
type -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
    sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
    signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] \
    https://cli.github.com/packages stable main" \
    | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt update && sudo apt install gh

# List installed packages
dpkg -l | grep <pattern>
apt list --installed
```

## Linux — dnf (RHEL/Fedora/AlmaLinux)
```bash
sudo dnf update -y
sudo dnf install -y git cmake ninja-build python3 nodejs npm gcc gcc-c++ clang
sudo dnf groupinstall "Development Tools"
dnf list installed | grep <pattern>
```

## Windows — winget (built-in Windows Package Manager)
```powershell
winget search git
winget install Git.Git
winget install Kitware.CMake
winget install Python.Python.3.12
winget install Microsoft.VisualStudioCode
winget install Docker.DockerDesktop
winget upgrade --all                      # upgrade everything
winget export -o packages.json            # export installed list
winget import -i packages.json            # import and install
```

## Windows — Scoop (developer-friendly, no admin needed)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
Invoke-RestMethod -Uri https://get.scoop.sh | Invoke-Expression

scoop install git cmake ninja python nodejs
scoop bucket add extras
scoop install vscode
scoop update *           # update all
scoop status             # show updatable
scoop export > scoop-packages.json   # export
```

## Nix — reproducible, cross-platform
```bash
# Install Nix (Linux/macOS)
sh <(curl -L https://nixos.org/nix/install) --daemon

# nix shell — ephemeral env (no install)
nix shell nixpkgs#git nixpkgs#cmake nixpkgs#ninja

# flake.nix (project-level devShell)
{
  outputs = { nixpkgs, ... }: {
    devShell.x86_64-linux = nixpkgs.legacyPackages.x86_64-linux.mkShell {
      packages = with nixpkgs.legacyPackages.x86_64-linux; [
        git cmake ninja python3 nodejs
      ];
    };
  };
}
# Enter dev shell: nix develop
```

## Common pitfalls
- Homebrew on Apple Silicon: installs to `/opt/homebrew/`; Intel: `/usr/local/`.
- winget: requires Windows Package Manager app from Store on older Windows 10.
- Scoop: installs to `~/scoop/` — no admin rights needed, great for CI.
- Nix: steep learning curve but ultimate reproducibility; use nix-shell for experiments.
""",
    ),
]
