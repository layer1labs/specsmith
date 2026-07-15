# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Portable Zoo Code asset lifecycle for Specsmith.

This module owns only reusable Specsmith assets and the project-local MCP merge.
Project-specific rules, commands, skills, models, and editor settings remain in
individual repositories.
"""

from __future__ import annotations

import json
import os
import shutil
from dat