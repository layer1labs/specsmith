# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs / BitConcepts, LLC.
"""AI-powered Skills Builder — generate agent skills from natural-language descriptions.

Skills follow the SkillNet-style ontology: each skill is a folder containing
a SKILL.md file with structured metadata (name, purpose, activation rules,
input/output schema, epistemic contract, tools used, tests required).

Usage:
    from specsmith.skills_builder import build_skill, list_skills
    skill = build_skill("Summarize a Python file into bullet points")
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SkillSpec:
    """Structured specification for an agent skill."""

    id: str
    name: str
    purpose: str
    activation_rules: list[str] = field(default_factory=list)
    input_schema: dict[str, str] = field(default_factory=dict)
    output_schema: dict[str, str] = field(default_factory=dict)
    epistemic_contract: str = ""
    tools_used: list[str] = field(default_factory=list)
    tests_required: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    active: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "purpose": self.purpose,
            "activation_rules": self.activation_rules,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "epistemic_contract": self.epistemic_contract,
            "tools_used": self.tools_used,
            "tests_required": self.tests_required,
            "stop_conditions": self.stop_conditions,
            "tags": self.tags,
            "active": self.active,
        }

    def to_markdown(self) -> str:
        """Generate SKILL.md content."""
        lines = [
            f"# {self.name}",
            "",
            f"**ID:** {self.id}",
            f"**Purpose:** {self.purpose}",
            "",
            "## Activation Rules",
            "",
        ]
        for rule in self.activation_rules:
            lines.append(f"- {rule}")
        lines.extend(
            [
                "",
                "## Input Schema",
                "",
                "```json",
                json.dumps(self.input_schema, indent=2),
                "```",
                "",
                "## Output Schema",
                "",
                "```json",
                json.dumps(self.output_schema, indent=2),
                "```",
                "",
                "## Epistemic Contract",
                "",
                self.epistemic_contract or "No epistemic contract defined.",
                "",
                "## Tools Used",
                "",
            ]
        )
        for tool in self.tools_used:
            lines.append(f"- {tool}")
        lines.extend(["", "## Tests Required", ""])
        for test in self.tests_required:
            lines.append(f"- {test}")
        lines.extend(["", "## Stop Conditions", ""])
        for cond in self.stop_conditions:
            lines.append(f"- {cond}")
        return "\n".join(lines)


def _generate_skill_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower().strip())[:30]
    return f"skill-{slug}-{uuid.uuid4().hex[:6]}"


def build_skill(
    description: str,
    project_dir: str = ".",
    tags: list[str] | None = None,
) -> SkillSpec:
    """Build a skill from a natural-language description.

    Currently generates a deterministic skill spec from the description.
    When an AI provider is configured, this will use the LLM to generate
    richer skill content.
    """
    # Deterministic generation (no LLM required)
    name = description.strip()[:60]
    skill_id = _generate_skill_id(name)

    spec = SkillSpec(
        id=skill_id,
        name=name,
        purpose=description.strip(),
        activation_rules=[f"User requests: {description[:80]}"],
        input_schema={"task": "string", "context": "string (optional)"},
        output_schema={"result": "string", "confidence": "number"},
        epistemic_contract="Output must be verifiable against the input task.",
        tools_used=["read_file", "run_shell"],
        tests_required=[f"Verify {name} produces correct output"],
        stop_conditions=["Confidence below 0.3", "Timeout exceeded"],
        tags=tags or [],
    )

    # Save to disk
    skill_dir = Path(project_dir).resolve() / ".specsmith" / "skills" / skill_id
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(spec.to_markdown(), encoding="utf-8")

    # Save JSON metadata
    (skill_dir / "skill.json").write_text(
        json.dumps(spec.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return spec


def list_skills(project_dir: str = ".") -> list[SkillSpec]:
    """List all available skills in the project."""
    skills_dir = Path(project_dir).resolve() / ".specsmith" / "skills"
    if not skills_dir.is_dir():
        return []
    skills: list[SkillSpec] = []
    for skill_dir in sorted(skills_dir.iterdir()):
        meta_path = skill_dir / "skill.json"
        if meta_path.is_file():
            try:
                raw = json.loads(meta_path.read_text(encoding="utf-8"))
                skills.append(
                    SkillSpec(
                        id=raw.get("id", ""),
                        name=raw.get("name", ""),
                        purpose=raw.get("purpose", ""),
                        activation_rules=raw.get("activation_rules", []),
                        tools_used=raw.get("tools_used", []),
                        tags=raw.get("tags", []),
                        active=raw.get("active", False),
                    )
                )
            except (OSError, ValueError):
                continue
    return skills


def activate_skill(skill_id: str, project_dir: str = ".") -> bool:
    """Activate a skill by ID."""
    meta_path = Path(project_dir).resolve() / ".specsmith" / "skills" / skill_id / "skill.json"
    if not meta_path.is_file():
        return False
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        raw["active"] = True
        meta_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except (OSError, ValueError):
        return False


__all__ = ["SkillSpec", "activate_skill", "build_skill", "list_skills"]
