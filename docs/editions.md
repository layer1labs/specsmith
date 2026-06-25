# OSS vs Commercial Feature Matrix

SpecSmith ships with a free, MIT-licensed SQLite backend and an optional commercial ChronoMemory package (ChronoStore backend).

| Capability | Free (SQLite backend) | Commercial (ChronoMemory / ChronoStore backend) |
|---|---|---|
| SQLite ESDB | ✅ Included | ✅ Included |
| ChronoMemory package (ChronoStore engine) | ❌ | ✅ |
| MCP server | ✅ | ✅ |
| Compliance reports | ✅ | ✅ (extended enterprise workflows) |
| Audit chain | ✅ | ✅ |
| Rollback | Basic workflow support | Extended WAL-backed rollback features |
| Dependency graph | ✅ | ✅ |
| WAL hash chain | Basic trace chain support | ✅ Full ChronoStore WAL chain |
| Tamper detection | ✅ | ✅ (extended verification tooling) |
| OEA fields | Limited/default fields | ✅ Extended OEA metadata |
| Rust acceleration | ❌ | ✅ |
| Terminology model | ESDB spec + SQLite backend | ESDB spec + ChronoMemory package + ChronoStore backend |

## Notes

- Free edition is sufficient for many teams adopting governance-first development.
- Commercial edition focuses on enterprise-grade durability, tamper evidence depth, and performance.

## Compliance disclaimer

SpecSmith provides governance and evidence tooling, but does not provide a legal compliance guarantee. Organizations remain responsible for legal interpretation, control design, and regulatory submission quality.

