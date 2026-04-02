# Release Workflow

specsmith uses **gitflow** branching with **SemVer** versioning and **Keep a Changelog** format.

## Branches

- **`main`** — Production. Every commit is a released version. Tags trigger PyPI publish.
- **`develop`** — Integration. Features merge here first. When ready for release, merge to main.
- **`feature/*`** — Branch from `develop`, merge back to `develop` via PR.
- **`hotfix/*`** — Branch from `main` for urgent fixes, merge to **both** `main` and `develop`.
- **`release/*`** — Optional. Branch from `develop` for release prep, merge to `main` + `develop`.

## Feature Release (minor/patch)

When features on `develop` are ready for release:

```bash
# 1. Ensure develop is clean
git checkout develop
pytest tests/ -q && ruff check src/ tests/ && mypy src/

# 2. Bump version in ALL places
#    - pyproject.toml (version)
#    - src/specsmith/__init__.py (__version__)
#    - src/specsmith/config.py (spec_version default)
#    - tests/test_smoke.py (version assertion)
#    - tests/test_cli.py (version assertion + upgrade test)

# 3. Update CHANGELOG.md
#    - Move [Unreleased] items into new [X.Y.Z] - YYYY-MM-DD section
#    - Update comparison links at bottom

# 4. Update docs if needed
#    - docs/site/*.md (remove any alpha/pre-release references)
#    - README.md (install command, version references)

# 5. Commit on develop
git add -A && git commit -m "release: vX.Y.Z"

# 6. Merge develop → main
git checkout main
git merge develop --no-edit

# 7. Tag on main
git tag -a vX.Y.Z -m "vX.Y.Z — description"

# 8. Merge back to develop (so develop has the version bump)
git checkout develop
git merge main --no-edit

# 9. Push everything
git push origin main develop --tags

# 10. Verify
#     - CI passes on main
#     - Release workflow: build ✓, pypi-publish ✓, github-release ✓
#     - pip index versions specsmith → shows new version
#     - RTD rebuilds with updated docs
```

## Hotfix Release

For urgent fixes (security vulnerabilities, critical bugs) that can't wait for the next feature release:

```bash
# 1. Branch from main
git checkout -b hotfix/description main

# 2. Apply fix (or cherry-pick from develop if already fixed there)
git cherry-pick <commit>

# 3. Bump PATCH version (X.Y.Z → X.Y.Z+1) in all 5 places

# 4. Add ### Security or ### Fixed section to CHANGELOG.md

# 5. Commit
git add -A && git commit -m "release: vX.Y.Z+1 — hotfix description"

# 6. Merge to main + tag
git checkout main
git merge hotfix/description --no-edit
git tag -a vX.Y.Z+1 -m "vX.Y.Z+1 — hotfix"

# 7. Merge to develop
git checkout develop
git merge hotfix/description --no-edit

# 8. Delete hotfix branch
git branch -d hotfix/description

# 9. Push everything
git push origin main develop --tags
```

## Version Locations

The version has a **single source of truth**: `pyproject.toml`.

All other code reads it dynamically via `importlib.metadata.version()`.

| File | How version is obtained |
|------|------------------------|
| `pyproject.toml` | **Source of truth** — `version = "X.Y.Z"` |
| `src/specsmith/__init__.py` | `importlib.metadata.version("specsmith")` at runtime |
| `src/specsmith/config.py` | `spec_version` default (for new scaffolds) |
| `docs/site/*.md` | `{{ version }}` replaced by MkDocs hook at build time |
| Tests | Compare against `importlib.metadata.version()` |

When releasing, `specsmith release X.Y.Z` updates `pyproject.toml` and `config.py`.

## CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added      ← new features
### Changed    ← changes to existing features
### Deprecated ← soon-to-be removed features
### Removed    ← removed features
### Fixed      ← bug fixes
### Security   ← vulnerability fixes
```

## Pre-Release Checklist

Before EVERY release (feature or hotfix), verify:

- [ ] Version bumped in all 5 places (see above)
- [ ] CHANGELOG.md has dated section with correct comparison links
- [ ] `pyproject.toml` classifier matches release status (not "Alpha" for stable)
- [ ] No stale alpha/pre-release references in docs or README
- [ ] `pip install specsmith` (not `--pre`) in all install instructions
- [ ] `python -m pytest tests/ -q` passes
- [ ] `ruff check src/ tests/` passes
- [ ] `mypy src/` passes  
- [ ] `specsmith audit --project-dir .` passes
- [ ] All open code scanning alerts resolved

## Post-Release Verification

After pushing the tag:

- [ ] CI passes on main
- [ ] Release workflow: build ✓, pypi-publish ✓, github-release ✓
- [ ] `pip index versions specsmith` shows new version as LATEST
- [ ] PyPI page (pypi.org/project/specsmith/) shows correct README and classifier
- [ ] RTD rebuilds with updated docs
- [ ] shields.io badge refreshes (may take 5 min)
- [ ] GitHub repo README renders correct badge version

## Automated Publishing

### Stable Releases (main branch)
When a tag matching `v*` is pushed to `main`, the release workflow automatically:

1. **Builds** sdist + wheel
2. **Publishes to PyPI** via OIDC trusted publishing (no tokens needed)
3. **Creates GitHub Release** with auto-generated notes and artifacts

Install: `pip install specsmith`

### Dev Releases (develop branch)
Every push to `develop` triggers the dev-release workflow:

1. **Calculates** dev version: `X.Y.(Z+1).devN` where Z is the current patch and N is commits since last tag
2. **Builds** sdist + wheel with dev version
3. **Publishes to PyPI** as a pre-release

Example: if stable is `0.1.3`, dev builds are `0.1.4.dev1`, `0.1.4.dev2`, etc.

Install: `pip install --pre specsmith`

Dev releases let users test features before they ship in a stable release. The next-patch `.devN` suffix ensures they sort correctly between stable versions.

## Lessons Learned

- **PyPI README is baked at upload time** — if README changes after a release, they won't appear on PyPI until the next release. Always finalize README before tagging.
- **PyPI classifiers are baked at upload time** — changing `Development Status` in pyproject.toml requires a new release to take effect on PyPI.
- **shields.io badges cache for ~5 minutes** — don't panic if the badge shows the old version immediately after release.
- **Hotfixes must include ALL changes** — not just the code fix. Version bump, CHANGELOG, docs, and classifiers must all be in the hotfix commit.
