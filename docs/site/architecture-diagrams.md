# Architecture and Workflow Diagrams
The diagrams below provide a visual reference for core specsmith governance paths.

## High-level architecture
```mermaid
flowchart LR
  U[User or Agent Client] --> P[specsmith preflight]
  P --> D{Decision}
  D -->|accepted| E[Execution Layer]
  D -->|needs_clarification| C[Clarification Loop]
  E --> V[specsmith verify]
  V --> A[specsmith audit]
  A --> T[TraceVault + ESDB]
  T --> R[Compliance Export / Reports]
```

## Preflight lifecycle
```mermaid
stateDiagram-v2
  [*] --> ReceiveIntent
  ReceiveIntent --> Classify
  Classify --> MatchReqTests
  MatchReqTests --> ScoreConfidence
  ScoreConfidence --> DecisionAccepted: confidence and scope OK
  ScoreConfidence --> DecisionClarify: ambiguity or risk
  DecisionAccepted --> MintWorkItem
  MintWorkItem --> ReturnPayload
  DecisionClarify --> ReturnInstruction
  ReturnPayload --> [*]
  ReturnInstruction --> [*]
```

## Work-item lifecycle
```mermaid
stateDiagram-v2
  [*] --> Open
  Open --> Implemented: verify reaches equilibrium
  Open --> Rejected
  Open --> Archived
  Implemented --> Promoted: promoted to requirement
  Implemented --> Closed: covered by existing requirement
  Archived --> Open: re-open
  Promoted --> Closed
  Closed --> [*]
  Rejected --> [*]
```

## Requirements-to-tests traceability
```mermaid
flowchart TD
  REQ[Requirement IDs] --> MAP[Trace Mapping]
  MAP --> TEST[Test Case IDs]
  TEST --> RUN[Test Execution]
  RUN --> RES[Pass/Fail Artifacts]
  RES --> AUD[Audit Coverage Check]
  AUD --> GAP[Gap Report or Compliance Evidence]
```

## MCP integration flow
```mermaid
sequenceDiagram
  participant Client as MCP Client
  participant Server as specsmith MCP Server
  participant Gov as Governance Engine
  Client->>Server: tool call (governance_preflight)
  Server->>Gov: preflight request
  Gov-->>Server: decision payload + work_item_id
  Server-->>Client: MCP tool result
  Client->>Server: tool call (governance_audit/checkpoint)
  Server->>Gov: audit/checkpoint
  Gov-->>Server: governance state
  Server-->>Client: structured result
```

## ESDB and audit flow
```mermaid
flowchart LR
  ACT[Agent/User Actions] --> LED[Trace Ledger Events]
  LED --> ESDB[ESDB Storage]
  ESDB --> VER[Chain Verification]
  VER --> AUD[Audit Report]
  AUD --> EXP[Compliance Export]
```

## Compliance evidence generation
```mermaid
flowchart TD
  PH[Phase + Policy State] --> EV[Evidence Collector]
  WI[Work Items] --> EV
  TR[TraceVault Chain] --> EV
  TC[Test Coverage] --> EV
  EV --> PKG[Compliance Package]
  PKG --> OUT[Markdown / JSON Export]
```

## Agent integration flow
```mermaid
flowchart LR
  AG[Agent Runtime] --> PF[preflight gate]
  PF -->|accepted| EX[execute task]
  EX --> VF[verify]
  VF --> AU[audit]
  AU --> CK[checkpoint / trace seal]
  PF -->|needs clarification| HC[human clarification]
  HC --> PF
```
