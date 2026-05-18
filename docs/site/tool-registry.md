# Tool Registry

## Overview

The tool registry is the data structure at the heart of specsmith's CI generation. It maps every project type to the exact verification tools that should be used — not generic "add your tools here" placeholders, but specific commands like `cargo clippy`, `ruff check`, `vale`, or `claim-ref-check`.

This means a Rust CLI project scaffolded by specsmith gets CI with `cargo clippy`, `cargo test`, `cargo audit`, and `cargo fmt -- --check` — not a blank YAML file.

## How It Flows

```
scaffold.yml (type: cli-rust)
    ↓
tools.py → ToolSet(lint=["cargo clippy"], test=["cargo test"], ...)
    ↓
github.py → .github/workflows/ci.yml with real cargo commands
    ↓
verification.md.j2 → docs/governance/verification.md lists the tools
    ↓
auditor.py → specsmith audit checks CI references these tools
    ↓
doctor.py → specsmith doctor checks tools are installed locally
```

## The 7 Tool Categories

| Category | Purpose | Examples |
|----------|---------|---------|
| **lint** | Static analysis, style | ruff, eslint, clippy, vale, clang-tidy, tflint |
| **typecheck** | Type safety | mypy, tsc, cargo check, cppcheck, go vet |
| **test** | Unit/integration testing | pytest, jest, cargo test, ctest, markdown-link-check |
| **security** | Vulnerability scanning | pip-audit, npm audit, cargo audit, govulncheck, tfsec |
| **build** | Compilation, output | cmake, cargo build, pandoc, pdflatex, docker compose |
| **format** | Code/doc formatting | ruff format, prettier, cargo fmt, clang-format, latexindent |
| **compliance** | Domain-specific rules | MISRA-C, claim-ref-check, regulation-ref-check, bom-validate |

## CI Metadata Per Language

For each language, specsmith stores setup information used by all three CI platforms:

| Language | GitHub Actions Setup | Docker Image | Install Cmd |
|----------|---------------------|-------------|-------------|
| Python | `actions/setup-python@v6` | `python:3.12-slim` | `pip install -e ".[dev]"` |
| Rust | `dtolnay/rust-toolchain@stable` | `rust:latest` | — |
| Go | `actions/setup-go@v5` | `golang:1.22` | — |
| JavaScript/TS | `actions/setup-node@v4` | `node:20` | `npm ci` |
| C# | `actions/setup-dotnet@v4` | `mcr.microsoft.com/dotnet/sdk:8.0` | `dotnet restore` |
| Dart | `subosito/flutter-action@v2` | `ghcr.io/cirruslabs/flutter:latest` | `flutter pub get` |
| Terraform | `hashicorp/setup-terraform@v3` | `hashicorp/terraform:latest` | `terraform init` |
| Markdown | — | `pandoc/core:latest` | `pip install vale mkdocs` |
| LaTeX | — | `texlive/texlive:latest` | — |
| OpenAPI | `actions/setup-node@v4` | `node:20` | `npm ci` |
| Protobuf | — | `namely/protoc:latest` | — |
| C/C++ | — | `gcc:latest` | — |
| VHDL | — | `ghdl/ghdl:latest` | — |
| Verilog | — | `verilator/verilator:latest` | — |

## Overriding Tools

If the defaults don't match your project, override any category in `scaffold.yml`:

```yaml
verification_tools:
  lint: "flake8,pylint"
  test: "unittest"
  security: "safety"
```

Non-overridden categories keep their registry defaults. For example, if you override `lint` but not `test`, you get your custom linter with the default test runner.

## Format Check Mode

In CI, you want format tools to *check* (not rewrite). specsmith converts format commands to check-mode:

| Format Command | CI Check Mode |
|---------------|---------------|
| `ruff format` | `ruff format --check .` |
| `cargo fmt` | `cargo fmt -- --check` |
| `prettier` | `npx prettier --check .` |
| `gofmt` | `test -z "$(gofmt -l .)"` |
| `clang-format` | `clang-format --dry-run --Werror` |
| `dotnet format` | `dotnet format --verify-no-changes` |

## Mixed-Language Projects

Projects like `backend-frontend` (Python + JS) or `microservices` (Python + JS) have tools from multiple ecosystems. specsmith detects this and adds multiple runtime setups to CI:

```yaml
# Generated for backend-frontend
steps:
  - uses: actions/setup-python@v6
  - uses: actions/setup-node@v4     # Auto-added for eslint/vitest
  - run: pip install -e ".[dev]"
  - run: npm ci                      # Auto-added
  - run: ruff check
  - run: eslint
```

## Audit Integration

`specsmith audit` reads scaffold.yml, looks up the expected tools, and verifies they appear in the CI config. If your CI is missing expected tools, audit reports it. `audit --fix` can regenerate the entire CI config from the registry.

## Doctor Integration

`specsmith doctor` checks if each tool in the ToolSet is actually installed on your local machine. Useful when setting up a new development environment.

## Agent Tool Registry (AVAILABLE_TOOLS)

The agent tool registry is separate from the CI verification tool registry above. These tools
are available to agent roles inside the agentic REPL and multi-agent DAG dispatcher.

### Core File and Shell Tools (REQ-067)

| Tool | Description |
|------|-------------|
| 
un_shell | Execute a shell command (safety-checked; destructive commands blocked) |
| 
ead_file | Read a file from the repository |
| write_file | Write/create a file |
| patch_file | Apply a unified diff patch |
| list_files | List files matching a glob pattern |
| grep | Search for a string across files |
| git_diff | Get git diff for the working tree |
| git_status | Get git status |
| 
un_tests | Run the project test suite |
| open_url | Fetch text content from a URL |
| search_docs | Search documentation files in the repo |
| 
emember_project_fact | Store a named fact in .repo-index/facts.json |

### Compiler and Formatter Tools

These tools are registered in AVAILABLE_TOOLS and wired into ROLE_TOOLS for relevant agent roles.
All use the @validate_json_args safety decorator; compiler invocations are gated by is_safe_command.

| Tool | Roles | Default binary |
|------|-------|---------------|
| 
un_gcc | coder, tester, embedded-coder | gcc |
| 
un_arm_gcc | coder, tester, embedded-coder | rm-none-eabi-gcc |
| 
un_aarch64_gcc | embedded-coder | arch64-linux-gnu-gcc |
| 
un_iar_compiler | embedded-coder | IarBuild |
| 
un_intel_compiler | embedded-coder | icx |
| 
un_clang_format | coder, architect | clang-format |
| 
un_clang_tidy | reviewer, embedded-coder | clang-tidy |
| 
un_vsg | coder, reviewer, embedded-coder | sg |

### Agent Roles and Tool Subsets (ROLE_TOOLS)

Each agent role receives a restricted subset of tools at spawn time (spawn_worker(role, llm_config)):

| Role | Tools |
|------|-------|
| coder | read_file, write_file, run_shell, apply_diff, run_gcc, run_arm_gcc, run_clang_format, run_clang_tidy, run_vsg |
| 
eviewer | read_file, run_shell, git_diff, run_clang_tidy, run_vsg |
| 	ester | read_file, run_shell, run_tests, run_gcc, run_arm_gcc |
| rchitect | read_file, write_file, run_clang_format |
| 
esearcher | read_file, search_web, search_repo |
| mbedded-coder | All compiler tools + read_file, write_file, run_shell |
