# Examples

These examples show the same lean workflow in different repositories. Specsmith
does not replace each ecosystem's formatter, test runner, CI, or coding agent.
It tracks the requirement, enforces the linked test, compresses verified context,
and records evidence around those tools.

Start with one of these three:

- `python-cli-app/` — smallest conventional project example.
- `ai-agent-app/` — MCP and coding-agent integration.
- `regulated-high-assurance-demo/` — adds a release approval without changing
  the core development loop.

The remaining directories are syntax variants for common ecosystems. Every
example follows this sequence:

```bash
specsmith import --project-dir . --yes
specsmith req add --title "Describe one observable behavior"
specsmith test add --req REQ-001 --title "Prove that behavior"
specsmith preflight "Implement the behavior. Scope: REQ-001" --json
# Let the host tool edit and run its native tests.
specsmith audit --project-dir .
specsmith checkpoint --project-dir .
```

Use `specsmith integrate <tool>` for a supported coding-agent adapter, or
`specsmith run` to use Grace as a local fallback.
