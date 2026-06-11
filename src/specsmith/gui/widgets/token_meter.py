# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""TokenMeter — context window fill bar with cost tracking."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QWidget

from specsmith.gui import theme

# Context window sizes by model family (tokens)
_CONTEXT_SIZES: dict[str, int] = {
    "claude": 200_000,
    "gpt-4o": 128_000,
    "gpt-4": 128_000,
    "o1": 200_000,
    "o3": 200_000,
    "gemini": 1_000_000,
    "mistral": 128_000,
    "default": 128_000,
}

_WARN_PCT = 70
_CRIT_PCT = 90


def _context_size_for(model: str) -> int:
    model_lower = (model or "").lower()
    for key, size in _CONTEXT_SIZES.items():
        if key in model_lower:
            return size
    return _CONTEXT_SIZES["default"]


class TokenMeter(QFrame):
    """Horizontal bar showing context fill % + token counts + cost.

    Emits optimize_suggested when fill exceeds the warn threshold.
    """

    optimize_suggested = Signal(float)  # fill_pct

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("token_bar")
        self._model = "default"
        self._in_tokens = 0
        self._out_tokens = 0
        self._cost_usd = 0.0
        self._warned = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        # Context label
        ctx_label = QLabel("Context")
        ctx_label.setObjectName("section_header")
        ctx_label.setFixedWidth(52)
        layout.addWidget(ctx_label)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(6)
        layout.addWidget(self._bar, stretch=1)

        # Fill percent label
        self._pct_label = QLabel("0%")
        self._pct_label.setObjectName("section_header")
        self._pct_label.setFixedWidth(36)
        layout.addWidget(self._pct_label)

        # Token counts
        self._token_label = QLabel("0 + 0 tokens")
        self._token_label.setObjectName("section_header")
        layout.addWidget(self._token_label)

        # Cost label
        self._cost_label = QLabel("$0.0000")
        self._cost_label.setObjectName("cost_label")
        layout.addWidget(self._cost_label)

    # ── Public API ───────────────────────────────────────────────────────────

    def set_model(self, model: str) -> None:
        self._model = model
        self._warned = False
        self.update_display(self._in_tokens, self._out_tokens, self._cost_usd)

    def update_display(self, in_tokens: int, out_tokens: int, cost_usd: float) -> None:
        """Update all token meter fields."""
        self._in_tokens = in_tokens
        self._out_tokens = out_tokens
        self._cost_usd = cost_usd

        total = in_tokens + out_tokens
        ctx_size = _context_size_for(self._model)
        fill_pct = min(100, int(total / ctx_size * 100))

        self._bar.setValue(fill_pct)
        self._pct_label.setText(f"{fill_pct}%")
        self._token_label.setText(f"{in_tokens:,} + {out_tokens:,}")
        self._cost_label.setText(f"${cost_usd:.4f}")

        # Color the bar by fill level
        if fill_pct >= _CRIT_PCT:
            chunk_css = f"QProgressBar::chunk {{ background: {theme.RED}; border-radius: 3px; }}"
        elif fill_pct >= _WARN_PCT:
            chunk_css = f"QProgressBar::chunk {{ background: {theme.AMBER}; border-radius: 3px; }}"
        else:
            chunk_css = f"QProgressBar::chunk {{ background: {theme.GREEN}; border-radius: 3px; }}"
        self._bar.setStyleSheet(chunk_css)

        # Emit optimization suggestion once when crossing warn threshold
        if fill_pct >= _WARN_PCT and not self._warned:
            self._warned = True
            self.optimize_suggested.emit(fill_pct)
        elif fill_pct < _WARN_PCT:
            self._warned = False

    def reset(self) -> None:
        self._in_tokens = 0
        self._out_tokens = 0
        self._cost_usd = 0.0
        self._warned = False
        self.update_display(0, 0, 0.0)
