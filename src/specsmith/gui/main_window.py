# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""MainWindow — top-level AEE Workbench window."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from specsmith.gui.session_tab import SessionTab
from specsmith.gui.widgets.update_checker import UpdateChecker


class _NewSessionDialog(QDialog):
    """Dialog to create a new agent session tab."""

    def __init__(
        self,
        default_dir: str = ".",
        default_provider: str = "anthropic",
        default_model: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("New Agent Session")
        self.setMinimumWidth(420)
        self._dir = default_dir
        self._setup_ui(default_dir, default_provider, default_model)

    def _setup_ui(self, default_dir: str, default_provider: str, default_model: str) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("🧠  New AEE Agent Session")
        title.setStyleSheet("font-size: 15px; font-weight: 600; padding: 8px 0;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # Project directory
        dir_row_widget = QWidget()
        dir_row = QFormLayout(dir_row_widget)
        dir_row.setContentsMargins(0, 0, 0, 0)

        self._dir_edit = QLineEdit(default_dir)
        browse_btn = QPushButton("…")
        browse_btn.setFixedWidth(32)
        browse_btn.clicked.connect(self._browse_dir)

        from PySide6.QtWidgets import QHBoxLayout

        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(4)
        dir_layout.addWidget(self._dir_edit)
        dir_layout.addWidget(browse_btn)
        form.addRow("Project dir:", self._build_row(self._dir_edit, browse_btn))

        # Provider
        from specsmith.gui.widgets.provider_bar import _PROVIDERS

        self._provider_combo = QComboBox()
        for p in _PROVIDERS:
            self._provider_combo.addItem(p)
        idx = _PROVIDERS.index(default_provider) if default_provider in _PROVIDERS else 0
        self._provider_combo.setCurrentIndex(idx)
        self._provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form.addRow("Provider:", self._provider_combo)

        # Model
        from specsmith.gui.widgets.provider_bar import _PROVIDER_MODELS

        self._model_combo = QComboBox()
        self._model_combo.setEditable(True)
        for m in _PROVIDER_MODELS.get(default_provider, []):
            self._model_combo.addItem(m)
        if default_model:
            self._model_combo.setCurrentText(default_model)
        form.addRow("Model:", self._model_combo)

        layout.addLayout(form)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_row(self, edit: QLineEdit, btn: QPushButton) -> QWidget:
        w = QWidget()
        from PySide6.QtWidgets import QHBoxLayout

        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(4)
        h.addWidget(edit)
        h.addWidget(btn)
        return w

    def _browse_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Select Project Directory", self._dir)
        if d:
            self._dir_edit.setText(d)

    def _on_provider_changed(self, provider: str) -> None:
        from specsmith.gui.widgets.provider_bar import _PROVIDER_MODELS

        self._model_combo.clear()
        for m in _PROVIDER_MODELS.get(provider, []):
            self._model_combo.addItem(m)

    # ── Result accessors ──────────────────────────────────────────────────────

    @property
    def project_dir(self) -> str:
        return self._dir_edit.text().strip() or "."

    @property
    def provider(self) -> str:
        return self._provider_combo.currentText()

    @property
    def model(self) -> str:
        return self._model_combo.currentText()


class MainWindow(QMainWindow):
    """Main application window with tabbed agent sessions."""

    def __init__(
        self,
        project_dir: str = ".",
        provider_name: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        self._default_dir = project_dir
        self._default_provider = provider_name or "anthropic"
        self._default_model = model or ""

        self.setWindowTitle("specsmith — AEE Workbench")
        self.resize(1280, 800)
        self.setMinimumSize(900, 600)

        self._setup_ui()
        self._setup_menu()
        self._setup_status_bar()
        self._start_update_checker()

        # Open the first tab
        self._new_session(project_dir, self._default_provider, self._default_model)

    # ── UI setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(True)
        self._tabs.setMovable(True)
        self._tabs.tabCloseRequested.connect(self._close_tab)

        # "+" button to add new session
        add_btn = QPushButton("+")
        add_btn.setFixedSize(28, 24)
        add_btn.setToolTip("New agent session")
        add_btn.clicked.connect(self._open_new_session_dialog)
        self._tabs.setCornerWidget(add_btn, Qt.Corner.TopRightCorner)

        self.setCentralWidget(self._tabs)

    def _setup_menu(self) -> None:
        mb = self.menuBar()

        # Session menu
        session_menu = mb.addMenu("&Session")
        new_act = session_menu.addAction("&New Session…")
        new_act.setShortcut("Ctrl+T")
        new_act.triggered.connect(self._open_new_session_dialog)

        close_act = session_menu.addAction("&Close Tab")
        close_act.setShortcut("Ctrl+W")
        close_act.triggered.connect(lambda: self._close_tab(self._tabs.currentIndex()))

        session_menu.addSeparator()
        clear_act = session_menu.addAction("Clear &History")
        clear_act.triggered.connect(self._clear_current_history)

        session_menu.addSeparator()
        quit_act = session_menu.addAction("&Quit")
        quit_act.setShortcut("Ctrl+Q")
        quit_act.triggered.connect(self.close)

        # View menu
        view_menu = mb.addMenu("&View")
        view_menu.addAction("Next Tab").setShortcut("Ctrl+Tab")
        view_menu.addAction("Previous Tab").setShortcut("Ctrl+Shift+Tab")

        # Help menu
        help_menu = mb.addMenu("&Help")
        about_act = help_menu.addAction("&About specsmith")
        about_act.triggered.connect(self._show_about)

    def _setup_status_bar(self) -> None:
        sb = self.statusBar()
        self._status_version = QLabel("specsmith")
        self._status_epi = QLabel("🧠 —")
        self._status_epi.setObjectName("epi_healthy")
        self._status_update = QLabel("")
        self._status_update.setObjectName("update_label")

        sb.addWidget(self._status_version)
        sb.addPermanentWidget(self._status_epi)
        sb.addPermanentWidget(self._status_update)

        # Show installed version
        try:
            import importlib.metadata

            ver = importlib.metadata.version("specsmith")
            self._status_version.setText(f"specsmith {ver}")
        except Exception:  # noqa: BLE001
            pass

    def _start_update_checker(self) -> None:
        self._updater = UpdateChecker(self)
        self._updater.updated.connect(self._on_updated)
        self._updater.check_done.connect(lambda v: None)  # already up to date
        self._updater.start()

    # ── Tab management ────────────────────────────────────────────────────────

    def _new_session(self, project_dir: str, provider: str, model: str) -> SessionTab:
        tab = SessionTab(
            project_dir=project_dir,
            provider_name=provider,
            model=model or None,
        )
        tab.epistemic_updated.connect(self._on_epistemic_updated)
        label = tab.tab_label()
        idx = self._tabs.addTab(tab, label)
        self._tabs.setCurrentIndex(idx)
        return tab

    def _open_new_session_dialog(self) -> None:
        dlg = _NewSessionDialog(
            default_dir=self._default_dir,
            default_provider=self._default_provider,
            default_model=self._default_model,
            parent=self,
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._new_session(dlg.project_dir, dlg.provider, dlg.model)

    def _close_tab(self, index: int) -> None:
        if self._tabs.count() <= 1:
            # Don't close the last tab; close the window instead
            self.close()
            return
        widget = self._tabs.widget(index)
        self._tabs.removeTab(index)
        if widget:
            widget.deleteLater()

    def _clear_current_history(self) -> None:
        tab = self._tabs.currentWidget()
        if isinstance(tab, SessionTab):
            tab.clear_history()

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_updated(self, version: str) -> None:
        self._status_update.setText(f"↑ Updated to {version}")
        # Also update version label
        self._status_version.setText(f"specsmith {version}")

    def _on_epistemic_updated(self, status: str) -> None:
        self._status_epi.setText(status)
        # Style by health
        if "✓" in status:
            self._status_epi.setObjectName("epi_healthy")
        elif "⚠" in status:
            self._status_epi.setObjectName("epi_warn")
        else:
            self._status_epi.setObjectName("epi_error")
        # Force QSS repaint
        self._status_epi.style().unpolish(self._status_epi)
        self._status_epi.style().polish(self._status_epi)

    def _show_about(self) -> None:
        try:
            import importlib.metadata

            ver = importlib.metadata.version("specsmith")
        except Exception:  # noqa: BLE001
            ver = "unknown"
        QMessageBox.about(
            self,
            "About specsmith AEE Workbench",
            f"<h2>specsmith {ver}</h2>"
            "<p>Applied Epistemic Engineering Workbench</p>"
            "<p>Belief artifacts as code — codable, testable, deployable.</p>"
            "<p><a href='https://specsmith.readthedocs.io'>Documentation</a></p>",
        )
