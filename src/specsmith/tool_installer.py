# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Platform-aware install commands for development tools.

Provides the best install command for each tool on the current platform,
using the preferred package manager (winget on Windows, brew on macOS,
apt/dnf/snap on Linux, pip/npm/cargo for language-specific tools).

Usage::

    from specsmith.tool_installer import get_best_install_command, KNOWN_TOOLS
    cmd = get_best_install_command("ghdl")
    print(cmd)   # → "sudo apt install ghdl"  (on Debian/Ubuntu Linux)
"""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass


@dataclass
class ToolInstallInfo:
    """Install information for a single tool."""

    key: str  # executable / tool key (matches FPGA_TOOL_EXES, toolrules keys)
    display_name: str  # human-readable name
    category: str  # fpga, python, rust, go, c, js, devops, linux, doc, other

    # Platform-specific install commands (None = no known method for that platform)
    linux_apt: str | None = None  # Debian/Ubuntu
    linux_dnf: str | None = None  # Fedora/RHEL
    linux_snap: str | None = None  # Snap
    macos: str | None = None  # Homebrew
    windows_winget: str | None = None  # winget (Windows 11+)
    windows_choco: str | None = None  # Chocolatey
    windows_scoop: str | None = None  # Scoop
    pip: str | None = None  # pip (cross-platform)
    npm: str | None = None  # npm (cross-platform)
    cargo: str | None = None  # cargo (cross-platform)
    manual: str | None = None  # manual URL / instructions (fallback)
    notes: str = ""  # additional notes


# ---------------------------------------------------------------------------
# Tool catalog
# ---------------------------------------------------------------------------

KNOWN_TOOLS: dict[str, ToolInstallInfo] = {
    # ── FPGA / HDL Simulation ────────────────────────────────────────────────
    "ghdl": ToolInstallInfo(
        key="ghdl",
        display_name="GHDL (VHDL Simulator)",
        category="fpga",
        linux_apt="sudo apt install ghdl",
        linux_dnf="sudo dnf install ghdl",
        macos="brew install ghdl",
        windows_winget="winget install --id GHDL.GHDL",
        windows_choco="choco install ghdl",
        manual="https://github.com/ghdl/ghdl/releases",
    ),
    "iverilog": ToolInstallInfo(
        key="iverilog",
        display_name="Icarus Verilog",
        category="fpga",
        linux_apt="sudo apt install iverilog",
        linux_dnf="sudo dnf install iverilog",
        macos="brew install icarus-verilog",
        windows_choco="choco install iverilog",
        manual="https://steveicarus.github.io/iverilog/",
    ),
    "verilator": ToolInstallInfo(
        key="verilator",
        display_name="Verilator",
        category="fpga",
        linux_apt="sudo apt install verilator",
        linux_dnf="sudo dnf install verilator",
        macos="brew install verilator",
        manual="https://verilator.org/guide/latest/install.html",
        notes="For latest features, build from source.",
    ),
    "vsg": ToolInstallInfo(
        key="vsg",
        display_name="VSG (VHDL Style Guide)",
        category="fpga",
        pip="pip install vsg",
        manual="https://vhdl-style-guide.readthedocs.io/",
    ),
    "yosys": ToolInstallInfo(
        key="yosys",
        display_name="Yosys (OSS synthesis)",
        category="fpga",
        linux_apt="sudo apt install yosys",
        linux_dnf="sudo dnf install yosys",
        macos="brew install yosys",
        windows_winget="winget install --id YosysHQ.Yosys",
        manual="https://github.com/YosysHQ/yosys/releases",
    ),
    "gtkwave": ToolInstallInfo(
        key="gtkwave",
        display_name="GTKWave (waveform viewer)",
        category="fpga",
        linux_apt="sudo apt install gtkwave",
        macos="brew install gtkwave",
        windows_winget="winget install --id GtkWave.GtkWave",
        windows_choco="choco install gtkwave",
        manual="https://gtkwave.sourceforge.net/",
    ),
    "sby": ToolInstallInfo(
        key="sby",
        display_name="SymbiYosys (formal verification)",
        category="fpga",
        linux_apt="sudo apt install symbiyosys",
        pip="pip install symbiyosys",
        manual="https://symbiyosys.readthedocs.io/",
        notes="Also requires Yosys and an SMT solver (e.g. z3).",
    ),
    # Vendor tools — manual only (no public package)
    "vivado": ToolInstallInfo(
        key="vivado",
        display_name="AMD Vivado",
        category="fpga",
        manual="https://www.xilinx.com/support/download.html",
        notes="Free WebPACK edition available. Requires AMD registration.",
    ),
    "quartus_sh": ToolInstallInfo(
        key="quartus_sh",
        display_name="Intel Quartus Prime",
        category="fpga",
        manual="https://www.intel.com/content/www/us/en/products/details/fpga/development-tools/quartus-prime.html",
        notes="Free Lite edition available. Requires Intel registration.",
    ),
    "diamondc": ToolInstallInfo(
        key="diamondc",
        display_name="Lattice Diamond",
        category="fpga",
        manual="https://www.latticesemi.com/latticediamond",
        notes="Free for all Lattice devices. Requires Lattice registration.",
    ),
    # ── Python tooling ───────────────────────────────────────────────────────
    "ruff": ToolInstallInfo(
        key="ruff",
        display_name="Ruff (Python linter)",
        category="python",
        pip="pip install ruff",
        linux_snap="sudo snap install ruff",
        macos="brew install ruff",
        windows_winget="winget install --id Astral.Ruff",
        windows_scoop="scoop install ruff",
        manual="https://docs.astral.sh/ruff/installation/",
    ),
    "mypy": ToolInstallInfo(
        key="mypy",
        display_name="Mypy (Python type checker)",
        category="python",
        pip="pip install mypy",
        macos="brew install mypy",
        linux_apt="sudo apt install python3-mypy",
        manual="https://mypy.readthedocs.io/",
    ),
    "pytest": ToolInstallInfo(
        key="pytest",
        display_name="pytest",
        category="python",
        pip="pip install pytest",
        manual="https://docs.pytest.org/",
    ),
    "uv": ToolInstallInfo(
        key="uv",
        display_name="uv (Python package manager)",
        category="python",
        pip="pip install uv",
        macos="brew install uv",
        windows_winget="winget install --id Astral.uv",
        windows_scoop="scoop install uv",
        manual="https://docs.astral.sh/uv/",
    ),
    "pip-audit": ToolInstallInfo(
        key="pip-audit",
        display_name="pip-audit (Python security)",
        category="python",
        pip="pip install pip-audit",
        manual="https://github.com/pypa/pip-audit",
    ),
    "bandit": ToolInstallInfo(
        key="bandit",
        display_name="Bandit (Python security linter)",
        category="python",
        pip="pip install bandit",
        manual="https://bandit.readthedocs.io/",
    ),
    "safety": ToolInstallInfo(
        key="safety",
        display_name="Safety (dependency checker)",
        category="python",
        pip="pip install safety",
        manual="https://safetycli.com/",
    ),
    "black": ToolInstallInfo(
        key="black",
        display_name="Black (Python formatter)",
        category="python",
        pip="pip install black",
        macos="brew install black",
        manual="https://black.readthedocs.io/",
    ),
    "isort": ToolInstallInfo(
        key="isort",
        display_name="isort (import sorter)",
        category="python",
        pip="pip install isort",
        manual="https://pycqa.github.io/isort/",
    ),
    "pyright": ToolInstallInfo(
        key="pyright",
        display_name="Pyright (Python type checker)",
        category="python",
        pip="pip install pyright",
        npm="npm install -g pyright",
        manual="https://github.com/microsoft/pyright",
    ),
    "pylint": ToolInstallInfo(
        key="pylint",
        display_name="Pylint",
        category="python",
        pip="pip install pylint",
        manual="https://pylint.readthedocs.io/",
    ),
    "flake8": ToolInstallInfo(
        key="flake8",
        display_name="Flake8",
        category="python",
        pip="pip install flake8",
        manual="https://flake8.pycqa.org/",
    ),
    "coverage": ToolInstallInfo(
        key="coverage",
        display_name="Coverage.py",
        category="python",
        pip="pip install coverage",
        manual="https://coverage.readthedocs.io/",
    ),
    "pre-commit": ToolInstallInfo(
        key="pre-commit",
        display_name="pre-commit",
        category="python",
        pip="pip install pre-commit",
        macos="brew install pre-commit",
        manual="https://pre-commit.com/",
    ),
    "nbstripout": ToolInstallInfo(
        key="nbstripout",
        display_name="nbstripout (notebook cleanup)",
        category="python",
        pip="pip install nbstripout",
        manual="https://github.com/kynan/nbstripout",
    ),
    "tox": ToolInstallInfo(
        key="tox",
        display_name="tox (test runner)",
        category="python",
        pip="pip install tox",
        manual="https://tox.wiki/",
    ),
    # ── JavaScript / TypeScript tooling ────────────────────────────────────────
    "eslint": ToolInstallInfo(
        key="eslint",
        display_name="ESLint",
        category="js",
        npm="npm install -g eslint",
        manual="https://eslint.org/",
    ),
    "prettier": ToolInstallInfo(
        key="prettier",
        display_name="Prettier",
        category="js",
        npm="npm install -g prettier",
        manual="https://prettier.io/",
    ),
    "jest": ToolInstallInfo(
        key="jest",
        display_name="Jest",
        category="js",
        npm="npm install -g jest",
        manual="https://jestjs.io/",
    ),
    "vitest": ToolInstallInfo(
        key="vitest",
        display_name="Vitest",
        category="js",
        npm="npm install -g vitest",
        manual="https://vitest.dev/",
    ),
    # ── C / C++ tooling ─────────────────────────────────────────────────────────
    "clang-tidy": ToolInstallInfo(
        key="clang-tidy",
        display_name="clang-tidy",
        category="c",
        linux_apt="sudo apt install clang-tidy",
        linux_dnf="sudo dnf install clang-tools-extra",
        macos="brew install llvm",
        windows_winget="winget install --id LLVM.LLVM",
        windows_choco="choco install llvm",
        manual="https://clang.llvm.org/extra/clang-tidy/",
    ),
    "clang-format": ToolInstallInfo(
        key="clang-format",
        display_name="clang-format",
        category="c",
        linux_apt="sudo apt install clang-format",
        macos="brew install llvm",
        windows_winget="winget install --id LLVM.LLVM",
        manual="https://clang.llvm.org/docs/ClangFormat.html",
    ),
    "cppcheck": ToolInstallInfo(
        key="cppcheck",
        display_name="cppcheck",
        category="c",
        linux_apt="sudo apt install cppcheck",
        linux_dnf="sudo dnf install cppcheck",
        macos="brew install cppcheck",
        windows_winget="winget install --id Cppcheck.Cppcheck",
        windows_choco="choco install cppcheck",
        manual="https://cppcheck.sourceforge.io/",
    ),
    "cmake": ToolInstallInfo(
        key="cmake",
        display_name="CMake",
        category="c",
        linux_apt="sudo apt install cmake",
        linux_dnf="sudo dnf install cmake",
        macos="brew install cmake",
        windows_winget="winget install --id Kitware.CMake",
        windows_choco="choco install cmake",
        pip="pip install cmake",
        manual="https://cmake.org/download/",
    ),
    # ── Rust tooling ───────────────────────────────────────────────────────────
    "cargo-audit": ToolInstallInfo(
        key="cargo-audit",
        display_name="cargo-audit (Rust security)",
        category="rust",
        cargo="cargo install cargo-audit",
        manual="https://github.com/rustsec/rustsec",
    ),
    "rustup": ToolInstallInfo(
        key="rustup",
        display_name="Rust (via rustup)",
        category="rust",
        linux_apt="curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh",
        macos="curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh",
        windows_winget="winget install --id Rustlang.Rustup",
        windows_choco="choco install rustup.install",
        manual="https://rustup.rs/",
    ),
    # ── Go tooling ────────────────────────────────────────────────────────────
    "govulncheck": ToolInstallInfo(
        key="govulncheck",
        display_name="govulncheck (Go security)",
        category="go",
        manual="go install golang.org/x/vuln/cmd/govulncheck@latest",
    ),
    "go": ToolInstallInfo(
        key="go",
        display_name="Go",
        category="go",
        linux_apt="sudo apt install golang-go",
        linux_dnf="sudo dnf install golang",
        macos="brew install go",
        windows_winget="winget install --id GoLang.Go",
        windows_choco="choco install golang",
        manual="https://go.dev/dl/",
    ),
    "golangci-lint": ToolInstallInfo(
        key="golangci-lint",
        display_name="golangci-lint",
        category="go",
        linux_apt="curl -sSfL https://raw.githubusercontent.com/golangci/golangci-lint/master/install.sh | sh -s -- -b $(go env GOPATH)/bin",
        macos="brew install golangci-lint",
        windows_scoop="scoop install golangci-lint",
        manual="https://golangci-lint.run/usage/install/",
    ),
    # ── Yocto / Embedded Linux ───────────────────────────────────────────────
    "oelint-adv": ToolInstallInfo(
        key="oelint-adv",
        display_name="oelint-adv (BitBake linter)",
        category="linux",
        pip="pip install oelint-adv",
        manual="https://github.com/priv-kweihmann/oelint-adv",
    ),
    "kas": ToolInstallInfo(
        key="kas",
        display_name="kas (Yocto build tool)",
        category="linux",
        pip="pip install kas",
        manual="https://kas.readthedocs.io/",
    ),
    # ── DevOps / IaC ─────────────────────────────────────────────────────────
    "terraform": ToolInstallInfo(
        key="terraform",
        display_name="Terraform / OpenTofu",
        category="devops",
        linux_apt=(
            "wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg && "
            'echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list && '
            "sudo apt update && sudo apt install terraform"
        ),
        macos="brew tap hashicorp/tap && brew install hashicorp/tap/terraform",
        windows_winget="winget install --id HashiCorp.Terraform",
        windows_choco="choco install terraform",
        manual="https://developer.hashicorp.com/terraform/downloads",
    ),
    "docker": ToolInstallInfo(
        key="docker",
        display_name="Docker",
        category="devops",
        linux_apt="curl -fsSL https://get.docker.com | sh",
        macos="brew install --cask docker",
        windows_winget="winget install --id Docker.DockerDesktop",
        windows_choco="choco install docker-desktop",
        manual="https://docs.docker.com/get-docker/",
    ),
    # ── Documentation ────────────────────────────────────────────────────────
    "vale": ToolInstallInfo(
        key="vale",
        display_name="Vale (prose linter)",
        category="doc",
        linux_apt="sudo snap install vale",
        macos="brew install vale",
        windows_winget="winget install --id Vale.Vale",
        windows_choco="choco install vale",
        manual="https://vale.sh/docs/vale-cli/installation/",
    ),
    "markdownlint": ToolInstallInfo(
        key="markdownlint",
        display_name="markdownlint-cli2",
        category="doc",
        npm="npm install -g markdownlint-cli2",
        manual="https://github.com/DavidAnson/markdownlint-cli2",
    ),
    # ── API tooling ──────────────────────────────────────────────────────────
    "spectral": ToolInstallInfo(
        key="spectral",
        display_name="Spectral (OpenAPI linter)",
        category="other",
        npm="npm install -g @stoplight/spectral-cli",
        manual="https://docs.stoplight.io/docs/spectral/",
    ),
    # ── Node / JS tooling ────────────────────────────────────────────────────
    "node": ToolInstallInfo(
        key="node",
        display_name="Node.js",
        category="js",
        linux_apt="sudo apt install nodejs npm",
        linux_dnf="sudo dnf install nodejs npm",
        macos="brew install node",
        windows_winget="winget install --id OpenJS.NodeJS",
        windows_choco="choco install nodejs",
        manual="https://nodejs.org/en/download/",
        notes="Recommended: use nvm/fnm for version management.",
    ),
}


# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------


def _detect_platform() -> str:
    """Return a simple platform identifier."""
    s = platform.system().lower()
    if s == "windows":
        return "windows"
    if s == "darwin":
        return "macos"
    return "linux"


def _has_cmd(exe: str) -> bool:
    """Return True if *exe* is on PATH."""
    return shutil.which(exe) is not None


def _preferred_linux_pkg_manager() -> str:
    """Return the preferred Linux package manager."""
    for mgr in ("apt", "dnf", "yum", "pacman", "zypper"):
        if _has_cmd(mgr):
            return mgr
    return "apt"


def _preferred_windows_pkg_manager() -> str:
    """Return the preferred Windows package manager."""
    for mgr in ("winget", "choco", "scoop"):
        if _has_cmd(mgr):
            return mgr
    return "winget"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_install_command(
    tool_key: str,
    target_platform: str | None = None,
    prefer_pip: bool = False,
) -> str | None:
    """Return the best install command for a tool on the given platform.

    *target_platform* is one of ``"windows"``, ``"macos"``, ``"linux"``; if
    omitted the current platform is detected automatically.

    Returns ``None`` if the tool is not in the catalog or no install method is
    known for the platform.
    """
    info = KNOWN_TOOLS.get(tool_key)
    if info is None:
        return None

    os_name = target_platform or _detect_platform()

    # Language-agnostic package managers preferred when prefer_pip is set
    if prefer_pip and info.pip:
        return info.pip

    if os_name == "windows":
        mgr = _preferred_windows_pkg_manager()
        if mgr == "winget" and info.windows_winget:
            return info.windows_winget
        if mgr == "choco" and info.windows_choco:
            return info.windows_choco
        if mgr == "scoop" and info.windows_scoop:
            return info.windows_scoop
        # Fall back through alternatives
        return (
            info.windows_winget
            or info.windows_choco
            or info.windows_scoop
            or info.pip
            or info.npm
            or info.cargo
            or info.manual
        )

    if os_name == "macos":
        return info.macos or info.pip or info.npm or info.cargo or info.manual

    # Linux
    mgr = _preferred_linux_pkg_manager()
    if mgr in ("apt",) and info.linux_apt:
        return info.linux_apt
    if mgr in ("dnf", "yum") and info.linux_dnf:
        return info.linux_dnf
    if mgr == "snap" and info.linux_snap:
        return info.linux_snap
    return (
        info.linux_apt
        or info.linux_dnf
        or info.linux_snap
        or info.pip
        or info.npm
        or info.cargo
        or info.manual
    )


def get_install_info(tool_key: str) -> ToolInstallInfo | None:
    """Return the full install info for a tool, or None if unknown."""
    return KNOWN_TOOLS.get(tool_key)


def list_tools(category: str | None = None) -> list[ToolInstallInfo]:
    """Return all known tools, optionally filtered by category."""
    tools = list(KNOWN_TOOLS.values())
    if category:
        tools = [t for t in tools if t.category == category]
    return sorted(tools, key=lambda t: t.display_name.lower())


def format_install_table(
    tool_keys: list[str],
    target_platform: str | None = None,
) -> str:
    """Format a human-readable install table for the given tools."""
    os_name = target_platform or _detect_platform()
    lines = [f"Install commands for platform: {os_name}\n"]
    for key in tool_keys:
        info = KNOWN_TOOLS.get(key)
        if info is None:
            lines.append(f"  {key:<25s}  (unknown tool)")
            continue
        cmd = get_install_command(key, os_name) or "(manual install required)"
        lines.append(f"  {info.display_name:<30s}  {cmd}")
        if info.notes:
            lines.append(f"    └─ {info.notes}")
    return "\n".join(lines)
