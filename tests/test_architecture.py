from __future__ import annotations

import ast
from pathlib import Path

INTERNAL_PREFIXES = (
    "specsmith.scaffolder",
    "specsmith.migrations",
    "specsmith.gui",
    "specsmith.agent.dispatch",
)

ALLOWED_IMPORTERS = {
    "specsmith.cli",
    "specsmith.scaffolder",
    "specsmith.migrations",
    "specsmith.gui",
    "specsmith.agent.dispatch",
    "specsmith.agent.orchestrator",
    "specsmith.governance_logic",
    "specsmith.serve",
    "specsmith.upgrader",
    "specsmith.sync",  # auto-triggers m007 migration in legacy markdown path
}


def _module_name(src_root: Path, py_file: Path) -> str:
    rel = py_file.relative_to(src_root).with_suffix("")
    return "specsmith." + ".".join(rel.parts)


def _matches_module_prefix(module: str, prefixes: tuple[str, ...]) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in prefixes)


def test_internal_modules_are_not_imported_outside_allowlist() -> None:
    src_root = Path(__file__).resolve().parents[1] / "src" / "specsmith"
    violations: list[str] = []
    for py_file in src_root.rglob("*.py"):
        importer = _module_name(src_root, py_file)
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for imported in names:
                if not imported:
                    continue
                if not imported.startswith("specsmith."):
                    continue
                if not _matches_module_prefix(imported, INTERNAL_PREFIXES):
                    continue
                if _matches_module_prefix(importer, tuple(ALLOWED_IMPORTERS)):
                    continue
                if importer.startswith(imported):
                    continue
                violations.append(f"{importer} imports internal module {imported}")
    assert not violations, "Architecture boundary canary failed:\n" + "\n".join(sorted(violations))
