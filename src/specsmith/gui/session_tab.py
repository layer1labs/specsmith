# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""SessionTab — one tab per independent agent session."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from specsmith.gui.widgets.chat_view import ChatView
from specsmith.gui.widgets.input_bar import InputBar
from specsmith.gui.widgets.provider_bar import ProviderBar
from specsmith.gui.widgets.token_meter import TokenMeter
from specsmith.gui.widgets.tool_panel import ToolPanel
from specsmith.gui.worker import AgentWorker, GUIAgentRunner, WorkerSignals


class OptimizeBanner(QFrame):
    """Dismissible amber banner shown when context exceeds 70%."""

    dismissed = Signal()

    def __init__(self, fill_pct: float, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("optimize_banner")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(8)

        msg = (
            f"⚠ Context at {fill_pct:.0f}% — consider: "
            "type /clear to reset history · run Audit · "
            "run specsmith compress"
        )
        label = QLabel(msg)
        label.setObjectName("optimize_label")
        label.setWordWrap(True)
        layout.addWidget(label, stretch=1)

        dismiss = QPushButton("✕")
        dismiss.setObjectName("dismiss_btn")
        dismiss.setFixedSize(22, 22)
        dismiss.clicked.connect(self.dismissed.emit)
        layout.addWidget(dismiss)


class SessionTab(QWidget):
    """A complete agent session tab.

    Layout:
      ┌──────────┬───────────────────────────────────────┐
      │          │  [ProviderBar                        ] │
      │ Tool     │  [ChatView                           ] │
      │ Panel    │  [OptimizeBanner? (hidden by default)] │
      │ (160px)  │  [TokenMeter                         ] │
      │          │  [InputBar                           ] │
      └──────────┴───────────────────────────────────────┘

    Signals:
      epistemic_updated(str)  — emitted after each turn with status text
    """

    epistemic_updated = Signal(str)

    def __init__(
        self,
        project_dir: str = ".",
        provider_name: str | None = None,
        model: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._project_dir = str(Path(project_dir).resolve())
        self._provider_name = provider_name or "anthropic"
        self._model = model or ""
        self._worker: AgentWorker | None = None
        self._signals = WorkerSignals()
        self._runner: GUIAgentRunner | None = None
        self._tool_result_pending: dict[str, str] = {}  # name -> args_json

        self._setup_runner()
        self._setup_ui()
        self._connect_signals()

    # ── Runner setup ─────────────────────────────────────────────────────────

    def _setup_runner(self) -> None:
        from specsmith.agent.core import ModelTier

        self._runner = GUIAgentRunner(
            signals=self._signals,
            project_dir=self._project_dir,
            provider_name=self._provider_name,
            model=self._model or None,
            tier=ModelTier.BALANCED,
            stream=False,
        )

    # ── UI setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left: tool panel
        self._tool_panel = ToolPanel()
        main_layout.addWidget(self._tool_panel)

        # Right: everything else in a vertical stack
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Provider bar at top
        self._provider_bar = ProviderBar(
            project_dir=self._project_dir,
            provider=self._provider_name,
            model=self._model,
        )
        right_layout.addWidget(self._provider_bar)

        # Chat view (stretching)
        self._chat = ChatView()
        right_layout.addWidget(self._chat, stretch=1)

        # Optimization banner (hidden until needed)
        self._banner: OptimizeBanner | None = None
        self._banner_placeholder = QFrame()
        self._banner_placeholder.setMaximumHeight(0)
        right_layout.addWidget(self._banner_placeholder)

        # Token meter
        self._token_meter = TokenMeter()
        if self._model:
            self._token_meter.set_model(self._model)
        right_layout.addWidget(self._token_meter)

        # Input bar
        self._input_bar = InputBar()
        right_layout.addWidget(self._input_bar)

        main_layout.addWidget(right, stretch=1)

        # Welcome message
        proj_name = Path(self._project_dir).name
        self._chat.append_system(
            f"AEE Workbench — {proj_name} | "
            f"Provider: {self._provider_name} | "
            "Type a message or click a tool on the left.",
        )

    # ── Signal connections ────────────────────────────────────────────────────

    def _connect_signals(self) -> None:
        # Input → agent
        self._input_bar.send_requested.connect(self._on_send)

        # Tool panel → run specsmith tool
        self._tool_panel.tool_requested.connect(self._on_tool_requested)

        # Provider bar → update runner
        self._provider_bar.provider_changed.connect(self._on_provider_changed)
        self._provider_bar.model_changed.connect(self._on_model_changed)

        # Token meter → optimization banner
        self._token_meter.optimize_suggested.connect(self._on_optimize_suggested)

        # Worker signals → UI
        self._signals.llm_chunk.connect(self._on_llm_chunk)
        self._signals.tool_started.connect(self._on_tool_started)
        self._signals.tool_finished.connect(self._on_tool_finished)
        self._signals.tokens_updated.connect(self._on_tokens_updated)
        self._signals.turn_done.connect(self._on_turn_done)
        self._signals.error.connect(self._on_error)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_send(self, text: str) -> None:
        if self._worker and self._worker.isRunning():
            return  # Busy — ignore

        self._chat.append_user(text)
        self._input_bar.set_enabled(False)
        self._tool_panel.set_all_running(True)

        self._worker = AgentWorker(self._runner, text)  # type: ignore[arg-type]
        self._worker.start()

    def _on_tool_requested(self, tool_key: str) -> None:
        """Run a specsmith tool directly (not via LLM)."""
        from specsmith.agent.tools import build_tool_registry, get_tool_by_name

        tools = build_tool_registry(self._project_dir)
        tool = get_tool_by_name(tools, tool_key)
        if not tool or not tool.handler:
            self._chat.append_error(f"Tool '{tool_key}' not found")
            return

        self._chat.append_system(f"Running {tool_key}…")
        self._tool_panel.set_tool_status(tool_key, "running")

        # Run in a simple QThread to avoid blocking UI
        from PySide6.QtCore import QThread

        class _ToolThread(QThread):
            done = Signal(str, bool)

            def __init__(self, handler: object, **kwargs: object) -> None:
                super().__init__()
                self._handler = handler
                self._kwargs = kwargs

            def run(self) -> None:
                try:
                    result = self._handler()  # type: ignore[operator]
                    self.done.emit(result, False)
                except Exception as e:  # noqa: BLE001
                    self.done.emit(str(e), True)

        thread = _ToolThread(tool.handler)
        tool_key_ref = tool_key

        def _on_done(result: str, is_error: bool) -> None:
            self._chat.append_tool(tool_key_ref, "{}", result, is_error)
            status = "fail" if is_error else "pass"
            self._tool_panel.set_tool_status(tool_key_ref, status)

        thread.done.connect(_on_done)
        thread.start()
        self._tool_threads = getattr(self, "_tool_threads", [])
        self._tool_threads.append(thread)

    def _on_provider_changed(self, provider: str) -> None:
        self._provider_name = provider
        self._setup_runner()
        self._chat.append_system(f"Provider → {provider}")

    def _on_model_changed(self, model: str) -> None:
        self._model = model
        if self._runner:
            self._runner._model = model
            if self._runner._provider:
                self._runner._provider.model = model
        self._token_meter.set_model(model)
        self._chat.append_system(f"Model → {model}")

    def _on_llm_chunk(self, text: str) -> None:
        self._chat.append_assistant(text)

    def _on_tool_started(self, name: str, args_json: str) -> None:
        self._tool_result_pending[name] = args_json
        self._chat.append_system(f"  ⚙ {name}…")

    def _on_tool_finished(self, name: str, result: str, is_error: bool) -> None:
        args_json = self._tool_result_pending.pop(name, "{}")
        self._chat.append_tool(name, args_json, result, is_error)

        # Update tool panel if it's a governance tool
        tool_key = name.replace("-", "_")
        if not is_error:
            self._tool_panel.set_tool_status(tool_key, "pass")
        else:
            self._tool_panel.set_tool_status(tool_key, "fail")

    def _on_tokens_updated(self, in_tok: int, out_tok: int, cost: float) -> None:
        self._token_meter.update_display(in_tok, out_tok, cost)

    def _on_turn_done(self) -> None:
        self._input_bar.set_enabled(True)
        self._tool_panel.set_all_running(False)
        # Emit epistemic status update
        self.epistemic_updated.emit(self._get_epistemic_status())

    def _on_error(self, msg: str) -> None:
        self._chat.append_error(msg)

    def _on_optimize_suggested(self, fill_pct: float) -> None:
        if self._banner is not None:
            return  # Already showing
        self._banner = OptimizeBanner(fill_pct)
        self._banner.dismissed.connect(self._dismiss_banner)
        # Insert before token meter — replace placeholder
        layout: QVBoxLayout = self.layout().itemAt(1).widget().layout()  # type: ignore[union-attr]
        # Find the banner placeholder and replace it
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and item.widget() is self._banner_placeholder:
                self._banner_placeholder.setMaximumHeight(100)
                layout.insertWidget(i, self._banner)
                break

    def _dismiss_banner(self) -> None:
        if self._banner:
            self._banner.hide()
            self._banner.deleteLater()
            self._banner = None
            self._banner_placeholder.setMaximumHeight(0)

    # ── Epistemic status ──────────────────────────────────────────────────────

    def _get_epistemic_status(self) -> str:
        """Return a short epistemic status string for the status bar."""
        try:
            from specsmith.epistemic.belief import parse_requirements_as_beliefs
            from specsmith.epistemic.certainty import CertaintyEngine

            req_path = Path(self._project_dir) / "docs" / "REQUIREMENTS.md"
            if not req_path.exists():
                return "🧠 No REQUIREMENTS.md"

            artifacts = parse_requirements_as_beliefs(req_path)
            engine = CertaintyEngine(threshold=0.7)
            report = engine.run(artifacts)
            avg = sum(s.propagated_score for s in report.scores) / max(len(report.scores), 1)
            below = len(report.below_threshold)
            if below == 0:
                return f"🧠 C={avg:.2f} ✓"
            return f"🧠 C={avg:.2f} ⚠{below} low"
        except Exception:  # noqa: BLE001
            return "🧠 —"

    # ── Public API ────────────────────────────────────────────────────────────

    def tab_label(self) -> str:
        """Return a display name for this tab's header."""
        proj = Path(self._project_dir).name
        provider = self._provider_name or "?"
        return f"{proj} [{provider}]"

    def clear_history(self) -> None:
        if self._runner:
            self._runner._state.messages.clear()
        self._chat.clear_messages()
        self._token_meter.reset()
        self._chat.append_system("Conversation history cleared.")
