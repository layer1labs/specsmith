# Example: AI Agent App
## Project type
Agent-driven application with governance gates and MCP-aware workflows.

## Governance setup steps
1. `specsmith init`
2. `specsmith mcp serve`
3. `specsmith preflight "agent task implementation"`

## Requirements file example
`docs/requirements/agent.yml`

## Tests file example
`docs/tests/agent-tests.yml`

## CI snippet
```yaml
- name: Governed agent checks
  run: |
    specsmith audit
    specsmith checkpoint
```

## Agent integration file example
`docs/site/warp-integration.md`
