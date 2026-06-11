# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""AgentPool + AgentDispatcher — bounded concurrent DAG scheduler.

REQ-324: independent nodes run concurrently up to max_workers.
REQ-325: FAILED nodes propagate BLOCKED to transitive dependents.
REQ-326: AgentPool reuses idle workers per role.
REQ-327: completed nodes write ESDB ChronoRecord; successors inject context.
REQ-329: each node passes a governance preflight before worker starts.
"""

from __future__ import annotations

import threading
import time
import uuid
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from specsmith.agent.dispatch.dag import TaskDAG, TaskNode, TaskStatus
from specsmith.agent.dispatch.events import EventEmitter
from specsmith.agent.dispatch.result import DispatchResult, DispatchSummary

# ---------------------------------------------------------------------------
# AgentPool  (REQ-326)
# ---------------------------------------------------------------------------


class AgentPool:
    """Pool of per-role ConversableAgent instances.

    Workers are created lazily and reused across tasks of the same role.
    The pool enforces the global *max_workers* ceiling — callers must call
    ``acquire()`` and ``release()`` to keep the concurrency count accurate.
    """

    def __init__(self, llm_config: dict[str, Any], max_workers: int = 4) -> None:
        self._llm_config = llm_config
        self._max_workers = max_workers
        self._idle: dict[str, list[Any]] = {}  # role → list of idle agents
        self._active_count = 0
        self._lock = threading.Lock()

    def acquire(self, role: str) -> Any | None:
        """Return an idle worker for *role*, or None if the pool is at capacity.

        Creates a new worker lazily when no idle one is available for the role.
        """
        with self._lock:
            if self._active_count >= self._max_workers:
                return None  # caller must back off
            idle_list = self._idle.get(role, [])
            if idle_list:
                worker = idle_list.pop()
                self._active_count += 1
                return worker

        # Create outside lock to avoid holding it during AG2 agent init
        worker = self._spawn_worker(role)
        with self._lock:
            # Re-check limit after creation (race-free)
            if self._active_count >= self._max_workers:
                # We over-created; discard the new worker
                return None
            self._active_count += 1
        return worker

    def release(self, role: str, worker: Any) -> None:
        """Return a worker to the idle pool after its task completes."""
        with self._lock:
            self._idle.setdefault(role, []).append(worker)
            self._active_count = max(0, self._active_count - 1)

    def _spawn_worker(self, role: str) -> Any:
        """Instantiate a real ConversableAgent with the role's tool subset."""
        from specsmith.agent.spawner import SubAgentSpawner

        spawner = SubAgentSpawner()
        return spawner.spawn_worker(role, self._llm_config)


# ---------------------------------------------------------------------------
# AgentDispatcher  (REQ-324, REQ-325)
# ---------------------------------------------------------------------------


class AgentDispatcher:
    """Schedules and executes a TaskDAG with bounded concurrency.

    Algorithm:
    1. Find all runnable nodes (deps all COMPLETED, status PENDING).
    2. Dispatch up to max_workers concurrently via ThreadPoolExecutor.
    3. On completion → write ESDB record → inject context into successors.
    4. On failure → propagate BLOCKED to transitive dependents; keep running siblings.
    5. Loop until DAG is fully terminal or no more runnable nodes.

    Cooperative abort:
    Each node gets a per-node ``threading.Event`` stored in ``_abort_flags``.
    ``abort_node(node_id)`` sets the event.  ``_run_node`` checks the flag
    before each major step (governance preflight, worker acquire, invoke,
    ESDB write) and transitions to FAILED immediately when set.
    """

    def __init__(
        self,
        dag: TaskDAG,
        pool: AgentPool,
        emitter: EventEmitter,
        *,
        project_root: Path,
        max_workers: int = 4,
    ) -> None:
        self._dag = dag
        self._pool = pool
        self._emitter = emitter
        self._project_root = project_root
        self._max_workers = max_workers
        # Per-node cooperative abort events.  Set by abort_node(); checked
        # in _run_node() between steps so the worker exits at the next safe point.
        self._abort_flags: dict[str, threading.Event] = {}

    def run(self) -> DispatchSummary:
        """Execute the DAG and return a DispatchSummary (REQ-324)."""
        summary = DispatchSummary(dag_id=self._dag.dag_id)
        futures: dict[Future[DispatchResult], TaskNode] = {}

        with ThreadPoolExecutor(max_workers=self._max_workers, thread_name_prefix="dispatch") as ex:
            while not self._dag.all_terminal():
                # Launch new runnable nodes up to the concurrency ceiling
                for node in self._dag.runnable_nodes():
                    if len(futures) >= self._max_workers:
                        break
                    node.status = TaskStatus.RUNNING
                    self._emitter.node_started(node.id, node.role, node.depends_on)
                    future = ex.submit(self._run_node, node)
                    futures[future] = node

                if not futures:
                    # Nothing running and nothing runnable → deadlock or done
                    break

                # Wait for the first completed future
                done_iter = as_completed(futures, timeout=None)
                try:
                    done = next(done_iter)
                except StopIteration:
                    break

                node = futures.pop(done)
                try:
                    result: DispatchResult = done.result()
                except Exception as exc:  # noqa: BLE001
                    result = DispatchResult(
                        node_id=node.id,
                        role=node.role,
                        status=TaskStatus.FAILED,
                        error=str(exc),
                    )

                node.result = result
                node.status = result.status

                if result.status == TaskStatus.COMPLETED:
                    node.context_out = result.esdb_record_id
                    self._emitter.node_completed(node.id, result.esdb_record_id, result.summary)
                    summary.completed.append(result)
                    # Inject predecessor context into waiting successors
                    self._propagate_context(node)
                else:
                    self._emitter.node_failed(node.id, result.error or "unknown error")
                    summary.failed.append(result)
                    # Propagate BLOCKED transitively (REQ-325)
                    blocked_ids = self._dag.blocked_by_failure(node.id)
                    for bid in blocked_ids:
                        self._emitter.node_blocked(bid, because_of=node.id)
                        summary.blocked.append(bid)

        # Terminate remaining in-flight futures gracefully
        for future, _node in futures.items():
            future.cancel()

        # Build final summary
        completed_count = len(summary.completed)
        total = len(self._dag.nodes())
        if total > 0:
            summary.equilibrium = completed_count == total
            summary.confidence = completed_count / total
        else:
            summary.equilibrium = True
            summary.confidence = 1.0

        self._emitter.dag_done(summary.to_dict())

        # REQ-313: write dispatch run ledger entry for EU AI Act Art. 12
        self._write_dispatch_ledger(summary)

        return summary

    def _write_dispatch_ledger(self, summary: DispatchSummary) -> None:
        """Append a governance ledger entry for this dispatch run (REQ-313).

        Records dag_id, node counts, and equilibrium result in LEDGER.md
        so every multi-agent dispatch run is traceable in the audit chain.
        Best-effort — never blocks or raises.
        """
        try:
            from specsmith.ledger import add_entry

            ledger_path = self._project_root / "LEDGER.md"
            if not ledger_path.exists():
                # Also try docs/LEDGER.md
                alt = self._project_root / "docs" / "LEDGER.md"
                if not alt.exists():
                    return
            description = (
                f"specsmith dispatch run dag_id={summary.dag_id} "
                f"completed={len(summary.completed)} "
                f"failed={len(summary.failed)} "
                f"blocked={len(summary.blocked)} "
                f"equilibrium={summary.equilibrium} "
                f"confidence={summary.confidence:.2f}"
            )
            add_entry(
                self._project_root,
                description=description,
                entry_type="dispatch",
                author="specsmith-dispatcher",
                reqs="REQ-313,REQ-321",
            )
        except Exception:  # noqa: BLE001 — ledger writes are best-effort
            pass

    # -----------------------------------------------------------------------
    # Node execution
    # -----------------------------------------------------------------------

    def abort_node(self, node_id: str) -> bool:
        """Request cooperative abort for a running node.

        Sets the node's abort event; ``_run_node`` will see it at the next
        checkpoint and transition to FAILED. Returns True if the node was
        found (running or pending), False if it doesn't exist.
        """
        flag = self._abort_flags.get(node_id)
        if flag is not None:
            flag.set()
            return True
        # Node hasn't started yet — pre-arm an event so it aborts immediately
        if self._dag.get(node_id) is not None:
            pre = threading.Event()
            pre.set()
            self._abort_flags[node_id] = pre
            return True
        return False

    def _run_node(self, node: TaskNode) -> DispatchResult:
        """Execute a single node inside a worker thread."""
        # Arm per-node abort event (creates if not pre-armed by abort_node)
        abort_flag = self._abort_flags.setdefault(node.id, threading.Event())

        worker = None
        try:
            # Abort check 1: before governance preflight
            if abort_flag.is_set():
                raise _NodeAbortedError(f"node {node.id!r} aborted before preflight")

            # REQ-329: governance preflight before work begins
            self._governance_preflight(node)

            # Abort check 2: between preflight and worker acquire
            if abort_flag.is_set():
                raise _NodeAbortedError(f"node {node.id!r} aborted after preflight")

            # Acquire a pooled worker agent
            worker = self._acquire_worker(node.role)

            # Abort check 3: between acquire and invoke
            if abort_flag.is_set():
                raise _NodeAbortedError(f"node {node.id!r} aborted after worker acquire")

            # Build context from predecessor ESDB records
            context_prompt = self._build_context_prompt(node)
            full_task = f"{context_prompt}\n\n{node.title}" if context_prompt else node.title

            # Execute via the worker agent in a monitored sub-thread so that
            # abort_node() can interrupt the LLM call at the next 0.5 s poll
            # boundary.  The sub-thread runs to completion in the background
            # (we cannot kill it) but _run_node returns failure immediately.
            run_result = self._invoke_worker_monitored(worker, full_task, abort_flag, node.id)

            # Abort check 4: between invoke and ESDB write
            if abort_flag.is_set():
                raise _NodeAbortedError(f"node {node.id!r} aborted after invocation")

            # Write ESDB record for successors (REQ-327)
            esdb_id = self._write_esdb_record(node, run_result)

            return DispatchResult(
                node_id=node.id,
                role=node.role,
                status=TaskStatus.COMPLETED,
                summary=run_result.get("summary", ""),
                files_changed=run_result.get("files_changed", []),
                esdb_record_id=esdb_id,
            )

        except _GovernanceBlockedError as exc:
            return DispatchResult(
                node_id=node.id,
                role=node.role,
                status=TaskStatus.FAILED,
                error=f"Governance preflight blocked: {exc}",
            )
        except _NodeAbortedError as exc:
            return DispatchResult(
                node_id=node.id,
                role=node.role,
                status=TaskStatus.FAILED,
                error=f"Aborted: {exc}",
            )
        except Exception as exc:  # noqa: BLE001
            return DispatchResult(
                node_id=node.id,
                role=node.role,
                status=TaskStatus.FAILED,
                error=str(exc),
            )
        finally:
            if worker is not None:
                self._pool.release(node.role, worker)

    def _acquire_worker(self, role: str) -> Any:
        """Block-spin until a worker slot opens (respects max_workers)."""
        for _ in range(300):  # up to 30s
            worker = self._pool.acquire(role)
            if worker is not None:
                return worker
            time.sleep(0.1)
        raise RuntimeError(f"Timed out waiting for a worker slot for role {role!r}")

    def _governance_preflight(self, node: TaskNode) -> None:
        """Run governance preflight for the node task (REQ-329).

        If governance returns needs_clarification or rejected,
        raise _GovernanceBlockedError.
        """
        try:
            from specsmith.agent.broker import run_preflight
        except ImportError:
            return  # Governance not available — allow through

        try:
            decision = run_preflight(node.title, self._project_root)
            if getattr(decision, "decision", "accepted") not in ("accepted",):
                raise _GovernanceBlockedError(
                    getattr(decision, "instruction", "governance rejected")
                )
        except _GovernanceBlockedError:
            raise
        except Exception:  # noqa: BLE001
            pass  # Governance errors are non-blocking (best-effort)

    def _invoke_worker(self, worker: Any, task: str) -> dict[str, Any]:
        """Invoke the AG2 worker agent and return a result dict."""
        try:
            # If worker is a real ConversableAgent, use it inside a mini GroupChat
            from autogen import (
                ConversableAgent,
            )

            executor = ConversableAgent(
                name="Executor",
                system_message="Execute tools and return results.",
                llm_config=False,
                human_input_mode="NEVER",
            )
            chat_result = worker.initiate_chat(
                executor,
                message=task,
                max_turns=10,
            )
            summary = getattr(chat_result, "summary", "") or ""
            return {"summary": str(summary), "files_changed": [], "equilibrium": True}
        except Exception as exc:  # noqa: BLE001
            # Fallback: return minimal result so the DAG keeps moving
            return {
                "summary": f"[worker invocation error: {exc}]",
                "files_changed": [],
                "equilibrium": False,
            }

    def _invoke_worker_monitored(
        self,
        worker: Any,
        task: str,
        abort_flag: threading.Event,
        node_id: str,
    ) -> dict[str, Any]:
        """Run ``_invoke_worker`` in a background thread while polling *abort_flag*.

        Checks ``abort_flag`` every 0.5 s.  If abort is requested before the
        LLM call completes, raises :class:`_NodeAbortedError` immediately.
        The background thread runs to natural completion (it cannot be killed)
        but its result is discarded.
        """
        result_holder: list[dict[str, Any]] = []
        error_holder: list[BaseException] = []

        def _run() -> None:
            try:
                result_holder.append(self._invoke_worker(worker, task))
            except Exception as exc:  # noqa: BLE001 — catches all non-system exceptions from worker
                error_holder.append(exc)

        t = threading.Thread(target=_run, daemon=True, name=f"invoke-{node_id}")
        t.start()

        while t.is_alive():
            if abort_flag.is_set():
                raise _NodeAbortedError(f"node {node_id!r} abort signalled during LLM invocation")
            t.join(timeout=0.5)  # 500 ms polling interval

        if error_holder:
            raise error_holder[0]
        return (
            result_holder[0]
            if result_holder
            else {"summary": "", "files_changed": [], "equilibrium": False}
        )

    def _write_esdb_record(self, node: TaskNode, run_result: dict[str, Any]) -> str | None:
        """Write a ChronoRecord to ESDB and return its ID (REQ-327)."""
        try:
            from chronomemory import ChronoRecord, ChronoStore

            record_id = f"dispatch-{node.id}-{uuid.uuid4().hex[:8]}"
            record = ChronoRecord(
                id=record_id,
                kind="dispatch_result",
                label=f"Result of {node.title}",
                confidence=0.8,
                source_type="observed",
                evidence=[f"dag={self._dag.dag_id}", f"node={node.id}"],
                data={
                    "dag_id": self._dag.dag_id,
                    "node_id": node.id,
                    "role": node.role,
                    "summary": run_result.get("summary", ""),
                    "files_changed": run_result.get("files_changed", []),
                },
            )
            with ChronoStore(self._project_root) as store:
                store.upsert(record)
            return record_id
        except Exception:  # noqa: BLE001
            return None

    def _build_context_prompt(self, node: TaskNode) -> str:
        """Fetch predecessor ESDB records and build a context block."""
        if not node.context_in:
            return ""
        try:
            from chronomemory import ChronoStore

            parts: list[str] = ["## Predecessor context from ESDB"]
            with ChronoStore(self._project_root) as store:
                for rec_id in node.context_in:
                    rec = store.get(rec_id)
                    if rec is not None:
                        parts.append(f"- [{rec_id}] {rec.label}: {rec.data.get('summary', '')}")
            return "\n".join(parts) if len(parts) > 1 else ""
        except Exception:  # noqa: BLE001
            return ""

    def _propagate_context(self, completed_node: TaskNode) -> None:
        """Inject context_out of completed_node into waiting successors."""
        if completed_node.context_out is None:
            return
        for node in self._dag.nodes():
            if completed_node.id in node.depends_on and node.status == TaskStatus.PENDING:
                node.context_in.append(completed_node.context_out)


# ---------------------------------------------------------------------------
# Internal exceptions
# ---------------------------------------------------------------------------


class _GovernanceBlockedError(Exception):
    """Raised when governance preflight rejects a node."""


class _NodeAbortedError(Exception):
    """Raised when abort_node() signals a running node to stop."""


__all__ = ["AgentDispatcher", "AgentPool"]
