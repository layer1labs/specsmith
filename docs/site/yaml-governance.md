# YAML Governance Reference

As of v0.12, specsmith uses **YAML-first governance**: requirements and test cases live in canonical YAML files; Markdown files are generated artifacts.

## Quick start

```bash
# Check current mode
cat .specsmith/governance-mode   # "yaml" = YAML-first, absent = legacy MD

# Full sync: YAML → JSON cache → Markdown
specsmith sync

# Strict schema validation
specsmith validate --strict

# Regenerate Markdown only (faster)
specsmith generate docs
```

---

## Authority model

| Layer | Location | Role |
|---|---|---|
| **Canonical source** | `docs/requirements/*.yml`, `docs/tests/*.yml` | Edit these |
| **JSON cache** | `.specsmith/requirements.json`, `.specsmith/testcases.json` | Auto-generated |
| **Markdown artifacts** | `docs/REQUIREMENTS.md`, `docs/TESTS.md` | Auto-generated — do NOT hand-edit |

The `.specsmith/governance-mode` flag controls which direction is authoritative:

```
governance-mode = yaml      → YAML-first (v0.12+ default after migration)
governance-mode = markdown  → Legacy Markdown-primary (backward compat)
(absent)                    → Legacy Markdown-primary
```

---

## Domain YAML files

Requirements and test cases are split into domain files. Add a new requirement by editing the appropriate file and running `specsmith sync`.

### Requirements

| File | REQ range | Domain |
|---|---|---|
| `docs/requirements/governance.yml` | REQ-001..064 | Core AEE governance |
| `docs/requirements/agent.yml` | REQ-065..129 | Nexus + CI |
| `docs/requirements/harness.yml` | REQ-130..160 | Slash commands + subagents |
| `docs/requirements/intelligence.yml` | REQ-161..220 | Instinct, eval, memory |
| `docs/requirements/context.yml` | REQ-244..247 | Context window |
| `docs/requirements/esdb.yml` | REQ-248..262 | ESDB + skills + MCP |
| `docs/requirements/ai_intelligence.yml` | REQ-263..299 | AI model intelligence |
| `docs/requirements/yaml_governance.yml` | REQ-300..399 | YAML governance layer |

### Test cases

Mirror structure under `docs/tests/` (e.g. `docs/tests/governance.yml`, `docs/tests/agent.yml`, …).

### YAML schema

**Requirements** (`docs/requirements/*.yml`):

```yaml
- id: REQ-NNN             # required — stable numeric ID, e.g. REQ-305
  title: Short title      # required
  status: implemented     # required — implemented | planned | partial | deprecated
  description: >-
    Full description of what the system must do.
  source: ARCHITECTURE.md §Section   # optional but recommended
```

**Test cases** (`docs/tests/*.yml`):

```yaml
- id: TEST-NNN            # required
  title: Short title      # required
  requirement_id: REQ-NNN # required — must reference an existing REQ
  type: unit              # optional — unit | integration | cli | e2e | build | manual
  verification_method: pytest   # optional
  description: >-
    What the test verifies.
  input: "test input description"
  expected_behavior: "what should happen"
  confidence: 1.0
```

---

## CLI reference

### `specsmith sync`

Full pipeline: load YAML → write JSON cache → regenerate Markdown.

```bash
specsmith sync                  # run full sync
specsmith sync --check          # exit 1 if JSON cache is out of sync (CI gate)
specsmith sync --project-dir /path/to/project
```

**When to run:** after editing any `docs/requirements/*.yml` or `docs/tests/*.yml` file.

### `specsmith generate docs`

Regenerate `REQUIREMENTS.md` and `TESTS.md` from YAML without touching the JSON cache.

```bash
specsmith generate docs            # regenerate Markdown
specsmith generate docs --check    # dry-run: report what would change
specsmith generate docs --json     # structured {ok, reqs, tests}
```

**When to use:** when you only want to refresh Markdown (e.g. after CI generates the cache).

### `specsmith validate --strict`

Enforce 8 governance schema checks.

```bash
specsmith validate --strict          # human-readable
specsmith validate --strict --json   # structured output
```

**Exit codes:**
- `0` — clean (zero errors; warnings allowed)
- `1` — one or more schema errors

**The 8 checks:**

| # | Check | Severity |
|---|---|---|
| 1 | Duplicate REQ IDs | Error |
| 2 | Duplicate TEST IDs | Error |
| 3 | Missing required REQ fields (`id`, `title`, `status`) | Error |
| 4 | Missing required TEST fields (`id`, `title`, `requirement_id`) | Error |
| 5 | Orphaned TESTs (reference a non-existent REQ) | Error |
| 6 | Untested REQs | Warning |
| 7 | Duplicate REQ titles | Warning |
| 8 | Machine-state drift (YAML vs JSON cache) | Warning |

**JSON output shape:**

```json
{
  "ok": true,
  "strict_errors": 0,
  "strict_warnings": 2,
  "details": [
    {"type": "warning", "check": "untested_req", "id": "REQ-042", "message": "..."}
  ]
}
```

---

## Migration from Markdown-primary

If your project has `docs/REQUIREMENTS.md` as the hand-edited source, migrate once:

```bash
python scripts/migrate_governance_to_yaml.py
```

This script is **idempotent** — re-running it on an already-migrated project produces no changes. It performs 4 steps in order:

1. Remove duplicate REQs from `docs/REQUIREMENTS.md`
2. Re-sync `.specsmith/` JSON from the cleaned Markdown
3. Export JSON to grouped YAML domain files under `docs/requirements/` and `docs/tests/`
4. Write `.specsmith/governance-mode = yaml`

After migration, `specsmith sync --check` exits 0 and `specsmith validate --strict` reports no errors.

---

## CI integration

The `validate-strict` and `sync-check` steps in `.github/workflows/ci.yml` enforce YAML governance on every push and PR:

```yaml
governance:
  name: Governance Audit
  steps:
    - name: Check machine state sync
      run: python -m specsmith sync --check --project-dir .

    - name: Validate governance schema (strict)
      run: python -m specsmith validate --strict --json --project-dir .
```

Both steps block the build on failure. The `sync-check` step catches JSON cache drift (e.g. YAML edited but sync not run). The `validate-strict` step catches schema errors such as duplicate IDs or orphaned tests.

---

## Python API

```python
from specsmith.governance_yaml import (
    is_yaml_mode,        # is_yaml_mode(root: Path) -> bool
    load_yaml_reqs,      # load_yaml_reqs(root: Path) -> list[dict]
    load_yaml_tests,     # load_yaml_tests(root: Path) -> list[dict]
    save_yaml_reqs,      # save_yaml_reqs(root: Path, reqs: list[dict]) -> None
    save_yaml_tests,     # save_yaml_tests(root: Path, tests: list[dict]) -> None
    generate_md_from_yaml,  # generate_md_from_yaml(root: Path) -> None
    validate_strict,     # validate_strict(root: Path) -> dict
)

root = Path(".")
if is_yaml_mode(root):
    reqs = load_yaml_reqs(root)   # merged, sorted list of all REQs
    result = validate_strict(root)
    print(result["strict_errors"], "errors,", result["strict_warnings"], "warnings")
```

---

## Workflow examples

### Add a new requirement

```bash
# 1. Edit the appropriate domain YAML file
#    e.g. docs/requirements/governance.yml
cat >> docs/requirements/governance.yml << 'EOF'
- id: REQ-065
  title: My new requirement
  status: planned
  description: >-
    The system must do X.
  source: ARCHITECTURE.md §6
EOF

# 2. Sync to regenerate JSON cache and Markdown
specsmith sync

# 3. Validate schema
specsmith validate --strict
```

### Add a test case

```bash
# Edit docs/tests/governance.yml (matching domain file)
# Then sync and validate
specsmith sync
specsmith validate --strict
```

### Check before commit

```bash
specsmith sync --check          # exits 0 if clean
specsmith validate --strict     # exits 0 if clean
```

---

## Troubleshooting

**`specsmith sync --check` exits 1**

Your JSON cache is out of sync with the YAML files. Run `specsmith sync` to regenerate it.

**`specsmith validate --strict` reports orphaned TEST**

A test case references a `requirement_id` that doesn't exist. Either add the missing REQ or fix the `requirement_id` in the test YAML file.

**`specsmith generate docs` says "not in YAML mode"**

The `.specsmith/governance-mode` file is missing or contains `markdown`. Run the migration script, or create the file manually:

```bash
echo "yaml" > .specsmith/governance-mode
```

**After migration, REQUIREMENTS.md looks different**

The migration regenerates `REQUIREMENTS.md` from the YAML sources. The content is the same, but formatting is normalised. This is expected — the Markdown file is now a generated artifact.
