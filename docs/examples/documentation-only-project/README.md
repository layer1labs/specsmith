# Example: Documentation-Only Project
## Project type
Documentation-centric repository governed for consistency and traceability.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith req add --title "Describe the documentation contract"`
3. `specsmith test add --req REQ-001 --title "Build and check links" --type build`
4. `specsmith preflight "Update the documentation. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/docs.yml`

## Tests file example
`docs/tests/docs-tests.yml`

## CI snippet
```yaml
- name: Governed docs checks
  run: |
    mkdocs build --strict
    specsmith audit --project-dir .
```

## Agent integration file example
`AGENTS.md`
