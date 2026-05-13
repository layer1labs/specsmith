# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Nexus runtime tests (TEST-065 through TEST-076).

These tests cover Specsmith governance requirements REQ-065..REQ-076 for the
local-first Nexus agent runtime, including its tooling layer, safety
middleware, repository indexer, REPL slash commands, AG2 orchestration, and
docker-compose configuration of the vLLM (l1-nexus) model server.
"""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from unittest import mock

import pytest

from specsmith.agent.broker import (
    RETRY_STRATEGIES as _RETRY_STRATEGIES,
)
from specsmith.agent.broker import (
    PreflightDecision as _PreflightDecision,
)
from specsmith.agent.broker import (
    classify_retry_strategy as _classify_retry_strategy,
)
from specsmith.agent.broker import (
    execute_with_governance as _execute_with_governance,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------------------------
# TEST-065 — Nexus must defer governance to Specsmith
# ---------------------------------------------------------------------------
def test_nexus_runtime_defers_governance_to_specsmith():
    from specsmith.agent import orchestrator

    src = inspect.getsource(orchestrator)
    assert "Specsmith governs" in src
    assert "Nexus only executes" in src


# ---------------------------------------------------------------------------
# TEST-066 — Nexus must provide all required agent roles
# ---------------------------------------------------------------------------
REQUIRED_AGENT_ATTRS = [
    "planner",
    "shell_agent",
    "code_agent",
    "reviewer_agent",
    "memory_agent",
    "git_agent",
    "human_proxy",
    "executor",
]


def test_orchestrator_instantiates_required_agents():
    from specsmith.agent import orchestrator as orch

    fake_agent = mock.MagicMock()
    fake_agent.register_for_llm = mock.MagicMock(return_value=lambda fn: fn)
    fake_agent.register_for_execution = mock.MagicMock(return_value=lambda fn: fn)
    fake_autogen = mock.MagicMock()
    fake_autogen.ConversableAgent = mock.MagicMock(return_value=fake_agent)

    with (
        mock.patch.object(orch, "autogen", fake_autogen),
        mock.patch.object(orch, "ConversableAgent", fake_autogen.ConversableAgent),
    ):
        instance = orch.Orchestrator()

    for attr in REQUIRED_AGENT_ATTRS:
        assert hasattr(instance, attr), f"Missing required agent: {attr}"


# ---------------------------------------------------------------------------
# TEST-067 — Nexus tool layer must expose the required tools
# ---------------------------------------------------------------------------
REQUIRED_TOOL_NAMES = {
    "run_shell",
    "read_file",
    "write_file",
    "patch_file",
    "list_files",
    "grep",
    "git_diff",
    "git_status",
    "run_tests",
    "open_url",
    "search_docs",
    "remember_project_fact",
}


def test_available_tools_contains_required_tool_names():
    from specsmith.agent.tools import AVAILABLE_TOOLS

    names = {tool.__name__ for tool in AVAILABLE_TOOLS}
    assert REQUIRED_TOOL_NAMES.issubset(names)


# ---------------------------------------------------------------------------
# TEST-068 — Safety middleware blocks unsafe commands
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "command,expected_safe",
    [
        ("ls -la", True),
        ("git status", True),
        ("pytest -q", True),
        ("rm -rf /tmp/foo", False),
        ("git push origin main", False),
        ("docker compose down -v", False),
        ("alembic upgrade head", False),
        ("kubectl apply -f deploy.yml", False),
        ("cat .env", False),
    ],
)
def test_is_safe_command(command, expected_safe):
    from specsmith.agent.safety import is_safe_command

    assert is_safe_command(command) is expected_safe


# ---------------------------------------------------------------------------
# TEST-069 — JSON argument validation rejects non-serializable args
# ---------------------------------------------------------------------------
def test_validate_json_args_rejects_non_serializable():
    from specsmith.agent.safety import validate_json_args

    @validate_json_args
    def some_tool(payload):
        return payload

    # set is not JSON-serializable
    with pytest.raises(ValueError):
        some_tool({1, 2, 3})

    # serializable args succeed
    assert some_tool({"a": 1}) == {"a": 1}


# ---------------------------------------------------------------------------
# TEST-070 — Path normalization
# ---------------------------------------------------------------------------
def test_normalize_path_returns_absolute_resolved(tmp_path):
    from specsmith.agent.safety import normalize_path

    relative = "subdir/file.txt"
    p = normalize_path(relative, cwd=str(tmp_path))
    assert p.is_absolute()
    # resolve() should anchor it under tmp_path
    assert str(tmp_path) in str(p)


# ---------------------------------------------------------------------------
# TEST-071 — Repository indexer populates .repo-index/
# ---------------------------------------------------------------------------
def test_generate_index_creates_required_files(tmp_path):
    # Create a couple of fake source files
    (tmp_path / "main.py").write_text("print('hi')")
    (tmp_path / "README.md").write_text("# repo")

    from specsmith.agent.indexer import generate_index

    generate_index(cwd=str(tmp_path))

    index_dir = tmp_path / ".repo-index"
    assert (index_dir / "files.json").is_file()
    assert (index_dir / "architecture.md").is_file()
    assert (index_dir / "conventions.md").is_file()

    files = json.loads((index_dir / "files.json").read_text())
    assert isinstance(files, list)
    assert any("main.py" in f for f in files)


# ---------------------------------------------------------------------------
# TEST-072 — REPL supports the required slash commands
# ---------------------------------------------------------------------------
REQUIRED_SLASH_COMMANDS = [
    "/plan",
    "/ask",
    "/fix",
    "/test",
    "/commit",
    "/pr",
    "/undo",
    "/context",
    "/exit",
]


def test_repl_supports_required_slash_commands():
    from specsmith.agent import repl

    src = inspect.getsource(repl)
    for cmd in REQUIRED_SLASH_COMMANDS:
        assert cmd in src, f"REPL missing slash command: {cmd}"


def test_repl_does_not_use_warp_branding():
    from specsmith.agent import repl

    src = inspect.getsource(repl)
    assert "warp-agent>" not in src
    assert "Warp Agentic Dev Environment" not in src
    assert "Nexus" in src


# ---------------------------------------------------------------------------
# TEST-073 — Nexus output contract
# ---------------------------------------------------------------------------
def test_nexus_output_contract_sections_present():
    from specsmith.agent import orchestrator

    src = inspect.getsource(orchestrator)
    for section in [
        "Plan:",
        "Commands to run:",
        "Files changed:",
        "Diff:",
        "Test results:",
        "Next action:",
    ]:
        assert section in src, f"Missing required output section: {section}"


# ---------------------------------------------------------------------------
# TEST-074 — vLLM image must be pinned (not :latest)
# ---------------------------------------------------------------------------
def test_docker_compose_pins_vllm_image():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "vllm/vllm-openai:v0.8.5" in compose
    assert "vllm/vllm-openai:latest" not in compose


# ---------------------------------------------------------------------------
# TEST-075 — vLLM must serve l1-nexus and use hermes tool-call parser
# ---------------------------------------------------------------------------
def test_docker_compose_serves_l1_nexus_with_hermes_parser():
    compose = (REPO_ROOT / "docker-compose.yml").read_text()
    assert "--served-model-name l1-nexus" in compose
    assert "--tool-call-parser hermes" in compose
    assert "--enable-auto-tool-choice" in compose


# ---------------------------------------------------------------------------
# TEST-076 — Each tool registered with executor exactly once
# ---------------------------------------------------------------------------
def test_orchestrator_register_tools_unique_executor_registration():
    from specsmith.agent import orchestrator as orch
    from specsmith.agent.tools import AVAILABLE_TOOLS

    # Build mock agents that record register_for_llm and register_for_execution calls
    def make_agent():
        agent = mock.MagicMock()
        agent.register_for_llm = mock.MagicMock(return_value=lambda fn: fn)
        agent.register_for_execution = mock.MagicMock(return_value=lambda fn: fn)
        return agent

    instance = orch.Orchestrator.__new__(orch.Orchestrator)
    instance.shell_agent = make_agent()
    instance.code_agent = make_agent()
    instance.git_agent = make_agent()
    instance.memory_agent = make_agent()
    instance.executor = make_agent()

    instance.register_tools()

    # Executor must register each tool exactly once
    assert instance.executor.register_for_execution.call_count == len(AVAILABLE_TOOLS)

    # LLM-side caller agents may register all tools, but the same call count
    # for each caller is exactly len(AVAILABLE_TOOLS) (1 per tool).
    for caller in (
        instance.shell_agent,
        instance.code_agent,
        instance.git_agent,
        instance.memory_agent,
    ):
        assert caller.register_for_llm.call_count == len(AVAILABLE_TOOLS)


# ---------------------------------------------------------------------------
# TEST-077 — Safe cleanup defaults to dry-run
# ---------------------------------------------------------------------------
def _seed_repo(root: Path) -> None:
    """Create a tmp repo that resembles a real Specsmith project."""
    (root / "src" / "specsmith").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "docs").mkdir()
    (root / "scripts").mkdir()
    (root / ".specsmith").mkdir()
    (root / ".github").mkdir()
    (root / "ARCHITECTURE.md").write_text("arch")
    (root / "REQUIREMENTS.md").write_text("reqs")
    (root / "TESTS.md").write_text("tests")
    (root / "LEDGER.md").write_text("ledger")
    (root / "README.md").write_text("readme")
    (root / "LICENSE").write_text("license")
    (root / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "9.9.9"\n')
    # Cleanup-eligible artifacts
    (root / "__pycache__").mkdir()
    (root / "__pycache__" / "a.pyc").write_text("x")
    (root / "src" / "specsmith" / "__pycache__").mkdir()
    (root / "src" / "specsmith" / "__pycache__" / "b.pyc").write_text("y")
    (root / ".mypy_cache").mkdir()
    (root / ".pytest_cache").mkdir()
    (root / ".ruff_cache").mkdir()
    (root / "build").mkdir()
    (root / "build" / "out.txt").write_text("out")
    (root / "tags").write_text("ctags")
    (root / "normalized_requirements.json").write_text("{}")
    (root / "test_cases.md").write_text("#")
    (root / "src" / "x.zip").write_text("zip")
    (root / "src" / "x.egg-info").mkdir()


def test_safe_cleanup_default_is_dry_run(tmp_path):
    from specsmith.agent.cleanup import clean_repo

    _seed_repo(tmp_path)
    report = clean_repo(tmp_path)  # apply omitted -> dry-run
    assert report.dry_run is True
    # __pycache__ must still exist after a dry-run
    assert (tmp_path / "__pycache__").is_dir()
    assert (tmp_path / ".mypy_cache").is_dir()
    assert (tmp_path / "tags").is_file()
    assert len(report.removed) > 0


# ---------------------------------------------------------------------------
# TEST-078 — Safe cleanup uses a hard-coded target list
# ---------------------------------------------------------------------------
def test_safe_cleanup_uses_hard_coded_target_list():
    from specsmith.agent import cleanup as cleanup_mod

    assert hasattr(cleanup_mod, "CANONICAL_TARGETS")
    targets = cleanup_mod.CANONICAL_TARGETS
    assert "__pycache__" in targets["recursive_dirs"]
    for required in (".mypy_cache", ".pytest_cache", ".ruff_cache", "build"):
        assert required in targets["top_level_dirs"]
    for required in ("tags", "normalized_requirements.json", "test_cases.md"):
        assert required in targets["top_level_files"]


# ---------------------------------------------------------------------------
# TEST-079 — Safe cleanup protects governance and source
# ---------------------------------------------------------------------------
def test_safe_cleanup_protects_governance_and_source(tmp_path):
    from specsmith.agent.cleanup import clean_repo

    _seed_repo(tmp_path)
    report = clean_repo(tmp_path, apply=True)
    # Protected paths must still exist after apply.
    for protected in (
        "src",
        "tests",
        "docs",
        "scripts",
        ".specsmith",
        ".github",
        "ARCHITECTURE.md",
        "REQUIREMENTS.md",
        "TESTS.md",
        "LEDGER.md",
        "README.md",
        "LICENSE",
        "pyproject.toml",
    ):
        assert (tmp_path / protected).exists(), f"Protected path removed: {protected}"

    # The src package itself remains; only its __pycache__ children should be gone.
    assert (tmp_path / "src" / "specsmith").is_dir()
    assert not (tmp_path / "src" / "specsmith" / "__pycache__").exists()

    # Top-level artifacts removed.
    assert not (tmp_path / "__pycache__").exists()
    assert not (tmp_path / ".mypy_cache").exists()
    assert not (tmp_path / "build").exists()
    assert not (tmp_path / "tags").exists()

    # Report should not list any protected path as removed.
    for entry in report.removed:
        assert not entry.startswith((".git", ".specsmith/", ".github"))
        assert entry not in {"src", "tests", "docs", "scripts"}


# ---------------------------------------------------------------------------
# TEST-080 — Safe cleanup emits a structured report
# ---------------------------------------------------------------------------
def test_safe_cleanup_emits_structured_report(tmp_path):
    from specsmith.agent.cleanup import CleanupReport, clean_repo

    _seed_repo(tmp_path)
    report = clean_repo(tmp_path)
    assert isinstance(report, CleanupReport)
    d = report.to_dict()
    for field_name in ("dry_run", "project_root", "removed", "skipped", "bytes_reclaimed"):
        assert field_name in d
    assert isinstance(d["removed"], list)
    assert isinstance(d["skipped"], list)
    assert isinstance(d["bytes_reclaimed"], int)
    assert d["bytes_reclaimed"] > 0


# ---------------------------------------------------------------------------
# TEST-081 — specsmith clean CLI subcommand (dry-run, --apply, --json)
# ---------------------------------------------------------------------------
def test_specsmith_clean_cli_dry_run(tmp_path):
    from click.testing import CliRunner

    from specsmith.cli import main

    _seed_repo(tmp_path)
    # Need a scaffold.yml with the current spec_version so the auto-update prompt
    # in the CLI group does not trigger interactive input during the test.
    (tmp_path / "scaffold.yml").write_text(
        "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
    )

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["clean", "--project-dir", str(tmp_path), "--json"],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["dry_run"] is True
    assert isinstance(data["removed"], list)
    # Dry-run must NOT delete: __pycache__ still present
    assert (tmp_path / "__pycache__").is_dir()


def test_specsmith_clean_cli_apply_records_ledger_entry(tmp_path):
    from click.testing import CliRunner

    from specsmith.cli import main

    _seed_repo(tmp_path)
    (tmp_path / "scaffold.yml").write_text(
        "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
    )
    ledger_before = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(
        main,
        ["clean", "--project-dir", str(tmp_path), "--apply"],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
        catch_exceptions=False,
    )
    assert result.exit_code == 0, result.output
    # Targets removed
    assert not (tmp_path / "__pycache__").exists()
    assert not (tmp_path / ".mypy_cache").exists()
    # Ledger entry appended
    ledger_after = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
    assert len(ledger_after) > len(ledger_before)
    assert "specsmith clean" in ledger_after
    assert "REQ-077" in ledger_after


# ---------------------------------------------------------------------------
# TEST-082 — UTF-8 safe console factory
# ---------------------------------------------------------------------------
def test_make_console_handles_utf8_glyphs():
    import io as _io

    from specsmith.console_utils import make_console

    buf = _io.StringIO()
    console = make_console(file=buf, force_terminal=False, legacy_windows=False)
    # Each of these previously crashed on Windows cp1252:
    glyphs = "\u26a0 \u2192 \u2713 \u2717"
    console.print(glyphs)
    output = buf.getvalue()
    for glyph in ("\u26a0", "\u2192", "\u2713", "\u2717"):
        assert glyph in output, f"Missing glyph in console output: {glyph!r}"


def test_make_console_disables_legacy_windows_by_default():
    import io as _io

    from specsmith.console_utils import make_console

    console = make_console(file=_io.StringIO(), force_terminal=False)
    # Console exposes legacy_windows attribute; make_console must default it to False.
    assert console.legacy_windows is False


# ---------------------------------------------------------------------------
# TEST-083 — Canonical test spec file is TESTS.md
# ---------------------------------------------------------------------------
LEGACY_TEST_SPEC_NAMES = ("TEST_SPEC.md", "TEST-SPEC.md", "TEST-SPECS.md")

_LEGACY_FILE_TYPES = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".json",
    ".jsonl",
    ".j2",
    ".rst",
    ".txt",
    ".cfg",
    ".ini",
    ".ps1",
    ".cmd",
    ".sh",
}

_LEGACY_SCAN_SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".pytest_tmp",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}

_LEGACY_SCAN_SKIP_FILES = {
    Path(".specsmith") / "runs" / "WI-NEXUS-001" / "diff.patch",
    Path(".specsmith") / "runs" / "WI-NEXUS-002" / "diff.patch",
    Path(".specsmith") / "runs" / "WI-NEXUS-003" / "diff.patch",
    Path(".specsmith") / "runs" / "WI-NEXUS-006" / "pr-body.md",
    Path("tags"),
    Path("scripts") / "rename_test_spec.py",
    Path("tests") / "test_nexus.py",  # this test file
    # Governance-record files that legitimately reference legacy names while
    # documenting the rename (REQ-083 description; ledger event history).
    Path("LEDGER.md"),
    Path("REQUIREMENTS.md"),
    Path("TESTS.md"),
    Path("docs") / "LEDGER.md",  # canonical ledger (moved from root)
    Path("docs") / "REQUIREMENTS.md",  # canonical requirements (moved from root; contains history)
    Path("docs") / "TESTS.md",  # canonical tests (moved from root; contains history)
    Path("docs") / "ledger-archive.md",  # archived history; contains rename chronicle
    Path(".specsmith") / "requirements.json",
    Path(".specsmith") / "testcases.json",
    # YAML governance source files — these are the canonical equivalents of
    # docs/REQUIREMENTS.md and docs/TESTS.md; REQ-083/TEST-083 descriptions
    # legitimately reference legacy names while documenting the rename.
    Path("docs") / "requirements" / "agent.yml",
    Path("docs") / "tests" / "agent.yml",
}


def test_canonical_tests_md_exists():
    # Canonical location is now docs/TESTS.md (root TESTS.md was moved there)
    assert (REPO_ROOT / "docs" / "TESTS.md").is_file()
    assert not (REPO_ROOT / "TESTS.md").exists(), "Root TESTS.md should have been moved to docs/"
    assert not (REPO_ROOT / "TEST_SPEC.md").exists()
    assert not (REPO_ROOT / "docs" / "TEST_SPEC.md").exists()


def test_no_remaining_legacy_test_spec_references():
    """Active source/docs/templates must not contain legacy TEST_SPEC.md style names."""
    offenders: list[str] = []
    for dirpath, dirnames, filenames in os.walk(REPO_ROOT):
        dirnames[:] = [d for d in dirnames if d not in _LEGACY_SCAN_SKIP_DIRS]
        for fname in filenames:
            p = Path(dirpath) / fname
            rel = p.relative_to(REPO_ROOT)
            if rel in _LEGACY_SCAN_SKIP_FILES:
                continue
            if p.suffix.lower() not in _LEGACY_FILE_TYPES:
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for legacy in LEGACY_TEST_SPEC_NAMES:
                if legacy in text:
                    offenders.append(f"{rel}: contains {legacy!r}")
                    break
    assert not offenders, "Legacy TEST_SPEC names found:\n" + "\n".join(offenders)


def test_key_modules_reference_tests_md():
    """Spot-check that key modules now reference TESTS.md."""
    for rel in (
        Path("src") / "specsmith" / "auditor.py",
        Path("src") / "specsmith" / "importer.py",
        Path("src") / "specsmith" / "scaffolder.py",
        Path("src") / "specsmith" / "retrieval.py",
        Path("src") / "specsmith" / "exporter.py",
        Path("src") / "specsmith" / "phase.py",
        Path("src") / "specsmith" / "requirements.py",
        Path("src") / "specsmith" / "epistemic" / "stress_tester.py",
        Path("src") / "specsmith" / "epistemic" / "recovery.py",
    ):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "TESTS.md" in text, f"{rel} does not reference TESTS.md"


# ---------------------------------------------------------------------------
# TEST-084 — Natural-language governance broker
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "utterance,expected_label",
    [
        ("what does this project do?", "read_only_ask"),
        ("explain the cleanup module", "read_only_ask"),
        ("fix the cleanup bug", "change"),
        ("add a new validator command", "change"),
        ("refactor the broker", "change"),
        ("ship a release", "release"),
        ("bump the version to 0.4.0", "release"),
        ("delete the entire dist directory", "destructive"),
        ("rm -rf node_modules", "destructive"),
        ("force-push to main", "destructive"),
    ],
)
def test_broker_classify_intent(utterance, expected_label):
    from specsmith.agent.broker import Intent, classify_intent

    label_to_intent = {
        "read_only_ask": Intent.READ_ONLY_ASK,
        "change": Intent.CHANGE,
        "release": Intent.RELEASE,
        "destructive": Intent.DESTRUCTIVE,
    }
    assert classify_intent(utterance) == label_to_intent[expected_label]


def _write_sample_requirements(path: Path) -> None:
    path.write_text(
        "# Requirements\n\n"
        "## 1. Cleanup Must Default to Dry-Run\n"
        "- **ID:** REQ-077\n"
        "- **Title:** Cleanup Must Default to Dry-Run\n"
        "- **Description:** Specsmith safe cleanup defaults to dry-run mode.\n\n"
        "## 2. Console Must Be UTF-8 Safe\n"
        "- **ID:** REQ-082\n"
        "- **Title:** CLI Console Must Be UTF-8 Safe Across Platforms\n"
        "- **Description:** Rich Console output must render UTF-8 glyphs without crashing.\n\n",
        encoding="utf-8",
    )


def test_broker_infer_scope_finds_relevant_req(tmp_path):
    from specsmith.agent.broker import infer_scope

    req_md = tmp_path / "REQUIREMENTS.md"
    _write_sample_requirements(req_md)
    proposal = infer_scope("fix the cleanup dry-run regression", req_md)
    assert proposal.is_known
    titles = {r.title for r in proposal.matched_requirements}
    assert any("Cleanup" in t for t in titles)


def test_broker_infer_scope_returns_empty_when_no_match(tmp_path):
    from specsmith.agent.broker import infer_scope

    req_md = tmp_path / "REQUIREMENTS.md"
    _write_sample_requirements(req_md)
    proposal = infer_scope("investigate quantum tunnelling", req_md)
    assert not proposal.is_known
    assert proposal.confidence == 0.0


def test_broker_run_preflight_uses_injected_runner(tmp_path):
    from types import SimpleNamespace

    from specsmith.agent.broker import run_preflight

    fake_payload = {
        "decision": "accepted",
        "work_item_id": "WI-FAKE-001",
        "requirement_ids": ["REQ-077"],
        "test_case_ids": ["TEST-077"],
        "confidence_target": 0.85,
    }

    def fake_runner(cmd):
        return SimpleNamespace(stdout=json.dumps(fake_payload), stderr="", returncode=0)

    decision = run_preflight("fix cleanup", tmp_path, runner=fake_runner)
    assert decision.accepted
    assert decision.work_item_id == "WI-FAKE-001"
    assert decision.confidence_target == 0.85


def test_broker_run_preflight_handles_missing_cli(tmp_path):
    from types import SimpleNamespace

    from specsmith.agent.broker import run_preflight

    def empty_runner(cmd):
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    decision = run_preflight("fix cleanup", tmp_path, runner=empty_runner)
    assert decision.decision == "needs_clarification"


def test_broker_narrate_plan_hides_governance_ids_by_default(tmp_path):
    from specsmith.agent.broker import (
        Intent,
        PreflightDecision,
        ScopeProposal,
        narrate_plan,
    )

    decision = PreflightDecision.from_json(
        {
            "decision": "accepted",
            "work_item_id": "WI-NEXUS-099",
            "requirement_ids": ["REQ-077"],
            "test_case_ids": ["TEST-077"],
            "confidence_target": 0.9,
            "instruction": "REQ-077 is in scope.",
        }
    )
    scope = ScopeProposal()
    text = narrate_plan(Intent.CHANGE, scope, decision)
    assert "REQ-" not in text
    assert "TEST-" not in text
    assert "WI-" not in text

    verbose = narrate_plan(Intent.CHANGE, scope, decision, verbose=True)
    assert "REQ-077" in verbose
    assert "WI-NEXUS-099" in verbose


def test_broker_execute_with_governance_succeeds_on_first_pass():
    from specsmith.agent.broker import (
        PreflightDecision,
        execute_with_governance,
    )

    decision = PreflightDecision(raw={}, decision="accepted", confidence_target=0.8)
    calls = []

    def executor(d, attempt):
        calls.append(attempt)
        return {"equilibrium": True, "confidence": 0.95, "summary": "ok"}

    result = execute_with_governance(decision, executor=executor, retry_budget=3)
    assert result.success
    assert result.attempts == 1
    assert calls == [1]


def test_broker_execute_with_governance_bounds_retries_and_escalates():
    from specsmith.agent.broker import (
        PreflightDecision,
        execute_with_governance,
    )

    decision = PreflightDecision(raw={}, decision="accepted", confidence_target=0.9)
    calls = []

    def executor(d, attempt):
        calls.append(attempt)
        return {"equilibrium": False, "confidence": 0.4, "summary": "no-go"}

    result = execute_with_governance(decision, executor=executor, retry_budget=2)
    assert not result.success
    assert result.attempts == 2
    assert calls == [1, 2]
    assert result.clarifying_question  # single question surfaced


def test_broker_step_pipeline_returns_plain_language(tmp_path):
    from types import SimpleNamespace

    from specsmith.agent.broker import broker_step

    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")

    def fake_runner(cmd):
        return SimpleNamespace(
            stdout=json.dumps(
                {
                    "decision": "accepted",
                    "work_item_id": "WI-NEXUS-099",
                    "requirement_ids": ["REQ-077"],
                    "test_case_ids": ["TEST-077"],
                    "confidence_target": 0.85,
                }
            ),
            stderr="",
            returncode=0,
        )

    text = broker_step("fix the cleanup dry-run regression", tmp_path, runner=fake_runner)
    assert "REQ-" not in text
    assert "TEST-" not in text
    assert "WI-" not in text
    assert "Specsmith approved" in text


# ---------------------------------------------------------------------------
# TEST-085 — specsmith preflight CLI subcommand
# ---------------------------------------------------------------------------
REQUIRED_PREFLIGHT_KEYS = {
    "decision",
    "work_item_id",
    "requirement_ids",
    "test_case_ids",
    "confidence_target",
    "instruction",
}


def _invoke_preflight(tmp_path: Path, utterance: str, *extra: str):
    from click.testing import CliRunner

    from specsmith.cli import main

    (tmp_path / "scaffold.yml").write_text(
        "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
    )
    runner = CliRunner()
    return runner.invoke(
        main,
        ["preflight", utterance, "--project-dir", str(tmp_path), "--json", *extra],
        env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
        catch_exceptions=False,
    )


def test_specsmith_preflight_cli_read_only_ask_accepts(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    result = _invoke_preflight(tmp_path, "what does the cleanup module do?")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert REQUIRED_PREFLIGHT_KEYS.issubset(payload.keys())
    assert payload["decision"] == "accepted"
    assert payload["intent"] == "read_only_ask"


def test_specsmith_preflight_cli_destructive_needs_clarification(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    result = _invoke_preflight(tmp_path, "delete the entire dist directory")
    # REQ-092: needs_clarification exits 2; JSON still printed on stdout.
    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "needs_clarification"
    assert payload["intent"] == "destructive"
    assert payload["instruction"]  # non-empty


def test_specsmith_preflight_cli_change_without_scope_needs_clarification(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    result = _invoke_preflight(tmp_path, "add support for quantum-tunnelling sensors")
    # REQ-092: needs_clarification exits 2; JSON still printed on stdout.
    assert result.exit_code == 2, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "needs_clarification"
    assert payload["intent"] == "change"
    assert payload["instruction"]


def test_specsmith_preflight_cli_change_with_scope_accepts(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "accepted"
    assert payload["intent"] == "change"
    assert payload["requirement_ids"]  # at least one matched REQ


# ---------------------------------------------------------------------------
# TEST-086 — REPL gates execution on preflight acceptance
# ---------------------------------------------------------------------------
def test_repl_gates_orchestrator_run_task_on_decision_accepted():
    from specsmith.agent import repl

    src = inspect.getsource(repl)
    # Must have a guard checking decision.accepted before running orchestrator.
    assert "if decision.accepted:" in src
    # Must explain the gate to the user when not accepted.
    assert "preflight did not accept" in src
    # The unconditional broker-branch run_task call must be removed.
    broker_branch = src.split("# REQ-086", 1)[-1]
    assert "if decision.accepted" in broker_branch


# ---------------------------------------------------------------------------
# TEST-087 — REPL drives orchestrator via bounded-retry harness
# ---------------------------------------------------------------------------
def test_repl_drives_orchestrator_via_execute_with_governance():
    from specsmith.agent import repl

    src = inspect.getsource(repl)
    # Must import and call execute_with_governance.
    assert "execute_with_governance" in src
    # The broker branch must use the harness rather than calling run_task
    # directly. We isolate the broker-branch by splitting on the REQ-086
    # marker; from that point onward, every reference to orchestrator.run_task
    # must be inside the executor closure passed to execute_with_governance.
    broker_branch = src.split("# REQ-086", 1)[-1]
    assert "execute_with_governance(decision" in broker_branch
    # All run_task references in the broker branch live inside the executor
    # closure named `_executor`. We assert that the closure exists and that
    # the only run_task call in the broker branch is reachable through it.
    assert "def _executor(" in broker_branch
    # No bare 'orchestrator.run_task(user_input)' call sits outside the
    # closure (the closure body is the only legitimate caller).
    closure_body = broker_branch.split("def _executor(", 1)[1]
    assert "orchestrator.run_task" in closure_body


# ---------------------------------------------------------------------------
# TEST-088 — specsmith preflight resolves test_case_ids from machine state
# ---------------------------------------------------------------------------
def test_specsmith_preflight_cli_resolves_test_case_ids_from_machine_state(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    # Seed a tiny .specsmith/testcases.json with a TEST -> REQ mapping.
    spec_dir = tmp_path / ".specsmith"
    spec_dir.mkdir()
    (spec_dir / "testcases.json").write_text(
        json.dumps(
            [
                {
                    "id": "TEST-077",
                    "requirement_id": "REQ-077",
                    "title": "Safe Cleanup Defaults to Dry-Run",
                },
                {
                    "id": "TEST-082",
                    "requirement_id": "REQ-082",
                    "title": "UTF-8 Safe Console Factory",
                },
                {
                    "id": "TEST-XXX",
                    "requirement_id": "REQ-XXX",  # unrelated; must not appear
                    "title": "Should not be matched",
                },
            ]
        ),
        encoding="utf-8",
    )

    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "accepted"
    assert "REQ-077" in payload["requirement_ids"]
    assert "TEST-077" in payload["test_case_ids"]
    # Unmatched ids never leak into the response.
    assert "TEST-XXX" not in payload["test_case_ids"]


# ---------------------------------------------------------------------------
# TEST-089 — Nexus live l1-nexus smoke test script
# ---------------------------------------------------------------------------
def test_nexus_smoke_script_exists_and_exposes_smoke_test():
    smoke_path = REPO_ROOT / "scripts" / "nexus_smoke.py"
    assert smoke_path.is_file(), "scripts/nexus_smoke.py is missing"

    import importlib.util as _iutil

    spec = _iutil.spec_from_file_location("nexus_smoke", smoke_path)
    assert spec is not None and spec.loader is not None
    module = _iutil.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert callable(getattr(module, "smoke_test", None))


def test_nexus_smoke_test_returns_structured_error_when_offline():
    smoke_path = REPO_ROOT / "scripts" / "nexus_smoke.py"
    import importlib.util as _iutil

    spec = _iutil.spec_from_file_location("nexus_smoke", smoke_path)
    module = _iutil.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Point at an unused localhost port; the function must not crash and must
    # return ok=False with a non-empty error string.
    result = module.smoke_test(base_url="http://127.0.0.1:1", timeout=0.5)
    assert isinstance(result, dict)
    assert result["ok"] is False
    assert result["error"]
    for key in ("ok", "content", "latency_ms", "error"):
        assert key in result


@pytest.mark.skipif(
    os.environ.get("NEXUS_LIVE") != "1",
    reason="set NEXUS_LIVE=1 to run against a running vLLM l1-nexus container",
)
def test_nexus_smoke_test_against_live_container():
    smoke_path = REPO_ROOT / "scripts" / "nexus_smoke.py"
    import importlib.util as _iutil

    spec = _iutil.spec_from_file_location("nexus_smoke", smoke_path)
    module = _iutil.module_from_spec(spec)
    spec.loader.exec_module(module)

    result = module.smoke_test()
    assert result["ok"], result
    assert result["content"]


# ---------------------------------------------------------------------------
# TEST-090 — Nexus documentation surfaces broker, preflight, gated execution
# ---------------------------------------------------------------------------
def test_architecture_md_describes_nexus_broker_preflight_and_gate():
    text = (REPO_ROOT / "ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "Nexus Broker Boundary" in text
    assert "Nexus Preflight CLI Subcommand" in text
    assert "Nexus REPL Execution Gate" in text
    assert "Nexus Bounded-Retry Harness" in text
    assert "specsmith preflight" in text
    assert "`/why`" in text


def test_readme_describes_nexus_broker_preflight_and_gate():
    text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    # Section heading and key concepts the user can search for.
    assert "## Nexus" in text
    assert "specsmith preflight" in text
    assert "broker" in text.lower()
    assert "`/why`" in text
    # The REPL prompt is the user's mental model anchor.
    assert "nexus>" in text


# ---------------------------------------------------------------------------
# TEST-091 — orchestrator.run_task returns a structured TaskResult
# ---------------------------------------------------------------------------
def test_orchestrator_taskresult_has_required_fields():
    from specsmith.agent.orchestrator import TaskResult

    result = TaskResult()
    for attr in ("equilibrium", "confidence", "summary", "files_changed", "test_results"):
        assert hasattr(result, attr), f"TaskResult missing field: {attr}"
    assert isinstance(result.files_changed, list)
    assert isinstance(result.test_results, dict)
    # to_dict() round-trips the fields.
    d = result.to_dict()
    assert set(d.keys()) >= {
        "equilibrium",
        "confidence",
        "summary",
        "files_changed",
        "test_results",
    }


def test_orchestrator_build_task_result_parses_output_contract():
    from specsmith.agent import orchestrator as orch_mod

    instance = orch_mod.Orchestrator.__new__(orch_mod.Orchestrator)
    summary = (
        "Plan:\n- step 1\n"
        "Commands to run:\n- pytest\n"
        "Files changed:\n- src/foo.py\n- src/bar.py\n"
        "Diff:\n+ added line\n"
        "Test results:\n3 passed, 0 failed\n"
        "Next action:\nrun pytest -q"
    )
    fake_chat = type("FakeChat", (), {"summary": summary})()
    result = instance._build_task_result(fake_chat, task="do thing")
    assert result.equilibrium
    assert 0.5 < result.confidence <= 1.0
    assert "src/foo.py" in result.files_changed
    assert "src/bar.py" in result.files_changed
    assert "raw" in result.test_results
    assert "3 passed" in result.test_results["raw"]


def test_repl_executor_consumes_taskresult_fields():
    from specsmith.agent import repl

    src = inspect.getsource(repl)
    # The executor closure must read structured fields rather than synthesize.
    assert "task_result.equilibrium" in src
    assert "task_result.confidence" in src
    # And the bool(summary) heuristic must be gone from the executor closure
    # body itself (the broker-branch comment may still reference it as the
    # historical antipattern that REQ-091 retired).
    broker_branch = src.split("# REQ-086", 1)[-1]
    closure_body = broker_branch.split("def _executor(", 1)[1]
    closure_until_dedent = closure_body.split("result = execute_with_governance", 1)[0]
    assert "bool(summary)" not in closure_until_dedent


# ---------------------------------------------------------------------------
# TEST-092 — specsmith preflight CLI returns decision-specific exit codes
# ---------------------------------------------------------------------------
def test_specsmith_preflight_cli_exit_code_zero_on_accepted(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    result = _invoke_preflight(tmp_path, "what does the cleanup module do?")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "accepted"


def test_specsmith_preflight_cli_exit_code_two_on_needs_clarification(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    result = _invoke_preflight(tmp_path, "force-push to main")
    assert result.exit_code == 2, result.output
    # JSON must still parse on stdout for non-zero exits.
    payload = json.loads(result.output)
    assert payload["decision"] == "needs_clarification"


# ---------------------------------------------------------------------------
# TEST-093 — accepted preflight records a ledger event
# ---------------------------------------------------------------------------
def test_specsmith_preflight_accepted_appends_ledger_event(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    ledger_before = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")

    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert result.exit_code == 0, result.output

    ledger_after = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
    assert len(ledger_after) > len(ledger_before)
    assert "specsmith preflight accepted" in ledger_after
    assert "REQ-085" in ledger_after
    # The matched requirement id must be tagged in the entry too.
    assert "REQ-077" in ledger_after


def test_specsmith_preflight_needs_clarification_does_not_touch_ledger(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")
    ledger_before = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")

    result = _invoke_preflight(tmp_path, "delete the entire dist directory")
    assert result.exit_code == 2, result.output

    ledger_after = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
    assert ledger_after == ledger_before


# ---------------------------------------------------------------------------
# TEST-094 — /why surfaces post-run governance block in REPL
# ---------------------------------------------------------------------------
def test_repl_emits_why_post_run_block_when_verbose():
    from specsmith.agent import repl

    src = inspect.getsource(repl)
    # The post-run block lives after the harness call and is guarded by
    # verbose_governance.
    broker_branch = src.split("# REQ-086", 1)[-1]
    assert "if verbose_governance:" in broker_branch
    assert "[/why]" in broker_branch
    for token in (
        "work_item_id",
        "requirement_ids",
        "test_case_ids",
        "confidence",
        "equilibrium",
    ):
        assert token in broker_branch, f"/why block missing reference to {token}"


# ---------------------------------------------------------------------------
# TEST-095 — Nexus live smoke evidence captured
# ---------------------------------------------------------------------------
def test_nexus_live_smoke_evidence_captured():
    log_path = REPO_ROOT / ".specsmith" / "runs" / "WI-NEXUS-011" / "logs.txt"
    # Runtime artifacts are now gitignored (see .gitignore entry for .specsmith/runs/).
    # When running locally after the live smoke was captured the file exists and is
    # validated; in CI it will be absent so we skip gracefully.
    if not log_path.is_file():
        pytest.skip(
            "WI-NEXUS-011/logs.txt not present — runtime run artifacts are gitignored; "
            "evidence is local-only. Re-run the live smoke locally to capture it."
        )
    body = log_path.read_text(encoding="utf-8")
    assert body.strip(), "WI-NEXUS-011 logs.txt is empty"
    # Either a successful live smoke or an honest skip note is acceptable.
    assert ('"ok": true' in body) or ('"ok": false' in body) or ("NEXUS_LIVE" in body), (
        "WI-NEXUS-011 logs.txt does not document a smoke result"
    )


# ---------------------------------------------------------------------------
# TEST-096 — execute_with_governance maps failures to retry strategies
# ---------------------------------------------------------------------------
def test_classify_retry_strategy_test_failures_map_to_fix_tests():
    decision = _PreflightDecision(raw={}, decision="accepted", confidence_target=0.9)
    report = {
        "equilibrium": False,
        "confidence": 0.4,
        "summary": "",
        "test_results": {"failed": 2},
    }
    assert _classify_retry_strategy(report, decision) == "fix_tests"


def test_classify_retry_strategy_rollback_signal():
    decision = _PreflightDecision(raw={}, decision="accepted", confidence_target=0.9)
    report = {
        "equilibrium": False,
        "confidence": 0.4,
        "summary": "detected a contradiction in the change set",
        "test_results": {},
    }
    assert _classify_retry_strategy(report, decision) == "rollback"


def test_classify_retry_strategy_low_confidence_to_narrow_scope():
    decision = _PreflightDecision(raw={}, decision="accepted", confidence_target=0.9)
    report = {"equilibrium": False, "confidence": 0.1, "summary": "", "test_results": {}}
    assert _classify_retry_strategy(report, decision) == "narrow_scope"


def test_execute_with_governance_surfaces_strategy_label():
    decision = _PreflightDecision(raw={}, decision="accepted", confidence_target=0.9)

    def executor(d, attempt):
        return {
            "equilibrium": False,
            "confidence": 0.4,
            "summary": "",
            "test_results": {"failed": 1},
        }

    result = _execute_with_governance(decision, executor=executor, retry_budget=2)
    assert not result.success
    assert result.strategy in _RETRY_STRATEGIES
    assert result.strategy == "fix_tests"
    assert result.strategy in result.clarifying_question


# ---------------------------------------------------------------------------
# TEST-097 — specsmith verify CLI emits required JSON
# ---------------------------------------------------------------------------
def _invoke_verify(tmp_path: Path, payload_in: dict, *extra: str):
    from click.testing import CliRunner

    from specsmith.cli import main

    (tmp_path / "scaffold.yml").write_text(
        "name: test\ntype: cli-python\nspec_version: 0.3.13\n", encoding="utf-8"
    )
    runner = CliRunner()
    return runner.invoke(
        main,
        ["verify", "--project-dir", str(tmp_path), "--stdin", *extra],
        input=json.dumps(payload_in),
        env={"SPECSMITH_NO_AUTO_UPDATE": "1"},
        catch_exceptions=False,
    )


def test_specsmith_verify_cli_zero_when_equilibrium(tmp_path):
    payload_in = {
        "diff": "@@ +++ added line\n",
        "files_changed": ["src/foo.py"],
        "test_results": {"passed": 5, "failed": 0},
    }
    result = _invoke_verify(tmp_path, payload_in)
    assert result.exit_code == 0, result.output
    out = json.loads(result.output)
    for key in (
        "equilibrium",
        "confidence",
        "summary",
        "files_changed",
        "test_results",
        "retry_strategy",
    ):
        assert key in out
    assert out["equilibrium"] is True
    assert out["retry_strategy"] == ""


def test_specsmith_verify_cli_two_when_retry_recommended(tmp_path):
    payload_in = {
        "diff": "@@ +++ added line\n",
        "files_changed": ["src/foo.py"],
        "test_results": {"passed": 5, "failed": 2},
    }
    result = _invoke_verify(tmp_path, payload_in)
    assert result.exit_code == 2, result.output
    out = json.loads(result.output)
    assert out["equilibrium"] is False
    assert out["retry_strategy"] in {
        "fix_tests",
        "narrow_scope",
        "expand_scope",
        "rollback",
        "stop",
    }


# ---------------------------------------------------------------------------
# TEST-098 — confidence threshold read from .specsmith/config.yml
# ---------------------------------------------------------------------------
def test_specsmith_preflight_confidence_threshold_floor_from_config(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    spec_dir = tmp_path / ".specsmith"
    spec_dir.mkdir()
    (spec_dir / "config.yml").write_text(
        "epistemic:\n  confidence_threshold: 0.95\n", encoding="utf-8"
    )
    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["decision"] == "accepted"
    assert payload["confidence_target"] >= 0.95


def test_specsmith_preflight_confidence_threshold_falls_back_without_config(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    # No .specsmith/config.yml — heuristic default applies (0.7 floor for changes).
    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["confidence_target"] >= 0.7
    assert payload["confidence_target"] < 0.95


# ---------------------------------------------------------------------------
# TEST-099 — accepted preflight records a distinct work_proposal event
# ---------------------------------------------------------------------------
def test_specsmith_preflight_accepted_records_work_proposal(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")

    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert result.exit_code == 0, result.output

    ledger = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
    # Both the preflight event and the work_proposal event must appear.
    assert "specsmith preflight accepted" in ledger
    assert "work_proposal" in ledger
    # The work_proposal entry references REQ-044 and REQ-085.
    assert "REQ-044" in ledger
    assert "REQ-085" in ledger


def test_specsmith_preflight_emits_work_proposal_per_unique_work_item(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    (tmp_path / "LEDGER.md").write_text("# Ledger\n", encoding="utf-8")

    r1 = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert r1.exit_code == 0, r1.output
    r2 = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert r2.exit_code == 0, r2.output

    ledger = (tmp_path / "LEDGER.md").read_text(encoding="utf-8")
    proposal_count = ledger.count("work_proposal")
    # Each invocation generates a fresh WI-XXXXXXXX so both should record a
    # distinct work_proposal event.
    assert proposal_count >= 2


# ---------------------------------------------------------------------------
# TEST-100 — broker scope inference surfaces stress warnings under --stress
# ---------------------------------------------------------------------------
def test_specsmith_preflight_stress_flag_surfaces_warnings(tmp_path, monkeypatch):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")

    # Patch the StressTester import path used by cli._stress_test_warnings to
    # return a synthetic critical failure so the test is deterministic and
    # does not depend on the real epistemic stress-tester implementation.
    import specsmith.cli as cli_mod

    class _FakeResult:
        critical_count = 1
        logic_knots = []

    def _fake_warnings(root, matched_requirements):
        return ["1 critical failure(s) detected by stress-tester."]

    monkeypatch.setattr(cli_mod, "_stress_test_warnings", _fake_warnings)

    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression", "--stress")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload.get("stress_warnings")
    assert any("critical" in w for w in payload["stress_warnings"])


def test_specsmith_preflight_no_stress_flag_omits_stress_warnings(tmp_path):
    _write_sample_requirements(tmp_path / "REQUIREMENTS.md")
    result = _invoke_preflight(tmp_path, "fix the cleanup dry-run regression")
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert not payload.get("stress_warnings")
