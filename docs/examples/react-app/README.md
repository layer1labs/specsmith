# Example: React App
## Project type
Frontend React application with requirements, test mapping, and governance checkpoints.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith req add --title "Describe the visible UI behavior"`
3. `specsmith test add --req REQ-001 --title "Verify the UI behavior" --type e2e`
4. `specsmith preflight "Implement the UI behavior. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/frontend.yml`

## Tests file example
`docs/tests/frontend-tests.yml`

## CI snippet
```yaml
- name: Governed frontend pipeline
  run: |
    npm test -- --runInBand
    specsmith audit --project-dir .
```

## Agent integration file example
`docs/site/agent-integrations.md`
