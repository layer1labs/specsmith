# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""InputBar — multi-line input with Send / File / URL buttons and drag-drop."""

from __future__ import annotations

import urllib.request
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class _InputEdit(QPlainTextEdit):
    """QPlainTextEdit that emits send_requested on Ctrl+Enter."""

    send_requested = Signal()

    def keyPressEvent(self, event: object) -> None:  # type: ignore[override]

        ev = event  # type: QKeyEvent
        if ev.key() == Qt.Key_Return and ev.modifiers() & Qt.ControlModifier:
            self.send_requested.emit()
        else:
            super().keyPressEvent(ev)


class InputBar(QFrame):
    """Input area at the bottom of a session tab.

    Layout:
      [input text area              ]  [Send]
      [ 📎 File ]  [ 🔗 URL ]  [hint]

    Drag-dropping files onto the widget also works.

    Signals:
      send_requested(str)  — user submitted text
    """

    send_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("input_container")
        self.setAcceptDrops(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        # Row 1: text input + send button
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self._input = _InputEdit()
        self._input.setPlaceholderText(
            "Message the AEE agent… (Ctrl+Enter to send, drag files here)"
        )
        self._input.setMaximumHeight(100)
        self._input.setMinimumHeight(48)
        self._input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._input.send_requested.connect(self._on_send)
        row1.addWidget(self._input)

        self._send_btn = QPushButton("Send ↵")
        self._send_btn.setObjectName("send_btn")
        self._send_btn.setFixedWidth(90)
        self._send_btn.setFixedHeight(56)
        self._send_btn.clicked.connect(self._on_send)
        self._send_btn.setToolTip("Send message (Ctrl+Enter)")
        row1.addWidget(self._send_btn)

        layout.addLayout(row1)

        # Row 2: file / URL buttons + hint
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        file_btn = QPushButton("📎 File")
        file_btn.setFixedHeight(24)
        file_btn.setToolTip("Upload a file — text files injected as context, images/PDFs via OCR")
        file_btn.clicked.connect(self._on_file)
        row2.addWidget(file_btn)

        url_btn = QPushButton("🔗 URL")
        url_btn.setFixedHeight(24)
        url_btn.setToolTip("Fetch a URL and inject content as context")
        url_btn.clicked.connect(self._on_url)
        row2.addWidget(url_btn)

        clear_btn = QPushButton("🗑 Clear")
        clear_btn.setFixedHeight(24)
        clear_btn.setToolTip("Clear input")
        clear_btn.clicked.connect(self._input.clear)
        row2.addWidget(clear_btn)

        hint = QLabel("Ctrl+Enter to send • drag & drop files")
        hint.setObjectName("section_header")
        row2.addStretch()
        row2.addWidget(hint)
        layout.addLayout(row2)

    # ── Drag and drop ────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: object) -> None:  # type: ignore[override]
        from PySide6.QtGui import QDragEnterEvent

        ev: QDragEnterEvent = event  # type: ignore[assignment]
        if ev.mimeData().hasUrls():
            ev.acceptProposedAction()

    def dropEvent(self, event: object) -> None:  # type: ignore[override]
        from PySide6.QtGui import QDropEvent

        ev: QDropEvent = event  # type: ignore[assignment]
        for url in ev.mimeData().urls():
            local = url.toLocalFile()
            if local:
                self.inject_file(local)
        ev.acceptProposedAction()

    # ── Public API ───────────────────────────────────────────────────────────

    def inject_file(self, path: str) -> None:
        """Read a file and prepend its contents to the input."""
        p = Path(path)
        if not p.exists():
            return

        ext = p.suffix.lower()
        image_exts = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
        pdf_ext = ".pdf"

        if ext in image_exts or ext == pdf_ext:
            # Route through Mistral OCR if available
            self._inject_ocr(p)
        else:
            # Read as text
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                prefix = f"[File: {p.name}]\n```\n{content[:8000]}\n```\n\n"
                current = self._input.toPlainText()
                self._input.setPlainText(prefix + current)
            except Exception as e:  # noqa: BLE001
                self._input.setPlainText(f"[Error reading {p.name}: {e}]\n\n")

    def inject_url(self, url: str) -> None:
        """Fetch URL content and prepend to input."""
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "specsmith-gui/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
                raw = resp.read(32768).decode("utf-8", errors="replace")
            # Strip HTML tags (basic)
            import re

            text = re.sub(r"<[^>]+>", " ", raw)
            text = re.sub(r"\s+", " ", text).strip()[:4000]
            prefix = f"[URL: {url}]\n{text}\n\n"
            current = self._input.toPlainText()
            self._input.setPlainText(prefix + current)
        except Exception as e:  # noqa: BLE001
            current = self._input.toPlainText()
            self._input.setPlainText(f"[Error fetching {url}: {e}]\n\n" + current)

    def set_enabled(self, enabled: bool) -> None:
        self._input.setEnabled(enabled)
        self._send_btn.setEnabled(enabled)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_send(self) -> None:
        text = self._input.toPlainText().strip()
        if text:
            self._input.clear()
            self.send_requested.emit(text)

    def _on_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Upload File",
            str(Path.home()),
            "All Files (*.*)",
        )
        if path:
            self.inject_file(path)

    def _on_url(self) -> None:
        url, ok = QInputDialog.getText(self, "Fetch URL", "Enter URL:")
        if ok and url.strip():
            self.inject_url(url.strip())

    def _inject_ocr(self, p: Path) -> None:
        """Route image/PDF through Mistral Pixtral OCR."""
        import os

        api_key = os.environ.get("MISTRAL_API_KEY", "")
        if not api_key:
            current = self._input.toPlainText()
            self._input.setPlainText(
                f"[File: {p.name} — OCR requires MISTRAL_API_KEY]\n\n" + current
            )
            return
        try:
            from specsmith.agent.providers.mistral import MistralProvider

            provider = MistralProvider(model="pixtral-large-latest", api_key=api_key)
            text = provider.ocr_image(str(p))
            prefix = f"[File: {p.name} — OCR extract]\n{text[:6000]}\n\n"
            current = self._input.toPlainText()
            self._input.setPlainText(prefix + current)
        except Exception as e:  # noqa: BLE001
            current = self._input.toPlainText()
            self._input.setPlainText(f"[OCR error for {p.name}: {e}]\n\n" + current)
