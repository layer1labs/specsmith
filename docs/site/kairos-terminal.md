# Kairos Terminal

**Kairos** is the official recommended terminal client for specsmith — a fully local,
governance-ready terminal with zero cloud dependencies, built on the open-source
[OpenWarp/zerx-lab](https://github.com/zerx-lab/warp) fork.

!!! info "License"
    Kairos is AGPL-3.0 (inherited from the Warp/OpenWarp fork). specsmith (the governance
    backend) is MIT / commercial. You can run Kairos as a standalone terminal; the specsmith
    integration is optional but recommended.

## Why Kairos?

| Feature | Kairos | Other terminals |
|---------|--------|-----------------|
| specsmith governance built-in | ✅ | ❌ |
| Zero cloud dependencies | ✅ | Varies |
| BYOE (any OpenAI-compat endpoint) | ✅ | Varies |
| AEE dispatch panel | ✅ | ❌ |
| Context fill indicator | ✅ | ❌ |
| No login / no account | ✅ | Varies |

## Installation

Kairos is distributed as pre-built binaries via GitHub Releases.

### Download a pre-built binary

```bash
# macOS Apple Silicon
curl -Lo kairos https://github.com/BitConcepts/kairos/releases/latest/download/kairos-macos-aarch64
chmod +x kairos && ./kairos

# macOS Intel
curl -Lo kairos https://github.com/BitConcepts/kairos/releases/latest/download/kairos-macos-x86_64
chmod +x kairos && ./kairos

# Linux x86_64
curl -Lo kairos https://github.com/BitConcepts/kairos/releases/latest/download/kairos-linux-x86_64
chmod +x kairos && ./kairos
```

Windows: download `kairos-windows-x86_64.exe` from the
[Releases page](https://github.com/BitConcepts/kairos/releases/latest) and run it.

### Update channels

Kairos has two update channels selectable from **Settings → About**:

| Channel | What it tracks |
|---------|---------------|
| **Latest** *(default)* | Most recently published build — may be a dev pre-release from `develop` |
| **Stable** | Non-pre-release tagged releases only |

During the current dev phase, **Latest** is the default. When the first stable `v1.0` ships,
the default will switch to **Stable**.

!!! note "First-stable-release checklist"
    When promoting v1.0 stable: change `KairosUpdateChannel::default()` back to `Stable` in
    `app/src/kairos_updater.rs`, flip `--no-latest` to `--latest` in specsmith `release.yml`.

### Build from source

Requires Rust stable (1.92+) and a platform C compiler.

```bash
git clone https://github.com/BitConcepts/kairos
cd kairos
cargo build --release --bin kairos
./target/release/kairos
```

Linux additionally needs `libdbus-1-dev` and `pkg-config`:

```bash
sudo apt install libdbus-1-dev pkg-config
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Kairos Terminal (Rust)                  │
│  BYOE: base_url = http://127.0.0.1:7700                 │
└──────────────────────┬──────────────────────────────────┘
                       │ POST /v1/chat/completions
┌──────────────────────▼──────────────────────────────────┐
│           specsmith governance-serve (Python)            │
│  1. Preflight gate  2. Forward to real AI  3. Verify    │
└──────────────────────┬──────────────────────────────────┘
                       │ KAIROS_AI_BASE_URL
┌──────────────────────▼──────────────────────────────────┐
│     Real AI Provider (Ollama / Anthropic / OpenAI …)    │
└─────────────────────────────────────────────────────────┘
```

Kairos intercepts every AI request through specsmith's governance proxy running locally
on port 7700. This means **no AI call ever leaves the machine without governance approval**.

Architecture invariants:

- **I1** — Kairos never calls any LLM API directly.
- **I2** — All governance HTTP targets `127.0.0.1` only.
- **I3** — `specsmith governance-serve` is spawned as a managed child process at startup.

## Pairing with specsmith

Kairos auto-spawns `specsmith governance-serve` at startup. For this to work specsmith must
be on `PATH`:

```bash
pipx install specsmith          # recommended
# or
pip install specsmith

# Verify
specsmith --version
```

Kairos will show a red health dot in **Settings → Governance** if specsmith is not found.
The terminal still works — you just lose the governance gate.

## Settings Pages

All specsmith-related settings live under **Settings → Specsmith** and **Settings → Governance**.

### Settings → Governance

| Card | What it shows |
|------|--------------|
| Engine health | Live health dot + specsmith version + BYOE endpoint |
| Update channel | Latest / Stable pill selector; persisted across restarts |
| Context window | Current fill %, recommended `num_ctx` for your GPU VRAM, editable field |
| AEE phase | Current project phase (Inception → Release) + readiness % |

### Settings → Specsmith → ESDB

EventStore Database panel: record count, chain validity, and action buttons
(Refresh, Export JSON, Import, Backup, Rollback, Compact) that invoke
`specsmith esdb *` commands.

### Settings → Specsmith → Skills

Shows `specsmith skills list` output and CLI hints for `skills build` and `skills activate`.

### Settings → Specsmith → Eval

Shows eval run history and CLI hints for `specsmith eval run/report`.

### Settings → About

Update channel selector, Check Now button, and update status row.
The selected channel (Latest or Stable) is persisted to `{data_dir}/kairos_update_channel`.

## AI Provider Configuration

Kairos uses the **BYOE (Bring Your Own Endpoint)** model. No provider is bundled.

Set the AI provider via environment variables **before starting Kairos**:

```bash
# Ollama (local, no key needed)
export KAIROS_AI_BASE_URL=http://localhost:11434

# Anthropic
export KAIROS_AI_BASE_URL=https://api.anthropic.com
export KAIROS_AI_API_KEY=sk-ant-...
export KAIROS_AI_MODEL=claude-opus-4-6

# Any OpenAI-compatible endpoint (vLLM, LM Studio, etc.)
export KAIROS_AI_BASE_URL=http://localhost:8000
```

The governance proxy on port 7700 forwards accepted requests to `KAIROS_AI_BASE_URL`.
If not set, governance runs but AI calls return a stub with the acceptance notice.

## Context Window Management

Kairos surfaces specsmith's context window state in real-time:

- **Fill indicator** — compact progress bar in the agent footer showing fill %.
- **Auto-compression at 80%** — `SummarizeAIConversation` fires before the next turn.
- **Hard ceiling at 85%** — emergency compression; context must never reach 100%.
- **GPU-aware recommendation** — the Governance panel suggests `num_ctx` based on VRAM:

| VRAM | Recommended num_ctx |
|------|---------------------|
| < 6 GB | 4096 |
| 6–11 GB | 8192 |
| 12–19 GB | 16384 |
| ≥ 20 GB | 32768 |

## AI Providers Table — Bucket Scores

**Settings → Agents → AI Providers** includes three extra columns:

| Column | Meaning |
|--------|---------|
| **R** | Reasoning score (0–100) from HF leaderboard |
| **C** | Conversational score |
| **L** | Longform score |

Click **Sync Scores** to refresh from `GET /api/model-intel/sync` without interrupting
the active session.

## SSH Integration

Kairos supports full block-based SSH integration (formerly "Warpify").
All user-facing strings use "SSH Integration" / "integrate"; the underlying subsystem
path (`app/src/terminal/ssh/`) is unchanged from OpenWarp.

## Common Pitfalls

- **Red health dot at startup** — specsmith is not on PATH. Run `pipx install specsmith`.
- **Port 7700 in use** — another process is using the governance port. Kill it or
  change the port in `~/.specsmith/config.yml` (`governance_port: 7701`).
- **macOS binary quarantine** — run `xattr -d com.apple.quarantine ./kairos` if macOS
  blocks the unsigned binary.
- **Windows Defender** — add a Windows Security exception for the kairos binary directory.
- **Build fails on Linux** — install `libdbus-1-dev pkg-config` (`apt`) first.
