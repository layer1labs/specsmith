# Deprecations & Teardown Registry

This file is the authoritative registry of **legacy flat-file artifacts** that
are being superseded by the Epistemic State Database (ESDB) as specsmith moves to
an ESDB-first, single-source-of-truth model.

Nothing in this registry has been deleted yet. Each item is annotated in source
with a greppable marker so teardown is a single grep:

```bash
# Find every legacy site slated for removal
grep -rn "DEPRECATED(REQ-421)" src/
```

**Forward-only policy:** there are no backward migrations. Once every specsmith
project has been updated to read its state from ESDB, the items below will be
removed in their named teardown requirement to keep specsmith lean.

When SQLite is used instead of the commercial ChronoMemory backend, the ESDB
kinds below behave identically (REQ-422) — no feature is gated behind the
commercial backend.

## How to read this registry

Each entry lists:
- **Artifact** — the legacy file/path on disk.
- **Sites** — the source module(s) carrying the `DEPRECATED(REQ-421)` marker.
- **Superseded by** — the ESDB record kind (and the REQ that introduced it).
- **Status** — what happens today (dual-write, cache, or orphaned).
- **Teardown** — the requirement that will remove the legacy code/file.

## Registry

### `.specsmith/trace.jsonl` — cryptographic trace vault
- **Sites:** `src/specsmith/trace.py` (`TraceVault.TRACE_FILE`, `_path`),
  `src/specsmith/auditor.py` (`check_trace_chain_integrity`, legacy
  `epistemic.trace` reader), `src/specsmith/cli.py` (`esdb_replay_cmd` docstring),
  `src/specsmith/agent/runner.py` (`_seal_profile_pin` docstring),
  `src/specsmith/config.py` (`enable_trace_vault` description),
  `src/specsmith/compliance/regulations.py` (EU AI Act Art. 12 control list),
  `src/specsmith/sync.py` (`_ESDB_GITIGNORE_REQUIRED`).
- **Superseded by:** ESDB `seal_record` (REQ-420).
- **Status:** ESDB-only as of REQ-420. The flat file is no longer written; the
  path constants are retained so external tooling imports keep working.
- **Teardown:** remove `TRACE_FILE`/`_path`, the `epistemic.trace` auditor
  branch, and the gitignore entry once all projects are ESDB-only.

### `.specsmith/workitems.json` — Work Item store
- **Sites:** `src/specsmith/wi_store.py` (module docstring, `_WORKITEMS_FILE`,
  `WorkItemStore.save`).
- **Superseded by:** ESDB `work_item` (REQ-398 dual-write via
  `WorkItemStore._sync_to_esdb`).
- **Status:** dual-written. The JSON file is still the read source of truth today.
- **Teardown:** REQ-423 makes ESDB `work_item` the source of truth and drops the
  JSON file.

### `.specsmith/requirements.json` and `.specsmith/testcases.json` — governance cache
- **Sites:** `src/specsmith/sync.py` (`run_sync` JSON writer, `_ESDB_GITIGNORE_REQUIRED`).
- **Superseded by:** ESDB `requirement` / `testcase` (mirrored by `_sync_esdb`).
- **Status:** regeneratable cache of `docs/requirements/*.yml` and
  `docs/tests/*.yml`; mirrored into ESDB on every sync.
- **Teardown:** REQ-424 stops writing the JSON cache once all CLI/audit surfaces
  read governance from ESDB.

### `.specsmith/session_metrics.jsonl` — project metrics
- **Sites:** `src/specsmith/project_metrics.py` (`_METRICS_FILE`,
  `MetricsStore.append`).
- **Superseded by:** ESDB `session_metric` (REQ-405 dual-write).
- **Status:** dual-written. NDJSON file retained for back-compat reads.
- **Teardown:** future REQ — switch `MetricsStore.load`/reporting to read from
  ESDB, then drop the NDJSON file.

### `.specsmith/session-state.json` and `.specsmith/conversation-history.jsonl` — session continuity
- **Sites:** `src/specsmith/session_store.py` (module docstring, `save_session`).
- **Superseded by:** _no ESDB equivalent yet._
- **Status:** legacy flat files; runtime/session-resume only (gitignored).
- **Teardown:** future REQ — model session state as ESDB session records, then
  drop these files.

### `.specsmith/esdb_migration_manifest.json` — one-shot migration scan
- **Sites:** `src/specsmith/cli.py` (`esdb migrate` scan), `src/specsmith/sync.py`
  (`_ESDB_GITIGNORE_REQUIRED`).
- **Superseded by:** native ESDB ingestion (no manifest needed once projects are
  ESDB-first).
- **Status:** written only by the legacy JSON→ESDB migration path.
- **Teardown:** remove with the JSON migration helpers (`migrate_from_json`,
  migrations `m008`/`m009`/`m010`) once no project needs JSON bootstrap.

### Generated `.gitignore` policy (`templates/gitignore.j2`)
- **Sites:** `src/specsmith/templates/gitignore.j2`, `src/specsmith/sync.py`
  (`_ESDB_GITIGNORE_REQUIRED`, `normalize_esdb_gitignore_policy`).
- **Superseded by:** a slimmer policy that only needs to track canonical ESDB
  state (`esdb.sqlite3`, `.chronomemory/*`).
- **Status:** still emits ignore rules for every legacy artifact above.
- **Teardown:** prune the legacy artifact lines from the template and the policy
  tuple as each artifact's teardown REQ lands.

## Teardown checklist (when the time comes)

1. Confirm every governed project has migrated (ESDB record counts > 0 for the
   relevant kinds).
2. `grep -rn "DEPRECATED(REQ-421)" src/` to enumerate every site.
3. Remove the legacy writer/reader code and path constants per entry above.
4. Drop the corresponding lines from `templates/gitignore.j2` and
   `sync._ESDB_GITIGNORE_REQUIRED`.
5. Delete this registry entry and re-run `specsmith audit`.
