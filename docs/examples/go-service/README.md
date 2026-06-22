# Example: Go Service
## Project type
Go microservice with governed change intent and verification.

## Governance setup steps
1. `specsmith init`
2. `specsmith preflight "add go service endpoint"`
3. `specsmith audit`

## Requirements file example
`docs/requirements/service.yml`

## Tests file example
`docs/tests/service-tests.yml`

## CI snippet
```yaml
- name: Governed Go service checks
  run: |
    go test ./...
    specsmith verify
```

## Agent integration file example
`docs/site/agents.md`
