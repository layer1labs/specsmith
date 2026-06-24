# ESDB API — ChronoRecord

The universal record envelope for ESDB. All fields have safe defaults.

```python
from chronomemory import ChronoRecord
```

## Dataclass fields

| Field | Type | Default | OEA rule | Description |
|-------|------|---------|----------|-------------|
| `id` | `str` | `""` | — | Unique identifier |
| `kind` | `str` | `"fact"` | — | Semantic kind: `fact`, `hypothesis`, `requirement`, `testcase`, `decision`, `risk` |
| `status` | `str` | `"active"` | — | ESDB lifecycle: `active`, `deprecated`, `tombstone` |
| `label` | `str` | `""` | — | Human-readable label or title |
| `confidence` | `float` | `0.7` | H17 | Degree of belief, `0.0–1.0` |
| `source_type` | `str` | `"observed"` | H19 | `observed`, `inferred`, `hypothesis`, `synthetic` |
| `evidence` | `list[str]` | `[]` | H20 | Source references supporting this record |
| `epistemic_boundary` | `list[str]` | `[]` | H15 | Scope constraints on validity |
| `is_hypothesis` | `bool` | `False` | H20 | True if this is a tentative, untested belief |
| `model_assumptions` | `dict` | `{}` | H21 | Model identity and settings for LLM-generated records |
| `recursion_depth` | `int` | `0` | H16 | Agent generation chain depth (stamped by ChronoStore) |
| `data` | `dict` | `{}` | — | Free-form JSON payload |

## Methods

### `to_dict() → dict`

Serialize to a JSON-compatible dict. All fields are included.

### `from_dict(d: dict) → ChronoRecord`

Reconstruct from a dict. Unknown keys are silently ignored (forward-compatible).

### `passes_rag_filter() → bool`

Returns `True` if this record should be included in RAG context injection per H18:
`confidence >= 0.6` AND `status == "active"`.

```python
rec = ChronoRecord(id="X", confidence=0.9)
print(rec.passes_rag_filter())  # True

rec2 = ChronoRecord(id="Y", confidence=0.5)
print(rec2.passes_rag_filter())  # False
```

## Examples

```python
# Minimal — safe defaults for all OEA fields
rec = ChronoRecord(id="MIN-001")

# Requirement
rec = ChronoRecord(
    id="REQ-001",
    kind="requirement",
    label="WAL must be append-only with SHA-256 hash chain",
    source_type="observed",
    confidence=1.0,
    evidence=["ESDB-Specification.md §2.4"],
)

# LLM-generated hypothesis
rec = ChronoRecord(
    id="HYP-scaling-001",
    kind="hypothesis",
    label="Scaling to K=1000 constraints keeps O(K) memory",
    is_hypothesis=True,
    source_type="synthetic",
    confidence=0.65,
    model_assumptions={
        "provider": "anthropic",
        "model": "claude-opus-4",
        "temperature": 0.0,
    },
)
```

## Status transitions

| From | To | Method | Notes |
|------|----|--------|-------|
| `active` | `tombstone` | `store.delete(id)` | Via WAL delete event |
| `active` | `deprecated` | `store.upsert(rec)` | Manually set `rec.status = "deprecated"` |
| `tombstone` | `active` | `store.upsert(rec)` | Override with new upsert |

The `status` field in `ChronoRecord` is the ESDB lifecycle status — it is **separate**
from governance lifecycle statuses (`defined`, `implemented`, etc.) used by specsmith.
