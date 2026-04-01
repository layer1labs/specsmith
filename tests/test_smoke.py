# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
"""Smoke tests for specsmith."""

from specsmith import __version__
from specsmith.config import Platform, ProjectConfig, ProjectType


def test_version():
    """Version string is set."""


assert __version__ == "0.1.0a4"


def test_config_defaults():
    """ProjectConfig creates with minimal input."""
    cfg = ProjectConfig(name="test-project", type=ProjectType.CLI_PYTHON)
    assert cfg.package_name == "test_project"
    assert cfg.type_label == "CLI tool (Python)"
    assert cfg.section_ref == "17.3"
    assert Platform.WINDOWS in cfg.platforms
    assert cfg.exec_shims is True
    assert cfg.git_init is True


def test_config_needs_shell_wrappers():
    """Hardware project types need shell wrappers."""
    fpga = ProjectConfig(name="my-fpga", type=ProjectType.FPGA_RTL)
    assert fpga.needs_shell_wrappers is True

    cli = ProjectConfig(name="my-cli", type=ProjectType.CLI_PYTHON)
    assert cli.needs_shell_wrappers is False
