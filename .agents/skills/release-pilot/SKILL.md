# Release Pilot Skill

## Preconditions (abort if any fail)
- `gh run list --branch develop --limit 1 --json conclusion` = `SUCCESS`.
- `gh pr list --state open --base main` returns 0 open PRs.
- `CHANGELOG.md` has the new version section already drafted.
- `specsmith audit && specsmith validate --strict` clean on develop.

## Sequence
1. Bump version: `specsmith release <version>`.
2. `git add -A && git commit -m 'release: v<version>'`.
3. Push develop: `git push origin develop`.
4. Wait for CI: `gh run watch`.
5. Merge to main: `git checkout main && git merge --ff-only develop`.
6. Tag: `git tag -a v<version> -m 'v<version>'`.
7. Push: `git push origin main --tags`.
8. Release workflow handles PyPI upload + GitHub Release automatically.

## Rollback
If step 7 fails: `git tag -d v<version> && git reset --hard HEAD~1`.
