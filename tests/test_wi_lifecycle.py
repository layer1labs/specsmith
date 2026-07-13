# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Comprehensive tests for the WI lifecycle subsystem.

Covers:
  - WorkItem dataclass: to_dict/from_dict, can_transition_to, is_terminal
  - WorkItemStore: create, get, upsert, list_by_status, set_status,
    mark_implemented, promote_to_req, tag, import_from_ledger, persistence
  - WorkItemError: invalid transitions, missing WIs, bad kinds/statuses
  - CLI: specsmith wi list / show / close / archive / promote / tag / import
  - Preflight wiring: run_preflight creates a WI in workitems.json
  - Verify wiring: run_verify with equilibrium marks WI as implemented
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from specsmith.cli import main
from specsmith.wi_store import (
    WI_KINDS,
    WI_STATES,
    WI_TERMINAL_STATES,
    WI_TRANSITIONS,
    WorkItem,
    WorkItemError,
    WorkItemStore,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _store(tmp_path: Path) -> WorkItemStore:
    return WorkItemStore(tmp_path)


def _wi(store: WorkItemStore, wi_id: str = "WI-DEADBEEF", **kw: object) -> WorkItem:
    intent = str(kw.pop("intent", "test intent"))  # type: ignore[misc]
    return store.create(wi_id, intent=intent, **kw)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# WorkItem dataclass
# ---------------------------------------------------------------------------


class TestWorkItemDataclass:
    def test_defaults(self) -> None:
        wi = WorkItem(id="WI-AABBCCDD")
        assert wi.status == "open"
        assert wi.kind == "feature"
        assert wi.verified is False
        assert wi.requirement_ids == []
        assert wi.test_case_ids == []

    def test_to_dict_round_trip(self) -> None:
        wi = WorkItem(
            id="WI-11223344",
            status="implemented",
            kind="bug",
            intent="fix the parser",
            requirement_ids=["REQ-001"],
            test_case_ids=["TEST-001"],
            verified=True,
        )
        d = wi.to_dict()
        wi2 = WorkItem.from_dict(d)
        assert wi2.id == wi.id
        assert wi2.status == wi.status
        assert wi2.kind == wi.kind
        assert wi2.intent == wi.intent
        assert wi2.requirement_ids == ["REQ-001"]
        assert wi2.verified is True

    def test_from_dict_ignores_unknown_keys(self) -> None:
        """Deserialisation must not blow up on unknown keys (forward compat)."""
        d = {"id": "WI-AAAABBBB", "status": "open", "future_field": "ignored"}
        wi = WorkItem.from_dict(d)
        assert wi.id == "WI-AAAABBBB"

    def test_is_terminal_true(self) -> None:
        for state in WI_TERMINAL_STATES:
            wi = WorkItem(id="WI-FFFFFFFF", status=state)
            assert wi.is_terminal(), f"Expected {state!r} to be terminal"

    def test_is_terminal_false(self) -> None:
        for state in ("open", "implemented"):
            wi = WorkItem(id="WI-00000000", status=state)
            assert not wi.is_terminal(), f"Expected {state!r} NOT to be terminal"

    def test_can_transition_to_all_valid(self) -> None:
        for src, targets in WI_TRANSITIONS.items():
            wi = WorkItem(id="WI-TTTTTTT1", status=src)
            for dst in targets:
                assert wi.can_transition_to(dst), f"{src} → {dst} should be allowed"

    def test_can_transition_to_invalid(self) -> None:
        wi = WorkItem(id="WI-TTTTTTT2", status="promoted")
        for dst in WI_STATES:
            assert not wi.can_transition_to(dst), f"promoted → {dst} should be forbidden"

    def test_archived_can_reopen(self) -> None:
        wi = WorkItem(id="WI-REREOPEN", status="archived")
        assert wi.can_transition_to("open")


# ---------------------------------------------------------------------------
# WorkItemStore — persistence
# ---------------------------------------------------------------------------


class TestWorkItemStorePersistence:
    def test_rejects_workitem_path_outside_project_root(self, tmp_path: Path, monkeypatch) -> None:
        """Persistence paths must remain under the caller's project root (REQ-451)."""
        original_realpath = os.path.realpath

        def escape_state(path: str) -> str:
            if path.endswith(".specsmith"):
                return original_realpath(str(tmp_path.parent / "outside"))
            return original_realpath(path)

        monkeypatch.setattr(os.path, "realpath", escape_state)
        with pytest.raises(WorkItemError, match="escapes project root"):
            WorkItemStore(tmp_path)

    def test_load_missing_file_returns_empty(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        assert store.load() == []

    def test_save_and_reload(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        _wi(store, "WI-PERSISTS1")
        store2 = _store(tmp_path)
        loaded = store2.get("WI-PERSISTS1")
        assert loaded is not None
        assert loaded.id == "WI-PERSISTS1"

    def test_save_is_atomic_no_tmp_file_left(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        _wi(store, "WI-ATOMICABC")
        tmp = tmp_path / ".specsmith" / "workitems.json.tmp"
        assert not tmp.exists(), "tmp file must be renamed away after save"

    def test_corrupt_json_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / ".specsmith" / "workitems.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("INVALID JSON {{{{", encoding="utf-8")
        store = _store(tmp_path)
        assert store.load() == []

    def test_non_list_json_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / ".specsmith" / "workitems.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text('{"not": "a list"}', encoding="utf-8")
        assert _store(tmp_path).load() == []

    def test_upsert_updates_existing(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        wi = _wi(store, "WI-UPSERT01")
        wi.kind = "bug"
        store.upsert(wi)
        reloaded = store.get("WI-UPSERT01")
        assert reloaded is not None
        assert reloaded.kind == "bug"


# ---------------------------------------------------------------------------
# WorkItemStore — CRUD
# ---------------------------------------------------------------------------


class TestWorkItemStoreCRUD:
    def test_create_is_idempotent(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        wi1 = store.create("WI-IDEM0001", intent="hello")
        wi2 = store.create("WI-IDEM0001", intent="different")
        assert wi1.id == wi2.id
        assert wi2.intent == "hello"  # original intent preserved

    def test_create_persists_all_fields(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create(
            "WI-FULLTEST",
            intent="full test",
            requirement_ids=["REQ-001", "REQ-002"],
            test_case_ids=["TEST-001"],
            confidence_target=0.9,
            kind="spike",
        )
        wi = store.get("WI-FULLTEST")
        assert wi is not None
        assert wi.requirement_ids == ["REQ-001", "REQ-002"]
        assert wi.test_case_ids == ["TEST-001"]
        assert wi.confidence_target == 0.9
        assert wi.kind == "spike"
        assert wi.status == "open"

    def test_get_returns_none_for_missing(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        assert store.get("WI-NOTHERE") is None

    def test_list_by_status_all(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-A0000001", intent="a")
        store.create("WI-A0000002", intent="b")
        store.set_status("WI-A0000002", "archived", reason="deferred")
        all_items = store.list_by_status(None)
        assert len(all_items) == 2

    def test_list_by_status_filtered(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-F0000001", intent="open one")
        store.create("WI-F0000002", intent="open two")
        store.set_status("WI-F0000002", "archived", reason="x")
        open_items = store.list_by_status("open")
        assert len(open_items) == 1
        assert open_items[0].id == "WI-F0000001"

    def test_list_by_status_empty_result(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-NOIMPL01", intent="test")
        assert store.list_by_status("implemented") == []

    def test_all_open_convenience(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-OPEN0001", intent="a")
        store.create("WI-OPEN0002", intent="b")
        store.set_status("WI-OPEN0002", "archived", reason="")
        assert len(store.all_open()) == 1


# ---------------------------------------------------------------------------
# WorkItemStore — lifecycle transitions
# ---------------------------------------------------------------------------


class TestWorkItemStoreTransitions:
    def test_set_status_open_to_archived(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-ARCH0001", intent="defer this")
        wi = store.set_status("WI-ARCH0001", "archived", reason="not needed")
        assert wi.status == "archived"
        assert wi.closed_reason == "not needed"
        assert wi.closed_at != ""

    def test_set_status_open_to_rejected(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-REJE0001", intent="bad idea")
        wi = store.set_status("WI-REJE0001", "rejected", reason="out of scope")
        assert wi.status == "rejected"

    def test_set_status_archived_to_open(self, tmp_path: Path) -> None:
        """archived → open is the only allowed reverse transition."""
        store = _store(tmp_path)
        store.create("WI-REOPEN01", intent="re-open me")
        store.set_status("WI-REOPEN01", "archived")
        wi = store.set_status("WI-REOPEN01", "open")
        assert wi.status == "open"

    def test_set_status_invalid_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-BADINV01", intent="test")
        with pytest.raises(WorkItemError, match="Cannot transition"):
            store.set_status("WI-BADINV01", "promoted")  # open → promoted is not allowed

    def test_set_status_unknown_status_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-BADST001", intent="test")
        with pytest.raises(WorkItemError, match="Unknown status"):
            store.set_status("WI-BADST001", "flying")

    def test_set_status_not_found_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        with pytest.raises(WorkItemError, match="not found"):
            store.set_status("WI-NOTHERE", "archived")

    def test_set_status_terminal_cannot_re_transition(self, tmp_path: Path) -> None:
        """Once rejected, no further transitions (unless force=True)."""
        store = _store(tmp_path)
        store.create("WI-TERM0001", intent="test")
        store.set_status("WI-TERM0001", "rejected")
        with pytest.raises(WorkItemError):
            store.set_status("WI-TERM0001", "archived")

    def test_set_status_force_bypasses_guard(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-FORCE001", intent="test")
        store.set_status("WI-FORCE001", "rejected")
        wi = store.set_status("WI-FORCE001", "open", force=True)
        assert wi.status == "open"


# ---------------------------------------------------------------------------
# WorkItemStore — mark_implemented
# ---------------------------------------------------------------------------


class TestMarkImplemented:
    def test_open_becomes_implemented(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-IMPL0001", intent="implement me")
        wi = store.mark_implemented("WI-IMPL0001")
        assert wi is not None
        assert wi.status == "implemented"
        assert wi.verified is True

    def test_mark_implemented_is_noop_when_already_advanced(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-IMPL0002", intent="already done")
        store.set_status("WI-IMPL0002", "archived")
        wi = store.mark_implemented("WI-IMPL0002")
        assert wi is not None
        assert wi.status == "archived"  # unchanged

    def test_mark_implemented_returns_none_for_missing(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        assert store.mark_implemented("WI-NOTHERE") is None

    def test_mark_implemented_persists(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-IMPLPERS", intent="persist me")
        store.mark_implemented("WI-IMPLPERS")
        wi = _store(tmp_path).get("WI-IMPLPERS")
        assert wi is not None
        assert wi.status == "implemented"
        assert wi.verified is True


# ---------------------------------------------------------------------------
# WorkItemStore — promote_to_req
# ---------------------------------------------------------------------------


class TestPromoteToReq:
    def test_open_can_be_promoted(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-PROM0001", intent="new behaviour")
        wi = store.promote_to_req("WI-PROM0001", "REQ-400")
        assert wi.status == "promoted"
        assert wi.promoted_to_req == "REQ-400"
        assert wi.closed_at != ""

    def test_implemented_can_be_promoted(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-PROM0002", intent="promote after impl")
        store.mark_implemented("WI-PROM0002")
        wi = store.promote_to_req("WI-PROM0002", "REQ-401")
        assert wi.status == "promoted"
        assert wi.promoted_to_req == "REQ-401"

    def test_promote_is_idempotent(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-PROM0003", intent="already promoted")
        store.promote_to_req("WI-PROM0003", "REQ-402")
        wi = store.promote_to_req("WI-PROM0003", "REQ-403")  # second call
        assert wi.promoted_to_req == "REQ-402"  # first one wins

    def test_promote_closed_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-PROM0004", intent="already closed")
        store.mark_implemented("WI-PROM0004")
        store.set_status("WI-PROM0004", "closed")
        with pytest.raises(WorkItemError, match="terminal state"):
            store.promote_to_req("WI-PROM0004", "REQ-500")

    def test_promote_not_found_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        with pytest.raises(WorkItemError, match="not found"):
            store.promote_to_req("WI-NOTHERE", "REQ-999")


# ---------------------------------------------------------------------------
# WorkItemStore — tag
# ---------------------------------------------------------------------------


class TestTag:
    def test_tag_valid_kinds(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-TAGTEST1", intent="tag me")
        for kind in WI_KINDS:
            wi = store.tag("WI-TAGTEST1", kind)
            assert wi.kind == kind

    def test_tag_unknown_kind_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-TAGBAD01", intent="bad kind")
        with pytest.raises(WorkItemError, match="Unknown kind"):
            store.tag("WI-TAGBAD01", "nonsense")

    def test_tag_not_found_raises(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        with pytest.raises(WorkItemError, match="not found"):
            store.tag("WI-NOTHERE", "bug")

    def test_tag_persists(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-TAGPERS1", intent="persist kind")
        store.tag("WI-TAGPERS1", "chore")
        wi = _store(tmp_path).get("WI-TAGPERS1")
        assert wi is not None
        assert wi.kind == "chore"


# ---------------------------------------------------------------------------
# WorkItemStore — import_from_ledger
# ---------------------------------------------------------------------------


class TestImportFromLedger:
    def test_import_missing_file_returns_zero(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        assert store.import_from_ledger(tmp_path / "NOFILE.md") == 0

    def test_import_empty_file_returns_zero(self, tmp_path: Path) -> None:
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("# No work proposals here\n", encoding="utf-8")
        store = _store(tmp_path)
        assert store.import_from_ledger(ledger) == 0

    def test_import_creates_new_wis(self, tmp_path: Path) -> None:
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text(
            "work_proposal WI-AABB1122: add retry logic to exporter\n"
            "work_proposal WI-CCDD3344: fix login regression\n",
            encoding="utf-8",
        )
        store = _store(tmp_path)
        imported = store.import_from_ledger(ledger)
        assert imported == 2
        wi1 = store.get("WI-AABB1122")
        assert wi1 is not None
        assert "retry" in wi1.intent

    def test_import_is_idempotent(self, tmp_path: Path) -> None:
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("work_proposal WI-ABCD1234: some intent\n", encoding="utf-8")
        store = _store(tmp_path)
        assert store.import_from_ledger(ledger) == 1
        assert store.import_from_ledger(ledger) == 0  # already exists

    def test_import_case_insensitive_match(self, tmp_path: Path) -> None:
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("Work_Proposal wi-CAFEBABE: lowercase variant\n", encoding="utf-8")
        store = _store(tmp_path)
        imported = store.import_from_ledger(ledger)
        assert imported == 1
        assert store.get("WI-CAFEBABE") is not None


# ---------------------------------------------------------------------------
# CLI — specsmith wi list
# ---------------------------------------------------------------------------


class TestCLIWiList:
    def test_list_empty(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "list", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "No work items" in result.output

    def test_list_shows_items(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-LIST0001", intent="show me")
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "list", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "WI-LIST0001" in result.output

    def test_list_filtered_by_status(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-FILT0001", intent="open")
        store.create("WI-FILT0002", intent="archived one")
        store.set_status("WI-FILT0002", "archived")
        runner = CliRunner()
        result = runner.invoke(
            main, ["wi", "list", "--project-dir", str(tmp_path), "--status", "open"]
        )
        assert result.exit_code == 0
        assert "WI-FILT0001" in result.output
        assert "WI-FILT0002" not in result.output

    def test_list_json_output(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-JSON0001", intent="json test")
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "list", "--project-dir", str(tmp_path), "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert data[0]["id"] == "WI-JSON0001"


# ---------------------------------------------------------------------------
# CLI — specsmith wi show
# ---------------------------------------------------------------------------


class TestCLIWiShow:
    def test_show_found(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-SHOW0001", intent="show details")
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "show", "WI-SHOW0001", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "WI-SHOW0001" in result.output
        assert "show details" in result.output

    def test_show_not_found_exits_1(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "show", "WI-NOTHERE", "--project-dir", str(tmp_path)])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_show_json(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-SHOWJ01", intent="json show")
        runner = CliRunner()
        result = runner.invoke(
            main, ["wi", "show", "WI-SHOWJ01", "--project-dir", str(tmp_path), "--json"]
        )
        assert result.exit_code == 0
        d = json.loads(result.output)
        assert d["id"] == "WI-SHOWJ01"
        assert d["status"] == "open"


# ---------------------------------------------------------------------------
# CLI — specsmith wi close
# ---------------------------------------------------------------------------


class TestCLIWiClose:
    def test_close_open_wi(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-CLOS0001", intent="close me")
        store.mark_implemented("WI-CLOS0001")
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "close", "WI-CLOS0001", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "closed" in result.output
        wi = store.get("WI-CLOS0001")
        assert wi is not None
        assert wi.status == "closed"

    def test_close_with_reason(self, tmp_path: Path) -> None:
        store = _store(tmp_path)
        store.create("WI-CLOS0002", intent="reason test")
        store.mark_implemented("WI-CLOS0002")
        runner = CliRunner()
        runner.invoke(
            main,
            [
                "wi",
                "close",
                "WI-CLOS0002",
                "--reason",
                "covered by REQ-042",
                "--project-dir",
                str(tmp_path),
            ],
        )
        wi = store.get("WI-CLOS0002")
        assert wi is not None
        assert wi.closed_reason == "covered by REQ-042"

    def test_close_invalid_transition_exits_1(self, tmp_path: Path) -> None:
        """open → closed is not a valid transition (must go via implemented first)."""
        _store(tmp_path).create("WI-CLOS0003", intent="bad close")
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "close", "WI-CLOS0003", "--project-dir", str(tmp_path)])
        assert result.exit_code == 1


# ---------------------------------------------------------------------------
# CLI — specsmith wi archive
# ---------------------------------------------------------------------------


class TestCLIWiArchive:
    def test_archive_open_wi(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-ARCH0001", intent="archive me")
        runner = CliRunner()
        result = runner.invoke(
            main, ["wi", "archive", "WI-ARCH0001", "--project-dir", str(tmp_path)]
        )
        assert result.exit_code == 0
        assert "archived" in result.output
        wi = _store(tmp_path).get("WI-ARCH0001")
        assert wi is not None
        assert wi.status == "archived"

    def test_archive_with_reason(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-ARCH0002", intent="reason archive")
        runner = CliRunner()
        runner.invoke(
            main,
            [
                "wi",
                "archive",
                "WI-ARCH0002",
                "--reason",
                "deferred to Q3",
                "--project-dir",
                str(tmp_path),
            ],
        )
        wi = _store(tmp_path).get("WI-ARCH0002")
        assert wi is not None
        assert wi.closed_reason == "deferred to Q3"


# ---------------------------------------------------------------------------
# CLI — specsmith wi promote
# ---------------------------------------------------------------------------


class TestCLIWiPromote:
    def test_promote_creates_req_entry(self, tmp_path: Path) -> None:
        """wi promote appends a REQ-NNN entry to docs/requirements/overflow.yml."""
        _store(tmp_path).create("WI-PROM0001", intent="new retry behaviour")
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True, exist_ok=True)

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "wi",
                "promote",
                "WI-PROM0001",
                "--title",
                "System must retry on HTTP 503",
                "--domain",
                "overflow",
                "--project-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        yaml_text = (req_dir / "overflow.yml").read_text(encoding="utf-8")
        assert "System must retry on HTTP 503" in yaml_text
        assert "REQ-" in yaml_text
        assert "WI-PROM0001" in yaml_text

    def test_promote_updates_wi_record(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-PROM0002", intent="new feature")
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True, exist_ok=True)
        runner = CliRunner()
        runner.invoke(
            main,
            [
                "wi",
                "promote",
                "WI-PROM0002",
                "--title",
                "Feature title",
                "--project-dir",
                str(tmp_path),
            ],
        )
        wi = _store(tmp_path).get("WI-PROM0002")
        assert wi is not None
        assert wi.status == "promoted"
        assert wi.promoted_to_req.startswith("REQ-")

    def test_promote_json_output(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-PROM0003", intent="json promote")
        (tmp_path / "docs" / "requirements").mkdir(parents=True, exist_ok=True)
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "wi",
                "promote",
                "WI-PROM0003",
                "--title",
                "JSON req",
                "--json",
                "--project-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0
        d = json.loads(result.output)
        assert d["wi_id"] == "WI-PROM0003"
        assert d["promoted_to"].startswith("REQ-")

    def test_promote_not_found_exits_1(self, tmp_path: Path) -> None:
        (tmp_path / "docs" / "requirements").mkdir(parents=True, exist_ok=True)
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["wi", "promote", "WI-NOTHERE", "--project-dir", str(tmp_path)],
        )
        assert result.exit_code == 1

    def test_promote_uses_next_req_id(self, tmp_path: Path) -> None:
        """Next REQ-NNN follows the highest existing ID."""
        req_dir = tmp_path / "docs" / "requirements"
        req_dir.mkdir(parents=True, exist_ok=True)
        (req_dir / "existing.yml").write_text(
            "- id: REQ-199\n  title: existing\n  status: implemented\n",
            encoding="utf-8",
        )
        _store(tmp_path).create("WI-NEXTID01", intent="next req id")
        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "wi",
                "promote",
                "WI-NEXTID01",
                "--title",
                "Next after 199",
                "--json",
                "--project-dir",
                str(tmp_path),
            ],
        )
        d = json.loads(result.output)
        assert d["promoted_to"] == "REQ-200"


# ---------------------------------------------------------------------------
# CLI — specsmith wi tag
# ---------------------------------------------------------------------------


class TestCLIWiTag:
    def test_tag_updates_kind(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-TAGCLI01", intent="tag via cli")
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["wi", "tag", "WI-TAGCLI01", "--kind", "bug", "--project-dir", str(tmp_path)],
        )
        assert result.exit_code == 0
        wi = _store(tmp_path).get("WI-TAGCLI01")
        assert wi is not None
        assert wi.kind == "bug"

    def test_tag_invalid_kind_exits_nonzero(self, tmp_path: Path) -> None:
        _store(tmp_path).create("WI-TAGBAD01", intent="bad kind cli")
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["wi", "tag", "WI-TAGBAD01", "--kind", "unknown_kind", "--project-dir", str(tmp_path)],
        )
        assert result.exit_code != 0


# ---------------------------------------------------------------------------
# CLI — specsmith wi import
# ---------------------------------------------------------------------------


class TestCLIWiImport:
    def test_import_from_ledger(self, tmp_path: Path) -> None:
        # WI IDs must be 8 valid hex chars (A-F0-9 only)
        ledger = tmp_path / "LEDGER.md"
        ledger.write_text("work_proposal WI-ABCE1234: do something\n", encoding="utf-8")
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "import", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "Imported 1" in result.output or "1 work item" in result.output

    def test_import_no_ledger_shows_nothing(self, tmp_path: Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["wi", "import", "--project-dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "No new work items" in result.output


# ---------------------------------------------------------------------------
# Preflight wiring — WI created on accepted preflight
# ---------------------------------------------------------------------------


def _seed_requirements(tmp_path: Path, content: str = "") -> None:
    """Write a minimal requirements file so preflight scope-matching works."""
    req_dir = tmp_path / ".specsmith"
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "requirements.json").write_text(
        '[{"id": "REQ-001", "title": "retry logic", "description": "'
        + (content or "system must retry on transient errors")
        + '", "status": "implemented"}]',
        encoding="utf-8",
    )


class TestPreflightWiring:
    def test_accepted_preflight_creates_wi(self, tmp_path: Path) -> None:
        """read-only asks are always accepted regardless of project state."""
        from specsmith.governance_logic import run_preflight

        # READ_ONLY_ASK is always decision=accepted; good for checking WI wiring
        result = run_preflight("what does the retry module do?", project_dir=str(tmp_path))
        assert result["decision"] == "accepted"
        wi_id = result["work_item_id"]
        assert wi_id.startswith("WI-")

        wi = WorkItemStore(tmp_path).get(wi_id)
        assert wi is not None
        assert wi.status == "open"
        assert "retry" in wi.intent.lower()

    def test_change_accepted_when_req_matched_creates_wi(self, tmp_path: Path) -> None:
        """A CHANGE whose utterance contains an explicit REQ-ID gets accepted."""
        from specsmith.governance_logic import run_preflight

        _seed_requirements(tmp_path, "system must retry on transient errors")
        # Embedding the REQ-ID in the utterance triggers the explicit-ID path
        result = run_preflight(
            "add retry logic for REQ-001",
            project_dir=str(tmp_path),
        )
        assert result["decision"] == "accepted"
        wi_id = result["work_item_id"]
        assert wi_id.startswith("WI-")
        wi = WorkItemStore(tmp_path).get(wi_id)
        assert wi is not None
        assert wi.status == "open"

    def test_needs_clarification_destructive_creates_wi(self, tmp_path: Path) -> None:
        """REQ-431: DESTRUCTIVE needs_clarification now allocates a WI so the user
        can pass --work-item to approve/preflight on retry."""
        from specsmith.governance_logic import run_preflight

        result = run_preflight("delete all the files", project_dir=str(tmp_path))
        assert result["decision"] == "needs_clarification"
        # REQ-431: WI IS now minted for DESTRUCTIVE intents on needs_clarification
        assert result["work_item_id"].startswith("WI-")
        wi = WorkItemStore(tmp_path).get(result["work_item_id"])
        assert wi is not None
        assert wi.status == "open"

    def test_needs_clarification_scope_creep_does_not_create_wi(self, tmp_path: Path) -> None:
        """Non-DESTRUCTIVE/non-RELEASE needs_clarification still produces no WI."""
        from specsmith.governance_logic import run_preflight

        # Ambiguous scope-creep CHANGE with no seed requirements → needs_clarification
        # but NOT a DESTRUCTIVE/RELEASE intent, so no WI is minted.
        result = run_preflight("refactor everything", project_dir=str(tmp_path))
        # Intent is CHANGE; empty scope → needs_clarification; no WI allocated
        if result["decision"] == "needs_clarification":
            assert result["work_item_id"] == ""
            assert WorkItemStore(tmp_path).load() == []

    def test_preflight_wi_carries_confidence_target(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight

        # read-only ask is always accepted
        result = run_preflight("what is the architecture?", project_dir=str(tmp_path))
        wi_id = result["work_item_id"]
        assert wi_id, "read-only ask must produce a WI"
        wi = WorkItemStore(tmp_path).get(wi_id)
        assert wi is not None
        assert wi.confidence_target == result["confidence_target"]

    def test_preflight_wiring_never_blocks_result(self, tmp_path: Path) -> None:
        """Even if workitems.json can't be written, preflight must not crash."""
        from specsmith.governance_logic import run_preflight

        # Make .specsmith a file so mkdir fails inside WorkItemStore
        fake = tmp_path / ".specsmith"
        fake.write_text("not a directory", encoding="utf-8")
        result = run_preflight("what does the system do?", project_dir=str(tmp_path))
        # Preflight still returns a valid result even when WI persistence fails
        assert "decision" in result


# ---------------------------------------------------------------------------
# Verify wiring — WI auto-transitions to implemented on equilibrium
# ---------------------------------------------------------------------------


class TestVerifyWiring:
    def test_equilibrium_marks_wi_implemented(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight, run_verify

        # read-only ask → always accepted → creates WI
        pre = run_preflight("what does the retry module do?", project_dir=str(tmp_path))
        wi_id = pre["work_item_id"]
        assert wi_id

        run_verify(
            diff="--- a/src/retry.py\n+++ b/src/retry.py\n@@ -1 +1 @@\n+retry logic\n",
            files_changed=["src/retry.py"],
            test_results={"passed": 5, "failed": 0},
            project_dir=str(tmp_path),
            work_item_id=wi_id,
        )

        wi = WorkItemStore(tmp_path).get(wi_id)
        assert wi is not None
        assert wi.status == "implemented"
        assert wi.verified is True

    def test_no_equilibrium_does_not_change_wi(self, tmp_path: Path) -> None:
        from specsmith.governance_logic import run_preflight, run_verify

        # read-only ask → always accepted → creates WI
        pre = run_preflight("what is the test status?", project_dir=str(tmp_path))
        wi_id = pre["work_item_id"]
        assert wi_id

        run_verify(
            diff="",
            files_changed=[],
            test_results={"passed": 0, "failed": 3},
            project_dir=str(tmp_path),
            work_item_id=wi_id,
        )

        wi = WorkItemStore(tmp_path).get(wi_id)
        assert wi is not None
        assert wi.status == "open"  # still open; no equilibrium (failed tests)

    def test_verify_wiring_never_blocks_result(self, tmp_path: Path) -> None:
        """Even if WorkItemStore.mark_implemented fails, verify must return normally."""
        from specsmith.governance_logic import run_verify

        # Pass a WI ID that doesn't exist — store.mark_implemented returns None silently
        result = run_verify(
            diff="--- a\n+++ b\n@@ -1 +1 @@\n+change",
            files_changed=["a.py"],
            test_results={"passed": 1, "failed": 0},
            project_dir=str(tmp_path),
            work_item_id="WI-NOTEXIST",
        )
        assert "equilibrium" in result


# ---------------------------------------------------------------------------
# Constants integrity
# ---------------------------------------------------------------------------


class TestConstantsIntegrity:
    def test_all_states_have_transitions_entry(self) -> None:
        for state in WI_STATES:
            assert state in WI_TRANSITIONS, f"WI_TRANSITIONS missing entry for {state!r}"

    def test_terminal_states_have_empty_transitions(self) -> None:
        # archived is special: terminal-ish but supports reopen (archived → open).
        # All other terminal states must have zero outgoing transitions.
        truly_terminal = WI_TERMINAL_STATES - {"archived"}
        for state in truly_terminal:
            assert WI_TRANSITIONS[state] == frozenset(), (
                f"Terminal state {state!r} should have no outgoing transitions"
            )
        # archived specifically allows only the reopen path
        assert WI_TRANSITIONS["archived"] == frozenset({"open"}), (
            "archived must allow exactly one transition: archived → open"
        )

    def test_wi_kinds_non_empty(self) -> None:
        assert len(WI_KINDS) >= 6

    def test_wi_states_non_empty(self) -> None:
        assert len(WI_STATES) >= 6
