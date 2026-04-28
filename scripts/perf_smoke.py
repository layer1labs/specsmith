# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Performance smoke harness for specsmith preflight (REQ-124).

Generates a synthetic 1000-REQ ``REQUIREMENTS.md`` in a temp project,
runs ``specsmith preflight`` against it three times, and writes a
JSON baseline to ``.specsmith/perf/baseline.json``. The numbers are
informational only — CI does not gate on absolute timings.

Usage:
    py scripts/perf_smoke.py [--project-dir PATH]
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def _build_synthetic_project(root: Path, n_reqs: int = 1000) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / ".repo-index").mkdir(exist_ok=True)
    (root / ".repo-index" / "files.json").write_text(json.dumps({"files": []}), encoding="utf-8")
    lines = ["# Requirements\n"]
    for i in range(1, n_reqs + 1):
        lines.append(
            f"## REQ-{i:04d}\n"
            f"- **Component**: synthetic\n"
            f"- **Status**: Accepted\n"
            f"- **Description**: Synthetic requirement #{i} for perf smoke.\n\n"
        )
    (root / "REQUIREMENTS.md").write_text("".join(lines), encoding="utf-8")
    (root / "TESTS.md").write_text("# Tests\n", encoding="utf-8")


def _time_preflight(project_dir: Path, utterance: str) -> float:
    start = time.perf_counter()
    argv = [
        sys.executable,
        "-m",
        "specsmith.cli",
        "preflight",
        utterance,
        "--project-dir",
        str(project_dir),
    ]
    subprocess.run(argv, check=False, capture_output=True)  # noqa: S603
    return time.perf_counter() - start


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--project-dir",
        default="",
        help="Where to write baseline.json (default: cwd).",
    )
    parser.add_argument("--reqs", type=int, default=1000, help="Synthetic requirement count.")
    args = parser.parse_args()

    out_root = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()
    perf_dir = out_root / ".specsmith" / "perf"
    perf_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="specsmith-perf-") as tmp:
        synth = Path(tmp)
        _build_synthetic_project(synth, n_reqs=args.reqs)
        utterance = "add hello world to synthetic component"
        timings = [_time_preflight(synth, utterance) for _ in range(3)]

    baseline = {
        "n_reqs": args.reqs,
        "timings_seconds": [round(t, 4) for t in timings],
        "median_seconds": round(statistics.median(timings), 4),
        "min_seconds": round(min(timings), 4),
        "max_seconds": round(max(timings), 4),
    }
    out_path = perf_dir / "baseline.json"
    out_path.write_text(json.dumps(baseline, indent=2), encoding="utf-8")
    print(f"perf_smoke: wrote {out_path}")
    print(json.dumps(baseline, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
