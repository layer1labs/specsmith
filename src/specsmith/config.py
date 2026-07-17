# SPDX-License-Identifier: MIT
"""Public project configuration schema for Specsmith."""

from specsmith._config_schema import Platform, ProjectConfig, ProjectType, _normalize_scaffold_raw
from specsmith import GOVERNANCE_VERSION

# Release/schema parity anchor. Keep synchronized with pyproject.toml.
ProjectConfig.model_fields["spec_version"].default = GOVERNANCE_VERSION

__all__ = ["Platform", "ProjectConfig", "ProjectType", "_normalize_scaffold_raw"]
