# Agent Integrations

specsmith generates governance files for 7 AI coding agent formats plus the cross-platform AGENTS.md standard. Each format has its own file convention and location.

## AGENTS.md (Cross-Platform Standard)

**File:** `AGENTS.md` (project root)
**Always generated.** This is the universal governance file that any AI agent can read. It follows the emerging `AGENTS.md` convention — a structured Markdown file that defines project governance, authority hierarchy, and workflow rules.

Even if you don't use any specific agent adapter, AGENTS.md provides governance for any AI assistant that reads project files.

## Agent Skill (SKILL.md)

**File:** `.agents/skills/SKILL.md`
**Config key:** `agent-skill` (legacy alias `warp` still accepted for existing scaffolds)

Generates a generic skill file under `.agents/skills/` for terminal-native AI agents that follow the SKILL.md convention. The file contains project metadata, governance rules, and verification tool references and works with any agent runtime that loads SKILL.md from a project-local directory.

## Claude Code

**File:** `CLAUDE.md` (project root)
**Config key:** `claude-code`

Claude Code reads `CLAUDE.md` at the project root for project-specific instructions. The generated file contains governance rules, verification requirements, and the closed-loop workflow formatted for Claude's instruction format.

## GitHub Copilot

**File:** `.github/copilot-instructions.md`
**Config key:** `copilot`

GitHub Copilot reads instructions from `.github/copilot-instructions.md`. The generated file contains project context, governance rules, and coding standards.

## Cursor

**File:** `.cursor/rules/governance.mdc`
**Config key:** `cursor`

Cursor reads rule files from `.cursor/rules/`. The generated `.mdc` file contains governance rules in Cursor's rule format.

## Gemini CLI

**File:** `GEMINI.md` (project root)
**Config key:** `gemini`

Google's Gemini CLI reads `GEMINI.md` for project instructions. The generated file contains governance rules and workflow expectations.

## Windsurf

**File:** `.windsurfrules` (project root)
**Config key:** `windsurf`

Windsurf reads `.windsurfrules` for project-specific rules. The generated file contains governance instructions.

## Aider

**File:** `.aider.conf.yml` (project root)
**Config key:** `aider`

Aider reads `.aider.conf.yml` for project configuration. The generated file contains governance context.

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
