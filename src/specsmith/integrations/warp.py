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

        return created

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
