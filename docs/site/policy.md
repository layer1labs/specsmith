# Governance Policy
Policy file path: `.specsmith/policy.yml`.
Validate policy:
```bash
specsmith policy validate
```
Simulate policy gates for a work item:
```bash
specsmith policy simulate --work-item WI-ABCDEF12 --json
```
Recognized policy keys:
- `required_preflight`
- `required_tests`
- `required_human_approval`
- `risk_threshold`
- `file_rules`
- `agent_allowlist`
- `command_allowlist`
- `command_denylist`
- `evidence_requirements`
