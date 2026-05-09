# Ledger — specsmith

## 2026-05-09T00:00 — Bootstrap: initial governance scaffold
- **Author**: specsmith-agent (Oz / Warp)
- **Type**: bootstrap
- **REQs affected**: REQ-001..REQ-025
- **Status**: complete
- **Chain hash**: `genesis`

Created the specsmith self-governing project scaffold. Established core governance
files (`ARCHITECTURE.md`, `REQUIREMENTS.md`, `TESTS.md`), machine state under
`.specsmith/`, and CLI entrypoint. Governance layer owns all governance files;
runtime layer executes through CLI and agent commands.

---

## 2026-05-09T01:00 — Compliance, Context Window Management, and Governance Panel
- **Author**: Oz (Warp AI agent)
- **Type**: implementation — compliance / context / governance
- **REQs affected**: REQ-206..REQ-220, REQ-244..REQ-247
- **Status**: complete — all CI jobs green
- **Chain hash**: `c7bc792`

### Summary

This session added the full AI compliance and auditability layer (REQ-206..REQ-220),
context window management (REQ-244..REQ-247), governance tools panel wiring, and
comprehensive mechanical test coverage for all new requirements.

### EU AI Act / NIST AI RMF Compliance (REQ-206..REQ-220)

**REQ-206 — Tamper-Evident Agent Action Log (`TraceVault`)**
- `src/specsmith/trace.py`: SHA-256 chained JSONL ledger at `.specsmith/trace.jsonl`
- `SealType` enum: `DECISION`, `MILESTONE`, `AUDIT_GATE`
- `TraceVault.seal()`: appends entry with `hash = sha256(content + prev_hash)`
- `TraceVault.verify()`: walks the chain; reports first break
- Satisfies EU AI Act Art. 12 (logging) and NIST AI RMF GOVERN (accountability)

**REQ-207 — AI Disclosure in Preflight**
- Every `specsmith preflight` response includes `ai_disclosure` block:
  `{governed_by, governance_gated, provider, model, spec_version}`
- Cannot be suppressed; injected at the governance layer
- Satisfies EU AI Act Art. 13 (transparency) and Art. 53 (GPAI transparency)

**REQ-208 / REQ-215 — Compliance Export Report**
- `src/specsmith/exporter.py`: `run_export()` produces a report with three required
  sections: AI System Inventory, Risk Classification, Human Oversight Controls
- `specsmith export --format markdown/json`

**REQ-209 — Human Escalation Threshold**
- `specsmith preflight --escalate-threshold <float>` sets `escalation_required: true`
  when action confidence < threshold; includes `escalation_reason`
- Satisfies EU AI Act Art. 14 (human oversight) and NIST AI RMF MANAGE

**REQ-210 — Kill-Switch**
- `specsmith kill-session` terminates all active agent sessions and records a kill
  event in `LEDGER.md` with timestamp
- Satisfies EU AI Act Art. 14 §4 (ability to intervene and stop the AI system)

**REQ-213 — Append-Only Safe Write**
- `src/specsmith/safe_write.py`: `append_file()` (never truncates) and
  `safe_overwrite()` (creates timestamped `.bak` before replacing)
- All governance file writes go through `safe_write`
- Satisfies EU AI Act Art. 12 (records must persist)

**REQ-217 — Least-Privilege Agent Permissions**
- `specsmith agent permissions-check <tool>` returns exit 0 (allowed) or 3 (denied)
- Four presets: `read_only`, `standard`, `extended`, `admin`
- Custom allow/deny lists via `.specsmith/config.yml`
- Satisfies NIST AI RMF GOVERN (policy enforcement)

**REQ-220 — Policy Guardrails (`is_safe_command`)**
- `src/specsmith/agent/safety.py`: classifies shell commands against deny patterns
  (`rm -rf`, `git push origin main`, `kubectl apply`, `cat .env`, etc.)
- Denied commands blocked and logged before execution
- Satisfies NIST AI RMF MANAGE (action-level risk treatment)

### Context Window Management (REQ-244..REQ-247)

**REQ-244 — GPU-Aware Context Sizing**
- `src/specsmith/context_window.py`: `detect_gpu_vram()` queries `nvidia-smi` then
  `rocm-smi`; returns float GB (0.0 on CPU-only)
- `suggest_context_window(vram_gb)` maps VRAM to context tier:
  `<6GB→4096`, `6-11GB→8192`, `12-19GB→16384`, `20GB+→32768`
- Surfaced in `specsmith ollama gpu` and the Kairos Governance panel

**REQ-245 — Live Context Fill Indicator**
- `ContextFillTracker.record(used)` emits `ContextFillEvent` with `{type, used, limit, pct}`
- Events serialised as JSONL and consumed by Kairos agent footer fill bar
- `ContextFillTracker.all_events()` accumulates the full fill history

**REQ-246 — Auto Context Compression Threshold**
- Default compression threshold: 80% fill
- When fill ≥ threshold, `ContextFillEvent` signals Kairos to fire
  `SummarizeAIConversation` before the next agent turn
- Configurable via `context.compression_threshold_pct` in `.specsmith/config.yml`

**REQ-247 — Hard Context Ceiling — Never 100% Full**
- `effective_ceiling_pct = min(hard_ceiling_pct=85, (1 - min_free_tokens/limit) × 100)`
- For large context windows (≥ ~13K tokens), the 15% rule governs → ceiling = 85%
- For small windows (e.g. 4096 tokens), `min_free_tokens=2048` tightens to 50%
- `ContextFullError` raised at the effective ceiling — impossible to overflow

### Governance Tools Panel Wiring (.kairos integration)

- `agent/cleanup.py`: `.kairos` added to `PROTECTED_PATHS` (never auto-deleted)
- `cli.py`: `workspace_dirs` includes `.kairos/rules` alongside `.warp/rules`

### Test Coverage (tests/test_compliance.py)

Added `tests/test_compliance.py` with 20+ mechanical pytest assertions covering
all REQ-206..REQ-220 and REQ-244..REQ-247 compliance mechanisms. Tests are
deterministic (no live LLM required), run in CI, and directly map to TEST-206..TEST-225
in `docs/TESTS.md`.

### CI Status
- All CI jobs (sync-check, lint, typecheck, security, api-surface, test matrix): ✓
- Commit: `c7bc792` on `develop`
