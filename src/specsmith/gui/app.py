# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith GUI bootstrap — QApplication setup and launch() entry point."""

from __future__ import annotations

import sys


def launch(
    project_dir: str = ".",
    provider_name: str | None = None,
    model: str | None = None,
) -> None:
    """Launch the AEE Workbench.

    Called by `specsmith gui` CLI command.
    Blocks until the window is closed.
    """
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtWidgets import QApplication

    from specsmith.gui.main_window import MainWindow
    from specsmith.gui.theme import qss

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("specsmith AEE Workbench")
    app.setOrganizationName("Layer1Labs")

    # Fusion style as the base (cross-platform, neutral widgets)
    app.setStyle("Fusion")

    # Apply AEE dark theme
    app.setStyleSheet(qss())

    # Font: prefer Inter/Segoe UI; fall back to system default
    preferred_fonts = ["Segoe UI", "Inter", "SF Pro Text", "Helvetica Neue", "Arial"]
    for font_name in preferred_fonts:
        if font_name in QFontDatabase.families():
            app.setFont(QFont(font_name, 12))
            break

    window = MainWindow(
        project_dir=project_dir,
        provider_name=provider_name,
        model=model,
    )
    window.show()

    sys.exit(app.exec())
