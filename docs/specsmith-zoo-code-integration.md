# Specsmith + Zoo Code Integration

Specsmith does not replace Zoo Code's models, editor tools, modes, or agent
workflow. It contributes a small portable contract: the active requirement,
its linked independent test, the accepted preflight decision, and compact
evidence with uncertainty preserved.

The maintained Read the Docs guide is
[Zoo Code / Roo Code](site/zoo-code-roo.md). It documents the supported setup,
doctor, uninstall, handoff, and local-provider commands.

## Supported workflow

```bash
specsmith zoo-code setup --project-dir .
specsmith zoo-code doctor --project-dir .
specsmith preflight "Implement REQ-001" --json

# Let Zoo Code edit and run the project's native tests.

specsmith audit --project-dir .
specsmith checkpoint --project-dir .
```

`setup` owns only marked Specsmith blocks and generated assets. Re-running it
repairs missing, older, or tampered managed configuration while preserving
unrelated user settings. The lifecycle implementation and tests use
platform-neutral paths and are exercised on Windows and Linux.

For a portable context envelope:

```bash
specsmith zoo-code export-handoff --project-dir . --output handoff.json
```

For a local LiteLLM profile:

```bash
specsmith zoo-code litellm setup --project-dir .
specsmith zoo-code litellm doctor --project-dir .
```

## What the benchmark does and does not show

The current complete GovernanceBench screen compares raw prompting, Cursor
rules, Specsmith LIGHT, and Specsmith FULL. It is not a direct Zoo Code versus
Zoo Code + Specsmith experiment, so no Zoo-Code-specific percentage improvement
is claimed.

Across the mixed seven-task GPT-5.6 Sol screen, LIGHT and FULL observed 21.8k
and 21.7k tokens per correct answer, compared with 25.4k raw and 32.3k for
Cursor rules. Coding-only correctness favored raw prompting. The practical
lesson for this integration is to keep the exported contract short, reject
ambiguity before model work, and enforce linked independent tests instead of
adding multiple generic custom modes or large skill bundles.

See the [full benchmark report](site/efficiency-benchmark.md) for task-level
results, confidence intervals, excluded-run provenance, and limitations.

## Integration boundary

Use Zoo Code for model selection, repository exploration, edits, terminals,
browser work, and its native modes. Use Specsmith for:

- requirement-to-test traceability;
- deterministic preflight and risk gates;
- independent verification evidence;
- bounded epistemic handoff and recovery; and
- comparable benchmark telemetry.

That boundary avoids duplicate prompt ceremony and keeps the cost of governance
proportional to the task.
