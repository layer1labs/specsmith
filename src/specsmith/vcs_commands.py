# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""VCS commands — governance-aware git operations."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitResult:
    """Result of a git operation."""

    success: bool
    message: str
    output: str = ""


def _run_git(root: Path, args: list[str], *, timeout: int = 30) -> GitResult:
    """Run a git command and return result."""
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return GitResult(
            success=result.returncode == 0,
            message=result.stdout.strip() or result.stderr.strip(),
            output=result.stdout.strip(),
        )
    except subprocess.TimeoutExpired:
        return GitResult(success=False, message=f"git {args[0]} timed out after {timeout}s")
    except FileNotFoundError:
        return GitResult(success=False, message="git not found on PATH")


def get_current_branch(root: Path) -> str:
    """Get the current git branch name."""
    result = _run_git(root, ["branch", "--show-current"])
    return result.output if result.success else ""


def has_uncommitted_changes(root: Path) -> bool:
    """Check if there are uncommitted changes."""
    result = _run_git(root, ["status", "--porcelain"])
    return bool(result.output.strip()) if result.success else False


def has_unpushed_commits(root: Path) -> bool:
    """Check if there are unpushed commits on current branch."""
    branch = get_current_branch(root)
    if not branch:
        return False
    result = _run_git(root, ["log", f"origin/{branch}..HEAD", "--oneline"])
    return bool(result.output.strip()) if result.success else False


def is_ledger_modified_since_last_commit(root: Path) -> bool:
    """Check if LEDGER.md has been modified since the last commit."""
    result = _run_git(root, ["diff", "--name-only", "HEAD"])
    if result.success and "LEDGER.md" in result.output:
        return True
    # Also check staged
    result = _run_git(root, ["diff", "--name-only", "--cached"])
    if result.success and "LEDGER.md" in result.output:
        return True
    # Also check untracked
    result = _run_git(root, ["status", "--porcelain"])
    return bool(result.success and "LEDGER.md" in result.output)


def generate_commit_message(root: Path) -> str:
    """Generate commit message from the last ledger entry."""
    ledger_path = root / "LEDGER.md"
    if not ledger_path.exists():
        return "chore: update project files"

    content = ledger_path.read_text(encoding="utf-8")
    # Find the last ## heading
    lines = content.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].startswith("## "):
            heading = lines[i][3:].strip()
            # Clean up: remove date prefix if present
            if " — " in heading:
                heading = heading.split(" — ", 1)[1]
            elif " - " in heading:
                heading = heading.split(" - ", 1)[1]
            return heading[:72]  # Git convention: 72 char limit

    return "chore: update project files"


def run_commit(
    root: Path,
    *,
    message: str = "",
    auto_push: bool = False,
    co_author: str = "",
) -> GitResult:
    """Stage all changes and commit with governance-aware message."""
    if not message:
        message = generate_commit_message(root)

    if co_author:
        message += f"\n\nCo-Authored-By: {co_author}"

    # Stage all
    stage = _run_git(root, ["add", "-A"])
    if not stage.success:
        return stage

    # Commit
    result = _run_git(root, ["commit", "-m", message])
    if not result.success:
        return result

    if auto_push:
        push_result = run_push(root)
        if not push_result.success:
            return GitResult(
                success=True,
                message=f"Committed but push failed: {push_result.message}",
                output=result.output,
            )
        return GitResult(
            success=True,
            message=f"Committed and pushed: {message.splitlines()[0]}",
            output=result.output,
        )

    return result


def run_push(root: Path, *, force: bool = False) -> GitResult:
    """Push current branch with safety checks."""
    import yaml

    branch = get_current_branch(root)
    if not branch:
        return GitResult(success=False, message="Not on any branch")

    # Safety: check branching strategy
    scaffold_path = root / "scaffold.yml"
    if scaffold_path.exists() and not force:
        with open(scaffold_path) as f:
            raw = yaml.safe_load(f) or {}
        strategy = raw.get("branching_strategy", "gitflow")
        main_branch = raw.get("default_branch", "main")

        if strategy == "gitflow" and branch == main_branch:
            return GitResult(
                success=False,
                message=(
                    f"Refusing to push directly to {main_branch} "
                    f"(gitflow: merge via PR). Use --force to override."
                ),
            )

    args = ["push", "origin", branch]
    if force:
        args.insert(1, "--force-with-lease")

    return _run_git(root, args)


def run_sync(root: Path) -> GitResult:
    """Pull latest and check for governance conflicts."""
    branch = get_current_branch(root)
    if not branch:
        return GitResult(success=False, message="Not on any branch")

    result = _run_git(root, ["pull", "origin", branch])
    if not result.success:
        return result

    # Check if governance files were in the pull.
    # Use ORIG_HEAD (set by git pull) rather than HEAD~1 — works even on first pull.
    gov_files = ["AGENTS.md", "LEDGER.md", "scaffold.yml", "docs/governance/"]
    warnings: list[str] = []
    diff_result = _run_git(root, ["diff", "--name-only", "ORIG_HEAD..HEAD"])
    if diff_result.success:
        for gf in gov_files:
            if gf in diff_result.output:
                warnings.append(gf)

    if warnings:
        return GitResult(
            success=True,
            message=(
                f"Pulled successfully. WARNING: governance files changed upstream: "
                f"{', '.join(warnings)}"
            ),
            output=result.output,
        )
    return result


def create_branch(
    root: Path, name: str, *, strategy: str = "gitflow", main_branch: str = "main"
) -> GitResult:
    """Create a branch following the branching strategy."""
    develop_branch = "develop"

    # Determine base branch
    if strategy == "gitflow":
        if name.startswith("feature/"):
            base = develop_branch
        elif name.startswith("hotfix/") or name.startswith("release/"):
            base = main_branch
        else:
            # Auto-prefix as feature/
            name = f"feature/{name}"
            base = develop_branch
    elif strategy == "trunk-based":
        base = main_branch
    else:  # github-flow
        base = main_branch

    # Create branch
    result = _run_git(root, ["checkout", "-b", name, base])
    return result


def list_branches(root: Path) -> list[dict[str, str]]:
    """List branches with strategy annotations."""
    result = _run_git(root, ["branch", "-a", "--no-color"])
    if not result.success:
        return []

    branches: list[dict[str, str]] = []
    current = get_current_branch(root)

    for line in result.output.splitlines():
        name = line.strip().lstrip("* ").strip()
        if not name or "HEAD" in name:
            continue

        role = ""
        if name == "main":
            role = "production"
        elif name == "develop":
            role = "integration"
        elif name.startswith("feature/"):
            role = "feature"
        elif name.startswith("hotfix/"):
            role = "hotfix"
        elif name.startswith("release/"):
            role = "release"
        elif name.startswith("remotes/"):
            role = "remote"

        branches.append(
            {
                "name": name,
                "role": role,
                "current": "yes" if name == current else "",
            }
        )

    return branches


def create_pr(
    root: Path,
    *,
    title: str = "",
    draft: bool = False,
    governance_summary: str = "",
) -> GitResult:
    """Create a PR via platform CLI with governance context."""
    import yaml

    scaffold_path = root / "scaffold.yml"
    platform = "github"
    base_branch = "develop"

    if scaffold_path.exists():
        with open(scaffold_path) as f:
            raw = yaml.safe_load(f) or {}
        platform = raw.get("vcs_platform", "github")
        strategy = raw.get("branching_strategy", "gitflow")
        branch = get_current_branch(root)

        if strategy == "gitflow":
            if branch.startswith("hotfix/") or branch.startswith("release/"):
                base_branch = raw.get("default_branch", "main")
            else:
                base_branch = raw.get("develop_branch", "develop")
        else:
            base_branch = raw.get("default_branch", "main")

    if not title:
        title = generate_commit_message(root)

    body = governance_summary or ""

    if platform == "github":
        args = ["gh", "pr", "create", "--base", base_branch, "--title", title, "--body", body]
        if draft:
            args.append("--draft")
    elif platform == "gitlab":
        args = [
            "glab",
            "mr",
            "create",
            "--target-branch",
            base_branch,
            "--title",
            title,
            "--description",
            body,
        ]
        if draft:
            args.append("--draft")
    else:
        return GitResult(success=False, message=f"PR creation not supported for {platform}")

    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=30, cwd=str(root))
        return GitResult(
            success=result.returncode == 0,
            message=result.stdout.strip() or result.stderr.strip(),
            output=result.stdout.strip(),
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return GitResult(success=False, message=str(e))
