# ESDB — Quick Start

This guide walks through the core chronomemory workflow: writing beliefs, querying
them, verifying integrity, and migrating from legacy JSON.

## 1. Open a store

```python
from chronomemory import ChronoStore, ChronoRecord

# Context manager — auto-opens and closes
with ChronoStore("/path/to/project") as store:
    ...

# Or manual lifecycle
store = ChronoStore("/path/to/project")
store.open()
# ... do work ...
store.close()
```

The store writes all data to `/path/to/project/.chronomemory/events.wal`.

## 2. Write a record

Every record requires an `id`. All other fields have safe defaults.

```python
with ChronoStore("/path/to/project") as store:
    store.upsert(ChronoRecord(
        id="FACT-001",
        kind="fact",
        label="Water freezes at 0°C at standard pressure",
        source_type="observed",
        confidence=1.0,
        evidence=["NIST", "textbook-chemistry"],
    ))
```

`upsert()` is idempotent by `id` — reinserting the same record updates it.

## 3. Read records

```python
with ChronoStore("/path/to/project") as store:
    # All active records
    all_records = store.query()

    # By kind
    facts = store.query(kind="fact")
    requirements = store.query(kind="requirement")

    # Confidence-filtered (for RAG injection) — H18
    rag_context = store.query(rag_filter=True)  # confidence >= 0.6

    # High-confidence only
    high_conf = store.query(min_confidence=0.9)

    # Single record
    rec = store.get("FACT-001")
    if rec:
        print(rec.label, rec.confidence)
```

## 4. Delete (tombstone) a record

```python
with ChronoStore("/path/to/project") as store:
    store.delete("FACT-001")
    # Record still exists in WAL with status="tombstone"
    # It is excluded from query() by default
    rec = store.get("FACT-001")  # still returns the record
    print(rec.status)  # "tombstone"
```

## 5. Verify chain integrity

```python
with ChronoStore("/path/to/project") as store:
    valid = store.chain_valid()
    print(f"Chain valid: {valid}")  # True if untampered
```

If `chain_valid()` returns `False`, the WAL has been modified after the fact.

## 6. Compact the WAL

After many writes, compact the WAL to keep it small:

```python
with ChronoStore("/path/to/project") as store:
    n = store.compact()
    print(f"Compacted {n} events → snapshot + 1-line WAL")
```

## 7. Backup

```python
with ChronoStore("/path/to/project") as store:
    backup_path = store.backup()
    print(f"Backup at: {backup_path}")
```

## 8. Write a hypothesis

Use `is_hypothesis=True` for tentative beliefs:

```python
store.upsert(ChronoRecord(
    id="HYP-001",
    kind="hypothesis",
    label="Model generalization gap < 5% of Bayes-optimal",
    is_hypothesis=True,
    confidence=0.75,
    source_type="inferred",
    evidence=["REQ-NN-006", "paper §4.2"],
))
```

After running the experiment, update the hypothesis:

```python
rec = store.get("HYP-001")
rec.is_hypothesis = False
rec.source_type = "observed"
rec.confidence = 1.0 if confirmed else 0.0
rec.evidence.append("bench-B-seed42: nll_gap=0.031")
store.upsert(rec)
```

## 9. Migrate from .specsmith/ JSON

If your project has existing `requirements.json` / `testcases.json`:

```python
from pathlib import Path

with ChronoStore("/path/to/project") as store:
    counts = store.migrate_from_json(Path("/path/to/project/.specsmith"))
    print(counts)  # {'requirements': 12, 'testcases': 10, 'skipped': 0}
```

Or via CLI: `specsmith esdb migrate` (requires specsmith ≥ 0.13.0).

## 10. Use the bridge adapter

`EsdbBridge` delegates to `ChronoStore` when a WAL exists, and falls back to
reading `.specsmith/*.json` when it doesn't:

```python
from chronomemory import EsdbBridge

bridge = EsdbBridge(project_dir="/path/to/project")

# Status check
print(bridge.status().to_dict())

# Read requirements (from ESDB or JSON fallback)
reqs = bridge.requirements()
tests = bridge.testcases()
```

## File layout

After running the above examples, your project directory contains:

```
/path/to/project/
  .chronomemory/
    events.wal        ← NDJSON, SHA-256 chained
    snapshot.json     ← materialized state (every 50 events)
    backup/
      20260518T120000/  ← timestamped backup
```
