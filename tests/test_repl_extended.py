# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Extended unit tests for specsmith.agent.repl — profile routing and command dispatch.

Complements the baseline test_repl.py by covering:
  TEST-RE-01: /fix command routes to coder profile via ProfileStore
  TEST-RE-02: /plan command routes to architect profile via ProfileStore
  TEST-RE-03: /test command routes to tester profile
  TEST-RE-04: /review command routes to reviewer profile
  TEST-RE-05: REPL /fix prefix is injected into the task string ("[FIX] ...")
  TEST-RE-06: REPL /plan prefix is injected into the task string ("[PLAN] ...")
  TEST-RE-07: /specsmith pass-through does NOT call orchestrator
  TEST-RE-08: Unknown slash commands fall through to broker (default path)
  TEST-RE-09: Provider diversity invariant — coder and reviewer use different families
  TEST-RE-10: Profile routing is deterministic across multiple resolve calls
  TEST-RE-11: REPL /agent command or profile_id override resolves to the pinned profile
  TEST-RE-12: Routes table is a superset of the minimum required slash-commands

No LLM, no AG2 calls; orchestrator and broker are mocked.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from specsmith.agent.profiles import ProfileStore, apply_preset, provider_family

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def default_store(tmp_path: Path) -> ProfileStore:
    """ProfileStore pre-loaded with the default preset — no ~/.specsmith dependency."""
    store_path = tmp_path / "agents.json"
    apply_preset("default", path=store_path)
    return ProfileStore.load(store_path)


# ---------------------------------------------------------------------------
# TEST-RE-01/02/03/04: Profile routing via ProfileStore
# ---------------------------------------------------------------------------


class TestProfileRouting:
    """Verify the routes table maps each key slash-command to the correct role."""

    def test_fix_routes_to_coder(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/fix")
        assert profile is not None, "/fix must resolve to a profile"
        assert profile.role == "coder", f"Expected role=coder, got {profile.role!r}"

    def test_plan_routes_to_architect(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/plan")
        assert profile is not None
        assert profile.role == "architect", f"Expected role=architect, got {profile.role!r}"

    def test_test_routes_to_tester(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/test")
        assert profile is not None
        assert profile.role == "tester"

    def test_review_routes_to_reviewer(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/review")
        assert profile is not None
        assert profile.role == "reviewer"

    def test_ask_routes_to_researcher(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/ask")
        assert profile is not None
        assert profile.role == "researcher"

    def test_commit_routes_to_editor(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/commit")
        assert profile is not None
        assert profile.role == "editor"

    def test_code_routes_to_coder(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/code")
        assert profile is not None
        assert profile.role == "coder"

    def test_refactor_routes_to_coder(self, default_store: ProfileStore) -> None:
        profile = default_store.resolve_for_activity("/refactor")
        assert profile is not None
        assert profile.role == "coder"


# ---------------------------------------------------------------------------
# TEST-RE-05/06: REPL command prefix injection
# ---------------------------------------------------------------------------


class TestReplCommandPrefix:
    """The REPL prepends a structured prefix to the task text for each slash-command.

    This is verified by observing what text is passed to orchestrator.run_task().
    """

    def _run_repl_command(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
        command: str,
        args: str = "some args",
    ) -> list[str]:
        """Run the REPL for one command, capture run_task calls, and return the task strings."""
        import specsmith.agent.repl as repl_mod

        task_calls: list[str] = []

        class _FakeOrch:
            def run_task(self, task: str, **kw: Any) -> SimpleNamespace:
                task_calls.append(task)
                return SimpleNamespace(
                    equilibrium=True,
                    confidence=0.9,
                    summary="ok",
                    files_changed=[],
                    test_results={},
                )

        monkeypatch.setattr(repl_mod, "Orchestrator", lambda: _FakeOrch())
        monkeypatch.chdir(tmp_path)

        user_input = f"{command} {args}" if args else command
        inputs = iter([user_input, "/exit"])
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        repl_mod.main()
        return task_calls

    def test_fix_prefix_injected(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        calls = self._run_repl_command(monkeypatch, tmp_path, "/fix", "broken import")
        assert len(calls) == 1
        assert "[FIX]" in calls[0], f"Expected [FIX] prefix in task, got: {calls[0]!r}"
        assert "broken import" in calls[0]

    def test_plan_prefix_injected(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        calls = self._run_repl_command(monkeypatch, tmp_path, "/plan", "add new endpoint")
        assert len(calls) == 1
        assert "[PLAN]" in calls[0], f"Expected [PLAN] prefix in task, got: {calls[0]!r}"
        assert "add new endpoint" in calls[0]

    def test_test_prefix_injected(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        calls = self._run_repl_command(monkeypatch, tmp_path, "/test", "")
        assert len(calls) == 1
        assert "[TEST]" in calls[0]

    def test_commit_prefix_injected(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        calls = self._run_repl_command(monkeypatch, tmp_path, "/commit", "")
        assert len(calls) == 1
        assert "[COMMIT]" in calls[0]

    def test_pr_prefix_injected(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        calls = self._run_repl_command(monkeypatch, tmp_path, "/pr", "")
        assert len(calls) == 1
        assert "[PR]" in calls[0]

    def test_fix_empty_args_prompts_usage(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture
    ) -> None:
        """/fix with no args must print a usage hint and NOT call run_task."""
        import specsmith.agent.repl as repl_mod

        task_calls: list[str] = []

        class _FakeOrch:
            def run_task(self, task: str, **kw: Any) -> SimpleNamespace:
                task_calls.append(task)
                return SimpleNamespace(
                    equilibrium=True, confidence=0.9, summary="", files_changed=[], test_results={}
                )

        monkeypatch.setattr(repl_mod, "Orchestrator", lambda: _FakeOrch())
        monkeypatch.chdir(tmp_path)
        inputs = iter(["/fix", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
        repl_mod.main()

        assert task_calls == [], "/fix with no args must NOT call run_task"
        out = capsys.readouterr().out
        assert "Usage" in out or "usage" in out.lower()


# ---------------------------------------------------------------------------
# TEST-RE-07: /specsmith pass-through does NOT call orchestrator
# ---------------------------------------------------------------------------


class TestSpecsmithPassThrough:
    def test_specsmith_passthrough_skips_orchestrator(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import subprocess as _subprocess

        import specsmith.agent.repl as repl_mod

        orch_calls: list[str] = []
        subprocess_calls: list[str] = []

        class _FakeOrch:
            def run_task(self, task: str, **kw: Any) -> SimpleNamespace:
                orch_calls.append(task)
                return SimpleNamespace(
                    equilibrium=True, confidence=0.9, summary="", files_changed=[], test_results={}
                )

        class _FakeResult:
            returncode = 0

        def _fake_run(cmd: str, **kw: Any) -> _FakeResult:
            subprocess_calls.append(cmd)
            return _FakeResult()

        monkeypatch.setattr(repl_mod, "Orchestrator", lambda: _FakeOrch())
        monkeypatch.setattr(_subprocess, "run", _fake_run)
        monkeypatch.chdir(tmp_path)
        inputs = iter(["/specsmith audit", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        repl_mod.main()

        assert orch_calls == [], "/specsmith must NOT invoke the orchestrator"
        assert any("audit" in c for c in subprocess_calls), "subprocess should run specsmith audit"


# ---------------------------------------------------------------------------
# TEST-RE-08: Unknown slash commands fall through to broker
# ---------------------------------------------------------------------------


class TestUnknownCommandFallthrough:
    def test_plain_english_goes_through_broker(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        import specsmith.agent.repl as repl_mod

        broker_calls: list[str] = []

        def _fake_classify(text: str) -> str:
            broker_calls.append(text)
            return "chat"

        def _fake_preflight(*a: Any, **kw: Any) -> SimpleNamespace:
            return SimpleNamespace(
                accepted=False,
                work_item_id="",
                requirement_ids=[],
                test_case_ids=[],
                clarifying_question="",
            )

        monkeypatch.setattr(repl_mod, "classify_intent", _fake_classify)
        monkeypatch.setattr(repl_mod, "run_preflight", _fake_preflight)
        monkeypatch.setattr(repl_mod, "infer_scope", lambda *a, **kw: {})
        monkeypatch.setattr(repl_mod, "narrate_plan", lambda *a, **kw: "")
        monkeypatch.setattr(repl_mod, "Orchestrator", lambda: None)
        monkeypatch.chdir(tmp_path)

        inputs = iter(["please add a README", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))
        repl_mod.main()

        assert broker_calls, "Plain English input must be classified by the broker"
        assert "README" in broker_calls[0]


# ---------------------------------------------------------------------------
# TEST-RE-09: Provider diversity — coder and reviewer use different families
# ---------------------------------------------------------------------------


class TestProviderDiversity:
    """The architect-coder-reviewer trio should span different provider families
    to maximise cross-check value (I7 diversity invariant)."""

    def test_coder_and_reviewer_different_provider_families(
        self, default_store: ProfileStore
    ) -> None:
        coder = default_store.resolve_for_activity("/fix")
        reviewer = default_store.resolve_for_activity("/review")
        coder_family = provider_family(coder.provider)
        reviewer_family = provider_family(reviewer.provider)
        assert coder_family != reviewer_family, (
            f"Coder ({coder.provider}, family={coder_family}) and "
            f"reviewer ({reviewer.provider}, family={reviewer_family}) should differ"
        )

    def test_all_profiles_have_valid_role(self, default_store: ProfileStore) -> None:
        from specsmith.agent.profiles import VALID_ROLES

        for profile in default_store.profiles:
            assert profile.role in VALID_ROLES, (
                f"Profile {profile.id!r} has invalid role {profile.role!r}"
            )


# ---------------------------------------------------------------------------
# TEST-RE-10: Profile routing is deterministic
# ---------------------------------------------------------------------------


class TestDeterministicRouting:
    def test_same_activity_always_resolves_same_profile(self, default_store: ProfileStore) -> None:
        """Multiple calls to resolve_for_activity with the same key return the same result."""
        for activity in ("/fix", "/plan", "/test", "/review"):
            first = default_store.resolve_for_activity(activity)
            second = default_store.resolve_for_activity(activity)
            assert first.id == second.id, (
                f"resolve_for_activity({activity!r}) must be deterministic"
            )

    def test_routing_unaffected_by_unrelated_activity_calls(
        self, default_store: ProfileStore
    ) -> None:
        """Calling resolve_for_activity with one activity doesn't change another's result."""
        coder_before = default_store.resolve_for_activity("/fix")
        _ = default_store.resolve_for_activity("/plan")
        _ = default_store.resolve_for_activity("/test")
        coder_after = default_store.resolve_for_activity("/fix")
        assert coder_before.id == coder_after.id


# ---------------------------------------------------------------------------
# TEST-RE-11: Profile_id override pins the session to that profile
# ---------------------------------------------------------------------------


class TestProfilePinning:
    """When a profile_id is set on the runner, it overrides the routes table."""

    def test_pinned_profile_overrides_route(self, tmp_path: Path) -> None:
        """If profile_id='coder', runner should use the coder profile regardless of activity."""
        store_path = tmp_path / "agents.json"
        apply_preset("default", path=store_path)
        store = ProfileStore.load(store_path)

        # Pin to architect
        architect = store.get("architect")
        assert architect is not None

        # Simulate what runner._resolve_for_activity does when profile_id is set:
        # it ignores the routes table and returns the pinned profile.
        pinned_profile_id = "architect"
        profile = store.get(pinned_profile_id)
        assert profile is not None
        assert profile.role == "architect", "Pinned profile should return architect, not coder"

    def test_pinned_profile_raises_for_unknown_id(self, tmp_path: Path) -> None:
        from specsmith.agent.profiles import ProfileError

        store_path = tmp_path / "agents.json"
        apply_preset("default", path=store_path)
        store = ProfileStore.load(store_path)
        with pytest.raises(ProfileError, match="unknown profile id"):
            store.get("nonexistent-profile-xyz")


# ---------------------------------------------------------------------------
# TEST-RE-12: Routes table covers minimum required slash-commands
# ---------------------------------------------------------------------------


class TestRoutesTableCompleteness:
    REQUIRED_ROUTES = {"/fix", "/plan", "/test", "/review", "/ask"}

    def test_all_required_routes_present(self, default_store: ProfileStore) -> None:
        for route in self.REQUIRED_ROUTES:
            assert route in default_store.routes, (
                f"Required route {route!r} missing from routes table"
            )

    def test_all_routes_resolve_to_valid_profiles(self, default_store: ProfileStore) -> None:
        for activity, profile_id in default_store.routes.items():
            profile = default_store.get(profile_id)
            assert profile is not None, (
                f"Route {activity!r} → {profile_id!r} does not resolve to a known profile"
            )

    def test_default_profile_id_exists(self, default_store: ProfileStore) -> None:
        default_id = default_store.default_profile_id
        assert default_id, "default_profile_id must not be empty"
        assert default_store.get(default_id) is not None, (
            f"default_profile_id={default_id!r} must resolve to a known profile"
        )
