# Specsmith 5-Minute Demo Script
This script demonstrates a complete governed flow in under five minutes.

## 0:00–0:30 — Initialize project
```bash
mkdir demo-governed-project
cd demo-governed-project
specsmith init
```
Expected snippet:
```text
Initialized specsmith project
Created scaffold.yml and governance directories
```

## 0:30–1:15 — Add requirement
```bash
specsmith req add --id REQ-900 --title "CLI returns structured JSON status"
```
Expected snippet:
```text
Added requirement REQ-900
```

## 1:15–2:00 — Run preflight before agent work
```bash
specsmith preflight "Implement REQ-900 JSON status command" --json
```
Expected snippet:
```json
{"decision":"accepted","work_item_id":"WI-...","requirement_ids":["REQ-900"]}
```

## 2:00–3:00 — Agent implements requirement
```bash
specsmith run
```
Narration cue: instruct the agent to implement the requirement and tests; mention that governed execution keeps the change inside traceable boundaries.

## 3:00–3:40 — Verify implementation
```bash
specsmith verify
```
Expected snippet:
```text
Verification complete
equilibrium: true
```

## 3:40–4:20 — Audit governance health
```bash
specsmith audit
```
Expected snippet:
```text
Audit: healthy
```

## 4:20–4:40 — Check ESDB status
```bash
specsmith esdb status
```
Expected snippet:
```text
ESDB active
```

## 4:40–5:00 — Governed PR check
```bash
specsmith checkpoint
```
Narration cue: show that checkpoint plus trace/audit outputs provide a review-ready governance anchor before opening a pull request.
