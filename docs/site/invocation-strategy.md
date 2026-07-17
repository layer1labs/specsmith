# Invocation strategy

Specsmith exposes the same governance through four entry points. Choose the
surface that owns the interaction; fall back to the direct CLI when a richer
surface is unavailable.

| Scenario | Preferred | Fallback | Why |
|---|---|---|---|
| AI agent in an MCP-capable IDE | MCP | direct CLI with `--json` | Structured decisions and stable schemas |
| Human in the Nexus REPL | `/specsmith` slash command | direct CLI | Short interactive operations |
| Multi-step domain workflow | activated skill | MCP or direct CLI | The skill supplies the procedure; governance still supplies decisions |
| CI, script, or headless host | direct CLI | none required | No resident server or interactive shell |
| Zoo Code governed session | MCP for decisions; generated assets for setup | direct CLI doctor/checkpoint | Zoo applies the exact Specsmith directive and packet |

## Compatibility

| Surface | Windows | Linux | macOS | IDE | Headless |
|---|---:|---:|---:|---:|---:|
| MCP | yes | yes | yes | preferred | when an MCP client is present |
| Slash command | yes | yes | yes | terminal/REPL | no |
| Skill | yes | yes | yes | agent-dependent | agent-dependent |
| Direct CLI | yes | yes | yes | terminal | preferred |

MCP unavailability must not weaken governance: use
`specsmith preflight "..." --json`, `specsmith audit`, and
`specsmith checkpoint`. A missing skill changes only procedural assistance, not
the underlying requirements or preflight gate. Zoo Code must preserve history
and enter an explicit degraded state when Specsmith cannot authorize a context
transition; it must not silently use its native summarizer.

For the full rationale, command mappings, and examples, see the repository
architecture decision record `docs/INVOCATION_STRATEGY.md`.
