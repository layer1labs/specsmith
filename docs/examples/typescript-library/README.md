# Example: TypeScript Library
## Project type
Reusable TypeScript package with governed release quality checks.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith req add --id REQ-001 --title "Public API behavior"`
3. `specsmith test add --req REQ-001 --title "Verify the public API" --type unit`
4. `specsmith preflight "Implement the public API behavior. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/library.yml`

## Tests file example
`docs/tests/library-tests.yml`

## CI snippet
```yaml
- name: Governed TS library checks
  run: |
    npm test
    specsmith audit --project-dir .
```

## Agent integration file example
`AGENTS.md`
