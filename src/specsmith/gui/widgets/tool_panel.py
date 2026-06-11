# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""ToolPanel — left sidebar with specsmith tool buttons."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

# (display_name, tool_key, emoji)
_TOOLS: list[tuple[str, str, str]] = [
    ("Audit", "audit", "🔍"),
    ("Validate", "validate", "✅"),
    ("Doctor", "doctor", "🩺"),
    ("Stress Test", "stress_test", "⚡"),
    ("Epistemic Audit", "epistemic_audit", "🧠"),
    ("Belief Graph", "belief_graph", "🕸"),
    ("Export", "export", "📄"),
    ("Trace Verify", "trace_verify", "🔐"),
    ("REQ List", "req_list", "📋"),
    ("REQ Gaps", "req_gaps", "⚠"),
    ("Ledger List", "ledger_list", "📒"),
    ("Diff", "diff", "↔"),
]

_STATUS_IDLE = "idle"
_STATUS_RUNNING = "running"
_STATUS_PASS = "pass"
_STATUS_FAIL = "fail"


class ToolPanel(QFrame):
    """Collapsible sidebar with one button per specsmith tool.

    Emits tool_requested(tool_key) when a button is clicked.
    """

    tool_requested = Signal(str)  # tool key

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("tool_panel")
        self.setFixedWidth(160)
        self._buttons: dict[str, QToolButton] = {}
        self._statuses: dict[str, str] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Header
        hdr = QLabel("TOOLS")
        hdr.setObjectName("section_header")
        hdr.setAlignment(Qt.AlignCenter)
        hdr.setContentsMargins(8, 8, 8, 4)
        outer.addWidget(hdr)

        # Scroll area for buttons
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(3)

        for display, key, emoji in _TOOLS:
            btn = QToolButton()
            btn.setText(f" {emoji}  {display}")
            btn.setToolTip(f"Run specsmith {key.replace('_', '-')}")
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda checked=False, k=key: self.tool_requested.emit(k))
            self._buttons[key] = btn
            self._statuses[key] = _STATUS_IDLE
            layout.addWidget(btn)

        layout.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll)

    # ── Public API ───────────────────────────────────────────────────────────

    def set_tool_status(self, tool_key: str, status: str) -> None:
        """Set button status: idle | running | pass | fail."""
        btn = self._buttons.get(tool_key)
        if not btn:
            return
        self._statuses[tool_key] = status
        obj_name = {
            _STATUS_IDLE: "",
            _STATUS_RUNNING: "tool_running",
            _STATUS_PASS: "tool_pass",
            _STATUS_FAIL: "tool_fail",
        }.get(status, "")
        btn.setObjectName(obj_name)
        # Force QSS repaint
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        btn.setEnabled(status != _STATUS_RUNNING)

    def set_all_running(self, running: bool) -> None:
        for btn in self._buttons.values():
            btn.setEnabled(not running)
