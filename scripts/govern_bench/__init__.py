"""govern_bench — Governance Efficiency Benchmark Suite for specsmith.

Measures token cost and task quality across six governance conditions:
  UNGOVERNED       – raw agent, no governance context
  CONTEXT_ONLY     – CLAUDE.md / AGENTS.md context injection only
  BMAD_STYLE       – BMAD Blueprint→Milestone artifact prompting
  OPENSPEC_STYLE   – structured OpenSpec REQUIREMENTS.md context
  SPECSMITH_LIGHT  – specsmith preflight gate only
  SPECSMITH_FULL   – full specsmith session (preflight + verify + save)

Primary metric: cost-of-pass = total_cost_usd / pass_rate
"""

__version__ = "0.1.0"
