# Multi-Agent DAG Dispatcher

The `specsmith dispatch` command group and `src/specsmith/agent/dispatch/` package implement a governed, concurrent multi-agent work scheduler (REQ-321..334).

## Overview

Instead of running agents sequentially in a flat GroupChat, the dispatcher:

1. Decomposes a task into a **Directed Acyclic Graph** of typed worker nodes
2. Runs independent nodes **concurrently** (up to `max_workers`)
3. Uses **fail-forward** semantics: a failed node blocks only its dependents; siblings keep running
4. Passes each completed node's output to its successors via ESDB context injection
5. Persists all state transitions to `.specsmith/dispatch/<dag_id>/events.jsonl` for resume and Kairos live view

## CLI

### `specsmith dispatch run`

```bash
specsmith dispatch run "add REST endpoint with tests" \
    --max-workers 4 \      # concurrent worker ceiling (default 4)
    --json                 # stream JSONL events to stdout
    --endpoint http://localhost:8000/v1 \
    --model "Qwen/Qwen2.5-Coder-32B"
```

The dispatcher calls `_call_planner(task)` which asks the PlannerAgent to emit a JSON array of task nodes. If the LLM is unavailable, it falls back to a single-node DAG.

To supply an explicit plan (bypasses LLM decomposition):

```python
from specsmith.agent.orchestrator import Orchestrator

orch = Orchestrator()
summary = orch.run_dispatch(
    "add REST endpoint with tests",
    planner_output=[
        {"id": "design", "title": "Design schema", "role": "architect", "depends_on": []},
        {"id": "impl",   "title": "Implement",      "role": "coder",     "depends_on": ["design"]},
        {"id": "test",   "title": "Write tests",    "role": "tester",    "depends_on": ["design"]},
        {"id": "review", "title": "Code review",    "role": "reviewer",  "depends_on": ["impl","test"]},
    ],
)
print(f"{len(summary.completed)} completed, {len(summary.failed)} failed")
```

### `specsmith dispatch status`

```bash
specsmith dispatch status --dag-id abc123def456   # specific run
specsmith dispatch status                          # most recent run
```

Prints per-node status from the persisted events.jsonl.

### `specsmith dispatch list`

```bash
specsmith dispatch list
```

Lists all saved runs under `.specsmith/dispatch/` with completed/failed counts.

### `specsmith dispatch retry`

```bash
specsmith dispatch retry --node impl --dag-id abc123def456
```

Re-runs a single FAILED or BLOCKED node from a checkpoint. COMPLETED nodes are
never re-executed (REQ-330). The retry creates a new `<dag_id>-retry-<node_id>` run.

## HTTP/SSE surface (specsmith serve)

When `specsmith serve` is running, the dispatch surface is available at:

| Endpoint | Description |
|---|---|
| `POST /api/dispatch/run` | Start a DAG run. Body: `{"task": "...", "max_workers": 4}`. Returns `{"dag_id": "..."}`. |
| `GET /api/dispatch/events?dag_id=X` | SSE stream — replays persisted events then streams live. |
| `GET /api/dispatch/status?dag_id=X` | Current per-node status JSON. |
| `GET /api/dispatch/list` | All saved run IDs. |
| `POST /api/dispatch/retry` | Body: `{"dag_id": "...", "node_id": "..."}`. Creates a new single-node retry run. |
| `POST /api/dispatch/abort` | Body: `{"dag_id": "...", "node_id": "..."}`. Sets the per-node abort flag — the worker exits at the next checkpoint. |

### Abort semantics

`POST /api/dispatch/abort` performs **cooperative** cancellation: it sets a
`threading.Event` that the worker thread checks between steps (before governance
preflight, after preflight, after worker acquire, after LLM invocation). The node
transitions to FAILED at the next safe checkpoint — it does not interrupt a live
LLM call mid-stream, but it will abort before the result is written to ESDB.

## TaskDAG data model

```python
from specsmith.agent.dispatch import TaskDAGBuilder, TaskStatus

# Build from a planner output string or list
dag = TaskDAGBuilder.build(
    "implement feature X",
    dag_id="my-run-001",         # optional, auto-generated if omitted
    planner_output=[             # optional; falls back to single-node if omitted
        {"id": "arch", "title": "Design", "role": "architect", "depends_on": []},
        {"id": "impl", "title": "Implement", "role": "coder",  "depends_on": ["arch"]},
    ],
)

# Cycle detection at build time
from specsmith.agent.dispatch import DAGValidationError
try:
    bad = TaskDAGBuilder.build("test", planner_output=[
        {"id": "a", "title": "A", "role": "coder", "depends_on": ["b"]},
        {"id": "b", "title": "B", "role": "coder", "depends_on": ["a"]},
    ])
except DAGValidationError as e:
    print(f"Cycle: {e}")  # Cycle detected in task DAG — execution aborted.

# Query the DAG
print(dag.runnable_nodes())      # nodes whose deps are all COMPLETED
print(dag.all_terminal())        # True when every node is COMPLETED/FAILED/BLOCKED

# Fail-forward blocking
dag.get("arch").status = TaskStatus.FAILED
blocked = dag.blocked_by_failure("arch")  # returns transitively blocked node ids
```

## TaskNode schema (REQ-323)

| Field | Type | Description |
|---|---|---|
| `id` | `str` | Unique slug within the DAG |
| `title` | `str` | Human-readable description |
| `role` | `str` | Worker role (maps to `ROLE_TOOLS`) |
| `depends_on` | `list[str]` | Node ids that must be COMPLETED first |
| `status` | `TaskStatus` | PENDING \| RUNNING \| COMPLETED \| FAILED \| BLOCKED |
| `context_in` | `list[str]` | ESDB ChronoRecord IDs injected as context |
| `context_out` | `str \| None` | ESDB record ID written on completion |
| `result` | `DispatchResult \| None` | Populated on completion or failure |

## Available roles

| Role | Description | Compiler tools |
|---|---|---|
| `coder` | Write and patch code | gcc, arm-gcc, clang-format, clang-tidy, vsg |
| `reviewer` | Review code and linting | clang-tidy, vsg |
| `tester` | Write and run tests | gcc, arm-gcc |
| `architect` | Design and document | clang-format |
| `researcher` | Search and synthesise | — |
| `embedded-coder` | Embedded C/C++/VHDL | All compiler tools |

## Event stream format

Each event is a JSON object on a single line (JSONL):

```jsonl
{"dag_id":"abc123","event_type":"node_started","node_id":"impl","ts":"...","payload":{"role":"coder"}}
{"dag_id":"abc123","event_type":"node_completed","node_id":"impl","ts":"...","payload":{"esdb_record_id":"dispatch-impl-a1b2c3d4","summary":"..."}}
{"dag_id":"abc123","event_type":"node_failed","node_id":"test","ts":"...","payload":{"error":"..."}}
{"dag_id":"abc123","event_type":"node_blocked","node_id":"review","ts":"...","payload":{"because_of":"test"}}
{"dag_id":"abc123","event_type":"dag_done","node_id":"","ts":"...","payload":{"equilibrium":false,...}}
```

Events are persisted to `.specsmith/dispatch/<dag_id>/events.jsonl` and this
directory is excluded from git (see `.gitignore`).

## Kairos dispatch panel

The `app/` directory contains a Rust (egui/eframe) application that subscribes
to the SSE stream and renders the dispatch view:

- **DAG graph** — nodes coloured by status (grey/blue/green/red/amber), click to open detail
- **Gantt timeline** — horizontal bars showing parallelism
- **Controls** — Retry (FAILED/BLOCKED), Abort (RUNNING) per node

```bash
cd app
cargo build --release
./target/release/kairos --dag-id abc123def456
```

See `app/README.md` for full build and usage instructions.

## Resumability (REQ-330)

A saved run can be resumed by replaying its events:

```python
from specsmith.agent.dispatch import EventEmitter
from pathlib import Path

# Read all past events
events = EventEmitter.replay(Path("."), "abc123def456")

# Find which nodes need retrying
failed_nodes = [e.node_id for e in events if e.event_type == "node_failed"]

# Retry via CLI
# specsmith dispatch retry --node <node_id> --dag-id abc123def456
```

The `dispatch retry` command and `POST /api/dispatch/retry` both rebuild a
minimal single-node DAG from the original run's role information and run it
as a new checkpoint-linked sub-run.


## Kairos DAG Panel — Topological Layout

The Kairos dispatch panel (`app/`) uses a **topological layout** algorithm:
each node is positioned at a horizontal level equal to the depth of its
longest dependency path. Root nodes (no deps) are at level 0; a node depending
on a level-2 node sits at level 3. Within each level, nodes are evenly
distributed vertically.

`depends_on` is included in every `node_started` SSE event payload so Kairos
can reconstruct the full dependency graph from the live stream without any
separate graph-structure endpoint.

**Edges** are drawn as cubic bezier curves from the right edge of each parent
to the left edge of each child, with arrowheads at the child end, rendered
behind the node layer.

## Abort — Cooperative Cancellation (0.5 s polling)

`POST /api/dispatch/abort` uses **cooperative cancellation**:
`abort_node(node_id)` sets a per-node `threading.Event`. `_run_node` checks
this flag at four safe checkpoints — before preflight, after preflight,
after worker acquire, and **during LLM invocation**.

For the LLM invocation checkpoint, `_invoke_worker_monitored()` runs the AG2
`initiate_chat` call in a daemon sub-thread and polls the abort flag every
**0.5 s** via `thread.join(timeout=0.5)`. If the flag fires mid-call,
`_run_node` raises `_NodeAbortedError` immediately without waiting for the
sub-thread to finish. The LLM sub-thread completes naturally in the background.

The node always transitions to FAILED with error `"Aborted: ..."` so every
abort is traceable in events.jsonl (REQ-320).

## Compliance — REQ-313..320 (EU AI Act Art. 12/13/14)

Eight multi-agent governance traceability requirements (compliance plan
5939f743) are implemented alongside the dispatcher:

| REQ | What is enforced |
|-----|-----------------|
| REQ-313 | Every `AgentDispatcher.run()` appends a `dispatch` ledger entry to LEDGER.md (EU AI Act Art. 12 record-keeping) |
| REQ-314 | `node_started` payload includes worker `role` and `depends_on` for audit trail transparency (Art. 13) |
| REQ-315 | `DispatchSummary.dag_id` traces every run back to its originating Orchestrator call |
| REQ-316 | Governance preflight blocks write `"Governance preflight blocked: ..."` to the node error field (Art. 14) |
| REQ-317 | `context_in` ESDB record IDs are stored in `TaskNode` for traceable information flow between agents |
| REQ-318 | `events.jsonl` checkpoint prevents re-execution of COMPLETED nodes on retry (REQ-330 correctness) |
| REQ-319 | ESDB `dispatch_result` records include `dag_id` and `node_id` in both evidence list and data dict |
| REQ-320 | Aborted nodes set error to `"Aborted: ..."` to distinguish intentional stops from failures (Art. 14 §4) |

All 8 requirements have pytest coverage in `tests/test_dispatch.py`
(`TestMultiAgentCompliance`).
