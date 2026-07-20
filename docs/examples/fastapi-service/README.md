# Example: FastAPI Service
## Project type
Python FastAPI backend service with API governance overlays.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith req add --title "Define the endpoint contract"`
3. `specsmith test add --req REQ-001 --title "Verify the endpoint contract" --type integration`
4. `specsmith preflight "Implement the endpoint. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/api.yml`

## Tests file example
`docs/tests/api-tests.yml`

## CI snippet
```yaml
- name: Verify governed API changes
  run: |
    python -m pytest tests/ -q
    specsmith audit --project-dir .
```

## Agent integration file example
`AGENTS.md` plus the host agent's native test tools
