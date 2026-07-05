# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""ChatView — HTML-rendered chat message display."""

from __future__ import annotations

import html
import time

from PySide6.QtWidgets import QSizePolicy, QTextBrowser, QVBoxLayout, QWidget

from specsmith.gui import theme


class ChatView(QWidget):
    """Scrollable chat view with styled HTML message bubbles.

    Roles:
      user      — right-aligned teal bubble
      assistant — left-aligned off-white bubble with AEE byline
      tool      — amber collapsible block (name + result)
      system    — dim italic status line
      error     — red inline error
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._browser = QTextBrowser()
        self._browser.setOpenLinks(False)
        self._browser.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._browser.setObjectName("chat_browser")
        layout.addWidget(self._browser)

        # Inject base CSS into the document
        self._browser.document().setDefaultStyleSheet(self._doc_css())

    # ── Public API ──────────────────────────────────────────────────────────

    def append_user(self, text: str) -> None:
        """Append a user message (right-aligned teal bubble)."""
        ts = time.strftime("%H:%M")
        safe = html.escape(text).replace("\n", "<br>")
        self._append_html(
            f"""<div class="msg user">
              <div class="bubble user-bubble">{safe}</div>
              <div class="meta">{ts}</div>
            </div>""",
        )

    def append_assistant(self, text: str) -> None:
        """Append an assistant response (left-aligned card)."""
        ts = time.strftime("%H:%M")
        safe = html.escape(text).replace("\n", "<br>")
        self._append_html(
            f"""<div class="msg assistant">
              <div class="role-tag">🧠 AEE Agent</div>
              <div class="bubble asst-bubble">{safe}</div>
              <div class="meta">{ts}</div>
            </div>""",
        )

    def append_assistant_chunk(self, text: str) -> None:
        """Append text to the last assistant bubble (for streaming simulation)."""
        safe = html.escape(text).replace("\n", "<br>")
        # Insert before the last </div></div> closing of the current bubble
        cursor = self._browser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._browser.setTextCursor(cursor)
        self._browser.insertHtml(safe)
        self._scroll_to_bottom()

    def append_tool(self, name: str, args_json: str, result: str, is_error: bool = False) -> None:
        """Append a tool call block (collapsible amber block)."""
        status_icon = "❌" if is_error else "✅"
        border_col = theme.RED if is_error else theme.AMBER
        result_safe = html.escape(result[:800]).replace("\n", "<br>")
        if len(result) > 800:
            result_safe += "<em>…(truncated)</em>"
        style = f"border-left: 3px solid {border_col}; padding-left:8px;"
        self._append_html(
            f"""<div class="msg tool">
              <div class="tool-header" style="{style}">
                <span class="tool-icon">{status_icon}</span>
                <span class="tool-name">{html.escape(name)}</span>
              </div>
              <div class="tool-result">{result_safe}</div>
            </div>""",
        )

    def append_system(self, text: str) -> None:
        """Append a dim system/status message."""
        safe = html.escape(text)
        self._append_html(f'<div class="msg system"><em>{safe}</em></div>')

    def append_error(self, text: str) -> None:
        """Append a red inline error message."""
        safe = html.escape(text)
        self._append_html(f'<div class="msg error">⚠ {safe}</div>')

    def clear_messages(self) -> None:
        """Clear all messages (keep styling)."""
        self._browser.clear()

    # ── Private ─────────────────────────────────────────────────────────────

    def _append_html(self, html_str: str) -> None:
        cursor = self._browser.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._browser.setTextCursor(cursor)
        self._browser.insertHtml(html_str + "<br>")
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        sb = self._browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    @staticmethod
    def _doc_css() -> str:
        bg = theme.BG_BASE
        surface = theme.BG_SURFACE
        elevated = theme.BG_ELEVATED
        text = theme.TEXT_PRIMARY
        muted = theme.TEXT_SECONDARY
        dim = theme.TEXT_DIM
        teal = theme.TEAL
        amber = theme.AMBER_LIGHT
        red = theme.RED
        user_bg = theme.MSG_USER_BG
        tool_bg = theme.MSG_TOOL_BG

        return f"""
            body {{ background: {bg}; color: {text}; margin: 0; padding: 8px; }}
            .msg {{ margin: 6px 0; }}
            .user {{ text-align: right; }}
            .user-bubble {{
                display: inline-block;
                background: {user_bg};
                color: {text};
                border-radius: 12px 12px 2px 12px;
                padding: 10px 14px;
                max-width: 72%;
                word-wrap: break-word;
                font-size: 13px;
                line-height: 1.5;
                text-align: left;
            }}
            .assistant {{ text-align: left; }}
            .role-tag {{
                font-size: 10px;
                color: {teal};
                font-weight: 600;
                letter-spacing: 0.5px;
                margin-bottom: 3px;
                text-transform: uppercase;
            }}
            .asst-bubble {{
                display: inline-block;
                background: {surface};
                color: {text};
                border-radius: 2px 12px 12px 12px;
                padding: 10px 14px;
                max-width: 90%;
                word-wrap: break-word;
                font-size: 13px;
                line-height: 1.5;
            }}
            .meta {{
                font-size: 10px;
                color: {dim};
                margin-top: 2px;
                padding: 0 2px;
            }}
            .tool {{
                background: {tool_bg};
                border-radius: 6px;
                padding: 8px 12px;
                margin: 4px 0;
                font-size: 12px;
            }}
            .tool-header {{
                margin-bottom: 4px;
            }}
            .tool-icon {{ margin-right: 6px; }}
            .tool-name {{
                font-weight: 600;
                color: {amber};
                font-family: monospace;
            }}
            .tool-result {{
                color: {muted};
                font-family: monospace;
                font-size: 11px;
                background: {elevated};
                padding: 6px 8px;
                border-radius: 4px;
                max-height: 120px;
                overflow: hidden;
                white-space: pre-wrap;
                word-break: break-all;
            }}
            .system {{
                color: {dim};
                font-size: 11px;
                text-align: center;
                padding: 4px;
            }}
            .error {{
                color: {red};
                font-size: 12px;
                padding: 4px 8px;
                background: #1a0505;
                border-radius: 4px;
                border-left: 3px solid {red};
            }}
            code {{
                font-family: "Cascadia Code", "Fira Code", "Courier New", monospace;
                background: {elevated};
                padding: 1px 4px;
                border-radius: 3px;
                font-size: 12px;
                color: {teal};
            }}
        """
