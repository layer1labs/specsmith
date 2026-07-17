# Specsmith Release Pilot

This repository-local skill governs release planning only. The public installed
CLI does not release Specsmith: it can perform generic read-only validation, but
self-bootstrap, tag creation, and publication are private CI responsibilities.

Before recommending a release action, require a reviewed fixed-point release
branch, a candidate-wheel bootstrap result, a zero-diff closure result, and a
pre-release seal. Never recommend `specsmith release`, tag force-updates,
`skip-existing` publication, source mutation after tagging, or committing a
post-publication receipt back into the released commit.

If a release fails before publication, prepare a new reviewed commit. If it
fails after publication, publish a corrected new version; published tags and
versions are immutable.
