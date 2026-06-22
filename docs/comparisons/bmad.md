# Specsmith for BMAD Users
BMAD users can retain familiar artifact workflows while adding governance gates, traceability, and compliance evidence through Specsmith.

## BMAD artifact mapping
| BMAD artifact | Specsmith artifact |
|---|---|
| Initiative brief | Requirement set + project context |
| Task plan | Work item + preflight decision |
| Acceptance notes | Verification results + test mapping |
| Delivery log | TraceVault/ledger events |
| Retrospective notes | Audit outcomes + governance actions |

## How Specsmith wraps BMAD workflows
Specsmith does not require replacing BMAD planning practices. Instead, BMAD artifacts become governed inputs: preflight mints tracked work items, implementation is verified, and audit artifacts capture final evidence.

## Example agent contract
```json
{
  "intent": "Implement BMAD task T-042 with tests",
  "governance": {
    "preflight_required": true,
    "verify_required": true,
    "audit_required": true
  }
}
```

## Import and bridge path
- Use `specsmith import bmad` (stub command path) to scaffold mappings.
- Keep BMAD artifact naming while linking to requirement IDs and tests.
- Incrementally enforce governance checkpoints on high-risk changes first.

## Risks and limitations
- Mapping quality depends on artifact consistency in existing BMAD repos.
- Initial migration can surface requirement/test gaps that need manual curation.
- Teams should agree on a shared minimum governance policy before broad rollout.
