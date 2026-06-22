# Example: FastAPI Service
## Project type
Python FastAPI backend service with API governance overlays.

## Governance setup steps
1. `specsmith init`
2. `specsmith req list`
3. `specsmith preflight "add endpoint"`

## Requirements file example
`docs/requirements/api.yml`

## Tests file example
`docs/tests/api-tests.yml`

## CI snippet
```yaml
- name: Verify governed API changes
  run: |
    specsmith preflight "ci-api-check" --json
    python -m pytest tests/ -q
```

## Agent integration file example
`.agents/skills/specsmith/SKILL.md`
