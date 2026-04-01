# CLI Commands

## `specsmith init`

Scaffold a new governed project.

```bash
specsmith init                                    # Interactive
specsmith init --config scaffold.yml              # From config
specsmith init --config scaffold.yml --guided     # With architecture definition
specsmith init --config scaffold.yml --no-git     # Skip git init
specsmith init --output-dir /path/to/parent       # Custom output location
```

**Options:**

- `--config PATH` — Path to scaffold.yml (skips interactive prompts)
- `--output-dir PATH` — Parent directory for the new project (default: `.`)
- `--no-git` — Skip `git init`
- `--guided` — Run interactive architecture definition after scaffolding

## `specsmith import`

Import an existing project and generate governance overlay.

```bash
specsmith import --project-dir ./my-project
specsmith import --project-dir ./my-project --force
specsmith import --project-dir ./my-project --guided
```

**Options:**

- `--project-dir PATH` — Project root (default: `.`)
- `--force` — Overwrite existing governance files
- `--guided` — Define components interactively after import

**Detects:** language, build system, test framework, CI platform, VCS remote, modules, entry points, existing governance.

## `specsmith audit`

Run drift detection and health checks.

```bash
specsmith audit --project-dir ./my-project
specsmith audit --fix --project-dir ./my-project
```

**Checks:**

- Required files (AGENTS.md, LEDGER.md)
- Modular governance when AGENTS.md exceeds 200 lines
- REQ ↔ TEST coverage consistency
- Ledger size and open TODO count
- Governance file size thresholds
- CI config tool verification (matches tool registry for project type)

**`--fix`** auto-repairs: creates missing governance stubs, compresses oversized ledgers, generates missing CI configs from the tool registry.

## `specsmith validate`

Check governance file consistency.

```bash
specsmith validate --project-dir ./my-project
```

**Checks:** scaffold.yml structure, AGENTS.md local references resolve, requirement ID uniqueness, architecture references requirements.

## `specsmith compress`

Archive old ledger entries.

```bash
specsmith compress --project-dir ./my-project
specsmith compress --threshold 300 --keep-recent 20
```

Archives entries to `docs/ledger-archive.md` when LEDGER.md exceeds the line threshold.

## `specsmith upgrade`

Update governance files to a newer spec version.

```bash
specsmith upgrade --spec-version 0.3.0 --project-dir ./my-project
```

Re-renders governance templates and updates `scaffold.yml` with the new version.

## `specsmith status`

Show CI, alerts, and PR status from the VCS platform CLI.

```bash
specsmith status --project-dir ./my-project
```

Requires `gh` (GitHub), `glab` (GitLab), or `bb` (Bitbucket) CLI to be installed and authenticated.

## `specsmith diff`

Compare governance files against what spec templates would generate.

```bash
specsmith diff --project-dir ./my-project
```

Shows which files match, differ from, or are missing compared to templates.

## `specsmith export`

Generate a compliance and coverage report.

```bash
specsmith export --project-dir ./my-project
specsmith export --project-dir ./my-project --output report.md
```

**Report includes:** project summary, verification tools, REQ↔TEST coverage matrix with percentage, audit summary, governance file inventory.
