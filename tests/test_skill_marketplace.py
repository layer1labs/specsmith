# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the `specsmith skill` subcommand group and skills module.

The skill marketplace exposes a tiny built-in catalog (verifier, planner,
diff-reviewer, onboarding-coach, release-pilot) that can be searched,
listed, and installed into a project's ``.agents/skills/`` directory.
"""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from specsmith import skills
from specsmith.cli import main

# ---------------------------------------------------------------------------
# Module-level helpers (search / get / install)
# ---------------------------------------------------------------------------


def test_catalog_has_expected_slugs() -> None:
    slugs = {entry.slug for entry in skills.CATALOG}
    assert {"verifier", "planner", "diff-reviewer", "onboarding-coach", "release-pilot"} <= slugs


def test_search_empty_query_returns_full_catalog() -> None:
    matches = skills.search("")
    assert len(matches) == len(skills.CATALOG)


def test_search_matches_by_tag() -> None:
    matches = skills.search("release")
    assert any(m.slug == "release-pilot" for m in matches)


def test_search_is_case_insensitive() -> None:
    matches = skills.search("VERIFIER")
    assert any(m.slug == "verifier" for m in matches)


def test_get_returns_entry_for_known_slug() -> None:
    entry = skills.get("verifier")
    assert entry is not None
    assert entry.name.startswith("Verifier")


def test_get_returns_none_for_unknown_slug() -> None:
    assert skills.get("does-not-exist") is None


def test_install_writes_skill_md(tmp_path: Path) -> None:
    target = skills.install("verifier", tmp_path)
    assert target.is_file()
    assert target.parent == tmp_path / ".agents" / "skills"
    assert target.read_text(encoding="utf-8").startswith("# Verifier Skill")


def test_install_refuses_overwrite_without_force(tmp_path: Path) -> None:
    skills.install("verifier", tmp_path)
    try:
        skills.install("verifier", tmp_path)
    except FileExistsError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected FileExistsError")


def test_install_force_overwrites(tmp_path: Path) -> None:
    target = skills.install("verifier", tmp_path)
    target.write_text("STALE", encoding="utf-8")
    rewritten = skills.install("verifier", tmp_path, force=True)
    assert rewritten.read_text(encoding="utf-8").startswith("# Verifier Skill")


def test_install_unknown_slug_raises_keyerror(tmp_path: Path) -> None:
    try:
        skills.install("does-not-exist", tmp_path)
    except KeyError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected KeyError")


def test_installed_skills_lists_md_files(tmp_path: Path) -> None:
    skills.install("verifier", tmp_path)
    skills.install("planner", tmp_path)
    listed = skills.installed_skills(tmp_path)
    names = sorted(p.name for p in listed)
    assert names == ["planner.md", "verifier.md"]


# ---------------------------------------------------------------------------
# CLI: specsmith skill search / list / install
# ---------------------------------------------------------------------------


def test_cli_skill_search_text(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["skill", "search", "verifier"])
    assert res.exit_code == 0, res.output
    assert "verifier" in res.output


def test_cli_skill_search_json(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(main, ["skill", "search", "release", "--json"])
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert any(item["slug"] == "release-pilot" for item in payload)


def test_cli_skill_list_json_shows_catalog(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(
        main,
        ["skill", "list", "--json", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 0, res.output
    payload = json.loads(res.output)
    assert payload["installed"] == []
    slugs = {entry["slug"] for entry in payload["catalog"]}
    assert "verifier" in slugs


def test_cli_skill_install_then_list(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(
        main,
        ["skill", "install", "verifier", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 0, res.output
    assert (tmp_path / ".agents" / "skills" / "verifier.md").is_file()

    res2 = runner.invoke(
        main,
        ["skill", "list", "--json", "--project-dir", str(tmp_path)],
    )
    payload = json.loads(res2.output)
    assert "verifier.md" in payload["installed"]
    verifier_entry = next(e for e in payload["catalog"] if e["slug"] == "verifier")
    assert verifier_entry["installed"] is True


def test_cli_skill_install_unknown_exits_1(tmp_path: Path) -> None:
    runner = CliRunner()
    res = runner.invoke(
        main,
        ["skill", "install", "does-not-exist", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 1
    assert "Unknown skill" in res.output


def test_cli_skill_install_existing_exits_2(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(
        main,
        ["skill", "install", "verifier", "--project-dir", str(tmp_path)],
    )
    res = runner.invoke(
        main,
        ["skill", "install", "verifier", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 2
    assert "Already installed" in res.output


def test_cli_skill_install_force_overwrites(tmp_path: Path) -> None:
    runner = CliRunner()
    runner.invoke(
        main,
        ["skill", "install", "verifier", "--project-dir", str(tmp_path)],
    )
    target = tmp_path / ".agents" / "skills" / "verifier.md"
    target.write_text("STALE", encoding="utf-8")
    res = runner.invoke(
        main,
        ["skill", "install", "verifier", "--force", "--project-dir", str(tmp_path)],
    )
    assert res.exit_code == 0, res.output
    assert target.read_text(encoding="utf-8").startswith("# Verifier Skill")
