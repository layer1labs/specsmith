# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Dynamic agent / model routing for the Nexus orchestrator (REQ-122).

The orchestrator asks ``choose_tier`` which model tier should run a given
task. Three tiers are recognized:

* ``coder``  - the local `l1-nexus` Qwen-Coder server (default).
* ``heavy``  - a larger reasoning model for governance / architecture work.
* ``fast``   - a quick lightweight model for read-only asks and summaries.

The default mapping is overridable per project via
``.specsmith/config.yml``::

    routing:
      change: coder
      release: heavy
      destructive: heavy
      read_only_ask: fast
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

Tier = Literal["coder", "heavy", "fast"]

DEFAULT_MAPPING: dict[str, Tier] = {
    "read_only_ask": "fast",
    "change": "coder",
    "release": "heavy",
    "destructive": "heavy",
}


def choose_tier(
    intent: str,
    *,
    project_dir: Path | None = None,
    retry_count: int = 0,
) -> Tier:
    """Pick a model tier for ``intent``.

    Repeated retries escalate from ``coder`` to ``heavy`` so a stuck task
    gets a more capable model on the next try (Phase-3 behaviour from the
    plan).
    """
    mapping = dict(DEFAULT_MAPPING)
    if project_dir is not None:
        mapping.update(_load_routing_overrides(project_dir))
    tier: Tier = mapping.get(intent, "coder")
    if retry_count >= 2 and tier == "coder":
        tier = "heavy"
    return tier


def _load_routing_overrides(project_dir: Path) -> dict[str, Tier]:
    cfg = Path(project_dir) / ".specsmith" / "config.yml"
    if not cfg.is_file():
        return {}
    try:
        import yaml

        raw = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return {}
    section = raw.get("routing") if isinstance(raw, dict) else None
    if not isinstance(section, dict):
        return {}
    out: dict[str, Tier] = {}
    for key, val in section.items():
        if isinstance(val, str) and val in ("coder", "heavy", "fast"):
            out[str(key)] = val  # type: ignore[assignment]
    return out


__all__ = ["DEFAULT_MAPPING", "Tier", "choose_tier"]
