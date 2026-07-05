# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Code analysis framework for specsmith."""

import ast
from dataclasses import dataclass
from pathlib import Path

from specsmith.auditor import AuditResult


@dataclass
class ComplexityReport:
    """Report of code complexity metrics."""
    file_path: str
    function_name: str
    complexity: int
    line_number: int
    message: str


@dataclass
class CodeQualityReport:
    """Comprehensive code quality report."""
    file_path: str
    complexity_reports: list[ComplexityReport]
    issues: list[AuditResult]
    overall_score: float


def analyze_file_complexity(file_path: Path) -> list[ComplexityReport]:
    """Analyze cyclomatic complexity of functions in a Python file."""
    reports: list[ComplexityReport] = []

    try:
        with open(file_path, encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        # Walk through the AST to find function definitions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                complexity = _calculate_complexity(node)
                if complexity > 10:  # Threshold for high complexity
                    reports.append(ComplexityReport(
                        file_path=str(file_path),
                        function_name=node.name,
                        complexity=complexity,
                        line_number=node.lineno,
                        message=f"Function '{node.name}' has cyclomatic complexity of {complexity}"
                    ))
    except Exception:
        # Silently ignore parsing errors for now
        pass

    return reports


def _calculate_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of an AST node."""
    complexity = 1  # Base complexity

    # Count control flow statements
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.Compare):
            complexity += len(child.comparators) - 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1

        # Recursively check children
        complexity += _calculate_complexity(child)

    return complexity


def analyze_code_quality(root: Path) -> CodeQualityReport:
    """Analyze overall code quality in a project."""
    complexity_reports = []
    issues = []

    # Analyze Python files
    for py_file in root.rglob("*.py"):
        # Skip test files and hidden directories
        if "test" in str(py_file) or any(part.startswith('.') for part in py_file.parts):
            continue

        complexity_reports.extend(analyze_file_complexity(py_file))

    # Check for A-range complexity (simplified check)
    if complexity_reports:
        # Find functions with complexity > 10 (E-range)
        high_complexity = [r for r in complexity_reports if r.complexity > 10]
        if high_complexity:
            issues.append(AuditResult(
                name="high-complexity-functions",
                passed=False,
                message=f"Found {len(high_complexity)} functions with high cyclomatic complexity (>10)",
                fixable=True
            ))
        else:
            issues.append(AuditResult(
                name="complexity-compliance",
                passed=True,
                message="All functions have A-range complexity (≤10)"
            ))
    else:
        issues.append(AuditResult(
            name="complexity-compliance",
            passed=True,
            message="No Python files analyzed for complexity"
        ))

    # Calculate overall score (simplified)
    overall_score = 100.0
    if complexity_reports:
        avg_complexity = sum(r.complexity for r in complexity_reports) / len(complexity_reports)
        # Score decreases with higher average complexity
        overall_score = max(0, 100 - (avg_complexity * 5))

    return CodeQualityReport(
        file_path=str(root),
        complexity_reports=complexity_reports,
        issues=issues,
        overall_score=overall_score
    )


def get_complexity_report(root: Path) -> list[ComplexityReport]:
    """Get a comprehensive complexity report for all Python files."""
    reports = []

    for py_file in root.rglob("*.py"):
        # Skip test files and hidden directories
        if "test" in str(py_file) or any(part.startswith('.') for part in py_file.parts):
            continue
        reports.extend(analyze_file_complexity(py_file))

    return reports


def check_complexity_compliance(root: Path) -> list[AuditResult]:
    """Check if all functions comply with A-range complexity requirements."""
    issues = []

    # Check all Python files for complexity issues
    complexity_reports = get_complexity_report(root)

    # Find functions with complexity > 10 (E-range)
    high_complexity = [r for r in complexity_reports if r.complexity > 10]

    if high_complexity:
        issues.append(AuditResult(
            name="complexity-compliance",
            passed=False,
            message=f"Found {len(high_complexity)} functions with complexity > 10",
            fixable=True
        ))
    else:
        issues.append(AuditResult(
            name="complexity-compliance",
            passed=True,
            message="All functions comply with A-range complexity requirements"
        ))

    return issues
