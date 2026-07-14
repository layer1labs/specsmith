# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Regression coverage for Git worktree branch resolution."""

from __future__ import annotations

from pathlib import Path

import specsmith.vcs_commands as vcs


def test_run_push_falls_back_to_symbolic_ref_for_supplied_worktree(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """TEST-477: an attached main branch must not be reported as detached."""
    calls: list[tuple[Path, list[str]]] = []

    def fake_run_git(root: Path, args: list[str], **_kwargs: object) -> vcs.GitResult:
        calls.append((root, args))
        if args == ["branch", "--show-current"]:
            return vcs.GitResult(success=True, message="", output="")
        if args == ["symbolic-ref", "--quiet", "--short", "HEAD"]:
            return vcs.GitResult(success=True, message="main", output="main")
        if args == ["push", "origin", "main"]:
            return vcs.GitResult(success=True, message="pushed", output="pushed")
        raise AssertionError(f"unexpected git command: {args}")

    monkeypatch.setattr(vcs, "_run_git", fake_run_git)
    result = vcs.run_push(tmp_path)

    assert result.success
    assert all(root == tmp_path for root, _args in calls)
    assert (tmp_path, ["push", "origin", "main"]) in calls


def test_run_push_reports_the_worktree_when_head_is_detached(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """TEST-477: diagnostics name the Git worktree that was inspected."""

    def fake_run_git(root: Path, args: list[str], **_kwargs: object) -> vcs.GitResult:
        if args in (
            ["branch", "--show-current"],
            ["symbolic-ref", "--quiet", "--short", "HEAD"],
        ):
            return vcs.GitResult(success=True, message="", output="")
        if args == ["rev-parse", "--show-toplevel"]:
            return vcs.GitResult(success=True, message=str(root), output=str(root))
        raise AssertionError(f"unexpected git command: {args}")

    monkeypatch.setattr(vcs, "_run_git", fake_run_git)
    result = vcs.run_push(tmp_path)

    assert not result.success
    assert str(tmp_path) in result.message
