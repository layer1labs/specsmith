# CLI Commands

specsmith has 11 commands. Every command that operates on a project accepts `--project-dir PATH` (default: current directory).

## `specsmith init`

Scaffold a new governed project.

```bash
specsmith init                                    # Interactive prompts
specsmith init --config scaffold.yml              # From config file
specsmith init --config scaffold.yml --guided     # + architecture definition
specsmith init --config scaffold.yml --no-git     # Skip git init
specsmith init --output-dir /path/to/parent       # Custom output location
```

**Options:**

- `--config PATH` — Path to scaffold.yml. If omitted, runs interactive prompts for project name, type, platforms, VCS, branching, and integrations.
- `--output-dir PATH` — Parent directory for the new project (default: `.`). The project is created as a subdirectory named after `name` in the config.
- `--no-git` — Skip running `git init` in the new project.
- `--guided` — After scaffolding, prompts for component names and generates REQUIREMENTS.md with `REQ-{COMPONENT}-001/002` stubs, TEST_SPEC.md with linked tests, and architecture.md with component descriptions.

**What it generates:** AGENTS.md, LEDGER.md, modular governance, project docs, type-specific directories, CI config, dependency management, agent integration files, scripts, and scaffold.yml.

**Exit codes:** 0 on success, 1 if the output directory already exists and is not empty.

## `specsmith import`

Adopt an existing project by detecting its structure and generating governance overlay.

```bash
specsmith import --project-dir ./my-project
specsmith import --project-dir ./my-project --force
specsmith import --project-dir ./my-project --guided
```

**Options:**

- `--project-dir PATH` — Project root to analyze (default: `.`).
- `--force` — Overwrite existing governance files. Without this flag, existing files (AGENTS.md, LEDGER.md, etc.) are preserved.
- `--guided` — After generating overlay, prompts for component names and generates richer REQ/TEST stubs.

**Merge behavior:** Import only generates files that don't already exist. This means you can safely run `import` on a project that already has a hand-crafted AGENTS.md — it will add the missing pieces (scaffold.yml, docs/governance/, REQUIREMENTS.md) without touching what's already there.

**Detection:** Language (by file extension counts), build system (pyproject.toml, Cargo.toml, etc.), test framework, CI platform, VCS remote, modules, entry points, test files, existing governance. See [Importing Projects](importing.md) for full details.

## `specsmith audit`

Run drift detection and health checks.

```bash
specsmith audit --project-dir ./my-project
specsmith audit --fix --project-dir ./my-project
```

**Checks performed:**

1. **Required files** — AGENTS.md and LEDGER.md must exist
2. **Modular governance** — If AGENTS.md exceeds 200 lines, docs/governance/*.md must exist
3. **REQ↔TEST coverage** — Every requirement ID in REQUIREMENTS.md must have a `Covers:` reference in TEST_SPEC.md
4. **Ledger health** — LEDGER.md must be under 500 lines; open TODOs must be under 20
5. **Governance size** — Individual governance files must not exceed their line thresholds
6. **Tool configuration** — CI config must reference the expected verification tools for the project type (reads scaffold.yml to determine type)

**`--fix` auto-repairs:**

- Creates stub AGENTS.md and LEDGER.md if missing
- Creates stub modular governance files if missing
- Compresses oversized ledger via `specsmith compress`
- Generates CI config from the tool registry if missing or incomplete

**Exit codes:** 0 if healthy, 1 if issues found.

## `specsmith validate`

Check governance file consistency.

```bash
specsmith validate --project-dir ./my-project
```

**Checks:** scaffold.yml structure and required fields, AGENTS.md local file references resolve, requirement ID uniqueness across REQUIREMENTS.md, architecture.md references at least one requirement.

**Exit codes:** 0 if valid, 1 if issues found.

## `specsmith compress`

Archive old ledger entries when LEDGER.md grows too large.

```bash
specsmith compress --project-dir ./my-project
specsmith compress --threshold 300 --keep-recent 20 --project-dir ./my-project
```

**Options:**

- `--threshold INT` — Only compress if LEDGER.md exceeds this many lines (default: 500).
- `--keep-recent INT` — Keep the N most recent entries in LEDGER.md (default: 10).

Archived entries are moved to `docs/ledger-archive.md`. This is non-destructive — the full history is preserved, just split across files.

## `specsmith upgrade`

Update governance files to a newer spec version.

```bash
specsmith upgrade --spec-version 0.3.0 --project-dir ./my-project
```

Re-renders all governance templates (docs/governance/*.md) using the current scaffold.yml config and the new version. Updates scaffold.yml with the new `spec_version`. Does not touch AGENTS.md, LEDGER.md, or project source code.

## `specsmith status`

Show CI, alerts, and PR status from the VCS platform CLI.

```bash
specsmith status --project-dir ./my-project
```

**Requires:** `gh` (GitHub), `glab` (GitLab), or `bb` (Bitbucket) CLI installed and authenticated. Reads `scaffold.yml` to determine which platform to use.

**Shows:** Latest CI run status, Dependabot/security alert count, open PR/MR count.

## `specsmith diff`

Compare current governance files against what specsmith templates would generate.

```bash
specsmith diff --project-dir ./my-project
```

For each governance file, reports: ✓ (matches template), ~ (differs from template), or ✗ (missing). Useful after manual edits to see what's drifted from the spec.

## `specsmith export`

Generate a compliance and coverage report.

```bash
specsmith export --project-dir ./my-project                    # Print to terminal
specsmith export --project-dir ./my-project --output report.md # Save to file
```

**Report sections:** Project summary, verification tools, REQ↔TEST coverage matrix (with percentage), audit summary (pass/fail/fixable), recent git activity (last 10 commits, contributors), governance file inventory.

See [Export & Compliance](export.md) for a detailed breakdown.

## `specsmith doctor`

Check if the verification tools for your project type are installed locally.

```bash
specsmith doctor --project-dir ./my-project
```

Reads scaffold.yml, looks up the ToolSet for the project type, and checks if each tool is available on PATH. Reports installed (with version) or missing for each tool across all 7 categories (lint, typecheck, test, security, build, format, compliance).

See [Doctor](doctor.md) for details.

## `specsmith --version`

```bash
specsmith --version
# specsmith, version 0.1.3
```
