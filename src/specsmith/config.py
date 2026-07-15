# SPDX-License-Identifier: MIT
"""Public project configuration schema for Specsmith."""

from pydantic import Field

from specsmith._config_schema import Platform, ProjectConfig, ProjectType, _normalize_scaffold_raw

# Release/schema parity anchor. Keep synchronized with pyproject.toml.
spec_version: str = Field(default="0.22.4", description="Spec version to scaffold from")
ProjectConfig.model_fields["spec_version"].default = "0.22.4"

__all__ = ["Platform", "ProjectConfig", "ProjectType", "_normalize_scaffold_raw"]
