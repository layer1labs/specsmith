# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""UpdateChecker — background QThread that silently upgrades specsmith."""

from __future__ import annotations

import subprocess
import sys

from PySide6.QtCore import QThread, Signal


class UpdateChecker(QThread):
    """Background thread: check PyPI → upgrade if newer dev version available.

    Signals:
      updated(str)    — emitted with new version string after successful upgrade
      check_done(str) — emitted with installed version (no upgrade needed)
      error(str)      — emitted on any error (non-fatal)
    """

    updated = Signal(str)
    check_done = Signal(str)
    error = Signal(str)

    def run(self) -> None:
        try:
            import importlib.metadata
            import json
            import urllib.request

            current = importlib.metadata.version("specsmith")

            # Fetch available versions from PyPI (include pre-releases)
            url = "https://pypi.org/pypi/specsmith/json"
            with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
                data = json.loads(resp.read())

            releases = list(data.get("releases", {}).keys())
            if not releases:
                self.check_done.emit(current)
                return

            # Find highest dev version of the same base
            from packaging.version import Version

            cur_ver = Version(current)
            cur_base = f"{cur_ver.major}.{cur_ver.minor}.{cur_ver.micro}"

            candidates = []
            for v_str in releases:
                try:
                    v = Version(v_str)
                    base = f"{v.major}.{v.minor}.{v.micro}"
                    if base == cur_base and v.is_devrelease and v > cur_ver:
                        candidates.append(v)
                except Exception:  # noqa: BLE001
                    pass

            if not candidates:
                self.check_done.emit(current)
                return

            latest = max(candidates)
            # Silently upgrade
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--quiet", f"specsmith=={latest}"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0:
                self.updated.emit(str(latest))
            else:
                self.check_done.emit(current)

        except ImportError:
            # packaging not installed — skip
            self.check_done.emit("unknown")
        except Exception as e:  # noqa: BLE001
            self.error.emit(str(e))
