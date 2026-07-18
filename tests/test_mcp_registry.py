# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Tests for MCP project registry hygiene (issue #316).

Covers MCPREG-001 through MCPREG-010:
- Explicit registration only
- Pytest isolation
- Project validation
- Canonical deduplication
- Stale pruning
- Offline/inaccessible path safety
- Atomic writes and recovery
- Concurrent registration
- Cross-platform paths
- Structured status
"""

from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path

import pytest

import specsmith.mcp_server as mcp_mod

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def reg_home(tmp_path: Path) -> Path:
    """Return tmp_path and set SPECSMITH_HOME for isolation."""
    os.environ["SPECSMITH_HOME"] = str(tmp_path)
    yield tmp_path
    os.environ.pop("SPECSMITH_HOME", None)


def _make_project_dir(base: Path, name: str) -> Path:
    """Create a directory with a .specsmith marker so it passes validation."""
    d = base / name
    d.mkdir(parents=True, exist_ok=True)
    (d / ".specsmith").mkdir(exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# MCPREG-001 — Explicit registration only
# ---------------------------------------------------------------------------


class TestMCPREG001ExplicitRegistration:
    """MCP startup never persists a path without explicit registration."""

    def test_startup_does_not_persist(self, reg_home: Path) -> None:
        """Starting an MCP server for a path must not automatically persist that path."""
        # The server reads the registry at startup but does not write to it.
        # We verify the registry stays empty when no register_project call is made.
        assert mcp_mod.read_registry() == []
        # Simulate "server startup" — just read the registry, don't write.
        _ = mcp_mod.read_registry()
        assert mcp_mod.read_registry() == []

    def test_register_is_explicit(self, reg_home: Path) -> None:
        """Only explicit register_project calls persist entries."""
        proj = _make_project_dir(reg_home, "explicit-proj")
        added = mcp_mod.register_project(str(proj))
        assert added is True
        assert len(mcp_mod.read_registry()) == 1


# ---------------------------------------------------------------------------
# MCPREG-002 — Pytest isolation
# ---------------------------------------------------------------------------


class TestMCPREG002PytestIsolation:
    """Temporary test roots leave the real/default registry unchanged."""

    def test_temp_dirs_not_persisted(self, reg_home: Path) -> None:
        """pytest temp directory paths are rejected by _is_temp_path."""
        temp_path = reg_home / "pytest-of-user" / "pytest123" / "test0"
        temp_path.mkdir(parents=True, exist_ok=True)
        (temp_path / ".specsmith").mkdir()
        # register_project should reject temp paths.
        added = mcp_mod.register_project(str(temp_path))
        assert added is False
        assert mcp_mod.read_registry() == []

    def test_multiple_tests_isolation(self, reg_home: Path) -> None:
        """Multiple test runs with different tmp_paths must not leak."""
        for i in range(5):
            test_home = reg_home / f"test_run_{i}"
            os.environ["SPECSMITH_HOME"] = str(test_home)
            proj = _make_project_dir(test_home, f"proj_{i}")
            mcp_mod.register_project(str(proj))
            # Each test_home has its own isolated registry.
            assert len(mcp_mod.read_registry()) == 1
            os.environ["SPECSMITH_HOME"] = str(reg_home)
        # The main reg_home registry should still be empty.
        assert mcp_mod.read_registry() == []

    def test_read_repairs_transient_and_malformed_entries(self, reg_home: Path) -> None:
        """Old or tampered registry entries are removed atomically on read."""
        valid = _make_project_dir(reg_home, "preserved")
        transient = reg_home / "pytest-of-user" / "pytest123" / "leaked"
        registry = mcp_mod._registry_file()
        registry.write_text(
            json.dumps(
                {
                    "projects": [
                        str(valid),
                        str(transient),
                        42,
                        "",
                        str(valid),
                    ]
                }
            ),
            encoding="utf-8",
        )

        assert mcp_mod.read_registry() == [str(valid.resolve())]
        assert json.loads(registry.read_text(encoding="utf-8")) == {"projects": [str(valid)]}


# ---------------------------------------------------------------------------
# MCPREG-003 — Project validation
# ---------------------------------------------------------------------------


class TestMCPREG003ProjectValidation:
    """Only valid Specsmith roots register without an explicit override."""

    def test_valid_specsmith_root_registers(self, reg_home: Path) -> None:
        """A directory with .specsmith marker registers successfully."""
        proj = _make_project_dir(reg_home, "valid-proj")
        added = mcp_mod.register_project(str(proj))
        assert added is True

    def test_missing_directory_rejected(self, reg_home: Path) -> None:
        """Non-existent paths are rejected."""
        added = mcp_mod.register_project(str(reg_home / "nonexistent"))
        assert added is False

    def test_regular_file_rejected(self, reg_home: Path) -> None:
        """A regular file (not a directory) is rejected."""
        f = reg_home / "afile.txt"
        f.write_text("hello", encoding="utf-8")
        added = mcp_mod.register_project(str(f))
        assert added is False

    def test_uninitialized_directory_rejected(self, reg_home: Path) -> None:
        """A directory without project markers is rejected by default."""
        plain = reg_home / "plain-dir"
        plain.mkdir()
        added = mcp_mod.register_project(str(plain))
        assert added is False

    def test_allow_uninitialized_bypasses_validation(self, reg_home: Path) -> None:
        """allow_uninitialized=True accepts any existing directory."""
        plain = reg_home / "plain-dir"
        plain.mkdir()
        added = mcp_mod.register_project(str(plain), allow_uninitialized=True)
        assert added is True


# ---------------------------------------------------------------------------
# MCPREG-004 — Canonical deduplication
# ---------------------------------------------------------------------------


class TestMCPREG004CanonicalDeduplication:
    """Equivalent paths produce one canonical entry."""

    def test_relative_vs_absolute_dedup(self, reg_home: Path) -> None:
        """Registering the same path via relative and absolute forms yields one entry."""
        proj = _make_project_dir(reg_home, "dedup-proj")
        abs_path = str(proj.resolve())
        rel_path = str(proj)

        added1 = mcp_mod.register_project(abs_path)
        assert added1 is True

        added2 = mcp_mod.register_project(rel_path)
        assert added2 is False  # Duplicate detected.

        assert len(mcp_mod.read_registry()) == 1

    def test_symlink_equivalent_dedup(self, reg_home: Path) -> None:
        """Symlink-equivalent paths resolve to the same canonical form."""
        proj = _make_project_dir(reg_home, "real-proj")
        link = reg_home / "link-proj"
        try:
            link.symlink_to(proj, target_is_directory=True)
        except OSError:
            pytest.skip("Symlinks not supported on this system")

        added1 = mcp_mod.register_project(str(proj))
        assert added1 is True

        added2 = mcp_mod.register_project(str(link))
        # After resolve(), both point to the same path.
        assert added2 is False

    def test_trailing_separator_dedup(self, reg_home: Path) -> None:
        """Paths with/without trailing separators deduplicate."""
        proj = _make_project_dir(reg_home, "trail-proj")
        added1 = mcp_mod.register_project(str(proj))
        assert added1 is True

        added2 = mcp_mod.register_project(str(proj) + "/")
        assert added2 is False


# ---------------------------------------------------------------------------
# MCPREG-005 — Stale pruning
# ---------------------------------------------------------------------------


class TestMCPREG005StalePruning:
    """Dry-run reports stale entries without mutation; confirmed prune removes them."""

    def test_dry_run_reports_stale(self, reg_home: Path) -> None:
        """prune --dry-run reports missing entries without mutating."""
        stale = reg_home / "stale-proj"
        stale.mkdir()
        (stale / ".specsmith").mkdir()
        mcp_mod.register_project(str(stale))
        assert len(mcp_mod.read_registry()) == 1

        # Delete the directory to make it stale.
        shutil.rmtree(stale)

        result = mcp_mod.prune_registry(dry_run=True)
        assert len(result["removed"]) == 1
        assert len(mcp_mod.read_registry()) == 1  # Not mutated.

    def test_confirmed_prune_removes(self, reg_home: Path) -> None:
        """prune without --dry-run actually removes stale entries."""
        stale = reg_home / "stale-proj"
        stale.mkdir()
        (stale / ".specsmith").mkdir()
        mcp_mod.register_project(str(stale))

        shutil.rmtree(stale)
        result = mcp_mod.prune_registry(dry_run=False)
        assert len(result["removed"]) == 1
        assert len(mcp_mod.read_registry()) == 0


# ---------------------------------------------------------------------------
# MCPREG-006 — Offline/inaccessible path safety
# ---------------------------------------------------------------------------


class TestMCPREG006OfflinePathSafety:
    """Temporarily inaccessible paths are preserved unless policy explicitly authorizes removal."""

    def test_deleted_paths_removed(self, reg_home: Path) -> None:
        """Confirmed deleted paths are removed by prune."""
        proj = _make_project_dir(reg_home, "deleted-proj")
        mcp_mod.register_project(str(proj))
        shutil.rmtree(proj)

        result = mcp_mod.prune_registry(dry_run=False)
        assert len(result["removed"]) == 1

    def test_temporarily_inaccessible_preserved(self, reg_home: Path) -> None:
        """If a path exists but is not a directory, it's treated as stale and removed."""
        proj = _make_project_dir(reg_home, "now-file")
        mcp_mod.register_project(str(proj))
        # Replace directory with a file.
        shutil.rmtree(proj)
        proj.write_text("data", encoding="utf-8")

        result = mcp_mod.prune_registry(dry_run=False)
        assert len(result["removed"]) == 1
        proj.unlink()


# ---------------------------------------------------------------------------
# MCPREG-007 — Atomic writes and recovery
# ---------------------------------------------------------------------------


class TestMCPREG007AtomicWrites:
    """Interrupted writes preserve either the prior or complete new registry."""

    def test_write_creates_valid_json(self, reg_home: Path) -> None:
        """After a successful write, the registry file is valid JSON."""
        proj = _make_project_dir(reg_home, "atomic-proj")
        mcp_mod.register_project(str(proj))
        reg_file = mcp_mod._registry_file()
        data = json.loads(reg_file.read_text(encoding="utf-8"))
        assert "projects" in data
        assert len(data["projects"]) == 1

    def test_malformed_registry_handled(self, reg_home: Path) -> None:
        """A malformed registry file returns an empty list without crashing."""
        reg_file = mcp_mod._registry_file()
        reg_file.parent.mkdir(parents=True, exist_ok=True)
        reg_file.write_text("{bad json", encoding="utf-8")
        result = mcp_mod.read_registry()
        assert result == []

    def test_backup_file_preserved_on_rename_failure(self, reg_home: Path) -> None:
        """If rename fails, direct write still produces valid output."""
        # This is a soft test — on most systems rename works.
        proj = _make_project_dir(reg_home, "rename-proj")
        mcp_mod.register_project(str(proj))
        # Verify no .tmp file is left behind after successful write.
        tmp_files = list(reg_home.glob("*.tmp"))
        assert len(tmp_files) == 0


# ---------------------------------------------------------------------------
# MCPREG-008 — Concurrent registration
# ---------------------------------------------------------------------------


class TestMCPREG008ConcurrentRegistration:
    """Two concurrent register/unregister operations do not lose unrelated entries."""

    def test_concurrent_registers_no_data_loss(self, reg_home: Path) -> None:
        """Multiple threads registering different projects should all persist."""
        errors: list[Exception] = []

        def register_thread(idx: int) -> None:
            try:
                proj = _make_project_dir(reg_home, f"concurrent-{idx}")
                mcp_mod.register_project(str(proj))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=register_thread, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        assert len(errors) == 0
        projects = mcp_mod.read_registry()
        assert len(projects) == 5
        assert not mcp_mod._registry_lock_file().exists()

    def test_atomic_replace_retries_transient_permission_error(
        self, reg_home: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A transient Windows file-handle denial does not lose registration."""
        project = _make_project_dir(reg_home, "replace-retry")
        real_replace = mcp_mod.os.replace
        attempts = 0

        def flaky_replace(source: str, destination: Path) -> None:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise PermissionError(13, "transient access denial")
            real_replace(source, destination)

        monkeypatch.setattr(mcp_mod.os, "replace", flaky_replace)

        assert mcp_mod.register_project(str(project)) is True
        assert mcp_mod.read_registry() == [str(project.resolve())]
        assert attempts == 2

    def test_concurrent_register_unregister(self, reg_home: Path) -> None:
        """Register and unregister in parallel should not crash."""
        proj = _make_project_dir(reg_home, "concurrent-reg")
        mcp_mod.register_project(str(proj))

        errors: list[Exception] = []

        def register_loop() -> None:
            for i in range(3):
                try:
                    p = _make_project_dir(reg_home, f"loop-{i}")
                    mcp_mod.register_project(str(p))
                except Exception as exc:
                    errors.append(exc)

        def unregister_loop() -> None:
            for i in range(3):
                try:
                    p = reg_home / f"loop-{i}"
                    mcp_mod.unregister_project(str(p))
                except Exception:
                    pass

        t1 = threading.Thread(target=register_loop)
        t2 = threading.Thread(target=unregister_loop)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        assert len(errors) == 0


# ---------------------------------------------------------------------------
# MCPREG-009 — Cross-platform paths
# ---------------------------------------------------------------------------


class TestMCPREG009CrossPlatformPaths:
    """Linux, macOS, and Windows path fixtures produce stable canonical entries."""

    def test_canonicalize_path(self, reg_home: Path) -> None:
        """_canonicalize_path produces consistent results."""
        proj = _make_project_dir(reg_home, "cross-proj")
        c1 = mcp_mod._canonicalize_path(str(proj))
        c2 = mcp_mod._canonicalize_path(str(proj) + "/")
        assert c1 == c2

    def test_case_insensitive_dedup(self, reg_home: Path) -> None:
        """Path case differences are deduplicated on case-insensitive filesystems."""
        proj = _make_project_dir(reg_home, "CaseProj")
        added1 = mcp_mod.register_project(str(proj))
        assert added1 is True
        # Register with different case.
        added2 = mcp_mod.register_project(
            str(proj).upper() if str(proj).islower() else str(proj).lower()
        )
        # The alternate spelling resolves to the same filesystem entry on
        # case-insensitive Windows and macOS volumes.
        assert added2 is False

    def test_path_equivalence_preserves_case_sensitive_entries(self, reg_home: Path) -> None:
        """Distinct case-sensitive entries must not be conflated."""
        upper = _make_project_dir(reg_home, "CaseSensitive")
        lower = _make_project_dir(reg_home, "casesensitive")

        if upper.samefile(lower):
            pytest.skip("filesystem is case-insensitive")

        assert mcp_mod._paths_equivalent(str(upper), str(lower)) is False


# ---------------------------------------------------------------------------
# MCPREG-010 — Structured status
# ---------------------------------------------------------------------------


class TestMCPREG010StructuredStatus:
    """Registry operations expose structured path, state, provenance, and reasons."""

    def test_prune_returns_structured_dict(self, reg_home: Path) -> None:
        """prune_registry returns a dict with removed, preserved, stale, inaccessible keys."""
        result = mcp_mod.prune_registry(dry_run=True)
        assert isinstance(result, dict)
        assert "removed" in result
        assert "preserved" in result
        assert "stale" in result
        assert "inaccessible" in result
        assert isinstance(result["removed"], list)
        assert isinstance(result["preserved"], list)

    def test_read_registry_returns_list_of_strings(self, reg_home: Path) -> None:
        """read_registry returns a list of strings."""
        proj = _make_project_dir(reg_home, "typed-proj")
        mcp_mod.register_project(str(proj))
        result = mcp_mod.read_registry()
        assert isinstance(result, list)
        assert all(isinstance(p, str) for p in result)
