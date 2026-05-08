# Architecture — specsmith

## Overview

specsmith is a CLI tool + governance engine for AI-assisted development.
It treats belief systems like code: codable, testable, deployable.

## Nexus Runtime

The Nexus runtime is the local-first agentic REPL that integrates with
the governance broker for safe, auditable AI-assisted development.

### Nexus Broker Boundary

The broker (`specsmith.agent.broker`) classifies natural-language
utterances into intents (read_only_ask, change, release, destructive)
and maps them to governance requirements via `infer_scope()`.

### Nexus Preflight CLI Subcommand

`specsmith preflight "<utterance>"` gates every change through the
governance broker. It returns a JSON payload with decision, work_item_id,
requirement_ids, test_case_ids, and confidence_target.

### Nexus REPL Execution Gate

The REPL (`specsmith.agent.repl`) uses `execute_with_governance()` to
wrap every agent action in a preflight → execute → verify cycle. The
`/why` toggle shows the governance trace in human-readable form.

### Nexus Bounded-Retry Harness

The harness (`specsmith.agent.broker.execute_with_governance`) retries
failed actions up to `DEFAULT_RETRY_BUDGET` times using strategy
classification (`classify_retry_strategy`). Strategies include
`fix_tests`, `reduce_scope`, `manual_review`, and `stop`.

## AI Provider & Model Intelligence

### Provider Registry

Unified flat list of all configured AI backends (cloud, ollama, vllm,
byoe, huggingface). See `specsmith.agent.provider_registry`.

### Execution Profiles

Profiles constrain which providers a session can use (unrestricted,
local-only, budget, performance, air-gapped).
See `specsmith.agent.execution_profiles`.

### Model Intelligence

Role-based scoring engine using HuggingFace benchmark data.
10 roles × benchmark weights. See `specsmith.agent.model_intelligence`.

### USPTO Data Sources

7 bundled client modules for patent/IP work (PatentsView, PPUBS, ODP,
PFW, Citations, FPD, PTAB). All stdlib urllib, no external dependencies.
See `specsmith.datasources.*`.

## Kairos Integration

Kairos (BitConcepts/kairos) is the Rust terminal that consumes
`specsmith serve` as its governance backend via HTTP/WebSocket.
See `specsmith.governance_logic.GovernanceHTTPServer`.
