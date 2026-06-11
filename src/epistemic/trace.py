# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Trace Vault — STP-inspired cryptographic decision sealing.

Part of the standalone ``epistemic`` library. Zero external dependencies.

    from epistemic.trace import TraceVault, SealType, SealRecord
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path


class SealType(str, Enum):
    """Type of a SealRecord."""

    DECISION = "decision"
    MILESTONE = "milestone"
    AUDIT_GATE = "audit-gate"
    LOGIC_KNOT = "logic-knot"
    STRESS_TEST = "stress-test"
    EPISTEMIC = "epistemic"


@dataclass
class SealRecord:
    """An immutable, cryptographically chained record of a significant event."""

    seal_id: str
    seal_type: str
    description: str
    content_hash: str
    prev_hash: str
    entry_hash: str
    timestamp: str
    author: str = "epistemic"
    artifact_ids: list[str] | None = None

    def to_dict(self) -> dict[str, object]:
        d = asdict(self)
        if d["artifact_ids"] is None:
            d["artifact_ids"] = []
        return d

    @classmethod
    def from_dict(cls, d: dict[str, object]) -> SealRecord:
        return cls(
            seal_id=str(d["seal_id"]),
            seal_type=str(d["seal_type"]),
            description=str(d["description"]),
            content_hash=str(d["content_hash"]),
            prev_hash=str(d["prev_hash"]),
            entry_hash=str(d["entry_hash"]),
            timestamp=str(d["timestamp"]),
            author=str(d.get("author", "epistemic")),
            artifact_ids=list(d.get("artifact_ids", [])),  # type: ignore[arg-type]
        )


_GENESIS_HASH = "0" * 64


class TraceVault:
    """Append-only, cryptographically chained store of SealRecords.

    Stores seals in a newline-delimited JSON file. Each seal chains to the
    previous via SHA-256 hashes, making the sequence tamper-evident.

        from epistemic.trace import TraceVault, SealType
        from pathlib import Path

        vault = TraceVault(Path(".epistemic"))
        seal = vault.seal(
            seal_type=SealType.DECISION,
            description="Adopted logosyllabic hypothesis for Indus corpus",
            artifact_ids=["HYP-IND-001"],
        )
        valid, errors = vault.verify()
    """

    TRACE_FILE = "trace.jsonl"

    def __init__(self, root: Path, filename: str = "trace.jsonl") -> None:
        self._root = root
        self._path = root / filename

    def seal(
        self,
        seal_type: SealType | str,
        description: str,
        author: str = "epistemic",
        artifact_ids: list[str] | None = None,
    ) -> SealRecord:
        """Create and append a new SealRecord."""
        records = self._load()
        seq = len(records) + 1
        seal_id = f"SEAL-{seq:04d}"
        prev_hash = records[-1].entry_hash if records else _GENESIS_HASH
        timestamp = datetime.now(timezone.utc).isoformat()

        seal_type_str = seal_type.value if isinstance(seal_type, SealType) else str(seal_type)
        content = f"{seal_id}:{seal_type_str}:{description}:{timestamp}"
        content_hash = _sha256(content)
        entry_hash = _sha256(f"{content_hash}:{prev_hash}")

        record = SealRecord(
            seal_id=seal_id,
            seal_type=seal_type_str,
            description=description,
            content_hash=content_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
            timestamp=timestamp,
            author=author,
            artifact_ids=artifact_ids or [],
        )
        self._append(record)
        return record

    def verify(self) -> tuple[bool, list[str]]:
        """Verify cryptographic integrity of the full chain.

        Checks three things per record:
        1. content_hash matches recomputed hash of (seal_id+type+description+timestamp)
        2. entry_hash matches recomputed hash of (content_hash+prev_hash)
        3. prev_hash matches the previous record's entry_hash
        """
        records = self._load()
        if not records:
            return True, []
        errors: list[str] = []
        prev_hash = _GENESIS_HASH
        for rec in records:
            # Recompute content_hash from stored fields
            expected_content = f"{rec.seal_id}:{rec.seal_type}:{rec.description}:{rec.timestamp}"
            expected_content_hash = _sha256(expected_content)
            if rec.content_hash != expected_content_hash:
                errors.append(
                    f"{rec.seal_id}: content_hash invalid — description or metadata tampered"
                )
            # Verify entry_hash
            expected_entry = _sha256(f"{rec.content_hash}:{rec.prev_hash}")
            if rec.entry_hash != expected_entry:
                errors.append(
                    f"{rec.seal_id}: entry_hash invalid — record may have been tampered with"
                )
            # Verify chain link
            if rec.prev_hash != prev_hash:
                errors.append(f"{rec.seal_id}: prev_hash mismatch")
            prev_hash = rec.entry_hash
        return len(errors) == 0, errors

    def list_seals(self, seal_type: str | None = None, limit: int = 50) -> list[SealRecord]:
        records = self._load()
        if seal_type:
            records = [r for r in records if r.seal_type == seal_type]
        return list(reversed(records[-limit:]))

    def get_latest(self) -> SealRecord | None:
        records = self._load()
        return records[-1] if records else None

    def count(self) -> int:
        return len(self._load())

    def format_log(self, limit: int = 20) -> str:
        records = list(reversed(self._load()[-limit:]))
        if not records:
            return "Trace vault is empty."
        lines = [f"Trace Vault — {self.count()} total seals", "=" * 50]
        for rec in records:
            lines.append(f"  {rec.seal_id}  [{rec.seal_type:12s}]  {rec.timestamp[:19]}Z")
            lines.append(f"    {rec.description[:100]}")
            if rec.artifact_ids:
                lines.append(f"    Artifacts: {', '.join(rec.artifact_ids)}")
            lines.append(f"    Hash: {rec.entry_hash[:16]}...")
        return "\n".join(lines)

    def _load(self) -> list[SealRecord]:
        if not self._path.exists():
            return []
        records: list[SealRecord] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                records.append(SealRecord.from_dict(json.loads(line)))
            except (json.JSONDecodeError, KeyError):
                continue
        return records

    def _append(self, record: SealRecord) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict()) + "\n")


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


__all__ = ["TraceVault", "SealRecord", "SealType"]
