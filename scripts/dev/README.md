# Developer scripts (Windows UTF-8 hygiene)
The default Windows console is configured for legacy code pages (cp437 /
cp1252), which mangles UTF-8 output from Python, pytest, ruff, and
similar tools. The pytest reporter becomes `ΓêÜ` instead of `✓` and
em-dashes in ledger / changelog tooling become `ΓÇö`.

These scripts work around that without forcing every contributor to edit
their PowerShell `$PROFILE`.

## Quick reference
| What you want | Run this |
|---|---|
| Run pytest with proper Unicode in PowerShell | `.\scripts\dev\test.ps1` |
| Run pytest with arguments forwarded | `.\scripts\dev\test.ps1 -k history -v` |
| Run ruff check + format check | `.\scripts\dev\lint.ps1` |
| Validate BOTH ESDB backends (SQLite + ChronoStore) | `.\scripts\dev\test-esdb-backends.ps1` |
| Run pytest from cmd.exe | `scripts\dev\test.cmd` |
| Just fix encoding in your current shell | `. .\scripts\dev\Set-Utf8Encoding.ps1` |

## What the scripts do
Each wrapper dot-sources `Set-Utf8Encoding.ps1` first, which:

* Switches the active code page to 65001 (`chcp 65001`).
* Sets `[Console]::OutputEncoding` and `[Console]::InputEncoding` to UTF-8.
* Sets `$OutputEncoding` to UTF-8 (covers PowerShell 5.1 too).
* Sets `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` so child Python
  processes emit UTF-8 regardless of the system locale.

After the encoding is fixed, the wrappers call `py -m pytest` (or
`py -m ruff`) with any arguments you passed.

## Two-tier ESDB harness (SQLite + ChronoStore)
`test-esdb-backends.ps1` (wrapping the cross-platform
`test_esdb_backends.py`) builds specsmith into a fresh, isolated virtual
environment and validates BOTH Epistemic State Database backends end-to-end,
mirroring the CI `esdb-backends` job locally before you push to git / PyPI:

* **Free tier** — the built-in SQLite backend (MIT, no license, no
  `chronomemory`). Always runs.
* **Commercial tier** — the ChronoStore backend (`chronomemory` + a valid
  Ed25519 license). Auto-skips when the `chronomemory` source or a license is
  unavailable, so the free tier stays the zero-config default for this OSS
  project.

It is non-destructive: every `esdb status` / `esdb migrate` dogfood runs against
an isolated **copy** of `.specsmith/`, never your tracked stores — important,
because `esdb status` auto-promotes SQLite records into ChronoStore in
non-interactive mode.

```pwsh
.\scripts\dev\test-esdb-backends.ps1             # both tiers, ESDB-focused set
.\scripts\dev\test-esdb-backends.ps1 --full      # whole pytest suite per tier
.\scripts\dev\test-esdb-backends.ps1 --free-only # SQLite tier only
```

Common flags (forwarded to the Python harness):

| Flag | Effect |
|---|---|
| `--full` | Run the entire pytest suite per tier (slow) instead of the ESDB set. |
| `--free-only` / `--chrono-only` | Run only one tier. |
| `--editable` | `pip install -e .` instead of building + installing a wheel. |
| `--chronomemory-src <path>` | Use a specific `chronomemory` source checkout. |
| `--keep-venv` | Keep the temp venv for inspection. |

The commercial tier sources `chronomemory` from (in priority order)
`--chronomemory-src`, `$env:SPECSMITH_CHRONOMEMORY_SRC`, `crates/chronomemory`,
or the sibling `../chronomemory`, and the license from `--license-key`,
`$env:SPECSMITH_ESDB_KEY`, or `~/.specsmith/esdb.key`. On macOS / Linux run
`python scripts/dev/test_esdb_backends.py` directly.

The harness builds its isolated venv from a specsmith-supported Python
(3.10-3.13, matching the CI test matrix), auto-selecting one when the default
`py` / `python` resolves to a newer, untested interpreter (e.g. 3.14). Override
with `--python <path>`.

## Permanent fix (recommended for daily Windows pwsh users)
Add this to your PowerShell `$PROFILE` so every new shell starts in
UTF-8 mode:

```pwsh
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::InputEncoding  = [System.Text.UTF8Encoding]::new()
$OutputEncoding           = [System.Text.UTF8Encoding]::new()
$env:PYTHONUTF8           = '1'
$env:PYTHONIOENCODING     = 'utf-8'
$null = & chcp.com 65001
```

Edit it with: `notepad $PROFILE` (creating the file if needed). After
saving, open a fresh shell and verify with:

```pwsh
chcp                                            # Active code page: 65001
[Console]::OutputEncoding.WebName               # utf-8
$env:PYTHONUTF8                                 # 1
```

Once the profile is in place you can run `py -m pytest` directly without
any wrapper.

## Why dot-source `Set-Utf8Encoding.ps1`?
PowerShell scripts run in a child scope by default, so changes to
`[Console]::OutputEncoding` etc. would only affect the script process and
not the caller. Dot-sourcing (`. .\Set-Utf8Encoding.ps1`) runs the script
in the current scope so the encoding settings persist for subsequent
commands you type into the same shell.

The wrapper scripts (`test.ps1`, `lint.ps1`) handle the dot-sourcing
internally so you don't need to remember it for routine use.
