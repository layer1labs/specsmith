"""Reject unexpected release-bootstrap worktree changes before CI stages them."""

import subprocess

ALLOWED = ("docs/", ".specsmith/requirements.json", ".specsmith/testcases.json")
status = subprocess.run(
    ["git", "status", "--porcelain=v1"], check=True, capture_output=True, text=True
).stdout.splitlines()
unexpected = [line for line in status if not line[3:].replace("\\", "/").startswith(ALLOWED)]
if unexpected:
    raise SystemExit("unexpected bootstrap files:\n" + "\n".join(unexpected))
