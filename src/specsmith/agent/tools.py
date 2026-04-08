# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""specsmith tool registry — maps specsmith CLI commands to agent-callable tools.

Inspired by ECC's principle: specsmith commands become native tools so the
agent can call them directly without shell invocation.

Tool categories:
  - Governance: audit, validate, diff, export, doctor
  - VCS: commit, push, sync, branch, pr
  - AEE: stress-test, epistemic-audit, belief-graph, trace
  - Scaffold: init, import, upgrade
  - Ledger: add, list, stats
  - Credits: record, summary
"""

from __future__ import annotations

import fnmatch
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

from specsmith.agent.core import Tool, ToolParam

# Env vars that prevent Rich from using the Windows Console API
# (LegacyWindowsTerm) when stdout is a captured pipe. Without these, Rich
# crashes with 'WriteFile failed' / handle errors on every command.
_SUBPROCESS_ENV: dict[str, str] = {
    **os.environ,
    "NO_COLOR": "1",         # Disables Rich colour / Windows console API path
    "FORCE_COLOR": "0",      # Belt-and-suspenders: also suppress colour
    "PYTHONIOENCODING": "utf-8",  # Ensure UTF-8 on pipes regardless of locale
}


def _run_specsmith(args: list[str], project_dir: str = ".") -> str:
    """Execute a specsmith command and return combined stdout+stderr."""
    cmd = [sys.executable, "-m", "specsmith"] + args + ["--project-dir", project_dir]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            env=_SUBPROCESS_ENV,
        )
        output = (result.stdout + result.stderr).strip()
        if result.returncode != 0:
            return f"[exit {result.returncode}]\n{output}"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "[TIMEOUT] Command exceeded 120s"
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def build_tool_registry(project_dir: str = ".") -> list[Tool]:
    """Build the full specsmith tool registry for the agentic client.

    Returns a list of Tool objects that the LLM can call.
    Each tool maps to one or more specsmith CLI commands.
    """
    pd = project_dir

    tools = [
        # ----------------------------------------------------------------
        # Governance tools
        # ----------------------------------------------------------------
        Tool(
            name="audit",
            description=(
                "Run specsmith audit: governance health checks (file existence, "
                "REQ↔TEST coverage, ledger health, governance size). "
                "Use --fix to auto-repair simple issues."
            ),
            params=[
                ToolParam("fix", "If 'true', attempt to auto-fix issues", required=False),
            ],
            handler=lambda fix="false": _run_specsmith(
                ["audit"] + (["--fix"] if fix == "true" else []), pd
            ),
            epistemic_claims=["Governance files are present and consistent"],
            uncertainty_bounds="Cannot verify runtime behavior or test correctness",
        ),
        Tool(
            name="validate",
            description=(
                "Run specsmith validate: check governance file consistency "
                "(req ↔ test ↔ arch), detect H11 blocking loops, check AGENTS.md refs."
            ),
            params=[],
            handler=lambda: _run_specsmith(["validate"], pd),
            epistemic_claims=["Requirements and tests are consistently linked"],
            uncertainty_bounds="Does not verify semantic correctness of requirements",
        ),
        Tool(
            name="epistemic_audit",
            description=(
                "Run the full AEE epistemic audit pipeline: "
                "Frame → Disassemble → Stress-Test → Failure-Mode Graph → "
                "Certainty scoring → Recovery proposals. "
                "Use this for deep knowledge quality checks."
            ),
            params=[
                ToolParam(
                    "threshold",
                    "Certainty threshold 0.0-1.0 (default 0.7)",
                    required=False,
                ),
            ],
            handler=lambda threshold="0.7": _run_specsmith(
                ["epistemic-audit", "--threshold", threshold], pd
            ),
            epistemic_claims=["Belief artifacts are stress-tested and at equilibrium"],
            uncertainty_bounds=(
                "Heuristic analysis only. Logic Knot detection uses pattern matching, "
                "not formal logic. Cannot guarantee completeness."
            ),
        ),
        Tool(
            name="stress_test",
            description=(
                "Run AEE stress-tests against docs/REQUIREMENTS.md. "
                "Applies 8 adversarial challenge functions per requirement, "
                "detects Logic Knots, emits recovery proposals."
            ),
            params=[
                ToolParam("format", "Output format: text or mermaid", required=False),
            ],
            handler=lambda format="text": _run_specsmith(  # noqa: A002
                ["stress-test", "--format", format], pd
            ),
            epistemic_claims=["Requirements survive adversarial challenges"],
            uncertainty_bounds="Pattern-based, not formal proof",
        ),
        Tool(
            name="belief_graph",
            description=(
                "Render the belief artifact dependency graph. Shows requirements "
                "as BeliefArtifacts with confidence scores, failure counts, "
                "and inferential links."
            ),
            params=[
                ToolParam("format", "text or mermaid", required=False),
                ToolParam("component", "Filter by component code (e.g. CLI, AEE)", required=False),
            ],
            handler=lambda format="text", component="": _run_specsmith(  # noqa: A002
                ["belief-graph", "--format", format]
                + (["--component", component] if component else []),
                pd,
            ),
        ),
        Tool(
            name="diff",
            description="Compare governance files against spec templates. Shows what has drifted.",
            params=[],
            handler=lambda: _run_specsmith(["diff"], pd),
        ),
        Tool(
            name="export",
            description=(
                "Generate a compliance and coverage report with REQ↔TEST matrix, "
                "audit summary, and governance inventory."
            ),
            params=[],
            handler=lambda: _run_specsmith(["export"], pd),
        ),
        Tool(
            name="doctor",
            description="Check if verification tools (ruff, mypy, pytest, etc.) are installed.",
            params=[],
            handler=lambda: _run_specsmith(["doctor"], pd),
        ),
        # ----------------------------------------------------------------
        # VCS tools
        # ----------------------------------------------------------------
        Tool(
            name="commit",
            description=(
                "Stage, audit, and commit with a governance-aware commit message. "
                "Checks LEDGER.md is updated and runs audit before committing."
            ),
            params=[
                ToolParam("message", "Override commit message", required=False),
            ],
            handler=lambda message="": _run_specsmith(
                ["commit"] + (["-m", message] if message else []), pd
            ),
        ),
        Tool(
            name="push",
            description="Push current branch with safety checks (blocks direct-to-main).",
            params=[],
            handler=lambda: _run_specsmith(["push"], pd),
        ),
        Tool(
            name="sync",
            description="Pull latest changes and warn on governance file conflicts.",
            params=[],
            handler=lambda: _run_specsmith(["sync"], pd),
        ),
        Tool(
            name="create_pr",
            description=(
                "Create a PR with governance context (ledger summary, audit results). "
                "Targets the correct base branch per branching strategy."
            ),
            params=[
                ToolParam("title", "PR title", required=False),
                ToolParam("draft", "'true' to create as draft", required=False),
            ],
            handler=lambda title="", draft="false": _run_specsmith(
                ["pr"]
                + (["--title", title] if title else [])
                + (["--draft"] if draft == "true" else []),
                pd,
            ),
        ),
        Tool(
            name="create_branch",
            description="Create a branch following the project's branching strategy.",
            params=[
                ToolParam("name", "Branch name (e.g. feature/aee-integration)"),
            ],
            handler=lambda name: _run_specsmith(["branch", "create", name], pd),
        ),
        # ----------------------------------------------------------------
        # Ledger tools
        # ----------------------------------------------------------------
        Tool(
            name="ledger_add",
            description=(
                "Add a structured entry to LEDGER.md. Use this after completing "
                "any significant task to maintain session continuity."
            ),
            params=[
                ToolParam("description", "Entry description (what was done)"),
                ToolParam("entry_type", "task, feature, fix, refactor, docs", required=False),
                ToolParam("reqs", "Affected REQ IDs (comma-separated)", required=False),
            ],
            handler=lambda description, entry_type="task", reqs="": _run_specsmith(
                ["ledger", "add", "--type", entry_type, "--reqs", reqs, description], pd
            ),
        ),
        Tool(
            name="ledger_list",
            description="List recent ledger entries to understand session state.",
            params=[],
            handler=lambda: _run_specsmith(["ledger", "list"], pd),
        ),
        # ----------------------------------------------------------------
        # Trace vault tools
        # ----------------------------------------------------------------
        Tool(
            name="trace_seal",
            description=(
                "Seal a decision, milestone, or audit gate to the cryptographic "
                "trace vault. Creates a tamper-evident SealRecord."
            ),
            params=[
                ToolParam(
                    "seal_type",
                    "Type of seal",
                    enum=["decision", "milestone", "audit-gate", "stress-test", "epistemic"],
                ),
                ToolParam("description", "What is being sealed"),
                ToolParam("artifacts", "Comma-separated artifact IDs", required=False),
            ],
            handler=lambda seal_type, description, artifacts="": _run_specsmith(
                ["trace", "seal", seal_type, description]
                + (["--artifacts", artifacts] if artifacts else []),
                pd,
            ),
        ),
        Tool(
            name="trace_verify",
            description="Verify cryptographic integrity of the trace vault chain.",
            params=[],
            handler=lambda: _run_specsmith(["trace", "verify"], pd),
        ),
        # ----------------------------------------------------------------
        # Requirements tools
        # ----------------------------------------------------------------
        Tool(
            name="req_list",
            description="List all requirements with status and coverage.",
            params=[],
            handler=lambda: _run_specsmith(["req", "list"], pd),
        ),
        Tool(
            name="req_gaps",
            description="List requirements that have no test coverage.",
            params=[],
            handler=lambda: _run_specsmith(["req", "gaps"], pd),
        ),
        Tool(
            name="req_trace",
            description="Show REQ→TEST traceability matrix.",
            params=[],
            handler=lambda: _run_specsmith(["req", "trace"], pd),
        ),
        # ----------------------------------------------------------------
        # Session tools
        # ----------------------------------------------------------------
        Tool(
            name="session_end",
            description=(
                "Run the session-end checklist: unpushed commits, open TODOs, "
                "dirty files, credit summary, and AEE epistemic status."
            ),
            params=[],
            handler=lambda: _run_specsmith(["session-end"], pd),
        ),
        # ----------------------------------------------------------------
        # Read file tool (essential for context loading)
        # ----------------------------------------------------------------
        Tool(
            name="read_file",
            description=(
                "Read the contents of a file in the project. Use for loading "
                "LEDGER.md, REQUIREMENTS.md, AGENTS.md, or any governance file "
                "to understand current project state."
            ),
            params=[
                ToolParam("path", "File path relative to project root"),
                ToolParam("lines", "Optional line range e.g. '1-100'", required=False),
            ],
            handler=lambda path, lines="": _read_file_handler(pd, path, lines),
        ),
        # ----------------------------------------------------------------
        # File system write tools
        # ----------------------------------------------------------------
        Tool(
            name="write_file",
            description=(
                "Write content to a file (creates or overwrites). "
                "Use for editing source code, docs, config files, etc. "
                "Path is relative to project root."
            ),
            params=[
                ToolParam("path", "File path relative to project root"),
                ToolParam("content", "Full content to write to the file"),
            ],
            handler=lambda path, content: _write_file_handler(pd, path, content),
        ),
        Tool(
            name="list_dir",
            description=(
                "List files and directories. Shows names, sizes, and types. "
                "Use to explore project structure before reading files."
            ),
            params=[
                ToolParam(
                    "path",
                    "Directory path relative to project root (default: root)",
                    required=False,
                ),
                ToolParam(
                    "pattern",
                    "Glob pattern to filter (e.g. '*.py', '*.md')",
                    required=False,
                ),
            ],
            handler=lambda path=".", pattern="": _list_dir_handler(pd, path, pattern),
        ),
        Tool(
            name="grep_files",
            description=(
                "Search for a regex pattern across files in the project. "
                "Returns matching lines with file:line references. "
                "Essential for finding where things are defined or used."
            ),
            params=[
                ToolParam("pattern", "Regex pattern to search for"),
                ToolParam(
                    "path",
                    "Directory or file to search (relative to root, default: root)",
                    required=False,
                ),
                ToolParam(
                    "glob",
                    "File glob filter e.g. '*.py' (default: all text files)",
                    required=False,
                ),
                ToolParam(
                    "ignore_case",
                    "'true' for case-insensitive search",
                    required=False,
                ),
            ],
            handler=lambda pattern, path=".", glob="", ignore_case="false": _grep_handler(
                pd, pattern, path, glob, ignore_case
            ),
        ),
        # ----------------------------------------------------------------
        # Shell execution — the most powerful tool
        # ----------------------------------------------------------------
        Tool(
            name="run_command",
            description=(
                "Execute a shell command in the project directory and return stdout+stderr. "
                "Use for: running tests (pytest), linting (ruff), building, git operations, "
                "installing packages, checking file contents with CLI tools, anything. "
                "Cross-platform: automatically uses PowerShell on Windows, bash on Linux/macOS. "
                "Commands run with a 120-second timeout."
            ),
            params=[
                ToolParam("command", "The shell command to execute"),
                ToolParam(
                    "working_dir",
                    "Working directory relative to project root (default: root)",
                    required=False,
                ),
                ToolParam(
                    "timeout",
                    "Timeout in seconds (default 120, max 300)",
                    required=False,
                ),
            ],
            handler=lambda command, working_dir=".", timeout="120": _run_command_handler(
                pd, command, working_dir, timeout
            ),
        ),
    ]

    return tools


def _read_file_handler(project_dir: str, path: str, lines: str = "") -> str:
    """Read a file from the project directory."""
    root = Path(project_dir).resolve()
    target = (root / path).resolve()

    # Safety: must be within project dir
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{path}' is outside the project directory"

    if not target.exists():
        return f"[NOT FOUND] {path}"

    try:
        content = target.read_text(encoding="utf-8")
        if lines:
            parts = lines.split("-")
            start = int(parts[0]) - 1 if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else None
            content_lines = content.splitlines()
            content = "\n".join(content_lines[start:end])
        if len(content) > 8000:
            content = content[:8000] + "\n...(truncated at 8000 chars, file has more)"
        return content
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def _write_file_handler(project_dir: str, path: str, content: str) -> str:
    """Write content to a file within the project directory."""
    root = Path(project_dir).resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{path}' is outside the project directory"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        size = len(content.encode("utf-8"))
        lines = content.count("\n") + 1
        return f"Written: {path} ({lines} lines, {size} bytes)"
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def _list_dir_handler(project_dir: str, path: str = ".", pattern: str = "") -> str:
    """List directory contents within the project."""
    root = Path(project_dir).resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{path}' is outside the project directory"
    if not target.exists():
        return f"[NOT FOUND] {path}"
    if not target.is_dir():
        return f"[NOT A DIR] {path}"
    try:
        entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        lines = []
        for entry in entries:
            if pattern and not fnmatch.fnmatch(entry.name, pattern):
                continue
            if entry.is_dir():
                lines.append(f"  {'DIR':>6}  {entry.name}/")
            else:
                size = entry.stat().st_size
                size_str = f"{size:,}" if size < 1_000_000 else f"{size // 1024:,}K"
                lines.append(f"  {size_str:>6}  {entry.name}")
        header = f"{path}/" if not path.endswith("/") else path
        return f"{header}\n" + "\n".join(lines) if lines else f"{header} (empty)"
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def _grep_handler(
    project_dir: str,
    pattern: str,
    path: str = ".",
    glob: str = "",
    ignore_case: str = "false",
) -> str:
    """Search for a regex pattern in files within the project."""
    root = Path(project_dir).resolve()
    target = (root / path).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return f"[ERROR] Path '{path}' is outside the project directory"

    flags = re.IGNORECASE if ignore_case.lower() == "true" else 0
    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        return f"[ERROR] Invalid regex: {e}"

    _TEXT_EXTENSIONS = {
        ".py",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".toml",
        ".json",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".sh",
        ".ps1",
        ".cmd",
        ".bat",
        ".rs",
        ".go",
        ".c",
        ".cpp",
        ".h",
        ".java",
        ".rb",
        ".php",
        ".tf",
        ".ini",
        ".cfg",
        ".conf",
    }
    _SKIP_DIRS = {".git", "__pycache__", ".venv", "node_modules", ".mypy_cache", "dist", "build"}

    results: list[str] = []
    files_searched = 0

    def search_file(fp: Path) -> None:
        nonlocal files_searched
        if glob and not fnmatch.fnmatch(fp.name, glob):
            return
        if not glob and fp.suffix.lower() not in _TEXT_EXTENSIONS:
            return
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
            files_searched += 1
            rel = fp.relative_to(root)
            for i, line in enumerate(text.splitlines(), 1):
                if compiled.search(line):
                    results.append(f"{rel}:{i}: {line.rstrip()}")
                    if len(results) >= 200:
                        return
        except Exception:  # noqa: BLE001
            pass

    if target.is_file():
        search_file(target)
    else:
        for dirpath, dirnames, filenames in os.walk(target):
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for fname in sorted(filenames):
                search_file(Path(dirpath) / fname)
                if len(results) >= 200:
                    break
            if len(results) >= 200:
                break

    if not results:
        return f"No matches for '{pattern}' in {files_searched} file(s) searched."
    summary = f"{len(results)} match(es) across {files_searched} file(s):"
    if len(results) >= 200:
        summary += " (truncated at 200)"
    return summary + "\n" + "\n".join(results)


def _run_command_handler(
    project_dir: str,
    command: str,
    working_dir: str = ".",
    timeout: str = "120",
) -> str:
    """Execute a shell command and return combined stdout+stderr."""
    root = Path(project_dir).resolve()
    cwd = (root / working_dir).resolve()
    try:
        cwd.relative_to(root)
    except ValueError:
        return f"[ERROR] working_dir '{working_dir}' is outside the project directory"

    try:
        timeout_secs = min(int(timeout), 300)
    except (ValueError, TypeError):
        timeout_secs = 120

    # Choose shell based on platform
    is_windows = platform.system() == "Windows"
    if is_windows:
        shell_cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", command]
    else:
        shell_cmd = ["bash", "-c", command]

    try:
        result = subprocess.run(
            shell_cmd,
            capture_output=True,
            text=True,
            cwd=str(cwd),
            timeout=timeout_secs,
        )
        output = (result.stdout + result.stderr).strip()
        exit_info = f"[exit {result.returncode}]" if result.returncode != 0 else "[exit 0]"
        if len(output) > 12000:
            output = output[:12000] + f"\n...(truncated, {len(output)} total chars)"
        return f"{exit_info}\n{output}" if output else exit_info
    except subprocess.TimeoutExpired:
        return f"[TIMEOUT] Command exceeded {timeout_secs}s"
    except FileNotFoundError:
        # Shell not found (e.g. bash on Windows) — fall back
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=str(cwd),
                timeout=timeout_secs,
                shell=True,  # noqa: S602
            )
            output = (result.stdout + result.stderr).strip()
            rc = result.returncode
            return f"[exit {rc}]\n{output}" if output else f"[exit {rc}]"
        except Exception as e2:  # noqa: BLE001
            return f"[ERROR] {e2}"
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {e}"


def get_tool_by_name(tools: list[Tool], name: str) -> Tool | None:
    return next((t for t in tools if t.name == name), None)
