# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Curated AI context rulesets per development tool.

Each entry is a concise, actionable ruleset that the agent injects into its
system prompt when that tool is present in the project.  Rules are drawn from
official docs, community best-practice guides, and widely-adopted linter
configurations (VSG community rules, Verilator -Wall policy, ruff default
ruleset, etc.).

Usage::

    from specsmith.toolrules import get_rules_for_project
    context = get_rules_for_project(project_type, fpga_tools, languages)
    # inject context into system prompt
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tool rule database
# Tool keys match the executable names used in FPGA_TOOL_EXES and ToolSet.
# ---------------------------------------------------------------------------

TOOL_RULES: dict[str, str] = {
    # ── HDL / FPGA simulation ────────────────────────────────────────────────
    "ghdl": """\
## GHDL (VHDL Simulator) Rules
- Default language standard is VHDL-93. Use `--std=08` for VHDL-2008 (preferred for new designs).
- Use `--ieee=synopsys` when working with legacy Synopsys IEEE libraries; prefer `--ieee=standard` for new code.
- Workflow: analyze (`ghdl -a`), elaborate (`ghdl -e`), run (`ghdl -r`).
- For VHDL-2008 testbenches, terminate cleanly with `std.env.stop(0)` instead of `wait;`.
- Use `--wave=<file>.ghw` or `--vcd=<file>.vcd` for waveform capture; prefer `.ghw` (more compact).
- Compile all dependencies before the entity that uses them; order matters.
- Common CI invocation: `ghdl -a --std=08 src/*.vhd && ghdl -e --std=08 tb_top && ghdl -r --std=08 tb_top --wave=tb.ghw`.
- Report pass/fail with `report "TEST PASSED" severity note;` and `report "TEST FAILED" severity failure;`.
""",
    "iverilog": """\
## Icarus Verilog (iverilog) Rules
- Compile with `iverilog -o sim.vvp -g2012 design.v tb.v` for IEEE 1800-2012 SystemVerilog support.
- Run simulation with `vvp sim.vvp`; dump waveforms with `$dumpfile("dump.vcd"); $dumpvars(0, tb);`.
- Use `-Wall` to enable all warnings — treat them as errors on clean projects.
- The `-g` flag controls language standard: `-g2005-sv`, `-g2009`, `-g2012` (recommended).
- `$finish` terminates simulation; `$stop` pauses for interactive debug.
- Icarus does not support all SystemVerilog synthesis constructs; prefer GHDL/Verilator for advanced SV.
- Use `` `include `` for file inclusion; avoid circular includes.
""",
    "verilator": """\
## Verilator Rules
- Use `verilator --lint-only -Wall <files>` for lint-only checks (no compilation needed).
- Suppress individual warnings with `/* verilator lint_off UNUSED */` … `/* verilator lint_on UNUSED */`.
- For SystemVerilog, add `--sv` flag; for C++ model generation use `--cc`.
- Avoid `initial` blocks in synthesizable RTL — use them only in testbenches.
- Prefer `always_ff`, `always_comb`, `always_latch` over plain `always` in SystemVerilog.
- `--top-module <name>` sets the DUT top; useful when multiple tops exist.
- Enable strict mode with `--Wno-fatal` to downgrade fatal to warnings during early development.
- `verilator -f <filelist>` reads a file containing command-line options for large projects.
""",
    "vsg": """\
## VSG (VHDL Style Guide) Rules
- Configuration lives in `.vsg_config.yaml` (or JSON). Always provide one for consistent team style.
- Signal/variable identifiers: `lower_snake_case`. Constants/generics: `UPPER_SNAKE_CASE`.
- One entity and one architecture per file; filename should match entity name.
- Architecture names: `rtl` for synthesizable, `tb` for testbench, `behav` for behavioural models.
- Registered signal names should carry a `_reg` suffix; combinational outputs `_comb`.
- Port naming: avoid trailing `_i` / `_o` suffixes (deprecated in VHDL-2008 style).
- Run `vsg --rules` to list all available rules. Run `vsg --fix` to apply auto-fixable violations.
- Suppress specific rules inline with `-- vsg_off rule.name` and `-- vsg_on rule.name`.
- Use `vsg --configuration .vsg_config.yaml <files>` in CI for deterministic checks.
""",
    "symbiyosys": """\
## SymbiYosys / Formal Verification Rules
- SymbiYosys (sby) uses `.sby` task files; run with `sby -f <taskfile>.sby`.
- Task structure: `[options]`, `[engines]`, `[script]`, `[files]` sections.
- Engine choices: `smtbmc` (general), `aiger` (BMC), `btor2` (BTOR2 model).
- Proof modes: `prove` (full proof), `cover` (reachability), `bmc` (bounded).
- Add `assume` properties in RTL using SystemVerilog `assume` or VHDL `assume` statements.
- Add `assert` properties for safety checks; `cover` for liveness/reachability.
- Use `--depth N` to set BMC depth; start with 20–50 for quick checks.
- Keep formal properties in a separate `_props.sv` or `_props.vhd` file, included in `.sby`.
""",
    "yosys": """\
## Yosys (Open-source Synthesis) Rules
- Basic synthesis flow: `read_verilog design.v`, `synth -top top_module`, `write_json netlist.json`.
- Use `synth_ice40`, `synth_ecp5`, `synth_nexus` for vendor-specific synthesis flows.
- `hierarchy -check -top <module>` validates the module hierarchy before synthesis.
- Use `opt; opt_clean -purge` to remove dead logic before technology mapping.
- For VHDL input, use GHDL as a frontend: `ghdl --std=08 <files> -e top && yosys -m ghdl ...`.
- Tcl scripting: use `yosys proc; yosys memory; yosys techmap` for manual flow control.
- `show -format dot -prefix out` renders the design as a Graphviz dot file.
""",
    # ── FPGA synthesis tools ─────────────────────────────────────────────────
    "vivado": """\
## AMD Vivado Tcl / Constraints Rules
- Always run in batch mode for CI: `vivado -mode batch -source run.tcl`.
- Separate synthesis and implementation into distinct Tcl scripts for modularity.
- Timing constraints (XDC): use `create_clock`, `set_input_delay`, `set_output_delay`.
  Example: `create_clock -period 10.0 -name clk [get_ports clk]`
- CDC paths: declare `set_false_path -from [get_clocks clk_a] -to [get_clocks clk_b]`.
- Multicycle paths: `set_multicycle_path -setup 2 -from [...] -to [...]`.
- Use `read_xdc constraints.xdc` in the synthesis script, NOT `add_files` for XDC.
- Always call `report_timing_summary -warn_on_violation` after implementation.
- Use `write_checkpoint` after synthesis and implementation for incremental flows.
- Pin assignments go in a separate `pins.xdc`; keep timing constraints in `timing.xdc`.
""",
    "quartus_sh": """\
## Intel/Altera Quartus Rules
- Full compilation flow: `quartus_sh --flow compile <project>.qpf`.
- SDC timing constraints are very similar to Vivado XDC syntax.
  Example: `create_clock -period 10 -name clk {clk}` (curly braces for node names).
- Pin assignments: `set_location_assignment PIN_xx -to <signal>`.
- I/O standard: `set_instance_assignment -name IO_STANDARD "3.3-V LVTTL" -to <signal>`.
- Use `quartus_sta` for timing analysis; `quartus_pgm` for device programming.
- Use `.qsf` (Quartus Settings File) for all project settings; keep it in version control.
- Enable `quartus_sh --determine_smart_action` to check if recompilation is needed.
""",
    "diamondc": """\
## Lattice Diamond Rules
- Synthesis script: use `prj_project open <project>.ldf` then `prj_run Synthesis -impl impl1`.
- Constraints go in `.lpf` (Lattice Preference File); pin LOC and IOSTANDARD assignment there.
  Example: `LOCATE COMP "clk" SITE "P3"; IOBUF PORT "clk" IO_TYPE=LVCMOS33;`
- Use `prj_run PAR -impl impl1` for place-and-route; `prj_run Export -impl impl1` for bitfile.
- For Radiant (ECP5/NX devices), prefer the Radiant Tcl API over Diamond.
- Timing analysis: run `trce -v 12 -o timing_report.txt <design>.ncd <design>.pct`.
""",
    # ── Python tooling ───────────────────────────────────────────────────────
    "ruff": """\
## Ruff (Python Linter & Formatter) Rules
- Configuration lives in `pyproject.toml` under `[tool.ruff]` and `[tool.ruff.lint]`.
- Recommended base selection: `select = ["E", "F", "I", "N", "UP", "B"]`.
- Per-file suppression: `# noqa: E501` or `# noqa: E501,F401` on the offending line.
- File-level suppression: add file pattern to `[tool.ruff.lint.per-file-ignores]`.
- Auto-fix: `ruff check --fix .` (safe fixes only). `--unsafe-fixes` for more.
- Format: `ruff format .` (Black-compatible). Use `ruff format --check .` in CI.
- Never suppress `F8xx` (undefined name / redefined) — these are real bugs.
- `ruff check --select ALL` to discover all available rules before choosing.
""",
    "mypy": """\
## Mypy (Python Type Checker) Rules
- Inline suppression: `# type: ignore[error-code]` — always specify the error code.
- Use `from __future__ import annotations` at top of file for forward reference syntax.
- Guard circular-import type annotations: `from typing import TYPE_CHECKING; if TYPE_CHECKING: import X`.
- `reveal_type(expr)` to inspect inferred types interactively; remove before committing.
- Strict mode: `mypy --strict` or `[tool.mypy] strict = true` — recommended for new projects.
- Stubs for third-party libraries: install `types-<package>` or add to `[[tool.mypy.overrides]] ignore_missing_imports = true`.
- `cast(T, expr)` to assert a type the checker can't infer; use sparingly.
- `Any` is an escape hatch — minimize its use; prefer `object` or proper generics.
""",
    "pytest": """\
## pytest Rules
- Fixtures are declared with `@pytest.fixture(scope="function"|"class"|"module"|"session")`.
- Use `tmp_path` (function-scoped) for temporary files — never hardcode `/tmp`.
- `capsys` captures stdout/stderr; `caplog` captures log output.
- `monkeypatch` for patching attributes, env vars, and builtins without permanent side-effects.
- Parametrize: `@pytest.mark.parametrize("x,y,expected", [(1,1,2),(2,3,5)])`.
- Group shared fixtures in `conftest.py` at the relevant directory level.
- Use `pytest.raises(ExceptionType)` as a context manager to assert exceptions.
- Mark slow tests: `@pytest.mark.slow` and run fast suite with `-m "not slow"`.
- `pytest -x` stops on first failure; `-v` shows full test names; `--tb=short` for concise tracebacks.
""",
    # ── C / C++ tooling ─────────────────────────────────────────────────────
    "clang-tidy": """\
## clang-tidy Rules
- Config lives in `.clang-tidy` YAML at the project root; `Checks:` field enables/disables checks.
- Recommended baseline: `Checks: "modernize-*,bugprone-*,cppcoreguidelines-*,readability-*,-readability-magic-numbers"`.
- Inline suppression: `// NOLINT(check-name)` or `// NOLINT` for the whole line.
- File-level suppression: `// NOLINTBEGIN(check-name)` … `// NOLINTEND(check-name)`.
- Run: `clang-tidy <files> -- -std=c++17 -I<includes>` (pass compiler flags after `--`).
- For CMake projects: `cmake -DCMAKE_EXPORT_COMPILE_COMMANDS=ON` to generate `compile_commands.json`.
- Use `--fix` to apply auto-fixable suggestions; review diffs before committing.
- `cppcoreguidelines-avoid-c-arrays` → replace C arrays with `std::array` or `std::vector`.
- `modernize-use-nullptr` → replace `NULL` with `nullptr`.
""",
    "cppcheck": """\
## cppcheck Rules
- Run: `cppcheck --enable=all --suppress=missingIncludeSystem <path>`.
- Use `--suppress=<id>:<file>:<line>` for targeted suppression, or `// cppcheck-suppress <id>` inline.
- Enable specific checks: `--enable=style,performance,portability,unusedFunction`.
- Use `--project=compile_commands.json` for CMake-based projects.
- `--error-exitcode=1` makes CI fail on errors (not just warnings).
- Suppressions file: `--suppressions-list=.cppcheck-suppressions`.
""",
    # ── Rust tooling ─────────────────────────────────────────────────────────
    "cargo": """\
## Cargo / Rust Build Rules
- `cargo clippy -- -D warnings` treats all Clippy warnings as errors (use in CI).
- `#[allow(clippy::lint_name)]` for targeted suppression; `#![allow(...)]` for whole module.
- `clippy.toml` (or `[lints.clippy]` in `Cargo.toml`) for project-wide Clippy config.
- Avoid `unwrap()` in library code; prefer `expect("context")` or proper `?` propagation.
- Prefer `cargo fmt --check` in CI; `cargo fmt` locally to auto-format.
- `cargo audit` checks for known security vulnerabilities in dependencies.
- `cargo test -- --nocapture` to see println! output during tests.
- Use `cargo build --release` for performance-critical builds; debug builds skip optimizations.
""",
    # ── Go tooling ────────────────────────────────────────────────────────────
    "go": """\
## Go Build & Vet Rules
- `go vet ./...` catches common mistakes (e.g. printf format mismatches, unreachable code).
- `go test ./...` runs all tests; `-race` enables the data-race detector.
- `gofmt -l .` lists files needing formatting; `gofmt -w .` applies formatting.
- `golangci-lint run` runs a curated set of linters (configure via `.golangci.yml`).
- Error handling: always check returned errors; do not use `_` for error values in production.
- Prefer explicit context propagation (`context.Context`) over goroutine-local state.
- `go mod tidy` removes unused and adds missing dependencies.
""",
    "golangci-lint": """\
## golangci-lint Rules
- Config file: `.golangci.yml` at the project root.
- Recommended linters: `errcheck`, `gosimple`, `govet`, `ineffassign`, `staticcheck`, `unused`.
- Enable with `linters: enable: [errcheck, gosimple, govet, ...]` or `enable-all: false`.
- Inline suppression: `//nolint:linter-name` or `//nolint:linter1,linter2`.
- File-level: `//nolint:linter-name` at the top of the file.
- Auto-fix: `golangci-lint run --fix` for fixable issues.
- Use `golangci-lint run --timeout 5m` for large projects.
""",
    # ── DevOps / IaC ─────────────────────────────────────────────────────────
    "terraform": """\
## Terraform / OpenTofu Rules
- `terraform fmt -recursive` auto-formats all `.tf` files; check with `terraform fmt -check`.
- `terraform validate` checks syntax and internal consistency without hitting cloud APIs.
- `tflint` lints provider-specific issues (e.g. invalid AWS instance types).
- `tfsec` / `checkov` scan for security misconfigurations.
- Pin provider versions: `required_providers { aws = { source = "hashicorp/aws" version = "~> 5.0" } }`.
- Use `terraform workspace` for environment separation; prefer modules for reusability.
- State backend: use remote state (S3/GCS/Terraform Cloud) — never commit `.tfstate` files.
- `terraform plan -out=plan.tfplan` saves a plan; `terraform apply plan.tfplan` applies it deterministically.
""",
    # ── Embedded Linux / Yocto ───────────────────────────────────────────────
    "oelint-adv": """\
## oelint-adv (BitBake/Yocto Recipe Linter) Rules
- Run: `oelint-adv <recipe.bb>` or `oelint-adv --fix <recipe.bb>` for auto-fixes.
- Configure with `--rulefile <rules.json>` for project-specific rule sets.
- Common rules: `oelint.vars.mand` (mandatory variables), `oelint.task.heredoc` (heredoc style).
- Recipe variables `DESCRIPTION`, `LICENSE`, `LIC_FILES_CHKSUM` are mandatory for all recipes.
- Use `do_install:append()` / `do_compile:prepend()` override syntax (not `_append` — deprecated in Kirkstone+).
- Keep `SRC_URI` checksums (`SRC_URI[sha256sum]`) up-to-date after source changes.
- `RDEPENDS` for runtime dependencies, `DEPENDS` for build-time; don't mix them.
- File paths in recipes must use `${D}` for the destination dir and `${S}` for source.
""",
    "bitbake": """\
## BitBake Build System Rules
- Run only inside a Yocto build environment (`source oe-init-build-env`).
- `bitbake <target>` builds; `bitbake -c clean <target>` cleans; `bitbake -c devshell <target>` opens dev shell.
- `bitbake -e <target> | grep "^<VAR>"` inspects resolved variable values.
- `bitbake -c listtasks <target>` lists all tasks for a recipe.
- `bitbake world` builds everything — rarely needed; use specific image targets instead.
- Layer priorities in `bblayers.conf`; higher priority layers override lower ones.
- Never edit files inside `tmp/` — changes are lost on next build. Edit recipes or `bbappend` files instead.
- `devtool modify <recipe>` creates an editable workspace for a recipe.
""",
    # ── VCS / Workflow ────────────────────────────────────────────────────────
    "git": """\
## Git / Conventional Commits Rules
- Commit format: `<type>(<scope>): <description>` — types: feat, fix, docs, style, refactor, test, chore, ci.
- Subject line ≤ 72 characters; body wrapped at 100 characters.
- Breaking changes: add `BREAKING CHANGE:` footer or `!` after type (e.g. `feat!: ...`).
- Branching (GitFlow): feature branches off `develop`; hotfix/release branches off `main`.
- Never force-push to `main` or `develop`; use `--force-with-lease` on feature branches.
- Sign commits with GPG for sensitive repositories: `git commit -S`.
- `git rebase -i HEAD~N` to squash/edit commits before PR; keep history clean.
- Tag releases with annotated tags: `git tag -a v1.0.0 -m "Release v1.0.0"`.
""",
    # ── Container tooling ────────────────────────────────────────────────────
    "docker": """\
## Docker / Dockerfile Rules
- Use multi-stage builds to minimize final image size (builder → runtime stages).
- Pin base image versions: `FROM python:3.12-slim` not `FROM python:latest`.
- Combine `RUN` commands into single layers to reduce image size and cache misses.
- Run containers as a non-root user: `RUN useradd -m app && USER app`.
- Copy only necessary files: use `.dockerignore` to exclude `.git`, `node_modules`, etc.
- `COPY` before `RUN pip install` so the install layer is cached when only source changes.
- Health checks: `HEALTHCHECK CMD curl -f http://localhost/health || exit 1`.
- `--no-cache` flag in CI prevents stale cache: `docker build --no-cache`.
- Scan images with `docker scout cves` or `trivy image` before publishing.
""",
    # ── Documentation tooling ────────────────────────────────────────────────
    "vale": """\
## Vale (Prose Linter) Rules
- Config in `.vale.ini` at the project root; `StylesPath = .vale/styles` for custom styles.
- Install style packages: `vale sync` downloads configured packages (e.g., Google, Microsoft).
- Inline suppression: `<!-- vale off -->` … `<!-- vale on -->` in Markdown/HTML.
- For RST: `.. vale off` … `.. vale on`.
- Common styles to enable: `Google`, `proselint`, `write-good`.
- Run: `vale <file>` or `vale --glob='*.md' .` for all Markdown files.
- `vale --output=line` for CI-friendly single-line output.
""",
    "markdownlint": """\
## markdownlint Rules
- Config in `.markdownlint.json` or `.markdownlint.yaml`.
- Inline suppression: `<!-- markdownlint-disable MD013 -->` … `<!-- markdownlint-enable MD013 -->`.
- Common rules to relax: `MD013` (line length — set to 120+), `MD033` (inline HTML if needed).
- `markdownlint-cli2 --fix "**/*.md"` applies auto-fixable corrections.
- Keep headings sequential (no skipping H2 → H4); use ATX-style headings (`##` not underline).
""",
    # ── API tooling ──────────────────────────────────────────────────────────
    "spectral": """\
## Spectral (OpenAPI Linter) Rules
- Config in `.spectral.yaml` or `.spectral.json` at the project root.
- Built-in ruleset: `extends: ["spectral:oas"]` for OpenAPI 2/3 validation.
- Custom rules use the `rules:` key with `given`, `then`, `severity`.
- Severity levels: `error`, `warn`, `info`, `hint` — only `error` fails by default in CI.
- Run: `spectral lint openapi.yaml` or `spectral lint --ruleset .spectral.yaml openapi.yaml`.
- All paths should have `operationId`; all schemas should have `description`.
- `$ref` loops cause infinite recursion — use `spectral lint --fail-severity warn` to catch early.
""",
}

# ---------------------------------------------------------------------------
# Project-type → tool-key mappings
# These determine which rules to inject based on project configuration.
# ---------------------------------------------------------------------------

_TYPE_TOOL_KEYS: dict[str, list[str]] = {
    "fpga-rtl": ["ghdl", "iverilog", "verilator", "vsg", "yosys", "git"],
    "fpga-rtl-amd": ["ghdl", "iverilog", "verilator", "vsg", "vivado", "git"],
    "fpga-rtl-xilinx": ["ghdl", "iverilog", "verilator", "vsg", "vivado", "git"],
    "fpga-rtl-intel": ["ghdl", "iverilog", "verilator", "vsg", "quartus_sh", "git"],
    "fpga-rtl-lattice": ["ghdl", "iverilog", "verilator", "vsg", "diamondc", "git"],
    "mixed-fpga-embedded": ["ghdl", "verilator", "vsg", "clang-tidy", "cppcheck", "git"],
    "mixed-fpga-firmware": ["ghdl", "verilator", "vsg", "ruff", "mypy", "pytest", "git"],
    "cli-python": ["ruff", "mypy", "pytest", "git"],
    "library-python": ["ruff", "mypy", "pytest", "git"],
    "backend-frontend": ["ruff", "mypy", "pytest", "git"],
    "backend-frontend-tray": ["ruff", "mypy", "pytest", "git"],
    "cli-rust": ["cargo", "git"],
    "library-rust": ["cargo", "git"],
    "cli-go": ["go", "golangci-lint", "git"],
    "cli-c": ["clang-tidy", "cppcheck", "git"],
    "library-c": ["clang-tidy", "cppcheck", "git"],
    "embedded-hardware": ["clang-tidy", "cppcheck", "git"],
    "yocto-bsp": ["bitbake", "oelint-adv", "git"],
    "devops-iac": ["terraform", "docker", "git"],
    "microservices": ["docker", "ruff", "pytest", "git"],
    "data-ml": ["ruff", "mypy", "pytest", "git"],
    "spec-document": ["vale", "markdownlint", "git"],
    "user-manual": ["vale", "markdownlint", "git"],
    "api-specification": ["spectral", "git"],
    "web-frontend": ["git"],
    "fullstack-js": ["git"],
    "epistemic-pipeline": ["ruff", "mypy", "pytest", "git"],
    "knowledge-engineering": ["ruff", "mypy", "pytest", "git"],
    "aee-research": ["ruff", "git"],
}

# FPGA tool chip name → rule key mapping
_FPGA_CHIP_TO_KEY: dict[str, str] = {
    "vivado": "vivado",
    "quartus": "quartus_sh",
    "diamond": "diamondc",
    "radiant": "diamondc",
    "ghdl": "ghdl",
    "iverilog": "iverilog",
    "verilator": "verilator",
    "vsg": "vsg",
    "yosys": "yosys",
    "symbiyosys": "symbiyosys",
    "oelint-adv": "oelint-adv",
}


def get_rules_for_tools(tool_keys: list[str]) -> str:
    """Return concatenated rules text for a list of tool keys.

    Missing keys are silently ignored.
    """
    parts: list[str] = []
    seen: set[str] = set()
    for key in tool_keys:
        if key in TOOL_RULES and key not in seen:
            seen.add(key)
            parts.append(TOOL_RULES[key])
    return "\n".join(parts)


def get_rules_for_project(
    project_type: str,
    fpga_tools: list[str] | None = None,
    max_chars: int = 6000,
) -> str:
    """Build tool rules context for a project.

    Combines type-based defaults with any explicitly listed fpga_tools from
    scaffold.yml.  Truncates to *max_chars* to avoid bloating the system prompt.

    Returns an empty string if no rules apply.
    """
    tool_keys: list[str] = list(_TYPE_TOOL_KEYS.get(project_type, ["git"]))

    # Add rules for FPGA tools explicitly listed in scaffold.yml
    if fpga_tools:
        for chip in fpga_tools:
            key = _FPGA_CHIP_TO_KEY.get(chip)
            if key and key not in tool_keys:
                tool_keys.append(key)

    if not tool_keys:
        return ""

    raw = get_rules_for_tools(tool_keys)
    if len(raw) <= max_chars:
        return raw

    # Truncate with a note
    return raw[:max_chars] + "\n…(tool rules truncated — see specsmith toolrules for full text)\n"
