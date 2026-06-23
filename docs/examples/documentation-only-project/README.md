# Example: Documentation-Only Project
## Project type
Documentation-centric repository governed for consistency and traceability.

## Governance setup steps
1. `specsmith init`
2. `specsmith preflight "update docs set"`
3. `specsmith audit`

## Requirements file example
`docs/requirements/docs.yml`

## Tests file example
`docs/tests/docs-tests.yml`

## CI snippet
```yaml
- name: Governed docs checks
  run: |
    specsmith sync --check
    specsmith audit
```

## Agent integration file example
`AGENTS.md`
