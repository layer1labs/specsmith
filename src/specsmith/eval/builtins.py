# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Built-in eval suites for core agent capabilities."""

from __future__ import annotations

from specsmith.eval import EvalCase, EvalSuite

CODE_GEN = EvalCase(
    id="eval-code-gen-001",
    name="Python function generation",
    role="coder",
    prompt=(
        "Write a Python function `fibonacci(n: int) -> list[int]` that returns "
        "the first n Fibonacci numbers. Include type hints and a docstring."
    ),
    expected_keywords=["def fibonacci", "list[int]", "return"],
    tags=["code", "python"],
)

ARCHITECTURE_REVIEW = EvalCase(
    id="eval-arch-001",
    name="Architecture review",
    role="architect",
    prompt=(
        "Review this architecture decision: 'We will use a monolithic SQLite database "
        "for a multi-tenant SaaS application serving 10,000 concurrent users.' "
        "Identify risks and suggest alternatives."
    ),
    expected_keywords=["scalability", "concurrent", "alternative"],
    tags=["architecture", "review"],
)

TEST_GEN = EvalCase(
    id="eval-test-gen-001",
    name="Test generation",
    role="tester",
    prompt=(
        "Write pytest tests for a function `add(a: int, b: int) -> int` that adds "
        "two integers. Cover edge cases: negative numbers, zero, large values."
    ),
    expected_keywords=["def test_", "assert", "add"],
    tags=["test", "pytest"],
)

PATENT_CLAIM = EvalCase(
    id="eval-patent-001",
    name="Patent claim analysis",
    role="ip-analyst",
    prompt=(
        "Analyze this patent claim: 'A method for sorting data records comprising: "
        "receiving a dataset, applying a comparison function, and outputting sorted "
        "records in ascending order.' Identify the key limitations and suggest "
        "potential design-arounds."
    ),
    expected_keywords=["limitation", "claim", "design"],
    tags=["patent", "ip"],
)

INTENT_CLASSIFY = EvalCase(
    id="eval-classify-001",
    name="Intent classification",
    role="classifier",
    prompt=(
        "Classify the following user request into one of these categories: "
        "[code_change, bug_fix, documentation, question, refactor]. "
        "Request: 'Can you rename the variable foo to bar in utils.py?'"
    ),
    expected_keywords=["refactor"],
    max_tokens=128,
    tags=["classify", "intent"],
)

# Pre-built suites
CORE_SUITE = EvalSuite(
    id="core",
    name="Core Capabilities",
    description="Tests fundamental AI capabilities across 5 roles",
    cases=[CODE_GEN, ARCHITECTURE_REVIEW, TEST_GEN, PATENT_CLAIM, INTENT_CLASSIFY],
    tags=["core", "smoke"],
)

ALL_SUITES: dict[str, EvalSuite] = {
    "core": CORE_SUITE,
}


def get_suite(suite_id: str) -> EvalSuite | None:
    """Get a built-in suite by ID."""
    return ALL_SUITES.get(suite_id)


def list_suites() -> list[EvalSuite]:
    """List all available built-in suites."""
    return list(ALL_SUITES.values())
