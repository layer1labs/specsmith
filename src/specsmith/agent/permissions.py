# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Least-privilege agent permissions (REG-012).

Every agent session operates with the minimum permissions required.
Sensitive operations (commit, push, create_pr, external network calls)
are individually gated and must be explicitly allowed.

Configuration in docs/SPECSMITH.yml::

    agent:
      permissions:
        allow: [run_shell, read_file, write_file, grep, list_files, git_status, git_diff]
        deny:  [open_url]
        # Omitting 'commit_files', 'push_changes', 'create_pr' = denied by default

Satisfies EU AI Act agent registration (agent capabilities explicitly declared),
NIST AI RMF least-privilege principle (REG-012).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

# ---------------------------------------------------------------------------
# Permission tiers — ordered from least to most privileged
# ---------------------------------------------------------------------------

#: Read-only tools — always permitted; never modify the filesystem or network.
READ_ONLY_TOOLS: frozenset[str] = frozenset(
    [
        "read_file",
        "list_files",
        "grep",
        "git_status",
        "git_diff",
    ]
)

#: Filesystem-modifying tools — require explicit allow.
WRITE_TOOLS: frozenset[str] = frozenset(
    [
        "write_file",
        "patch_file",
        "remember_project_fact",
    ]
)

#: Shell execution — may run arbitrary commands; gated by safety middleware.
SHELL_TOOLS: frozenset[str] = frozenset(["run_shell", "run_tests"])

#: High-privilege VCS operations — blocked by default; must be explicitly allowed.
HIGH_PRIVILEGE_TOOLS: frozenset[str] = frozenset(
    [
        "git_commit",  # REG-012: explicit declaration; not yet in AVAILABLE_TOOLS
        "git_push",  # REG-012: explicit declaration; not yet in AVAILABLE_TOOLS
        "git_create_pr",  # REG-012: explicit declaration; not yet in AVAILABLE_TOOLS
    ]
)

#: External network tools — blocked by default; must be explicitly allowed.
NETWORK_TOOLS: frozenset[str] = frozenset(["open_url", "search_docs"])

#: Default-allowed tools (least-privilege baseline).
DEFAULT_ALLOWED: frozenset[str] = READ_ONLY_TOOLS | WRITE_TOOLS | SHELL_TOOLS

#: Default-denied tools (require explicit opt-in).
DEFAULT_DENIED: frozenset[str] = HIGH_PRIVILEGE_TOOLS | NETWORK_TOOLS


# ---------------------------------------------------------------------------
# Permission profile
# ---------------------------------------------------------------------------


@dataclass
class AgentPermissions:
    """Active permission set for a single agent session (REG-012).

    Loaded from ``docs/SPECSMITH.yml`` ``agent.permissions`` section.
    Fallback is the least-privilege default (read + local write + shell;
    no network or VCS commit/push operations).
    """

    allow: frozenset[str] = field(default_factory=lambda: frozenset(DEFAULT_ALLOWED))
    deny: frozenset[str] = field(default_factory=lambda: frozenset(DEFAULT_DENIED))

    #: Human-readable label for this permission set (for logging / audit).
    label: str = "default-least-privilege"

    # Preset profiles -------------------------------------------------------

    #: Read-only — safest; no filesystem writes, no shell, no network.
    READ_ONLY: ClassVar[AgentPermissions]

    #: Standard (default) — local read/write/shell; no VCS commits or network.
    STANDARD: ClassVar[AgentPermissions]

    #: Extended — includes network access (open_url, search_docs).
    EXTENDED: ClassVar[AgentPermissions]

    #: Admin — all tools permitted (use only for supervised sessions).
    ADMIN: ClassVar[AgentPermissions]

    def is_allowed(self, tool_name: str) -> bool:
        """Return True if ``tool_name`` is permitted under this profile."""
        if tool_name in self.deny:
            return False
        # Explicitly allowed OR within default-allowed baseline; default deny
        return tool_name in self.allow

    def gate(self, tool_name: str) -> None:
        """Raise PermissionError if the tool is not allowed.

        REG-012: all tool invocations should call this before execution.
        The error message includes a remediation hint.
        """
        if not self.is_allowed(tool_name):
            raise PermissionError(
                f"Tool '{tool_name}' is not permitted under the '{self.label}' "
                f"agent permission profile.\n"
                f"To allow it, add to docs/SPECSMITH.yml:\n"
                f"  agent:\n"
                f"    permissions:\n"
                f"      allow: [{tool_name}]\n"
                f"Or switch to a broader profile (extended, admin)."
            )

    def check_and_log(
        self,
        tool_name: str,
        root: Path,
        *,
        log_denied: bool = True,
    ) -> tuple[bool, str]:
        """Check whether *tool_name* is allowed and optionally log denied attempts.

        Returns ``(allowed, message)`` where *message* is empty on success or
        contains the denial reason.  Denied attempts are appended to the project
        ledger (REG-012) so the audit trail captures every blocked tool call.

        Args:
            tool_name: The tool identifier to check.
            root: Project root directory (used to locate the ledger).
            log_denied: If ``True`` (default), write a ledger entry when the
                tool is denied so denials are auditable.
        """
        allowed = self.is_allowed(tool_name)
        if allowed:
            return True, ""

        reason = (
            f"Tool '{tool_name}' is not permitted under the "
            f"'{self.label}' agent permission profile.  "
            f"To allow it, add to docs/SPECSMITH.yml:\n"
            f"  agent:\n    permissions:\n      allow: [{tool_name}]"
        )

        if log_denied:
            # Best-effort — never crash the caller on ledger errors.
            try:
                from specsmith.ledger import add_entry  # lazy import avoids cycles

                add_entry(
                    root,
                    description=(
                        f"REG-012 DENIED: tool '{tool_name}' blocked by "
                        f"'{self.label}' permission profile"
                    ),
                    entry_type="permission-denied",
                    author="specsmith",
                    reqs="REG-012",
                    status="denied",
                    epistemic_status="high",
                )
            except Exception:  # noqa: BLE001
                pass

        return False, reason

    def summary(self) -> dict[str, object]:
        """Return a JSON-serialisable summary for audit logging."""
        return {
            "label": self.label,
            "allow": sorted(self.allow),
            "deny": sorted(self.deny),
        }


# ---------------------------------------------------------------------------
# Preset instances
# ---------------------------------------------------------------------------

AgentPermissions.READ_ONLY = AgentPermissions(
    allow=frozenset(READ_ONLY_TOOLS),
    deny=frozenset(WRITE_TOOLS | SHELL_TOOLS | HIGH_PRIVILEGE_TOOLS | NETWORK_TOOLS),
    label="read-only",
)

AgentPermissions.STANDARD = AgentPermissions(
    allow=frozenset(DEFAULT_ALLOWED),
    deny=frozenset(DEFAULT_DENIED),
    label="standard",
)

AgentPermissions.EXTENDED = AgentPermissions(
    allow=frozenset(DEFAULT_ALLOWED | NETWORK_TOOLS),
    deny=frozenset(HIGH_PRIVILEGE_TOOLS),
    label="extended",
)

AgentPermissions.ADMIN = AgentPermissions(
    allow=frozenset(
        READ_ONLY_TOOLS | WRITE_TOOLS | SHELL_TOOLS | HIGH_PRIVILEGE_TOOLS | NETWORK_TOOLS
    ),
    deny=frozenset(),
    label="admin",
)


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def load_permissions(project_dir: Path) -> AgentPermissions:
    """Load agent permissions from docs/SPECSMITH.yml (or legacy scaffold.yml).

    Falls back to STANDARD if no permissions section is configured.

    REG-012: capabilities must be explicitly declared in the project config.
    """
    from specsmith.paths import find_scaffold

    scaffold = find_scaffold(project_dir)
    if not scaffold or not scaffold.exists():
        return AgentPermissions.STANDARD

    try:
        import yaml

        raw = yaml.safe_load(scaffold.read_text(encoding="utf-8")) or {}
        agent_cfg = raw.get("agent", {})
        if not isinstance(agent_cfg, dict):
            return AgentPermissions.STANDARD

        perm_cfg = agent_cfg.get("permissions", {})
        if not isinstance(perm_cfg, dict):
            return AgentPermissions.STANDARD
        # No permissions section at all → least-privilege standard.
        if not perm_cfg:
            return AgentPermissions.STANDARD

        # Named preset shortcut: agent.permissions.preset = read_only|standard|extended|admin
        preset = perm_cfg.get("preset", "")
        presets = {
            "read_only": AgentPermissions.READ_ONLY,
            "read-only": AgentPermissions.READ_ONLY,
            "standard": AgentPermissions.STANDARD,
            "extended": AgentPermissions.EXTENDED,
            "admin": AgentPermissions.ADMIN,
        }
        if preset in presets:
            return presets[preset]

        # Custom allow/deny lists
        raw_allow = perm_cfg.get("allow")
        raw_deny = perm_cfg.get("deny")

        allow = frozenset(raw_allow) if isinstance(raw_allow, list) else frozenset(DEFAULT_ALLOWED)
        deny = frozenset(raw_deny) if isinstance(raw_deny, list) else frozenset(DEFAULT_DENIED)

        return AgentPermissions(allow=allow, deny=deny, label="custom")

    except Exception:  # noqa: BLE001
        return AgentPermissions.STANDARD
