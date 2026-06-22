# Specsmith for Spec Kit Users
Specsmith and Spec Kit share a focus on structured requirements and delivery discipline, but differ in governance depth and evidence-chain expectations.

## Overlap and differences
| Area | Spec Kit | Specsmith |
|---|---|---|
| Requirements structure | Strong templating and organization | Strong templating plus governance linkage |
| Agent workflow | Project-dependent | Governed preflight + verify + audit lifecycle |
| Traceability | Varies by project setup | First-class, persistent work-item + trace chain |
| Compliance evidence | Typically manual/adjacent tooling | Built-in export and audit-oriented outputs |
| Runtime modes | Lightweight authoring focus | Lightweight to high-assurance governance modes |

## Migration and import path
- Use `specsmith import spec-kit` (stub command path) to bootstrap migration metadata.
- Preserve existing requirement IDs where possible, then map them to specsmith work items and tests.
- Run `specsmith sync` and `specsmith audit` to establish initial governance baseline.

## Side-by-side workflow
1. Define/update requirements in your source structure.
2. In Specsmith, run `preflight` before implementation-oriented agent actions.
3. Execute change, then run `verify`.
4. Run `audit` and export evidence for review.

## Governing Spec Kit-generated projects
Specsmith can wrap a Spec Kit-generated project by treating existing artifacts as inputs rather than replacing them. This enables incremental adoption: keep your current templates, add governance gates and evidence outputs, then gradually align deeper lifecycle steps as needed.
