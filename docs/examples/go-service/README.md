# Example: Go Service
## Project type
Go microservice with governed change intent and verification.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith req add --title "Define the service behavior"`
3. `specsmith test add --req REQ-001 --title "Verify the service behavior" --type integration`
4. `specsmith preflight "Implement the service behavior. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/service.yml`

## Tests file example
`docs/tests/service-tests.yml`

## CI snippet
```yaml
- name: Governed Go service checks
  run: |
    go test ./...
    specsmith audit --project-dir .
```

## Agent integration file example
`docs/site/agents.md`
