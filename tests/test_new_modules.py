# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for P2–P5 new modules: hf_sync, eval, spawner, teams, instincts."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# P2: HF Sync
# ---------------------------------------------------------------------------


class TestHFSync:
    def test_save_and_load_scores(self, tmp_path: Path) -> None:
        from specsmith.agent.hf_sync import load_cached_scores, save_scores

        scores = {"gpt-4.1": {"baseline_composite": 92.0}}
        save_scores(scores, tmp_path)
        loaded = load_cached_scores(tmp_path)
        assert "models" in loaded
        assert loaded["models"]["gpt-4.1"]["baseline_composite"] == 92.0
        assert "synced_at" in loaded

    def test_load_missing_returns_empty(self, tmp_path: Path) -> None:
        from specsmith.agent.hf_sync import load_cached_scores

        assert load_cached_scores(tmp_path) == {}

    def test_is_stale_no_cache(self, tmp_path: Path) -> None:
        from specsmith.agent.hf_sync import is_stale

        assert is_stale(tmp_path) is True

    def test_is_stale_fresh_cache(self, tmp_path: Path) -> None:
        from specsmith.agent.hf_sync import is_stale, save_scores

        save_scores({"test": {}}, tmp_path)
        assert is_stale(tmp_path, max_age_hours=1) is False

    def test_extract_benchmark_scores_empty(self) -> None:
        from specsmith.agent.hf_sync import _extract_benchmark_scores

        assert _extract_benchmark_scores({}) == {}

    def test_extract_benchmark_scores_with_data(self) -> None:
        from specsmith.agent.hf_sync import _extract_benchmark_scores

        info = {
            "cardData": {
                "eval_results": [
                    {
                        "dataset": {"name": "hellaswag"},
                        "metrics": [{"name": "accuracy", "value": 0.85}],
                    }
                ]
            }
        }
        scores = _extract_benchmark_scores(info)
        assert "hellaswag/accuracy" in scores
        assert scores["hellaswag/accuracy"] == 0.85


# ---------------------------------------------------------------------------
# P3: Eval Framework
# ---------------------------------------------------------------------------


class TestEvalFramework:
    def test_eval_case_to_dict(self) -> None:
        from specsmith.eval import EvalCase

        case = EvalCase(id="t1", name="Test", role="coder", prompt="Hello")
        d = case.to_dict()
        assert d["id"] == "t1"
        assert d["role"] == "coder"

    def test_score_output_all_match(self) -> None:
        from specsmith.eval.runner import score_output

        assert score_output("def fibonacci return list", ["def fibonacci", "return"]) == 1.0

    def test_score_output_partial(self) -> None:
        from specsmith.eval.runner import score_output

        score = score_output("def fibonacci", ["def fibonacci", "return", "list"])
        assert 0.3 < score < 0.4  # 1/3

    def test_score_output_none(self) -> None:
        from specsmith.eval.runner import score_output

        assert score_output("hello", ["xyz", "abc"]) == 0.0

    def test_run_case_stub(self) -> None:
        from specsmith.eval import EvalCase
        from specsmith.eval.runner import run_case_stub

        case = EvalCase(
            id="stub-test",
            name="Stub",
            role="coder",
            prompt="test",
            expected_keywords=["keyword1"],
        )
        result = run_case_stub(case)
        assert result.passed is True
        assert result.score == 1.0
        assert result.model == "stub"

    def test_run_suite(self) -> None:
        from specsmith.eval.builtins import CORE_SUITE
        from specsmith.eval.runner import run_suite

        report = run_suite(CORE_SUITE)
        assert report.total == 5
        assert report.passed == 5  # stubs always pass
        assert report.avg_score == 1.0

    def test_list_suites(self) -> None:
        from specsmith.eval.builtins import list_suites

        suites = list_suites()
        assert len(suites) >= 1
        assert suites[0].id == "core"

    def test_markdown_report(self) -> None:
        from specsmith.eval.builtins import CORE_SUITE
        from specsmith.eval.runner import generate_markdown_report, run_suite

        report = run_suite(CORE_SUITE)
        md = generate_markdown_report(report)
        assert "# Eval Report" in md
        assert "Passed" in md


# ---------------------------------------------------------------------------
# P4: Spawner & Teams
# ---------------------------------------------------------------------------


class TestSpawner:
    def test_spawn_agent(self) -> None:
        from specsmith.agent.spawner import SubAgentSpawner

        spawner = SubAgentSpawner()
        agent = spawner.spawn("coder")
        assert agent.role == "coder"
        assert "read_file" in agent.tools
        assert agent.status == "idle"

    def test_spawn_custom_tools(self) -> None:
        from specsmith.agent.spawner import SubAgentSpawner

        spawner = SubAgentSpawner()
        agent = spawner.spawn("custom", tools=["tool1", "tool2"])
        assert agent.tools == ["tool1", "tool2"]

    def test_complete_agent(self) -> None:
        from specsmith.agent.spawner import SubAgentSpawner

        spawner = SubAgentSpawner()
        agent = spawner.spawn("tester")
        spawner.complete(agent.id, {"passed": True})
        assert agent.status == "completed"
        assert agent.result["passed"] is True

    def test_list_active(self) -> None:
        from specsmith.agent.spawner import SubAgentSpawner

        spawner = SubAgentSpawner()
        a1 = spawner.spawn("coder")
        a2 = spawner.spawn("reviewer")
        spawner.complete(a1.id, {})
        active = spawner.list_active()
        assert len(active) == 1
        assert active[0].id == a2.id


class TestTeams:
    def test_list_teams(self) -> None:
        from specsmith.agent.teams import list_teams

        teams = list_teams()
        assert len(teams) >= 4
        ids = [t.id for t in teams]
        assert "pair-review" in ids
        assert "full-stack" in ids

    def test_get_team(self) -> None:
        from specsmith.agent.teams import get_team

        team = get_team("pair-review")
        assert team is not None
        assert len(team.members) == 2
        roles = [m.role for m in team.members]
        assert "coder" in roles
        assert "reviewer" in roles

    def test_team_to_dict(self) -> None:
        from specsmith.agent.teams import get_team

        team = get_team("full-stack")
        assert team is not None
        d = team.to_dict()
        assert d["id"] == "full-stack"
        assert len(d["members"]) == 3


# ---------------------------------------------------------------------------
# P5: Instincts
# ---------------------------------------------------------------------------


class TestInstincts:
    def test_add_and_list(self, tmp_path: Path) -> None:
        from specsmith.instinct import InstinctStore

        store = InstinctStore(tmp_path)
        rec = store.add("fix.*test", "Run pytest after fixing")
        assert rec.trigger_pattern == "fix.*test"
        all_inst = store.all()
        assert len(all_inst) == 1
        assert "pytest" in all_inst[0].content

    def test_remove(self, tmp_path: Path) -> None:
        from specsmith.instinct import InstinctStore

        store = InstinctStore(tmp_path)
        inst = store.add("pattern", "action content")
        removed = store.remove(inst.id)
        assert removed is True
        assert len(store.all()) == 0

    def test_persistence(self, tmp_path: Path) -> None:
        from specsmith.instinct import InstinctStore

        store1 = InstinctStore(tmp_path)
        store1.add("trigger pattern", "action content")
        # Reload from disk
        store2 = InstinctStore(tmp_path)
        assert len(store2.all()) == 1
        assert store2.all()[0].trigger_pattern == "trigger pattern"

    def test_record_accepted(self, tmp_path: Path) -> None:
        from specsmith.instinct import InstinctStore

        store = InstinctStore(tmp_path)
        inst = store.add("pattern", "action content")
        initial_conf = inst.confidence
        store.record_accepted(inst.id)
        assert inst.confidence > initial_conf
        assert inst.use_count == 1

    def test_export_markdown(self, tmp_path: Path) -> None:
        from specsmith.instinct import InstinctStore

        store = InstinctStore(tmp_path)
        store.add("test trigger", "test content")
        md = store.export_markdown()
        assert "# Instincts" in md
        assert "test trigger" in md
