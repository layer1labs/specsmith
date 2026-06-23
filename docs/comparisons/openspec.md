# Specsmith for OpenSpec Users
OpenSpec emphasizes lightweight specification workflows, while Specsmith adds governed execution, traceability, and audit evidence generation.

## Lightweight vs governed workflows
- OpenSpec-style flow: low ceremony, rapid authoring, minimal mandatory gates.
- Specsmith flow: explicit decision gates (`preflight`), verification checkpoints, and trace-backed auditability.
- Teams can combine both by keeping lightweight authoring while enabling governance only for higher-risk changes.

## Import and conversion plan
- Use `specsmith import openspec` (stub command path) to ingest baseline project metadata.
- Map OpenSpec artifacts to requirements/tests in specsmith governance docs.
- Establish governance checkpoints (`preflight`, `verify`, `audit`) for implementation changes.

## Lite mode for low ceremony
Specsmith can be configured in lower-ceremony patterns for teams that want OpenSpec-like speed while preserving optional governance controls. This provides a migration runway: start with lightweight operation, then increase rigor as team size, compliance pressure, or product risk grows.

## Side-by-side example
1. Write/update spec in existing OpenSpec process.
2. Run `specsmith preflight "<change intent>" --json`.
3. Implement with agent or manually.
4. Run `specsmith verify` and `specsmith audit`.
5. Export evidence when needed.
