# Architecture diagrams

## Governed change loop

```mermaid
flowchart LR
    A["Developer or host agent"] --> B["Preflight"]
    B --> C["Requirement scope"]
    C --> D["Linked tests"]
    D --> E["Native implementation"]
    E --> F["Verification"]
    F -->|pass| G["Checkpoint and evidence"]
    F -->|retry| C
    B -->|clarify or stop| H["Human alignment"]
```

## Source-of-truth flow

```mermaid
flowchart TD
    R["docs/requirements/*.yml"] --> S["specsmith sync"]
    T["docs/tests/*.yml"] --> S
    S --> C[".specsmith derived caches"]
    C --> P["Preflight and audit"]
    P --> L["LEDGER.md"]
    P --> E["ESDB"]
    L --> K["Compact checkpoint"]
    E --> K
```

## Integration boundary

```mermaid
flowchart LR
    H["Host agent tools"] -->|intent and observed evidence| S["Specsmith AEE kernel"]
    S -->|accepted scope and linked tests| H
    S --> M["MCP or focused adapter"]
    S --> G["Grace local fallback"]
    S --> D["Ledger and ESDB"]
```

The host owns code editing, Git, browsers, deployment, and framework skills.
Specsmith owns requirements, test traceability, epistemic boundaries, verification,
and durable evidence.
