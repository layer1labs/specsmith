# Governed PR Action
The governed PR action runs `specsmith audit`, evaluates governance linkage, and posts a PR comment with status fields for work item linkage, requirements/tests linkage, verification, audit chain status, and risk level.
## Usage
Add this step to `.github/workflows/<workflow>.yml`:
```yaml
uses: ./.github/actions/governed-pr
with:
  project-dir: .
  work-item-id: WI-ABCDEF12
  required-check: "true"
```
`required-check: "true"` exits non-zero when governance gaps are found.
## Example PR Comment
```text
## Specsmith Governance Status
- Linked work item: ✅ `WI-ABCDEF12`
- Linked requirement: ✅
- Linked tests: ✅
- Verification status: ✅
- Audit chain status: ✅
- Risk level: `medium`
### Governance gaps
- None
```
