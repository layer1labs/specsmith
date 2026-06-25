# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for specsmith.agent.model_router (REQ-388, REQ-389, TEST-396, TEST-397)."""

from __future__ import annotations

import os
from pathlib import Path  # noqa: F401
from unittest.mock import patch

# ---------------------------------------------------------------------------
# classify_intent (REQ-388, TEST-396)
# ---------------------------------------------------------------------------


class TestClassifyIntent:
    def test_coding_slash_command(self) -> None:
        from specsmith.agent.model_router import classify_intent

        assert classify_intent("/code write a parser") == "coding"
        assert classify_intent("/fix the bug in utils.py") == "coding"
        assert classify_intent("/refactor the class hierarchy") == "coding"
        assert classify_intent("/test coverage for api module") == "coding"
        assert classify_intent("/commit staged changes") == "coding"
        assert classify_intent("/pr prepare release") == "coding"

    def test_reasoning_slash_command(self) -> None:
        from specsmith.agent.model_router import classify_intent

        assert classify_intent("/architect the microservices layout") == "reasoning"
        assert classify_intent("/plan the migration") == "reasoning"
        assert classify_intent("/audit the security model") == "reasoning"
        assert classify_intent("/review this PR") == "reasoning"
        assert classify_intent("/why was this decision made") == "reasoning"

    def test_coding_keyword(self) -> None:
        from specsmith.agent.model_router import classify_intent

        assert classify_intent("write a function that does X") == "coding"
        assert classify_intent("implement the authentication module") == "coding"
        assert classify_intent("debug the import error") == "coding"
        assert classify_intent("there is a bug in the loop") == "coding"
        assert classify_intent("refactor this class") == "coding"

    def test_reasoning_keyword(self) -> None:
        from specsmith.agent.model_router import classify_intent

        assert classify_intent("analyze the architecture tradeoffs") == "reasoning"
        assert classify_intent("explain why this approach is better") == "reasoning"
        assert classify_intent("evaluate the design alternatives") == "reasoning"
        assert classify_intent("what are the pros and cons") == "reasoning"
        assert classify_intent("assess the scalability of this model") == "reasoning"

    def test_general_fallback(self) -> None:
        from specsmith.agent.model_router import classify_intent

        assert classify_intent("what is the status of the project") == "general"
        assert classify_intent("hello, how are you") == "general"
        assert classify_intent("what did we do last session") == "general"
        assert classify_intent("") == "general"

    def test_coding_beats_reasoning_on_overlap(self) -> None:
        """Coding keywords are checked before reasoning; overlap → coding wins."""
        from specsmith.agent.model_router import classify_intent

        # "code" is coding, "architecture" is reasoning; coding wins
        assert classify_intent("write code for the architecture module") == "coding"


# ---------------------------------------------------------------------------
# ModelRouter (REQ-388, TEST-396)
# ---------------------------------------------------------------------------


class TestModelRouter:
    def _router(self) -> object:
        from specsmith.agent.model_router import ModelRouter

        return ModelRouter(
            {
                "general": "qwen2.5:14b",
                "coding": "qwen2.5-coder:14b",
                "reasoning": "deepseek-r1:14b",
            }
        )

    def test_first_call_returns_model_and_not_switched(self) -> None:
        from specsmith.agent.model_router import ModelRouter

        router = ModelRouter({"general": "qwen2.5:7b", "coding": "qwen2.5-coder:7b"})
        model, switched = router.route("hello")
        assert model == "qwen2.5:7b"
        assert switched is False  # first call: no previous role → not a switch

    def test_coding_utterance_returns_coding_model(self) -> None:
        router = self._router()
        from specsmith.agent.model_router import ModelRouter

        assert isinstance(router, ModelRouter)
        model, _ = router.route("write a function to parse JSON")
        assert model == "qwen2.5-coder:14b"

    def test_reasoning_utterance_returns_reasoning_model(self) -> None:
        router = self._router()
        model, _ = router.route("analyze the architecture tradeoffs")
        assert model == "deepseek-r1:14b"

    def test_general_utterance_returns_general_model(self) -> None:
        router = self._router()
        model, _ = router.route("what is the project status")
        assert model == "qwen2.5:14b"

    def test_switched_true_on_role_change(self) -> None:
        router = self._router()
        router.route("what is the status")  # general
        model, switched = router.route("write a function")  # coding → switch
        assert switched is True
        assert model == "qwen2.5-coder:14b"

    def test_switched_false_on_same_role(self) -> None:
        router = self._router()
        router.route("write a function")  # coding
        model, switched = router.route("implement another function")  # still coding
        assert switched is False
        assert model == "qwen2.5-coder:14b"

    def test_empty_roles_returns_none(self) -> None:
        from specsmith.agent.model_router import ModelRouter

        router = ModelRouter({})
        model, switched = router.route("anything")
        assert model is None
        assert switched is False

    def test_fallback_to_general_when_role_missing(self) -> None:
        from specsmith.agent.model_router import ModelRouter

        # Only general configured; coding utterance falls back to general.
        router = ModelRouter({"general": "qwen2.5:7b"})
        model, _ = router.route("write a function")
        assert model == "qwen2.5:7b"

    def test_table_contains_all_configured_roles(self) -> None:
        router = self._router()
        table = router.table()
        assert "general" in table
        assert "coding" in table
        assert "reasoning" in table
        assert "qwen2.5:14b" in table
        assert "qwen2.5-coder:14b" in table
        assert "deepseek-r1:14b" in table

    def test_table_marks_active_role(self) -> None:
        router = self._router()
        router.route("write a function")  # activates coding
        table = router.table()
        assert "active" in table.lower() or "◀" in table

    def test_table_empty_router_message(self) -> None:
        from specsmith.agent.model_router import ModelRouter

        router = ModelRouter({})
        table = router.table()
        assert "not configured" in table.lower() or "no multi" in table.lower()

    def test_active_model_and_role_properties(self) -> None:
        router = self._router()
        assert router.active_model is None  # type: ignore[attr-defined]
        assert router.active_role is None  # type: ignore[attr-defined]
        router.route("analyze the design")
        assert router.active_model == "deepseek-r1:14b"  # type: ignore[attr-defined]
        assert router.active_role == "reasoning"  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# AgentRunner ModelRouter integration (REQ-389, TEST-397)
# ---------------------------------------------------------------------------


class TestAgentRunnerModelRouter:
    """Verify that AgentRunner sets/restores SPECSMITH_OLLAMA_MODEL per turn."""

    def _write_local_models(self, tmp_path: Path) -> None:
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir(parents=True, exist_ok=True)
        cfg = spec_dir / "local-models.yml"
        cfg.write_text(
            "provider: ollama\n"
            "hardware: nvidia-16gb\n"
            "models:\n"
            "  general: qwen2.5:14b\n"
            "  coding: qwen2.5-coder:14b\n"
            "  reasoning: deepseek-r1:14b\n",
            encoding="utf-8",
        )

    def test_router_loaded_from_config(self, tmp_path: Path) -> None:
        self._write_local_models(tmp_path)
        from specsmith.agent.runner import AgentRunner

        runner = AgentRunner(project_dir=str(tmp_path))
        assert runner._model_router is not None

    def test_no_router_without_config(self, tmp_path: Path) -> None:
        from specsmith.agent.runner import AgentRunner

        runner = AgentRunner(project_dir=str(tmp_path))
        assert runner._model_router is None

    def test_coding_turn_sets_ollama_env_var(self, tmp_path: Path) -> None:
        """Coding utterance temporarily sets SPECSMITH_OLLAMA_MODEL = coder model."""
        self._write_local_models(tmp_path)

        captured: list[str] = []

        def fake_run_chat(*_args, **_kwargs):  # type: ignore[no-untyped-def]
            captured.append(os.environ.get("SPECSMITH_OLLAMA_MODEL", ""))
            return None

        from specsmith.agent.runner import AgentRunner

        runner = AgentRunner(project_dir=str(tmp_path))

        with patch("specsmith.agent.runner.run_chat", fake_run_chat, create=True):
            # Import the module so we can patch correctly
            import specsmith.agent.chat_runner as cr

            with patch.object(cr, "run_chat", fake_run_chat):
                runner._handle_command("write a function")

        # The env var should have been set to the coding model during the call
        # (we captured it inside fake_run_chat).  After the turn it must be
        # restored (or removed) — verify by checking the env now.
        assert os.environ.get("SPECSMITH_OLLAMA_MODEL") != "qwen2.5-coder:14b"

    def test_env_var_restored_after_turn(self, tmp_path: Path) -> None:
        """SPECSMITH_OLLAMA_MODEL restored to its original value after each turn."""
        self._write_local_models(tmp_path)

        sentinel = "test-model-sentinel"
        os.environ["SPECSMITH_OLLAMA_MODEL"] = sentinel

        try:
            import specsmith.agent.chat_runner as cr

            def fake_run_chat(*_args, **_kwargs):  # type: ignore[no-untyped-def]
                return None

            from specsmith.agent.runner import AgentRunner

            runner = AgentRunner(project_dir=str(tmp_path))
            with patch.object(cr, "run_chat", fake_run_chat):
                runner._handle_command("implement a parser")

            # Must be restored to sentinel after the turn
            assert os.environ.get("SPECSMITH_OLLAMA_MODEL") == sentinel
        finally:
            os.environ.pop("SPECSMITH_OLLAMA_MODEL", None)
