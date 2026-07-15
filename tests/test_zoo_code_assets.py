from __future__ import annotations

import json
from pathlib import Path

from specsmith.commands.zoo_code import zoo_code_group
from specsmith.commands.zoo_code_assets import GLOBAL, MARKER, MCP, ZooCodeAssets


def test_lifecycle_commands_are_registered() -> None:
    assert {"setup", "doctor", "uninstall"} <= set(zoo_code_group.commands)


def test_setup_doctor_and_idempotence(tmp_path: Path) -> None:
    project = tmp_path / "project"
    global_roo = tmp_path / "global"
    manager = ZooCodeAssets(project, global_roo)
    first = manager.setup()
    assert first.ok
    assert manager.doctor().ok
    second = manager.setup()
    assert second.ok
    assert second.changed == []


def test_backup_and_preserve_existing(tmp_path: Path) -> None:
    target = tmp_path / "global" / "rules" / "10-specsmith-governance.md"
    target.parent.mkdir(parents=True)
    target.write_text("custom\n", encoding="utf-8")
    result = ZooCodeAssets(tmp_path / "project", tmp_path / "global").setup("global")
    assert result.ok
    assert target.with_name(target.name + ".before-specsmith-zoo-code").exists()
    target.write_text("custom again\n", encoding="utf-8")
    result = ZooCodeAssets(
        tmp_path / "project", tmp_path / "global", preserve_existing=True
    ).setup("global")
    assert not result.ok
    assert target.read_text(encoding="utf-8") == "custom again\n"


def test_mcp_merge_and_duplicate_cleanup(tmp_path: Path) -> None:
    project = tmp_path / "project"
    roo = project / ".roo"
    roo.mkdir(parents=True)
    (roo / "mcp.json").write_text(
        json.dumps({"mcpServers": {"other": {"command": "other"}}}),
        encoding="utf-8",
    )
    duplicate = roo / "rules" / "00-specsmith-source-of-truth.md"
    duplicate.parent.mkdir(parents=True)
    duplicate.write_text(
        GLOBAL["rules/00-specsmith-source-of-truth.md"], encoding="utf-8"
    )
    custom = roo / "rules" / "10-specsmith-governance.md"
    custom.write_text("project-specific\n", encoding="utf-8")
    result = ZooCodeAssets(project, tmp_path / "global").setup("project")
    data = json.loads((roo / "mcp.json").read_text(encoding="utf-8"))
    assert result.ok
    assert data["mcpServers"]["other"] == {"command": "other"}
    assert data["mcpServers"]["specsmith-governance"] == MCP
    assert not duplicate.exists()
    assert custom.exists()


def test_stale_cleanup_and_safe_uninstall(tmp_path: Path) -> None:
    project = tmp_path / "project"
    global_roo = tmp_path / "global"
    stale = global_roo / "rules" / "99-stale.md"
    stale.parent.mkdir(parents=True)
    stale.write_text(f"<!-- {MARKER} -->\n# stale\n", encoding="utf-8")
    (global_roo / ".specsmith-zoo-code-assets.json").write_text(
        json.dumps({"files": ["rules/99-stale.md"]}), encoding="utf-8"
    )
    manager = ZooCodeAssets(project, global_roo)
    result = manager.setup()
    assert result.ok
    assert not stale.exists()
    unmanaged = global_roo / "rules" / "custom.md"
    unmanaged.write_text("keep\n", encoding="utf-8")
    result = manager.uninstall()
    assert result.ok
    assert unmanaged.read_text(encoding="utf-8") == "keep\n"
    assert all(not (global_roo / rel).exists() for rel in GLOBAL)
