# Specsmith

[![CI](https://github.com/layer1labs/specsmith/actions/workflows/ci.yml/badge.svg)](https://github.com/layer1labs/specsmith/actions/workflows/ci.yml)
[![Docs](https://readthedocs.org/projects/specsmith/badge/?version=stable)](https://specsmith.readthedocs.io/stable/)
[![PyPI](https://img.shields.io/pypi/v/specsmith?label=stable&style=flat&color=blue&cacheSeconds=60)](https://pypi.org/project/specsmith/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Specsmith is a lean governance layer for AI-assisted development. It keeps four
things explicit while your existing coding agent and toolchain do the work:

1. the requirement being changed;
2. the test that proves it;
3. the evidence that was actually observed; and
4. a compact epistemic context that does not turn guesses into facts.

Specsmith is not an IDE, autonomous coding agent, CI replacement, generic skill
catalog, or legal-compliance certificate. It integrates with those tools instead
of duplicating them.

## Install

The CLI is distributed through PyPI and should be isolated with `pipx`:

```bash
pipx install specsmith
specsmith --version
```

Python-library use remains available from an ordinary environment:

```bash
pip install specsmith
```

## Five-minute start

Adopt an existing repository:

```bash
cd your-project
specsmith import --project-dir . --yes
specsmith req add --title "The API returns a stable error envelope"
specsmith test add --req REQ-001 --title "Verify the error envelope" --type integration
specsmith preflight "Implement the error envelope. Scope: REQ-001" --json
```

Let your normal agent edit the code and let your normal test runner execute the
tests. Then close the evidence loop:

```bash
pytest -q                         # or your native test command
specsmith audit --project-dir .
specsmith checkpoint --project-dir .
```

For a new repository, use `specsmith init`. See the
[quick start](https://specsmith.readthedocs.io/stable/quickstart/) for Windows,
Linux, CI, and provider setup.

## The core loop

```text
requirement -> linked test -> accepted preflight -> host edits/tests
            -> verify/audit evidence -> compact trusted context
```

- `req` and `test` maintain requirement-to-test traceability.
- `preflight` classifies intent and stops ambiguous or destructive work.
- `verify`, `audit`, and `checkpoint` preserve observed evidence and uncertainty.
- `compress` and ESDB keep context bounded without promoting unsupported claims.
- `integrate` and MCP expose that contract to coding agents and editors.

Run `specsmith --help` for the small core surface and `specsmith commands` for
the complete supported command list.

## Grace local REPL

Grace is Specsmith's optional local fallback—not a replacement for a coding
agent you already use.

```bash
specsmith run
```

The first run explains provider recovery and useful commands:

```text
grace> /help
grace> /status
grace> /why
grace> /specsmith preflight "Fix config repair. Scope: REQ-001"
```

Grace reports its active provider, model, requirement/test context, token
pressure, and evidence state. Older `.specsmith/nexus.yml` files and the
`l1-nexus` served-model identifier are read only as compatibility inputs; the
user-facing REPL is Grace.

Use `/why` to inspect the evidence behind the current decision.

For CPU-safe local fallback and VRAM-aware recommendations, see the
[local model guide](https://specsmith.readthedocs.io/stable/local-models/).

## Agent integrations

Prefer the host tool's native Git, browser, testing, and framework capabilities.
Specsmith supplies only its distinct governance context.

```bash
specsmith integrate <tool> --project-dir .
specsmith mcp --help
```

- [Agent integration guide](https://specsmith.readthedocs.io/stable/agent-integrations/)
- [Zoo Code / Roo Code setup and config repair](https://specsmith.readthedocs.io/stable/zoo-code-roo/)
- [Invocation strategy](https://specsmith.readthedocs.io/stable/invocation-strategy/)

Zoo Code integration repairs missing, older, and tampered managed configuration
while preserving unrelated user settings. The same generated assets and tests
run on Windows and Linux.

## Policy

Policy stays intentionally small. Keep preflight and linked-test enforcement on;
add approvals only where risk justifies them.

```yaml
required_preflight: true
required_tests: true
required_human_approval:
  - release
risk_threshold: high
```

See the [policy reference](https://specsmith.readthedocs.io/stable/policy/) and
the [`examples/policies`](examples/policies) directory.

## Governance efficiency benchmark

The current matched GPT-5.6 Sol screen covers eight task types—feature, bug,
API, schema, CLI, ambiguity, destructive safety, and the polyglot `T28`
long-horizon product—under Cursor rules and Specsmith FULL. Each cell has five
repetitions (80 valid rows) at commit `f474bb6`.

| Condition | Correct | Total tokens | Tokens/correct | Cost | Mean turns |
|---|---:|---:|---:|---:|---:|
| Cursor rules | 34/40 | 1,148,565 | 33,781 | $5.1779 | 6.38 |
| Specsmith FULL | 40/40 | 360,662 | 9,017 | $3.3110 | 3.40 |

On this versioned suite, FULL achieved six more correct results, 73.3% lower
tokens per correct answer, 36.1% lower measured cost, and 17.4% lower wall time.
Every individual task type preserved or improved correctness and token use.
`T28` improved from the superseded 71.4k FULL result to 20.6k tokens/correct,
versus Cursor's 57.3k, while both remained 5/5 correct.

A T28-only matched replication at commit `5790d41`
([run 30045327768](https://github.com/layer1labs/specsmith/actions/runs/30045327768))
again passed 5/5 in both conditions. FULL averaged 32.0k tokens/correct versus
Cursor rules at 69.1k: 53.6% fewer tokens and 26.0% lower measured cost.

The next FULL-only n=5 confirmation at commit `3d86308`
([run 30077217017](https://github.com/layer1labs/specsmith/actions/runs/30077217017))
also passed every public and independent check. A focused repair-context handoff
reduced mean TPCA to 28.3k, mean turns from 11.4 to 10.2, and mean measured cost
from $0.2640 to $0.2519. That is 11.6% fewer tokens for the same model and task
without weakening correctness.

The July 24 learning replay at commit `708d47b`
([run 30093712102](https://github.com/layer1labs/specsmith/actions/runs/30093712102))
again passed 5/5 and reduced TPCA to 26.5k, mean turns to 9.8, and measured
cost per correct run to $0.2414. This is 6.4% fewer tokens than the 28.3k
screen, with a 60% first-pass rate and no audit weakness. It is the current
T28 Sol frontier envelope; FULL-only confirmations are not recombined with the
older matched grid.

The receipts are split into two complete, non-overlapping matched workflows:
[T1/T6/T7/T13 run 29963772623](https://github.com/layer1labs/specsmith/actions/runs/29963772623)
and [T2/T10/T11/T28 run 29963515885](https://github.com/layer1labs/specsmith/actions/runs/29963515885).
The result is evidence for this model, task set, prompts, and commit—not a claim
that every repository or model will behave identically.

Managed Hugging Face Qwen evidence remains diagnostic, not publication quality.
The best recent Qwen3.6/DeepInfra T28 cell,
[run 30010219286](https://github.com/layer1labs/specsmith/actions/runs/30010219286),
was correct but used 180,895 tokens and all 20 turns. Trace-driven read and
repair controls then reduced one cell to 136,360 tokens
([run 30011743699](https://github.com/layer1labs/specsmith/actions/runs/30011743699)),
but that stochastic sample failed the independent oracle. The final
[run 30013020354](https://github.com/layer1labs/specsmith/actions/runs/30013020354)
passed the hidden oracle 5/5 yet failed its self-authored public tests and Ruff
after 151,666 tokens. These n=1 cells are not combined or promoted.

The managed Qwen3-Coder-Next route also failed admission: one T28 request
returned HTTP 400 before a model action
([run 30007255204](https://github.com/layer1labs/specsmith/actions/runs/30007255204)),
and its T2 control wrote no files in 58,149 tokens
([run 30007554143](https://github.com/layer1labs/specsmith/actions/runs/30007554143)).
That route did not demonstrate the model's native `qwen3_coder` parser. The
current evidence therefore supports GPT-5.6 Sol plus Specsmith FULL as the
efficient reliable configuration on this suite; a new Qwen comparison must
change the serving/tool protocol before it earns another paid repetition.

The July 24 open-frontier replay probed seven exact hosted routes and ran one
matched T28 diagnostic per model in
[workflow 30091184259](https://github.com/layer1labs/specsmith/actions/runs/30091184259).
Specsmith FULL turned Qwen3.6/DeepInfra from a 163.9k-token Cursor failure into
a correct 62.1k-token result, and Kimi K2.7 Code from a 42.3k-token Cursor
failure into a correct 24.0k-token result. DeepSeek-V4 Flash and Nemotron 3
Ultra failed both conditions; MiniMax again failed through empty continuation.
Narration and public-contract traces then produced two bounded repairs.
Final-commit confirmations made GLM-5.2 correct at 73.6k and DeepSeek-V4 Pro
correct at 84.4k
([run 30093614453](https://github.com/layer1labs/specsmith/actions/runs/30093614453)).
Their deterministic audits reject n=5 promotion because each is more than
2.5× the Sol envelope. Kimi's DeepInfra n=5 attempt was rejected after eight
router 504 cells; Together returned an account-level 403 during its live probe.
A one-repetition Novita fallback
([run 30096796977](https://github.com/layer1labs/specsmith/actions/runs/30096796977))
completed: Cursor Rules failed at 108.1k tokens and 20 turns, while FULL passed
at 43.0k tokens, 10 turns, and $0.0735. This demonstrates a large governance
gain on Kimi but remains 1.62× the current 26.5k Sol envelope, so its audit
correctly blocks an n=5 repeat.
The GPT-OSS-120B DeepInfra route then failed continuation immediately after a
valid tool call
([run 30077072490](https://github.com/layer1labs/specsmith/actions/runs/30077072490));
the controlled Novita route repair worked but serialized all 20 actions and
failed correctness
([run 30077459159](https://github.com/layer1labs/specsmith/actions/runs/30077459159)).
Separating composite-read state reduced the follow-up to 44.7k tokens and 17
turns, but the provider emitted the final `done` arguments as plain JSON text
([run 30077929145](https://github.com/layer1labs/specsmith/actions/runs/30077929145)).
The exact-completion confirmation then failed to reach complete write scope and
exhausted 20 turns at 49.3k tokens
([run 30078601832](https://github.com/layer1labs/specsmith/actions/runs/30078601832)).
The managed GPT-OSS model/route pair is rejected; no larger sample or turn cap
is warranted.

Every new raw benchmark artifact now receives a deterministic weakness audit.
That audit also emits a machine-readable next experiment—reject malformed
evidence, repair correctness, optimize measured token waste, repeat a clean
diagnostic to five, or expand a clean screen to ten—without paying a model to
judge its own work. Versioned reference envelopes now stop a correct but
materially less efficient challenger before five paid repetitions.
The audit also distinguishes a native tool-continuation failure from ordinary
model incorrectness, so provider/protocol repairs remain one-variable
experiments.

To combine those outcome findings with the normal project governance audit:

```bash
specsmith audit --project-dir . \
  --benchmark-results bench-results.json \
  --report benchmark-project-audit.json
```

- [Benchmark report](https://specsmith.readthedocs.io/stable/efficiency-benchmark/)
- [Comparison validity and limitations](https://specsmith.readthedocs.io/stable/model-comparison/)
- [Long-horizon benchmark and weakness audit](https://specsmith.readthedocs.io/stable/benchmark-audit/)

## ESDB and evidence

SQLite is the free default ESDB. ChronoMemory/ChronoStore is an optional
commercial backend for cryptographic WAL integrity, richer provenance, and
epistemic rollback.

```bash
specsmith esdb status
```

See the [ESDB guide](https://specsmith.readthedocs.io/stable/esdb/) for migration,
licensing, and the Python API. Commercial inquiries:
[licensing@layer1labs.ai](mailto:licensing@layer1labs.ai).

## Development and release quality

The supported baseline is Python 3.10–3.13 on Linux, macOS, and Windows. CI
enforces formatting, Ruff, mypy, strict documentation builds, governance schema
validation, dependency auditing, CodeQL, the full test matrix, and built-wheel
smoke tests.

```bash
ruff format --check src/ tests/
ruff check src/ tests/
pytest tests/ -q
mypy src/specsmith/
mkdocs build --strict
```

Contributor guidance is in [CONTRIBUTING.md](CONTRIBUTING.md). Security reports
belong in [SECURITY.md](SECURITY.md). Release history is in
[CHANGELOG.md](CHANGELOG.md).

## Documentation

- [Stable documentation](https://specsmith.readthedocs.io/stable/)
- [CLI and first steps](https://specsmith.readthedocs.io/stable/standalone-cli/)
- [Requirements and test workflow](https://specsmith.readthedocs.io/stable/governance/)
- [Examples](docs/examples/README.md)

Specsmith is MIT licensed. ChronoMemory is separately licensed; see
[COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md).
