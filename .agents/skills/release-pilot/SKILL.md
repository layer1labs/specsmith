# Release Pilot Skill

## Preconditions (abort if any fail)
- `gh run list --branch develop --limit 1 --json conclusion` = `SUCCESS`.
- `gh pr list --state open --base main` returns 0 open PRs.
- `CHANGELOG.md` has the new version section already drafted.
- `specsmith audit && specsmith validate --strict` clean on develop.

## Important: `main` is protected
`main` requires changes to land via a pull request and does NOT accept direct
pushes or fast-forward pushes. Do NOT use `git merge --ff-only develop` followed
by `git push origin main` — it will be rejected. Releases reach `main` through a
PR merge, and each release tag points to the **merge commit on `main`** (see the
existing `v0.19.2` / `v0.19.1` tags, which sit on `Merge pull request` commits).

## Sequence
1. Bump version: `specsmith release <version>`.
2. `git add -A && git commit -m 'release: v<version>'`.
3. Push develop: `git push origin develop`.
4. Wait for CI on develop to go green: `gh run watch <run-id> --exit-status`
   (confirm both the `CI` and `CodeQL` workflows succeed).
5. Open the release PR: `gh pr create --base main --head develop --title 'release: v<version>'`.
6. Merge the PR (creates the merge commit on `main`):
   `gh pr merge <pr> --merge --admin` (admin merge satisfies branch protection).
7. Fetch and tag the **main merge commit**, not the develop tip:
   `git fetch origin main` then
   `git tag -a v<version> $(git rev-parse origin/main) -m 'v<version>'`.
8. Push the tag: `git push origin v<version>`.
9. The `Release` workflow (triggered by the `v*` tag) handles PyPI upload +
   GitHub Release automatically. It is idempotent: `pypi-publish` uses
   `skip_existing: true` and `github-release` no-ops if the release already
   exists, so a corrective re-tag (`git tag -f` + `git push --force origin v<version>`)
   is safe.

## Rollback
- Before the PR merges: `git push origin --delete <feature>` is not needed; just
  close the PR. To undo the local version bump: `git reset --hard HEAD~1` on develop
  (force-push develop only if already pushed and safe to do so).
- After tagging, to repoint a mis-placed tag: `git tag -f -a v<version> <correct-sha> -m 'v<version>'`
  then `git push --force origin v<version>` (safe — Release workflow is idempotent).
