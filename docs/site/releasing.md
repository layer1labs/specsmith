# Immutable Specsmith release runbook

Specsmith releases are prepared and published only by repository-local GitHub
Actions. The installed public CLI can audit a user project with
`specsmith verify-release`; it cannot release Specsmith.

## Maintainer sequence

1. Create a reviewed `release/<version>` branch and finish version metadata,
   changelog, README, migration notes, API surface, and governance sources.
2. Dispatch **Prepare Release** in `prepare` mode. It builds an sdist, builds the
   wheel from that sdist, installs the exact wheel in isolation, applies candidate
   governance, and permits only allowlisted generated changes.
3. Review the generated patch and candidate closure manifest. The workflow commits
   candidate-owned changes only to the originating release branch.
4. The workflow rebuilds the candidate and runs `check`; the second pass must be
   clean and all package, project, governance, and expected-tag versions must match.
5. Generate the deterministic pre-release governance seal and include it with the
   reviewed release artifacts before merging.
6. Merge the fixed-point release PR to `main`, then create `v<version>` on that exact
   approved main commit.
7. The tag workflow proves main ancestry and closure, builds one canonical sdist and
   wheel, verifies their digests, rejects an existing PyPI version, and publishes the
   same artifacts to GitHub Releases and PyPI.
8. After publication, create a post-publication receipt that references the seal,
   tag, commit, workflow run, and independently verified published artifact digests.
   Attach it externally to the GitHub Release; do not commit it into the tagged tree.

## Evidence boundary

The pre-release seal proves candidate governance closure and artifact identity; it
cannot prove future publication. The post-publication receipt proves what external
services received and cryptographically links that evidence to the prior seal.
Schemas live under `docs/release-evidence/`.

## Recovery matrix

| Failure | Required recovery |
|---|---|
| Candidate produces expected changes | Review and commit them on the release branch, then rerun check. |
| Candidate produces unexpected files | Stop; correct the generator or allowlist in a new reviewed commit. |
| Second pass is dirty | Do not merge or tag; restore deterministic closure. |
| Version parity fails | Correct all version anchors on the release branch. |
| Tag is not on main | Do not publish; create a new correct tag only if nothing was published. |
| PyPI version already exists | Stop. Never skip or overwrite it; prepare a new version. |
| GitHub Release succeeds but PyPI fails | Record an incomplete receipt and repair with a new version if artifacts could conflict. |
| Published digest mismatches | Mark the receipt failed, preserve evidence, and issue a new version. |

Published tags and package versions are immutable. After publication, every
correction uses a new commit and a new version.
