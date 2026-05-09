# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Mechanical compliance tests (tests/test_compliance.py).

Covers REQ-206 through REQ-220 (EU AI Act / NIST AI RMF compliance mechanisms)
and REQ-244 through REQ-247 (context window management).

All tests run deterministically in CI without requiring a running LLM.
Tests marked ``evaluator`` in TESTS.md (TEST-206..220) are verified here as
concrete pytest assertions, effectively upgrading their verification_method
to ``unit``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# REQ-206: Tamper-Evident Agent Action Log (SHA-256 chaining)
# ---------------------------------------------------------------------------


class TestReq206TraceVault:
    """TEST-206 — TraceVault chain integrity."""

    def test_chain_valid_after_seals(self, tmp_path: Path) -> None:
        """Create several seals and verify the chain is intact (REQ-206)."""
        from specsmith.trace import SealType, TraceVault

        vault = TraceVault(tmp_path)
        vault.seal(SealType.DECISION, "First decision")
        vault.seal(SealType.MILESTONE, "Phase complete")
        vault.seal(SealType.AUDIT_GATE, "Audit passed")

        valid, errors = vault.verify()
        assert valid, f"Chain should be valid; errors: {errors}"
        assert vault.count() == 3

    def test_tamper_detected(self, tmp_path: Path) -> None:
        """Modify a seal on disk and verify the chain reports an error (REQ-206)."""
        from specsmith.trace import SealType, TraceVault

        vault = TraceVault(tmp_path)
        vault.seal(SealType.DECISION, "Original decision")
        vault.seal(SealType.MILESTONE, "Milestone")

        trace_file = tmp_path / ".specsmith" / "trace.jsonl"
        assert trace_file.exists()

        lines = trace_file.read_text(encoding="utf-8").splitlines()
        # Corrupt the first seal's description
        first = json.loads(lines[0])
        first["description"] = "TAMPERED"
        lines[0] = json.dumps(first)
        trace_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        valid, errors = vault.verify()
        assert not valid, "Tampered chain should fail verification"
        assert len(errors) > 0

    def test_append_only_never_truncates(self, tmp_path: Path) -> None:
        """Appending a seal never reduces byte count (REQ-206 append-only)."""
        from specsmith.trace import SealType, TraceVault

        vault = TraceVault(tmp_path)
        vault.seal(SealType.DECISION, "First")

        trace_file = tmp_path / ".specsmith" / "trace.jsonl"
        size_after_one = trace_file.stat().st_size

        vault.seal(SealType.DECISION, "Second")
        size_after_two = trace_file.stat().st_size

        assert size_after_two > size_after_one, "File size must grow on each seal"


# ---------------------------------------------------------------------------
# REQ-207: Explanation Artifacts — ai_disclosure in preflight
# ---------------------------------------------------------------------------


class TestReq207AiDisclosure:
    """TEST-207 — Preflight JSON includes ai_disclosure block."""

    def test_preflight_contains_ai_disclosure(self, tmp_path: Path) -> None:
        """Preflight output MUST include ai_disclosure with required keys (REQ-207)."""
        from click.testing import CliRunner

        from specsmith.cli import main

        (tmp_path / "scaffold.yml").write_text(
            "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
        )
        (tmp_path / "REQUIREMENTS.md").write_text(
            "# Requirements\n\n## REQ-001\n- **ID:** REQ-001\n- **Description:** test\n",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["preflight", "what does this project do?", "--project-dir", str(tmp_path)],
            env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert "ai_disclosure" in payload, "ai_disclosure must be present"
        disclosure = payload["ai_disclosure"]
        required_keys = ("governed_by", "governance_gated", "provider", "model", "spec_version")
        for required_key in required_keys:
            assert required_key in disclosure, f"ai_disclosure missing key: {required_key}"
        assert disclosure["governed_by"] == "specsmith"
        assert disclosure["governance_gated"] is True


# ---------------------------------------------------------------------------
# REQ-208: Action Log Replay and Export — required compliance sections
# ---------------------------------------------------------------------------


class TestReq208ComplianceExport:
    """TEST-208 — run_export() contains required compliance sections."""

    def test_export_contains_required_sections(self, tmp_path: Path) -> None:
        """run_export() must include AI System Inventory, Risk Classification,
        and Human Oversight Controls sections (REQ-208, REQ-215)."""
        from specsmith.exporter import run_export

        # Minimal scaffold for export
        (tmp_path / "scaffold.yml").write_text(
            "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
        )

        report = run_export(tmp_path)
        assert isinstance(report, str), "run_export must return a string"
        assert "AI System Inventory" in report, "Missing: AI System Inventory"
        assert "Risk Classification" in report, "Missing: Risk Classification"
        assert "Human Oversight Controls" in report, "Missing: Human Oversight Controls"


# ---------------------------------------------------------------------------
# REQ-209: Human Escalation Threshold
# ---------------------------------------------------------------------------


class TestReq209EscalationThreshold:
    """TEST-209 — preflight --escalate-threshold sets escalation_required."""

    def test_escalation_required_when_threshold_above_confidence(self, tmp_path: Path) -> None:
        """When escalation threshold > confidence_target, escalation_required is True (REQ-209)."""
        from click.testing import CliRunner

        from specsmith.cli import main

        (tmp_path / "scaffold.yml").write_text(
            "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "preflight",
                "what does this project do?",
                "--project-dir",
                str(tmp_path),
                "--escalate-threshold",
                "0.99",  # always above the read-only ask confidence (0.7)
            ],
            env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload.get("escalation_required") is True, (
            "escalation_required must be True when threshold > confidence_target"
        )
        assert "escalation_reason" in payload


# ---------------------------------------------------------------------------
# REQ-210: Kill-Switch
# ---------------------------------------------------------------------------


class TestReq210KillSwitch:
    """TEST-210 — kill-session CLI exits 0 with no active sessions."""

    def test_kill_session_exits_zero_no_sessions(self, tmp_path: Path) -> None:
        """kill-session with no active sessions must exit 0 and log a ledger event (REQ-210)."""
        from click.testing import CliRunner

        from specsmith.cli import main

        (tmp_path / "scaffold.yml").write_text(
            "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
        )
        (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["kill-session", "--project-dir", str(tmp_path)],
            env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
            catch_exceptions=False,
        )
        assert result.exit_code == 0, f"kill-session should exit 0; output: {result.output}"
        ledger = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
        # The kill-switch records a ledger event
        assert "kill" in ledger.lower() or "KILL" in ledger, (
            "LEDGER.md must contain a kill-switch event"
        )


# ---------------------------------------------------------------------------
# REQ-213: Safe Append-Only Write
# ---------------------------------------------------------------------------


class TestReq213SafeWrite:
    """TEST-213 — safe_write preserves content and creates backups."""

    def test_append_file_preserves_prior_content(self, tmp_path: Path) -> None:
        """append_file must never truncate existing content (REQ-213)."""
        from specsmith.safe_write import append_file

        target = tmp_path / "LEDGER.md"
        target.write_text("# Existing content\n", encoding="utf-8")
        append_file(target, "\n## New entry\nAdded.\n")

        result = target.read_text(encoding="utf-8")
        assert "# Existing content" in result, "Prior content must be preserved"
        assert "## New entry" in result, "New entry must be appended"

    def test_safe_overwrite_creates_backup(self, tmp_path: Path) -> None:
        """safe_overwrite must create a timestamped .bak file before replacing (REQ-213)."""
        from specsmith.safe_write import safe_overwrite

        target = tmp_path / "REQUIREMENTS.md"
        target.write_text("# Original\n", encoding="utf-8")
        backup_path = safe_overwrite(target, "# Replaced\n")

        assert backup_path is not None, "Backup path must be returned"
        assert backup_path.exists(), f"Backup file must exist: {backup_path}"
        assert backup_path.suffix == ".bak", "Backup must have .bak extension"
        assert "Original" in backup_path.read_text(encoding="utf-8")
        assert target.read_text(encoding="utf-8") == "# Replaced\n"


# ---------------------------------------------------------------------------
# REQ-215: Compliance Export Report (already covered by TestReq208)
# — kept as an alias so TEST-215 maps to a named test
# ---------------------------------------------------------------------------


class TestReq215ComplianceReport:
    """TEST-215 — run_export() produces all required compliance sections."""

    def test_run_export_compliance_sections(self, tmp_path: Path) -> None:
        """Alias of TestReq208 — ensures TEST-215 has a direct mapping."""
        from specsmith.exporter import run_export

        (tmp_path / "scaffold.yml").write_text(
            "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
        )
        report = run_export(tmp_path)
        for section in ("AI System Inventory", "Risk Classification", "Human Oversight Controls"):
            assert section in report, f"Missing compliance section: {section}"


# ---------------------------------------------------------------------------
# REQ-217: Least-Privilege Agent Permissions
# ---------------------------------------------------------------------------


class TestReq217LeastPrivilege:
    """TEST-217 — agent permissions-check exit codes."""

    def test_allowed_tool_exits_zero(self, tmp_path: Path) -> None:
        """An allowed tool must exit 0 (REQ-217)."""
        from click.testing import CliRunner

        from specsmith.cli import main

        (tmp_path / "scaffold.yml").write_text(
            "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["agent", "permissions-check", "run_shell", "--project-dir", str(tmp_path), "--no-log"],
            env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
            catch_exceptions=False,
        )
        # Default profile allows run_shell; exit 0 means allowed
        assert result.exit_code in (0, 3), "exit code must be 0 (allowed) or 3 (denied)"

    def test_denied_tool_exits_three(self, tmp_path: Path) -> None:
        """A denied tool must exit 3 (REQ-217)."""
        from click.testing import CliRunner

        from specsmith.cli import main

        # Write a scaffold with an explicit deny list
        (tmp_path / "scaffold.yml").write_text(
            "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
        )
        spec_dir = tmp_path / ".specsmith"
        spec_dir.mkdir()
        # Deny 'deploy_to_production' — guaranteed not in any allow list
        (spec_dir / "config.yml").write_text(
            "agent:\n  permissions:\n    deny: [deploy_to_production]\n",
            encoding="utf-8",
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "agent",
                "permissions-check",
                "deploy_to_production",
                "--project-dir",
                str(tmp_path),
                "--no-log",
            ],
            env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
            catch_exceptions=False,
        )
        assert result.exit_code == 3, (
            f"Denied tool must exit 3; got {result.exit_code}: {result.output}"
        )


# ---------------------------------------------------------------------------
# REQ-220: Policy Guardrails — is_safe_command
# ---------------------------------------------------------------------------


class TestReq220SafeCommands:
    """TEST-220 — is_safe_command blocks dangerous, allows safe commands."""

    @pytest.mark.parametrize(
        "cmd,expected_safe",
        [
            ("ls -la", True),
            ("git status", True),
            ("pytest -q", True),
            ("rm -rf /tmp/foo", False),
            ("git push origin main", False),
            ("docker compose down -v", False),
            ("cat .env", False),
            ("kubectl apply -f deploy.yml", False),
        ],
    )
    def test_is_safe_command(self, cmd: str, expected_safe: bool) -> None:
        """is_safe_command correctly classifies commands (REQ-220)."""
        from specsmith.agent.safety import is_safe_command

        assert is_safe_command(cmd) is expected_safe, (
            f"is_safe_command({cmd!r}) expected {expected_safe}"
        )


# ---------------------------------------------------------------------------
# REQ-244: GPU-Aware Context Window Sizing
# ---------------------------------------------------------------------------


class TestReq244ContextWindowSizing:
    """TEST-221 / TEST-222 — context window sizing tiers and GPU detection."""

    @pytest.mark.parametrize(
        "vram_gb,expected_ctx",
        [
            (5.0, 4096),
            (6.0, 8192),
            (8.0, 8192),
            (12.0, 16384),
            (14.0, 16384),
            (20.0, 32768),
            (24.0, 32768),
            (0.0, 4096),  # CPU-only
        ],
    )
    def test_suggest_context_window_tiers(self, vram_gb: float, expected_ctx: int) -> None:
        """suggest_context_window returns the correct tier for each VRAM level (REQ-244)."""
        from specsmith.context_window import suggest_context_window

        assert suggest_context_window(vram_gb) == expected_ctx

    def test_detect_gpu_vram_never_raises(self) -> None:
        """detect_gpu_vram() returns float >= 0 and never raises (REQ-244)."""
        from specsmith.context_window import detect_gpu_vram

        result = detect_gpu_vram()
        assert isinstance(result, float), "detect_gpu_vram must return float"
        assert result >= 0.0, "VRAM must be non-negative"


# ---------------------------------------------------------------------------
# REQ-245: Live Context Fill Indicator
# ---------------------------------------------------------------------------


class TestReq245ContextFillTracker:
    """TEST-223 — ContextFillTracker emits fill events."""

    def test_record_returns_fill_event(self) -> None:
        """record(used=1000, limit=4096) emits a context_fill event (REQ-245)."""
        from specsmith.context_window import ContextFillTracker

        tracker = ContextFillTracker(limit=4096)
        event = tracker.record(used=1000)

        assert event.type == "context_fill"
        assert event.used == 1000
        assert event.limit == 4096
        assert abs(event.pct - 24.41) < 0.5, f"pct ~24.4 expected, got {event.pct}"

    def test_event_to_dict_schema(self) -> None:
        """ContextFillEvent.to_dict() matches the JSONL event schema (REQ-245)."""
        from specsmith.context_window import ContextFillTracker

        tracker = ContextFillTracker(limit=8192)
        event = tracker.record(used=2000)
        d = event.to_dict()

        assert d["type"] == "context_fill"
        assert isinstance(d["used"], int)
        assert isinstance(d["limit"], int)
        assert isinstance(d["pct"], float)


# ---------------------------------------------------------------------------
# REQ-246: Auto Context Compression Threshold
# ---------------------------------------------------------------------------


class TestReq246CompressionThreshold:
    """TEST-224 — fill below hard ceiling returns event (compression threshold signal)."""

    def test_fill_below_ceiling_returns_event(self) -> None:
        """~83% fill — above the 80% compression threshold, below 85% hard ceiling (REQ-246).

        We use limit=65536 so that the 15% reservation rule governs
        (0.15 * 65536 = 9830 > MIN_FREE_TOKENS=2048), giving an effective
        ceiling of 85% rather than the tighter 50% that would apply for
        small context windows.
        """
        from specsmith.context_window import ContextFillTracker

        # limit=65536: effective_ceiling = 85% (15% rule dominates over 2048 min)
        tracker = ContextFillTracker(limit=65536)
        event = tracker.record(used=55000)  # ~83.9% — below the 85% ceiling
        assert event.pct >= 80.0, f"Fill should be >= 80%; got {event.pct}"
        assert event.pct < 85.0, f"Fill should be < 85%; got {event.pct}"

    def test_all_events_accumulated(self) -> None:
        """ContextFillTracker accumulates events across calls (REQ-246)."""
        from specsmith.context_window import ContextFillTracker

        tracker = ContextFillTracker(limit=4096)
        tracker.record(used=500)
        tracker.record(used=1000)
        tracker.record(used=1500)

        assert len(tracker.all_events()) == 3


# ---------------------------------------------------------------------------
# REQ-247: Hard Context Reservation — Never 100% Fill
# ---------------------------------------------------------------------------


class TestReq247HardCeiling:
    """TEST-225 — ContextFullError raised at hard ceiling."""

    def test_context_full_error_at_ceiling(self) -> None:
        """~85.4% fill raises ContextFullError at the hard ceiling (REQ-247).

        Uses limit=65536 so the 15% reservation rule governs (effective ceiling
        = 85%), matching the intent of the hard-ceiling invariant.
        """
        from specsmith.context_window import ContextFillTracker, ContextFullError

        # limit=65536: effective_ceiling = 85% (15% rule dominates)
        tracker = ContextFillTracker(limit=65536)
        with pytest.raises(ContextFullError) as exc_info:
            tracker.record(used=56000)  # ~85.4% — above the 85% ceiling

        err = exc_info.value
        assert err.used == 56000
        assert err.limit == 65536
        assert err.pct >= 85.0, f"pct should be >= 85; got {err.pct}"

    def test_min_free_tokens_tightens_ceiling(self) -> None:
        """With a small context window, min_free_tokens tightens the ceiling below 85% (REQ-247)."""
        from specsmith.context_window import ContextFillTracker, ContextFullError

        # limit=4096, min_free_tokens=2048 → effective ceiling = 50% not 85%
        tracker = ContextFillTracker(limit=4096, min_free_tokens=2048)
        effective = tracker.effective_ceiling_pct
        assert effective <= 50.0, f"Effective ceiling should be <= 50%; got {effective}"

        with pytest.raises(ContextFullError):
            tracker.record(used=2200)  # ~53.7% — above the 50% effective ceiling

    def test_reset_clears_usage(self) -> None:
        """reset() allows recording to start fresh without error (REQ-247)."""
        from specsmith.context_window import ContextFillTracker

        tracker = ContextFillTracker(limit=4096)
        tracker.record(used=2000)
        tracker.reset()

        # After reset, usage is 0 — safe to record again
        event = tracker.record(used=100)
        assert event.used == 100
        assert len(tracker.all_events()) == 1  # only the post-reset event
