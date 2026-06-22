# Init modes
`specsmith init` supports mode presets:

- `--mode lite`: minimal bootstrap (`AGENTS.md`, requirements/tests docs, `.specsmith` state)
- `--mode team` (default): standard collaborative governance scaffold
- `--mode regulated`: team scaffold plus compliance/evidence/checkpoint files

Additional init flags:

- `--dry-run`: list planned files without creating them
- `--explain`: explain mode intent and generated file purpose
- `--quiet`: suppress non-essential output
- `--verbose`: print full generated file list
- `--json`: emit machine-readable summary

## Migration checks
Schema migration runner supports:

- `specsmith migrate run --check` — exits non-zero when migrations are pending
- `specsmith migrate run --dry-run` — preview migrations without writing
- `specsmith migrate run` — applies pending migrations and writes a backup snapshot under `.specsmith/migration-backups/`
