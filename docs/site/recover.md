# Recover
`specsmith recover` summarizes the last known good state, likely failed step, impacted requirements/tests, and recommends rollback vs retry guidance.
Examples:
```bash
specsmith recover --work-item WI-ABCDEF12 --json
git --no-pager diff | specsmith recover --git-diff --work-item WI-ABCDEF12
specsmith recover --test-results .specsmith/test-results.json
```
