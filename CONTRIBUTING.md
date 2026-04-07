# Contributing to specsmith

## Bootstrap Notice

specsmith is **bootstrapping its own governance process**. The tool generates the Agentic AI Development Workflow for other projects, but specsmith itself is iteratively adopting that same workflow. Future versions will be developed using an older stable version of itself — the process will converge.

Until then, governance files in this repo (`AGENTS.md`, `LEDGER.md`, `docs/governance/`) represent the target state we are working toward, not a fully enforced process yet.

## Development Setup

```bash
git clone https://github.com/BitConcepts/specsmith.git
cd specsmith
pip install -e ".[dev]"
```

## Branching Strategy (gitflow)

- `main` — production-ready releases
- `develop` — integration branch for next release
- `feature/*` — branch from `develop`, merge back to `develop`
- `release/*` — branch from `develop`, merge to `main` + `develop`
- `hotfix/*` — branch from `main`, merge to `main` + `develop`

```bash
git checkout develop
git checkout -b feature/my-feature
# work, commit, push
gh pr create --base develop
```

## Running Checks

```bash
ruff check src/ tests/ && ruff format --check src/ tests/ && mypy src/specsmith/ && pytest tests/ -v
```

## Pre-commit

```bash
pre-commit install
```

## Code Standards

- SPDX headers on all `.py` files (`MIT`, `BitConcepts, LLC.`)
- Must pass `ruff check`, `ruff format --check`, `mypy --strict`
- All features require tests
- Windows scripts: `.cmd` only (no `.ps1`)
- Line length: 100

## Tool Registry

When adding a new project type:
1. Add the enum to `config.py` (`ProjectType`)
2. Add type label and section ref to `config.py` (`_TYPE_LABELS`, `_SECTION_REFS`)
3. Add directory structure to `scaffolder.py` (`_get_empty_dirs`)
4. Add tool entries to `tools.py` (`_TOOL_REGISTRY`)
5. Add CI metadata to `tools.py` (`LANG_CI_META`) if the language is new
6. Add type-specific rules to `templates/agents.md.j2`
7. Add type→tool-key mapping in `toolrules.py` (`_TYPE_TOOL_KEYS`)
8. Add install commands in `tool_installer.py` (`KNOWN_TOOLS`) for any new tools
9. Add tests for the new type

## Execution Profiles

The four built-in profiles (`safe`, `standard`, `open`, `admin`) live in `profiles.py`.
To change what commands are allowed by default in the `standard` profile, edit
`_STANDARD_ALLOWED_COMMANDS` / `_STANDARD_BLOCKED_COMMANDS` / `_STANDARD_BLOCKED_PATTERNS`.
New profiles can be added to the `PROFILES` dict — they will be available via `scaffold.yml`
`execution_profile` and in the VS Code Settings panel.

## Tool Rules

Curated AI context rules live in `toolrules.py` (`TOOL_RULES` dict).
Each entry is a markdown bullet-list injected into the agent system prompt.
When adding rules for a new tool:
1. Add an entry to `TOOL_RULES` keyed by the tool executable name.
2. Add the key to `_FPGA_CHIP_TO_KEY` if it's an FPGA chip name (as used in `fpga_tools:`).
3. Update `_TYPE_TOOL_KEYS` to include it for relevant project types.

## Supporting the Project

Star the repo, report issues, and consider [sponsoring BitConcepts](https://github.com/sponsors/BitConcepts).

## Importing Existing Projects

`specsmith import` generates governance overlay for existing projects. The detection engine in `importer.py` handles:
- Language detection by file extension
- Build system detection (pyproject.toml, Cargo.toml, CMakeLists.txt, etc.)
- Test framework detection
- CI and VCS platform detection
- Module and entry point discovery

## Pull Requests

- Branch from `develop` (features) or `main` (hotfixes)
- All CI must pass (lint, typecheck, test × 9 matrix, security)
- Update `CHANGELOG.md` and docs if applicable
- One approval required

## Configurable Governance

Key tuning knobs in `scaffold.yml` for enterprise teams:

| Setting | Default | Description |
|---------|---------|-------------|
| `branching_strategy` | gitflow | gitflow, trunk-based, github-flow |
| `require_pr_reviews` | true | Require reviews before merge |
| `required_approvals` | 1 | Number of required approvals |
| `require_ci_pass` | true | CI must pass before merge |
| `allow_force_push` | false | Allow force push to protected branches |
| `use_remote_rules` | false | Accept existing remote branch rules |
| `vcs_platform` | github | github, gitlab, bitbucket |
