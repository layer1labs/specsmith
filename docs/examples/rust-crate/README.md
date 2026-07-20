# Example: Rust Crate
## Project type
Rust crate with requirement coverage and audit-backed release flow.

## Governance setup steps
1. `specsmith import --project-dir . --yes`
2. `specsmith req add --title "Describe the crate behavior"`
3. `specsmith test add --req REQ-001 --title "Verify the crate behavior" --type unit`
4. `specsmith preflight "Implement the crate behavior. Scope: REQ-001" --json`

## Requirements file example
`docs/requirements/rust.yml`

## Tests file example
`docs/tests/rust-tests.yml`

## CI snippet
```yaml
- name: Governed Rust checks
  run: |
    cargo test --quiet
    specsmith audit --project-dir .
```

## Agent integration file example
`.specsmith/config.yml`
