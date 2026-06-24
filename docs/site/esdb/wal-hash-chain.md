# ESDB — WAL and Hash Chain

chronomemory uses a **Write-Ahead Log (WAL)** with a **SHA-256 hash chain** to make
epistemic state tamper-evident and replayable.

## What is the WAL?

The WAL is the ground truth for a chronomemory store. It is an append-only NDJSON file
(`events.wal`) where every write is recorded as a complete, independently-parseable JSON line.

```
.chronomemory/
  events.wal       ← the WAL (NDJSON, SHA-256 chained)
  snapshot.json    ← materialized snapshot (every 50 events)
```

No data is ever deleted from the WAL. A `delete()` call writes a new WAL event with
`op="delete"` — the original upsert remains. This is the **tombstone invariant**:
records can be marked inactive but never physically removed.

## NDJSON format

Every line in `events.wal` is a complete JSON object:

```json
{"seq": 1, "ts": "2026-05-18T17:00:00Z", "op": "upsert", "record_id": "FACT-001", "record": {...}, "prev_hash": "", "hash": "a3f2...", "recursion_depth": 0}
{"seq": 2, "ts": "2026-05-18T17:00:01Z", "op": "upsert", "record_id": "FACT-002", "record": {...}, "prev_hash": "a3f2...", "hash": "b7c1...", "recursion_depth": 0}
```

This format is:

- **Human-readable**: `grep`, `jq`, `cat` work without special tooling
- **Cross-compatible**: any project using chronomemory writes the same format
- **Robust**: a single corrupted line doesn't prevent parsing of other lines

## Hash chain

Each event links to the previous via a cryptographic chain:

```
Genesis:  prev_hash = ""
Event 1:  hash = SHA256("" + canonical_json(event1_payload))
Event 2:  hash = SHA256(event1.hash + canonical_json(event2_payload))
Event N:  hash = SHA256(event_N-1.hash + canonical_json(eventN_payload))
```

The hash input uses canonical JSON — keys sorted alphabetically, no whitespace.
This ensures the hash is deterministic regardless of Python's dict ordering.

### Why is this useful?

If anyone modifies a past event (even a single character), every subsequent hash becomes
invalid. `chain_valid()` recomputes the entire chain from scratch and returns `False` if
any link is broken.

```python
store = ChronoStore(project)
assert store.chain_valid()
# The WAL on disk has not been tampered with
```

## Snapshot + tail replay

Reading an entire WAL on every startup is O(n) in the total WAL size. chronomemory
solves this with **snapshot + tail replay**:

1. Every 50 events, the store writes `snapshot.json` — the full materialized in-memory state.
2. On `open()`, the store loads the snapshot (fast) and replays only the WAL events with
   `seq > snapshot.seq` (the "tail").

```
WAL:     [1][2]...[50] [51][52][53][54][55]
Snapshot:           ↑ written here (seq=50)
Replay:                 ↑ only these 5 events
```

**Corruption recovery**: if `snapshot.json` is corrupt, the store discards it and replays
the full WAL. You never lose data — only startup time.

## Atomic writes

Every `upsert()` and `delete()` uses an atomic O(1) append:

1. Open `events.wal` in append mode
2. Write the new JSON line + newline
3. `fsync`

If the process crashes mid-write, the partial line is detected and skipped on next open
(NDJSON lines must be complete valid JSON to be parsed). The WAL is never in a partial state.

## Compact operation

After many writes, use `compact()` to truncate the WAL:

```python
with ChronoStore(project) as store:
    n = store.compact()
    # events.wal now contains: [compact-sentinel]
    # snapshot.json contains full state
```

After compacting, the WAL starts a fresh hash chain. New events chain from the compact
sentinel. `chain_valid()` remains `True` across compact boundaries.

## WAL event fields

| Field | Type | Description |
|-------|------|-------------|
| `seq` | int | Monotonically-increasing sequence number |
| `ts` | str | ISO-8601 UTC timestamp |
| `op` | str | `upsert` \| `delete` \| `compact` \| `migrate` |
| `record_id` | str | ID of the affected record |
| `record` | dict | Full record payload (for `upsert`/`migrate`) |
| `prev_hash` | str | SHA-256 hex of the previous event |
| `hash` | str | SHA-256 hex of this event |
| `recursion_depth` | int | Agent recursion depth (H16) |

## Inspecting the WAL

Because the WAL is NDJSON, standard tools work:

```bash
# View all events
cat .chronomemory/events.wal | python -m json.tool

# Count events
wc -l .chronomemory/events.wal

# Find all upsert events
grep '"op": "upsert"' .chronomemory/events.wal | wc -l

# Get the last event
tail -1 .chronomemory/events.wal | python -m json.tool
```
