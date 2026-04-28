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
