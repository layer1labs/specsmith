# Security and Threat Model

This document defines SpecSmith security assumptions, primary threats, and hardening guidance for production use.

## Security assumptions

- The host OS, Python runtime, and package manager are maintained and patched.
- Access to repository write permissions is controlled by the organization.
- CI secrets are scoped and rotated by operators.
- Human maintainers review governance policy and critical changes.
- Cryptographic primitives (SHA-256 usage in chain linking) are not replaced with weaker variants.

## Non-goals

- SpecSmith does not provide legal compliance guarantees.
- SpecSmith does not replace endpoint security, IAM, or network segmentation.
- SpecSmith does not claim to prevent all malicious prompts or supply-chain compromise.
- SpecSmith does not guarantee that third-party MCP tools are safe.

## Threats and controls

## 1) Prompt injection
- Threat: adversarial prompt text attempts to bypass governance.
- Primary controls: preflight gating, requirement/test linkage, audit trace, least-privilege agent permissions.
- Residual risk: social engineering of human operators.

## 2) Malicious repository content
- Threat: repository files include hostile instructions or unsafe scripts.
- Primary controls: policy checks before execution, explicit preflight decisions, human review checkpoints.
- Residual risk: trusted maintainer merges harmful code.

## 3) Compromised agent runtime
- Threat: an agent process is hijacked or behaves unexpectedly.
- Primary controls: bounded retries, explicit tool permissions, audit logging, kill-session controls.
- Residual risk: host-level compromise outside SpecSmith control.

## 4) Forged audit records
- Threat: attacker edits historical records to hide actions.
- Primary controls: append-only patterns, hash-chain linkage, trace verification.
- Residual risk: attacker controls storage and rewrites entire chain with key material access.

## 5) Tampered ledger
- Threat: log truncation or out-of-order insertion.
- Primary controls: monotonic sequence fields, chained hashes, verification tooling.
- Residual risk: delayed detection if verification is not run.

## 6) MCP tool abuse
- Threat: MCP tools are used for unsafe operations or data exfiltration.
- Primary controls: explicit tool allow/deny policy, bounded scope, provenance review for external servers.
- Residual risk: permissive policy profiles in high-risk environments.

## 7) Generated CI misuse
- Threat: generated pipelines execute dangerous steps or leak secrets.
- Primary controls: mandatory review of generated CI files, branch protections, scoped CI tokens.
- Residual risk: over-privileged runners or unmanaged self-hosted agents.

## 8) Secrets leakage
- Threat: credentials appear in prompts, logs, exports, or artifacts.
- Primary controls: secret redaction discipline, environment-variable usage, restricted report sharing.
- Residual risk: user copies sensitive values into plain-text artifacts.

## 9) Path traversal
- Threat: untrusted input accesses files outside intended project scope.
- Primary controls: canonical path checks, strict path allowlists for project-root operations.
- Residual risk: custom integrations that skip canonicalization.

## 10) Command injection
- Threat: untrusted text is executed by shell wrappers.
- Primary controls: validated command templates, argument escaping, denylisted dangerous patterns.
- Residual risk: integrations that pass raw user strings to shell.

## Hardening recommendations

- Enforce branch protection and required reviews for policy, CI, and governance changes.
- Run `specsmith audit` and `specsmith trace verify` in CI on every pull request.
- Keep agent permissions at least-privilege profiles by default.
- Restrict outbound network and MCP server allowlists in production.
- Rotate credentials and separate read/write CI tokens.
- Store exports containing governance evidence in access-controlled locations.
- Pin dependency versions and patch security advisories quickly.

## Secure deployment checklist

- [ ] Branch protections and CODEOWNERS for governance files are enabled.
- [ ] CI executes `audit`, `sync --check`, and trace verification.
- [ ] Agent permissions are restricted (no broad admin profile by default).
- [ ] MCP servers are approved and documented with owner and scope.
- [ ] Secrets are managed by secret manager / CI vault, not committed files.
- [ ] Release process includes security review for CLI/API/schema changes.
- [ ] Incident contacts and reporting workflow are documented.

## Responsible disclosure policy

- Report vulnerabilities privately through:
  - GitHub Security Advisories: https://github.com/layer1labs/specsmith/security/advisories/new
  - Email: security@layer1labs.ai
- Include impact, affected versions, reproduction steps, and mitigation ideas.
- Do not disclose publicly until maintainers confirm remediation guidance.

