# Example: Rust Crate
## Project type
Rust crate with requirement coverage and audit-backed release flow.

## Governance setup steps
1. `specsmith init`
2. `specsmith preflight "implement crate feature"`
3. `specsmith verify`

## Requirements file example
`docs/requirements/rust.yml`

## Tests file example
`docs/tests/rust-tests.yml`

## CI snippet
```yaml
- name: Governed Rust checks
  run: |
    cargo test --quiet
    specsmith audit
```

## Agent integration file example
`.specsmith/config.yml`
