# Branch Workflows

New Specsmith projects use the `single-branch` workflow by default. Governed work,
verification, commits, and pushes happen directly on the configured default branch,
normally `main`.

This is intentionally conservative: Specsmith does not create feature branches or
pull requests until a project explicitly opts into a branching workflow.

## Check Or Enable A Workflow

Show the current workflow:

```bash
specsmith branch workflow
```

Enable one of the supported branching workflows for the current project:

```bash
specsmith branch workflow gitflow
specsmith branch workflow trunk-based
specsmith branch workflow github-flow
```

The command records the selection in `scaffold.yml`. Once selected,
`specsmith branch create` and `specsmith pr` use that workflow's rules.

## Single-Branch Behavior

While `single-branch` is active:

- `specsmith branch create` refuses to create a branch.
- `specsmith pr` refuses to open a pull request.
- Governed commits and pushes to `main` remain available.

To return to direct governed work, run:

```bash
specsmith branch workflow single-branch
```
