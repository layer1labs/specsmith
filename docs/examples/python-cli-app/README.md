# Example: Python CLI App
## Project type
Command-line Python application with governed requirements and tests.

## Governance setup steps
1. `specsmith init`
2. `specsmith sync`
3. `specsmith audit`

## Requirements file example
`docs/requirements/cli.yml`

## Tests file example
`docs/tests/cli-tests.yml`

## CI snippet
```yaml
- name: Governance checks
  run: |
    specsmith sync --check
    specsmith audit
```

## Agent integration file example
`AGENTS.md`
