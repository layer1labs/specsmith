# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Advanced code analysis framework for specsmith with AI-assisted features."""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from specsmith.auditor import AuditResult
from specsmith.code_analysis import ComplexityReport


@dataclass
class RefactoringSuggestion:
    """A suggestion for code refactoring."""
    file_path: str
    line_number: int
    suggestion_type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    confidence: float  # 0.0 to 1.0


@dataclass
class AIAssistedAnalysis:
    """AI-assisted code analysis results."""
    file_path: str
    suggestions: list[RefactoringSuggestion]
    code_quality_score: float
    complexity_trend: str  # 'improving', 'stable', 'regressing'
    improvement_potential: float  # 0.0 to 1.0


class AdvancedCodeAnalyzer:
    """Advanced code analysis engine with AI-assisted features."""

    def __init__(self) -> None:
        self.complexity_threshold = 10  # A-range complexity threshold

    def analyze_file_for_refactoring(self, file_path: Path) -> list[RefactoringSuggestion]:
        """Analyze a file for potential refactoring opportunities."""
        suggestions: list[RefactoringSuggestion] = []

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            # Parse the file with AST
            tree = ast.parse(content)

            # Check for long functions (potential candidates for refactoring)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Calculate function length
                    if hasattr(node, 'body'):
                        lines = node.body
                        if len(lines) > 20:  # Arbitrary threshold for long functions
                            description = (f"Function '{node.name}' has {len(lines)} lines - "
                                           "consider refactoring")
                            suggestions.append(RefactoringSuggestion(
                                file_path=str(file_path),
                                line_number=node.lineno,
                                suggestion_type="function_length",
                                description=description,
                                severity="medium",
                                confidence=0.7
                            ))

                    # Check for complex conditionals
                    complex_conditions = self._find_complex_conditions(node)
                    for condition in complex_conditions:
                        description = (f"Complex conditional at line {condition['line']} - "
                                       "consider simplification")
                        suggestions.append(RefactoringSuggestion(
                            file_path=str(file_path),
                            line_number=condition['line'],
                            suggestion_type="conditional_complexity",
                            description=description,
                            severity="high",
                            confidence=0.8
                        ))

        except Exception:
            # Silently ignore parsing errors for now
            pass

        return suggestions

    def _find_complex_conditions(self, node: ast.AST) -> list[dict[str, Any]]:
        """Find complex conditional statements."""
        conditions: list[dict[str, Any]] = []
        if isinstance(node, ast.If):
            # Check for nested if statements or complex boolean expressions
            if isinstance(node.test, ast.BoolOp):
                # Count the number of operations in boolean expressions
                bool_op = node.test
                if len(bool_op.values) > 3:  # More than 3 operands is complex
                    conditions.append({
                        'line': node.lineno,
                        'type': 'boolean_expression',
                        'complexity': len(bool_op.values)
                    })
        return conditions

    def analyze_codebase_for_ai_assistance(self, root: Path) -> dict[str, AIAssistedAnalysis]:
        """Analyze entire codebase for AI-assisted insights."""
        results = {}

        # Analyze Python files
        for py_file in root.rglob("*.py"):
            # Skip test files and hidden directories
            if "test" in str(py_file) or any(part.startswith('.') for part in py_file.parts):
                continue

            # Get complexity report
            complexity_reports = self._analyze_file_complexity(py_file)

            # Get refactoring suggestions
            suggestions = self.analyze_file_for_refactoring(py_file)

            # Calculate quality score
            quality_score = self._calculate_quality_score(complexity_reports, suggestions)

            # Determine complexity trend (simplified)
            complexity_trend = self._determine_complexity_trend(complexity_reports)

            results[str(py_file)] = AIAssistedAnalysis(
                file_path=str(py_file),
                suggestions=suggestions,
                code_quality_score=quality_score,
                complexity_trend=complexity_trend,
                improvement_potential=self._calculate_improvement_potential(suggestions)
            )

        return results

    def _analyze_file_complexity(self, file_path: Path) -> list[ComplexityReport]:
        """Analyze complexity of a single file."""
        # This would use the existing functionality from code_analysis.py
        # For now, we'll create a simplified version
        reports = []
        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            # Walk through the AST to find function definitions
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    if complexity > self.complexity_threshold:
                        reports.append(ComplexityReport(
                            file_path=str(file_path),
                            function_name=node.name,
                            complexity=complexity,
                            line_number=node.lineno,
                            message=(f"Function '{node.name}' has cyclomatic complexity of "
                                     f"{complexity}")
                        ))
        except Exception:
            pass

        return reports

    def _calculate_complexity(self, node: ast.AST) -> int:
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
            complexity += self._calculate_complexity(child)

        return complexity

    def _calculate_quality_score(self, complexity_reports: list[ComplexityReport],
                               suggestions: list[RefactoringSuggestion]) -> float:
        """Calculate overall code quality score."""
        # Base score is 100
        score = 100.0

        # Deduct points for high complexity
        high_complexity_count = len([r for r in complexity_reports if r.complexity > 10])
        score -= high_complexity_count * 5

        # Deduct points for refactoring suggestions
        score -= len(suggestions) * 2

        # Ensure score is within bounds
        return max(0, min(100, score))

    def _determine_complexity_trend(self, complexity_reports: list[ComplexityReport]) -> str:
        """Determine if complexity is improving, stable, or regressing."""
        if not complexity_reports:
            return "stable"

        # Simplified logic - in a real implementation, this would compare with historical data
        high_complexity = [r for r in complexity_reports if r.complexity > 10]
        if len(high_complexity) > 0:
            return "regressing"
        else:
            return "stable"

    def _calculate_improvement_potential(self, suggestions: list[RefactoringSuggestion]) -> float:
        """Calculate potential improvement based on suggestions."""
        if not suggestions:
            return 0.0

        # Weight suggestions by severity
        severity_weights = {
            'low': 0.2,
            'medium': 0.5,
            'high': 0.8,
            'critical': 1.0
        }

        total_weight = sum(severity_weights.get(s.suggestion_type, 0.5) for s in suggestions)
        return min(1.0, total_weight / len(suggestions) if suggestions else 0)


def create_ai_assisted_code_report(root: Path) -> dict[str, AIAssistedAnalysis]:
    """Create an AI-assisted code quality report."""
    analyzer = AdvancedCodeAnalyzer()
    return analyzer.analyze_codebase_for_ai_assistance(root)


def generate_refactoring_report(root: Path) -> dict[str, list[RefactoringSuggestion]]:
    """Generate a comprehensive refactoring report."""
    analyzer = AdvancedCodeAnalyzer()
    report = {}

    # Analyze Python files
    for py_file in root.rglob("*.py"):
        # Skip test files and hidden directories
        if "test" in str(py_file) or any(part.startswith('.') for part in py_file.parts):
            continue

        suggestions = analyzer.analyze_file_for_refactoring(py_file)
        report[str(py_file)] = suggestions

    return report


def get_ai_assisted_analysis(root: Path) -> dict[str, AIAssistedAnalysis]:
    """Get AI-assisted analysis for all files."""
    return create_ai_assisted_code_report(root)


def check_ai_compliance(root: Path) -> list[AuditResult]:
    """Check AI compliance based on the analysis."""
    issues = []

    # Check if we have AI-assisted analysis capabilities
    try:
        analysis = get_ai_assisted_analysis(root)
        if analysis:
            issues.append(AuditResult(
                name="ai-assisted-analysis",
                passed=True,
                message="AI-assisted code analysis capabilities are available"
            ))
        else:
            issues.append(AuditResult(
                name="ai-assisted-analysis",
                passed=False,
                message="AI-assisted code analysis capabilities are not available"
            ))
    except Exception as e:
        issues.append(AuditResult(
            name="ai-assisted-analysis",
            passed=False,
            message=f"Error checking AI compliance: {str(e)}"
        ))

    return issues

