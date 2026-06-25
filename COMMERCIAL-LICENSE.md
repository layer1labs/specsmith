# COMMERCIAL LICENSE — ChronoMemory ESDB (specsmith add-on)

This document defines the commercial licensing scope for the **ChronoMemory ESDB engine** used by `specsmith[esdb]`.

## Scope (important)

- Applies to: **ChronoMemory commercial backend** (`chronomemory` package, ChronoStore WAL backend).
- Does **not** apply to: the default **SQLite backend** that ships with `specsmith` under the MIT license.

In other words:
- `pip install specsmith` → SQLite backend only → MIT/free path.
- `pip install "specsmith[esdb]"` or `pip install chronomemory` → commercial ChronoMemory path.

## Tier summary

### Free tier (default)
- Backend: SQLite (`.specsmith/esdb.sqlite3`)
- License: MIT
- Commercial key required: No

### Commercial tier
- Backend: ChronoMemory ChronoStore (`.chronomemory/events.wal`)
- License: Proprietary commercial license (this document)
- Commercial key required: Yes (`specsmith esdb enable --key-file ...`)

## Commercial-use triggers

A commercial ChronoMemory license is required when you:
- Install or use `chronomemory` directly.
- Install `specsmith[esdb]`.
- Activate ChronoStore with `specsmith esdb enable`.
- Use ChronoStore features (tamper-evident SHA-256 WAL chain, full OEA fields, rollback/context-pack features).

## Distribution and deployment

The commercial license for ChronoMemory is required for production/commercial usage of the ChronoMemory backend, including hosted and internal deployments that rely on the commercial backend.

The MIT license remains valid for the free SQLite backend in specsmith.

## Contact

- Licensing: licensing@layer1labs.ai
- Support: support@layer1labs.ai

