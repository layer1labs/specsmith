# Product Principles
These principles guide product and governance design decisions in specsmith.

## 1) Governed by default
Specsmith should bias toward explicit governance over implicit behavior. Every meaningful action should leave an auditable trail and a clear rationale in context.
Design example: `preflight` runs before execution-oriented agent actions and emits an explicit decision payload.

## 2) Traceability over convenience
Convenience features are valuable only when they preserve decision traceability. If a shortcut hides intent or evidence, it should be redesigned.
Design example: Work item IDs are minted on accepted preflight decisions and carried through verification and audit.

## 3) Human authority at decision boundaries
Humans retain final authority for ambiguous, risky, or policy-sensitive decisions. The system should surface uncertainty and request explicit clarification when needed.
Design example: escalation thresholds and `needs_clarification` decisions gate uncertain operations.

## 4) Evidence-first compliance
Compliance outputs should be generated from concrete runtime evidence, not narrative claims. Evidence must be reproducible and inspectable.
Design example: export reports aggregate trace entries, requirement coverage, and verification outcomes.

## 5) Local-first, cloud-compatible
Specsmith should work well in local/offline workflows while enabling cloud integrations when teams need them. Local reliability must not depend on external services.
Design example: Ollama and local governance flows operate without mandatory cloud dependencies.

## 6) Interoperability without lock-in
Teams should be able to integrate existing tools and migrate incrementally. Specsmith should provide adapters and import paths rather than forcing rewrites.
Design example: `import` pathways for adjacent ecosystems and OpenAI-compatible endpoint support.

## 7) Progressive rigor
Governance depth should be tunable to project risk and maturity. Teams can start lightweight and increase rigor as requirements become stricter.
Design example: permission presets and configurable governance profiles support different assurance levels.

## 8) Explicit uncertainty and falsifiability
The system should expose confidence, assumptions, and unknowns, rather than masking them with deterministic language. Claims must remain testable.
Design example: confidence targets, requirement/test mappings, and verification outputs are surfaced in governance responses.

## 9) Cross-platform reliability
Specsmith should treat Windows, Linux, and macOS as first-class targets for contributor and CI workflows. Platform assumptions must be explicit.
Design example: docs and automation include platform-aware command and shell guidance.

## 10) Dogfood the governance stack
Specsmith should use its own governance model to develop itself. Product improvements should continuously validate and refine the same mechanisms users rely on.
Design example: the repository maintains governance artifacts and workflow documentation as part of day-to-day development.
