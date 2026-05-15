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


_SKILL_PROMPT = """
You are an expert agent-skill designer for the specsmith AEE framework.
Given a description, produce a JSON object (no markdown fences) with these exact keys:
  name         - short title (\u2264 60 chars)
  purpose      - one-sentence purpose
  activation_rules - list of 2-4 strings describing when to activate
  input_schema - dict of {{field: type description}}
  output_schema - dict of {{field: type description}}
  epistemic_contract - one sentence about verifiability guarantees
  tools_used   - list of tool names (e.g. read_file, run_shell, run_tests)
  tests_required - list of 1-3 test descriptions
  stop_conditions - list of 2-3 stop conditions
  tags         - list of keyword tags

Description: {description}

Respond with ONLY valid JSON. No explanation, no markdown.
"""


def _build_skill_with_llm(description: str, tags: list[str]) -> SkillSpec | None:
    """Attempt to build a richer skill spec via the LLM provider.

    Returns None if no provider is available or the call fails.
    """
    import os

    # Detect whether any provider is configured.
    has_anthropic = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_ollama = bool(
        os.environ.get("OLLAMA_HOST") or os.environ.get("SPECSMITH_PROVIDER") == "ollama"
    )

    if not (has_anthropic or has_openai or has_ollama):
        return None  # No provider — skip LLM, fall through to stub

    try:
        from specsmith.agent.runner import AgentRunner

        runner = AgentRunner(project_dir=".")
        prompt = _SKILL_PROMPT.format(description=description)
        raw = runner.run_task(prompt)
        if not raw:
            return None

        # Strip accidental markdown fences
        raw = raw.strip()
        if raw.startswith("```"):
            raw = "\n".join(raw.splitlines()[1:])
        if raw.endswith("```"):
            raw = raw[: raw.rfind("```")]
        raw = raw.strip()

        data = json.loads(raw)
        skill_id = _generate_skill_id(data.get("name", description))
        return SkillSpec(
            id=skill_id,
            name=data.get("name", description[:60]),
            purpose=data.get("purpose", description),
            activation_rules=data.get("activation_rules", []),
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            epistemic_contract=data.get("epistemic_contract", ""),
            tools_used=data.get("tools_used", []),
            tests_required=data.get("tests_required", []),
            stop_conditions=data.get("stop_conditions", []),
            tags=tags + data.get("tags", []),
        )
    except Exception:  # noqa: BLE001 — always fall back to stub
        return None


def build_skill(
    description: str,
    project_dir: str = ".",
    tags: list[str] | None = None,
) -> SkillSpec:
    """Build a skill from a natural-language description.

    When an AI provider is configured (ANTHROPIC_API_KEY, OPENAI_API_KEY,
    or Ollama), uses the LLM to generate a richer skill spec.
    Falls back to a deterministic stub when no provider is available or
    the LLM call fails.
    """
    tags = tags or []

    # Try LLM-enriched generation first.
    spec = _build_skill_with_llm(description, tags)

    if spec is None:
        # Deterministic fallback — no LLM required.
        name = description.strip()[:60]
        spec = SkillSpec(
            id=_generate_skill_id(name),
            name=name,
            purpose=description.strip(),
            activation_rules=[f"User requests: {description[:80]}"],
            input_schema={"task": "string", "context": "string (optional)"},
            output_schema={"result": "string", "confidence": "number"},
            epistemic_contract="Output must be verifiable against the input task.",
            tools_used=["read_file", "run_shell"],
            tests_required=[f"Verify {name} produces correct output"],
            stop_conditions=["Confidence below 0.3", "Timeout exceeded"],
            tags=tags,
        )

    # Save to disk
    skill_dir = Path(project_dir).resolve() / ".specsmith" / "skills" / spec.id
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


def deactivate_skill(skill_id: str, project_dir: str = ".") -> bool:
    """Deactivate a skill by ID."""
    meta_path = Path(project_dir).resolve() / ".specsmith" / "skills" / skill_id / "skill.json"
    if not meta_path.is_file():
        return False
    try:
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        raw["active"] = False
        meta_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except (OSError, ValueError):
        return False


def delete_skill(skill_id: str, project_dir: str = ".") -> bool:
    """Delete a skill and its directory."""
    import shutil

    skill_dir = Path(project_dir).resolve() / ".specsmith" / "skills" / skill_id
    if not skill_dir.is_dir():
        return False
    try:
        shutil.rmtree(skill_dir)
        return True
    except OSError:
        return False


__all__ = [
    "SkillSpec",
    "activate_skill",
    "build_skill",
    "deactivate_skill",
    "delete_skill",
    "list_skills",
]
