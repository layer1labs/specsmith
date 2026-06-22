# Example: React App
## Project type
Frontend React application with requirements, test mapping, and governance checkpoints.

## Governance setup steps
1. `specsmith init`
2. `specsmith sync`
3. `specsmith preflight "implement UI change"`

## Requirements file example
`docs/requirements/frontend.yml`

## Tests file example
`docs/tests/frontend-tests.yml`

## CI snippet
```yaml
- name: Governed frontend pipeline
  run: |
    specsmith audit
    npm test -- --runInBand
```

## Agent integration file example
`docs/site/agent-integrations.md`
