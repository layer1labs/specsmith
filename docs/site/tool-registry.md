# Tool Registry

The verification tool registry is the core of specsmith's tool-aware CI generation. It maps each project type to the correct lint, typecheck, test, security, build, format, and compliance tools.

## How It Works

1. **Registry lookup** — When scaffolding a project, specsmith looks up the `ToolSet` for the project type in `tools.py`.
2. **CI generation** — The VCS platform (GitHub/GitLab/Bitbucket) uses the `ToolSet` to generate CI config with the correct tool commands.
3. **Verification templates** — The `verification.md` governance file lists the project's specific tools.
4. **Audit checks** — `specsmith audit` verifies that CI configs reference the expected tools.
5. **Auto-fix** — `specsmith audit --fix` can generate missing CI configs from the registry.

## Tool Categories

Each `ToolSet` has 7 categories:

- **lint** — Static analysis and style checking (ruff, eslint, clippy, vale)
- **typecheck** — Type safety verification (mypy, tsc, cargo check, cppcheck)
- **test** — Unit and integration testing (pytest, jest, cargo test, markdown-link-check)
- **security** — Vulnerability scanning (pip-audit, npm audit, cargo audit, tfsec)
- **build** — Compilation and output generation (cmake, cargo build, pandoc, pdflatex)
- **format** — Code/document formatting (ruff format, prettier, cargo fmt, clang-format)
- **compliance** — Domain-specific compliance (MISRA-C, claim-ref-check, regulation-ref-check)

## CI Metadata

For each language, specsmith knows:

- **GitHub Actions setup step** — e.g., `actions/setup-python@v6`, `dtolnay/rust-toolchain@stable`
- **Docker image** — for GitLab CI and Bitbucket Pipelines (e.g., `python:3.12-slim`, `rust:latest`)
- **Install command** — dependency installation (e.g., `pip install -e ".[dev]"`, `npm ci`)
- **Cache key** — Bitbucket pipeline caches (pip, node)

Supported languages: Python, Rust, Go, JavaScript, TypeScript, C#, Dart, C, C++, Terraform, VHDL, Verilog, Markdown, LaTeX, OpenAPI, Protobuf.

## Overriding Tools

Override any tool category in `scaffold.yml`:

```yaml
verification_tools:
  lint: "flake8,pylint"
  test: "unittest"
```

Non-overridden categories keep their registry defaults.

## Format Check Mode

For CI, format tools are converted to check-mode equivalents:

- `ruff format` → `ruff format --check .`
- `cargo fmt` → `cargo fmt -- --check`
- `prettier` → `npx prettier --check .`
- `gofmt` → `test -z "$(gofmt -l .)"`
- `clang-format` → `clang-format --dry-run --Werror`
- `dotnet format` → `dotnet format --verify-no-changes`
