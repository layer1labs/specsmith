# SPDX-License-Identifier: MIT
"""Public project configuration schema for Specsmith."""

from specsmith._config_schema import *  # noqa: F403
from specsmith._config_schema import ProjectConfig

# Release/schema parity anchor. Keep synchronized with pyproject.toml.
spec_version: str = Field(default="0.22.4", description="Spec version to scaffold from")  # type: ignore[name-defined]
ProjectConfig.model_fields["spec_version"].default = "0.22.4"
