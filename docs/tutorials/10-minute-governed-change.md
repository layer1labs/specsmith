# 10-Minute Governed Change Tutorial

This tutorial walks through a tiny Python CLI app and a single governed change from idea to closure.

## Scenario

You have a tiny calculator CLI and want to add a `%` command that prints percentages.

## Starting project

```text
tiny-calc/
  app.py
  tests/
    test_app.py
```

`app.py` starts with `add` and `sub` commands only.

## Step 1: Initialize governance

```bash
specsmith init
```

Expected output snippet:

```text
✔ Initialized SpecSmith project
✔ Created docs/requirements and docs/tests governance sources
✔ Created .specsmith state directory
```

## Step 2: Add a requirement

Add a requirement entry in your requirements YAML:

```yaml
- id: REQ-901
  title: Calculator shall support percent operation
  description: Given value and percent, app returns computed portion.
  status: proposed
```

Then sync generated artifacts:

```bash
specsmith sync
```

Expected output snippet:

```text
✔ Synced YAML governance sources
✔ Regenerated docs/REQUIREMENTS.md and docs/TESTS.md
```

## Step 3: Run preflight for the change

```bash
specsmith preflight "add percent command to calculator CLI and tests" --json
```

Expected output snippet:

```json
{
  "decision": "accepted",
  "work_item_id": "WI-AB12CD34",
  "requirement_ids": ["REQ-901"]
}
```

## Step 4: Implement the small change

Example change in `app.py`:
- parse `percent <value> <pct>`
- return `value * pct / 100`

Run tests:

```bash
python -m pytest tests/ -q
```

## Step 5: Link and verify

Add/update test mapping so the new test points to `REQ-901`, then run:

```bash
specsmith verify
```

Expected output snippet:

```text
✔ Verification complete
✔ Equilibrium reached
✔ Requirement coverage: REQ-901 linked to tests
```

## Step 6: Audit and close work item

```bash
specsmith audit
specsmith wi close WI-AB12CD34 --reason "implemented and verified"
```

Expected output snippet:

```text
✔ Audit passed
✔ Work item WI-AB12CD34 closed
```

## Final repo tree (example)

```text
tiny-calc/
  app.py
  tests/
    test_app.py
  docs/
    REQUIREMENTS.md
    TESTS.md
    requirements/
      governance.yml
    tests/
      governance.yml
  .specsmith/
    workitems.json
    trace.jsonl
    ledger.jsonl
```

## Troubleshooting

- `decision: needs_clarification`
  - Rewrite intent to be specific about files and expected behavior.
- Missing requirement/test linkage
  - Ensure requirement IDs in tests exactly match requirement IDs.
- Audit failures
  - Run `specsmith sync` and `specsmith validate --strict`, then re-run audit.
- Work item not found
  - Run `specsmith wi list --status open` to confirm ID.

