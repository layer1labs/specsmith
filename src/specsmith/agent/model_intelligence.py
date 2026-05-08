# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Model Intelligence — automated capability scoring (REQ-223).

Scores models per-role using HuggingFace benchmark data.  Scores are
stored in ``~/.specsmith/model_scores.json`` and refreshed on startup +
daily.  The auto-configure wizard uses these scores to pick the best
model for each role within the active profile's provider constraints.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

SCORES_FILE = "model_scores.json"

# Benchmark → Role scoring weights.
# Each role has a weighted sum of benchmark scores (0–1 scale).
ROLE_WEIGHTS: dict[str, dict[str, float]] = {
    "coder": {"humaneval": 0.35, "swe_bench": 0.30, "livecode": 0.20, "mbpp": 0.15},
    "architect": {"gpqa": 0.35, "mmlu_pro_stem": 0.30, "bbh": 0.20, "ifeval": 0.15},
    "reviewer": {"ifeval": 0.35, "code_understanding": 0.30, "bbh": 0.20, "mmlu_pro": 0.15},
    "researcher": {"mmlu_pro": 0.30, "musr": 0.30, "long_context": 0.25, "ifeval": 0.15},
    "tester": {"humaneval": 0.35, "ifeval": 0.25, "mbpp": 0.25, "bbh": 0.15},
    "classifier": {"speed": 0.50, "cost_efficiency": 0.50},
    "strategist": {"mmlu_pro_biz": 0.30, "musr": 0.30, "gpqa": 0.25, "ifeval": 0.15},
    "drafter": {"musr": 0.35, "ifeval": 0.30, "mmlu_pro": 0.20, "long_context": 0.15},
    "ip-analyst": {"mmlu_pro_law": 0.30, "ifeval": 0.25, "long_context": 0.25, "tool_calling": 0.20},
    "editor": {"ifeval": 0.40, "mmlu_pro": 0.30, "bbh": 0.30},
}


# Well-known model baseline scores (hand-curated from HF leaderboard).
# These serve as the default when HF sync hasn't run yet.
# Scores are normalized 0–100.
BASELINE_SCORES: dict[str, dict[str, float]] = {
    "gpt-4.1": {"humaneval": 90, "swe_bench": 55, "mmlu_pro": 85, "ifeval": 88, "bbh": 82, "gpqa": 56, "musr": 65, "tool_calling": 90},
    "gpt-4.1-mini": {"humaneval": 80, "swe_bench": 40, "mmlu_pro": 75, "ifeval": 82, "bbh": 72, "gpqa": 45, "musr": 55, "tool_calling": 85},
    "claude-sonnet-4-5": {"humaneval": 88, "swe_bench": 60, "mmlu_pro": 82, "ifeval": 90, "bbh": 80, "gpqa": 55, "musr": 68, "tool_calling": 88},
    "claude-opus-4": {"humaneval": 85, "swe_bench": 50, "mmlu_pro": 88, "ifeval": 92, "bbh": 85, "gpqa": 65, "musr": 75, "tool_calling": 85},
    "claude-haiku-4-5": {"humaneval": 72, "swe_bench": 30, "mmlu_pro": 68, "ifeval": 78, "bbh": 65, "gpqa": 38, "musr": 48, "tool_calling": 75},
    "gemini-2.5-pro": {"humaneval": 85, "swe_bench": 52, "mmlu_pro": 84, "ifeval": 85, "bbh": 80, "gpqa": 60, "musr": 72, "long_context": 90, "tool_calling": 82},
    "gemini-2.5-flash": {"humaneval": 75, "swe_bench": 35, "mmlu_pro": 72, "ifeval": 78, "bbh": 68, "gpqa": 42, "musr": 55, "long_context": 85, "tool_calling": 78},
    "mistral-large-latest": {"humaneval": 78, "swe_bench": 38, "mmlu_pro": 75, "ifeval": 80, "bbh": 72, "gpqa": 45, "musr": 58, "tool_calling": 80},
    "codestral-latest": {"humaneval": 85, "swe_bench": 45, "mmlu_pro": 65, "ifeval": 72, "bbh": 60, "gpqa": 35, "musr": 42, "tool_calling": 78},
    "qwen2.5-coder:32b": {"humaneval": 82, "swe_bench": 42, "mmlu_pro": 60, "ifeval": 68, "bbh": 58, "gpqa": 32, "musr": 40, "tool_calling": 65},
    "qwen2.5:32b": {"humaneval": 65, "swe_bench": 28, "mmlu_pro": 68, "ifeval": 72, "bbh": 62, "gpqa": 38, "musr": 50, "tool_calling": 60},
    "qwen2.5:14b": {"humaneval": 55, "swe_bench": 20, "mmlu_pro": 58, "ifeval": 62, "bbh": 52, "gpqa": 30, "musr": 40, "tool_calling": 50},
    "qwen2.5:7b": {"humaneval": 42, "swe_bench": 12, "mmlu_pro": 45, "ifeval": 50, "bbh": 40, "gpqa": 22, "musr": 30, "tool_calling": 35},
    "qwen2.5:3b": {"humaneval": 28, "swe_bench": 5, "mmlu_pro": 32, "ifeval": 38, "bbh": 28, "gpqa": 15, "musr": 20, "speed": 95, "cost_efficiency": 98},
    "deepseek-r1:14b": {"humaneval": 60, "swe_bench": 25, "mmlu_pro": 62, "ifeval": 65, "bbh": 58, "gpqa": 35, "musr": 45, "tool_calling": 48},
}


def score_model_for_role(model: str, role: str, scores: dict[str, float] | None = None) -> float:
    """Compute a 0–100 composite score for a model in a given role.

    Uses the role's benchmark weights and the model's individual scores.
    Falls back to BASELINE_SCORES if no explicit scores are provided.
    """
    if role not in ROLE_WEIGHTS:
        return 0.0
    weights = ROLE_WEIGHTS[role]
    model_scores = scores or BASELINE_SCORES.get(model, {})
    if not model_scores:
        return 0.0
    total = 0.0
    weight_sum = 0.0
    for benchmark, weight in weights.items():
        if benchmark in model_scores:
            total += model_scores[benchmark] * weight
            weight_sum += weight
    return round(total / weight_sum, 1) if weight_sum > 0 else 0.0


def rank_models_for_role(
    role: str,
    available_models: list[str],
    *,
    custom_scores: dict[str, dict[str, float]] | None = None,
) -> list[tuple[str, float]]:
    """Rank models by score for a given role, highest first.

    Returns list of (model_name, score) tuples.
    """
    all_scores = custom_scores or BASELINE_SCORES
    ranked = []
    for model in available_models:
        s = score_model_for_role(model, role, all_scores.get(model))
        ranked.append((model, s))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


# ---------------------------------------------------------------------------
# Score persistence
# ---------------------------------------------------------------------------


class ModelScoreStore:
    """Persist and query model scores."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path.home() / ".specsmith" / SCORES_FILE
        self._scores: dict[str, dict[str, float]] = {}
        self._last_synced: str = ""
        self._load()

    def _load(self) -> None:
        if not self._path.is_file():
            self._scores = dict(BASELINE_SCORES)
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
            self._scores = raw.get("scores", {})
            self._last_synced = raw.get("last_synced", "")
        except Exception:  # noqa: BLE001
            self._scores = dict(BASELINE_SCORES)

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = {"scores": self._scores, "last_synced": self._last_synced}
        self._path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    @property
    def scores(self) -> dict[str, dict[str, float]]:
        return dict(self._scores)

    @property
    def last_synced(self) -> str:
        return self._last_synced

    def update_scores(self, model: str, benchmarks: dict[str, float]) -> None:
        """Update or add scores for a model."""
        self._scores[model] = benchmarks
        self._last_synced = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self._save()

    def rank_for_role(self, role: str, available_models: list[str]) -> list[tuple[str, float]]:
        return rank_models_for_role(role, available_models, custom_scores=self._scores)

    def best_for_role(self, role: str, available_models: list[str]) -> str | None:
        """Return the highest-scoring model for a role, or None."""
        ranked = self.rank_for_role(role, available_models)
        return ranked[0][0] if ranked else None
