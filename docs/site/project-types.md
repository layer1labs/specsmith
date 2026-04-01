# Project Types

specsmith supports 30 project types organized into six categories.

## Software — Python

| Type | Key | Verification Tools |
|------|-----|-------------------|
| Python backend + web frontend | `backend-frontend` | ruff, mypy, pytest, pip-audit, eslint, vitest |
| Python backend + frontend + tray | `backend-frontend-tray` | ruff, mypy, pytest, pip-audit, eslint, vitest |
| CLI tool (Python) | `cli-python` | ruff, mypy, pytest, pip-audit |
| Library / SDK (Python) | `library-python` | ruff, mypy, pytest, pip-audit |

## Software — Systems Languages

| Type | Key | Verification Tools |
|------|-----|-------------------|
| CLI tool (Rust) | `cli-rust` | clippy, cargo check/test/audit, rustfmt |
| Library / crate (Rust) | `library-rust` | clippy, cargo check/test/audit, rustfmt |
| CLI tool (Go) | `cli-go` | golangci-lint, go vet, go test, govulncheck, gofmt |
| CLI tool (C/C++) | `cli-c` | clang-tidy, cppcheck, ctest, flawfinder, clang-format |
| Library (C/C++) | `library-c` | clang-tidy, cppcheck, ctest, flawfinder, clang-format |
| .NET / C# application | `dotnet-app` | dotnet format, dotnet test, dotnet audit |

## Software — Web / Mobile / Infra

| Type | Key | Verification Tools |
|------|-----|-------------------|
| Web frontend (SPA) | `web-frontend` | eslint, tsc, vitest, npm audit, prettier |
| Fullstack JS/TS | `fullstack-js` | eslint, tsc, vitest, jest, npm audit, prettier |
| Mobile app | `mobile-app` | flutter analyze, eslint, flutter test, jest |
| Browser extension | `browser-extension` | eslint, web-ext lint, tsc, vitest, web-ext build |
| Monorepo (multi-package) | `monorepo` | eslint, ruff, nx/turbo test, npm audit, pip-audit |
| Microservices | `microservices` | ruff, eslint, pytest, jest, docker compose build |
| DevOps / IaC | `devops-iac` | tflint, ansible-lint, terratest, tfsec, checkov |
| Data / ML pipeline | `data-ml` | ruff, mypy, pytest, pip-audit |

## Hardware / Embedded

| Type | Key | Verification Tools |
|------|-----|-------------------|
| Embedded / hardware | `embedded-hardware` | clang-tidy, cppcheck, ctest, flawfinder, MISRA-C |
| FPGA / RTL | `fpga-rtl` | vsg, verilator, ghdl, cocotb, vivado, quartus |
| Yocto / embedded Linux BSP | `yocto-bsp` | oelint-adv, bitbake, kas build |
| PCB / hardware design | `pcb-hardware` | DRC, ERC, kicad-cli, BOM validate |

## Document / Knowledge

| Type | Key | Verification Tools |
|------|-----|-------------------|
| Technical specification | `spec-document` | vale, markdownlint, cspell, pandoc, mkdocs |
| User manual / documentation | `user-manual` | vale, markdownlint, cspell, sphinx, mkdocs |
| Research paper / white paper | `research-paper` | vale, cspell, chktex, pdflatex, bibtex |
| API specification | `api-specification` | spectral, buf lint, schemathesis, dredd, openapi-generator |
| Requirements management | `requirements-mgmt` | vale, markdownlint, prettier, req-trace |

## Business / Legal

| Type | Key | Verification Tools |
|------|-----|-------------------|
| Business plan / proposal | `business-plan` | vale, cspell, prettier, pandoc |
| Patent application | `patent-application` | vale, cspell, prettier, pandoc, claim-ref-check |
| Legal / compliance | `legal-compliance` | vale, cspell, prettier, pandoc, regulation-ref-check |

Each type gets:

- **Type-specific directory structure** (e.g., `claims/`, `specification/`, `prior-art/` for patents)
- **AGENTS.md governance rules** tailored to the domain
- **CI config** with the correct verification tools
- **Domain-specific REQUIREMENTS.md and TEST_SPEC.md starters** (e.g., claim validation for patents, citation integrity for research papers)
