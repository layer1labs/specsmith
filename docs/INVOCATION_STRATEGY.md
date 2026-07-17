# Invocation Strategy

**Issue:** [#343](https://github.com/layer1labs/specsmith/issues/343)
**Phase:** Architectural decision record
**Status:** Proposed

## Overview

Specsmith supports four invocation mechanisms. This document defines when each
should be used, their relationships, and provides a decision matrix for optimal
UX, reliability, and cross-environment compatibility.

```mermaid
graph TD
    A[Human Operator] --> B[Nexus REPL]
    A --> C[Direct Shell]
    D[AI Agent - IDE] --> E[MCP Tools]
    D --> B
    D --> C
    F[CI/CD Pipeline] --> C
    G[AI Agent - Skill] --> H[Skill Instructions]
    H --> C
    H --> E

    B --> I[/specsmith CLI pass-through]
    B --> J[Broker: classify + preflight + execute]
    C --> K[specsmith <command>]
    E --> L[governance_preflight / audit / checkpoint]

    style A fill:#e1f5fe
    style D fill:#f3e5f5
    style F fill:#e8f5e9
    style E fill:#fff3e0
    style B fill:#e1f5fe
    style C fill:#e8f5e9
```

## Invocation Mechanisms

### 1. MCP Tools (Model Context Protocol)

**Entry point:** `specsmith mcp serve`

**Tools exposed:**

| Tool | Purpose | Returns |
|---|---|---|
| `governance_preflight` | Gate a change through governance | decision, work_item_id, requirement_ids |
| `governance_audit` | Run governance health check | health status, check results |
| `governance_checkpoint` | Emit GOVERNANCE ANCHOR | phase, health, counts |
| `governance_phase` | Current AEE phase + readiness | phase, readiness_pct, failing_checks |
| `governance_req_list` | List all requirements | id, title, status, covered |
| `governance_trace_seal` | Seal milestone in trace vault | trace_id, hash |

**Best for:** AI agent-to-agent communication, structured governance decisions,
programmatic access from MCP-compatible clients.

**Environments:** Cursor, VS Code extensions, Warp, Claude Code, any MCP client.

**Pros:**
- Structured JSON I/O with schema validation
- Governance-enforced with traceable decisions
- No server process management needed (stdio-based)

**Cons:**
- Requires MCP server configuration in client
- Limited to the 6 tools defined by MCP
- No interactive REPL capabilities

**Configuration example (Cursor):**
```json
{
  "specsmith-governance": {
    "command": "specsmith",
    "args": ["mcp", "serve"]
  }
}
```

### 2. Slash Commands (Nexus REPL)

**Entry point:** `specsmith nexus` (or `specsmith run`)

**Available slash commands:**

| Command | Purpose |
|---|---|
| `/specsmith <args>` | Direct CLI pass-through to any specsmith command |
| `/plan <description>` | Create a step-by-step plan via orchestrator |
| `/ask <question>` | Clarify intent and answer via orchestrator |
| `/fix <issue>` | Modify code to fix an issue via orchestrator |
| `/test` | Run tests for the project |
| `/commit` | Create a git commit |
| `/pr` | Prepare a pull request |
| `/undo` | Revert the last action or commit |
| `/context <query>` | Show repo knowledge and search context |
| `/why` | Toggle verbose governance details |
| `/exit`, `/quit` | Exit the REPL |

**Best for:** Interactive sessions, quick governance operations, human operators
working in a terminal.

**Environments:** Nexus REPL, any terminal with REPL mode.

**Pros:**
- Simple slash syntax, built into specsmith CLI
- No extra setup beyond `specsmith run`
- Natural language broker classifies intent automatically

**Cons:**
- REPL-bound, not scriptable in non-interactive contexts
- 120-second timeout on CLI pass-through commands
- No structured output for programmatic consumption

### 3. Skills (Procedural Instructions)

**Entry point:** Loaded via `skill` tool by AI agents

**Available skills:**

| Skill | Purpose |
|---|---|
| `execution` | Local command execution with specsmith governance |
| `git` | Git platform management with specsmith governance |
| `release` | Release creation and deployment with specsmith governance |
| `testing-configuration` | Configure Playwright, pytest, and others |
| `testing-parallel-execution` | Execute tests in parallel |
| `testing-artifact-management` | Manage screenshots, videos, logs |
| `testing-cicd-integration` | Integrate testing with CI/CD pipelines |
| `testing-coverage-reporting` | Generate and track test coverage |
| `testing-environment-isolation` | Ensure proper test environment isolation |
| `testing-report-generation` | Automatically generate test reports |
| `playwright-testing` | End-to-end browser testing with Playwright |
| `lmstudio-integration` | Integrate with LMStudio for local AI |
| `ollama-integration` | Integrate with Ollama for local AI |
| `vllm-integration` | Integrate with VLLM for LLM serving |
| `webui-integration` | Integrate with WebUI platforms |
| `openterminal-integration` | Integrate with OpenTerminal |
| `specsmith-context-continuity` | Preserve state across handoffs |
| `specsmith-evidence-debugging` | Debug with evidence and hypotheses |
| `specsmith-governed-work` | Run requirement-bound work through governance |

**Best for:** Complex, multi-step workflows with specific domain procedures.
Skills provide rich procedural instructions that guide AI agents through
established patterns.

**Environments:** AI agents with skill-loading capability (Zoo, Roo, etc.).

**Pros:**
- Rich procedural instructions with domain-specific guidance
- Encapsulates best practices and project conventions
- Composable across skills

**Cons:**
- Skill must be loaded first, adding context overhead
- Not directly usable by humans in shell
- Skills are static Markdown; no runtime validation

### 4. Direct CLI (Command-Line Interface)

**Entry point:** `specsmith <command> [args]`

**Command categories:**

| Category | Commands | Purpose |
|---|---|---|
| **Project lifecycle** | `init`, `update`, `migrate-project` | Scaffold, upgrade, migrate projects |
| **Governance core** | `preflight`, `audit`, `sync`, `checkpoint`, `verify`, `clean` | Core governance operations |
| **Session management** | `serve`, `run`, `kill-session`, `session-show`, `session-clear`, `session-end` | Lifecycle of governed sessions |
| **Requirements/Tests** | `req add/list`, `test add/list`, `validate` | Manage requirements and tests |
| **Ledger/Trace** | `ledger`, `trace`, `commit`, `push`, `save`, `load`, `inspect` | Cryptographic trace management |
| **Branch/PR** | `branch`, `pr`, `pull`, `push` | Git workflow operations |
| **Agent operations** | `agent ask`, `agents`, `chat`, `dispatch` | AI agent interaction |
| **MCP server** | `mcp generate`, `mcp serve`, `mcp projects` | MCP server management |
| **Skills** | `skills build/list/activate/deactivate/delete` | AI skills lifecycle |
| **ESDB** | `esdb status/migrate/replay/export/import/backup/rollback/compact` | Database management |
| **Model intelligence** | `model-intel sync/scores/recommendations` | AI model management |
| **Phase management** | `phase set/show` | AEE phase transitions |
| **Monitoring** | `ps`, `exec`, `abort`, `watch` | Process and CI monitoring |
| **Configuration** | `config`, `channel`, `auth`, `workspace` | Project configuration |
| **Utilities** | `info`, `scan`, `api-surface`, `optimize`, `gui`, `credits` | General utilities |

**Best for:** Scripting, CI/CD pipelines, automation, shell scripts, headless
environments.

**Environments:** Any shell (bash, pwsh, cmd), CI runners, cron jobs.

**Pros:**
- Fully scriptable with predictable exit codes
- No server process required
- Works in headless/CI environments
- `--json` flag for structured output on most commands
- `--project-dir` flag for cross-project operations

**Cons:**
- Less structured output than MCP (text-based by default)
- No built-in governance enforcement without explicit flags
- Large command surface requires documentation

## Decision Matrix

### Primary Selection

| Scenario | Preferred | Fallback | Rationale |
|---|---|---|---|
| AI agent in IDE (Cursor/VS Code) | MCP tools | Slash commands via `/specsmith` | Structured JSON, governance-enforced |
| AI agent with skill loading | Skills + Direct CLI | MCP tools | Rich procedural guidance for complex workflows |
| Interactive terminal session | Slash commands | Direct CLI | Natural language broker, simple syntax |
| CI/CD pipeline | Direct CLI | MCP tools | No server needed, fully scriptable |
| Shell script / automation | Direct CLI | MCP tools | Predictable exit codes, `--json` output |
| Headless / SSH session | Direct CLI | Slash commands | No REPL support needed |
| Human operator quick check | Slash commands | Direct CLI | Simple `/specsmith audit` syntax |
| Cross-environment handoff | Skills + MCP | Direct CLI | Skills encode procedure, MCP enforces governance |

### Governance Command Mapping

Every governance operation is available through multiple mechanisms. Use this
table to select the appropriate invocation for your context:

| Operation | MCP | Slash | Direct CLI | Skill |
|---|---|---|---|---|
| Preflight a change | `governance_preflight` | `/specsmith preflight` | `specsmith preflight` | `specsmith-governed-work` |
| Run audit | `governance_audit` | `/specsmith audit` | `specsmith audit` | N/A |
| Checkpoint | `governance_checkpoint` | `/specsmith checkpoint` | `specsmith checkpoint` | N/A |
| Check phase | `governance_phase` | `/specsmith session-show` | `specsmith session-show` | N/A |
| List requirements | `governance_req_list` | `/specsmith req list` | `specsmith req list` | N/A |
| Seal trace | `governance_trace_seal` | `/specsmith commit` | `specsmith commit` | `git` |
| Save governance | N/A | `/specsmith save` | `specsmith save` | N/A |
| Load governance | N/A | `/specsmith load` | `specsmith load` | N/A |
| Kill session | N/A | N/A | `specsmith kill-session` | N/A |
| Watch CI | N/A | `/specsmith watch` | `specsmith watch` | N/A |

### Environment Compatibility

| Environment | MCP | Slash | Skills | Direct CLI |
|---|---|---|---|---|
| Cursor | Yes | Via `/specsmith` | Via agent | Via terminal |
| VS Code | Yes | Via terminal | Via agent | Via terminal |
| Warp | Yes | Via terminal | Via agent | Yes |
| Claude Code | Yes | Via terminal | Via agent | Yes |
| GitHub Actions | No | No | No | Yes |
| GitLab CI | No | No | No | Yes |
| Local terminal | No | Yes | Via agent | Yes |
| SSH session | No | No | No | Yes |

## Relationship Between CLI, AEE, and Agent Modes

```mermaid
flowchart LR
    subgraph Human
        H1[Terminal]
    end

    subgraph AI Agent
        A1[IDE Agent]
        A2[Skill Agent]
    end

    subgraph Governance Layer
        G1[Nexus Broker]
        G2[ESDB]
        G3[Trace Vault]
    end

    subgraph Execution
        E1[Direct CLI]
        E2[MCP Server]
        E3[Nexus REPL]
    end

    H1 --> E1
    H1 --> E3
    A1 --> E2
    A1 --> E1
    A2 --> E1
    A2 --> E2

    E1 --> G1
    E2 --> G1
    E3 --> G1

    G1 --> G2
    G1 --> G3

    style Human fill:#e1f5fe
    style "AI Agent" fill:#f3e5f5
    style Governance fill:#fff3e0
    style Execution fill:#e8f5e9
```

**Key relationships:**

1. **CLI is the universal executor.** All three invocation mechanisms (MCP,
   slash, skills) ultimately delegate to CLI commands. The CLI is the single
   point of truth for specsmith operations.

2. **MCP is the structured gateway.** MCP tools wrap CLI commands with JSON
   schema validation and return structured results. The MCP server internally
   calls the same CLI functions.

3. **Slash commands are the interactive layer.** The Nexus REPL provides a
   natural language interface that classifies intent, runs preflight, and
   delegates to the orchestrator or CLI pass-through.

4. **Skills are the procedural layer.** Skills provide step-by-step instructions
   that tell AI agents *how* to use the CLI and MCP tools for specific domains.

5. **Governance is the invariant.** All paths flow through the Nexus Broker
   (`specsmith.agent.broker`) which enforces preflight decisions, tracks state
   in ESDB, and maintains the cryptographic trace.

## Common Workflows

### Workflow 1: New Project Setup

```bash
# 1. Scaffold the project
specsmith init --mode team --guided

# 2. Run initial audit
specsmith audit --project-dir ./my-project

# 3. Enter interactive mode for first changes
specsmith run --project-dir ./my-project
# Then in REPL: /plan "Add authentication requirement"
```

### Workflow 2: AI-Assisted Development in Cursor

```
# 1. Add MCP server config in Cursor settings:
# { "specsmith-governance": { "command": "specsmith", "args": ["mcp", "serve"] } }

# 2. Agent invokes governance_preflight before any code change:
# Tool: governance_preflight
# Input: { "utterance": "Add user registration endpoint", "project_dir": "/path/to/project" }

# 3. If decision == "accepted", agent proceeds with implementation

# 4. Agent invokes governance_checkpoint after changes:
# Tool: governance_checkpoint
# Input: { "project_dir": "/path/to/project" }
```

### Workflow 3: CI/CD Pipeline Integration

```yaml
# .github/workflows/specsmith-governance.yml
jobs:
  governance-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run governance audit
        run: specsmith audit --project-dir . --json

      - name: Validate requirements
        run: specsmith validate --strict --project-dir .

      - name: Check phase readiness
        run: specsmith session-show --project-dir . --json

      - name: Watch for CI green
        run: specsmith watch --project-dir .
```

### Workflow 4: Interactive Development Session

```bash
# Start governed session
specsmith run

# In Nexus REPL:
nexus> /plan "Implement user authentication"
# Broker classifies intent, runs preflight, renders plan

nexus> /fix "Fix the JSON parse error in App.tsx"
# Broker runs preflight, executes fix via orchestrator
```

### Workflow 5: Skill-Guided Complex Workflow

```bash
# 1. Agent loads the 'execution' skill for local command execution
# 2. Skill instructs: run specsmith preflight before any code change
# 3. Agent runs: specsmith preflight "Add rate limiting to API" --json
# 4. If accepted, skill guides through implementation steps
# 5. Agent runs: specsmith checkpoint --project-dir .
# 6. Skill verifies governance anchor before proceeding
```

## Design Decisions

### D1: CLI as Universal Executor

**Decision:** All invocation mechanisms ultimately delegate to CLI commands.

**Rationale:** The CLI is the single point of truth for specsmith operations.
MCP tools, slash commands, and skills all call the same underlying functions.
This ensures consistency and prevents divergence between invocation paths.

**Implication:** When fixing bugs or adding features, modify the CLI layer.
MCP and REPL will automatically inherit the fix.

### D2: MCP for Structured Agent Communication

**Decision:** MCP is the preferred mechanism for AI agent-to-governance communication.

**Rationale:** MCP provides structured JSON I/O with schema validation, which
is essential for reliable programmatic governance decisions. The 6 tools
cover all governance operations that agents need.

**Implication:** IDE agents should configure MCP as their primary governance
interface, falling back to `/specsmith` CLI pass-through for operations
not covered by MCP tools.

### D3: Slash Commands for Interactive Use

**Decision:** Slash commands in Nexus REPL are the preferred interactive interface.

**Rationale:** The natural language broker classifies intent automatically,
making it easy for humans to interact without memorizing command syntax.
The `/specsmith` pass-through provides access to all CLI commands.

**Implication:** Human operators should use `specsmith run` for interactive
sessions, reserving direct CLI for scripting and automation.

### D4: Skills for Procedural Guidance

**Decision:** Skills provide domain-specific procedural instructions but do
not replace CLI or MCP for actual execution.

**Rationale:** Skills encode best practices and project conventions that guide
AI agents through complex workflows. They complement (not replace) the
execution mechanisms.

**Implication:** Agents should load relevant skills before complex operations,
then use CLI or MCP for the actual execution.

### D5: Governance Invariant Across All Paths

**Decision:** All invocation paths flow through the Nexus Broker for governance
enforcement.

**Rationale:** The broker (`specsmith.agent.broker`) provides intent classification,
scope inference, preflight decisions, and bounded-retry execution. This ensures
consistent governance regardless of invocation mechanism.

**Implication:** No invocation path can bypass governance. Even direct CLI
commands that skip the broker can be governed via explicit preflight flags.

## Migration Path

For projects not yet using a structured invocation strategy:

1. **Phase 1:** Adopt direct CLI for all automation and scripting
2. **Phase 2:** Configure MCP in IDE agents for governance-enforced development
3. **Phase 3:** Use Nexus REPL for interactive sessions
4. **Phase 4:** Load relevant skills for complex domain workflows

## References

- Issue: [#343](https://github.com/layer1labs/specsmith/issues/343)
- MCP Server: [`src/specsmith/mcp_server.py`](src/specsmith/mcp_server.py)
- CLI: [`src/specsmith/cli.py`](src/specsmith/cli.py)
- REPL: [`src/specsmith/agent/repl.py`](src/specsmith/agent/repl.py)
- Broker: [`src/specsmith/agent/broker.py`](src/specsmith/agent/broker.py)
- Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)