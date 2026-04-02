# Configuration

Projects are configured via `scaffold.yml`. This file is created by `specsmith init` (saved automatically) or `specsmith import` (generated from detection). It drives all subsequent commands — audit, upgrade, diff, export, and doctor all read it.

## Full Reference

```yaml
# Config inheritance — merge org-level defaults
extends: path/to/org-defaults.yml

# Project identity
name: my-project                    # Required — used for directory and package name
type: cli-python                    # Required — one of 30 project types
platforms: [windows, linux, macos]  # Target platforms
language: python                    # Primary language/runtime
description: "Short description"    # Optional project description
spec_version: 0.1.3                 # Spec version (auto-managed by upgrade)

# VCS and branching
vcs_platform: github                # github, gitlab, bitbucket, or "" (none)
branching_strategy: gitflow         # gitflow, trunk-based, github-flow
default_branch: main                # Production branch name
develop_branch: develop             # Integration branch (gitflow only)
require_pr_reviews: true            # Require PR reviews before merge
required_approvals: 1               # Number of required approvals
require_ci_pass: true               # CI must pass before merge
allow_force_push: false             # Allow force push to protected branches
use_remote_rules: false             # Accept existing remote branch protection

# Scaffold options
git_init: true                      # Run git init in new project
services: false                     # Include services.md for daemon projects
shell_wrappers: false               # Include shell wrapper scripts
exec_shims: true                    # Include timeout shim scripts

# Agent integrations
integrations:
  - agents-md        # AGENTS.md (always included)
  - warp             # .warp/skills/SKILL.md
  - claude-code      # CLAUDE.md
  - copilot          # .github/copilot-instructions.md
  - cursor           # .cursor/rules/governance.mdc
  - gemini           # GEMINI.md
  - windsurf         # .windsurfrules
  - aider            # .aider.conf.yml

# Tool overrides (defaults from registry per type)
verification_tools:
  lint: "flake8,pylint"
  test: "unittest"

# Import metadata (auto-populated by specsmith import)
detected_build_system: ""
detected_test_framework: ""
```

## Field Details

### `extends`
Path to a parent scaffold.yml. The child config inherits all fields from the parent. Any field set in the child overrides the parent. Use this for organization-level defaults:

```yaml
# org-defaults.yml
name: placeholder
type: cli-python
vcs_platform: github
required_approvals: 2
```

```yaml
# project scaffold.yml
extends: ../org-defaults.yml
name: my-project
description: "Inherits org defaults, overrides name"
```

### `type`
One of 30 project types. Determines directory structure, verification tools, CI config, governance rules, and template starters. See [Project Types](project-types.md).

### `vcs_platform`
Controls which CI config is generated:
- `github` → `.github/workflows/ci.yml` + `.github/dependabot.yml`
- `gitlab` → `.gitlab-ci.yml` + `renovate.json`
- `bitbucket` → `bitbucket-pipelines.yml` + `renovate.json`
- `""` → no CI config generated

### `branching_strategy`
- `gitflow` — `main` + `develop` + feature/release/hotfix branches
- `trunk-based` — single `main` with short-lived feature branches
- `github-flow` — `main` + feature branches with PR workflow

### `integrations`
List of agent integration adapters to generate files for. `agents-md` is always included (generates AGENTS.md). Each adapter generates its platform-specific governance file. See [Agent Integrations](agent-integrations.md).

### `verification_tools`
Override any tool category. Values are comma-separated tool commands. Non-overridden categories keep their registry defaults. See [Tool Registry](tool-registry.md).
