# ESDB API — EsdbBridge

Unified read/write adapter with automatic backend detection and `.specsmith/` JSON fallback.

```python
from chronomemory import EsdbBridge
```

## Purpose

`EsdbBridge` provides a single interface for projects that may be in one of two states:

1. **ESDB active** — `.chronomemory/events.wal` exists → delegates to `ChronoStore`
2. **JSON fallback** — no WAL yet → reads `.specsmith/requirements.json` and `testcases.json`

This allows specsmith CLI commands, dashboards, and CI scripts to work with both migrated
and non-migrated projects without branching.

## Constructor

```python
EsdbBridge(project_dir: str = ".")
```

## Methods

### `status() → EsdbStatus`

Return the ESDB status for this project.

```python
bridge = EsdbBridge(project_dir="/path/to/project")
s = bridge.status()
print(s.backend)       # "ChronoStore WAL" or ".specsmith/ JSON (run esdb migrate...)"
print(s.record_count)
print(s.chain_valid)
print(s.wal_seq)
```

`EsdbStatus.to_dict()` returns all fields as a JSON-serialisable dict.

### `requirements() → list[EsdbRecord]`

Load requirements from ESDB (if active) or `.specsmith/requirements.json`.

### `testcases() → list[EsdbRecord]`

Load test cases from ESDB (if active) or `.specsmith/testcases.json`.

### `record_counts() → dict[str, int]`

Record counts by kind.

When ESDB is active: `{"requirement": 12, "testcase": 8, "fact": 3, ...}`

When JSON fallback: `{"requirements": 12, "testcases": 8}`

### `upsert_record(record: EsdbRecord) → bool`

Write or update a record. Returns `True` if ESDB is active and the write succeeded.
Returns `False` if only the JSON fallback is available.

### `delete_record(record_id: str) → bool`

Tombstone a record. Returns `True` if ESDB is active. Returns `False` for JSON fallback.

---

## EsdbRecord

```python
from chronomemory.bridge import EsdbRecord
```

Simpler mirror of `ChronoRecord` used by the bridge layer.

| Field | Type | Default |
|-------|------|---------|
| `id` | `str` | required |
| `kind` | `str` | `"fact"` |
| `status` | `str` | `"active"` |
| `confidence` | `float` | `0.7` |
| `label` | `str` | `""` |
| `data` | `dict` | `{}` |
| `source_ids` | `list[str]` | `[]` |

---

## EsdbStatus

| Field | Type | Description |
|-------|------|-------------|
| `available` | `bool` | Always `True` (bridge never fails) |
| `backend` | `str` | `"ChronoStore WAL"` or `".specsmith/ JSON ..."` |
| `record_count` | `int` | Total active record count |
| `wal_seq` | `int` | Current WAL seq (0 for JSON fallback) |
| `epoch` | `int` | Store epoch (0 for JSON fallback) |
| `chain_valid` | `bool` | `True` if WAL chain is unbroken |
