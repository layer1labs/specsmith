# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Shared pytest configuration for specsmith tests.

Includes a workaround for WinError 448 ("untrusted mount point") that
crashes pytest's temp directory cleanup on Windows when tests create
git repos or junctions in tmp_path directories.
"""

from __future__ import annotations

import contextlib
import sys

import pytest


def pytest_configure(config):  # type: ignore[no-untyped-def]  # noqa: ARG001
    """Patch pytest's cleanup_dead_symlinks early to suppress WinError 448.

    pytest 9.x creates a *-current symlink in basetemp. On Windows, this
    can become an "untrusted mount point" (WinError 448) when the test
    creates git repos or NTFS junctions inside the tmp_path. The error
    crashes ``cleanup_dead_symlinks`` in ``pytest_sessionfinish`` before
    the test summary is printed.

    Patching at configure time ensures it happens before any session hooks.
    """
    if sys.platform != "win32":
        return

    try:
        from _pytest import pathlib as _pytest_pathlib
        from _pytest import tmpdir as _pytest_tmpdir

        _orig = _pytest_pathlib.cleanup_dead_symlinks

        def _safe_cleanup(basepath):  # type: ignore[no-untyped-def]
            with contextlib.suppress(OSError):
                _orig(basepath)

        # Patch in both modules — tmpdir imports the function directly
        _pytest_pathlib.cleanup_dead_symlinks = _safe_cleanup
        _pytest_tmpdir.cleanup_dead_symlinks = _safe_cleanup  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass


@pytest.fixture(autouse=True)
def _disable_specsmith_auto_update(monkeypatch: pytest.MonkeyPatch) -> None:
    """Suppress the project auto-update / PyPI-check prompts during tests.

    Both ``_maybe_prompt_project_update`` and ``_maybe_notify_pypi_update``
    in ``specsmith.cli`` run on every CLI invocation. The first calls
    ``input()`` when the project's ``scaffold.yml`` ``spec_version`` is
    behind the installed version — that ``input()`` call would silently
    consume the first line of stdin in tests that drive the chat
    ``--interactive`` protocol. The second hits the network. Pinning the
    suppression env vars keeps tests hermetic, deterministic, and free of
    network access.
    """
    monkeypatch.setenv("SPECSMITH_NO_AUTO_UPDATE", "1")
    monkeypatch.setenv("SPECSMITH_PYPI_CHECKED", "1")
