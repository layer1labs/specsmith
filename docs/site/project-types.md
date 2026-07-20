# Project Types

specsmith supports **64 project types** across eleven categories. Each type determines:

- **Directory structure** — what directories and .gitkeep files are created
- **Verification tools** — what lint/test/security/build tools are configured in CI
- **Governance rules** — what type-specific rules appear in AGENTS.md
- **Template starters** — what domain-specific requirements and tests are pre-populated
- **CI config** — what GitHub Actions setup steps, Docker images, and cache keys are used
- **.gitignore** — what type-specific ignore patterns are included

## Software — Python

| Type | Key | Lint | Test | Security |
|------|-----|------|------|----------|
| Python backend + web frontend | `backend-frontend` | ruff, eslint | pytest, vitest | pip-audit, npm audit |
| Python backend + frontend + tray | `backend-frontend-tray` | ruff, eslint | pytest, vitest | pip-audit, npm audit |
| CLI tool (Python) | `cli-python` | ruff | pytest | pip-audit |
| Library / SDK (Python) | `library-python` | ruff | pytest | pip-audit |

**Directory structure (cli-python):** `src/{package}/`, `src/{package}/commands/`, `src/{package}/utils/`, `tests/`

**Governance rules:** CLI must have `--help` for all commands. Exit codes must be documented and tested. Cross-platform rules apply.

## Software — Systems Languages

| Type | Key | Lint | Test | Security |
|------|-----|------|------|----------|
| CLI tool (Rust) | `cli-rust` | cargo clippy | cargo test | cargo audit |
| Library / crate (Rust) | `library-rust` | cargo clippy | cargo test | cargo audit |
| CLI tool (Go) | `cli-go` | golangci-lint | go test | govulncheck |
| CLI tool (C/C++) | `cli-c` | clang-tidy | ctest | flawfinder |
| Library (C/C++) | `library-c` | clang-tidy | ctest | flawfinder |
| .NET / C# application | `dotnet-app` | dotnet format | dotnet test | dotnet audit |

**Rust governance rules:** `cargo clippy` must pass with no warnings. All public APIs must have doc comments. `cargo audit` must pass in CI.

**C/C++ governance rules:** MISRA-C compliance rules apply where annotated. `clang-tidy` and `cppcheck` must pass. Memory safety must be verified.

## Software — Web / Mobile / Infra

| Type | Key | Lint | Test | Build |
|------|-----|------|------|-------|
| Web frontend (SPA) | `web-frontend` | eslint | vitest | — |
| Fullstack JS/TS | `fullstack-js` | eslint | vitest, jest | — |
| Mobile app | `mobile-app` | flutter analyze | flutter test | flutter build |
| Browser extension | `browser-extension` | eslint, web-ext lint | vitest | web-ext build |
| Monorepo | `monorepo` | eslint, ruff | nx/turbo test | nx/turbo build |
| Microservices | `microservices` | ruff, eslint | pytest, jest | docker compose |
| DevOps / IaC | `devops-iac` | tflint, ansible-lint | terratest | — |
| Data / ML pipeline | `data-ml` | ruff | pytest | — |

**DevOps governance rules:** Security scanning (tfsec/checkov) is mandatory. State files must never be committed. Infrastructure changes require proposals.

## Hardware / Embedded

| Type | Key | Lint | Test | Build |
|------|-----|------|------|-------|
| Embedded / hardware | `embedded-hardware` | clang-tidy | ctest, unity | cmake |
| FPGA / RTL | `fpga-rtl` | vsg, verilator | ghdl, cocotb | vivado, quartus |
| Yocto / embedded Linux BSP | `yocto-bsp` | oelint-adv | bitbake | kas build |
| PCB / hardware design | `pcb-hardware` | — | DRC, ERC | kicad-cli |

**FPGA governance rules:** Tool invocations MUST use batch/non-interactive modes only. Constraint files (.xdc, .sdc) are governance artifacts. Timing closure is a formal milestone.

**PCB governance rules:** BOM files are governance artifacts. Schematic review is a formal gate before layout. ECAD-MCAD sync points must be documented.

## Document / Knowledge

| Type | Key | Lint | Test | Build |
|------|-----|------|------|-------|
| Technical specification | `spec-document` | vale, markdownlint, cspell | markdown-link-check | pandoc, mkdocs |
| User manual | `user-manual` | vale, markdownlint, cspell | markdown-link-check | sphinx, mkdocs |
| Research paper | `research-paper` | vale, cspell, chktex | — | pdflatex, bibtex |
| API specification | `api-specification` | spectral, buf lint | schemathesis, dredd | openapi-generator |
| Requirements management | `requirements-mgmt` | vale, markdownlint | req-trace | — |

**Research paper governance rules:** Citation integrity must be maintained — all `\cite{}` must resolve. Data and figures must be reproducible. LaTeX must compile clean.

**API specification governance rules:** API specs are governance artifacts. Breaking changes require proposals and version bumps. Generated code must not be manually edited.

**Template starters for spec-document/user-manual:** Pre-populated with REQ-DOC-001 (precise language) and REQ-REF-001 (cross-reference validation).

## Modern Web Frameworks

| Type | Key | Lint | Test | Build |
|------|-----|------|------|-------|
| Next.js app (React + SSR/SSG) | `nextjs-app` | eslint, next lint | jest, vitest, playwright | next build |
| Nuxt.js app (Vue + SSR/SSG) | `nuxt-app` | eslint | vitest, playwright | nuxt build |
| SvelteKit app | `sveltekit-app` | eslint | vitest, playwright | vite build |
| Remix full-stack React app | `remix-app` | eslint | vitest, playwright | remix vite:build |
| Astro site (static / SSR) | `astro-site` | eslint | vitest, playwright | astro build |

**Governance rules:** TypeScript strict mode required. SSR components must not import client-only APIs at the module level. Data fetching must be idempotent (safe to re-run on reconnect).

## Python — Extended Types

| Type | Key | Lint | Test | Notes |
|------|-----|------|------|-------|
| Embedded Python HMI / kiosk | `embedded-python-hmi` | ruff | pytest | Hardware-interfacing PySide6/Qt apps |
| Research Python | `research-python` | ruff | pytest | Experiment packages, no CLI distribution |

## Safety-Critical Embedded

| Type | Key | Lint | Test | Compliance |
|------|-----|------|------|------------|
| Safety-critical embedded | `safety-critical` | clang-tidy, cppcheck | ctest, west twister | misra-c, polyspace |

**Governance rules:** IEC 60204-1 / IEC 62061 / IEC 61508 compliance. All safety-critical functions require formal verification or thorough code review. MISRA-C annotations mandatory.

## Hardware / Embedded — Vendor-Specific FPGA

In addition to the generic `fpga-rtl` type, vendor-specific types set the correct toolchain:

| Type | Key | Build tool |
|------|-----|------------|
| AMD Adaptive Computing (Vivado) | `fpga-rtl-amd` | vivado -mode batch |
| Intel/Altera Quartus Prime | `fpga-rtl-intel` | quartus_sh --flow compile |
| Lattice Diamond / Radiant | `fpga-rtl-lattice` | diamondc |
| FPGA + Embedded C/C++ drivers | `mixed-fpga-embedded` | vivado + cmake |
| FPGA + Python/C verification | `mixed-fpga-firmware` | vivado + pytest |

**Scaffold behaviour:** These types are in `_EXPLICIT_ONLY_TYPES` — auto-detection is bypassed when the type is set explicitly, so auxiliary Python tooling never triggers a false-positive type mismatch.

## IP / Patent Prosecution

| Type | Key | Lint | Compliance |
|------|-----|------|------------|
| Patent prosecution repository | `patent-prosecution` | vale, cspell | specsmith audit, claim-ref-check |

**Governance rules:** Integrates with USPTO MCP and prior-art research workflows. All claim changes require a preflight with explicit epistemic boundaries. See the `patent-prosecution-workflow` skill.

## AI / LLM / Agents

Specialized types for AI/agent projects. All use Python tooling (ruff, mypy, pytest, pip-audit). Auto-detection via dependency analysis: crewai/langgraph → `agent-orchestration`, chromadb/faiss → `rag-pipeline`, mlflow/bentoml → `mlops-platform`, mcp package → `mcp-server`.

| Type | Key | Key tools/frameworks |
|------|-----|---------------------|
| LLM-powered application | `llm-app` | LangChain, LlamaIndex, Haystack, Anthropic/OpenAI SDK |
| Multi-agent orchestration | `agent-orchestration` | AutoGen, CrewAI, LangGraph, Swarm |
| MCP server | `mcp-server` | FastMCP, mcp Python SDK |
| RAG / embedding pipeline | `rag-pipeline` | ChromaDB, FAISS, Pinecone, Weaviate, pgvector |
| MLOps platform | `mlops-platform` | MLflow, BentoML, Ray Serve, Kubeflow, Prefect |

**Governance rules:** All AI types include `_EXPLICIT_ONLY_TYPES` membership — explicit type declaration overrides auto-detection. MCP servers must expose tool descriptions that include trigger conditions. LLM apps must version system prompts as governed artifacts.

**Directory structure (llm-app):** `src/{package}/agents/`, `src/{package}/tools/`, `src/{package}/prompts/`, `tests/`

**Directory structure (mcp-server):** `src/{package}/tools/`, `src/{package}/resources/`, `tests/`

**Directory structure (rag-pipeline):** `src/{package}/ingestion/`, `src/{package}/retrieval/`, `src/{package}/generation/`, `data/`, `tests/`

## JVM

| Type | Key | Lint | Test | Build |
|------|-----|------|------|-------|
| Spring Boot application | `java-spring` | checkstyle, pmd | mvn test / ./gradlew test | mvn package |
| Java library / SDK | `java-library` | checkstyle | mvn test / ./gradlew test | mvn package |

**Detection:** `pom.xml` or `build.gradle` with `spring-boot` → `java-spring`. Any `.java`-primary project without Spring → `java-library`.

**Directory structure:** `src/main/java/`, `src/main/resources/`, `src/test/java/`

## Infrastructure / Cloud

| Type | Key | Lint | Test | Notes |
|------|-----|------|------|-------|
| Serverless / FaaS | `serverless` | eslint, ruff | jest, pytest | Lambda, GCP Functions, Cloudflare Workers |
| Kubernetes operator | `kubernetes-operator` | golangci-lint | go test | CRDs, controllers; uses Go toolchain |
| Streaming data pipeline | `streaming-pipeline` | ruff | pytest | Kafka, Flink, Beam, Spark Streaming |
| Data warehouse | `data-warehouse` | sqlfluff lint | dbt test | dbt, Snowflake, BigQuery, Redshift |

**Detection:** `serverless.yml` / `wrangler.toml` → `serverless`. `dbt_project.yml` → `data-warehouse`. Go + `controllers/` dir → `kubernetes-operator`.

**Directory structure (kubernetes-operator):** `cmd/manager/`, `controllers/`, `api/v1alpha1/`, `config/crd/`, `config/rbac/`, `tests/e2e/`

**Directory structure (data-warehouse):** `models/staging/`, `models/intermediate/`, `models/marts/`, `macros/`, `seeds/`, `tests/`, `analyses/`

## Game Development

| Type | Key | Lint | Test | Build |
|------|-----|------|------|-------|
| Unity game | `game-unity` | — | unity-test-runner | unity -batchmode |
| Godot game | `game-godot` | gdlint | godot --headless | godot --export-release |

**Detection:** `project.godot` file → `game-godot`. `Assets/` directory with `.unity` files → `game-unity`.

**Directory structure (game-unity):** `Assets/Scripts/`, `Assets/Scenes/`, `Assets/Prefabs/`, `Assets/Materials/`, `Assets/Tests/`

**Directory structure (game-godot):** `scenes/`, `scripts/`, `assets/sprites/`, `assets/audio/`, `tests/`

## Web3 / Blockchain

| Type | Key | Lint | Test | Build | Security |
|------|-----|------|------|-------|----------|
| Solidity / EVM smart contracts | `smart-contract` | solhint | hardhat test, forge test | hardhat compile | slither, mythril |

**Detection:** `.sol` files as primary language, or `hardhat` / `ethers` / `solidity` in `package.json`.

**Directory structure:** `contracts/`, `contracts/interfaces/`, `scripts/`, `test/`, `deployments/`

**Governance rules:** Every contract change requires a preflight. Security audit (slither/mythril) must pass before deployment. Deployed contract addresses are governance artifacts.

## Desktop Applications

| Type | Key | Lint | Test | Build |
|------|-----|------|------|-------|
| Electron desktop app | `desktop-electron` | eslint | jest, playwright | electron-builder |
| Tauri desktop app (Rust + WebView) | `desktop-tauri` | cargo clippy, eslint | cargo test, vitest | cargo tauri build |

**Detection:** `electron` in `package.json` → `desktop-electron`. `src-tauri/` directory → `desktop-tauri`.

**Governance rules (desktop-electron):** `electronegativity` security scan required. `contextIsolation: true` and `nodeIntegration: false` are enforced governance requirements.

## Business / Legal

| Type | Key | Lint | Build | Compliance |
|------|-----|------|-------|------------|
| Business plan | `business-plan` | vale, cspell | pandoc | — |
| Patent application | `patent-application` | vale, cspell | pandoc | claim-ref-check |
| Legal / compliance | `legal-compliance` | vale, cspell | pandoc | regulation-ref-check |

**Patent governance rules:** Claims are governance artifacts — ALL changes require proposals. Independent claims must be self-contained. Prior art references must include publication dates. Figures must be numbered and referenced. Claim dependency chains must be validated.

**Template starters for patent-application:** Pre-populated with REQ-CLM-001 (self-contained claims), REQ-SPEC-001 (enablement), REQ-FIG-001 (figure references), and corresponding test stubs.

**Legal governance rules:** All document changes must be tracked with version history. Regulatory references must include jurisdiction and effective date. Approval workflows are mandatory before publication.

**Directory structure (patent-application):** `claims/`, `specification/`, `figures/`, `prior-art/`, `correspondence/`

**Directory structure (legal-compliance):** `contracts/`, `policies/`, `templates/`, `evidence/`, `audit-trail/`
