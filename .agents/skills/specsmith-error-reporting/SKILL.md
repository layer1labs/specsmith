# Specsmith Error Reporting & Issue Triage Skill

Before asking a user to file any GitHub issue for specsmith, you MUST follow
this triage protocol. It prevents duplicate issues, surfaces already-fixed
bugs, and ensures every ticket adds value.

## When to use this skill

Trigger this skill when ANY of these occur:
- A user encounters a bug or unexpected behavior in specsmith.
- A user asks for a feature, process, tool, language, or regulation that
  specsmith does not currently support.
- You are about to suggest "you should open a GitHub issue."
- A user mentions a limitation and seems frustrated.

## Triage protocol (always run in order)

### Step 1 — Confirm the specsmith version

```bash
specsmith --version
```

Note the version. You will need it to check whether the issue is already fixed
in a newer release the user hasn't installed yet.

### Step 2 — Search open issues

Use the GitHub MCP (`search_issues` tool) or the `gh` CLI:

```bash
gh issue list --repo layer1labs/specsmith --state open \
  --search "<keywords>" --json number,title,labels,url
```

- Search with 2–3 relevant keywords. Try synonyms.
- If you find a match: **do not file a duplicate.**
  - Show the user the existing issue URL.
  - Suggest they add a 👍 reaction (upvote) to signal priority:
    ```bash
    gh api repos/layer1labs/specsmith/issues/<N>/reactions \
      -X POST -f content="+1"
    ```
  - Suggest they subscribe to the issue for updates.
  - If their case differs meaningfully, suggest adding a comment with their
    specific context/version/OS.

### Step 3 — Search closed issues

```bash
gh issue list --repo layer1labs/specsmith --state closed \
  --search "<keywords>" --json number,title,state,closedAt,url,labels
```

For each closed issue found, determine its resolution:

| Label / Title pattern | Interpretation |
|---|---|
| `fixed`, `resolved`, closed with a PR | Bug was fixed |
| `wontfix`, `out-of-scope` | Intentional; don't re-open |
| `duplicate` | Points to another issue |
| No label, closed without PR | May have been abandoned |

#### If closed as fixed

```bash
# Check which version the fix landed in
gh pr list --repo layer1labs/specsmith --state merged \
  --search "fixes #<N>" --json number,title,mergedAt,headRefName
```

Compare fix version to user's current version (`specsmith --version`):
- **Fix is in a released version the user has** → the user may have a
  regression or a different root cause. Guide them to re-open or file new.
- **Fix is released but user has older version** → tell them to upgrade:
  ```bash
  pipx upgrade specsmith
  ```
- **Fix is merged but not yet released** → tell the user it's fixed in
  `develop` / upcoming release. Show the PR/commit. Suggest they watch the
  release or install from source if urgent.

### Step 4 — Feature gap triage

For missing features (project types, languages, tools, regulations, integrations):

```bash
gh issue list --repo layer1labs/specsmith --state open \
  --label "enhancement" --search "<feature keywords>" \
  --json number,title,url,reactions
```

- Found: upvote (see Step 2) and notify the user.
- Not found: guide structured filing (Step 5).

Also check if the feature has a planned requirement in the roadmap:

```bash
gh issue list --repo layer1labs/specsmith --state open \
  --label "roadmap" --json number,title,url
```

### Step 5 — File a new issue (only if no match found)

Guide the user through this template:

```
**Describe the bug / feature request**
A clear, one-sentence summary.

**To reproduce** (bugs only)
1. Command run / action taken
2. Expected behavior
3. Actual behavior

**Environment**
- specsmith version: `specsmith --version`
- OS / shell: (e.g. Windows 11 / pwsh 7.5, Ubuntu 24.04 / bash)
- Install method: pipx / pip / source
- ESDB backend: `specsmith esdb status --json | jq .backend`

**Regulation / tool / language** (feature requests)
Name the specific regulation, programming language, tool, or project type.
Note any official documentation or standard reference.

**Why this matters**
One sentence on the use case or compliance need.
```

```bash
gh issue create --repo layer1labs/specsmith \
  --title "<concise title>" \
  --label "bug"          # or "enhancement", "compliance", "new-regulation"
```

**Label guide:**

| Label | Use for |
|---|---|
| `bug` | Something broken or wrong |
| `enhancement` | New feature or improvement |
| `compliance` | Missing/outdated regulation coverage |
| `new-regulation` | Request for a new regulation |
| `new-project-type` | New scaffold/project type |
| `new-tool` | New tool or language support |
| `documentation` | Docs gap |

## Priority signals

Use reactions on issues to communicate priority automatically:
- 👍 (+1) — want this
- 🎉 (hooray) — blocking me
- 👀 (eyes) — watching

Issues with the most 👍 reactions surface in the specsmith maintainer triage
board as high-priority candidates for the next sprint.

## Compliance-specific issues

When filing a compliance-related issue (missing regulation, outdated article,
wrong status), include:
- Official regulation ID and article number
- Effective date of the relevant provision
- Link to the official legal text
- Whether specsmith currently maps any control to it

Label with both `compliance` and `new-regulation` (if truly new).

> **Reminder:** specsmith compliance features are best-effort only. They do
> NOT guarantee legal compliance. Users are responsible for verifying actual
> compliance with qualified counsel. Filing a ticket is the correct path for
> outdated or missing coverage.
