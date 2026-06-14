# Work Item (WI) Lifecycle

Every `specsmith preflight` that is **accepted** mints a Work Item — a
governance breadcrumb that tracks user intent from the moment of the request
through to a formal requirement or a verified close.

Work Items are persisted to `.specsmith/workitems.json` and surfaced via the
`specsmith wi` command group.

---

## States

| State | Meaning |
|---|---|
| `open` | Created by preflight; work in progress |
| `implemented` | `specsmith verify` reached equilibrium (auto-set) |
| `promoted` | Elevated to a formal REQ-NNN via `specsmith wi promote` |
| `closed` | Done; satisfies an existing requirement; no new REQ needed |
| `archived` | Abandoned or deferred; may be re-opened |
| `rejected` | Explicitly rejected |

---

## State Machine

```
preflight accepted
    │
    ▼
 [open]
    ├── verify equilibrium ──────► [implemented]
    │                                    ├── wi promote ──► [promoted]  → promoted_to_req=REQ-NNN
    │                                    ├── wi close  ──► [closed]
    │                                    └── wi archive ─► [archived]
    ├── wi archive ──────────────► [archived]
    │                                    └── wi open (reopen) → [open]
    └── wi reject  ──────────────► [rejected]
```

The only permitted **reverse** transition is `archived → open` (un-defer).
All other transitions are forward-only and enforced by `WorkItemStore`.

---

## When Does a WI Become a REQ?

Promote a WI to a formal requirement when **all** of the following are true:

1. The change introduced **new behavior** not covered by any existing REQ.
2. The pattern is **expected to recur** and needs permanent test coverage.
3. The WI's `requirement_ids` list was **empty** at preflight time
   (no existing requirement matched the utterance).

Use `specsmith wi promote` to create the REQ entry and link it back:

```bash
specsmith wi promote WI-3A9F1C02 \
    --title "Exporter must retry on transient HTTP 5xx failures" \
    --domain governance
```

This appends a `REQ-NNN` entry to `docs/requirements/<domain>.yml`,
transitions the WI to `promoted`, and records `promoted_to_req=REQ-NNN`
on the WI record.  Run `specsmith sync` afterwards to regenerate
`REQUIREMENTS.md`.

---

## When Does a WI Stay Closed (No New REQ)?

Close (not promote) when the change is covered by existing requirements:

| Scenario | Command |
|---|---|
| Bug fix against existing REQ | `specsmith wi close WI-XXXX --reason "fixed bug in REQ-042"` |
| Refactoring within existing scope | `specsmith wi close WI-XXXX` |
| Docs update with no new behaviour | `specsmith wi close WI-XXXX` |
| Config / chore already covered | `specsmith wi close WI-XXXX` |

---

## Commands

### `specsmith wi list`

```bash
# All work items
specsmith wi list

# Filter by status
specsmith wi list --status open
specsmith wi list --status implemented

# Machine-readable JSON
specsmith wi list --json
```

### `specsmith wi show`

```bash
specsmith wi show WI-3A9F1C02
specsmith wi show WI-3A9F1C02 --json
```

### `specsmith wi close`

```bash
specsmith wi close WI-3A9F1C02
specsmith wi close WI-3A9F1C02 --reason "bug fixed in src/foo.py"
```

### `specsmith wi archive`

```bash
# Defer a WI (may be re-opened later)
specsmith wi archive WI-3A9F1C02 --reason "superseded by WI-AABBCCDD"
```

### `specsmith wi promote`

```bash
specsmith wi promote WI-3A9F1C02 \
    --title "System must validate JWT expiry before every API call" \
    --domain governance
```

Options:

| Flag | Default | Description |
|---|---|---|
| `--title` | WI intent (truncated) | Human-readable requirement title |
| `--domain` | `overflow` | Target requirements YAML file (without `.yml`) |
| `--json` | off | Emit JSON result |

### `specsmith wi tag`

Set the kind / classification label:

```bash
specsmith wi tag WI-3A9F1C02 --kind bug
specsmith wi tag WI-3A9F1C02 --kind feature
```

Valid kinds: `feature`, `bug`, `chore`, `spike`, `refactor`, `docs`.

### `specsmith wi import`

Import WIs from `LEDGER.md` `work_proposal` entries into
`.specsmith/workitems.json`.  Useful for bootstrapping projects that already
have a populated ledger:

```bash
specsmith wi import --from-ledger
```

Existing WIs are never overwritten.

---

## Data Model

```
WorkItem:
  id              str        # WI-XXXXXXXX  (8-char hex UUID prefix, uppercase)
  status          str        # open | implemented | promoted | closed | archived | rejected
  kind            str        # feature | bug | chore | spike | refactor | docs
  intent          str        # verbatim preflight utterance
  created_at      str        # ISO-8601 UTC
  updated_at      str        # ISO-8601 UTC
  requirement_ids list[str]  # REQ-NNN IDs matched at preflight time
  test_case_ids   list[str]  # TEST-NNN IDs linked at preflight time
  promoted_to_req str|None   # REQ-NNN created by wi promote
  closed_at       str|None   # ISO-8601 UTC (set on close/archive/reject)
  closed_reason   str|None   # free-text reason
  confidence_target float    # from preflight
  verified        bool       # True once mark_implemented() is called
```

Stored in `.specsmith/workitems.json` as a JSON object keyed by WI ID.
Writes are atomic (write-to-tmp-then-rename) to prevent corruption on crash.

---

## Automatic Transitions

Two state transitions happen automatically without any CLI command:

| Trigger | Transition |
|---|---|
| `specsmith preflight` accepted | `(none) → open` (WI minted) |
| `specsmith verify` reaches equilibrium | `open → implemented` |

Both wires are **best-effort** — a failure in `WorkItemStore` never blocks
the preflight or verify result.

---

## Example: Full Happy Path

```bash
# 1. Start work — mints WI-ABC12345 (open)
specsmith preflight "add retry logic to the HTTP exporter"
# → decision: accepted, work_item_id: WI-ABC12345

# 2. Implement the change, run tests, verify
specsmith verify --diff "$(git diff HEAD~1)" --files-changed src/exporter.py \
    --work-item-id WI-ABC12345
# → equilibrium: true  → WI-ABC12345 auto-set to implemented

# 3a. No existing REQ covers retry logic → promote
specsmith wi promote WI-ABC12345 \
    --title "HTTP exporter must retry on transient 5xx failures" \
    --domain governance

# 3b. (alternative) Change already covered by REQ-042 → close
# specsmith wi close WI-ABC12345 --reason "covered by REQ-042"

# 4. Sync governance docs
specsmith sync

# 5. Check your WI
specsmith wi show WI-ABC12345
```

---

## RTD / Architecture Links

- Architecture: `docs/ARCHITECTURE.md` — Section 6.2
- Requirements: REQ-065 through REQ-069 in `docs/requirements/governance.yml`
- Tests: TEST-065 through TEST-069 in `docs/tests/governance.yml`
- Implementation: `src/specsmith/wi_store.py`, `src/specsmith/governance_logic.py`
