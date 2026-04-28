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
integrations: [agents-md, agent-skill, claude-code]
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
├── CONTRIBUTING.md                    # Contribution guide
├── SECURITY.md                        # Vulnerability reporting
├── CODE_OF_CONDUCT.md                 # Contributor Covenant
├── LICENSE                            # MIT (configurable)
├── pyproject.toml                     # Python project config
├── scaffold.yml                       # specsmith config (saved)
├── .gitignore / .gitattributes
├── docs/
│   ├── governance/
│   │   ├── RULES.md                   # Hard rules H1-H9
│   │   ├── WORKFLOW.md                # Session lifecycle
│   │   ├── ROLES.md                   # Agent boundaries
│   │   ├── CONTEXT-BUDGET.md          # Token optimization
│   │   ├── VERIFICATION.md            # Tools: ruff, mypy, pytest
│   │   └── DRIFT-METRICS.md           # Health signals
│   ├── ARCHITECTURE.md
│   ├── WORKFLOW.md
│   ├── REQUIREMENTS.md
│   └── TESTS.md
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
│   ├── dependabot.yml                 # pip + github-actions
│   ├── PULL_REQUEST_TEMPLATE.md        # Governance-aware PR template
│   └── ISSUE_TEMPLATE/                # Bug report + feature request
├── .agents/skills/SKILL.md            # Generic agent SKILL.md (terminal-native AI runtimes)
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

### Step 5: Set the AEE Workflow Phase

```bash
specsmith phase --project-dir my-tool
```

This shows the current phase (defaults to `inception`) with a readiness checklist. Advance when checks pass:

```bash
specsmith phase next --project-dir my-tool   # advance to architecture
specsmith phase list                         # show all 7 phases
```

### Step 6: Open in Your AI Agent

From the project root, use the universal session start command:

```
/agent AGENTS.md
```

This works in Claude Code, Cursor, terminal-native AI agents that load `.agents/skills/SKILL.md`, and any agent that reads project context files. The agent reads `AGENTS.md` (the governance hub), loads `LEDGER.md` for session state, and follows the closed-loop workflow.

After the agent is loaded, use the quick command `start` to trigger the full session start protocol.

**Or use the VS Code extension:** Open the specsmith sidebar, click **+** in Sessions, and select the project folder. The Settings Panel shows your current AEE phase and all governance file status.

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
- `docs/TESTS.md` — one TEST per detected test file
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
