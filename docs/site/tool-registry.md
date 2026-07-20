# Verification tool registry

Specsmith does not provide a second general-purpose agent tool ecosystem. It
records and enforces the native validation tools already used by a project.

## Purpose

The registry maps project metadata to evidence categories:

| Category | Typical evidence |
|---|---|
| lint | Ruff, ESLint, Clippy, golangci-lint |
| type checking | mypy, TypeScript, `cargo check`, `go vet` |
| tests | pytest, Vitest, Cargo test, Go test |
| security | pip-audit, npm audit, cargo audit, govulncheck |
| build | package build, compiler, container build |
| formatting | formatter check mode, never an unreviewed rewrite |
| domain checks | project-owned validators required by policy |

`specsmith doctor` reports whether declared tools are locally available.
`specsmith audit` checks that required evidence and CI references are present.
The host or CI runner executes the tools and returns observed results to
verification.

## Flow

```text
project configuration
  -> expected native validators
  -> host/CI execution
  -> observed result evidence
  -> requirement and linked-test verification
```

## Overrides

Projects can declare their own validators in configuration. An override changes
the expected evidence; it does not grant Specsmith permission to install tools or
replace user-owned CI. Generated CI uses check-only formatter modes and preserves
existing project configuration unless the user explicitly requests regeneration.

## Cross-platform behavior

Adapters normalize path and executable discovery for Windows, Linux, and macOS.
Platform-specific commands may differ, but the evidence contract is identical:
the executed command, exit status, relevant output, requirement/test scope, and
provenance are retained.

## Agent boundary

Coding agents keep their native filesystem, shell, Git, browser, framework, and
cloud tools. Specsmith integrations exchange only mutation intent, accepted
requirements, linked tests, uncertainty, and validation evidence. This keeps
context small and avoids duplicating capabilities that host tools already provide.
