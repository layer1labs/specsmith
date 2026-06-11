# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Execution profiles — command allow/block lists for the agentic tool runner.

Four built-in profiles control what the AI agent is permitted to do:

  safe      — Read-only inspection; no shell, no file writes.
  standard  — Default. specsmith + git + build tools; no sudo/rm-rf.
  open      — Almost all commands; only blocks catastrophic disk ops.
  admin     — No restrictions (use in trusted/sandbox environments only).

The active profile is stored in ``scaffold.yml`` as ``execution_profile``.
Custom overrides (``custom_allowed_commands``, ``custom_blocked_commands``,
``custom_blocked_tools``) are merged on top of the base profile at load time.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class ExecutionProfile:
    """Defines what the agent is allowed to do.

    Fields
    ------
    name
        Profile identifier (safe, standard, open, admin, or custom+overrides).
    description
        Human-readable summary of what this profile allows.
    allowed_tools
        Which agent tool names may be invoked.  Empty list = allow all.
    blocked_tools
        Tool names that are always blocked (override ``allowed_tools``).
    allowed_commands
        For the ``run_command`` tool: prefix-match whitelist.
        Empty = no command restriction (subject to ``blocked_*`` below).
    blocked_commands
        Prefix-match list that overrides ``allowed_commands``.
    blocked_patterns
        Regex patterns applied to the full command string — block on match.
    allow_shell_exec
        Whether ``run_command`` is callable at all.
    allow_file_write
        Whether ``write_file`` is callable at all.
    max_write_bytes
        Max bytes for a single ``write_file`` call; 0 = unlimited.
    """

    name: str
    description: str
    allowed_tools: list[str] = field(default_factory=list)
    blocked_tools: list[str] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)
    blocked_commands: list[str] = field(default_factory=list)
    blocked_patterns: list[str] = field(default_factory=list)
    allow_shell_exec: bool = True
    allow_file_write: bool = True
    max_write_bytes: int = 0  # 0 = unlimited


# ---------------------------------------------------------------------------
# Built-in profiles
# ---------------------------------------------------------------------------

_SAFE_ALLOWED_TOOLS = [
    "audit",
    "validate",
    "epistemic_audit",
    "stress_test",
    "belief_graph",
    "diff",
    "export",
    "doctor",
    "ledger_list",
    "req_list",
    "req_gaps",
    "req_trace",
    "trace_verify",
    "read_file",
    "list_dir",
    "grep_files",
]

_SAFE_BLOCKED_TOOLS = [
    "run_command",
    "write_file",
    "commit",
    "push",
    "sync",
    "create_pr",
    "create_branch",
    "ledger_add",
    "trace_seal",
    "session_end",
]

_STANDARD_ALLOWED_COMMANDS = [
    # specsmith itself
    "specsmith",
    # Python ecosystem
    "python",
    "python3",
    "pip",
    "pip3",
    "uv",
    "uvx",
    # Rust / Go / JS
    "cargo",
    "go",
    "npm",
    "yarn",
    "pnpm",
    "npx",
    "node",
    # Build systems
    "make",
    "cmake",
    "ninja",
    "meson",
    # Yocto / Embedded Linux
    "bitbake",
    "kas",
    "devtool",
    "oelint-adv",
    # VCS
    "git",
    # Linters & formatters
    "pytest",
    "mypy",
    "ruff",
    "eslint",
    "tsc",
    "prettier",
    "clang-tidy",
    "clang-format",
    "cppcheck",
    "golangci-lint",
    "dotnet",
    "flutter",
    "dart",
    # FPGA / HDL tools
    "vivado",
    "quartus_sh",
    "quartus",
    "diamondc",
    "radiantlsp",
    "ghdl",
    "iverilog",
    "vvp",
    "verilator",
    "vsg",
    "yosys",
    "nextpnr-ecp5",
    "nextpnr-ice40",
    "openFPGALoader",
    "symbiyosys",
    "sby",
    "gtkwave",
    "surfer",
    # Infra / container
    "terraform",
    "ansible",
    "docker",
    "docker-compose",
    "podman",
    # Filesystem read ops
    "cat",
    "ls",
    "dir",
    "find",
    "rg",
    "grep",
    "echo",
    "mkdir",
    "cp",
    "mv",
    # Misc
    "ruby",
    "gem",
    "bundle",
    "perl",
]

_STANDARD_BLOCKED_COMMANDS = [
    "sudo",
    "su ",
    "doas",
    "runas",
    "format ",
    "fdisk",
    "mkfs",
    "blkdiscard",
]

_STANDARD_BLOCKED_PATTERNS = [
    r"\brm\s+-rf\s+[/~]",  # rm -rf / or ~/
    r"\bsudo\b",  # sudo anything
    r"\bdd\s+if=.*of=/dev/(sd|nvme|hd)",  # disk wipe
    r"\|\s*(bash|sh|zsh|fish)\b",  # pipe to shell
    r"curl[^|]*\|\s*(bash|sh|zsh)\b",  # curl | bash
    r"wget[^|]*\|\s*(bash|sh|zsh)\b",  # wget | bash
]

PROFILES: dict[str, ExecutionProfile] = {
    # ── safe ────────────────────────────────────────────────────────────────
    "safe": ExecutionProfile(
        name="safe",
        description=(
            "Read-only mode. Inspection and analysis only — no shell commands, "
            "no file writes. The agent can read files, grep, list dirs, and "
            "call read-only specsmith commands (audit, validate, doctor)."
        ),
        allowed_tools=_SAFE_ALLOWED_TOOLS,
        blocked_tools=_SAFE_BLOCKED_TOOLS,
        allowed_commands=[],
        blocked_commands=[],
        blocked_patterns=[],
        allow_shell_exec=False,
        allow_file_write=False,
        max_write_bytes=0,
    ),
    # ── standard ────────────────────────────────────────────────────────────
    "standard": ExecutionProfile(
        name="standard",
        description=(
            "Standard mode (default). Allows specsmith tools, git, linters, "
            "build systems, and common dev tools. Blocks destructive shell ops "
            "(sudo, rm -rf, disk format) and curl|bash-style pipe installers."
        ),
        allowed_tools=[],  # empty = all tools allowed
        blocked_tools=[],
        allowed_commands=_STANDARD_ALLOWED_COMMANDS,
        blocked_commands=_STANDARD_BLOCKED_COMMANDS,
        blocked_patterns=_STANDARD_BLOCKED_PATTERNS,
        allow_shell_exec=True,
        allow_file_write=True,
        max_write_bytes=10_000_000,  # 10 MB
    ),
    # ── open ────────────────────────────────────────────────────────────────
    "open": ExecutionProfile(
        name="open",
        description=(
            "Open mode. Almost all shell commands allowed. Only blocks "
            "catastrophic physical disk operations (dd wipe, mkfs, blkdiscard). "
            "Use in trusted environments only."
        ),
        allowed_tools=[],
        blocked_tools=[],
        allowed_commands=[],  # empty = no prefix restriction
        blocked_commands=["format ", "fdisk", "mkfs", "blkdiscard"],
        blocked_patterns=[
            r"\bdd\s+if=.*of=/dev/(sd|nvme|hd)",
            r"\brm\s+-rf\s+/$",  # rm -rf / only — not subpaths
        ],
        allow_shell_exec=True,
        allow_file_write=True,
        max_write_bytes=100_000_000,  # 100 MB
    ),
    # ── admin ────────────────────────────────────────────────────────────────
    "admin": ExecutionProfile(
        name="admin",
        description=(
            "Admin mode — no restrictions whatsoever. Use only in fully "
            "sandboxed or isolated environments where you accept all consequences."
        ),
        allowed_tools=[],
        blocked_tools=[],
        allowed_commands=[],
        blocked_commands=[],
        blocked_patterns=[],
        allow_shell_exec=True,
        allow_file_write=True,
        max_write_bytes=0,
    ),
}

DEFAULT_PROFILE_NAME = "standard"


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------


def get_profile(name: str) -> ExecutionProfile:
    """Return the named profile, falling back to 'standard' if unknown."""
    return PROFILES.get(name, PROFILES[DEFAULT_PROFILE_NAME])


def load_from_scaffold(project_dir: str) -> ExecutionProfile:
    """Read execution settings from scaffold.yml and return merged profile.

    Reads ``execution_profile``, ``custom_allowed_commands``,
    ``custom_blocked_commands``, and ``custom_blocked_tools`` from the scaffold
    and merges any custom overrides on top of the base profile.

    Falls back to 'standard' if the file or the field is absent.
    """
    from pathlib import Path

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        return PROFILES[DEFAULT_PROFILE_NAME]

    scaffold = Path(project_dir) / "scaffold.yml"
    if not scaffold.exists():
        return PROFILES[DEFAULT_PROFILE_NAME]

    try:
        with open(scaffold, encoding="utf-8") as f:
            raw: dict = yaml.safe_load(f) or {}
    except Exception:  # noqa: BLE001
        return PROFILES[DEFAULT_PROFILE_NAME]

    profile_name = str(raw.get("execution_profile", DEFAULT_PROFILE_NAME))
    base = get_profile(profile_name)

    extra_allowed: list[str] = list(raw.get("custom_allowed_commands", []) or [])
    extra_blocked: list[str] = list(raw.get("custom_blocked_commands", []) or [])
    extra_blocked_tools: list[str] = list(raw.get("custom_blocked_tools", []) or [])

    if not (extra_allowed or extra_blocked or extra_blocked_tools):
        return base

    return replace(
        base,
        name=f"{base.name}+custom",
        allowed_commands=list(base.allowed_commands) + extra_allowed,
        blocked_commands=list(base.blocked_commands) + extra_blocked,
        blocked_tools=list(base.blocked_tools) + extra_blocked_tools,
    )


# ---------------------------------------------------------------------------
# Enforcement helpers (used by runner.py)
# ---------------------------------------------------------------------------


def check_tool_allowed(profile: ExecutionProfile, tool_name: str) -> tuple[bool, str]:
    """Return ``(allowed, reason)``.  If *allowed* is False, *reason* explains why."""
    if tool_name in profile.blocked_tools:
        return False, (f"Tool '{tool_name}' is blocked by profile '{profile.name}'.")
    if profile.allowed_tools and tool_name not in profile.allowed_tools:
        sample = ", ".join(profile.allowed_tools[:8])
        return False, (
            f"Tool '{tool_name}' is not in the allowed list for profile "
            f"'{profile.name}'. Allowed tools include: {sample}…"
        )
    return True, ""


def check_command_allowed(profile: ExecutionProfile, command: str) -> tuple[bool, str]:
    """Return ``(allowed, reason)`` for a shell command string."""
    if not profile.allow_shell_exec:
        return False, (
            f"Shell execution is disabled by profile '{profile.name}'. "
            "Switch to 'standard' or 'open' to allow run_command."
        )

    stripped = command.strip()

    # Blocked patterns take highest priority
    for pattern in profile.blocked_patterns:
        if re.search(pattern, stripped, re.IGNORECASE):
            return False, (
                f"Command blocked by profile '{profile.name}': matches blocked pattern '{pattern}'."
            )

    # Blocked command prefixes
    for blocked in profile.blocked_commands:
        if stripped.startswith(blocked):
            return False, (
                f"Command blocked by profile '{profile.name}': "
                f"starts with blocked prefix '{blocked!r}'."
            )

    # Allowed-commands whitelist (only enforced when non-empty)
    if profile.allowed_commands:
        cmd_exe = stripped.split()[0] if stripped else ""
        if not any(
            stripped.startswith(a) or cmd_exe == a.split()[0] for a in profile.allowed_commands
        ):
            return False, (
                f"Command executable '{cmd_exe}' is not in the allowed list for "
                f"profile '{profile.name}'. Switch to 'open' for arbitrary commands, "
                "or add it to custom_allowed_commands in scaffold.yml."
            )

    return True, ""


def check_write_allowed(profile: ExecutionProfile, content: str) -> tuple[bool, str]:
    """Return ``(allowed, reason)`` for a file write operation."""
    if not profile.allow_file_write:
        return False, (
            f"File writes are disabled by profile '{profile.name}'. "
            "Switch to 'standard' or higher to allow write_file."
        )
    if profile.max_write_bytes > 0:
        size = len(content.encode("utf-8"))
        if size > profile.max_write_bytes:
            mb = profile.max_write_bytes // 1_000_000
            return False, (
                f"Write size {size:,} bytes exceeds the {mb} MB limit set by "
                f"profile '{profile.name}'. Increase max_write_bytes or split the write."
            )
    return True, ""


def profile_summary(profile: ExecutionProfile) -> str:
    """Return a single human-readable paragraph describing the active profile."""
    lines = [f"Active execution profile: **{profile.name}**", profile.description]
    if profile.blocked_tools:
        lines.append(f"Blocked tools: {', '.join(profile.blocked_tools[:10])}")
    if not profile.allow_shell_exec:
        lines.append("Shell execution (run_command) is DISABLED.")
    if not profile.allow_file_write:
        lines.append("File writes (write_file) are DISABLED.")
    if profile.max_write_bytes:
        lines.append(f"Max write size: {profile.max_write_bytes // 1_000_000} MB.")
    return "\n".join(lines)
