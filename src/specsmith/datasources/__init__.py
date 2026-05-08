# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Built-in data source clients for specsmith.

All clients use stdlib ``urllib`` only — no external dependencies.
Each module exposes:
  search()          — progressive disclosure (minimal/balanced/complete)
  get()             — individual record lookup
  test_connection() — health/status check
"""

from specsmith.datasources.base import DataSource, DataSourceError

__all__ = ["DataSource", "DataSourceError"]
