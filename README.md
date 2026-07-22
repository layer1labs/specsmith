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

The latest complete screen uses GPT-5.6 Sol across seven tasks, four matched
conditions, and five repetitions per cell (140/140 valid cells).

| Condition | Pass rate | Tokens/correct | Conservative list cost/pass |
|---|---:|---:|---:|
| Ungoverned | 86% | 25.4k | $0.1724 |
| Cursor rules | 83% | 32.3k | $0.2124 |
| Specsmith LIGHT | 94% | 21.8k | $0.1502 |
| Specsmith FULL | 91% | 21.7k | $0.1508 |

These are mixed governance-and-coding point estimates; confidence intervals
overlap. Coding-only correctness favored raw GPT-5.6 Sol, while Specsmith's
aggregate benefit came from deterministic ambiguity/safety gates and lower
token use than Cursor rules. The result reinforces the lean direction: focus on
linked independent tests, requirements, and compact epistemic context—not more
generic skills or prompt ceremony.

Only complete matched runs are published. Earlier provider, compatibility, and
artifact failures are retained as diagnostic provenance but excluded from the
table. From this release onward, task-level TPCA and correctness regressions are
treated as product signals: benchmark failures become linked requirements and
tests before another efficiency claim is made.

The historical dollar column prices all input tokens at the list input rate.
The run recorded cache reads but predates cache-write telemetry, so exact
GPT-5.6 cached billing cannot be reconstructed. TPCA is unaffected; new runs
record cache reads and writes separately.

GovernanceBench also includes `T28`, a long-horizon incident-command console
that coordinates a Python API, Go worker, TypeScript/React UI, Playwright user
journey, JSON Schema, CSS, tests, and architecture documentation. It is reported
separately from the short-task screen so long-horizon cost cannot be hidden by
cheap deterministic gates.

The latest matched T28 screen used GPT-5.6 Sol, Cursor rules, Specsmith FULL,
and five repetitions per condition. Both conditions passed 5/5 hidden oracles.
Cursor used 56.3k tokens/correct and $0.3187/pass; FULL used 71.4k and $0.3813.
This does **not** establish a Specsmith token-efficiency advantage: FULL was
26.7% higher in TPCA. It does show measurable progress from the preceding
84.6k FULL screen after controller-owned validation and protocol-valid
superseded-read compaction. The deterministic post-run audit reported no
weaknesses. One 127k FULL outlier was independent verification catching an
acceptance gap and successfully forcing another repair; its full cost remains
in the result. See [run 29942515095](https://github.com/layer1labs/specsmith/actions/runs/29942515095).

The corrected managed Hugging Face Qwen3.6 diagnostic did not converge:
Cursor and FULL both failed the T28 oracle at the 20-turn ceiling, using 230.8k
and 236.9k tokens. Its TPCA is therefore infinite, and it was not advanced to
five repetitions. See [run 29944111036](https://github.com/layer1labs/specsmith/actions/runs/29944111036).

Every new raw benchmark artifact now receives a deterministic weakness audit.
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
