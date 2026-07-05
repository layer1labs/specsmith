# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Per-turn intent classifier and Ollama model router (REQ-388, REQ-389).

``ModelRouter`` classifies each user utterance into one of three roles
(``general``, ``coding``, ``reasoning``) using a fast keyword + slash-command
heuristic and returns the best Ollama model tag for that role.  The router
only changes the active model when the role classification changes, so a
long coding session stays on the coder model without emitting a switch event
on every turn.

Usage
-----
::

    router = ModelRouter({"general": "qwen2.5:14b",
                          "coding": "qwen2.5-coder:14b",
                          "reasoning": "deepseek-r1:14b"})
    model_tag, switched = router.route("write a function that ...")
    if switched:
        print(f"→ switched to {model_tag}")
"""

from __future__ import annotations

__all__ = ["ModelRouter", "classify_intent"]

# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

# Slash commands that strongly signal coding work.
_CODING_SLASH: frozenset[str] = frozenset({"/code", "/fix", "/refactor", "/test", "/commit", "/pr"})

# Slash commands that signal analytical / planning work.
_REASONING_SLASH: frozenset[str] = frozenset({"/architect", "/plan", "/audit", "/review", "/why"})

# Keywords that indicate the user wants code written or bugs fixed.
_CODING_KEYWORDS: frozenset[str] = frozenset(
    {
        "write",
        "implement",
        "function",
        "method",
        "class",
        "bug",
        "error",
        "fix",
        "patch",
        "test",
        "debug",
        "refactor",
        "import",
        "syntax",
        "compile",
        "code",
        "script",
        "module",
        "api",
        "endpoint",
        "snippet",
        "variable",
        "loop",
        "array",
        "dict",
        "parse",
        "format",
        "regex",
        "unittest",
        "pytest",
        "mock",
        "stub",
        "boilerplate",
        "scaffold",
        "decorator",
        "lambda",
        "iterator",
        "generator",
        "async",
        "await",
        "coroutine",
        "type",
        "hint",
        "annotation",
        "dataclass",
    },
)

# Keywords that indicate the user wants analysis, architecture, or deep reasoning.
_REASONING_KEYWORDS: frozenset[str] = frozenset(
    {
        "analyze",
        "analyse",
        "explain",
        "reason",
        "strategy",
        "architecture",
        "design",
        "evaluate",
        "compare",
        "tradeoff",
        "trade-off",
        "review",
        "audit",
        "assess",
        "consider",
        "approach",
        "decision",
        "structure",
        "plan",
        "requirements",
        "spec",
        "diagram",
        "model",
        "rationale",
        "justify",
        "pros",
        "cons",
        "recommend",
        "alternative",
        "consequence",
        "impact",
        "risk",
        "bottleneck",
        "complexity",
        "scalability",
    },
)


def classify_intent(text: str) -> str:
    """Classify *text* as ``"coding"``, ``"reasoning"``, or ``"general"``.

    The classification is intentionally fast (O(n) word scan, no ML) so it
    adds negligible latency to each turn.  Rules in priority order:

    1. Slash-command prefix → maps directly to a role.
    2. Keyword match → first-match wins; coding keywords checked before
       reasoning keywords so ``/fix a bug in the design docs`` routes to
       coding.
    3. Default → ``"general"``.
    """
    text_stripped = text.strip()

    # --- Rule 1: explicit slash-command ---
    head = text_stripped.split()[0].lower() if text_stripped else ""
    if head in _CODING_SLASH:
        return "coding"
    if head in _REASONING_SLASH:
        return "reasoning"

    # --- Rule 2: keyword scan ---
    words = set(text_stripped.lower().split())
    if words & _CODING_KEYWORDS:
        return "coding"
    if words & _REASONING_KEYWORDS:
        return "reasoning"

    return "general"


# ---------------------------------------------------------------------------
# ModelRouter
# ---------------------------------------------------------------------------


class ModelRouter:
    """Routes each user turn to the appropriate Ollama model (REQ-388).

    Parameters
    ----------
    roles:
        Mapping of role name (``"general"``, ``"coding"``, ``"reasoning"``)
        to Ollama model tag.  Missing roles fall back to ``"general"``; if
        ``"general"`` is also missing the router returns ``(None, False)``
        and the caller uses whatever model was already set.

    """

    def __init__(self, roles: dict[str, str | None]) -> None:
        # Strip out None values so lookups never return None.
        self._roles: dict[str, str] = {k: v for k, v in roles.items() if v}
        self._current_role: str | None = None
        self._current_model: str | None = None

    # ── Public interface ────────────────────────────────────────────────────

    def route(self, text: str) -> tuple[str | None, bool]:
        """Classify *text* and return the model tag for the detected role.

        Returns
        -------
        (model_tag, switched)
            *model_tag* is the Ollama tag to use for this turn, or ``None``
            when no role→model mapping is configured.
            *switched* is ``True`` when the model changed from the previous
            turn (useful for emitting a switch notification).

        """
        if not self._roles:
            return None, False

        role = classify_intent(text)

        # Resolve: prefer exact role match, fallback to general, then any.
        model = (
            self._roles.get(role) or self._roles.get("general") or next(iter(self._roles.values()))
        )

        if model == self._current_model:
            return model, False

        prev_role = self._current_role
        self._current_role = role
        self._current_model = model
        switched = prev_role is not None  # first call is not a "switch"
        return model, switched

    @property
    def active_model(self) -> str | None:
        """Model tag currently in use, or ``None`` before the first turn."""
        return self._current_model

    @property
    def active_role(self) -> str | None:
        """Role name currently in use, or ``None`` before the first turn."""
        return self._current_role

    def table(self) -> str:
        """Human-readable routing table for the ``/models`` slash command."""
        if not self._roles:
            return "  (no multi-model routing configured)"
        role_order = ["general", "coding", "reasoning"]
        lines: list[str] = ["  Multi-model routing:"]
        for role in role_order:
            if role in self._roles:
                active_marker = " ◀ active" if role == self._current_role else ""
                lines.append(f"    {role:<10} → {self._roles[role]}{active_marker}")
        # Any roles not in the standard order
        for role, model in self._roles.items():
            if role not in role_order:
                active_marker = " ◀ active" if role == self._current_role else ""
                lines.append(f"    {role:<10} → {model}{active_marker}")
        return "\n".join(lines)
