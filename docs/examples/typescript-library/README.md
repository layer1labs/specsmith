# Example: TypeScript Library
## Project type
Reusable TypeScript package with governed release quality checks.

## Governance setup steps
1. `specsmith init`
2. `specsmith req add --id REQ-001 --title "Public API behavior"`
3. `specsmith verify`

## Requirements file example
`docs/requirements/library.yml`

## Tests file example
`docs/tests/library-tests.yml`

## CI snippet
```yaml
- name: Governed TS library checks
  run: |
    specsmith sync --check
    npm test
```

## Agent integration file example
`AGENTS.md`
