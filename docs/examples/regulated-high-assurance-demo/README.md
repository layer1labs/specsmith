# Example: Regulated / High-Assurance Demo
## Project type
High-assurance project with strict traceability and evidence export requirements.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. Copy `examples/policies/strict-policy.yml` to `.specsmith/policy.yml`.
3. Add one requirement and its linked test.
4. `specsmith preflight "Implement the governed behavior. Scope: REQ-001" --json`
5. Run native tests, `specsmith audit`, and obtain the configured release approval.

## Requirements file example
`docs/requirements/compliance.yml`

## Tests file example
`docs/tests/compliance-tests.yml`

## CI snippet
```yaml
- name: High-assurance governance gate
  run: |
    pytest -q
    specsmith audit --project-dir .
    specsmith checkpoint --project-dir .
```

## Agent integration file example
`AGENTS.md`; add only the focused Specsmith integration skill required by the host.
