# Cloud Agents — Endpoint Contract (Pre-1.0)
This document specifies the contract a cloud-agent receiver must implement
so the local `specsmith cloud spawn` CLI can hand off a task. The contract
is intentionally narrow for pre-1.0; it will widen once at least one
external receiver has been implemented end-to-end (see
`docs/site/api-stability.md` for 1.0 criteria).
## Endpoint
A cloud receiver is any HTTP endpoint reachable via the URL configured in
`SPECSMITH_CLOUD_ENDPOINT` (or `--endpoint`). It MUST accept:
```http
POST <endpoint>
Content-Type: application/json
Authorization: Bearer <SPECSMITH_CLOUD_TOKEN>   (optional)
```
The body is the **manifest** described below. The endpoint MAY return:
- `200 OK` with a streaming body of newline-delimited JSON events
  (`Content-Type: application/jsonl` or `application/x-ndjson`).
- `202 Accepted` with `Location:` header pointing to a follow-up URL the
  CLI can long-poll.
- `4xx`/`5xx` with a JSON error body `{"error": "<message>"}`.
The current `specsmith cloud spawn` implementation reads the response as a
single stream, so receivers SHOULD stream JSONL on `200 OK`. The
`202 Accepted` follow-up flow is reserved for a future minor release.
## Manifest schema
The CLI writes the manifest to
`.specsmith/cloud/<run_id>/manifest.json` for auditability and POSTs the
same payload to the endpoint:
```json
{
  "run_id":     "cloud_<12-hex>",
  "utterance":  "<the natural-language task>",
  "workspace":  "workspace.tar.gz",
  "endpoint":   "<the endpoint URL or '' for dry-run>",
  "dry_run":    false
}
```
The corresponding `workspace.tar.gz` lives next to `manifest.json` and
contains the local working tree minus `.git`, `.venv`, `.specsmith`,
`node_modules`, `dist`, and `build`. The receiver SHOULD reject manifests
where `workspace` is missing or larger than 100 MB; specsmith's local
copy is provided for auditing only.
## Stream protocol (response body)
The receiver MUST emit the same JSONL block protocol that `specsmith chat`
emits locally (REQ-113). This lets IDEs (the VS Code extension, the GUI)
consume cloud and local runs identically. The minimum viable event set:
- `block_start` — opens a `plan`, `message`, `tool_call`, `tool_result`,
  or `diff` block.
- `block_complete` — closes the most recent block of that id.
- `task_complete` — terminal event with `success`, `confidence`,
  `summary`, `profile`, and optional `comments`.
The full event vocabulary is documented in
`src/specsmith/agent/events.py`. Receivers MAY emit additional event kinds
prefixed with `cloud_*` (e.g. `cloud_progress`); local consumers ignore
unknown event kinds without failing.
## Security baseline (pre-1.0)
- The CLI never sends API keys in the manifest. The receiver MUST obtain
  its own credentials.
- The workspace tarball MUST be treated as untrusted user input.
- The receiver SHOULD honor `dry_run: true` by responding with a single
  `task_complete` event of `{"success": false, "summary": "dry-run"}` and
  no side effects.
- TLS is REQUIRED when `endpoint` does not point at `localhost`.
## What's deferred for after 1.0
- Authentication header standardization (currently informally
  `Authorization: Bearer ...`).
- Resumable / chunked upload for large workspaces.
- Multi-tenant manifest ids (today the CLI generates `cloud_<random>`,
  the receiver MAY assign its own canonical id).
- Push-style result delivery (today receivers respond synchronously; a
  webhook-based callback is a candidate future feature).
## Reference: minimum viable receiver
A 50-line aiohttp / FastAPI receiver that accepts the manifest, runs a
fixed Nexus orchestrator turn, and emits the JSONL block protocol back is
sufficient to claim compatibility with the pre-1.0 contract. The
specsmith repo will publish a reference receiver under
`examples/cloud-receiver/` in a follow-up minor release.
