# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.15.x  | ✅ Current |
| 0.14.x  | ⚠ Security fixes only |
| < 0.14.0 | ❌ No longer supported |

## Reporting a Vulnerability

If you discover a security vulnerability in specsmith, please report it responsibly:

1. **Do NOT open a public issue.**
2. Email: **info@layer1labs.com**
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will acknowledge receipt within **48 hours** and aim to provide a fix or mitigation within **7 days** for critical issues.

You may also use [GitHub's private security advisory](https://github.com/layer1labs/specsmith/security/advisories/new) workflow.

## Scope

This policy covers:
- The `specsmith` CLI tool and its dependencies
- Generated scaffold files and templates
- CI/CD workflows and configuration files

## Security Practices

- Dependencies are monitored by Dependabot (GitHub) and Renovate (GitLab/Bitbucket)
- CI runs `pip-audit` on every push to detect known vulnerabilities
- All agent-invoked commands enforce timeouts to prevent hung processes
- No secrets are stored in generated scaffold files
