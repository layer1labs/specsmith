# SPDX-License-Identifier: MIT
"""Public project configuration schema for Specsmith."""

from specsmith._config_schema import Platform, ProjectConfig, ProjectType, _normalize_scaffold_raw

# Release/schema parity anchor. Keep synchronized with pyproject.toml.
ProjectConfig.model_fields["spec_version"].default = "0.22.5"

__all__ = ["Platform", "ProjectConfig", "ProjectType", "_normalize_scaffold_raw"]
