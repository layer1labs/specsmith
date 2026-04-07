# VS Code Extension — specsmith AEE Workbench

The **specsmith AEE Workbench** VS Code extension is the flagship client for specsmith. It provides multi-tab AI agent sessions, live model management, governance file editing, and full Ollama support — all inside VS Code's right-side panel.

**GitHub:** [BitConcepts/specsmith-vscode](https://github.com/BitConcepts/specsmith-vscode)

---

## Requirements

- VS Code 1.85+
- specsmith v0.3.1+ installed and on PATH
- At least one LLM provider (API key or local Ollama)

```bash
# Install specsmith first
pip install "specsmith[anthropic,openai,gemini,mistral]"
# or
pipx install specsmith
```

---

## Installation

Install the extension from [the GitHub repository](https://github.com/BitConcepts/specsmith-vscode):

```bash
git clone https://github.com/BitConcepts/specsmith-vscode
cd specsmith-vscode
npm install && npm run build
# Press F5 in VS Code to launch the Extension Development Host
```

!!! note "Marketplace"
    The extension will be published to the VS Code Marketplace. Until then, install from source as above.

---

## First Run

1. Open the **Secondary Side Bar** — `View → Open Secondary Side Bar` or `Ctrl+Alt+B`
2. The **specsmith AEE** panel appears on the right
3. Set your API key: `Ctrl+Shift+P → specsmith: Set API Key`
4. Click **+** in the Sessions panel or press `Ctrl+Shift+;`
5. Select your project folder — the agent starts automatically

---

## Features

### Agent Sessions

Each session is an independent `specsmith run --json-events` process with its own:

- Conversation history (saved to `.specsmith/chat/`)
- Provider and model (remembered per project)
- Token budget tracking with live context fill bar

When a session connects, it automatically runs the **start protocol**:
sync → load AGENTS.md → read LEDGER.md → check for updates.

### Model Provider Support

| Provider | Free tier | Notes |
|----------|-----------|-------|
| **Anthropic** | No | Best for requirements engineering |
| **OpenAI** | No (separate from ChatGPT sub) | GPT-4o, o3, o3-mini |
| **Google Gemini** | Yes (generous limits) | Free key at [aistudio.google.com](https://aistudio.google.com/apikey) |
| **Mistral** | Trial credits | Pixtral supports OCR |
| **Ollama** | Yes (local, free) | GPU-aware; see [Ollama setup](#ollama-local-models) below |

API keys are stored in the **OS credential store** (Windows Credential Manager / macOS Keychain) via VS Code's SecretStorage — never in `settings.json`.

### Ollama — Local Models

The extension includes full Ollama integration:

```bash
# From terminal — see available models for your GPU
specsmith ollama available

# Download a model (also available via model dropdown in VS Code)
specsmith ollama pull qwen2.5:14b

# Get GPU-aware model suggestions for your task
specsmith ollama suggest requirements
```

From VS Code:

- **Model dropdown** — shows `Installed` and `Available to Download` groups, GPU-VRAM filtered
- Selecting an undownloaded model → download confirmation → progress notification with Cancel
- `Ctrl+Shift+P → specsmith: Select Model for Task` — task-specific model recommendations

Context length is auto-detected from GPU VRAM:

| VRAM | Context |
|------|---------|
| < 4 GB | 4K tokens |
| 4–8 GB | 8K tokens |
| 8–16 GB | 16K tokens |
| 16+ GB | 32K tokens |

Override with `specsmith.ollamaContextLength` in VS Code settings.

### Governance Panel

Open with `Ctrl+Shift+G` or the `📖` icon in the Projects toolbar.

The Governance Panel provides:

- **scaffold.yml form** — project type (all 33 types), platforms, agent integrations, VCS
- **Governance file status** — ✓/✗ for REQUIREMENTS.md, AGENTS.md, LEDGER.md, TEST_SPEC.md, architecture.md
- **Quick Actions** — audit --fix, validate, doctor, epistemic-audit, stress-test, export
- **AI Prompt Palette** — 9 pre-written prompts sent to the active agent session

### Projects Sidebar

The Projects panel (right side bar) shows each project with:
- `📋 Governance` folder — key spec docs with direct Open buttons
- Full file tree (dirs-first, filtered for noise)
- Right-click: New File, New Folder, Delete, Rename, Copy Path

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+;` | New agent session |
| `Ctrl+Shift+G` | Open Governance Panel |
| `Ctrl+Shift+R` | Quick add requirement |
| `Ctrl+Shift+Q` | Navigate requirements (QuickPick) |
| `Enter` | Send message |
| `Shift+Enter` | New line in message |
| `↑` (empty input) | Recall last message |
| `@` (empty input) | Pick file to inject as context |
| `Escape` | Stop agent |

### Chat Features

- **Drag & drop** — drop files or screenshots onto the chat to inject as context
- **Paste images** — `Ctrl+V` pastes screenshots directly
- **Copy message** — hover any message → `⎘` button
- **Edit last message** — hover user message → `✏` button → puts back in input
- **Regenerate** — hover agent message → `↺` button
- **Export chat** — `⬇` button in header → saves as Markdown
- **Clear history** — `🗑` button → clears display + JSONL files + agent context
- **Resize input** — drag the teal handle above the input bar (drag up = bigger textarea)

---

## Configuration

All settings are under `specsmith.*` in VS Code settings (`Ctrl+,`):

| Setting | Default | Description |
|---------|---------|-------------|
| `specsmith.executablePath` | `specsmith` | Path to specsmith CLI. Auto-detected if not set. |
| `specsmith.defaultProvider` | `anthropic` | Default LLM provider. Auto-selected if only one API key is set. |
| `specsmith.defaultModel` | `` | Default model. Remembered per-project. |
| `specsmith.ollamaContextLength` | `0` | Ollama context size. `0` = auto-detect from GPU VRAM. |

---

## Bridge Protocol

The extension communicates with specsmith via `specsmith run --json-events`:

```
specsmith run --json-events --project-dir <dir> --provider <p> --model <m>
        ↑ stdin: user messages (one line each)
        ↓ stdout: JSONL events
```

Event types: `ready`, `llm_chunk`, `tool_started`, `tool_finished`, `tokens`, `turn_done`, `error`, `system`.

This design means all AI logic lives in the Python CLI — the extension is a pure UI layer.

---

## Troubleshooting

**"specsmith not responding"** — The extension probes for a valid specsmith (>= v0.3.1) across all known paths. If it fails:

1. Run `Ctrl+Shift+P → specsmith: Install or Upgrade`
2. Or set `specsmith.executablePath` to the full path of your installation

**"Ollama 404 — model not installed"** — The saved model for this project isn't in Ollama. Open the model dropdown and select from the **Installed** group.

**"Ollama not running"** — Start Ollama: run `ollama serve` in a terminal, or open the Ollama desktop app.

**API key 401** — Re-enter via `Ctrl+Shift+P → specsmith: Set API Key`.

**API key 429 (quota exceeded)** — Add credits at your provider's billing portal.

---

## Links

- [GitHub: specsmith-vscode](https://github.com/BitConcepts/specsmith-vscode)
- [GitHub: specsmith](https://github.com/BitConcepts/specsmith)
- [specsmith CLI reference](commands.md)
- [Agentic client overview](agent-client.md)
- [Ollama documentation](https://ollama.ai)
