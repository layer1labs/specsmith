# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""GovernanceStore — reads governance data from .specsmith/governance/*.yaml.

Priority:
  1. .specsmith/governance/*.yaml  (preferred — structured, machine-readable)
  2. docs/governance/*.md           (fallback — for legacy projects)

This allows a smooth migration path: run `specsmith migrate run --version 1`
to create the YAML files, then specsmith automatically uses them.

REQ-316: Governance data MUST be readable from .specsmith/governance/ YAML
         when present, with fallback to docs/governance/ MD.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class GovernanceStore:
    """Reads governance configuration from a project's .specsmith/governance/ directory."""

    def __init__(self, project_dir: str | Path) -> None:
        self.root = Path(project_dir).resolve()
        self._gov_dir = self.root / ".specsmith" / "governance"
        self._md_dir = self.root / "docs" / "governance"

    def has_yaml(self) -> bool:
        """Return True if .specsmith/governance/ YAML files exist."""
        return self._gov_dir.is_dir() and any(self._gov_dir.glob("*.yaml"))

    def load_rules(self) -> list[dict[str, Any]]:
        """Return H1-H22 governance rules as a list of dicts."""
        yaml_path = self._gov_dir / "rules.yaml"
        if yaml_path.is_file():
            return self._load_rules_yaml(yaml_path)

        # Fall back to parsing RULES.md
        md_path = self._md_dir / "RULES.md"
        if md_path.is_file():
            return self._parse_rules_md(md_path)

        # Built-in default (always available, no file needed)
        return self._builtin_rules()

    def load_axioms(self) -> list[dict[str, Any]]:
        """Return AEE epistemic axioms."""
        yaml_path = self._gov_dir / "axioms.yaml"
        if yaml_path.is_file():
            return self._load_yaml_list(yaml_path, "axioms")

        md_path = self._md_dir / "EPISTEMIC-AXIOMS.md"
        if md_path.is_file():
            return [{"source": "md", "content": md_path.read_text(encoding="utf-8")}]

        return []

    def load_roles(self) -> list[dict[str, Any]]:
        """Return agent role definitions."""
        yaml_path = self._gov_dir / "roles.yaml"
        if yaml_path.is_file():
            return self._load_yaml_list(yaml_path, "roles")

        md_path = self._md_dir / "ROLES.md"
        if md_path.is_file():
            return [{"source": "md", "content": md_path.read_text(encoding="utf-8")}]

        return []

    def load_config(self) -> dict[str, Any]:
        """Return governance configuration."""
        config_yaml = self._gov_dir / "config.yaml"
        if config_yaml.is_file():
            try:
                import yaml

                raw = yaml.safe_load(config_yaml.read_text(encoding="utf-8")) or {}
                return raw if isinstance(raw, dict) else {}
            except Exception:  # noqa: BLE001
                pass

        # Fall back to .specsmith/config.yml
        specsmith_config = self.root / ".specsmith" / "config.yml"
        if specsmith_config.is_file():
            try:
                import yaml

                raw = yaml.safe_load(specsmith_config.read_text(encoding="utf-8")) or {}
                return raw if isinstance(raw, dict) else {}
            except Exception:  # noqa: BLE001
                pass

        return {}

    def load_all(self) -> dict[str, Any]:
        """Return all governance data as a dict."""
        return {
            "rules": self.load_rules(),
            "axioms": self.load_axioms(),
            "roles": self.load_roles(),
            "config": self.load_config(),
            "has_yaml": self.has_yaml(),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load_rules_yaml(self, path: Path) -> list[dict[str, Any]]:
        try:
            import yaml

            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            rules = raw.get("rules", [])
            if isinstance(rules, list):
                return [r for r in rules if isinstance(r, dict)]
        except Exception:  # noqa: BLE001
            pass
        return []

    def _load_yaml_list(self, path: Path, key: str) -> list[dict[str, Any]]:
        try:
            import yaml

            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            items = raw.get(key, [])
            if isinstance(items, list):
                return [i for i in items if isinstance(i, dict)]
        except Exception:  # noqa: BLE001
            pass
        return []

    def _parse_rules_md(self, path: Path) -> list[dict[str, Any]]:
        """Parse H-rules from RULES.md."""
        text = path.read_text(encoding="utf-8", errors="replace")
        rules: list[dict[str, Any]] = []
        pattern = re.compile(
            r"### (H\d+) [—\-] (.+?)\n(.*?)(?=\n### H|\Z)",
            re.DOTALL,
        )
        for match in pattern.finditer(text):
            rules.append(
                {
                    "id": match.group(1),
                    "name": match.group(2).strip(),
                    "description": match.group(3).strip()[:300],
                    "source": "md",
                }
            )
        return rules

    def _builtin_rules(self) -> list[dict[str, Any]]:
        """Return built-in rule definitions (fallback when no files exist)."""
        # Try the compliance module's rule list (already has H1-H22 structured)
        try:
            # Old compliance.py (root module — has get_governance_rules_status)
            import importlib

            mod = importlib.import_module("specsmith.compliance")
            fn = getattr(mod, "get_governance_rules_status", None)
            if callable(fn):
                return fn(".")
        except Exception:  # noqa: BLE001
            pass

        # Minimal inline fallback — H1-H22
        return [
            {"id": f"H{i}", "name": f"Rule H{i}", "description": "", "source": "builtin"}
            for i in range(1, 23)
        ]
