# ESDB API — ChronoStore (ChronoMemory backend)

Per-project WAL-based Epistemic State Database.
Terminology note: ChronoStore is the backend engine/class provided by the ChronoMemory package.

```python
from chronomemory import ChronoStore
```

## Constructor

```python
ChronoStore(project_root: str | Path, *, recursion_depth: int = 0)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `project_root` | `str \| Path` | required | Project directory. The `.chronomemory/` subdirectory is created here. |
| `recursion_depth` | `int` | `0` | OEA H16 value stamped on every upserted record. `0` = human-initiated. |

## Context manager

```python
with ChronoStore("/path/to/project") as store:
    store.upsert(...)
    # store.close() called automatically on __exit__
```

---

## Lifecycle methods

### `open() → ChronoStore`

Load the snapshot and replay the WAL tail into memory. Returns `self` for chaining.

The store auto-opens on the first method call if not already open.

### `close() → None`

Write snapshot if `events_since_snapshot >= 50`, then mark store as closed.

---

## Write methods

### `upsert(record: ChronoRecord) → WalEvent`

Persist an upsert event to the WAL and update in-memory state.

- Idempotent by `id`: reinserting the same ID overwrites in memory; WAL retains all events.
- Stamps `record.recursion_depth = self.recursion_depth` (H16).
- Triggers snapshot write every 50 events.
- Returns the `WalEvent` written to the WAL.

```python
event = store.upsert(ChronoRecord(id="X", label="a fact"))
print(event.hash)  # SHA-256 of this WAL event
```

### `delete(record_id: str) → WalEvent`

Tombstone a record. Status is set to `"tombstone"` in memory and a delete event is
appended to the WAL. The record is never physically removed.

```python
store.delete("FACT-001")
rec = store.get("FACT-001")   # still present
print(rec.status)              # "tombstone"
```

---

## Read methods

### `query(*, kind=None, status="active", rag_filter=False, min_confidence=0.0) → list[ChronoRecord]`

Return records matching the given filters.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `kind` | `str \| None` | `None` | Filter by kind (`"fact"`, `"requirement"`, etc.). `None` = all kinds. |
| `status` | `str` | `"active"` | Filter by status. Pass `""` to include all statuses. |
| `rag_filter` | `bool` | `False` | Apply H18 confidence filter (`confidence >= 0.6`). |
| `min_confidence` | `float` | `0.0` | Minimum confidence threshold. |

```python
# All active records
all_recs = store.query()

# RAG-safe context (H18)
context = store.query(rag_filter=True)

# High-confidence requirements only
reqs = store.query(kind="requirement", min_confidence=0.9)

# Include tombstones
including_deleted = store.query(status="")
```

### `get(record_id: str) → ChronoRecord | None`

Return a single record by ID, or `None` if not found. Returns tombstoned records.

### `record_count() → int`

Count of active (non-tombstoned) records.

### `wal_seq() → int`

Current WAL sequence number. Increments by 1 for every `upsert()` or `delete()`.

---

## Integrity methods

### `chain_valid() → bool`

Recompute the full SHA-256 hash chain from disk and return `True` iff every link is unbroken.

- Returns `True` on an empty store.
- Returns `False` if any event has been modified, deleted, or reordered.
- Reads directly from `events.wal`; does not use the in-memory state.

```python
if not store.chain_valid():
    raise RuntimeError("WAL has been tampered with!")
```

---

## Maintenance methods

### `compact() → int`

Write a fresh snapshot and truncate the WAL to a single compact sentinel.

Returns the number of events that were in the WAL before compaction.

After compacting:
- `events.wal` contains 1 line (the compact sentinel)
- `snapshot.json` contains the full materialized state
- `chain_valid()` remains `True`
- New upserts extend the chain from the sentinel

```python
n = store.compact()
print(f"Compacted {n} events")
```

### `backup() → Path`

Copy `.chronomemory/` to a timestamped backup directory.

```python
backup_path = store.backup()
print(backup_path)  # e.g. .chronomemory/backup/20260518T170000/
```

### `replay(*, from_seq: int = 0) → list[WalEvent]`

Return WAL events with `seq >= from_seq`. Useful for incremental synchronization.

### `export_records() → list[dict]`

Return all active records as plain dicts (suitable for JSON export).

---

## Migration

### `migrate_from_json(specsmith_dir: Path) → dict[str, int]`

Import `requirements.json` and `testcases.json` from a `.specsmith/` directory into the WAL.

- Tags all records with `source_type="observed"` (H19).
- Idempotent: records whose `id`, `label`, and `status` match existing records are skipped.

Returns `{"requirements": N, "testcases": N, "skipped": N}`.

```python
from pathlib import Path
counts = store.migrate_from_json(Path(".specsmith"))
print(counts)  # {'requirements': 12, 'testcases': 8, 'skipped': 0}
```

---

## Thread safety

`ChronoStore` is safe to use from **a single thread only**. For concurrent reads, create
a separate instance per reader (each `open()` replays from disk independently). Do not
share a single instance across threads.
