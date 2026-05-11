# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for the multi-provider LLM client (TEST-274..TEST-276, REQ-275..REQ-277)."""

from __future__ import annotations

import urllib.error
from typing import Any
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# TEST-274 — LLM Client fallback on 429/401 (REQ-275)
# ---------------------------------------------------------------------------


class TestLLMClientFallback:
    def test_fallback_on_429(self) -> None:
        """TEST-274: LLMClient falls back to MockProvider when primary returns 429."""
        from specsmith.agent.llm_client import LLMClient, MockProvider

        class Failing429(MockProvider):
            name = "failing429"

            def chat(self, messages: Any, **kwargs: Any) -> Any:
                raise urllib.error.HTTPError(
                    url="http://x",
                    code=429,
                    msg="Too Many Requests",
                    hdrs=None,
                    fp=None,  # type: ignore[arg-type]
                )

        mock = MockProvider("ok-response")
        client = LLMClient([Failing429("x"), mock])
        result = client.chat([{"role": "user", "content": "hi"}])
        assert result.text == "ok-response"
        assert result.provider == "mock"

    def test_fallback_on_401(self) -> None:
        """TEST-274: LLMClient falls back when primary returns 401."""
        from specsmith.agent.llm_client import LLMClient, MockProvider

        class Failing401(MockProvider):
            name = "failing401"

            def chat(self, messages: Any, **kwargs: Any) -> Any:
                raise urllib.error.HTTPError(
                    url="http://x",
                    code=401,
                    msg="Unauthorized",
                    hdrs=None,
                    fp=None,  # type: ignore[arg-type]
                )

        mock = MockProvider("fallback-ok")
        client = LLMClient([Failing401("x"), mock])
        result = client.chat([{"role": "user", "content": "test"}])
        assert result.text == "fallback-ok"

    def test_all_providers_fail_raises_llm_error(self) -> None:
        """TEST-274: all providers failing raises LLMError."""
        from specsmith.agent.llm_client import LLMClient, LLMError, MockProvider

        class AlwaysFail(MockProvider):
            name = "fail"

            def chat(self, messages: Any, **kwargs: Any) -> Any:
                raise urllib.error.HTTPError(
                    url="http://x",
                    code=503,
                    msg="Service Unavailable",
                    hdrs=None,
                    fp=None,  # type: ignore[arg-type]
                )

        client = LLMClient([AlwaysFail("x")])
        with pytest.raises(LLMError):
            client.chat([{"role": "user", "content": "hi"}])


# ---------------------------------------------------------------------------
# TEST-275 — O-series parameter translation (REQ-276)
# ---------------------------------------------------------------------------


class TestOSeriesTranslation:
    def test_o3_uses_max_completion_tokens_and_developer_role(self) -> None:
        """TEST-275: o3-mini model uses max_completion_tokens, temperature=1, developer role."""
        from specsmith.agent.llm_client import _translate_o_series

        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ]
        adj_messages, extra = _translate_o_series(messages, max_tokens=4096, temperature=0.3)

        # system → developer
        assert adj_messages[0]["role"] == "developer"
        assert adj_messages[1]["role"] == "user"

        # O-series params
        assert "max_completion_tokens" in extra
        assert extra["max_completion_tokens"] == 4096  # noqa: PLR2004
        assert extra["temperature"] == 1  # noqa: PLR2004
        assert "max_tokens" not in extra

    def test_is_o_series_detection(self) -> None:
        """TEST-275: _is_o_series correctly detects o1/o3/o4 variants."""
        from specsmith.agent.llm_client import _is_o_series

        assert _is_o_series("o1")
        assert _is_o_series("o3-mini")
        assert _is_o_series("o4-mini-deep-research")
        assert _is_o_series("gpt-o3-mini-preview")

        assert not _is_o_series("gpt-4o")
        assert not _is_o_series("claude-3-5-sonnet")
        assert not _is_o_series("qwen2.5:14b")


# ---------------------------------------------------------------------------
# TEST-276 — vLLM guided-JSON mode (REQ-277)
# ---------------------------------------------------------------------------


class TestVLLMGuidedJSON:
    def test_guided_json_payload_for_byoe(self) -> None:
        """TEST-276: byoe provider with json_schema → guided_json in request body."""
        captured: list[dict[str, Any]] = []

        def fake_http_post(
            url: str, *, body: dict[str, Any], headers: Any = None, timeout: float = 60.0
        ) -> tuple[int, dict]:  # noqa: ARG001
            captured.append(body)
            # Return a minimal valid OpenAI-compatible response
            return 200, {
                "choices": [{"message": {"role": "assistant", "content": '{"foo": "bar"}'}}]
            }

        from specsmith.agent.llm_client import dispatch_byoe

        with patch("specsmith.agent.llm_client._http_post_json", side_effect=fake_http_post):
            dispatch_byoe(
                base_url="http://localhost:8000/v1",
                model="Qwen3-14B",
                messages=[{"role": "user", "content": "hi"}],
                json_schema={"type": "object", "properties": {"foo": {"type": "string"}}},
            )

        assert len(captured) == 1
        sent = captured[0]
        assert "guided_json" in sent
        assert "chat_template_kwargs" in sent
        assert sent["chat_template_kwargs"]["enable_thinking"] is False

    def test_json_mode_without_schema_for_byoe(self) -> None:
        """TEST-276: json_mode=True without schema also sets chat_template_kwargs."""
        captured: list[dict[str, Any]] = []

        def fake_http_post(
            url: str, *, body: dict[str, Any], headers: Any = None, timeout: float = 60.0
        ) -> tuple[int, dict]:  # noqa: ARG001
            captured.append(body)
            return 200, {"choices": [{"message": {"role": "assistant", "content": '{"x": 1}'}}]}

        from specsmith.agent.llm_client import dispatch_byoe

        with patch("specsmith.agent.llm_client._http_post_json", side_effect=fake_http_post):
            dispatch_byoe(
                base_url="http://localhost:8000/v1",
                model="llama3.1:8b",
                messages=[{"role": "user", "content": "hi"}],
                json_mode=True,
            )

        assert len(captured) == 1
        sent = captured[0]
        assert "chat_template_kwargs" in sent
        assert sent["chat_template_kwargs"]["enable_thinking"] is False
        assert sent.get("response_format") == {"type": "json_object"}


# ---------------------------------------------------------------------------
# Additional LLMClient tests
# ---------------------------------------------------------------------------


class TestLLMClientJSONExtraction:
    def test_chat_json_parses_clean_json(self) -> None:
        """TEST-275 (auxiliary): chat_json parses a clean JSON response."""
        from specsmith.agent.llm_client import LLMClient, MockProvider

        client = LLMClient([MockProvider('{"key": "value"}')])
        result_json, result = client.chat_json([{"role": "user", "content": "test"}])
        assert result_json == {"key": "value"}

    def test_chat_json_extracts_from_fence(self) -> None:
        """TEST-275 (auxiliary): chat_json extracts JSON from markdown code fence."""
        from specsmith.agent.llm_client import LLMClient, MockProvider

        raw = 'Sure! Here is the result:\n```json\n{"answer": 42}\n```\nHope that helps!'
        client = LLMClient([MockProvider(raw)])
        result_json, _ = client.chat_json([{"role": "user", "content": "test"}])
        assert result_json["answer"] == 42  # noqa: PLR2004
