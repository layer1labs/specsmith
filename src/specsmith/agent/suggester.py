# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Lightweight NL-to-command suggester for `specsmith suggest-command` (REQ-131).

Given a partial natural-language fragment, return a structured suggestion
that the VS Code extension renders as inline ghost-text in the chat input.
Three classification buckets:

* ``command`` -- the input is shell-y (starts with an imperative verb that
  maps to a known CLI). Suggest a concrete shell command.
* ``utterance`` -- the input is plain English meant for the agent. Suggest
  a refined utterance that names a likely component (best-effort).
* ``passthrough`` -- input is too short or ambiguous; echo it back so the
  ghost-text matches what the user typed (no-op suggestion).

The suggester is **deterministic and LLM-free**. The IDE may layer an LLM
predictor on top, but the CLI baseline must always succeed quickly. If the
extension wants a richer suggestion, it can call `specsmith preflight
--predict-only` separately for utterances.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Common imperative verbs that map to shell-y intents.
_SHELL_VERBS = {
    "run",
    "exec",
    "execute",
    "kill",
    "stop",
    "start",
    "restart",
    "build",
    "test",
    "lint",
    "format",
    "git",
    "cd",
    "ls",
    "cat",
    "rm",
    "mv",
    "cp",
    "find",
    "grep",
    "ps",
    "top",
    "open",
    "edit",
    "tail",
    "head",
    "make",
    "npm",
    "pnpm",
    "yarn",
    "pip",
    "pipx",
    "uv",
    "pytest",
    "ruff",
    "mypy",
    "cargo",
    "go",
    "docker",
    "kubectl",
    "terraform",
}

# Map verb -> default refined command.
_VERB_TEMPLATES: dict[str, str] = {
    "run tests": "pytest -q",
    "run lint": "ruff check .",
    "run mypy": "mypy src/",
    "format": "ruff format .",
    "lint": "ruff check .",
    "test": "pytest -q",
    "build": "python -m build",
    "git status": "git --no-pager status",
    "git log": "git --no-pager log --oneline -20",
    "git diff": "git --no-pager diff",
}


@dataclass
class CommandSuggestion:
    """Output payload of :func:`suggest_command`."""

    kind: str  # "command" | "utterance" | "passthrough"
    suggestion: str
    confidence: float = 0.5
    reasoning: str = ""
    candidates: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "suggestion": self.suggestion,
            "confidence": round(self.confidence, 3),
            "reasoning": self.reasoning,
            "candidates": list(self.candidates),
        }


def classify(text: str) -> str:
    """Return ``command``, ``utterance``, or ``passthrough``."""
    stripped = text.strip()
    if len(stripped) < 2:
        return "passthrough"
    first = stripped.split()[0].lower()
    if first in _SHELL_VERBS:
        return "command"
    return "utterance"


def suggest_command(text: str, *, project_dir: Path | None = None) -> CommandSuggestion:
    """Return a structured suggestion for ``text``.

    The suggester is deterministic. It looks for verb prefixes and a short
    catalogue of common templates; if nothing matches, it returns the input
    unchanged with kind=``passthrough``.
    """
    stripped = text.strip()
    kind = classify(stripped)
    if kind == "passthrough":
        return CommandSuggestion(
            kind="passthrough",
            suggestion=text,
            confidence=0.0,
            reasoning="input too short to suggest",
        )
    if kind == "utterance":
        return _suggest_utterance(stripped, project_dir=project_dir)
    return _suggest_shell(stripped)


def _suggest_shell(text: str) -> CommandSuggestion:
    lower = text.lower()
    # Direct multi-word template match (e.g. "run tests").
    for phrase, command in _VERB_TEMPLATES.items():
        if lower.startswith(phrase):
            return CommandSuggestion(
                kind="command",
                suggestion=command,
                confidence=0.85,
                reasoning=f"matched template '{phrase}'",
            )
    # Single-verb fallback: if the user typed "git" alone, propose
    # `git status`. If "test", propose pytest -q.
    first = lower.split()[0]
    fallback = {
        "git": "git --no-pager status",
        "ls": "ls -la",
        "test": "pytest -q",
        "lint": "ruff check .",
        "format": "ruff format .",
        "build": "python -m build",
        "find": "find . -name '*.py'",
    }.get(first)
    if fallback and lower.strip() == first:
        return CommandSuggestion(
            kind="command",
            suggestion=fallback,
            confidence=0.7,
            reasoning=f"single verb '{first}' resolved to default command",
        )
    # Pass through what the user typed; mark as command anyway so the IDE
    # knows it's shell-y rather than NL.
    return CommandSuggestion(
        kind="command",
        suggestion=text,
        confidence=0.3,
        reasoning="recognised as shell command but no template applied",
    )


_REQ_REGEX = re.compile(r"REQ-[A-Z0-9-]+", re.IGNORECASE)
_KNOWN_VERBS = ("add", "fix", "refactor", "remove", "rename", "document", "test")


def _suggest_utterance(text: str, *, project_dir: Path | None) -> CommandSuggestion:
    lower = text.lower()
    candidates: list[str] = []

    # If the text already names a REQ, surface it verbatim with a higher
    # confidence — the user is already specific.
    matched = _REQ_REGEX.findall(text)
    if matched:
        return CommandSuggestion(
            kind="utterance",
            suggestion=text,
            confidence=0.9,
            reasoning=f"references {matched[0]} explicitly",
            candidates=matched,
        )

    # If the text starts with a change verb but doesn't name a component,
    # suggest a refined version that asks the user to add a target.
    first = lower.split()[0] if lower.split() else ""
    if first in _KNOWN_VERBS and len(lower.split()) <= 3:
        return CommandSuggestion(
            kind="utterance",
            suggestion=f"{text.rstrip()} (please name the component or file)",
            confidence=0.6,
            reasoning=f"verb '{first}' lacks an explicit target",
        )

    # Project-aware refinement: scan REQUIREMENTS.md for keywords that match
    # the input and propose the first hit. Best-effort; never blocks.
    if project_dir is not None:
        candidates = _scan_requirements(text, project_dir)
        if candidates:
            return CommandSuggestion(
                kind="utterance",
                suggestion=f"{text.rstrip()} ({candidates[0]})",
                confidence=0.65,
                reasoning=f"matched {candidates[0]} from REQUIREMENTS.md",
                candidates=candidates,
            )

    # Default: echo back unchanged.
    return CommandSuggestion(
        kind="utterance",
        suggestion=text,
        confidence=0.4,
        reasoning="no project-specific refinement available",
    )


def _scan_requirements(text: str, project_dir: Path) -> list[str]:
    """Return up to 5 REQ ids whose description shares words with ``text``."""
    candidates: list[tuple[int, str]] = []
    for path in (
        project_dir / "REQUIREMENTS.md",
        project_dir / "docs" / "REQUIREMENTS.md",
    ):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", text)}
        if not words:
            return []
        for match in re.finditer(
            r"^###?\s+(REQ-[A-Z0-9-]+)\s*(.*?)(?=^###?\s+REQ|^##\s|\Z)",
            content,
            re.MULTILINE | re.DOTALL,
        ):
            req_id, body = match.group(1), match.group(2)
            body_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", body)}
            score = len(words & body_words)
            if score > 0:
                candidates.append((score, req_id))
    candidates.sort(key=lambda x: (-x[0], x[1]))
    return [req for _, req in candidates[:5]]


__all__ = ["CommandSuggestion", "classify", "suggest_command"]
