# Focused Skills

Specsmith is not a general-purpose prompt or skill marketplace. Modern agents
already provide testing, Git, browsing, document, framework, and language
skills. Duplicating those capabilities increases context size and maintenance
cost without improving governance.

The default catalog therefore exposes only 12 Specsmith-specific skills:

| Skill | Purpose |
|---|---|
| `preflight-gate` | Deterministically accept, clarify, or stop work before mutation |
| `requirement-author` | Capture behavior as durable requirements |
| `testcase-author` | Link enforceable tests to requirements |
| `traceability-auditor` | Find missing requirement-to-test evidence |
| `context-pack-compiler` | Build bounded epistemic context for an agent |
| `token-budget-auditor` | Measure and reduce governance token amplification |
| `verifier` | Verify tests, scope, confidence, and evidence |
| `release-pilot` | Validate fixed-point release readiness |
| `specsmith` | Compact CLI reference |
| `specsmith-save` | Persist governed state and evidence |
| `specsmith-audit` | Detect governance drift |
| `specsmith-session-governance` | Preserve continuity across agent sessions |

```bash
specsmith skill list
specsmith skill search context
specsmith skill install specsmith
```

Skills are installed as `.agents/skills/<slug>/SKILL.md`. Installing a skill is
optional: host-native integration is preferred.

## Agent and tool integrations

Use `specsmith integrate <host>` or the Specsmith MCP server so each host keeps
its native tools and receives only the compact AEE contract it needs. Supported
adapters include Claude Code, Codex-compatible `AGENTS.md`, Cursor, GitHub
Copilot, Gemini CLI, Aider, Warp, Windsurf, Zoo/Roo Code, Ollama, LM Studio,
vLLM, and Open WebUI.

An integration should translate four things and no more:

1. mutation intent to deterministic preflight;
2. accepted requirement and linked-test IDs to compact context;
3. native validator output to Specsmith verification evidence;
4. durable decisions and unknowns to the epistemic store.

Generic capabilities remain the host agent's responsibility. The previous broad
multi-domain catalog is no longer packaged, advertised, or injected into context.
