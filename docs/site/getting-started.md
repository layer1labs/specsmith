# Getting Started

## Installation

```bash
pip install specsmith
```

From source:

```bash
git clone https://github.com/BitConcepts/specsmith.git
cd specsmith
pip install -e ".[dev]"
```

## Create a New Project

### Interactive Mode

```bash
specsmith init
```

This walks you through selecting a project type, platforms, VCS platform, branching strategy, and agent integrations.

### From Config File

Create a `scaffold.yml`:

```yaml
name: my-project
type: cli-python
platforms: [windows, linux, macos]
language: python
vcs_platform: github
branching_strategy: gitflow
integrations: [agents-md, warp, claude-code]
```

Then scaffold:

```bash
specsmith init --config scaffold.yml --output-dir .
```

### Guided Mode

Add `--guided` to interactively define your architecture components. specsmith auto-generates requirement and test stubs:

```bash
specsmith init --config scaffold.yml --output-dir . --guided
```

## Import an Existing Project

```bash
specsmith import --project-dir ./my-existing-project
```

specsmith detects language, build system, test framework, CI, and VCS platform, then generates governance overlay files (AGENTS.md, LEDGER.md, docs/REQUIREMENTS.md, docs/TEST_SPEC.md, docs/architecture.md).

Use `--force` to overwrite existing governance files, or `--guided` to add architecture definitions after import.

## Ongoing Governance

```bash
# Health and drift checks
specsmith audit --project-dir ./my-project

# Auto-fix missing files and CI configs
specsmith audit --fix --project-dir ./my-project

# Consistency checks
specsmith validate --project-dir ./my-project

# Compress oversized ledger
specsmith compress --project-dir ./my-project

# Upgrade governance to new spec version
specsmith upgrade --spec-version 0.3.0 --project-dir ./my-project

# Compare files against templates
specsmith diff --project-dir ./my-project

# CI/PR/alert status from VCS platform
specsmith status --project-dir ./my-project

# Generate compliance report
specsmith export --project-dir ./my-project
specsmith export --project-dir ./my-project --output report.md
```

## What Gets Generated

A scaffolded project includes:

- **AGENTS.md** — Agent governance hub with type-specific rules
- **LEDGER.md** — Append-only change record
- **docs/governance/** — Modular governance (rules, workflow, roles, verification, etc.)
- **docs/REQUIREMENTS.md** — Numbered requirements with domain-specific starters
- **docs/TEST_SPEC.md** — Test specifications linked to requirements
- **docs/architecture.md** — Architecture overview with tool listings
- **CI config** — GitHub Actions / GitLab CI / Bitbucket Pipelines with correct tools
- **Dependency management** — Dependabot or Renovate with correct ecosystem
- **Agent files** — Warp SKILL.md, CLAUDE.md, Copilot instructions, etc.
- **Scripts** — setup, run, exec shims for cross-platform support
