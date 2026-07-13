# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Warp integration adapter (REQ-444).

Generates Warp-native artifacts so Warp's agent is governed by specsmith:

  * ``.warp/specsmith-mcp.json``                      — governance MCP server config
  * ``.warp/launch_configs/specsmith-governed.yaml``  — launch config for a governed session
  * ``.agents/skills/SKILL.md``                       — governance skill (shared with agent-skill)

``AGENTS.md`` is already the governance hub Warp reads as project Rules, so the
adapter does not duplicate it.

This adapter supersedes the pre-0.5.0 ``warp`` name that previously aliased to
the generic ``agent-skill`` adapter; the skill is still emitted here (by reusing
``AgentSkillAdapter``), so existing setups keep their ``.agents/skills/SKILL.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

from specsmith.config import ProjectConfig
from specsmith.integrations.agent_skill import AgentSkillAdapter
from specsmith.integrations.base import AgentAdapter


class WarpAdapter(AgentAdapter):
    """Generate Warp-native governance integration files."""

    @property
    def name(self) -> str:
        return "warp"

    @property
    def description(self) -> str:
        return "Warp native integration (MCP server config, launch config, governance skill)"

    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        created: list[Path] = []
        warp_dir = target / ".warp"
        warp_dir.mkdir(parents=True, exist_ok=True)

        # 1. MCP governance server config (shared builder with `mcp install-warp`).
        from specsmith.mcp_server import build_warp_mcp_config

        mcp_path = warp_dir / "specsmith-mcp.json"
        mcp_path.write_text(
            json.dumps(build_warp_mcp_config(), indent=2) + "\n",
            encoding="utf-8",
        )
        created.append(mcp_path)

        # 2. Launch config for a governed `specsmith run` session.
        launch_dir = warp_dir / "launch_configs"
        launch_dir.mkdir(parents=True, exist_ok=True)
        launch_path = launch_dir / "specsmith-governed.yaml"
        launch_path.write_text(self._render_launch_config(config, target), encoding="utf-8")
        created.append(launch_path)

        # 3. Governance skill (reuse the agent-skill adapter; .agents/skills/SKILL.md).
        created.extend(AgentSkillAdapter().generate(config, target))

        # 4. Third-party CLI agent toolbar setup guide.
        setup_path = warp_dir / "SETUP.md"
        setup_path.write_text(self._render_setup_guide(config), encoding="utf-8")
        created.append(setup_path)

        # Print the single most-important instruction so it appears immediately
        # after `specsmith integrate warp` completes.
        import sys

        print(
            "\n  ↳ Warp toolbar (one-time, per machine):\n"
            "    Settings → Agents → Third party CLI agents\n"
            "    Commands that enable the toolbar → add regex:\n"
            "      specsmith\\s+run|aider\n"
            "    (claude, codex, gemini, cursor — already natively supported)\n"
            "\n"
            "    Full setup guide: .warp/SETUP.md",
            file=sys.stdout,
            flush=True,
        )

        return created

    def _render_setup_guide(self, config: ProjectConfig) -> str:  # noqa: ARG002
        """Render the .warp/SETUP.md toolbar + notification setup guide."""
        return """\
# Warp — specsmith governance integration

## Third-party CLI agent toolbar (one-time setup per machine)

Warp natively supports the toolbar for: **claude**, **codex**, **gemini**, **cursor**.
For **specsmith** and **aider** (not yet natively supported), add the following
regex to Warp → Settings → Agents → Third party CLI agents → Commands that enable the toolbar:

```
specsmith\\s+run|aider
```

Once saved, the Warp toolbelt appears automatically when either `specsmith run` or
`aider` is active in any pane, providing Rich Input (Ctrl+G), attach code as context,
File Explorer, Tab Configs, and Remote Control.

## Desktop notifications

`specsmith run` emits OSC 9 desktop notifications when running inside Warp
(or any OSC-9-compatible terminal such as iTerm2 or Windows Terminal).
No extra setup is needed — Warp intercepts the escape sequence automatically.

Notification events:
- Session start: `specsmith run | <project> | governance active`

## MCP governance server

Add `.warp/specsmith-mcp.json` to Warp → Settings → Agents → MCP servers so
Warp's Oz agent can call governance tools natively (preflight, audit, checkpoint,
req_list, phase, trace_seal) without shell roundtrips.

Paste the contents of `.warp/specsmith-mcp.json` or run:
```bash
specsmith mcp install-warp
```

## Launch configuration

`.warp/launch_configs/specsmith-governed.yaml` opens a governed `specsmith run`
session. Copy it to your Warp launch configurations directory:
- macOS/Linux: `~/.warp/launch_configurations/`
- Windows: `%APPDATA%/warp/Warp/data/launch_configurations/`

## Supported REPLs and their Warp status

| REPL | Toolbar | How |
|---|---|---|
| `specsmith run` | Custom regex | Add `specsmith\\s+run` to toolbar regex |
| `aider` | Custom regex | Add `aider` to toolbar regex |
| `claude` | Native | Built into Warp — no setup needed |
| `codex` | Native | Built into Warp — no setup needed |
| `gemini` | Native | Built into Warp — no setup needed |
| `cursor` | Native | Built into Warp — no setup needed |

## Session protocol (all REPLs)

```bash
# Session start
specsmith kill-session  # idempotent; safe when no processes exist
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .   # output GOVERNANCE ANCHOR verbatim

# Before every code change
specsmith preflight "<describe the change>" --json

# Session end
specsmith save && specsmith kill-session
```
"""

    def _render_launch_config(self, config: ProjectConfig, target: Path) -> str:
        cwd = str(target).replace("\\", "/")
        return f"""\
# specsmith governed session — Warp launch configuration.
# Copy to your Warp launch configurations directory to use it:
#   macOS/Linux: ~/.warp/launch_configurations/
#   Windows:     %APPDATA%/warp/Warp/data/launch_configurations/
# The governance MCP server config lives in .warp/specsmith-mcp.json — add it
# under Warp Settings -> Agents -> MCP servers so Warp's agent is governed.
name: {config.name} — specsmith governed
windows:
  - tabs:
      - title: specsmith
        layout:
          cwd: "{cwd}"
          commands:
            - exec: specsmith run
"""
