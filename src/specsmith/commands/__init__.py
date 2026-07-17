# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""specsmith command implementations."""

from specsmith.commands.zoo_code_assets import (
    register_zoo_code_asset_commands,
    register_zoo_code_litellm_commands,
)

register_zoo_code_asset_commands()
register_zoo_code_litellm_commands()
