# Configuration

Projects are configured via `scaffold.yml`.

## Full Reference

```yaml
# Config inheritance (optional — merge org defaults)
extends: path/to/org-defaults.yml

# Project identity
name: my-project                    # Required
type: cli-python                    # Required — one of 30 types
platforms: [windows, linux, macos]  # Target platforms
language: python                    # Primary language
description: "Short description"    # Optional
spec_version: 0.1.0-alpha.3        # Spec version

# VCS and branching
vcs_platform: github                # github, gitlab, bitbucket, or ""
branching_strategy: gitflow         # gitflow, trunk-based, github-flow
default_branch: main
develop_branch: develop
require_pr_reviews: true
required_approvals: 1
require_ci_pass: true
allow_force_push: false
use_remote_rules: false

# Scaffold options
git_init: true                      # Run git init
services: false                     # Include services.md
shell_wrappers: false               # Include shell wrapper scripts
exec_shims: true                    # Include timeout shim scripts

# Agent integrations
integrations:
  - agents-md                       # Always included
  - warp                            # Warp / Oz
  - claude-code                     # Claude Code
  - copilot                         # GitHub Copilot
  - cursor                          # Cursor
  - gemini                          # Gemini CLI
  - windsurf                        # Windsurf
  - aider                           # Aider

# Tool overrides (optional — defaults from registry)
verification_tools:
  lint: "flake8,pylint"
  test: "unittest"

# Import metadata (auto-populated by specsmith import)
detected_build_system: ""
detected_test_framework: ""
```

## Config Inheritance

Use `extends` to inherit defaults from a parent config:

```yaml
# org-defaults.yml (shared across team)
name: placeholder
type: cli-python
vcs_platform: github
branching_strategy: gitflow
require_pr_reviews: true
required_approvals: 2
```

```yaml
# project scaffold.yml
extends: ./org-defaults.yml
name: my-specific-project
description: "Overrides name but inherits everything else"
```

The child config overrides any field it sets; everything else comes from the parent.
