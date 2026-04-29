# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Keyword + (optional) semantic search over chat history (REQ-135).

The default backend is keyword-based: tokenises the query, scores each
turn by token overlap, returns top N. Hermetic, fast, no extra deps.

A ``--semantic`` mode is documented but only available when the optional
``[history-semantic]`` extra (``sentence-transformers`` + ``faiss-cpu``) is
installed. The CLI surfaces this as an opt-in flag and falls back to
keyword matching with a warning when the import fails.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class HistoryHit:
    session_id: str
    timestamp: str
    role: str
    text: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "role": self.role,
            "text": self.text,
            "score": round(self.score, 3),
        }


_WORD_RE = re.compile(r"[A-Za-z]{3,}")


def _tokenize(text: str) -> set[str]:
    return {w.lower() for w in _WORD_RE.findall(text)}


def _iter_turns(project_dir: Path) -> list[dict[str, Any]]:
    sessions_root = project_dir / ".specsmith" / "sessions"
    if not sessions_root.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for session_dir in sorted(sessions_root.iterdir()):
        if not session_dir.is_dir():
            continue
        for path in (session_dir / "turns.jsonl", session_dir / "events.jsonl"):
            if not path.is_file():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(obj, dict):
                    continue
                obj["_session_id"] = session_dir.name
                out.append(obj)
    return out


def search(
    query: str,
    project_dir: Path,
    *,
    limit: int = 10,
    semantic: bool = False,
) -> list[HistoryHit]:
    """Return up to ``limit`` ``HistoryHit`` rows matching ``query``."""
    if semantic:
        try:
            return _semantic_search(query, project_dir, limit=limit)
        except (ImportError, RuntimeError):
            pass  # fall through to keyword
    return _keyword_search(query, project_dir, limit=limit)


def _keyword_search(query: str, project_dir: Path, *, limit: int) -> list[HistoryHit]:
    q = _tokenize(query)
    if not q:
        return []
    hits: list[HistoryHit] = []
    for turn in _iter_turns(project_dir):
        text = str(turn.get("text") or turn.get("utterance") or "").strip()
        if not text:
            continue
        words = _tokenize(text)
        score = len(q & words) / max(len(q), 1)
        if score > 0:
            hits.append(
                HistoryHit(
                    session_id=str(turn.get("_session_id", "")),
                    timestamp=str(turn.get("timestamp", "")),
                    role=str(turn.get("role", "")),
                    text=text,
                    score=score,
                )
            )
    hits.sort(key=lambda h: -h.score)
    return hits[:limit]


def _semantic_search(query: str, project_dir: Path, *, limit: int) -> list[HistoryHit]:
    """Optional semantic search.

    Requires ``sentence-transformers``. If the import fails, raises
    ``ImportError`` so the caller falls back to keyword matching.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # noqa: BLE001
        raise ImportError("sentence-transformers not installed") from exc

    turns = _iter_turns(project_dir)
    if not turns:
        return []
    texts = [str(t.get("text") or t.get("utterance") or "").strip() for t in turns]
    keep = [(turn, text) for turn, text in zip(turns, texts, strict=False) if text]
    if not keep:
        return []
    model = SentenceTransformer("all-MiniLM-L6-v2")
    corpus = [text for _, text in keep]
    embs = model.encode(corpus + [query], convert_to_numpy=True)
    import numpy as np

    corpus_emb = embs[:-1]
    query_emb = embs[-1]
    norms = np.linalg.norm(corpus_emb, axis=1) * np.linalg.norm(query_emb)
    norms[norms == 0] = 1.0
    scores = (corpus_emb @ query_emb) / norms
    idxs = scores.argsort()[::-1][:limit]
    out: list[HistoryHit] = []
    for i in idxs:
        turn, text = keep[i]
        out.append(
            HistoryHit(
                session_id=str(turn.get("_session_id", "")),
                timestamp=str(turn.get("timestamp", "")),
                role=str(turn.get("role", "")),
                text=text,
                score=float(scores[i]),
            )
        )
    return out


__all__ = ["HistoryHit", "search"]
