# Importing Existing Projects

`specsmith import` adopts an existing project by detecting its structure and generating governance overlay files.

## How It Works

### Phase 1: Detection (deterministic)

The importer walks the project directory and detects:

- **Languages** — by file extension counts (Python, Rust, Go, C, JS/TS, LaTeX, protobuf, etc.)
- **Build system** — pyproject.toml, Cargo.toml, CMakeLists.txt, package.json, go.mod, .csproj, Makefile
- **Test framework** — pytest, cargo test, ctest, jest, vitest, go test
- **CI platform** — .github/workflows, .gitlab-ci.yml, bitbucket-pipelines.yml
- **VCS remote** — git remote URL → GitHub, GitLab, or Bitbucket
- **Existing governance** — AGENTS.md, LEDGER.md, CLAUDE.md, etc.
- **Modules** — Python packages, Rust crates, Go packages, JS/TS source directories
- **Entry points** — CLI files, main files, app files
- **Test files** — files matching test_*, _test.*, .test., .spec. patterns

### Phase 2: Scaffold Overlay

Based on detection, specsmith generates:

- **AGENTS.md** — populated with detected project info and workflow rules
- **LEDGER.md** — initial entry recording the import
- **docs/REQUIREMENTS.md** — one REQ per detected module + build requirement
- **docs/TEST_SPEC.md** — one TEST per detected test file, linked to inferred REQs
- **docs/architecture.md** — directory structure, modules, entry points, language distribution
- **scaffold.yml** — project config for future specsmith commands

Existing files are **never overwritten** unless `--force` is specified.

### Phase 3: AI Enrichment

After import, open the project in your AI agent. The AGENTS.md contains a note that this project was imported by specsmith, prompting the agent to propose deeper analysis.

## Usage

```bash
# Basic import
specsmith import --project-dir ./my-project

# Force overwrite existing governance files
specsmith import --project-dir ./my-project --force

# Import + guided architecture definition
specsmith import --project-dir ./my-project --guided
```

## Type Inference

The importer infers the best project type from detection results:

- Python with `cli.py` entry point → `cli-python`
- Python with `manage.py` → `backend-frontend`
- Rust with `src/lib.rs` → `library-rust`
- Rust with `src/main.rs` → `cli-rust`
- Go project → `cli-go`
- C/C++ with CMake → `cli-c` or `library-c`
- JS/TS with React/Vue in package.json → `web-frontend`
- LaTeX files → `research-paper`
- Protobuf/GraphQL → `api-specification`
- Terraform → `devops-iac`
