# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Base agent integration adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from specsmith.config import ProjectConfig


class AgentAdapter(ABC):
    """Base class for agent-specific integration file generators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Short identifier for this integration (e.g. 'agent-skill', 'claude-code')."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""

    @abstractmethod
    def generate(self, config: ProjectConfig, target: Path) -> list[Path]:
        """Generate integration files in the target project directory.

        Returns list of created file paths.
        """
