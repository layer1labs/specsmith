"""Repository-private validation and maintenance helpers.

This package marker keeps imports deterministic when pytest is launched through a
console-script entry point whose directory, rather than the repository root, is
first on ``sys.path``.
"""
