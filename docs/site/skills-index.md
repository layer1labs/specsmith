# Built-in Skills Index

specsmith ships with **136 built-in skills** across 16 domains.
Each skill is a curated `SKILL.md` injected into the agent context with
`specsmith skill activate <slug>` or auto-matched by project type.

!!! tip "Using skills"
    ```bash
    specsmith skills list                  # list all skills
    specsmith skills list --domain docs    # filter by domain
    specsmith skill activate mkdocs        # inject into .agents/skills/
    specsmith skills search "vivado"       # search by keyword
    ```

    In the REPL: `/skill mkdocs` to load a skill mid-session.

---

## Governance (20)

Skills for project governance workflows, verification, release management, ESDB, CI polling, IP prosecution, and AI code review.

| Slug | Name | Key tags |
|------|------|----------|
| `aider-integration` | Aider — specsmith governance integration | aider, integration, governance, session, git |
| `chronomemory-esdb` | ChronoMemory ESDB — epistemic state database (v0.1.1) | esdb, chronomemory, wal, query, context-pack |
| `claude-code-integration` | Claude Code — specsmith governance integration | claude-code, mcp, integration, governance, session |
| `codity-ai-review` | Codity.ai AI Review — staged-diff code review, security scan, test-gen | codity, ai-review, code-review, security, pre-commit |
| `copilot-integration` | GitHub Copilot — specsmith governance integration | copilot, github, integration, governance, session |
| `cursor-integration` | Cursor — specsmith governance integration | cursor, mcp, integration, governance, session |
| `diff-reviewer` | Diff Reviewer — surface changes for approval | git, review, pr |
| `gemini-cli-integration` | Gemini CLI — specsmith governance integration | gemini, google, integration, governance, session |
| `gh-ci-polling` | GitHub Actions CI polling — smart wait (no sleep) | ci, gh, polling, github-actions |
| `issue-triage` | Issue Triage — classify and prioritise GitHub issues | github, issues, labels |
| `onboarding-coach` | Onboarding Coach — guided first session | onboarding, first-run |
| `patent-prosecution-workflow` | Patent Prosecution Workflow — prior-art, USPTO MCP, PAR | patent, uspto, ppubs, claim-themes, ip |
| `planner` | Planner — propose-then-execute | planning, aee, governance |
| `release-pilot` | Release Pilot — gitflow release cut | git, semver, release, gitflow |
| `specsmith` | Specsmith — master governance CLI reference | specsmith, aee, session, audit, phase |
| `specsmith-audit` | Specsmith Audit — drift detection and governance health | specsmith, audit, drift, health, aee |
| `specsmith-save` | Specsmith Save — governance-aware save workflow | specsmith, save, commit, esdb, backup |
| `specsmith-session-governance` | Specsmith Session Governance — drift prevention, heartbeat, preflight gate | governance, session, drift, checkpoint, anchor |
| `verifier` | Verifier — five-gate verification | audit, tests, verification |
| `windsurf-integration` | Windsurf — specsmith governance integration | windsurf, mcp, integration, governance, session |

---

## Documentation (10) — H23/H24

Documentation systems covered by governance rules H23 and H24.
Default recommendations by language/stack:

| Stack | Recommended skill |
|-------|-------------------|
| Python | `mkdocs` (narrative docs) + `sphinx` (API docs) |
| Rust library | `rustdoc` |
| Rust app | `mdbook` |
| C/C++ | `doxygen` |
| JavaScript | `jsdoc` |
| TypeScript | `typedoc` |
| Java / Kotlin | `javadoc` |
| REST API | `openapi` |
| Any project (bare minimum) | `user-manual-md` |

| Slug | Name | Key tags |
|------|------|----------|
| `doxygen` | Doxygen — C/C++ API docs, Doxyfile, HTML + LaTeX | c, cpp, api-docs, graphviz |
| `javadoc` | Javadoc / Dokka — Java and Kotlin API docs | java, kotlin, gradle |
| `jsdoc` | JSDoc — JavaScript API docs, @param/@returns | javascript, nodejs |
| `mdbook` | mdBook — Rust book-format docs, GitHub Pages | rust, markdown, github-pages |
| `mkdocs` | MkDocs — Material theme, RTD deploy, nav | python, readthedocs, material |
| `openapi` | OpenAPI / Swagger — REST API specs, validation | rest, swagger, codegen |
| `rustdoc` | rustdoc — cargo doc, docs.rs, doctests | rust, api-docs, docs-rs |
| `sphinx` | Sphinx — RST/MyST, autodoc, RTD, intersphinx | python, sphinx, autodoc |
| `typedoc` | TypeDoc — TypeScript API docs, reflection | typescript, tsdoc |
| `user-manual-md` | User Manual — MANUAL.md bare-minimum docs | manual, minimal, markdown |

---

## Hardware / EDA (9)

FPGA, PCB, and embedded hardware design skills.

| Slug | Name | Key tags |
|------|------|----------|
| `altium-designer` | Altium Designer — schematics, PCB, BOM, ODB++, Vault | altium, pcb, eda |
| `gtkwave` | GTKWave — VCD/FST waveform analysis | gtkwave, vcd, simulation, verilog, vhdl |
| `jtag-debug` | JTAG/SWD Debug — adapters, boundary scan, GDB, J-Link | jtag, swd, gdb, debug |
| `kicad` | KiCad — schematic, PCB layout, DRC/ERC, Gerber | kicad, pcb, gerber |
| `openocd` | OpenOCD — flash, GDB debug, JTAG/SWD | openocd, flash, stm32 |
| `pynq` | PYNQ — PYNQ-Z1/Z2, Overlay, MMIO, GPIO, DMA | pynq, zynq, overlay, python |
| `quartus-prime` | Intel/Altera Quartus Prime — TimeQuest, SignalTap | quartus, intel, fpga, verilog, vhdl |
| `vivado` | AMD/Xilinx Vivado — project flow, IP, timing | vivado, fpga, verilog, systemverilog, vhdl |
| `vivado-zynq-ps-pl` | Vivado — Zynq PS+PL deployment (Kria, PYNQ-Z2) | zynq, kria, axi, fpgautil |

!!! info "Verilog vs VHDL"
    Vivado and Quartus skills cover both HDLs. Most teams pick one primary HDL
    (Verilog/SV or VHDL) for their own RTL; the other appears when vendor IP or
    legacy modules require it. See the `vivado` skill's **HDL — Verilog vs VHDL**
    section for `add_files` patterns and mixed-language builds.

---

## Embedded / RTOS (11)

RTOS and embedded Linux skills.

| Slug | Name | Key tags |
|------|------|----------|
| `azure-rtos` | Azure RTOS — ThreadX, FileX, USBX, NetX Duo | azure-rtos, threadx, iot |
| `bare-metal-c` | Bare-metal C — startup, linker scripts, libc/runtime, interrupts | bare-metal, c, startup, linker-script, libc |
| `buildroot` | Buildroot — menuconfig, BR2_EXTERNAL, packages | buildroot, rootfs, board |
| `embedded-linux` | Embedded Linux — cross-compile, rootfs, systemd | cross-compile, sysroot |
| `freertos` | FreeRTOS — kernel tasks, IPC, timers, ISRs, memory, ports | freertos, rtos, tasks, queues, isr |
| `mbed-os` | Mbed OS 6 — Mbed CLI 2, Greentea testing | mbed, arm, cortex-m |
| `nuttx-rtos` | NuttX — menuconfig, NSH, apps | nuttx, rtos, posix |
| `rt-thread` | RT-Thread — scons, packages, Studio IDE | rt-thread, rtos |
| `rtems` | RTEMS — RSB toolchain, BSPs, testing | rtems, bsp |
| `yocto-bsp` | Yocto/OpenEmbedded — kas, bitbake, layers, devtool | yocto, bitbake, recipe |
| `zephyr-rtos` | Zephyr RTOS — 4.4→3.x, west, sysbuild, Kconfig, DTS, Twister | zephyr, west, devicetree, sysbuild |

---

## Cloud (4)

Cloud CLI and infrastructure skills.

| Slug | Name | Key tags |
|------|------|----------|
| `aws-cli` | AWS CLI v2 — profiles, SSO, S3, EC2, Lambda, CDK | aws, s3, lambda, cdk |
| `azure-cli` | Azure CLI — resource groups, AKS, App Service, Bicep | azure, aks, bicep |
| `gcp-cli` | GCP — gcloud CLI, GKE, Cloud Run, GCS, IAM | gcp, gke, cloud-run |
| `gh-cli` | GitHub CLI (gh) — PRs, issues, Actions, releases | github, gh, actions |

---

## DevOps (6)

Container, orchestration, CI/CD, and GitHub health skills.

| Slug | Name | Key tags |
|------|------|----------|
| `ci-cd-github-actions` | GitHub Actions — workflows, matrix, secrets, caching | github-actions, ci, yaml |
| `docker-workflow` | Docker — multi-stage builds, Compose, registries | docker, compose, dockerfile |
| `github-actions-ci` | GitHub Actions CI — Layer1Labs pattern (zero-trust, parallel) | ci, permissions, zero-trust, matrix |
| `github-health-check` | GitHub Health Check — CI/PR/security/code-quality triage | ci, codeql, dependabot, pr, triage |
| `kubernetes` | Kubernetes — kubectl, Helm, namespaces, GitOps | kubernetes, helm, gitops |
| `terraform` | Terraform — init/plan/apply, state, modules | terraform, iac, hcl |

---

## Mobile (4)

iOS, Android, Flutter, and React Native skills.

| Slug | Name | Key tags |
|------|------|----------|
| `android-dev` | Android — Gradle, ADB, emulator, Play Store | android, gradle, adb |
| `flutter-mobile` | Flutter — Dart, platform channels, Pub | flutter, dart, pub |
| `ios-dev` | iOS — Xcode, Swift, SPM, TestFlight, fastlane | ios, xcode, swift, testflight |
| `react-native` | React Native — Expo, Metro, EAS Build | react-native, expo, eas |

---

## Cross-Platform (3)

Cross-platform build, package manager, and shell awareness skills.

| Slug | Name | Key tags |
|------|------|----------|
| `cmake-cross-platform` | CMake — cross-platform builds, vcpkg, conan, presets | cmake, vcpkg, conan |
| `package-managers` | Package Managers — brew, winget, scoop, apt, nix | brew, winget, apt, nix |
| `terminal-awareness` | Terminal Awareness — PowerShell 5/7, cmd.exe, bash/zsh/fish, PID | powershell, pwsh, cmd, bash, pid, subprocess |

---

## SSH (3)

Remote development and WSL2 skills.

| Slug | Name | Key tags |
|------|------|----------|
| `remote-dev` | Remote Development — VS Code tunnels, rsync, tmux, mosh | vscode, rsync, tmux |
| `ssh-workflow` | SSH — key management, config, tunnels, ProxyJump | ssh, keys, agent |
| `wsl2-dev` | WSL2 — Windows Subsystem for Linux 2, interop | wsl2, windows, linux |

---

## Productivity (3)

Office, email, and presentation skills.

| Slug | Name | Key tags |
|------|------|----------|
| `email-workflow` | Email — professional writing, templates, inbox zero | email, templates |
| `office-productivity` | MS Office/LibreOffice — Excel, Word, macros | excel, word, macros |
| `presentations` | Presentations — storytelling, Gamma.ai, PowerPoint | slides, gamma, storytelling |

---

## Corporate (7)

Business operations, fundraising, and legal skills.

| Slug | Name | Key tags |
|------|------|----------|
| `budget-tracking` | Budget Tracking — P&L, cash flow, Excel models | budget, finance, excel |
| `fundraising-vc` | Fundraising — VC/Angel pitch, deck, due diligence | vc, pitch, term-sheet |
| `hr-onboarding` | HR & Onboarding — job descriptions, interviews | hr, hiring, onboarding |
| `legal-contracts` | Legal — contracts, NDAs, SaaS agreements, IP | legal, nda, contracts |
| `marketing-gtm` | Marketing GTM — positioning, ICP, content, demand gen | marketing, gtm, icp |
| `project-management` | Project Management — scope, milestones, RACI, risk | pm, raci, milestones |
| `sales-crm` | Sales CRM — pipeline, outreach, discovery, closing | sales, crm, pipeline |

---

## AI / LLM / Agents (14)

Skills for building and governing AI-powered systems — LLM apps, MCP servers, agent orchestration, RAG pipelines, and MLOps.

| Slug | Name | Key tags |
|------|------|----------|
| `llm-app-development` | LLM App Development — production LLM apps with LangChain/SDK | llm, langchain, openai, anthropic, streaming, tool-use |
| `mcp-server-development` | MCP Server Development — Model Context Protocol servers | mcp, fastmcp, tools, resources, stdio |
| `agent-orchestration` | Agent Orchestration — multi-agent with LangGraph/AutoGen/CrewAI | agents, multi-agent, langgraph, autogen, crewai, dag |
| `prompt-engineering` | Prompt Engineering — design, caching, and optimising prompts | prompt, system-prompt, caching, anthropic, token-cost |
| `rag-development` | RAG Development — retrieval-augmented generation pipelines | rag, embeddings, vector-database, chunking, reranking |
| `context-engineering` | Context Engineering — managing LLM context windows | context, tokens, summarization, sliding-window |
| `ai-safety-review` | AI Safety Review — safety, alignment, and bias review | ai-safety, prompt-injection, bias, pii, red-teaming |
| `langchain-development` | LangChain Development — LCEL chains, agents, and tools | langchain, lcel, runnable, langsmith, structured-output |
| `langgraph-development` | LangGraph Development — stateful agent workflows | langgraph, state-machine, tool-loop, human-in-the-loop |
| `vector-database` | Vector Database — choosing, configuring, and querying vector stores | chromadb, pgvector, qdrant, faiss, hybrid-search, ann |
| `model-evaluation` | Model Evaluation — LLM quality measurement and benchmarking | evals, llm-as-judge, faithfulness, ragas, deepeval |
| `fine-tuning-workflow` | Fine-Tuning Workflow — PEFT / LoRA / SFT fine-tuning | fine-tuning, lora, peft, qlora, huggingface, trl |
| `computer-vision-pipeline` | Computer Vision Pipeline — CV model training and deployment | yolo, pytorch, object-detection, segmentation, roboflow |
| `mlops-workflow` | MLOps Workflow — pipeline orchestration, tracking, and serving | mlflow, prefect, bentoml, ray-serve, model-registry, drift |

---

## Software Engineering (13)

Workflow skills for software engineering best practices — code review, TDD, debugging, security, and architecture.

| Slug | Name | Key tags |
|------|------|----------|
| `brief-lang` | Brief lang — declarative contract-enforced logic language | brief, brief-lang, declarative, contracts, transactions |
| `code-review` | Code Review — systematic pull request review workflow | code-review, pull-request, correctness, security, design |
| `test-driven-development` | Test-Driven Development — red-green-refactor workflow | tdd, test-first, red-green-refactor, pytest, jest |
| `debugging` | Debugging — systematic error diagnosis and recovery | debugging, error, root-cause, pdb, traceback |
| `refactoring` | Refactoring — improving code structure without changing behaviour | refactoring, clean-code, extract, simplify, duplication |
| `security-hardening` | Security Hardening — OWASP-aligned application security review | owasp, injection, xss, auth, secrets, hardening |
| `performance-optimization` | Performance Optimization — profiling and resolving bottlenecks | profiling, n+1, caching, latency, benchmark |
| `api-design` | API Design — REST, GraphQL, and gRPC API design principles | rest, graphql, grpc, openapi, versioning, pagination |
| `database-design` | Database Design — schema design, migrations, and query optimisation | postgresql, schema, migration, index, normalisation |
| `dependency-management` | Dependency Management — keeping dependencies secure and up to date | pip, npm, cargo, dependabot, lockfile, supply-chain |
| `git-workflow` | Git Workflow — branching strategy and commit conventions | git, gitflow, conventional-commits, rebase, squash |
| `pr-workflow` | PR Workflow — creating, reviewing, and merging pull requests | pull-request, review, merge, github, ci |
| `architecture-decision-records` | Architecture Decision Records — documenting architectural decisions | adr, architecture, madr, decision, documentation |

---

## Web / Backend (11)

Frontend engineering, web performance, and backend patterns for modern web apps.

| Slug | Name | Key tags |
|------|------|----------|
| `frontend-ui-engineering` | Frontend UI Engineering — component architecture and state management | react, vue, components, state, zustand, storybook |
| `web-performance` | Web Performance — Core Web Vitals and bundle optimisation | lcp, cls, inp, bundle, lighthouse, lazy-loading |
| `accessibility` | Accessibility — WCAG 2.1 AA implementation | a11y, wcag, aria, keyboard, screen-reader, axe |
| `testing-e2e` | End-to-End Testing — Playwright workflow for web apps | playwright, e2e, page-object, flaky-tests, ci |
| `nextjs-development` | Next.js Development — App Router, Server Components, Server Actions | nextjs, rsc, app-router, server-actions, hydration |
| `rest-api-development` | REST API Development — production-grade REST APIs with FastAPI | fastapi, rest, authentication, jwt, rate-limiting |
| `graphql-development` | GraphQL Development — schema design, resolvers, and N+1 prevention | graphql, strawberry, dataloader, n+1, subscription |
| `database-postgresql` | PostgreSQL — production setup, queries, and maintenance | postgresql, pgbouncer, vacuum, replication, pgvector |
| `caching-redis` | Caching with Redis — patterns, pitfalls, and eviction strategies | redis, cache-aside, ttl, stampede, pub-sub |
| `message-queue` | Message Queues — async task processing with Celery/RabbitMQ | celery, redis, rabbitmq, background-jobs, dead-letter |
| `websocket-realtime` | WebSocket & Real-Time — building real-time features | websocket, sse, pub-sub, reconnection, collaboration |

---

## Data Engineering (8)

Data pipeline design, transformation, quality, and stream processing.

| Slug | Name | Key tags |
|------|------|----------|
| `data-pipeline-etl` | Data Pipeline — ETL/ELT design with Airflow, Prefect, or dbt | etl, elt, pipeline, airflow, prefect, idempotent |
| `dbt-development` | dbt Development — data modelling, testing, and documentation | dbt, data-modelling, staging, marts, incremental |
| `data-quality` | Data Quality — validation and monitoring with Great Expectations | great-expectations, schema-validation, profiling, soda |
| `stream-processing` | Stream Processing — real-time data with Kafka and Flink | kafka, flink, spark-streaming, exactly-once, cdc |
| `ml-experiment-tracking` | ML Experiment Tracking — MLflow, W&B, and reproducible experiments | mlflow, wandb, model-registry, reproducibility |
| `feature-engineering` | Feature Engineering — feature stores, transformations, versioning | feature-store, feast, sklearn, training-serving-skew |
| `data-lakehouse` | Data Lakehouse — Delta Lake, Iceberg, and open table formats | delta-lake, iceberg, acid, time-travel, schema-evolution |
| `spark-pipeline` | Apache Spark — distributed data processing with PySpark | spark, pyspark, partitioning, broadcast-join, databricks |

---

## Platform Engineering (10)

Kubernetes, observability, GitOps, security, and resilience engineering.

| Slug | Name | Key tags |
|------|------|----------|
| `helm-chart` | Helm Chart — packaging K8s applications with Helm | helm, kubernetes, chart, values, upgrade, hooks |
| `monitoring-observability` | Monitoring & Observability — OpenTelemetry, Prometheus, Grafana | opentelemetry, prometheus, grafana, tracing, slo, alerting |
| `incident-response` | Incident Response — production incident handling and post-mortems | incident, on-call, post-mortem, runbook, blameless |
| `secret-management` | Secret Management — Vault, SOPS, and Kubernetes secrets | vault, sops, external-secrets, rotation, gitops |
| `gitops` | GitOps — declarative infrastructure with ArgoCD and Flux | argocd, flux, kustomize, promotion, sync |
| `serverless-functions` | Serverless Functions — AWS Lambda, GCP Functions, Cloudflare Workers | lambda, cold-start, sam, faas, cloudflare-workers |
| `oauth2-auth` | OAuth2 & Authentication — OAuth2/OIDC implementation | oauth2, oidc, jwt, pkce, keycloak, auth0 |
| `api-gateway` | API Gateway — Kong, AWS API Gateway, rate limiting | kong, nginx, rate-limiting, cors, circuit-breaker |
| `chaos-engineering` | Chaos Engineering — controlled failure injection with Litmus | litmus, chaos-monkey, resilience, game-day, steady-state |
| `service-mesh` | Service Mesh — Istio and Linkerd for microservices communication | istio, linkerd, mtls, canary, zero-trust, envoy |

---

## Adding a new skill

When contributing a new skill (H24):

1. Add a `SkillEntry` to the appropriate domain module in `src/specsmith/skills/`.
2. Update this page (`docs/site/skills-index.md`) in the same commit.
3. Run `python -m pytest tests/ -k skill` to verify the catalog loads correctly.
4. The `validate-strict` CI step checks that the index is not stale.

See [Contributing](contributing.md) for the full PR process.
