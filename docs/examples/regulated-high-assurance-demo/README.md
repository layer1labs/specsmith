# Example: Regulated / High-Assurance Demo
## Project type
High-assurance project with strict traceability and evidence export requirements.

## Governance setup steps
1. `specsmith init`
2. `specsmith preflight "regulated change"`
3. `specsmith verify`
4. `specsmith export`

## Requirements file example
`docs/requirements/compliance.yml`

## Tests file example
`docs/tests/compliance-tests.yml`

## CI snippet
```yaml
- name: High-assurance governance gate
  run: |
    specsmith audit
    specsmith export --format json > compliance.json
```

## Agent integration file example
`docs/skills/specsmith-audit/SKILL.md`
