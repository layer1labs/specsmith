# Getting Started

## Installation

### From PyPI

```bash
pip install specsmith
```

### From Source

```bash
git clone https://github.com/BitConcepts/specsmith.git
cd specsmith
pip install -e ".[dev]"
```

### Verify Installation

```bash
specsmith --version
# specsmith, version {{ version }}

# Or via python module
python -m specsmith --version
```

## Tutorial: Create a New Python CLI Project

This walkthrough creates a governed Python CLI project from scratch.

### Step 1: Create the Config

Create `scaffold.yml`:

```yaml
name: my-tool
type: cli-python
platforms: [windows, linux, macos]
language: python
vcs_platform: github
branching_strategy: gitflow
integrations: [agents-md, warp, claude-code]
```

### Step 2: Scaffold

```bash
specsmith init --config scaffold.yml --output-dir .
```

This creates the `my-tool/` directory with ~30 files:

```
my-tool/
├── AGENTS.md                          # Governance hub
├── LEDGER.md                          # Change ledger
├── README.md                          # Project readme
├── pyproject.toml                     # Python project config
├── scaffold.yml                       # specsmith config (saved)
├── .gitignore / .gitattributes
├── docs/
│   ├── governance/
│   │   ├── rules.md                   # Hard rules H1-H9
│   │   ├── workflow.md                # Session lifecycle
│   │   ├── roles.md                   # Agent boundaries
│   │   ├── context-budget.md          # Token optimization
│   │   ├── verification.md            # Tools: ruff, mypy, pytest
│   │   └── drift-metrics.md           # Health signals
│   ├── architecture.md
│   ├── workflow.md
│   ├── REQUIREMENTS.md
│   └── TEST_SPEC.md
├── src/my_tool/
│   ├── __init__.py
│   └── cli.py
├── tests/.gitkeep
├── scripts/
│   ├── setup.cmd / setup.sh
│   ├── run.cmd / run.sh
│   └── exec.cmd / exec.sh
├── .github/
│   ├── workflows/ci.yml               # ruff + mypy + pytest + pip-audit
│   └── dependabot.yml                 # pip + github-actions
├── .warp/skills/SKILL.md              # Warp/Oz governance skill
└── CLAUDE.md                          # Claude Code governance
```

### Step 3: Verify Governance Health

```bash
specsmith audit --project-dir my-tool
# Healthy. 9 checks passed.
```

### Step 4: Check Your Tools

```bash
specsmith doctor --project-dir my-tool
# ✓ lint: ruff (ruff 0.4.x)
# ✓ typecheck: mypy (mypy 1.10.x)
# ✓ test: pytest (pytest 9.x)
# ...
```

### Step 5: Open in Your AI Agent

Open the project in Warp, Claude Code, Cursor, or your preferred agent. The agent reads `AGENTS.md` and knows the governance rules. Type `start` to begin a governed session.

## Tutorial: Import an Existing Project

This walkthrough adopts an existing Python project that has no specsmith governance.

### Step 1: Run Import

```bash
specsmith import --project-dir ./my-existing-project
```

specsmith analyzes the project and reports:

```
Analyzing C:\path\to\my-existing-project...

  Files: 47
  Language: python
  Build system: pyproject
  Test framework: pytest
  CI: github
  VCS: github
  Inferred type: cli-python
  Modules: myapp
  Existing governance: (none)

Proceed with these settings? [Y/n]:
```

### Step 2: Review Generated Files

After confirming, specsmith generates only the **missing** governance files:

- `AGENTS.md` — populated with detected project info
- `LEDGER.md` — initial import entry
- `docs/REQUIREMENTS.md` — one REQ per detected module
- `docs/TEST_SPEC.md` — one TEST per detected test file
- `docs/architecture.md` — modules, entry points, language distribution
- `docs/governance/*.md` — modular governance stubs
- `scaffold.yml` — project config for future commands

If the project already has `AGENTS.md` (from a previous manual setup), specsmith **skips it** and only generates what's missing. Use `--force` to overwrite.

### Step 3: Add Architecture (Optional)

```bash
specsmith import --project-dir ./my-existing-project --guided
```

The `--guided` flag prompts you to name your components, then generates richer REQ/TEST stubs and an architecture document.

### Step 4: Ongoing Governance

Now you can use all specsmith commands:

```bash
specsmith audit --project-dir ./my-existing-project    # Health check
specsmith validate --project-dir ./my-existing-project  # Consistency
specsmith export --project-dir ./my-existing-project    # Coverage report
specsmith doctor --project-dir ./my-existing-project    # Tool check
```

## What Happens With Different Project Types

The scaffold structure changes based on project type. A patent application:

```bash
specsmith init --config patent.yml
```

Gets: `claims/`, `specification/`, `figures/`, `prior-art/`, `correspondence/` directories, claim-specific REQs (`REQ-CLM-001`), and governance rules about claim dependencies.

A Rust CLI project gets: `src/`, `tests/`, `benches/` directories, CI with `cargo clippy`, `cargo test`, `cargo audit`, and rules about clippy warnings and doc comments.

See [Project Types](project-types.md) for all 30 types.
