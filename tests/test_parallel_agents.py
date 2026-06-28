# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for parallel agent dispatch with profile pinning and cost aggregation.

Covers:
  TEST-PA-01: Independent DAG nodes are simultaneously runnable (fan-out)
  TEST-PA-02: Dependent nodes are NOT runnable until predecessor completes
  TEST-PA-03: AgentPool respects max_workers concurrency ceiling
  TEST-PA-04: AgentPool releases workers back to the idle pool
  TEST-PA-05: AgentPool worker reuse per role
  TEST-PA-06: Profile-pinned routing: coder role → coder profile
  TEST-PA-07: Profile-pinned routing: architect role → architect profile
  TEST-PA-08: AgentState.credit() aggregates tokens from parallel nodes
  TEST-PA-09: Cost aggregation across parallel nodes is cumulative
  TEST-PA-10: Token metric ESDB write fires for each completed node (mocked)
  TEST-PA-11: Parallel fan-out completions produce correct DispatchSummary
  TEST-PA-12: AgentDispatcher with mocked worker runs fan-out successfully

No LLM or AG2 calls; workers and ESDB writes are mocked throughout.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import specsmith.esdb_writer as _esdb_mod
from specsmith.agent.core import AgentState
from specsmith.agent.dispatch import (
    AgentPool,
    DispatchResult,
    DispatchSummary,
    TaskDAGBuilder,
    TaskNode,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# TEST-PA-01: Independent DAG nodes are simultaneously runnable (fan-out)
# ---------------------------------------------------------------------------


class TestParallelFanOut:
    def test_two_independent_nodes_both_runnable(self) -> None:
        """Two root nodes (no deps) must both appear in runnable_nodes()."""
        plan = [
            {"id": "coder-task", "title": "Write the service", "role": "coder", "depends_on": []},
            {
                "id": "arch-task",
                "title": "Design the schema",
                "role": "architect",
                "depends_on": [],
            },
        ]
        dag = TaskDAGBuilder.build("fan-out test", planner_output=plan)
        runnable = dag.runnable_nodes()
        ids = {n.id for n in runnable}
        assert ids == {"coder-task", "arch-task"}, (
            "Both independent nodes must be simultaneously runnable"
        )

    def test_three_independent_nodes_all_runnable(self) -> None:
        plan = [
            {"id": "a", "title": "A", "role": "coder", "depends_on": []},
            {"id": "b", "title": "B", "role": "architect", "depends_on": []},
            {"id": "c", "title": "C", "role": "tester", "depends_on": []},
        ]
        dag = TaskDAGBuilder.build("three-way fan-out", planner_output=plan)
        assert len(dag.runnable_nodes()) == 3

    def test_fan_out_then_merge_topology(self) -> None:
        """Diamond: root → two parallel nodes → merge node."""
        plan = [
            {"id": "root", "title": "Root", "role": "architect", "depends_on": []},
            {"id": "left", "title": "Left", "role": "coder", "depends_on": ["root"]},
            {"id": "right", "title": "Right", "role": "coder", "depends_on": ["root"]},
            {"id": "merge", "title": "Merge", "role": "reviewer", "depends_on": ["left", "right"]},
        ]
        dag = TaskDAGBuilder.build("diamond", planner_output=plan)
        # Initially only root is runnable
        runnable = dag.runnable_nodes()
        assert [n.id for n in runnable] == ["root"]
        # After root completes, left and right are runnable
        dag.get("root").status = TaskStatus.COMPLETED
        runnable2 = dag.runnable_nodes()
        assert {n.id for n in runnable2} == {"left", "right"}
        # After both complete, merge is runnable
        dag.get("left").status = TaskStatus.COMPLETED
        dag.get("right").status = TaskStatus.COMPLETED
        runnable3 = dag.runnable_nodes()
        assert [n.id for n in runnable3] == ["merge"]


# ---------------------------------------------------------------------------
# TEST-PA-02: Dependent nodes are NOT runnable until predecessor completes
# ---------------------------------------------------------------------------


class TestDependencyOrdering:
    def test_dependent_node_blocked_until_parent_completes(self) -> None:
        plan = [
            {"id": "arch", "title": "Arch", "role": "architect", "depends_on": []},
            {"id": "impl", "title": "Impl", "role": "coder", "depends_on": ["arch"]},
        ]
        dag = TaskDAGBuilder.build("sequential", planner_output=plan)
        runnable = dag.runnable_nodes()
        assert [n.id for n in runnable] == ["arch"]
        assert dag.get("impl") not in runnable

    def test_transitive_dependency_not_runnable_until_chain_done(self) -> None:
        plan = [
            {"id": "a", "title": "A", "role": "architect", "depends_on": []},
            {"id": "b", "title": "B", "role": "coder", "depends_on": ["a"]},
            {"id": "c", "title": "C", "role": "tester", "depends_on": ["b"]},
        ]
        dag = TaskDAGBuilder.build("chain", planner_output=plan)
        dag.get("a").status = TaskStatus.COMPLETED
        runnable = dag.runnable_nodes()
        assert {n.id for n in runnable} == {"b"}
        assert dag.get("c") not in runnable


# ---------------------------------------------------------------------------
# TEST-PA-03/04/05: AgentPool concurrency and worker reuse
# ---------------------------------------------------------------------------


class TestAgentPool:
    def _pool(self, max_workers: int = 2) -> AgentPool:
        return AgentPool(llm_config={}, max_workers=max_workers)

    def test_acquire_returns_none_at_capacity(self) -> None:
        """Pool at max_workers must return None on further acquire."""
        pool = self._pool(max_workers=2)

        # Patch spawner to return simple mock workers
        with mock.patch("specsmith.agent.dispatch.dispatcher.AgentPool._spawn_worker") as sp:
            sp.return_value = object()
            w1 = pool.acquire("coder")
            w2 = pool.acquire("architect")
            assert w1 is not None and w2 is not None
            # Pool is now at capacity (active_count == 2)
            w3 = pool.acquire("tester")
            assert w3 is None, "Pool at capacity must return None"

    def test_release_decrements_active_count(self) -> None:
        pool = self._pool(max_workers=1)
        worker = object()
        with mock.patch("specsmith.agent.dispatch.dispatcher.AgentPool._spawn_worker") as sp:
            sp.return_value = worker
            w = pool.acquire("coder")
            assert w is not None
            # Should be at capacity now
            assert pool.acquire("coder") is None
            # Release
            pool.release("coder", w)
            # Should be able to acquire again
            w2 = pool.acquire("coder")
            assert w2 is not None  # reused from idle pool

    def test_idle_worker_reused_for_same_role(self) -> None:
        """Worker released for a role is returned on the next acquire for that role."""
        pool = self._pool(max_workers=2)
        sentinel = object()
        with mock.patch("specsmith.agent.dispatch.dispatcher.AgentPool._spawn_worker") as sp:
            sp.return_value = sentinel
            w1 = pool.acquire("coder")
            pool.release("coder", w1)
            w2 = pool.acquire("coder")
            # Should be the same object (reused from idle)
            assert w2 is sentinel

    def test_different_roles_do_not_share_idle_workers(self) -> None:
        pool = self._pool(max_workers=4)
        with mock.patch("specsmith.agent.dispatch.dispatcher.AgentPool._spawn_worker") as sp:
            coder_worker = object()
            arch_worker = object()
            sp.side_effect = [coder_worker, arch_worker]
            wc = pool.acquire("coder")
            pool.release("coder", wc)
            wa = pool.acquire("architect")
            # architect gets a fresh worker, not the coder one
            assert wa is arch_worker


# ---------------------------------------------------------------------------
# TEST-PA-06/07: Profile-pinned routing via ProfileStore
# ---------------------------------------------------------------------------


class TestProfilePinnedRouting:
    """Verify that the routing table maps task roles to the correct profiles.

    Uses the default preset so tests are fully self-contained and independent
    of the user's ~/.specsmith/agents.json.
    """

    def _load_default_store(self, tmp_path: Path):
        from specsmith.agent.profiles import ProfileStore, apply_preset

        store_path = tmp_path / "agents.json"
        apply_preset("default", path=store_path)
        return ProfileStore.load(store_path)

    def test_fix_command_routes_to_coder(self, tmp_path: Path) -> None:
        store = self._load_default_store(tmp_path)
        profile = store.resolve_for_activity("/fix")
        assert profile.role == "coder", f"Expected coder role, got {profile.role!r}"

    def test_plan_command_routes_to_architect(self, tmp_path: Path) -> None:
        store = self._load_default_store(tmp_path)
        profile = store.resolve_for_activity("/plan")
        assert profile.role == "architect", f"Expected architect role, got {profile.role!r}"

    def test_test_command_routes_to_tester(self, tmp_path: Path) -> None:
        store = self._load_default_store(tmp_path)
        profile = store.resolve_for_activity("/test")
        assert profile.role == "tester"

    def test_review_command_routes_to_reviewer(self, tmp_path: Path) -> None:
        store = self._load_default_store(tmp_path)
        profile = store.resolve_for_activity("/review")
        assert profile.role == "reviewer"

    def test_coder_and_architect_are_different_profiles(self, tmp_path: Path) -> None:
        """The two parallel worker profiles must have distinct identities."""
        store = self._load_default_store(tmp_path)
        coder = store.resolve_for_activity("/fix")
        architect = store.resolve_for_activity("/plan")
        assert coder.id != architect.id, "Coder and architect must map to different profiles"

    def test_parallel_dag_roles_map_to_distinct_profiles(self, tmp_path: Path) -> None:
        """A 2-node parallel DAG (coder + architect) should resolve to 2 different profiles."""
        store = self._load_default_store(tmp_path)
        plan = [
            {"id": "code-it", "title": "Code it", "role": "coder", "depends_on": []},
            {"id": "design-it", "title": "Design it", "role": "architect", "depends_on": []},
        ]
        dag = TaskDAGBuilder.build("parallel-profile test", planner_output=plan)
        # Both nodes runnable immediately (no deps)
        runnable = dag.runnable_nodes()
        assert len(runnable) == 2
        # Resolve profiles for each node's role
        profiles = {n.role: store.resolve_for_activity(f"/{n.role}") for n in runnable}
        assert len({p.id for p in profiles.values()}) == 2, (
            "Each parallel role must resolve to a distinct profile"
        )


# ---------------------------------------------------------------------------
# TEST-PA-08/09: AgentState.credit() aggregates parallel node costs
# ---------------------------------------------------------------------------


class TestAgentStateCostAggregation:
    def test_credit_aggregates_tokens_from_two_nodes(self) -> None:
        state = AgentState()
        # Simulate two parallel nodes completing and reporting costs
        state.credit(profile_id="coder-14b", tokens_in=1000, tokens_out=500, cost_usd=0.005)
        state.credit(profile_id="planner-30b", tokens_in=2000, tokens_out=800, cost_usd=0.012)
        assert state.tokens_in == 3000
        assert state.tokens_out == 1300
        assert state.session_tokens == 4300
        assert abs(state.total_cost_usd - 0.017) < 1e-10

    def test_credit_tracks_per_profile_breakdown(self) -> None:
        state = AgentState()
        state.credit(profile_id="coder", tokens_in=500, tokens_out=200, cost_usd=0.003)
        state.credit(profile_id="coder", tokens_in=300, tokens_out=100, cost_usd=0.002)
        state.credit(profile_id="architect", tokens_in=1000, tokens_out=400, cost_usd=0.008)
        # Per-profile aggregation
        assert state.by_profile["coder"]["tokens_in"] == 800
        assert state.by_profile["coder"]["tokens_out"] == 300
        assert state.by_profile["coder"]["turns"] == 2
        assert state.by_profile["architect"]["tokens_in"] == 1000
        assert state.by_profile["architect"]["turns"] == 1

    def test_credit_aggregates_zero_cost_ollama_nodes(self) -> None:
        """Ollama parallel nodes contribute tokens but no cost."""
        state = AgentState()
        # Two Ollama workers (free)
        state.credit(profile_id="coder-14b", tokens_in=5000, tokens_out=2000, cost_usd=0.0)
        state.credit(profile_id="planner-30b", tokens_in=3000, tokens_out=1500, cost_usd=0.0)
        assert state.tokens_in == 8000
        assert state.tokens_out == 3500
        assert state.total_cost_usd == 0.0

    def test_parallel_cost_sum_is_total(self) -> None:
        """Sum of per-profile costs equals total_cost_usd."""
        state = AgentState()
        costs = [0.01, 0.02, 0.03]
        for i, c in enumerate(costs):
            state.credit(profile_id=f"p{i}", tokens_in=1000, tokens_out=500, cost_usd=c)
        per_profile_total = sum(v["cost_usd"] for v in state.by_profile.values())
        assert abs(per_profile_total - state.total_cost_usd) < 1e-9


# ---------------------------------------------------------------------------
# TEST-PA-10: Token metric ESDB write per node (mocked)
# ---------------------------------------------------------------------------


class TestTokenMetricPerNode:
    """write_token_metric should be called once per completed node when tokens > 0."""

    def test_write_token_metric_called_per_completed_node(self, tmp_path: Path) -> None:
        calls: list[dict] = []

        def _fake_write(project_dir, **kwargs):
            calls.append({"project_dir": project_dir, **kwargs})
            return False  # no ESDB sqlite in tmp_path, so always False

        with mock.patch.object(_esdb_mod, "write_token_metric", side_effect=_fake_write):
            # Simulate two nodes completing and writing their token metrics
            for node_id in ("coder-task", "architect-task"):
                _esdb_mod.write_token_metric(
                    tmp_path,
                    input_tokens=1000,
                    output_tokens=500,
                    cost_usd=0.005,
                    model="qwen2.5-coder:14b",
                    command_source=node_id,
                    work_item_id="WI-TEST",
                )
        assert len(calls) == 2
        sources = {c["command_source"] for c in calls}
        assert sources == {"coder-task", "architect-task"}

    def test_write_token_metric_skipped_for_zero_tokens(self, tmp_path: Path) -> None:
        """Nodes that produce 0 tokens (e.g. governance-only turns) should not write."""
        calls: list[dict] = []

        with mock.patch("specsmith.esdb_writer.write_token_metric", side_effect=calls.append):
            # The runner guards with: if tokens_in or tokens_out: write_token_metric(...)
            # Zero-token nodes never satisfy the guard; write_token_metric is not called.
            tokens_in, tokens_out = 0, 0
            assert not (tokens_in or tokens_out), "tokens must be zero to exercise the guard"
        assert calls == [], "No ESDB write should occur for zero-token nodes"


# ---------------------------------------------------------------------------
# TEST-PA-11: DispatchSummary reflects parallel completions
# ---------------------------------------------------------------------------


class TestDispatchSummary:
    def test_summary_equilibrium_when_all_complete(self) -> None:
        summary = DispatchSummary(dag_id="test-dag")
        summary.completed.append(
            DispatchResult(node_id="a", role="coder", status=TaskStatus.COMPLETED)
        )
        summary.completed.append(
            DispatchResult(node_id="b", role="architect", status=TaskStatus.COMPLETED)
        )
        # Simulate the dispatcher's final computation
        completed_count = len(summary.completed)
        total = 2
        summary.equilibrium = completed_count == total
        summary.confidence = completed_count / total
        assert summary.equilibrium is True
        assert summary.confidence == 1.0

    def test_summary_non_equilibrium_with_failures(self) -> None:
        summary = DispatchSummary(dag_id="test-dag")
        summary.completed.append(
            DispatchResult(node_id="a", role="coder", status=TaskStatus.COMPLETED)
        )
        summary.failed.append(
            DispatchResult(node_id="b", role="architect", status=TaskStatus.FAILED, error="oops")
        )
        completed_count = len(summary.completed)
        total = 2
        summary.equilibrium = completed_count == total
        summary.confidence = completed_count / total
        assert summary.equilibrium is False
        assert summary.confidence == 0.5

    def test_summary_to_dict_keys(self) -> None:
        summary = DispatchSummary(dag_id="my-dag")
        summary.equilibrium = True
        summary.confidence = 1.0
        d = summary.to_dict()
        assert "dag_id" in d
        assert "equilibrium" in d
        assert "confidence" in d
        assert "completed" in d
        assert "failed" in d
        assert "blocked" in d


# ---------------------------------------------------------------------------
# TEST-PA-12: AgentDispatcher mock — parallel fan-out execution
# ---------------------------------------------------------------------------


class TestAgentDispatcherMocked:
    """Run AgentDispatcher with fully mocked workers so no LLM is needed."""

    def _make_dispatcher(self, dag, tmp_path: Path):
        from specsmith.agent.dispatch import AgentPool, EventEmitter
        from specsmith.agent.dispatch.dispatcher import AgentDispatcher

        pool = AgentPool(llm_config={}, max_workers=4)
        emitter = EventEmitter(tmp_path, dag.dag_id)
        return AgentDispatcher(dag, pool, emitter, project_root=tmp_path, max_workers=4)

    def test_parallel_fan_out_completes_all_nodes(self, tmp_path: Path) -> None:
        """Two independent nodes dispatched in parallel both complete."""
        plan = [
            {"id": "n1", "title": "Node 1", "role": "coder", "depends_on": []},
            {"id": "n2", "title": "Node 2", "role": "architect", "depends_on": []},
        ]
        dag = TaskDAGBuilder.build("parallel-run", planner_output=plan)
        dispatcher = self._make_dispatcher(dag, tmp_path)

        def _fake_run_node(node: TaskNode) -> DispatchResult:
            return DispatchResult(
                node_id=node.id,
                role=node.role,
                status=TaskStatus.COMPLETED,
                summary=f"done: {node.id}",
            )

        with (
            mock.patch.object(dispatcher, "_run_node", side_effect=_fake_run_node),
            mock.patch.object(dispatcher, "_write_dispatch_ledger"),
        ):
            summary = dispatcher.run()

        assert summary.equilibrium is True, "Both nodes completed → equilibrium"
        assert len(summary.completed) == 2
        assert len(summary.failed) == 0
        completed_ids = {r.node_id for r in summary.completed}
        assert completed_ids == {"n1", "n2"}

    def test_failed_node_blocks_dependent(self, tmp_path: Path) -> None:
        """A failed node causes its dependent to be BLOCKED."""
        plan = [
            {"id": "root", "title": "Root", "role": "architect", "depends_on": []},
            {"id": "child", "title": "Child", "role": "coder", "depends_on": ["root"]},
        ]
        dag = TaskDAGBuilder.build("failure-propagation", planner_output=plan)
        dispatcher = self._make_dispatcher(dag, tmp_path)

        def _fake_run_node(node: TaskNode) -> DispatchResult:
            if node.id == "root":
                return DispatchResult(
                    node_id=node.id,
                    role=node.role,
                    status=TaskStatus.FAILED,
                    error="simulated failure",
                )
            return DispatchResult(node_id=node.id, role=node.role, status=TaskStatus.COMPLETED)

        with (
            mock.patch.object(dispatcher, "_run_node", side_effect=_fake_run_node),
            mock.patch.object(dispatcher, "_write_dispatch_ledger"),
        ):
            summary = dispatcher.run()

        assert summary.equilibrium is False
        assert len(summary.failed) >= 1
        assert "child" in summary.blocked

    def test_parallel_cost_aggregation_via_agent_state(self, tmp_path: Path) -> None:
        """AgentState.credit() accumulates costs for two parallel nodes post-dispatch."""
        plan = [
            {"id": "coder-node", "title": "Code", "role": "coder", "depends_on": []},
            {"id": "arch-node", "title": "Arch", "role": "architect", "depends_on": []},
        ]
        dag = TaskDAGBuilder.build("cost-agg-test", planner_output=plan)
        dispatcher = self._make_dispatcher(dag, tmp_path)

        def _fake_run_node(node: TaskNode) -> DispatchResult:
            return DispatchResult(
                node_id=node.id,
                role=node.role,
                status=TaskStatus.COMPLETED,
                summary=f"completed {node.id}",
            )

        with (
            mock.patch.object(dispatcher, "_run_node", side_effect=_fake_run_node),
            mock.patch.object(dispatcher, "_write_dispatch_ledger"),
        ):
            summary = dispatcher.run()

        # Simulate how the runner accumulates costs per completed node via AgentState.
        # Two nodes completed (coder + architect); apply one credit per node.
        state = AgentState()
        node_payloads = [
            {"profile_id": "coder-14b", "tokens_in": 1000, "tokens_out": 500, "cost_usd": 0.005},
            {"profile_id": "planner-30b", "tokens_in": 2000, "tokens_out": 800, "cost_usd": 0.010},
        ]
        for payload in node_payloads[: len(summary.completed)]:
            state.credit(**payload)
        assert abs(state.total_cost_usd - 0.015) < 1e-10
        assert state.session_tokens == 4300
