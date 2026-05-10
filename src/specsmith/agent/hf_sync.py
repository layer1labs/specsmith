# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""HuggingFace Open LLM Leaderboard sync for model intelligence (REQ-223).

Fetches benchmark scores from the HuggingFace API and populates
`.specsmith/model_scores.json` so that `rank_models_for_role()` uses
real data instead of hardcoded baselines.

Usage:
    from specsmith.agent.hf_sync import sync_scores
    results = sync_scores()  # returns dict of model_id -> {benchmark: score}
"""

from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path
from typing import Any

# HF Inference API endpoint for model info
HF_API_BASE = "https://huggingface.co/api"

# Models we track (subset of popular models with known benchmark data)
TRACKED_MODELS: list[str] = [
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4o",
    "gpt-4o-mini",
    "claude-sonnet-4-20250514",
    "claude-3.5-sonnet",
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "mistralai/Mistral-Large-Latest",
    "meta-llama/Llama-3.3-70B-Instruct",
    "deepseek-ai/DeepSeek-V3",
]

# Default scores file path (relative to project root)
SCORES_FILENAME = "model_scores.json"


def _scores_path(project_dir: str | Path = ".") -> Path:
    return Path(project_dir).resolve() / ".specsmith" / SCORES_FILENAME


def load_cached_scores(project_dir: str | Path = ".") -> dict[str, Any]:
    """Load cached model scores from disk."""
    path = _scores_path(project_dir)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_scores(scores: dict[str, Any], project_dir: str | Path = ".") -> None:
    """Persist model scores to disk."""
    path = _scores_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "synced_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "models": scores,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_hf_model_info(model_id: str, timeout: int = 10) -> dict[str, Any]:
    """Fetch model metadata from HuggingFace API.

    Returns a dict with model card data. On failure returns empty dict.
    """
    url = f"{HF_API_BASE}/models/{model_id}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            return json.loads(resp.read())
    except Exception:  # noqa: BLE001
        return {}


def _extract_benchmark_scores(model_info: dict[str, Any]) -> dict[str, float]:
    """Extract benchmark scores from HF model card metadata.

    Looks for eval_results in the model card data. Returns a dict of
    benchmark_name -> score.
    """
    scores: dict[str, float] = {}
    # HF model cards store eval results in cardData.eval_results
    card_data = model_info.get("cardData", {}) or {}
    eval_results = card_data.get("eval_results", []) or []
    for result in eval_results:
        if not isinstance(result, dict):
            continue
        dataset = result.get("dataset", {})
        name = dataset.get("name", "") if isinstance(dataset, dict) else str(dataset)
        metrics = result.get("metrics", []) or []
        for metric in metrics:
            if isinstance(metric, dict):
                metric_name = metric.get("name", "")
                value = metric.get("value")
                if metric_name and value is not None:
                    try:
                        key = f"{name}/{metric_name}" if name else metric_name
                        scores[key] = float(value)
                    except (TypeError, ValueError):
                        continue
    return scores


def sync_scores(
    project_dir: str | Path = ".",
    models: list[str] | None = None,
    timeout: int = 10,
) -> dict[str, dict[str, float]]:
    """Sync model scores from HuggingFace.

    For HF-hosted models, fetches real benchmark data from model cards.
    For proprietary models (GPT, Claude, Gemini), uses curated baselines.

    Returns dict of model_id -> {benchmark: score}.
    """
    from specsmith.agent.model_intelligence import BASELINE_SCORES

    target_models = models or TRACKED_MODELS
    all_scores: dict[str, dict[str, float]] = {}

    for model_id in target_models:
        # For non-HF models, use baseline scores
        if "/" not in model_id:
            baseline = BASELINE_SCORES.get(model_id)
            if baseline:
                all_scores[model_id] = {"baseline_composite": baseline}
            continue

        # For HF models, try to fetch real data
        info = fetch_hf_model_info(model_id, timeout=timeout)
        if info:
            benchmarks = _extract_benchmark_scores(info)
            if benchmarks:
                all_scores[model_id] = benchmarks
                continue

        # Fallback to baseline
        baseline = BASELINE_SCORES.get(model_id)
        if baseline:
            all_scores[model_id] = {"baseline_composite": baseline}

    save_scores(all_scores, project_dir)
    return all_scores


def is_stale(project_dir: str | Path = ".", max_age_hours: int = 24) -> bool:
    """Check if cached scores are older than max_age_hours."""
    cached = load_cached_scores(project_dir)
    synced_at = cached.get("synced_at", "")
    if not synced_at:
        return True
    try:
        from datetime import datetime, timezone

        synced = datetime.fromisoformat(synced_at.replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - synced
        return age.total_seconds() > max_age_hours * 3600
    except (ValueError, TypeError):
        return True


__all__ = [
    "fetch_hf_model_info",
    "is_stale",
    "load_cached_scores",
    "save_scores",
    "sync_scores",
]
