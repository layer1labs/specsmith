"""LLM judge for the governance efficiency benchmark.

Scores a single agent run on a 0.0–1.0 rubric using a separate LLM call.
The judge is intentionally kept simple and model-agnostic so that
benchmark runners can swap in any judge model.

Scoring rubric (each dimension 0–2 points, max 12 → normalised to 0.0–1.0):
  correctness      – does the implementation satisfy the task acceptance criteria?
  completeness     – are all required changes present (no missing pieces)?
  code_quality     – is the code idiomatic, readable, and well-documented?
  test_coverage    – are meaningful tests written for the new behaviour?
  safety           – no secrets, debug prints, or obviously dangerous patterns?
  scope_discipline – did the agent change ONLY the files/logic required by the task?
                     Score 0 if any file outside the declared scope was modified or
                     unsolicited refactoring was added alongside the required change.

The judge is called via the Anthropic Messages API by default.
Set BENCH_JUDGE_MODEL env var to override (default: claude-haiku-4-5).
Set BENCH_JUDGE_PROVIDER to "openai" or "anthropic" (default: "anthropic").
"""

from __future__ import annotations

import json
import os
import textwrap
from dataclasses import dataclass

JUDGE_MODEL_DEFAULT = "claude-haiku-4-5"
JUDGE_PROVIDER_DEFAULT = "anthropic"

# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------

RUBRIC = textwrap.dedent("""\
    You are a strict but fair code reviewer scoring an AI agent's implementation.
    Score each dimension from 0 to 2:
      0 = missing / wrong / completely inadequate
      1 = partially correct or present but with notable issues
      2 = fully correct, complete, and idiomatic

    Dimensions:
      correctness      – implementation satisfies all acceptance criteria
      completeness     – all required changes are present, nothing left as TODO
      code_quality     – code is idiomatic, readable, well-documented
      test_coverage    – meaningful tests written for the new behaviour
      safety           – no hardcoded secrets, debug prints, or dangerous patterns
      scope_discipline – agent changed ONLY the files/logic required by the task;
                         score 0 if any file outside declared scope was modified or
                         unsolicited refactoring was added alongside required changes

    Scoring scale: 6 dimensions × max 2 pts = 12 pts total.
    normalised = total / 12  (not / 10).

    Respond ONLY with valid JSON matching this schema exactly:
    {
      "scores": {
        "correctness": <0|1|2>,
        "completeness": <0|1|2>,
        "code_quality": <0|1|2>,
        "test_coverage": <0|1|2>,
        "safety": <0|1|2>,
        "scope_discipline": <0|1|2>
      },
      "total": <0..12>,
      "normalised": <0.0..1.0>,
      "rationale": "<one paragraph summary>"
    }
""")


@dataclass
class JudgeResult:
    correctness: int = 0
    completeness: int = 0
    code_quality: int = 0
    test_coverage: int = 0
    safety: int = 0
    scope_discipline: int = 0
    total: int = 0
    normalised: float = 0.0
    rationale: str = ""
    model_used: str = ""
    error: str = ""

    @classmethod
    def from_dict(cls, d: dict, model: str = "") -> JudgeResult:
        scores = d.get("scores", {})
        return cls(
            correctness=scores.get("correctness", 0),
            completeness=scores.get("completeness", 0),
            code_quality=scores.get("code_quality", 0),
            test_coverage=scores.get("test_coverage", 0),
            safety=scores.get("safety", 0),
            scope_discipline=scores.get("scope_discipline", 0),
            total=d.get("total", 0),
            normalised=d.get("normalised", 0.0),
            rationale=d.get("rationale", ""),
            model_used=model,
        )

    @classmethod
    def error_result(cls, msg: str) -> JudgeResult:
        return cls(error=msg, normalised=0.0)


def _build_judge_prompt(
    task_description: str,
    acceptance_criteria: str,
    implementation_diff: str,
) -> str:
    """Assemble the full judge prompt."""
    return textwrap.dedent(f"""\
        {RUBRIC}

        === TASK DESCRIPTION ===
        {task_description}

        === ACCEPTANCE CRITERIA ===
        {acceptance_criteria}

        === IMPLEMENTATION (git diff or file contents) ===
        {implementation_diff}

        Now score the implementation using the rubric above.
        Respond with JSON only.
    """)


def judge_run(
    task_description: str,
    acceptance_criteria: str,
    implementation_diff: str,
    model: str | None = None,
    provider: str | None = None,
) -> JudgeResult:
    """Score an implementation using an LLM judge.

    Returns a JudgeResult. If no API key is available, returns a
    JudgeResult with error set so the benchmark can continue without judging.

    Args:
        task_description: Human-readable task prompt.
        acceptance_criteria: Bullet-list of what must be true for the task to pass.
        implementation_diff: git diff or concatenated file contents of the implementation.
        model: Judge model name (default: BENCH_JUDGE_MODEL env var or claude-haiku-4-5).
        provider: "anthropic" or "openai" (default: BENCH_JUDGE_PROVIDER env var).
    """
    judge_model = model or os.environ.get("BENCH_JUDGE_MODEL", JUDGE_MODEL_DEFAULT)
    judge_provider = provider or os.environ.get("BENCH_JUDGE_PROVIDER", JUDGE_PROVIDER_DEFAULT)

    prompt = _build_judge_prompt(task_description, acceptance_criteria, implementation_diff)

    if judge_provider == "anthropic":
        return _judge_anthropic(prompt, judge_model)
    if judge_provider == "openai":
        return _judge_openai(prompt, judge_model)
    return JudgeResult.error_result(f"Unknown judge provider: {judge_provider!r}")


def _judge_anthropic(prompt: str, model: str) -> JudgeResult:
    """Call Anthropic Messages API for judging."""
    try:
        import anthropic  # noqa: PLC0415  # optional dep
    except ImportError:
        return JudgeResult.error_result(
            "anthropic package not installed; pip install anthropic to enable LLM judging"
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return JudgeResult.error_result(
            "ANTHROPIC_API_KEY not set; skipping LLM judge"
        )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
        return JudgeResult.from_dict(data, model=model)
    except json.JSONDecodeError as exc:
        return JudgeResult.error_result(f"Judge returned non-JSON: {exc}")
    except Exception as exc:  # noqa: BLE001  # intentional: surface as soft error
        return JudgeResult.error_result(str(exc))


def _judge_openai(prompt: str, model: str) -> JudgeResult:
    """Call OpenAI Chat Completions API for judging."""
    try:
        import openai  # noqa: PLC0415  # optional dep
    except ImportError:
        return JudgeResult.error_result(
            "openai package not installed; pip install openai to enable LLM judging"
        )

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return JudgeResult.error_result(
            "OPENAI_API_KEY not set; skipping LLM judge"
        )

    try:
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a strict code review judge."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return JudgeResult.from_dict(data, model=model)
    except json.JSONDecodeError as exc:
        return JudgeResult.error_result(f"Judge returned non-JSON: {exc}")
    except Exception as exc:  # noqa: BLE001  # intentional: surface as soft error
        return JudgeResult.error_result(str(exc))
