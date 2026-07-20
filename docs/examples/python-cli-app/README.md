# Example: Python CLI App
## Project type
Command-line Python application with governed requirements and tests.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith req add --title "Document one CLI behavior"`
3. `specsmith test add --req REQ-001 --title "Exercise that behavior" --type cli`
4. `specsmith preflight "Implement the CLI behavior. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/cli.yml`

## Tests file example
`docs/tests/cli-tests.yml`

## CI snippet
```yaml
- name: Governance checks
  run: |
    ruff check .
    pytest -q
    specsmith audit --project-dir .
```

## Agent integration file example
`AGENTS.md` or `specsmith run` (Grace local fallback)
