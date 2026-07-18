---
name: release
description: Validate release readiness for a governed project without publishing or tag mutation.
---

# Release Readiness

Use this skill to establish whether a governed project is ready for its own
maintainer-led release process. It is deliberately read-only: it does not create
releases, tags, deployments, uploads, or promotions.

## Public boundary

The installed Specsmith CLI may audit and validate a user's project. It must not
publish Specsmith itself or manage the Layer1Labs release pipeline. Those actions
belong to repository-local CI with explicit maintainer review.

## Read-only checks

```bash
specsmith audit --project-dir .
specsmith validate --strict --project-dir .
specsmith verify-release --project-dir .
```

Resolve every reported issue before handing the project to the responsible
release process. These checks do not replace a project's own artifact, signing,
or publication controls.

## Safety

- Do not invoke a `specsmith release` command; it is intentionally not public.
- Do not create, move, or force-update tags.
- Do not upload packages or use publication credentials from this skill.
- Treat immutable published versions as requiring a new version to correct.
