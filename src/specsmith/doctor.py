# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Doctor — check if verification tools are installed locally."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolCheck:
    """Result of checking a single tool."""

    name: str
    category: str
    installed: bool
    version: str = ""


@dataclass
class DoctorReport:
    """Results from doctor checks."""

    checks: list[ToolCheck] = field(default_factory=list)

    @property
    def installed_count(self) -> int:
        return sum(1 for c in self.checks if c.installed)

    @property
    def missing_count(self) -> int:
        return sum(1 for c in self.checks if not c.installed)


# ---------------------------------------------------------------------------
# Extra tool lists for specific build systems / domains
# ---------------------------------------------------------------------------

#: Zephyr / west project: detected by presence of west.yml at repo root.
_ZEPHYR_TOOLS = [
    ("build", "west"),
    ("test", "west"),  # west twister
    ("build", "cmake"),
    ("build", "ninja"),
    ("build", "arm-none-eabi-gcc"),
    ("build", "dtc"),  # device-tree compiler
]

#: Yocto / KAS project: detected by kas.yml or west.yml-like manifest.
_YOCTO_TOOLS = [
    ("build", "kas"),
    ("build", "docker"),
    ("lint", "oelint-adv"),
]

#: KiCad PCB project.
_KICAD_TOOLS = [
    ("build", "kicad-cli"),
]

#: FPGA AMD/Xilinx Vivado.
_VIVADO_TOOLS = [
    ("build", "vivado"),
]

#: FPGA Intel/Altera Quartus.
_QUARTUS_TOOLS = [
    ("build", "quartus_sh"),
]

#: Mobile tools.
_FLUTTER_TOOLS = [
    ("build", "flutter"),
    ("build", "dart"),
]
_ANDROID_TOOLS = [
    ("build", "java"),
    ("debug", "adb"),
]


def _detect_extra_tools(root: Path) -> list[tuple[str, str]]:
    """Return (category, tool_exe) pairs for domain-specific tools.

    Inspects the project directory for build-system indicator files to
    determine which extra tool checks are relevant.  This supplements the
    tool registry entries (which come from scaffold.yml `type` field) with
    file-based heuristics so the doctor works even before `specsmith import`.
    """
    extras: list[tuple[str, str]] = []

    if (root / "west.yml").exists() or (root / "zephyr" / "CMakeLists.txt").exists():
        extras.extend(_ZEPHYR_TOOLS)
    if any((root / f).exists() for f in ("kas.yml", "kas.yaml")) or any(root.glob("kas/**/*.yml")):
        extras.extend(_YOCTO_TOOLS)
    if any(root.glob("*.kicad_pro")) or any(root.glob("**/*.kicad_pro")):
        extras.extend(_KICAD_TOOLS)
    if any(root.glob("*.xpr")) or any(root.glob("**/*.xpr")):
        extras.extend(_VIVADO_TOOLS)
    if any(root.glob("*.qpf")) or any(root.glob("**/*.qpf")):
        extras.extend(_QUARTUS_TOOLS)
    if (root / "pubspec.yaml").exists():
        extras.extend(_FLUTTER_TOOLS)
    if any(root.glob("**/gradle/wrapper/gradle-wrapper.properties")):
        extras.extend(_ANDROID_TOOLS)

    return extras


def run_doctor(root: Path) -> DoctorReport:
    """Check if verification tools for the project are installed.

    Combines three sources of tool checks:
    1. Registered tool sets from ``tools.py`` (driven by ``scaffold.yml`` type).
    2. File-based heuristics for embedded/hardware/mobile/cloud projects.
    3. Always-available base tools (git, python3) surfaced for every project.
    """
    from specsmith.config import ProjectConfig, _normalize_scaffold_raw
    from specsmith.paths import find_scaffold

    scaffold_path = find_scaffold(root)
    report = DoctorReport()

    # Always check the absolute basics
    for category, exe in [("vcs", "git"), ("runtime", "python3")]:
        report.checks.append(_check_tool(exe, category, root=root))

    # Scaffold-driven checks
    if scaffold_path and scaffold_path.exists():
        import yaml

        from specsmith.tools import get_tools

        try:
            with open(scaffold_path) as f:
                raw = yaml.safe_load(f)
            raw = _normalize_scaffold_raw(raw or {})
            config = ProjectConfig(**raw)
        except Exception:  # noqa: BLE001
            config = None

        if config is not None:
            tools = get_tools(config)
            seen: set[str] = set()
            for category, cmds in [
                ("lint", tools.lint),
                ("typecheck", tools.typecheck),
                ("test", tools.test),
                ("security", tools.security),
                ("build", tools.build),
                ("format", tools.format),
                ("compliance", tools.compliance),
            ]:
                for cmd in cmds:
                    tool_name = cmd.split()[0]
                    if tool_name not in seen:
                        seen.add(tool_name)
                        check = _check_tool(tool_name, category, root=root)
                        report.checks.append(check)

    # File-based heuristic extras (deduplication with existing checks)
    existing_names = {c.name for c in report.checks}
    for category, exe in _detect_extra_tools(root):
        if exe not in existing_names:
            existing_names.add(exe)
            report.checks.append(_check_tool(exe, category, root=root))

    return report


def _check_tool(name: str, category: str, root: Path | None = None) -> ToolCheck:
    """Check if a tool is available on PATH or in the project's .venv."""
    # Handle compound tool names (cargo clippy → cargo)
    exe = name.split(maxsplit=1)[0] if " " in name else name

    # Some tools are subcommands (dotnet format → dotnet)
    if exe in ("dotnet", "cargo", "go", "flutter", "nx", "turbo"):
        pass  # Use the base command
    elif exe in ("golangci-lint",):
        pass  # Already the executable name

    # 1. Check system PATH
    path = shutil.which(exe)

    # 2. Fall back to project's .venv (projects often don't install tools globally)
    if not path and root is not None:
        for venv_dir in (".venv", "venv", ".env"):
            # POSIX layout: .venv/bin/<exe>
            posix_path = root / venv_dir / "bin" / exe
            # Windows layout: .venv\Scripts\<exe>.exe
            win_path = root / venv_dir / "Scripts" / (exe + ".exe")
            win_path_no_ext = root / venv_dir / "Scripts" / exe
            for candidate in (posix_path, win_path, win_path_no_ext):
                if candidate.exists():
                    path = str(candidate)
                    break
            if path:
                break

    if not path:
        return ToolCheck(name=name, category=category, installed=False)

    # Try to get version
    version = ""
    try:
        result = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0][:80]
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return ToolCheck(name=name, category=category, installed=True, version=version)
