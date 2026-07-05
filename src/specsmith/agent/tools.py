import contextlib
import glob
import json
import os
import subprocess
import urllib.request
from dataclasses import dataclass
from dataclasses import field as _dc_field
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
    except subprocess.SubprocessError as e:
        return f"Subprocess error occurred: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Unexpected error occurred: {e}"


@validate_json_args
def read_file(path: str, cwd: str | None = None) -> str:
    """Read contents of a file."""
    p = normalize_path(path, cwd)
    if not p.is_file():
        return f"Error: File '{path}' does not exist."
    try:
        return p.read_text(encoding="utf-8")
    except OSError as e:
        return f"OS error reading file: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Unexpected error reading file: {e}"


@validate_json_args
def write_file(path: str, content: str, cwd: str | None = None) -> str:
    """Write content to a file (creates or overwrites)."""
    p = normalize_path(path, cwd)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"Successfully wrote to '{path}'."
    except OSError as e:
        return f"OS error writing file: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Unexpected error writing file: {e}"


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
            ["patch", "-p0", "-i", temp_diff_path],
            cwd=p.parent,
            capture_output=True,
            text=True,
        )
        os.unlink(temp_diff_path)

        if result.returncode == 0:
            return f"Successfully patched '{path}'."
        return f"Failed to patch '{path}': {result.stderr or result.stdout}"
    except OSError as e:
        return f"OS error patching file: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Unexpected error patching file: {e}"


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
    except OSError as e:
        return f"OS error listing files: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Unexpected error listing files: {e}"


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
    except urllib.error.URLError as e:
        return f"URL error fetching: {e}"
    except Exception as e:  # noqa: BLE001
        return f"Unexpected error fetching URL: {e}"


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
            description=(
                "Execute a shell command. Safety-checked; destructive commands are blocked."
            ),
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
        # ── Compiler / linter / formatter tools ─────────────────────────────
        ToolSpec(
            name="run_gcc",
            description=(
                "Compile or build with GCC / G++. Pass compiler flags verbatim via *args*."
                " Use *compiler* to select g++, gcc-12, etc."
            ),
            func=run_gcc,
            epistemic_claims=["invokes compiler process; may produce build artifacts"],
        ),
        ToolSpec(
            name="run_arm_gcc",
            description=(
                "Cross-compile for ARM bare-metal (arm-none-eabi-gcc / g++)."
                " Set *compiler* to 'arm-none-eabi-g++' for C++."
            ),
            func=run_arm_gcc,
            epistemic_claims=["invokes cross-compiler; produces .elf/.bin artifacts"],
        ),
        ToolSpec(
            name="run_aarch64_gcc",
            description=("Cross-compile for AArch64 Linux (aarch64-linux-gnu-gcc / g++)."),
            func=run_aarch64_gcc,
            epistemic_claims=["invokes cross-compiler; produces shared/static libraries"],
        ),
        ToolSpec(
            name="run_iar_compiler",
            description=(
                "Build an IAR Embedded Workbench project via IarBuild command-line."
                " Provide the .ewp *project_file* path."
            ),
            func=run_iar_compiler,
            epistemic_claims=["requires IAR Embedded Workbench installed; produces .out artifacts"],
        ),
        ToolSpec(
            name="run_intel_compiler",
            description=(
                "Compile with Intel oneAPI (icx/icpx) or classic (icc/icpc) compilers."
                " Use *compiler* to select the binary."
            ),
            func=run_intel_compiler,
            epistemic_claims=["requires Intel oneAPI or classic compiler installed"],
        ),
        ToolSpec(
            name="run_clang_format",
            description=(
                "Run clang-format on source files. Use *in_place=True* to apply changes,"
                " or leave False to print the diff only."
            ),
            func=run_clang_format,
            epistemic_claims=["modifies source files in-place when in_place=True"],
        ),
        ToolSpec(
            name="run_clang_tidy",
            description=(
                "Run clang-tidy static analysis on source files."
                " Pass *checks* to filter specific lint rules."
            ),
            func=run_clang_tidy,
            epistemic_claims=["read-only analysis unless --fix is passed"],
        ),
        ToolSpec(
            name="run_vsg",
            description=(
                "Run VSG (VHDL Style Guide) on .vhd/.vhdl files or directories."
                " Use *fix=True* to apply automatic style corrections in place."
            ),
            func=run_vsg,
            epistemic_claims=["modifies VHDL source files in-place when fix=True"],
        ),
        # ── Specsmith governance tool ────────────────────────────────────────
        ToolSpec(
            name="specsmith_run",
            description=(
                "Run any specsmith CLI command. Accepts slash-command form "
                "('/specsmith save'), single-word verb shortcuts ('save', 'push', "
                "'pull', 'load', 'sync', 'audit', 'status', 'watch', 'commit', "
                "'validate', 'doctor', 'run'), or the full 'specsmith <args>' form. "
                "Use this for all specsmith governance operations."
            ),
            func=specsmith_run,
            epistemic_claims=[
                "invokes specsmith CLI; may write to .specsmith/ and .chronomemory/",
                "save/push/commit modify git history",
                "load/pull may overwrite local governance state",
            ],
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


# ---------------------------------------------------------------------------
# Aliases / stubs for ROLE_TOOLS references
# (apply_diff, search_web, search_repo were referenced in ROLE_TOOLS before
#  the compiler tools were added; these bridge them to existing tools.)
# ---------------------------------------------------------------------------


@validate_json_args
def apply_diff(path: str, diff: str, cwd: str | None = None) -> str:
    """Apply a unified diff to a file (alias for patch_file)."""
    return patch_file(path, diff, cwd=cwd)


@validate_json_args
def search_web(query: str) -> str:
    """Search the web for a query using DuckDuckGo HTML interface."""
    encoded = query.replace(" ", "+")
    return open_url(f"https://html.duckduckgo.com/html/?q={encoded}")


@validate_json_args
def search_repo(query: str, path: str = ".", cwd: str | None = None) -> str:
    """Search for a string across repo files (alias for grep)."""
    return grep(query, path=path, cwd=cwd)


# ---------------------------------------------------------------------------
# Compiler / linter / formatter tools
# ---------------------------------------------------------------------------


def _run_compiler(
    executable: str,
    args: str,
    cwd: str | None = None,
    timeout: int = 120,
) -> str:
    """Shared helper: invoke a compiler/tool and return stdout+stderr."""
    return run_shell(f"{executable} {args}", cwd=cwd, timeout=timeout)


@validate_json_args
def run_gcc(
    args: str,
    cwd: str | None = None,
    compiler: str = "gcc",
    timeout: int = 120,
) -> str:
    """Compile or build with GCC (or g++ when compiler='g++').

    *args* is passed verbatim to the compiler, e.g. '-Wall -O2 main.c -o main'.
    Use *compiler* to select g++, gcc-12, etc.
    """
    return _run_compiler(compiler, args, cwd=cwd, timeout=timeout)


@validate_json_args
def run_arm_gcc(
    args: str,
    cwd: str | None = None,
    compiler: str = "arm-none-eabi-gcc",
    timeout: int = 120,
) -> str:
    """Cross-compile for ARM bare-metal using arm-none-eabi-gcc (or g++).

    Set *compiler* to 'arm-none-eabi-g++' for C++, or any installed
    arm cross-compiler such as 'arm-linux-gnueabihf-gcc'.
    """
    return _run_compiler(compiler, args, cwd=cwd, timeout=timeout)


@validate_json_args
def run_aarch64_gcc(
    args: str,
    cwd: str | None = None,
    compiler: str = "aarch64-linux-gnu-gcc",
    timeout: int = 120,
) -> str:
    """Cross-compile for AArch64 (64-bit ARM) using aarch64-linux-gnu-gcc.

    Set *compiler* to 'aarch64-linux-gnu-g++' for C++.
    """
    return _run_compiler(compiler, args, cwd=cwd, timeout=timeout)


@validate_json_args
def run_iar_compiler(
    project_file: str,
    args: str = "",
    cwd: str | None = None,
    executable: str = "IarBuild",
    timeout: int = 300,
) -> str:
    """Build an IAR Embedded Workbench project via the IarBuild command-line.

    *project_file* should be the path to a .ewp project file.
    *args* are additional flags passed to IarBuild (e.g. '-build Debug').
    Set *executable* to the full path to IarBuild.exe when it is not on PATH.
    """
    cmd = f'"{executable}" "{project_file}" {args}'.strip()
    return run_shell(cmd, cwd=cwd, timeout=timeout)


@validate_json_args
def run_intel_compiler(
    args: str,
    cwd: str | None = None,
    compiler: str = "icx",
    timeout: int = 120,
) -> str:
    """Compile with an Intel compiler (icx / icpx / icc / icpc).

    *compiler* selects the binary:
      - 'icx'  — Intel oneAPI C compiler (recommended)
      - 'icpx' — Intel oneAPI C++ compiler
      - 'icc'  — Classic Intel C compiler (deprecated)
      - 'icpc' — Classic Intel C++ compiler (deprecated)
    """
    return _run_compiler(compiler, args, cwd=cwd, timeout=timeout)


@validate_json_args
def run_clang_format(
    files: str,
    style: str = "file",
    in_place: bool = False,
    cwd: str | None = None,
) -> str:
    """Run clang-format on one or more source files.

    *files* is a space-separated list of file paths or a glob pattern.
    *style* maps to --style (e.g. 'file', 'LLVM', 'Google', 'Mozilla').
    Set *in_place* to True to apply formatting changes (-i flag).
    """
    flag = "-i" if in_place else ""
    cmd = f"clang-format --style={style} {flag} {files}".strip()
    return run_shell(cmd, cwd=cwd)


@validate_json_args
def run_clang_tidy(
    files: str,
    checks: str = "",
    fix: bool = False,
    compile_commands: str | None = None,
    cwd: str | None = None,
) -> str:
    """Run clang-tidy static analysis on source files.

    *files* is a space-separated list of source files.
    *checks* is a comma-separated clang-tidy check filter (e.g. 'modernize-*,readability-*').
    Set *fix* to True to apply automatic fixes (--fix flag).
    *compile_commands* is the path to compile_commands.json when not in cwd.
    """
    check_flag = f"--checks={checks}" if checks else ""
    fix_flag = "--fix" if fix else ""
    db_flag = f"-p {compile_commands}" if compile_commands else ""
    cmd = f"clang-tidy {check_flag} {fix_flag} {db_flag} {files}".strip()
    return run_shell(cmd, cwd=cwd)


@validate_json_args
def run_vsg(
    files: str = ".",
    rules: str | None = None,
    fix: bool = False,
    junit: str | None = None,
    cwd: str | None = None,
) -> str:
    """Run VSG (VHDL Style Guide) on one or more VHDL files or directories.

    *files* is a space-separated list of .vhd/.vhdl files or directories.
    *rules* is an optional path to a VSG rules YAML configuration file.
    Set *fix* to True to apply automatic style fixes in place.
    *junit* is an optional path to write a JUnit XML report.
    """
    rule_flag = f"--rules {rules}" if rules else ""
    fix_flag = "--fix" if fix else ""
    junit_flag = f"--junit {junit}" if junit else ""
    cmd = f"vsg {rule_flag} {fix_flag} {junit_flag} --filename {files}".strip()
    return run_shell(cmd, cwd=cwd)


# ---------------------------------------------------------------------------
# specsmith_run — slash-command and verb shortcut routing
# ---------------------------------------------------------------------------

#: Single-word verb shortcuts that expand to their full `specsmith <verb>` form.
_SPECSMITH_VERB_SHORTCUTS: frozenset[str] = frozenset(
    [
        "audit",
        "commit",
        "doctor",
        "load",
        "pull",
        "push",
        "run",
        "save",
        "status",
        "sync",
        "validate",
        "watch",
    ],
)


@validate_json_args
def specsmith_run(
    command: str,
    cwd: str | None = None,
    timeout: int = 120,
) -> str:
    """Run a specsmith CLI command with /specsmith prefix or verb shortcut support.

    Accepts three input forms:
      1. Slash prefix:  ``/specsmith save`` or ``/specsmith audit --strict``
      2. Verb shortcut: ``save``, ``push``, ``pull``, etc.
      3. Passthrough:   ``specsmith <anything>`` or any other full command

    All forms are normalised to ``specsmith <args>`` and executed as a
    subprocess so that agents can invoke governance commands uniformly.

    Examples::

        specsmith_run("/specsmith save")
        specsmith_run("save")
        specsmith_run("/specsmith audit --strict")
        specsmith_run("specsmith status")
    """
    cmd = command.strip()

    # Strip leading /specsmith prefix (slash-command form)
    if cmd.startswith("/specsmith"):
        cmd = cmd[len("/specsmith") :].strip()

    # Strip leading 'specsmith ' if caller passed the full binary name
    if cmd.startswith("specsmith "):
        cmd = cmd[len("specsmith ") :].strip()

    # Single-word verb shortcuts expand to their full command
    first_word = cmd.split()[0] if cmd else ""
    if first_word in _SPECSMITH_VERB_SHORTCUTS and not cmd.startswith("specsmith"):
        # Already stripped to just the verb + optional args — wrap with binary
        pass  # cmd is correct as-is; we prepend below

    full_command = f"specsmith {cmd}" if cmd else "specsmith --help"
    return run_shell(full_command, cwd=cwd, timeout=timeout)


# Expose available tools as a list for AG2 tool registration
AVAILABLE_TOOLS = [
    run_shell,
    read_file,
    write_file,
    patch_file,
    apply_diff,  # alias for patch_file (ROLE_TOOLS compat)
    list_files,
    grep,
    search_repo,  # alias for grep (ROLE_TOOLS compat)
    search_web,  # DuckDuckGo search (ROLE_TOOLS compat)
    git_diff,
    git_status,
    run_tests,
    open_url,
    search_docs,
    remember_project_fact,
    # Compiler / linter / formatter tools
    run_gcc,
    run_arm_gcc,
    run_aarch64_gcc,
    run_iar_compiler,
    run_intel_compiler,
    run_clang_format,
    run_clang_tidy,
    run_vsg,
    # Governance routing
    specsmith_run,
]
