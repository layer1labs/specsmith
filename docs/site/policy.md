# Policy

Policy is a small overlay on Specsmith's core contract: describe the change,
link it to requirements and tests, run the real tests, and preserve evidence.
It is not a second workflow engine or a legal-compliance certificate.

Store the policy at `.specsmith/policy.yml`.

```yaml
required_preflight: true
required_tests: true
required_human_approval:
  - release
risk_threshold: high
command_denylist:
  - git reset --hard
  - git push --force
evidence_requirements:
  - diff
  - tests
  - audit
```

## Fields

| Field | Meaning |
|---|---|
| `required_preflight` | Require an accepted intent decision before edits. Keep this enabled. |
| `required_tests` | Require linked test cases. Keep this enabled. |
| `required_human_approval` | Optional gates: `requirement`, `plan`, `implementation`, `verification`, or `release`. |
| `risk_threshold` | One of `low`, `medium`, `high`, or `critical`. |
| `file_rules` | Per-path overrides for repositories that genuinely need them. |
| `agent_allowlist` | Optional names of allowed agent integrations, such as `grace`. |
| `command_allowlist` | Optional commands an execution integration may run. |
| `command_denylist` | Destructive commands an integration must reject. |
| `evidence_requirements` | Evidence labels the project expects to retain. |

Start with [the permissive example](https://github.com/layer1labs/specsmith/blob/main/examples/policies/permissive-policy.yml)
for ordinary projects or [the strict example](https://github.com/layer1labs/specsmith/blob/main/examples/policies/strict-policy.yml)
when releases require explicit approval. Avoid adding gates that do not improve
requirements, tests, evidence quality, or safe execution.

## Check a policy

```bash
specsmith policy validate --project-dir .
specsmith policy simulate --work-item WI-123 --project-dir . --json
```

`simulate` explains missing linked tests, approvals, and evidence without making
repository changes.

Record a configured approval explicitly:

```bash
specsmith approve release --work-item WI-123 --rationale "Release evidence reviewed"
```
