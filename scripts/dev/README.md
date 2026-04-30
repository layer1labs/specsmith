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
