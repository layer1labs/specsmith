# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""ProviderBar — provider and model selector dropdowns."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QWidget,
)

# ── Model lists per provider ─────────────────────────────────────────────────
_PROVIDER_MODELS: dict[str, list[str]] = {
    "anthropic": [
        "claude-opus-4-5",
        "claude-sonnet-4-5",
        "claude-haiku-4-5",
        "claude-opus-4-0",
        "claude-sonnet-4-0",
    ],
    "openai": [
        "gpt-4o",
        "gpt-4o-mini",
        "o3",
        "o3-mini",
        "o1",
        "gpt-4-turbo",
    ],
    "gemini": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-pro",
        "gemini-2.0-flash",
    ],
    "mistral": [
        "mistral-large-latest",
        "mistral-small-latest",
        "codestral-latest",
        "pixtral-large-latest",
        "pixtral-12b-2409",
    ],
    "ollama": [
        "qwen2.5:14b",
        "qwen2.5:7b",
        "llama3.2:latest",
        "deepseek-coder-v2:latest",
        "mistral:latest",
    ],
}

_PROVIDERS = list(_PROVIDER_MODELS.keys())


class ProviderBar(QFrame):
    """Top bar with provider + model dropdowns and project dir display.

    Signals:
      provider_changed(str)   — new provider name
      model_changed(str)      — new model name
    """

    provider_changed = Signal(str)
    model_changed = Signal(str)

    def __init__(
        self,
        project_dir: str = ".",
        provider: str = "anthropic",
        model: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("provider_bar")
        self._setup_ui(project_dir, provider, model)

    def _setup_ui(self, project_dir: str, provider: str, model: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(10)

        # Project dir (read-only display)
        proj_icon = QLabel("📁")
        layout.addWidget(proj_icon)
        self._dir_label = QLabel(project_dir)
        self._dir_label.setObjectName("section_header")
        self._dir_label.setMaximumWidth(280)
        self._dir_label.setToolTip(project_dir)
        layout.addWidget(self._dir_label)

        layout.addStretch()

        # Provider selector
        prov_label = QLabel("Provider:")
        prov_label.setObjectName("section_header")
        layout.addWidget(prov_label)

        self._provider_combo = QComboBox()
        for p in _PROVIDERS:
            self._provider_combo.addItem(p)
        idx = _PROVIDERS.index(provider) if provider in _PROVIDERS else 0
        self._provider_combo.setCurrentIndex(idx)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        layout.addWidget(self._provider_combo)

        # Model selector
        model_label = QLabel("Model:")
        model_label.setObjectName("section_header")
        layout.addWidget(model_label)

        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)  # allow typing custom model names
        self._populate_models(provider)
        if model:
            self._model_combo.setCurrentText(model)
        self._model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self._model_combo)

    def _populate_models(self, provider: str) -> None:
        self._model_combo.clear()
        models = _PROVIDER_MODELS.get(provider, [])
        for m in models:
            self._model_combo.addItem(m)

    def _on_provider_changed(self, provider: str) -> None:
        self._populate_models(provider)
        self.provider_changed.emit(provider)
        # Also emit the new default model
        default_model = self._model_combo.currentText()
        if default_model:
            self.model_changed.emit(default_model)

    def _on_model_changed(self, model: str) -> None:
        if model:
            self.model_changed.emit(model)

    # ── Public API ───────────────────────────────────────────────────────────

    def current_provider(self) -> str:
        return self._provider_combo.currentText()

    def current_model(self) -> str:
        return self._model_combo.currentText()

    def set_project_dir(self, path: str) -> None:
        self._dir_label.setText(path)
        self._dir_label.setToolTip(path)
