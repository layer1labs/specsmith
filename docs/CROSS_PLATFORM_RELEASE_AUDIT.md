# Cross-platform release and bootstrap audit

This report records the release/bootstrap portability baseline for GitHub issue
#330. It covers supported desktop environments: Windows, Linux, and macOS.

## Enforcement

The CI `test` matrix runs the full suite on `ubuntu-latest`,
`windows-latest`, and `macos-latest` with Python 3.10 through 3.13. The
`wheel-smoke` matrix builds the candidate wheel on each OS, installs that exact
wheel into a fresh virtual environment, and runs the public CLI from a
workspace whose path contains spaces and Unicode.

The smoke flow deliberately uses the selected venv interpreter as
`python -m specsmith`; it never activates the environment and never assumes a
`bin/`, `Scripts/`, or console-script path. It verifies:

- package installation and `--version`;
- non-interactive project initialization;
- audit and strict validation;
- sync followed by the fixed-point `sync --check` pass; and
- Local-LLM Zoo Code asset generation and validation.

## Findings and resolution

| Area | Result |
| --- | --- |
| Interpreter and executable resolution | The wheel smoke helper has one platform-aware `venv_python()` function. Commands use argv arrays and `python -m specsmith`. |
| Shell independence | The smoke workflow uses no shell activation, POSIX utility, glob, or environment-assignment syntax. The release build no longer mutates `pyproject.toml` with `sed`. |
| Paths, Unicode, and spaces | The wheel smoke workspace is created with spaces and `ünicode` in its path; all paths pass through `pathlib` and subprocess argument arrays. |
| Text and JSON | Smoke configuration is written explicitly as UTF-8 with LF line endings. The Local-LLM asset uses canonical JSON serialization and atomic replacement. |
| Temporary files and Windows locking | Registry writes use unique same-directory temporary files plus `os.replace`; mutation operations hold a bounded portable lock-file protocol. Focused concurrency tests cover lock cleanup and no lost registrations. |
| Zoo Code integration | Specsmith generates Zoo's current settings-import schema rather than writing VS Code Secret Storage or legacy `cline_settings.json`. Windows, Linux, and macOS VS Code settings paths are tested. |
| Symlinks and file modes | Registry tests skip symlink equivalence when the platform disallows symlink creation. No public bootstrap or wheel-smoke step depends on executable bits or `chmod`. |
| Git status | Project behavior uses structured Git commands in its existing validators; the wheel smoke uses `--no-git` because it validates a generic scaffold, not a maintainer checkout. |

## Intentional boundaries

Publishing to PyPI, GitHub Releases, and Read the Docs remains a trusted,
Linux-hosted CI operation. That is a maintainer deployment boundary, not a
public desktop requirement. The produced universal wheel is independently
built and smoke-tested on all supported operating systems before release.

The Read the Docs deployment workflow may use Bash and `/tmp` because it is
explicitly an Ubuntu-hosted remote-deployment integration. Normal Specsmith
commands and the candidate-wheel smoke flow do not require Bash, WSL, Git Bash,
Docker, or a shell-specific venv activation step.

## Operator guidance

When a platform failure occurs, run the candidate workflow locally without
activating a venv:

```text
python -m build
python scripts/platform_smoke.py --wheel-dir dist
```

Use `--work-dir PATH` if the system temporary directory is locked or governed.
The script closes child processes and temporary files before cleanup, so a
persistent cleanup failure is reported instead of being silently ignored.
