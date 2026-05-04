# VS Code Extension — specsmith AEE Workbench

The **specsmith AEE Workbench** VS Code extension is the flagship client for specsmith. It provides
AI agent sessions, a 6-tab Settings panel, execution profiles, the AEE workflow phase indicator,
live Ollama management, FPGA/HDL tool support, and full epistemic engineering workflow — all inside
VS Code's secondary sidebar.

**GitHub:** [BitConcepts/specsmith-vscode](https://github.com/BitConcepts/specsmith-vscode)

---

## Requirements

- VS Code 1.85+
- specsmith **v0.3.6+** installed and on PATH
- At least one LLM provider (API key or local Ollama)

```bash
pipx install specsmith                   # install core CLI
pipx inject specsmith anthropic          # + Claude
pipx inject specsmith openai             # + GPT / O-series
pipx inject specsmith google-generativeai  # + Gemini
```

!!! warning "Do not use bare `pip install specsmith`"
    `pip install` without a virtual environment puts specsmith in your active
    Python's Scripts directory. If you have multiple Pythons (Scoop, Conda,
    system) this creates duplicate binaries that VS Code and your terminal may
    resolve differently. **pipx is the only supported install method for VS Code users.**

---

## Installation

From the [GitHub repository](https://github.com/BitConcepts/specsmith-vscode):

```bash
git clone https://github.com/BitConcepts/specsmith-vscode
cd specsmith-vscode
npm install && npm run build
# Press F5 in VS Code to launch the Extension Development Host
```

!!! note "Marketplace"
    The extension will be published to the VS Code Marketplace. Until then, install from source.

---

## First Run

1. Open the **specsmith** Activity Bar icon (left sidebar)
2. Set your API key: `Ctrl+Shift+P → specsmith: Set API Key`
3. Press `Ctrl+Shift+;` or click **+** in Sessions to start a session
4. Select your project folder — the agent starts automatically and runs the start protocol

The **Settings Panel** opens automatically on startup (`Ctrl+Shift+G` to open manually).

---

## AEE Workflow Phase Indicator

The Settings Panel displays a persistent **phase bar** below the header showing:

- **Current phase pill** — emoji + label (e.g. `📋 Requirements`)
- **Phase description** — what this phase accomplishes
- **Readiness %** — how many prerequisite checks pass (e.g. `60% ready · step 3/7`)
- **→ next phase button** — runs `specsmith phase next` in a terminal
- **Phase selector** — jump to any phase directly

The 7 AEE phases:

```
🌱 Inception → 🏗 Architecture → 📋 Requirements → ✅ Test Spec
   → ⚙ Implementation → 🔬 Verification → 🚀 Release
```

From the CLI:
```bash
specsmith phase show               # show current phase + readiness checklist
specsmith phase list               # visual pipeline with current phase highlighted
specsmith phase next               # advance (checks prerequisites first)
specsmith phase set implementation # jump to a phase (--force to skip checks)
```

### Phase-Driven Prompts

The Actions tab adapts to the current phase. Each phase shows:

- **🤖 AI-Guided button** — starts a comprehensive interactive session for the phase (e.g. "Guide me through requirements gathering")
- **Phase-specific prompts** — only prompts relevant to the current phase (e.g. architecture phase shows "Generate ARCHITECTURE.md" and "Define components")
- **Always-available prompts** — audit, upgrade, and ledger update are always shown

This means the extension actively guides you through the AEE lifecycle rather than showing a static list of actions.

### Governance File Naming

specsmith v0.3.7+ uses clearer governance file names:

| Old Name | New Name | Purpose |
|----------|----------|---------|
| `WORKFLOW.md` | `SESSION-PROTOCOL.md` | How agent sessions work (proposals, ledger format) |
| *(new)* | `LIFECYCLE.md` | Phase-aware project lifecycle roadmap |
| `docs/WORKFLOW.md` | *(removed)* | Replaced by the phase system + LIFECYCLE.md |

Old projects are automatically migrated when you run `specsmith upgrade`.

---

## Settings Panel — 6 Tabs

Open with `Ctrl+Shift+G` or the `📖` toolbar icon.

### Tab: Project
- scaffold.yml form: name, type (35 types), description, languages (multi-select chips with filter), VCS platform, spec version
- **Detect Languages** button — scans file extensions and patches scaffold.yml
- **Upgrade spec** button — runs `specsmith upgrade` in terminal
- Save button persists all changes to scaffold.yml

### Tab: Tools
- **FPGA/HDL tools** (21 tools) — vivado, quartus, gtkwave, ghdl, iverilog, verilator, vsg, yosys, nextpnr, symbiyosys, and more
- **Auxiliary disciplines** — add mixed-discipline support (e.g. FPGA + embedded C + Python verification)
- **CI/CD build platforms** — linux, windows, macos, embedded, FPGA variants (target deploy/test platforms, not the host OS)
- **Installed Ollama models** with Update / Remove buttons
- All saved to `fpga_tools:`, `platforms:` in scaffold.yml

### Tab: Files
- Governance file status table: scaffold.yml, AGENTS.md, REQUIREMENTS.md, TESTS.md, ARCHITECTURE.md, LEDGER.md
- Governance files use new naming: SESSION-PROTOCOL.md, LIFECYCLE.md (replaces old WORKFLOW.md)
- ✓ / ✗ indicators with line counts
- **Add** buttons for missing files — choose AI-generated or template
- **Open** buttons for existing files

### Tab: Updates & System
- Current vs available specsmith version (fetches from PyPI)
- **Check for Updates** button — queries PyPI API without resetting the active tab
- **Install Update** button — respects `specsmith.releaseChannel` (stable / pre-release)
- After install: button swaps to **↺ Reload Window** automatically
- Last checked timestamp; Ollama version checker
- System info panel (lazy-loaded): OS, CPU, cores, RAM, GPU, disk

### Tab: Actions & AI
- Quick actions grid: audit --fix, validate, doctor, epistemic-audit, stress-test, export, req list, req gaps, lifecycle status
- **🤖 AI-Guided Session** button — launches a comprehensive interactive session for the current AEE phase
- **Phase Prompts** — prompts change dynamically based on the current lifecycle phase (inception, architecture, requirements, etc.)
- **Always Available** prompts — audit, upgrade, ledger update (available in every phase)

### Tab: Execution
- **Execution profile selector** — `🔒 safe` (read-only), `⚙ standard` (default), `🔓 open`, `⚠ admin`
- Profile description updates live as you change the selection
- **Custom overrides**: additional allowed / blocked command prefixes and agent tool blocks
- Changes saved to `execution_profile`, `custom_allowed_commands`, `custom_blocked_commands` in `scaffold.yml`
- **Tool Installer** — scan tools (runs `specsmith tools scan --json --fpga`), show install status, **Install** button for missing tools opens `specsmith tools install <key>` in a terminal

---

## Agent Sessions

Each session is an independent `specsmith run --json-events` process with:

- Conversation history saved to `.specsmith/chat/chat-YYYYMMDD.jsonl`
- Provider and model remembered per project
- Real-time token meter with context fill bar
- Chat history replayed on session re-open (last 40 messages)
- Auto-start protocol on session ready: sync → load AGENTS.md → read LEDGER.md

**Session status icons in the Sessions sidebar:**

- 🟡 Starting — process spawning
- 🟢 Waiting — ready for input
- ⚙ Running (spin) — agent is thinking
- ⚠ Error — check the chat panel for the error message

---

## Model Provider Support

| Provider | Free tier | Notes |
|----------|-----------|-------|
| **Anthropic** | No | Best for requirements engineering |
| **OpenAI** | No | GPT-4o, o3, o4-mini, GPT-4.1 |
| **Google Gemini** | Yes | Free key at aistudio.google.com |
| **Mistral** | Trial credits | Pixtral supports OCR |
| **Ollama** | Yes (local) | GPU-aware; see below |

API keys are stored in the **OS credential store** (Windows Credential Manager / macOS Keychain) via VS Code SecretStorage — never in `settings.json`.

---

## Ollama — Local Models

```bash
# From terminal
specsmith ollama gpu               # detect VRAM tier
specsmith ollama available         # VRAM-filtered catalog
specsmith ollama pull qwen2.5:14b  # download
specsmith ollama suggest requirements  # task-based recommendations
```

From VS Code:

- **Model dropdown** — shows `Installed` and `Available to Download` groups (GPU-VRAM filtered)
- Selecting an undownloaded model triggers download confirmation → progress notification with Cancel
- `Ctrl+Shift+P → specsmith: Select Model for Task` — task-specific model selector

**Context length auto-detection from GPU VRAM:**

| VRAM | Context |
|------|---------|
| < 4 GB | 4K tokens |
| 4–8 GB | 8K tokens |
| 8–16 GB | 16K tokens |
| 16+ GB | 32K tokens |

Override with `specsmith.ollamaContextLength` in VS Code settings.

**Ollama 404 fix:** The extension automatically resolves quantization-suffix mismatches
(e.g. saved `qwen2.5:14b` → installed `qwen2.5:14b-instruct-q4_K_M`) by querying the actual
installed model list before spawning the session.

---

## Chat Features

- **Drag & drop** — drop files or screenshots onto the chat
- **Paste images** — `Ctrl+V` pastes screenshots directly
- **Copy message** — hover any message → `⎘`
- **Edit last message** — hover user message → `✏` → puts back in input
- **Regenerate** — hover agent message → `↺`
- **Export chat** — `⬇` button → saves as Markdown
- **Clear history** — `🗑` button → clears display + JSONL files + agent context
- **Resize input** — drag the teal handle above the input bar (drag up = bigger)
- **@file** — type `@` in empty input to inject a file as context

---

## Multi-Agent + BYOE Surfaces (0.10.0)
The extension exposes the CLI's `agents` (REQ-146) and `endpoints` (REQ-142)
stores as two sidebar trees plus eight Command Palette entries. Each
command shells out to `specsmith <subcommand> --json` so the on-disk
schema lives in exactly one place.
### Sidebar trees
- **BYOE Endpoints** (`specsmith.endpoints` view) — every entry from
  `~/.specsmith/endpoints.json`; the entry marked `★` is the default.
- **Agent Profiles** (`specsmith.agents` view) — grouped under *Profiles*
  (with `★` on the default) and *Routes* (`activity → profile_id`).
### Commands
| Command palette                                  | Action                                                                |
|--------------------------------------------------|------------------------------------------------------------------------|
| `specsmith: BYOE Endpoints…`                     | Quick Pick over endpoints with copy-id / set-default / test actions.   |
| `specsmith: Test BYOE Endpoint`                  | Probes `/v1/models`; toast shows latency + model count.                |
| `specsmith: Refresh BYOE Endpoints`              | Re-runs `specsmith endpoints list --json` and refreshes the tree.      |
| `specsmith: Agent Profiles…`                     | Quick Pick over profiles; copy id, set default, route to activity.     |
| `specsmith: Test Agent Profile`                  | Probes the resolved provider / endpoint and shows reachability.        |
| `specsmith: Refresh Agent Profiles`              | Re-runs `specsmith agents list --json` and refreshes the tree.         |
| `specsmith: Apply Agent Preset (default / local-only / frontier-only / cost-conscious)` | Runs `specsmith agents preset apply <name>`.                           |
| `specsmith: Route Activity to Agent Profile`     | Picks an activity (`/plan`, `/fix`, `phase:requirements`, …) and a profile, then runs `specsmith agents route set`. |
| `specsmith: Pick Session Profile`                | Per-session pin for the active SessionPanel; appends `--agent <id>` to the bridge invocation. |
The SessionPanel header chip surfaces the resolved profile + endpoint for
the current turn; click it to open the picker without leaving the chat.
### `/agent <id>` from chat
Typing `/agent opus-reviewer` in the chat input flips the active session
to the named profile and writes a TraceVault decision seal so the change
is chained into `.specsmith/trace.jsonl`.
## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+;` | New agent session |
| `Ctrl+Shift+G` | Open Settings Panel |
| `Ctrl+Shift+R` | Quick add requirement |
| `Ctrl+Shift+Q` | Navigate requirements |
| `Enter` | Send message |
| `Shift+Enter` | New line in message |
| `↑` (empty input) | Recall last message |
| `@` (empty input) | Pick file to inject |
| `Escape` | Stop agent |

---

## Configuration

All settings under `specsmith.*` in VS Code Settings (`Ctrl+,`):

| Setting | Default | Description |
|---------|---------|-------------|
| `specsmith.executablePath` | `specsmith` | Path to specsmith CLI |
| `specsmith.defaultProvider` | `anthropic` | Default LLM provider |
| `specsmith.defaultModel` | `` | Default model (blank = provider default) |
| `specsmith.ollamaContextLength` | `0` | Ollama context size (0 = auto-detect from VRAM) |
| `specsmith.autoOpenGovernancePanel` | `true` | Auto-open Settings panel on VS Code start |

---

## Bridge Protocol

The extension communicates with specsmith via `specsmith run --json-events`:

```
specsmith run --json-events --project-dir <dir> --provider <p> --model <m>
        ↑ stdin: user messages (one line each)
        ↓ stdout: JSONL events
```

Event types: `ready`, `llm_chunk`, `tool_started`, `tool_finished`, `tokens`, `turn_done`, `error`, `system`.

All AI logic lives in the Python CLI — the extension is a pure UI layer.

---

## Troubleshooting

**"specsmith not responding"** — The extension probes for specsmith ≥ v0.3.3 across all known paths.
Run `Ctrl+Shift+P → specsmith: Install or Upgrade` or set `specsmith.executablePath`.

**"Ollama 404 — model not installed"** — The model name doesn't match what's installed. Open the
model dropdown and select from the **Installed** group, or `specsmith ollama list`.

**"Ollama not running"** — Start it: `ollama serve` or open the Ollama desktop app.

**API key 401** — Re-enter: `Ctrl+Shift+P → specsmith: Set API Key`.

**API key 429 (quota exceeded)** — Add credits at your provider's billing portal.

---

## Learn More

- **[AEE Primer (Full Guide)](aee-primer.md)** — Applied Epistemic Engineering from zero to productive
- **[epistemic Library Reference](epistemic-library.md)** — standalone Python library for belief engineering
- **[Governance Model](governance.md)** — the closed-loop workflow, file hierarchy, modular governance
- **[CLI Commands](commands.md)** — every specsmith command with options and examples
- **[Project Types](project-types.md)** — all 35+ project types with tools and governance rules
- **[Importing Projects](importing.md)** — how detection works, merge behavior, type inference

## Links

- [GitHub: specsmith-vscode](https://github.com/BitConcepts/specsmith-vscode)
- [GitHub: specsmith](https://github.com/BitConcepts/specsmith)
- [specsmith Documentation (RTD)](https://specsmith.readthedocs.io)
