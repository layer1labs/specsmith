# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Explicit opt-in local retrieval index (RAG foundation)."""

from __future__ import annotations

import json
import re
from pathlib import Path

_INDEX_PATH = Path(".specsmith") / "retrieval-index.json"
_TEXT_EXTS = {
    ".md",
    ".txt",
    ".py",
    ".ts",
    ".js",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".java",
    ".sh",
    ".ps1",
    ".cmd",
}
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".mypy_cache"}


#: Infrastructure record kinds excluded from the RAG index (critical rule §18).
#: Mirrors chronomemory ``query.what_is_known()`` so the free SQLite backend
#: produces the same retrieval context as the commercial ChronoStore (REQ-422).
_RAG_EXCLUDE_KINDS = frozenset(
    {
        "edge",
        "rollback_event",
        "token_metric",
        "skill_run",
        "efficiency_metric",
        "context_usage",
    },
)


def build_index(root: Path, *, include_ledger: bool = False, external: str = "") -> str:
    """Build or refresh the local retrieval index.

    H18 (RAG retrieval filtering): only records with confidence >= 0.6 are
    included in the retrieval context. REQ-422: parity across backends — the
    ChronoStore WAL is used when present, otherwise the free SQLite ESDB backend
    supplies the same governance knowledge so RAG works without commercial deps.
    """
    entries: list[dict[str, str]] = []

    # H18: inject high-confidence ESDB records as retrieval context.
    # Infrastructure records (see _RAG_EXCLUDE_KINDS) are excluded — rule §18.
    wal = root / ".chronomemory" / "events.wal"
    if wal.exists():
        # ChronoStore branch (commercial backend). Use query.what_is_known()
        # so infrastructure records are excluded from the RAG index.
        try:
            from chronomemory import ChronoStore
            from chronomemory import query as _cm_query

            with ChronoStore(root) as store:
                for rec in _cm_query.what_is_known(store):
                    if rec.data:
                        content = (
                            f"[{rec.kind.upper()} {rec.id}] {rec.label}\n"
                            + str(rec.data.get("description", rec.data.get("title", "")))[:500]
                        )
                        entries.append(
                            {
                                "path": f".chronomemory/{rec.kind}/{rec.id}",
                                "content": content,
                                "source_type": rec.source_type,
                                "confidence": str(rec.confidence),
                            },
                        )
        except Exception:  # noqa: BLE001
            pass  # ChronoStore read failure is non-fatal for RAG
    else:
        # SQLite parity branch (free default backend) — REQ-422. Inject the same
        # high-confidence governance knowledge via SqliteStore.query(rag_filter)
        # (confidence >= 0.6, active only), excluding infrastructure kinds.
        sqlite_path = root / ".specsmith" / "esdb.sqlite3"
        if sqlite_path.exists():
            try:
                from specsmith.esdb import SqliteStore

                with SqliteStore(root) as store:
                    for rec in store.query(rag_filter=True):
                        if rec.kind in _RAG_EXCLUDE_KINDS or not rec.data:
                            continue
                        content = (
                            f"[{rec.kind.upper()} {rec.id}] {rec.label}\n"
                            + str(rec.data.get("description", rec.data.get("title", "")))[:500]
                        )
                        entries.append(
                            {
                                "path": f"esdb/{rec.kind}/{rec.id}",
                                "content": content,
                                "source_type": str(rec.data.get("source_type", "observed")),
                                "confidence": str(rec.confidence),
                            },
                        )
            except Exception:  # noqa: BLE001
                pass  # SQLite read failure is non-fatal for RAG
    candidates: list[Path] = []

    for rel in ["AGENTS.md", "docs/REQUIREMENTS.md", "docs/ARCHITECTURE.md", "docs/TESTS.md"]:
        fp = root / rel
        if fp.exists():
            candidates.append(fp)
    if include_ledger:
        for rel in ["LEDGER.md", "docs/LEDGER.md"]:
            fp = root / rel
            if fp.exists():
                candidates.append(fp)

    ext_path = Path(external).resolve() if external else None
    if ext_path and ext_path.exists():
        if ext_path.is_file():
            candidates.append(ext_path)
        else:
            for fp in ext_path.rglob("*"):
                if fp.is_file() and fp.suffix.lower() in _TEXT_EXTS:
                    candidates.append(fp)

    for src_dir in [root / "src", root / "client", root / "server", root / "shared"]:
        if not src_dir.exists():
            continue
        for fp in src_dir.rglob("*"):
            if (
                fp.is_file()
                and fp.suffix.lower() in _TEXT_EXTS
                and not any(part in _SKIP_DIRS for part in fp.parts)
            ):
                candidates.append(fp)

    for fp in sorted(set(candidates)):
        try:
            text = fp.read_text(encoding="utf-8", errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        if not text.strip():
            continue
        entries.append(
            {
                "path": str(fp.relative_to(root)) if fp.is_relative_to(root) else str(fp),
                "content": text[:12000],
            },
        )

    index_path = root / _INDEX_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps({"entries": entries}, indent=2), encoding="utf-8")
    return f"Indexed {len(entries)} file(s) into {index_path.relative_to(root)}"


def search_index(root: Path, query: str, *, limit: int = 5) -> str:
    """Search the local retrieval index with a simple keyword score."""
    index_path = root / _INDEX_PATH
    if not index_path.exists():
        return "[NOT INDEXED] Run `specsmith index` first."

    data = json.loads(index_path.read_text(encoding="utf-8"))
    entries = data.get("entries", [])
    tokens = [t for t in re.findall(r"[a-zA-Z0-9_\\-]+", query.lower()) if len(t) > 1]
    if not tokens:
        return "[ERROR] Query must include at least one keyword."

    scored: list[tuple[int, dict[str, str]]] = []
    for entry in entries:
        hay = f"{entry.get('path', '')}\n{entry.get('content', '')}".lower()
        score = sum(hay.count(tok) for tok in tokens)
        if score > 0:
            scored.append((score, entry))

    if not scored:
        return f"No indexed matches for '{query}'."

    scored.sort(key=lambda item: (-item[0], item[1].get("path", "")))
    lines = [f"Top {min(limit, len(scored))} result(s) for '{query}':"]
    for score, entry in scored[:limit]:
        content = entry.get("content", "").strip().replace("\r\n", "\n")
        preview = "\n".join(content.splitlines()[:8])
        lines.append(f"\n[{score}] {entry.get('path', '')}\n{preview}")
    return "\n".join(lines)
