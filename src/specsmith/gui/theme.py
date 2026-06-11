# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""AEE Workbench theme — deep navy / teal / amber palette."""

# ── Palette ────────────────────────────────────────────────────────────────
BG_BASE = "#0d1117"  # near-black canvas
BG_SURFACE = "#161b22"  # card / panel background
BG_ELEVATED = "#1c2128"  # slightly raised elements
BG_INPUT = "#21262d"  # text-input fields
BORDER = "#30363d"  # subtle dividers
BORDER_FOCUS = "#0d9488"  # teal focus ring

TEXT_PRIMARY = "#e6edf3"  # main text
TEXT_SECONDARY = "#8b949e"  # muted labels
TEXT_DIM = "#484f58"  # disabled / very muted

TEAL = "#0d9488"  # primary accent
TEAL_LIGHT = "#2dd4bf"  # hover / highlight
AMBER = "#d97706"  # warnings / tool blocks
AMBER_LIGHT = "#fbbf24"  # tool result header
RED = "#f85149"  # errors / critical
GREEN = "#3fb950"  # success / pass
BLUE = "#58a6ff"  # links / info

# ── Message colours ─────────────────────────────────────────────────────────
MSG_USER_BG = "#0e3a47"  # user bubble bg
MSG_ASSISTANT_BG = "#161b22"
MSG_TOOL_BG = "#1c160a"  # dark amber tint for tool blocks
MSG_SYSTEM_BG = "#0d1117"

# ── Token-meter thresholds ───────────────────────────────────────────────────
TOKEN_GREEN_CSS = f"background: {GREEN};"
TOKEN_YELLOW_CSS = f"background: {AMBER};"
TOKEN_RED_CSS = f"background: {RED};"


def qss() -> str:
    """Return the full QSS stylesheet for the application."""
    return f"""
/* ── Global ──────────────────────────────────────────────────────────── */
* {{
    font-family: "Segoe UI", "Inter", "SF Pro Text", system-ui, sans-serif;
    font-size: 13px;
    color: {TEXT_PRIMARY};
    outline: none;
}}

QMainWindow, QDialog, QWidget {{
    background-color: {BG_BASE};
}}

/* ── Tab bar ─────────────────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background: {BG_BASE};
}}
QTabBar::tab {{
    background: {BG_SURFACE};
    color: {TEXT_SECONDARY};
    padding: 6px 16px;
    border: 1px solid {BORDER};
    border-bottom: none;
    margin-right: 2px;
    border-radius: 4px 4px 0 0;
    min-width: 120px;
}}
QTabBar::tab:selected {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border-bottom: 2px solid {TEAL};
}}
QTabBar::tab:hover:!selected {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
}}

/* ── Scroll bars ─────────────────────────────────────────────────────── */
QScrollBar:vertical {{
    background: {BG_SURFACE};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {TEXT_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: {BG_SURFACE};
    height: 8px;
}}
QScrollBar::handle:horizontal {{
    background: {BORDER};
    border-radius: 4px;
    min-width: 24px;
}}

/* ── Text inputs ─────────────────────────────────────────────────────── */
QTextEdit, QPlainTextEdit, QLineEdit {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 8px;
    color: {TEXT_PRIMARY};
    selection-background-color: {TEAL};
}}
QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {{
    border: 1px solid {BORDER_FOCUS};
}}
QTextBrowser {{
    background: {BG_BASE};
    border: none;
    color: {TEXT_PRIMARY};
}}

/* ── Buttons ─────────────────────────────────────────────────────────── */
QPushButton {{
    background: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 14px;
    color: {TEXT_PRIMARY};
    font-weight: 500;
}}
QPushButton:hover {{
    background: {TEAL};
    border-color: {TEAL};
    color: white;
}}
QPushButton:pressed {{
    background: {TEAL_LIGHT};
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
    background: {BG_SURFACE};
}}
QPushButton#send_btn {{
    background: {TEAL};
    border: none;
    color: white;
    font-weight: 600;
    padding: 8px 20px;
    border-radius: 6px;
}}
QPushButton#send_btn:hover {{
    background: {TEAL_LIGHT};
}}
QPushButton#send_btn:disabled {{
    background: {TEXT_DIM};
    color: {BG_BASE};
}}

/* ── Tool buttons ────────────────────────────────────────────────────── */
QToolButton {{
    background: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 8px;
    color: {TEXT_SECONDARY};
    text-align: left;
}}
QToolButton:hover {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border-color: {TEAL};
}}
QToolButton#tool_pass {{
    border-left: 3px solid {GREEN};
}}
QToolButton#tool_fail {{
    border-left: 3px solid {RED};
}}
QToolButton#tool_running {{
    border-left: 3px solid {AMBER};
}}

/* ── Combo boxes ─────────────────────────────────────────────────────── */
QComboBox {{
    background: {BG_INPUT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px 8px;
    color: {TEXT_PRIMARY};
    min-width: 120px;
}}
QComboBox:focus {{
    border-color: {BORDER_FOCUS};
}}
QComboBox::drop-down {{
    border: none;
    width: 20px;
}}
QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_SECONDARY};
    margin-right: 4px;
}}
QComboBox QAbstractItemView {{
    background: {BG_ELEVATED};
    border: 1px solid {BORDER};
    selection-background-color: {TEAL};
    color: {TEXT_PRIMARY};
}}

/* ── Labels ──────────────────────────────────────────────────────────── */
QLabel {{
    color: {TEXT_PRIMARY};
    background: transparent;
}}
QLabel#section_header {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    padding: 4px 0 2px 0;
}}
QLabel#cost_label {{
    color: {AMBER_LIGHT};
    font-size: 11px;
    font-weight: 500;
}}
QLabel#update_label {{
    color: {GREEN};
    font-size: 11px;
}}

/* ── Progress bar (token meter) ──────────────────────────────────────── */
QProgressBar {{
    background: {BG_ELEVATED};
    border: 1px solid {BORDER};
    border-radius: 3px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {GREEN};
    border-radius: 3px;
}}

/* ── Splitter ─────────────────────────────────────────────────────────── */
QSplitter::handle {{
    background: {BORDER};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}

/* ── Status bar ──────────────────────────────────────────────────────── */
QStatusBar {{
    background: {BG_SURFACE};
    border-top: 1px solid {BORDER};
    color: {TEXT_SECONDARY};
    font-size: 11px;
}}
QStatusBar QLabel {{
    color: {TEXT_SECONDARY};
    font-size: 11px;
    padding: 0 8px;
}}

/* ── Menu bar ────────────────────────────────────────────────────────── */
QMenuBar {{
    background: {BG_SURFACE};
    border-bottom: 1px solid {BORDER};
}}
QMenuBar::item {{
    padding: 4px 10px;
    color: {TEXT_SECONDARY};
    background: transparent;
}}
QMenuBar::item:selected {{
    background: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
}}
QMenu {{
    background: {BG_ELEVATED};
    border: 1px solid {BORDER};
}}
QMenu::item {{
    padding: 6px 24px 6px 12px;
    color: {TEXT_PRIMARY};
}}
QMenu::item:selected {{
    background: {TEAL};
    color: white;
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 8px;
}}

/* ── Frame / group box ───────────────────────────────────────────────── */
QFrame#tool_panel {{
    background: {BG_SURFACE};
    border-right: 1px solid {BORDER};
}}
QFrame#chat_container {{
    background: {BG_BASE};
}}
QFrame#input_container {{
    background: {BG_SURFACE};
    border-top: 1px solid {BORDER};
    padding: 8px;
}}
QFrame#token_bar {{
    background: {BG_SURFACE};
    border-top: 1px solid {BORDER};
    padding: 4px 10px;
}}
QFrame#provider_bar {{
    background: {BG_SURFACE};
    border-bottom: 1px solid {BORDER};
    padding: 6px 10px;
}}

/* ── Optimization banner ─────────────────────────────────────────────── */
QFrame#optimize_banner {{
    background: #1a1200;
    border: 1px solid {AMBER};
    border-radius: 4px;
    margin: 4px 8px;
}}
QLabel#optimize_label {{
    color: {AMBER_LIGHT};
    font-size: 12px;
}}
QPushButton#dismiss_btn {{
    background: transparent;
    border: none;
    color: {TEXT_DIM};
    padding: 2px 6px;
    font-size: 11px;
}}
QPushButton#dismiss_btn:hover {{
    color: {TEXT_SECONDARY};
}}

/* ── Epistemic strip ──────────────────────────────────────────────────── */
QLabel#epi_healthy {{
    color: {GREEN};
    font-size: 11px;
    font-weight: 500;
}}
QLabel#epi_warn {{
    color: {AMBER};
    font-size: 11px;
    font-weight: 500;
}}
QLabel#epi_error {{
    color: {RED};
    font-size: 11px;
    font-weight: 500;
}}

/* ── Dialog ──────────────────────────────────────────────────────────── */
QDialog {{
    background: {BG_SURFACE};
}}
"""
