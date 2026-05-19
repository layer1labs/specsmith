# Built-in Skills Index

specsmith ships with **69 built-in skills** across 11 domains.
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

## Governance (10)

Skills for project governance workflows, verification, release management, ESDB, CI polling, and IP prosecution.

| Slug | Name | Key tags |
|------|------|----------|
| `chronomemory-esdb` | ChronoMemory ESDB — epistemic state database (v0.1.1) | esdb, chronomemory, wal, query, context-pack |
| `diff-reviewer` | Diff Reviewer — surface changes for approval | git, review, pr |
| `gh-ci-polling` | GitHub Actions CI polling — smart wait (no sleep) | ci, gh, polling, github-actions |
| `issue-triage` | Issue Triage — classify and prioritise GitHub issues | github, issues, labels |
| `onboarding-coach` | Onboarding Coach — guided first session | onboarding, first-run |
| `patent-prosecution-workflow` | Patent Prosecution Workflow — prior-art, USPTO MCP, PAR | patent, uspto, ppubs, claim-themes, ip |
| `planner` | Planner — propose-then-execute | planning, aee, governance |
| `release-pilot` | Release Pilot — gitflow release cut | git, semver, release, gitflow |
| `specsmith-session-governance` | Specsmith Session Governance — drift prevention, heartbeat, preflight gate | governance, session, drift, checkpoint, anchor |
| `verifier` | Verifier — five-gate verification | audit, tests, verification |

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

## Embedded / RTOS (10)

RTOS and embedded Linux skills.

| Slug | Name | Key tags |
|------|------|----------|
| `azure-rtos` | Azure RTOS — ThreadX, FileX, USBX, NetX Duo | azure-rtos, threadx, iot |
| `buildroot` | Buildroot — menuconfig, BR2_EXTERNAL, packages | buildroot, rootfs, board |
| `embedded-linux` | Embedded Linux — cross-compile, rootfs, systemd | cross-compile, sysroot |
| `freertos` | FreeRTOS — tasks, queues, heap schemes, CMake | freertos, rtos, cmake |
| `mbed-os` | Mbed OS 6 — Mbed CLI 2, Greentea testing | mbed, arm, cortex-m |
| `nuttx-rtos` | NuttX — menuconfig, NSH, apps | nuttx, rtos, posix |
| `rt-thread` | RT-Thread — scons, packages, Studio IDE | rt-thread, rtos |
| `rtems` | RTEMS — RSB toolchain, BSPs, testing | rtems, bsp |
| `yocto-bsp` | Yocto/OpenEmbedded — kas, bitbake, layers, devtool | yocto, bitbake, recipe |
| `zephyr-rtos` | Zephyr RTOS — west, KConfig, DTS, Twister | zephyr, west, devicetree |

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

## Adding a new skill

When contributing a new skill (H24):

1. Add a `SkillEntry` to the appropriate domain module in `src/specsmith/skills/`.
2. Update this page (`docs/site/skills-index.md`) in the same commit.
3. Run `python -m pytest tests/ -k skill` to verify the catalog loads correctly.
4. The `validate-strict` CI step checks that the index is not stale.

See [Contributing](contributing.md) for the full PR process.
