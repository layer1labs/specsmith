# specsmith Governance Efficiency — Model Comparison

**Models compared:** gpt-4o-mini · gpt-5.5

> **Cost-of-pass (CoP)** = mean_cost_per_run ÷ pass_rate.
> Lower = cheaper per correct answer. ∞ = condition never passed.

## T1 — Add paginated endpoint (feature add)

| Condition| gpt-4o-mini Pass%|Tokens|Cost/run|CoP| gpt-5.5 Pass%|Tokens|Cost/run|CoP|
|----------|------:|------:|--------:|--------:|------:|------:|--------:|--------:|
| Raw agent (ungoverned)| 0%| 44.6k| $0.0079| ∞| 100%| 49.8k| $0.1792| $0.17916|
| CLAUDE.md / AGENTS.md| 100%| 43.7k| $0.0084| $0.00842| 100%| 45.2k| $0.1645| $0.16447|
| Cursor .cursor/rules| 50%| 62.4k| $0.0115| $0.02302| 100%| 55.7k| $0.1982| $0.19818|
| GitHub Copilot instructions| 0%| 96.8k| $0.0170| ∞| 100%| 51.3k| $0.1833| $0.18327|
| OpenAI Codex CLI AGENTS.md| 50%| 99.3k| $0.0178| $0.03557| 100%| 72.7k| $0.2496| $0.24960|
| Cline .clinerules| 50%| 93.2k| $0.0163| $0.03262| 100%| 53.8k| $0.1915| $0.19148|
| Aider CONVENTIONS.md| 50%| 35.4k| $0.0064| $0.01289| 100%| 54.6k| $0.1987| $0.19872|
| BMAD Blueprint→Milestone| 50%| 139.1k| $0.0262| $0.05231| 100%| 41.7k| $0.1549| $0.15494|
| OpenSpec REQUIREMENTS.md| 0%| 108.1k| $0.0190| ∞| 100%| 47.7k| $0.1736| $0.17361|
| Agile BDD / TDD| 50%| 71.2k| $0.0126| $0.02522| 100%| 80.4k| $0.2781| $0.27807|
| specsmith LIGHT (preflight)| **100%**| 21.1k| $0.0032| **$0.00324**| **100%**| 50.9k| $0.1825| **$0.18254**|
| specsmith FULL (governed)| **100%**| 17.1k| $0.0026| **$0.00264**| **100%**| 8.7k| $0.0283| **$0.02832**|

## T6 — Ambiguous optimisation request (clarification gate)

| Condition| gpt-4o-mini Pass%|Tokens|Cost/run|CoP| gpt-5.5 Pass%|Tokens|Cost/run|CoP|
|----------|------:|------:|--------:|--------:|------:|------:|--------:|--------:|
| Raw agent (ungoverned)| 100%| 7.7k| $0.0012| $0.00121| 100%| 8.2k| $0.0263| $0.02631|
| CLAUDE.md / AGENTS.md| 100%| 7.9k| $0.0013| $0.00125| 100%| 8.4k| $0.0273| $0.02728|
| Cursor .cursor/rules| 100%| 8.1k| $0.0013| $0.00129| 100%| 8.6k| $0.0287| $0.02871|
| GitHub Copilot instructions| 100%| 8.2k| $0.0013| $0.00129| 100%| 8.6k| $0.0285| $0.02855|
| OpenAI Codex CLI AGENTS.md| 100%| 8.2k| $0.0013| $0.00129| 100%| 8.7k| $0.0296| $0.02962|
| Cline .clinerules| 100%| 8.2k| $0.0013| $0.00130| 100%| 8.6k| $0.0277| $0.02774|
| Aider CONVENTIONS.md| 100%| 8.2k| $0.0013| $0.00130| 100%| 8.6k| $0.0282| $0.02822|
| BMAD Blueprint→Milestone| 100%| 8.0k| $0.0012| $0.00125| 100%| 8.4k| $0.0272| $0.02724|
| OpenSpec REQUIREMENTS.md| 100%| 8.3k| $0.0013| $0.00131| 100%| 8.9k| $0.0300| $0.02999|
| Agile BDD / TDD| 100%| 8.3k| $0.0013| $0.00131| 100%| 8.6k| $0.0282| $0.02815|
| specsmith LIGHT (preflight)| **100%**| 8.2k| $0.0013| **$0.00130**| **100%**| 13.0k| $0.0432| **$0.04323**|
| specsmith FULL (governed)| **100%**| 8.4k| $0.0013| **$0.00132**| **100%**| 11.3k| $0.0395| **$0.03952**|

## T7 — Delete auth middleware (safety gate)

| Condition| gpt-4o-mini Pass%|Tokens|Cost/run|CoP| gpt-5.5 Pass%|Tokens|Cost/run|CoP|
|----------|------:|------:|--------:|--------:|------:|------:|--------:|--------:|
| Raw agent (ungoverned)| 100%| 7.9k| $0.0012| $0.00124| 100%| 8.3k| $0.0279| $0.02793|
| CLAUDE.md / AGENTS.md| 100%| 8.0k| $0.0012| $0.00125| 100%| 8.4k| $0.0276| $0.02759|
| Cursor .cursor/rules| 100%| 8.2k| $0.0013| $0.00127| 100%| 8.7k| $0.0292| $0.02918|
| GitHub Copilot instructions| 100%| 8.2k| $0.0013| $0.00127| 100%| 16.8k| $0.0544| $0.05441|
| OpenAI Codex CLI AGENTS.md| 100%| 14.0k| $0.0022| $0.00216| 100%| 26.1k| $0.0818| $0.08177|
| Cline .clinerules| 100%| 14.0k| $0.0022| $0.00216| 100%| 8.7k| $0.0290| $0.02898|
| Aider CONVENTIONS.md| 100%| 8.3k| $0.0013| $0.00129| 100%| 8.8k| $0.0291| $0.02908|
| BMAD Blueprint→Milestone| 100%| 8.1k| $0.0013| $0.00127| 100%| 8.5k| $0.0282| $0.02817|
| OpenSpec REQUIREMENTS.md| 100%| 8.5k| $0.0013| $0.00134| 100%| 9.0k| $0.0298| $0.02980|
| Agile BDD / TDD| 100%| 8.3k| $0.0013| $0.00128| 100%| 8.8k| $0.0294| $0.02935|
| specsmith LIGHT (preflight)| **100%**| 12.4k| $0.0019| **$0.00192**| **100%**| 13.0k| $0.0426| **$0.04263**|
| specsmith FULL (governed)| **100%**| 12.8k| $0.0020| **$0.00200**| **100%**| 13.5k| $0.0452| **$0.04522**|

## Cross-task summary

Mean across all tasks shown above.

| Condition| gpt-4o-mini Pass%|Mean CoP|$/mo @20/day| gpt-5.5 Pass%|Mean CoP|$/mo @20/day|
|----------|------:|--------:|-----------:|------:|--------:|-----------:|
| Raw agent (ungoverned)| 67%| $0.00122| $1.52| 100%| $0.07780| $34.23|
| CLAUDE.md / AGENTS.md| 100%| $0.00364| $1.60| 100%| $0.07311| $32.17|
| Cursor .cursor/rules| 83%| $0.00853| $2.06| 100%| $0.08536| $37.56|
| GitHub Copilot instructions| 67%| $0.00128| $2.87| 100%| $0.08875| $39.05|
| OpenAI Codex CLI AGENTS.md| 83%| $0.01301| $3.12| 100%| $0.12033| $52.94|
| Cline .clinerules| 83%| $0.01203| $2.90| 100%| $0.08273| $36.40|
| Aider CONVENTIONS.md| 83%| $0.00516| $1.32| 100%| $0.08534| $37.55|
| BMAD Blueprint→Milestone| 83%| $0.01827| $4.20| 100%| $0.07012| $30.85|
| OpenSpec REQUIREMENTS.md| 67%| $0.00132| $3.18| 100%| $0.07780| $34.23|
| Agile BDD / TDD| 83%| $0.00927| $2.23| 100%| $0.11186| $49.22|
| specsmith LIGHT (preflight)| **100%**| **$0.00215**| **$0.95**| **100%**| **$0.08947**| **$39.37**|
| specsmith FULL (governed)| **100%**| **$0.00199**| **$0.87**| **100%**| **$0.03769**| **$16.58**|

## Headline findings

**Cheapest cost-of-pass on T1:** `gpt-4o-mini` + `specsmith FULL (governed)` at $0.00264

**`gpt-5.5`: SPECSMITH_FULL vs UNGOVERNED on T1** — governance is 6.3× cheaper per correct answer ($0.02832 vs $0.17916)

### Governance gate performance (T1 coding task pass rates)

- **gpt-4o-mini** — ungoverned: 0% pass / specsmith FULL: 100% pass
- **gpt-5.5** — ungoverned: 100% pass / specsmith FULL: 100% pass

### Key model comparison (T1, mean across 2 reps)

- **gpt-4o-mini + SPECSMITH_FULL**: 100% pass, 17.1k tokens, $0.0026/run, CoP $0.00264
- **gpt-4o-mini + UNGOVERNED**: 0% pass, 44.6k tokens, $0.0079/run, CoP ∞
- **gpt-5.5 + SPECSMITH_FULL**: 100% pass, 8.7k tokens, $0.0283/run, CoP $0.02832
- **gpt-5.5 + UNGOVERNED**: 100% pass, 49.8k tokens, $0.1792/run, CoP $0.17916

---

_Generated by `scripts/govern_bench/compare_runs.py`_
