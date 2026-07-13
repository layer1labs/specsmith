# Agent Integrations

specsmith generates governance files for 7 AI coding agent formats plus the cross-platform AGENTS.md standard.
Run `specsmith integrate <tool>` once in your project root; the generated file is read automatically by the agent on every session start.

## Quick reference

| Tool | Command | Generated file | MCP support |
|---|---|---|---|
| **Warp** | `specsmith integrate warp` | `.warp/specsmith-mcp.json` + `.warp/launch_configs/` | ✓ Native |
| **Claude Code** | `specsmith integrate claude-code` | `CLAUDE.md` | ✓ via `.mcp.json` |
| **Cursor** | `specsmith integrate cursor` | `.cursor/rules/governance.mdc` | ✓ via `.cursor/mcp.json` |
| **Windsurf** | `specsmith integrate windsurf` | `.windsurfrules` | ✓ via Settings → MCP |
| **Gemini CLI** | `specsmith integrate gemini` | `GEMINI.md` | — |
| **Aider** | `specsmith integrate aider` | `.aider.conf.yml` | — |
| **Copilot** | `specsmith integrate copilot` | `.github/copilot-instructions.md` | — |

No AI agent? See [Standalone CLI](standalone-cli.md) for the pure-terminal session workflow.

---

## Mandatory session protocol (all tools)

Regardless of which tool you use, the governance session protocol is the same:

**Session start** (run once before any other action):

```bash
specsmith kill-session  # idempotent; safe when no processes exist
specsmith audit --project-dir .
specsmith sync  --project-dir .
specsmith checkpoint --project-dir .   # output GOVERNANCE ANCHOR verbatim
```

**Before every code change:**

```bash
specsmith preflight "<describe the change>" --json
# decision == "accepted"          → proceed; note the work_item_id
# decision == "needs_clarification" → surface the instruction first
```

**Governance heartbeat** (every 8–10 turns):

```bash
specsmith checkpoint --project-dir .   # output verbatim
```

**Session end:**

```bash
specsmith save && specsmith kill-session
```

---

## Warp

Warp has a dedicated integration page with full detail on the MCP server, repository workflows, and skill auto-discovery:

→ **[Warp Integration](warp-integration.md)**

**One-time setup:**

```bash
specsmith integrate warp          # writes .warp/ MCP config + launch configs + SKILL.md
specsmith mcp install-warp        # prints config snippet to paste into Warp → Settings → Agents → MCP
```

See the Warp integration page for inline `oz agent run` usage, the full MCP tool reference, and the `Ctrl+Shift+R` workflow catalogue.

---

## Claude Code

**One-time setup:**

```bash
specsmith integrate claude-code   # writes CLAUDE.md at project root
```

Claude Code reads `CLAUDE.md` automatically. To enable native MCP tool calls (structured JSON, no shell roundtrip), add to `.mcp.json` in the project root or `~/.claude/mcp.json` globally:

```json
{
  "mcpServers": {
    "specsmith-governance": {
      "command": "specsmith",
      "args": ["mcp", "serve", "--project-dir", "."]
    }
  }
}
```

Or run `specsmith mcp install-claude-code` to print the snippet.

With MCP configured, Claude can call `governance_preflight`, `governance_audit`, `governance_checkpoint`, `governance_req_list`, `governance_phase`, and `governance_trace_seal` as native tools.

**Key files:**

- `CLAUDE.md` — project-level governance instructions
- `.mcp.json` — MCP server config
- `.agents/skills/` — skill files auto-discovered by Claude Code 3.x+

---

## Cursor

**One-time setup:**

```bash
specsmith integrate cursor   # writes .cursor/rules/governance.mdc
```

Cursor reads rule files from `.cursor/rules/` automatically. To enable MCP, create or add to `.cursor/mcp.json`:

```json
{
  "specsmith-governance": {
    "command": "specsmith",
    "args": ["mcp", "serve", "--project-dir", "${workspaceFolder}"]
  }
}
```

**Key files:**

- `.cursor/rules/governance.mdc` — Cursor rule file (applied to all files)
- `.cursor/mcp.json` — project-level MCP config
- `AGENTS.md` — universal governance hub (Cursor reads this as project context)
- `.agents/skills/` — skill files (Cursor Agent mode discovers these)

---

## Windsurf

**One-time setup:**

```bash
specsmith integrate windsurf   # writes .windsurfrules at project root
```

Windsurf reads `.windsurfrules` automatically. To enable MCP, go to **Settings → MCP Servers** and add:

```json
{
  "specsmith-governance": {
    "command": "specsmith",
    "args": ["mcp", "serve"]
  }
}
```

**Key files:**

- `.windsurfrules` — Windsurf global rules file
- `AGENTS.md` — universal governance hub
- `.agents/skills/` — skill directory (Cascade agent reads these)

---

## Gemini CLI

**One-time setup:**

```bash
specsmith integrate gemini   # writes GEMINI.md at project root
```

The `gemini` CLI reads `GEMINI.md` from the project root automatically. No MCP configuration is required; governance is enforced through the instructions file and AGENTS.md.

**Key files:**

- `GEMINI.md` — Gemini CLI project instructions
- `AGENTS.md` — universal governance hub
- `.agents/skills/` — skills referenced from GEMINI.md

---

## Aider

**One-time setup:**

```bash
specsmith integrate aider   # writes .aider.conf.yml at project root
```

The generated `.aider.conf.yml` includes a `read:` list that loads `AGENTS.md` and the key governance skills automatically. You can also pass them at startup without the config file:

```bash
aider --read AGENTS.md \
      --read .agents/skills/specsmith-session-governance/SKILL.md
```

**Aider-specific note:** Aider auto-commits via git by default. For full governance traceability, use `--no-auto-commits` and commit through `specsmith save` instead:

```bash
aider --no-auto-commits   # let specsmith save handle commits + ESDB backup
```

Before aider makes any code change, run preflight in a separate terminal:

```bash
specsmith preflight "<intent>" --json
```

After aider finishes its changes, run `specsmith save` to add the ESDB backup and push.

**Key files:**

- `.aider.conf.yml` — aider configuration (reads AGENTS.md + skills)
- `AGENTS.md` — universal governance hub
- `.agents/skills/` — skills loaded via `read:` in aider config

---

## GitHub Copilot

**One-time setup:**

```bash
specsmith integrate copilot   # writes .github/copilot-instructions.md
```

Copilot reads `.github/copilot-instructions.md` automatically for all workspace interactions. The generated file embeds the preflight gate, session protocol, and hard governance rules.

!!! note "MCP support"
    GitHub Copilot does not natively support MCP as of 2026. Governance is enforced through `.github/copilot-instructions.md` and `AGENTS.md`.

**Key files:**

- `.github/copilot-instructions.md` — Copilot workspace instructions
- `AGENTS.md` — universal governance hub
- `.agents/skills/specsmith/SKILL.md` — master CLI reference

---

## AGENTS.md (Cross-Platform Standard)

**File:** `AGENTS.md` (project root)
**Always generated.** This is the universal governance file that any AI agent can read. It follows the emerging `AGENTS.md` convention — a structured Markdown file that defines project governance, authority hierarchy, and workflow rules.

Even if you don't use any specific agent adapter, AGENTS.md provides governance for any AI assistant that reads project files.

## Agent Skill (SKILL.md)

**File:** `.agents/skills/SKILL.md`
**Config key:** `agent-skill` (legacy alias `warp` still accepted for existing scaffolds)

Generates a generic skill file under `.agents/skills/` for terminal-native AI agents that follow the SKILL.md convention. The file contains project metadata, governance rules, and verification tool references and works with any agent runtime that loads SKILL.md from a project-local directory.

---

## Selecting Integrations

In `scaffold.yml`:

```yaml
integrations:
  - agents-md      # Always included
  - agent-skill    # Generic SKILL.md (.agents/skills/)
  - claude-code    # Add Claude Code support
  - copilot        # Add Copilot support
```

Or during interactive `specsmith init`, select from the numbered list.

## What Each File Contains

All agent files contain the same core governance information, adapted for each platform's format:

- Project name, type, and language
- Verification tools from the [Tool Registry](tool-registry.md)
- The closed-loop workflow (propose → check → execute → verify → record)
- Reference to AGENTS.md as the primary governance source
- Pointer to LEDGER.md for session context
