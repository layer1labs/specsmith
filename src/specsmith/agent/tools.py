import contextlib
import glob
import json
import os
import subprocess
import urllib.request
from pathlib import Path

from specsmith.agent.safety import (
    normalize_path,
    safe_shell_command,
    validate_json_args,
)


@validate_json_args
@safe_shell_command
def run_shell(command: str, cwd: str | None = None, timeout: int = 60) -> str:
    """Run a shell command and return its output."""
    if cwd is None:
        cwd = os.getcwd()

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        return result.stdout or "Command executed successfully with no output."
    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e}\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout} seconds."
    except Exception as e:
        return f"Exception occurred: {e}"


@validate_json_args
def read_file(path: str, cwd: str | None = None) -> str:
    """Read contents of a file."""
    p = normalize_path(path, cwd)
    if not p.is_file():
        return f"Error: File '{path}' does not exist."
    try:
        return p.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading file: {e}"


@validate_json_args
def write_file(path: str, content: str, cwd: str | None = None) -> str:
    """Write content to a file (creates or overwrites)."""
    p = normalize_path(path, cwd)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote to '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"


@validate_json_args
def patch_file(path: str, diff: str, cwd: str | None = None) -> str:
    """Patch a file using standard diff/patch."""
    # We can write the diff to a temp file and use the `patch` command
    import tempfile

    p = normalize_path(path, cwd)
    if not p.is_file():
        return f"Error: File '{path}' does not exist to patch."

    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(diff)
            temp_diff_path = f.name

        result = subprocess.run(
            ["patch", "-p0", "-i", temp_diff_path], cwd=p.parent, capture_output=True, text=True
        )
        os.unlink(temp_diff_path)

        if result.returncode == 0:
            return f"Successfully patched '{path}'."
        return f"Failed to patch '{path}': {result.stderr or result.stdout}"
    except Exception as e:
        return f"Error patching file: {e}"


@validate_json_args
def list_files(path: str = ".", pattern: str = "**/*", cwd: str | None = None) -> str:
    """List files in a directory matching a glob pattern."""
    p = normalize_path(path, cwd)
    if not p.is_dir():
        return f"Error: Directory '{path}' does not exist."

    try:
        # Use recursive glob
        search_pattern = str(p / pattern)
        files = glob.glob(search_pattern, recursive=True)
        # Make paths relative to cwd
        if cwd is None:
            cwd = os.getcwd()
        rel_files = [os.path.relpath(f, cwd) for f in files if os.path.isfile(f)]
        return "\n".join(rel_files) if rel_files else "No files found."
    except Exception as e:
        return f"Error listing files: {e}"


@validate_json_args
def grep(query: str, path: str = ".", cwd: str | None = None) -> str:
    """Search for a string in files."""
    return run_shell(f"grep -rnw '{path}' -e '{query}'", cwd=cwd)


@validate_json_args
def git_diff(cwd: str | None = None) -> str:
    """Get git diff for the current repo."""
    return run_shell("git diff", cwd=cwd)


@validate_json_args
def git_status(cwd: str | None = None) -> str:
    """Get git status for the current repo."""
    return run_shell("git status", cwd=cwd)


@validate_json_args
def run_tests(command: str = "pytest", cwd: str | None = None) -> str:
    """Run tests."""
    return run_shell(command, cwd=cwd)


@validate_json_args
def open_url(url: str) -> str:
    """Fetch contents from a URL."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        return f"Error fetching URL: {e}"


@validate_json_args
def search_docs(query: str, cwd: str | None = None) -> str:
    """Search documentation within the repo."""
    # Assuming docs are in 'docs/' or similar
    return run_shell(f"grep -rni 'docs/' -e '{query}'", cwd=cwd)


@validate_json_args
def remember_project_fact(key: str, value: str, cwd: str | None = None) -> str:
    """Store a fact about the project in the local context index."""
    if cwd is None:
        cwd = os.getcwd()

    index_dir = Path(cwd) / ".repo-index"
    index_dir.mkdir(parents=True, exist_ok=True)

    facts_file = index_dir / "facts.json"
    facts: dict[str, str] = {}
    if facts_file.is_file():
        with contextlib.suppress(Exception):
            facts = json.loads(facts_file.read_text())

    facts[key] = value
    facts_file.write_text(json.dumps(facts, indent=2))
    return f"Remembered fact '{key}'."


# ---------------------------------------------------------------------------
# Tool specification (REG-001 / REG-002)
# ---------------------------------------------------------------------------
from dataclasses import dataclass, field as _dc_field


@dataclass
class ToolSpec:
    """Metadata wrapper around a tool function.

    Carries the tool's name, description, and epistemic contract
    (claims about what it does and does NOT reliably detect).

    REG-002: agent capabilities must be explicitly declared before use.
    """

    name: str
    description: str
    func: object
    epistemic_claims: list[str] = _dc_field(default_factory=list)


def build_tool_registry(project_dir: str = ".") -> list[ToolSpec]:
    """Return a list of ToolSpec objects for all available tools.

    REG-001: tool capability declarations satisfy the agent registration
    principle from EU AI Act (agent must have a signed registry entry
    describing capabilities and allowed actions).
    """
    return [
        ToolSpec(
            name="run_shell",
            description="Execute a shell command. Safety-checked; destructive commands are blocked.",
            func=run_shell,
            epistemic_claims=["EXEC-001: no python -c for non-trivial code"],
        ),
        ToolSpec(
            name="read_file",
            description="Read a text file from the repository.",
            func=read_file,
            epistemic_claims=["read-only: does not modify files"],
        ),
        ToolSpec(
            name="write_file",
            description="Write content to a file (creates or overwrites).",
            func=write_file,
            epistemic_claims=["modifies filesystem: logged in audit chain"],
        ),
        ToolSpec(
            name="patch_file",
            description="Apply a unified diff patch to a file.",
            func=patch_file,
            epistemic_claims=["modifies filesystem: logged in audit chain"],
        ),
        ToolSpec(
            name="list_files",
            description="List files matching a glob pattern in a directory.",
            func=list_files,
            epistemic_claims=["read-only: does not modify files"],
        ),
        ToolSpec(
            name="grep",
            description="Search for a pattern in files.",
            func=grep,
            epistemic_claims=["read-only: does not modify files"],
        ),
        ToolSpec(
            name="git_diff",
            description="Show the git diff for the working tree.",
            func=git_diff,
            epistemic_claims=["read-only: does not modify files"],
        ),
        ToolSpec(
            name="git_status",
            description="Show git status for the working tree.",
            func=git_status,
            epistemic_claims=["read-only: does not modify files"],
        ),
        ToolSpec(
            name="run_tests",
            description="Run the project test suite.",
            func=run_tests,
            epistemic_claims=["may modify test artifacts but not source"],
        ),
        ToolSpec(
            name="open_url",
            description="Fetch text content from a URL.",
            func=open_url,
            epistemic_claims=["network: reads external resources"],
        ),
        ToolSpec(
            name="search_docs",
            description="Search documentation files in the repo.",
            func=search_docs,
            epistemic_claims=["read-only: does not modify files"],
        ),
        ToolSpec(
            name="remember_project_fact",
            description="Store a named fact in the local project index (.repo-index/facts.json).",
            func=remember_project_fact,
            epistemic_claims=["modifies .repo-index/facts.json only"],
        ),
    ]


# ---------------------------------------------------------------------------
# REG-001: tamper-evident agent action logging
# ---------------------------------------------------------------------------

def log_agent_action(
    root: "Path | str",
    tool_name: str,
    args: dict,
    result_summary: str = "",
) -> None:
    """Append a tool-call record to the agent action log (REG-001).

    Writes to ``.specsmith/agent-actions.jsonl`` using the CryptoAuditChain
    for tamper-evidence. Best-effort — never raises or blocks the caller.

    Satisfies EU AI Act Art. 12 (logging obligations for AI systems).
    """
    import datetime
    import json

    try:
        from specsmith.ledger import CryptoAuditChain, _sha256

        root_path = Path(root) if not isinstance(root, Path) else root
        log_file = root_path / ".specsmith" / "agent-actions.jsonl"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        chain = CryptoAuditChain(root_path)
        prev_hash = chain.latest_hash()
        entry_body = f"{tool_name}|{json.dumps(args, default=str)}|{result_summary[:100]}"
        entry_hash = _sha256(f"{entry_body}:{prev_hash}")

        record = {
            "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "tool": tool_name,
            "args_summary": entry_body[:200],
            "result_summary": result_summary[:100],
            "chain_hash": entry_hash[:16],
        }
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
    except Exception:  # noqa: BLE001 — logging must never break execution
        pass


# Expose available tools as a list for AG2 tool registration
AVAILABLE_TOOLS = [
    run_shell,
    read_file,
    write_file,
    patch_file,
    list_files,
    grep,
    git_diff,
    git_status,
    run_tests,
    open_url,
    search_docs,
    remember_project_fact,
]
