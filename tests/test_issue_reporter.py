# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Tests for specsmith.issue_reporter (REQ-303, REQ-304)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from specsmith.issue_reporter import (
    DUPLICATE_THRESHOLD,
    SIMILAR_THRESHOLD,
    DuplicateBlockedError,
    DuplicateCheckResult,
    FiledIssueResult,
    _jaccard,
    _words,
    check_duplicate,
    file_issue,
    search_issues,
)

# ── Similarity helpers ────────────────────────────────────────────────────────


class TestWords:
    def test_lowercases(self) -> None:
        assert _words("Crash Bug") == {"crash", "bug"}

    def test_strips_punctuation(self) -> None:
        assert "hello" in _words("hello, world!")

    def test_removes_stop_words(self) -> None:
        result = _words("the crash is in the app")
        assert "the" not in result
        assert "crash" in result
        assert "app" in result

    def test_filters_short_words(self) -> None:
        # words ≤ 2 chars are filtered
        result = _words("a an in ok go crash")
        assert "a" not in result
        assert "an" not in result
        assert "crash" in result


class TestJaccard:
    def test_identical_sets(self) -> None:
        s = {"crash", "app", "startup"}
        assert _jaccard(s, s) == pytest.approx(1.0)

    def test_disjoint_sets(self) -> None:
        assert _jaccard({"a", "b"}, {"c", "d"}) == pytest.approx(0.0)

    def test_partial_overlap(self) -> None:
        a = {"crash", "app", "startup"}
        b = {"crash", "app", "other"}
        # intersection=2, union=4  → 0.5
        assert _jaccard(a, b) == pytest.approx(0.5)

    def test_empty_sets(self) -> None:
        assert _jaccard(set(), set()) == pytest.approx(0.0)

    def test_one_empty(self) -> None:
        assert _jaccard({"a"}, set()) == pytest.approx(0.0)


# ── DuplicateCheckResult ──────────────────────────────────────────────────────


class TestDuplicateCheckResult:
    def test_blocked_when_duplicates(self) -> None:
        r = DuplicateCheckResult(duplicates=[{"title": "foo"}])
        assert r.blocked is True
        assert r.has_likely_duplicates is True

    def test_not_blocked_without_duplicates(self) -> None:
        r = DuplicateCheckResult(similar=[{"title": "foo"}])
        assert r.blocked is False

    def test_to_dict_keys(self) -> None:
        r = DuplicateCheckResult()
        d = r.to_dict()
        assert "duplicates" in d
        assert "similar" in d
        assert "blocked" in d
        assert "error" in d


# ── search_issues ─────────────────────────────────────────────────────────────


class TestSearchIssues:
    def _make_gh_response(self, items: list[dict]) -> MagicMock:
        mock = MagicMock()
        mock.returncode = 0
        mock.stdout = json.dumps({"items": items})
        return mock

    @patch("specsmith.issue_reporter._gh_available", return_value=True)
    @patch("specsmith.issue_reporter.subprocess.run")
    def test_returns_list_of_dicts(
        self, mock_run: MagicMock, _mock_avail: MagicMock
    ) -> None:
        items = [
            {
                "number": 1,
                "title": "crash on startup",
                "html_url": "https://github.com/x/1",
                "state": "open",
            },
        ]
        mock_run.return_value = self._make_gh_response(items)
        results = search_issues("kairos", "crash startup")
        assert len(results) == 1
        assert results[0]["number"] == 1
        assert results[0]["title"] == "crash on startup"

    @patch("specsmith.issue_reporter._gh_available", return_value=True)
    @patch("specsmith.issue_reporter.subprocess.run")
    def test_empty_items(
        self, mock_run: MagicMock, _mock_avail: MagicMock
    ) -> None:
        mock_run.return_value = self._make_gh_response([])
        assert search_issues("specsmith", "anything") == []

    @patch("specsmith.issue_reporter._gh_available", return_value=True)
    @patch("specsmith.issue_reporter.subprocess.run")
    def test_non_dict_items_skipped(
        self, mock_run: MagicMock, _mock_avail: MagicMock
    ) -> None:
        mock = MagicMock()
        mock.returncode = 0
        real_item = {"number": 5, "title": "real", "html_url": "u", "state": "open"}
        mock.stdout = json.dumps({"items": ["not_a_dict", real_item]})
        mock_run.return_value = mock
        results = search_issues("kairos", "real")
        assert len(results) == 1

    @patch("specsmith.issue_reporter._gh_available", return_value=False)
    @patch("specsmith.issue_reporter.urllib.request.urlopen")
    def test_unauthenticated_fallback(
        self, mock_urlopen: MagicMock, _mock_avail: MagicMock
    ) -> None:
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.read.return_value = json.dumps({"items": []}).encode()
        mock_urlopen.return_value = mock_resp
        results = search_issues("kairos", "test")
        assert results == []


# ── check_duplicate ───────────────────────────────────────────────────────────


class TestCheckDuplicate:
    def _patch_search(self, monkeypatch: pytest.MonkeyPatch, items: list[dict]) -> None:
        monkeypatch.setattr(
            "specsmith.issue_reporter.search_issues",
            lambda repo, query, **kw: items,
        )

    def test_no_candidates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_search(monkeypatch, [])
        result = check_duplicate("kairos", "unique title nobody filed")
        assert result.duplicates == []
        assert result.similar == []
        assert result.blocked is False

    def test_high_similarity_goes_to_duplicates(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # "crash on startup" vs "crash on startup" → Jaccard ≈ 1.0 ≥ DUPLICATE_THRESHOLD
        self._patch_search(
            monkeypatch,
            [{"number": 1, "title": "crash on startup", "html_url": "u", "state": "open"}],
        )
        result = check_duplicate("kairos", "crash on startup")
        assert len(result.duplicates) == 1
        assert result.blocked is True

    def test_medium_similarity_goes_to_similar(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Enough word overlap to be SIMILAR but not a DUPLICATE
        # Our title: "crash during startup", candidate: "crash when launching app"
        # Words: {crash, during, startup} vs {crash, when, launching, app}
        # intersection={crash}, union={crash,during,startup,when,launching,app}
        # → 1/6 ≈ 0.17 < SIMILAR
        # Let's use a closer pair: "settings page crash" vs "crash settings page"
        # both → {settings, page, crash} → Jaccard = 1.0 → duplicate
        # Try: "specsmith preflight fails" vs "preflight command error"
        # {specsmith, preflight, fails} vs {preflight, command, error}
        # intersection={preflight}, union=5 → 0.2 < SIMILAR; let's pick known values
        # "kairos window crash bug" vs "kairos crash window"
        # {kairos,window,crash,bug} vs {kairos,crash,window} → inter=3, union=4 → 0.75 ≥ DUPLICATE
        # For SIMILAR test, need 0.30 ≤ J < 0.60
        # "kairos crash settings" {kairos,crash,settings}
        # vs "kairos crashes network" {kairos,crashes,network}
        # inter={kairos}, union={kairos,crash,settings,crashes,network}=5 → 0.2 < SIMILAR
        # Let's just patch at the Jaccard level by controlling exact titles:
        # "window crash" vs "window bug"
        # → inter={window}, union={window,crash,bug}=3 → 0.33 ≥ SIMILAR < DUPLICATE
        self._patch_search(
            monkeypatch,
            [{"number": 2, "title": "window bug", "html_url": "u", "state": "open"}],
        )
        result = check_duplicate("kairos", "window crash")
        # {window,crash} vs {window,bug}: inter=1, union=3 → 0.33 ≥ 0.30 SIMILAR
        assert len(result.similar) == 1
        assert result.blocked is False

    def test_low_similarity_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        self._patch_search(
            monkeypatch,
            [
                {
                    "number": 3,
                    "title": "completely unrelated topic",
                    "html_url": "u",
                    "state": "open",
                },
            ],
        )
        result = check_duplicate("kairos", "specific crash bug")
        # Minimal/zero word overlap → neither similar nor duplicate
        assert result.blocked is False

    def test_search_error_captured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        def raise_exc(*args: object, **kwargs: object) -> None:
            raise RuntimeError("network down")

        monkeypatch.setattr("specsmith.issue_reporter.search_issues", raise_exc)
        result = check_duplicate("kairos", "any title")
        assert result.error != ""
        assert result.blocked is False


# ── file_issue ────────────────────────────────────────────────────────────────


class TestFileIssue:
    def test_blocks_on_duplicates_without_force(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "specsmith.issue_reporter.check_duplicate",
            lambda repo, title: DuplicateCheckResult(
                duplicates=[{"number": 1, "title": title, "html_url": "u", "similarity": 0.9}]
            ),
        )
        with pytest.raises(DuplicateBlockedError) as exc_info:
            file_issue("kairos", "crash on startup", "body text")
        assert exc_info.value.result.blocked is True

    def test_force_bypasses_duplicate_check(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # check_duplicate should NOT be called when force=True
        called = []
        monkeypatch.setattr(
            "specsmith.issue_reporter.check_duplicate",
            lambda *a, **kw: called.append(True) or DuplicateCheckResult(),
        )
        monkeypatch.setattr(
            "specsmith.issue_reporter._gh_api_post",
            lambda path, payload: {
                "number": 99,
                "html_url": "https://github.com/BitConcepts/kairos/issues/99",
                "title": payload["title"],
            },
        )
        result = file_issue("kairos", "title", "body", force=True)
        assert result.ok is True
        assert result.number == 99
        assert called == []  # check_duplicate was never called

    def test_file_returns_url_on_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "specsmith.issue_reporter.check_duplicate",
            lambda *a, **kw: DuplicateCheckResult(),
        )
        monkeypatch.setattr(
            "specsmith.issue_reporter._gh_api_post",
            lambda path, payload: {
                "number": 42,
                "html_url": "https://github.com/BitConcepts/kairos/issues/42",
                "title": "My Bug",
            },
        )
        result = file_issue("kairos", "My Bug", "details")
        assert result.ok is True
        assert result.number == 42
        assert "42" in result.html_url

    def test_file_returns_error_on_gh_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "specsmith.issue_reporter.check_duplicate",
            lambda *a, **kw: DuplicateCheckResult(),
        )
        monkeypatch.setattr(
            "specsmith.issue_reporter._gh_api_post",
            lambda path, payload: {"error": "gh: authentication failed"},
        )
        result = file_issue("kairos", "title", "body")
        assert result.ok is False
        assert "authentication" in result.error

    def test_labels_passed_to_payload(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        captured: list[dict] = []
        monkeypatch.setattr(
            "specsmith.issue_reporter.check_duplicate",
            lambda *a, **kw: DuplicateCheckResult(),
        )

        def capture_post(path: str, payload: dict) -> dict:
            captured.append(payload)
            return {"number": 1, "html_url": "u", "title": "t"}

        monkeypatch.setattr("specsmith.issue_reporter._gh_api_post", capture_post)
        file_issue("kairos", "title", "body", labels=("bug", "crash"))
        assert captured[0]["labels"] == ["bug", "crash"]

    def test_filed_result_to_dict(self) -> None:
        r = FiledIssueResult(number=5, html_url="https://u", title="t")
        d = r.to_dict()
        assert d["ok"] is True
        assert d["number"] == 5


# ── DuplicateBlockedError ─────────────────────────────────────────────────────


class TestDuplicateBlockedError:
    def test_message_contains_title(self) -> None:
        result = DuplicateCheckResult(
            duplicates=[{"title": "known crash", "number": 1, "html_url": "u", "similarity": 0.8}]
        )
        err = DuplicateBlockedError(result)
        assert "known crash" in str(err)
        assert "force" in str(err).lower()

    def test_result_attached(self) -> None:
        result = DuplicateCheckResult(
            duplicates=[{"title": "x", "number": 1, "html_url": "u", "similarity": 0.7}]
        )
        err = DuplicateBlockedError(result)
        assert err.result is result


# ── Threshold constants ───────────────────────────────────────────────────────


class TestThresholds:
    def test_duplicate_threshold_above_similar(self) -> None:
        assert DUPLICATE_THRESHOLD > SIMILAR_THRESHOLD

    def test_similar_threshold_positive(self) -> None:
        assert 0 < SIMILAR_THRESHOLD < 1.0

    def test_duplicate_threshold_below_one(self) -> None:
        assert DUPLICATE_THRESHOLD < 1.0
