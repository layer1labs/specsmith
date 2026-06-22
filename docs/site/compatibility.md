# Compatibility Matrix
This matrix summarizes specsmith compatibility status across runtimes, platforms, AI clients, and model backends.

## Python runtimes
- Python 3.10 — **supported** (tested in CI)
- Python 3.11 — **supported** (tested in CI)
- Python 3.12 — **supported** (tested in CI)
- Python 3.13 — **experimental** (ongoing validation)

## Operating systems
- Windows (PowerShell 7+) — **supported** (active contributor workflows)
- Linux — **supported** (primary CI target)
- macOS — **supported** (validated in CI matrix)

## CI and automation
- GitHub Actions — **supported** (first-party CI workflows)

## Agent clients and IDE integrations
- Claude Code — **supported** (documented integration path)
- Cursor — **supported** (documented integration path)
- Windsurf — **experimental** (integration guidance available)
- Aider — **supported** (documented integration path)
- GitHub Copilot / Copilot Chat — **experimental** (governance workflow docs in progress)
- Warp / Oz — **supported** (first-party MCP + workflow integration)

## MCP ecosystem
- MCP clients (generic stdio/http clients) — **supported** via `specsmith mcp serve`
- MCP server hosting in AI clients — **supported** with client-specific setup steps

## Model backends
- Ollama / local models — **supported** (local-first workflows)
- OpenAI-compatible endpoints (BYOE) — **supported** (endpoint profiles)
- Cloud hosted frontier models — **supported** with provider SDK availability

## Lifecycle states
- **supported**: actively maintained and tested
- **experimental**: usable with caveats; interfaces may change
- **planned**: intended roadmap target, not yet shipped
- **deprecated**: maintained only for migration windows; avoid for new projects
