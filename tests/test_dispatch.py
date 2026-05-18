# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the multi-agent DAG dispatcher (REQ-321..REQ-334).

TEST-321: Orchestrator sole entry point (checked via import/source inspection)
TEST-322: DAG decomposition before dispatch
TEST-323: TaskNode schema
TEST-324: Bounded concurrent dispatch (unit-level via mock)
TEST-325: Fail-forward BLOCKED propagation
TEST-326: AgentPool worker reuse
TEST-327: ESDB context written on completion (unit-level mock)
TEST-328: DAG state transitions persisted as JSONL
TEST-329: Per-node governance preflight (unit-level mock)
TEST-330: DAG run resumable from checkpoint
TEST-331: Dispatch CLI group subcommands
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

import pytest

# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------


def test_dispatch_package_imports():
    """All public dispatch symbols are importable (REQ-322..REQ-328)."""
    from specsmith.agent.dispatch import (  # noqa: F401
        AgentDispatcher,
        AgentPool,
        DAGValidationError,
        DispatchEvent,
        DispatchResult,
        DispatchSummary,
        EventEmitter,
        TaskDAG,
        TaskDAGBuilder,
        TaskNode,
        TaskStatus,
    )


# ---------------------------------------------------------------------------
# TEST-322: TaskDAGBuilder — DAG decomposition before dispatch
# ---------------------------------------------------------------------------


class TestTaskDAGBuilder:
    def test_build_fallback_single_node(self):
        """No planner output → single-node fallback DAG (REQ-322)."""
        from specsmith.agent.dispatch import TaskDAGBuilder, TaskStatus

        dag = TaskDAGBuilder.build("add hello-world endpoint", dag_id="t001")
        assert dag.dag_id == "t001"
        nodes = dag.nodes()
        assert len(nodes) == 1
        assert nodes[0].id == "task-main"
        assert nodes[0].status == TaskStatus.PENDING

    def test_build_from_list(self):
        """Planner dict list → multi-node DAG with dependency edges (REQ-322)."""
        from specsmith.agent.dispatch import TaskDAGBuilder

        plan = [
            {"id": "a", "title": "First", "role": "architect", "depends_on": []},
            {"id": "b", "title": "Second", "role": "coder", "depends_on": ["a"]},
        ]
        dag = TaskDAGBuilder.build("task", planner_output=plan)
        assert len(dag.nodes()) == 2
        assert dag.get("b").depends_on == ["a"]

    def test_build_from_json_string(self):
        """Planner JSON string → extract array and build DAG (REQ-322)."""
        from specsmith.agent.dispatch import TaskDAGBuilder

        json_str = 'Here is the plan:\n[{"id":"x","title":"X","role":"coder","depends_on":[]}]'
        dag = TaskDAGBuilder.build("task", planner_output=json_str)
        assert dag.get("x") is not None

    def test_cycle_raises_dag_validation_error(self):
        """Cycle detection at build time raises DAGValidationError (REQ-322)."""
        from specsmith.agent.dispatch import DAGValidationError, TaskDAGBuilder

        with pytest.raises(DAGValidationError, match="Cycle"):
            TaskDAGBuilder.build(
                "cycle",
                planner_output=[
                    {"id": "a", "title": "A", "role": "coder", "depends_on": ["b"]},
                    {"id": "b", "title": "B", "role": "coder", "depends_on": ["a"]},
                ],
            )

    def test_unknown_dep_raises_error(self):
        from specsmith.agent.dispatch import DAGValidationError, TaskDAGBuilder

        with pytest.raises(DAGValidationError):
            TaskDAGBuilder.build(
                "bad",
                planner_output=[
                    {"id": "x", "title": "X", "role": "coder", "depends_on": ["nonexistent"]},
                ],
            )

    def test_dag_ids_are_unique(self):
        """Auto-generated dag_ids differ between calls."""
        from specsmith.agent.dispatch import TaskDAGBuilder

        d1 = TaskDAGBuilder.build("t")
        d2 = TaskDAGBuilder.build("t")
        assert d1.dag_id != d2.dag_id


# ---------------------------------------------------------------------------
# TEST-323: TaskNode schema
# ---------------------------------------------------------------------------


class TestTaskNode:
    def test_node_carries_required_fields(self):
        """TaskNode schema matches REQ-323."""
        from specsmith.agent.dispatch import TaskNode, TaskStatus

        node = TaskNode(
            id="my-node",
            title="Do something",
            role="coder",
            depends_on=["dep-1"],
        )
        assert node.id == "my-node"
        assert node.title == "Do something"
        assert node.role == "coder"
        assert node.depends_on == ["dep-1"]
        assert node.status == TaskStatus.PENDING
        assert node.context_in == []
        assert node.context_out is None
        assert node.result is None

    def test_node_to_dict(self):
        from specsmith.agent.dispatch import TaskNode

        d = TaskNode(id="n", title="T", role="reviewer").to_dict()
        assert d["id"] == "n"
        assert d["role"] == "reviewer"
        assert d["status"] == "pending"
        assert d["context_in"] == []


# ---------------------------------------------------------------------------
# TEST-325: Fail-forward BLOCKED propagation
# ---------------------------------------------------------------------------


class TestBlockedPropagation:
    def test_transitive_blocking(self):
        """Failed node blocks direct and transitive dependents; siblings continue (REQ-325)."""
        from specsmith.agent.dispatch import TaskDAGBuilder, TaskStatus

        plan = [
            {"id": "arch", "title": "Arch", "role": "architect", "depends_on": []},
            {"id": "impl", "title": "Impl", "role": "coder", "depends_on": ["arch"]},
            {"id": "test", "title": "Test", "role": "tester", "depends_on": ["arch"]},
            {"id": "review", "title": "Review", "role": "reviewer", "depends_on": ["impl", "test"]},
        ]
        dag = TaskDAGBuilder.build("f", planner_output=plan)
        dag.get("arch").status = TaskStatus.COMPLETED
        dag.get("impl").status = TaskStatus.FAILED

        blocked = dag.blocked_by_failure("impl")

        assert "review" in blocked
        assert "test" not in blocked  # test depends only on arch (COMPLETED)
        assert dag.get("review").status == TaskStatus.BLOCKED
        assert dag.get("test").status == TaskStatus.PENDING

    def test_non_dependent_sibling_unaffected(self):
        from specsmith.agent.dispatch import TaskDAGBuilder, TaskStatus

        plan = [
            {"id": "a", "title": "A", "role": "coder", "depends_on": []},
            {"id": "b", "title": "B", "role": "coder", "depends_on": []},
        ]
        dag = TaskDAGBuilder.build("f", planner_output=plan)
        dag.get("a").status = TaskStatus.FAILED
        dag.blocked_by_failure("a")
        assert dag.get("b").status == TaskStatus.PENDING

    def test_all_terminal_after_blocking(self):
        from specsmith.agent.dispatch import TaskDAGBuilder, TaskStatus

        plan = [
            {"id": "a", "title": "A", "role": "coder", "depends_on": []},
            {"id": "b", "title": "B", "role": "coder", "depends_on": ["a"]},
        ]
        dag = TaskDAGBuilder.build("f", planner_output=plan)
        dag.get("a").status = TaskStatus.FAILED
        dag.blocked_by_failure("a")
        assert dag.all_terminal()


# ---------------------------------------------------------------------------
# TEST-322 (continued): Runnable nodes scheduling
# ---------------------------------------------------------------------------


class TestRunnableNodes:
    def test_no_runnable_when_dep_pending(self):
        """Node with PENDING dep is not yet runnable."""
        from specsmith.agent.dispatch import TaskDAGBuilder

        dag = TaskDAGBuilder.build(
            "f",
            planner_output=[
                {"id": "x", "title": "X", "role": "coder", "depends_on": []},
                {"id": "y", "title": "Y", "role": "coder", "depends_on": ["x"]},
            ],
        )
        runnable = dag.runnable_nodes()
        assert len(runnable) == 1
        assert runnable[0].id == "x"

    def test_both_runnable_after_dep_completed(self):
        from specsmith.agent.dispatch import TaskDAGBuilder, TaskStatus

        plan = [
            {"id": "root", "title": "Root", "role": "architect", "depends_on": []},
            {"id": "left", "title": "Left", "role": "coder", "depends_on": ["root"]},
            {"id": "right", "title": "Right", "role": "tester", "depends_on": ["root"]},
        ]
        dag = TaskDAGBuilder.build("f", planner_output=plan)
        dag.get("root").status = TaskStatus.COMPLETED
        runnable = dag.runnable_nodes()
        ids = {n.id for n in runnable}
        assert ids == {"left", "right"}


# ---------------------------------------------------------------------------
# TEST-328: DAG state transitions persisted as JSONL
# ---------------------------------------------------------------------------


class TestEventEmitter:
    def test_emitter_creates_jsonl(self, tmp_path: Path):
        """EventEmitter creates events.jsonl before first node (REQ-328)."""
        from specsmith.agent.dispatch import EventEmitter
        from specsmith.agent.dispatch.events import _dag_dir_name

        EventEmitter(tmp_path, "test-dag-001")
        expected = (
            tmp_path / ".specsmith" / "dispatch" / _dag_dir_name("test-dag-001") / "events.jsonl"
        )
        assert expected.exists()

    def test_emit_writes_jsonl_line(self, tmp_path: Path):
        from specsmith.agent.dispatch import EventEmitter

        emitter = EventEmitter(tmp_path, "dag-write")
        emitter.node_started("node-1", "coder")
        emitter.node_completed("node-1", "rec-abc", "task done")
        emitter.node_failed("node-2", "timeout")

        from specsmith.agent.dispatch.events import _dag_dir_name

        path = tmp_path / ".specsmith" / "dispatch" / _dag_dir_name("dag-write") / "events.jsonl"
        lines = [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]
        assert len(lines) == 3
        assert lines[0]["event_type"] == "node_started"
        assert lines[0]["node_id"] == "node-1"
        assert lines[1]["event_type"] == "node_completed"
        assert lines[1]["payload"]["esdb_record_id"] == "rec-abc"
        assert lines[2]["event_type"] == "node_failed"

    def test_emit_dag_done(self, tmp_path: Path):
        from specsmith.agent.dispatch import EventEmitter

        emitter = EventEmitter(tmp_path, "dag-done-test")
        emitter.dag_done({"equilibrium": True, "completed": [], "failed": []})

        from specsmith.agent.dispatch.events import _dag_dir_name

        path = (
            tmp_path / ".specsmith" / "dispatch" / _dag_dir_name("dag-done-test") / "events.jsonl"
        )
        line = json.loads(path.read_text().strip())
        assert line["event_type"] == "dag_done"

    def test_replay_reads_all_events(self, tmp_path: Path):
        """Replay returns all persisted events for a DAG run (REQ-330)."""
        from specsmith.agent.dispatch import EventEmitter

        emitter = EventEmitter(tmp_path, "replay-dag")
        emitter.node_started("n1", "coder")
        emitter.node_completed("n1", None, "done")
        emitter.dag_done({})

        replayed = EventEmitter.replay(tmp_path, "replay-dag")
        assert len(replayed) == 3
        assert replayed[0].event_type == "node_started"
        assert replayed[2].event_type == "dag_done"

    def test_replay_missing_dag_returns_empty(self, tmp_path: Path):
        from specsmith.agent.dispatch import EventEmitter

        result = EventEmitter.replay(tmp_path, "nonexistent-dag")
        assert result == []

    def test_list_runs(self, tmp_path: Path):
        """list_runs returns all dag_ids with events.jsonl (REQ-331)."""
        from specsmith.agent.dispatch import EventEmitter

        EventEmitter(tmp_path, "dag-alpha")
        EventEmitter(tmp_path, "dag-beta")

        runs = EventEmitter.list_runs(tmp_path)
        assert "dag-alpha" in runs
        assert "dag-beta" in runs

    def test_sse_subscribe_receives_events(self, tmp_path: Path):
        """SSE subscriber queue receives emitted events."""
        from specsmith.agent.dispatch import EventEmitter

        emitter = EventEmitter(tmp_path, "sse-dag")
        q = emitter.subscribe()
        emitter.node_started("n1", "coder")
        evt = q.get_nowait()
        assert evt.event_type == "node_started"
        assert evt.node_id == "n1"
        emitter.unsubscribe(q)


# ---------------------------------------------------------------------------
# TEST-323 (schema): DispatchResult and DispatchSummary
# ---------------------------------------------------------------------------


class TestDispatchResult:
    def test_dispatch_result_to_dict(self):
        from specsmith.agent.dispatch import DispatchResult, TaskStatus

        r = DispatchResult(
            node_id="n1",
            role="coder",
            status=TaskStatus.COMPLETED,
            summary="done",
            files_changed=["src/foo.py"],
            esdb_record_id="rec-123",
        )
        d = r.to_dict()
        assert d["node_id"] == "n1"
        assert d["status"] == "completed"
        assert d["esdb_record_id"] == "rec-123"

    def test_dispatch_summary_to_dict(self):
        from specsmith.agent.dispatch import DispatchResult, DispatchSummary, TaskStatus

        s = DispatchSummary(
            dag_id="dag-1",
            completed=[DispatchResult("n1", "coder", TaskStatus.COMPLETED)],
            failed=[],
            blocked=[],
            equilibrium=True,
            confidence=1.0,
        )
        d = s.to_dict()
        assert d["dag_id"] == "dag-1"
        assert d["equilibrium"] is True
        assert len(d["completed"]) == 1


# ---------------------------------------------------------------------------
# TEST-326: AgentPool reuses idle workers
# ---------------------------------------------------------------------------


class TestAgentPool:
    def test_pool_reuses_idle_worker(self):
        """AgentPool.release() then acquire() for same role returns reused agent (REQ-326)."""
        from specsmith.agent.dispatch.dispatcher import AgentPool

        pool = AgentPool.__new__(AgentPool)
        pool._llm_config = {}
        pool._max_workers = 4
        pool._idle = {}
        pool._active_count = 0
        import threading

        pool._lock = threading.Lock()

        sentinel = object()
        pool._idle["coder"] = [sentinel]
        pool._active_count = 0

        worker = pool.acquire("coder")
        assert worker is sentinel
        assert pool._active_count == 1

        pool.release("coder", sentinel)
        assert pool._active_count == 0
        assert sentinel in pool._idle.get("coder", [])

    def test_pool_respects_max_workers(self):
        """Pool returns None when at capacity (REQ-324)."""
        from specsmith.agent.dispatch.dispatcher import AgentPool

        pool = AgentPool.__new__(AgentPool)
        pool._llm_config = {}
        pool._max_workers = 2
        pool._idle = {}
        pool._active_count = 2  # already at cap
        import threading

        pool._lock = threading.Lock()

        result = pool.acquire("coder")
        assert result is None


# ---------------------------------------------------------------------------
# TEST-331: Dispatch CLI group — subcommands exist and load
# ---------------------------------------------------------------------------


class TestDispatchCLI:
    def test_dispatch_group_registered(self):
        """specsmith dispatch group and subcommands are registered in CLI (REQ-331)."""
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["dispatch", "--help"])
        assert result.exit_code == 0
        assert "run" in result.output
        assert "status" in result.output
        assert "list" in result.output
        assert "retry" in result.output

    def test_dispatch_run_help(self):
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["dispatch", "run", "--help"])
        assert result.exit_code == 0
        assert "--max-workers" in result.output
        assert "--json" in result.output

    def test_dispatch_list_empty(self, tmp_path: Path):
        """dispatch list on an empty project prints gracefully (REQ-331)."""
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        result = runner.invoke(main, ["dispatch", "list", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0

    def test_dispatch_status_missing(self, tmp_path: Path):
        from click.testing import CliRunner

        from specsmith.cli import main

        runner = CliRunner()
        result = runner.invoke(
            main, ["dispatch", "status", "--dag-id", "nonexistent", "--project-dir", str(tmp_path)]
        )
        assert result.exit_code == 0


# ---------------------------------------------------------------------------
# TEST-325 + TEST-330: AgentDispatcher end-to-end with mocked workers
# ---------------------------------------------------------------------------


class TestAgentDispatcherEndToEnd:
    def test_single_node_dispatch_completes(self, tmp_path: Path):
        """Single-node DAG completes when worker returns success (REQ-324, REQ-327)."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
            TaskStatus,
        )

        dag = TaskDAGBuilder.build("do work", dag_id="e2e-001")
        emitter = EventEmitter(tmp_path, "e2e-001")

        mock_pool = mock.MagicMock(spec=AgentPool)
        mock_worker = mock.MagicMock()
        mock_pool.acquire.return_value = mock_worker

        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)

        # Patch _invoke_worker to return a success result without calling AG2
        with (
            mock.patch.object(
                dispatcher,
                "_invoke_worker",
                return_value={"summary": "done", "files_changed": ["f.py"], "equilibrium": True},
            ),
            mock.patch.object(dispatcher, "_write_esdb_record", return_value="rec-xyz"),
            mock.patch.object(dispatcher, "_governance_preflight"),
        ):
            summary = dispatcher.run()

        assert summary.equilibrium is True
        assert len(summary.completed) == 1
        assert summary.completed[0].status == TaskStatus.COMPLETED

    def test_failed_node_propagates_blocked(self, tmp_path: Path):
        """Failed node propagates BLOCKED to dependents (REQ-325)."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
            TaskStatus,
        )

        plan = [
            {"id": "root", "title": "Root", "role": "coder", "depends_on": []},
            {"id": "child", "title": "Child", "role": "coder", "depends_on": ["root"]},
        ]
        dag = TaskDAGBuilder.build("f", dag_id="fail-001", planner_output=plan)
        emitter = EventEmitter(tmp_path, "fail-001")

        mock_pool = mock.MagicMock(spec=AgentPool)
        mock_pool.acquire.return_value = mock.MagicMock()

        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=2)

        with (
            mock.patch.object(
                dispatcher,
                "_invoke_worker",
                side_effect=RuntimeError("worker crashed"),
            ),
            mock.patch.object(dispatcher, "_governance_preflight"),
        ):
            summary = dispatcher.run()

        assert len(summary.failed) == 1
        assert "child" in summary.blocked
        assert dag.get("child").status == TaskStatus.BLOCKED

    def test_events_jsonl_written(self, tmp_path: Path):
        """Node lifecycle events are persisted to JSONL (REQ-328)."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        dag = TaskDAGBuilder.build("job", dag_id="events-001")
        emitter = EventEmitter(tmp_path, "events-001")

        mock_pool = mock.MagicMock(spec=AgentPool)
        mock_pool.acquire.return_value = mock.MagicMock()

        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)
        with (
            mock.patch.object(
                dispatcher,
                "_invoke_worker",
                return_value={"summary": "ok", "files_changed": [], "equilibrium": True},
            ),
            mock.patch.object(dispatcher, "_write_esdb_record", return_value=None),
            mock.patch.object(dispatcher, "_governance_preflight"),
        ):
            dispatcher.run()

        from specsmith.agent.dispatch.events import _dag_dir_name

        jsonl = tmp_path / ".specsmith" / "dispatch" / _dag_dir_name("events-001") / "events.jsonl"
        lines = [json.loads(ln) for ln in jsonl.read_text().splitlines() if ln.strip()]
        event_types = [ln["event_type"] for ln in lines]
        assert "node_started" in event_types
        assert "node_completed" in event_types
        assert "dag_done" in event_types


# ---------------------------------------------------------------------------
# Cooperative abort (REQ-334)
# ---------------------------------------------------------------------------


class TestCooperativeAbort:
    def test_pre_armed_abort_prevents_execution(self, tmp_path):
        """abort_node() called before _run_node starts causes immediate FAILED."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        dag = TaskDAGBuilder.build("job", dag_id="abort-pre")
        emitter = EventEmitter(tmp_path, "abort-pre")
        mock_pool = mock.MagicMock(spec=AgentPool)
        mock_pool.acquire.return_value = mock.MagicMock()
        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)

        # Pre-arm abort BEFORE the worker starts
        dispatcher.abort_node("task-main")

        with mock.patch.object(dispatcher, "_governance_preflight"):
            summary = dispatcher.run()

        assert len(summary.failed) == 1
        assert "Aborted" in (summary.failed[0].error or "")

    def test_abort_node_returns_false_for_unknown_node(self, tmp_path):
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        dag = TaskDAGBuilder.build("job", dag_id="abort-unknown")
        emitter = EventEmitter(tmp_path, "abort-unknown")
        dispatcher = AgentDispatcher(
            dag, mock.MagicMock(spec=AgentPool), emitter, project_root=tmp_path, max_workers=1
        )
        assert dispatcher.abort_node("nonexistent-node") is False
        assert dispatcher.abort_node("task-main") is True

    def test_abort_flag_checked_after_preflight(self, tmp_path):
        """Abort signalled during governance preflight exits before worker acquire."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        dag = TaskDAGBuilder.build("job", dag_id="abort-post-preflight")
        emitter = EventEmitter(tmp_path, "abort-post-preflight")
        mock_pool = mock.MagicMock(spec=AgentPool)
        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)

        def _preflight_and_abort(node):
            # Simulate preflight setting the abort flag mid-execution
            dispatcher.abort_node(node.id)

        with mock.patch.object(
            dispatcher, "_governance_preflight", side_effect=_preflight_and_abort
        ):
            summary = dispatcher.run()

        # Worker should never have been acquired
        mock_pool.acquire.assert_not_called()
        assert len(summary.failed) == 1


# ---------------------------------------------------------------------------
# REQ-313..320: compliance plan 5939f743 — multi-agent governance traceability
# ---------------------------------------------------------------------------


class TestMultiAgentCompliance:
    # REQ-314: worker identity in dispatch events
    def test_node_started_payload_contains_role(self, tmp_path):
        """node_started JSONL payload MUST include role (REQ-314)."""
        from specsmith.agent.dispatch import EventEmitter

        emitter = EventEmitter(tmp_path, "dag-314")
        emitter.node_started("n1", "coder", depends_on=[])
        events = EventEmitter.replay(tmp_path, "dag-314")
        assert events[0].payload.get("role") == "coder"

    # REQ-314: depends_on included in node_started payload
    def test_node_started_payload_contains_depends_on(self, tmp_path):
        from specsmith.agent.dispatch import EventEmitter

        emitter = EventEmitter(tmp_path, "dag-314b")
        emitter.node_started("child", "coder", depends_on=["parent"])
        events = EventEmitter.replay(tmp_path, "dag-314b")
        assert events[0].payload.get("depends_on") == ["parent"]

    # REQ-315: summary.dag_id matches DAG dag_id
    def test_dispatch_summary_dag_id_traceable(self, tmp_path):
        """DispatchSummary.dag_id must match TaskDAG.dag_id (REQ-315)."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        dag = TaskDAGBuilder.build("t", dag_id="trace-315")
        emitter = EventEmitter(tmp_path, "trace-315")
        mock_pool = mock.MagicMock(spec=AgentPool)
        mock_pool.acquire.return_value = mock.MagicMock()
        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)
        with (
            mock.patch.object(
                dispatcher,
                "_invoke_worker",
                return_value={"summary": "", "files_changed": [], "equilibrium": True},
            ),
            mock.patch.object(dispatcher, "_write_esdb_record", return_value=None),
            mock.patch.object(dispatcher, "_governance_preflight"),
            mock.patch.object(dispatcher, "_write_dispatch_ledger"),
        ):
            summary = dispatcher.run()
        assert summary.dag_id == "trace-315"

    # REQ-316: governance block recorded in error
    def test_governance_block_in_error(self, tmp_path):
        """Governance block must set error to 'Governance preflight blocked' (REQ-316)."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        dag = TaskDAGBuilder.build("t", dag_id="gov-316")
        emitter = EventEmitter(tmp_path, "gov-316")
        mock_pool = mock.MagicMock(spec=AgentPool)
        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)
        from specsmith.agent.dispatch.dispatcher import _GovernanceBlockedError

        with (
            mock.patch.object(
                dispatcher, "_governance_preflight", side_effect=_GovernanceBlockedError("denied")
            ),
            mock.patch.object(dispatcher, "_write_dispatch_ledger"),
        ):
            summary = dispatcher.run()
        assert len(summary.failed) == 1
        assert summary.failed[0].error.startswith("Governance preflight blocked")

    # REQ-317: context_in populated by _propagate_context
    def test_context_injection_traceable(self):
        """After _propagate_context, child.context_in contains parent's esdb_id (REQ-317)."""
        import tempfile
        from pathlib import Path

        from specsmith.agent.dispatch import TaskDAGBuilder, TaskStatus
        from specsmith.agent.dispatch.dispatcher import AgentDispatcher, AgentPool
        from specsmith.agent.dispatch.events import EventEmitter

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dag = TaskDAGBuilder.build(
                "f",
                planner_output=[
                    {"id": "root", "title": "Root", "role": "coder", "depends_on": []},
                    {"id": "child", "title": "Child", "role": "coder", "depends_on": ["root"]},
                ],
            )
            emitter = EventEmitter(root, dag.dag_id)
            dispatcher = AgentDispatcher(
                dag, mock.MagicMock(spec=AgentPool), emitter, project_root=root, max_workers=1
            )
            # Simulate root completing with an ESDB record
            root_node = dag.get("root")
            root_node.context_out = "rec-xyz"
            root_node.status = TaskStatus.COMPLETED
            dispatcher._propagate_context(root_node)
            assert "rec-xyz" in dag.get("child").context_in

    # REQ-318: completed nodes not re-executed on retry
    def test_retry_refuses_completed_node(self, tmp_path):
        """dispatch retry --node n1 returns error if n1 is already completed (REQ-318)."""
        from click.testing import CliRunner

        from specsmith.agent.dispatch import EventEmitter
        from specsmith.cli import main

        # Set up a completed run
        emitter = EventEmitter(tmp_path, "dag-318")
        emitter.node_started("n1", "coder", depends_on=[])
        emitter.node_completed("n1", None, "done")
        emitter.dag_done({})

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "dispatch",
                "retry",
                "--node",
                "n1",
                "--dag-id",
                "dag-318",
                "--project-dir",
                str(tmp_path),
            ],
        )
        # Should exit 0 but print 'already completed'
        assert result.exit_code == 0
        assert "already completed" in result.output.lower() or "completed" in result.output.lower()

    # REQ-319: ESDB record contains DAG lineage
    def test_esdb_record_contains_dag_lineage(self, tmp_path):
        """dispatch_result ChronoRecord MUST include dag_id and node_id (REQ-319)."""
        from chronomemory import ChronoStore

        from specsmith.agent.dispatch import EventEmitter, TaskDAGBuilder
        from specsmith.agent.dispatch.dispatcher import AgentDispatcher, AgentPool

        dag = TaskDAGBuilder.build("t", dag_id="esdb-319")
        emitter = EventEmitter(tmp_path, "esdb-319")
        dispatcher = AgentDispatcher(
            dag, mock.MagicMock(spec=AgentPool), emitter, project_root=tmp_path, max_workers=1
        )
        node = dag.nodes()[0]
        run_result = {"summary": "ok", "files_changed": []}
        record_id = dispatcher._write_esdb_record(node, run_result)
        assert record_id is not None
        # Verify lineage in ESDB
        with ChronoStore(tmp_path) as store:
            rec = store.get(record_id)
        assert rec is not None
        assert any("dag=" in e for e in rec.evidence)
        assert any("node=" in e for e in rec.evidence)
        assert rec.data.get("dag_id") == "esdb-319"
        assert rec.data.get("node_id") == node.id

    # REQ-320: abort error contains 'Aborted'
    def test_abort_error_contains_aborted(self, tmp_path):
        """Pre-armed abort_node() produces error containing 'Aborted' (REQ-320)."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        dag = TaskDAGBuilder.build("t", dag_id="abort-320")
        emitter = EventEmitter(tmp_path, "abort-320")
        mock_pool = mock.MagicMock(spec=AgentPool)
        mock_pool.acquire.return_value = mock.MagicMock()
        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)
        dispatcher.abort_node("task-main")
        with (
            mock.patch.object(dispatcher, "_governance_preflight"),
            mock.patch.object(dispatcher, "_write_dispatch_ledger"),
        ):
            summary = dispatcher.run()
        assert len(summary.failed) == 1
        assert "Aborted" in (summary.failed[0].error or "")

    # REQ-313: ledger entry written after dispatch run
    def test_dispatch_ledger_entry_written(self, tmp_path):
        """AgentDispatcher.run() writes a dispatch ledger entry (REQ-313)."""
        from specsmith.agent.dispatch import (
            AgentDispatcher,
            AgentPool,
            EventEmitter,
            TaskDAGBuilder,
        )

        # Create a minimal LEDGER.md so the ledger writer can find it
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("# Ledger\n", encoding="utf-8")

        dag = TaskDAGBuilder.build("test task", dag_id="ledger-313")
        emitter = EventEmitter(tmp_path, "ledger-313")
        mock_pool = mock.MagicMock(spec=AgentPool)
        mock_pool.acquire.return_value = mock.MagicMock()
        dispatcher = AgentDispatcher(dag, mock_pool, emitter, project_root=tmp_path, max_workers=1)
        with (
            mock.patch.object(
                dispatcher,
                "_invoke_worker",
                return_value={"summary": "ok", "files_changed": [], "equilibrium": True},
            ),
            mock.patch.object(dispatcher, "_write_esdb_record", return_value=None),
            mock.patch.object(dispatcher, "_governance_preflight"),
        ):
            dispatcher.run()

        content = ledger.read_text(encoding="utf-8")
        assert "ledger-313" in content
        assert "dispatch" in content.lower()


# ---------------------------------------------------------------------------
# TEST-321: Orchestrator is sole entry point
# ---------------------------------------------------------------------------


def test_orchestrator_source_mentions_sole_entry():
    """Orchestrator source documents REQ-321 constraint."""
    import inspect

    from specsmith.agent import orchestrator

    src = inspect.getsource(orchestrator)
    assert "REQ-321" in src
    assert "sole entry point" in src


# ---------------------------------------------------------------------------
# Tool registry — compiler/linter tools present (implicit REQ for ROLE_TOOLS)
# ---------------------------------------------------------------------------


class TestCompilerTools:
    def test_compiler_tools_in_available_tools(self):
        """All 8 compiler/linter tools are in AVAILABLE_TOOLS."""
        from specsmith.agent.tools import AVAILABLE_TOOLS

        names = {t.__name__ for t in AVAILABLE_TOOLS}
        expected = {
            "run_gcc",
            "run_arm_gcc",
            "run_aarch64_gcc",
            "run_iar_compiler",
            "run_intel_compiler",
            "run_clang_format",
            "run_clang_tidy",
            "run_vsg",
        }
        assert expected.issubset(names)

    def test_coder_role_tools_include_compilers(self):
        """ROLE_TOOLS['coder'] includes compiler tools (embedded support)."""
        from specsmith.agent.spawner import ROLE_TOOLS

        coder_tools = set(ROLE_TOOLS["coder"])
        assert "run_gcc" in coder_tools
        assert "run_arm_gcc" in coder_tools
        assert "run_clang_format" in coder_tools
        assert "run_vsg" in coder_tools

    def test_embedded_coder_role_exists(self):
        """embedded-coder role is registered with all compiler tools."""
        from specsmith.agent.spawner import ROLE_TOOLS

        assert "embedded-coder" in ROLE_TOOLS
        embedded = set(ROLE_TOOLS["embedded-coder"])
        for tool in (
            "run_gcc",
            "run_arm_gcc",
            "run_aarch64_gcc",
            "run_iar_compiler",
            "run_intel_compiler",
            "run_clang_format",
            "run_clang_tidy",
            "run_vsg",
        ):
            assert tool in embedded, f"{tool} missing from embedded-coder"

    def test_reviewer_role_has_linters(self):
        from specsmith.agent.spawner import ROLE_TOOLS

        reviewer = set(ROLE_TOOLS["reviewer"])
        assert "run_clang_tidy" in reviewer
        assert "run_vsg" in reviewer
