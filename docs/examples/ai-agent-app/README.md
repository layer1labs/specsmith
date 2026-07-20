# Example: AI Agent App
## Project type
Agent-driven application with governance gates and MCP-aware workflows.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith integrate <host-tool>` or configure the Specsmith MCP server
3. `specsmith req add --title "Describe the agent-visible behavior"`
4. `specsmith test add --req REQ-001 --title "Verify the agent-visible behavior" --type integration`
5. `specsmith preflight "Implement the agent behavior. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/agent.yml`

## Tests file example
`docs/tests/agent-tests.yml`

## CI snippet
```yaml
- name: Governed agent checks
  run: |
    pytest -q
    specsmith audit --project-dir .
    specsmith checkpoint --project-dir .
```

## Agent integration file example
Use the host agent's native integration; use `specsmith run` only when Grace is
the desired local fallback.
