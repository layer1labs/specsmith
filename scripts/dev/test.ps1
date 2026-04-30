# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
#
# Run pytest with the active PowerShell session reconfigured for UTF-8 so
# the test reporter, ruff output, and any Unicode in test fixtures render
# correctly on Windows.
#
# Usage:
#   PS> .\scripts\dev\test.ps1                # py -m pytest
#   PS> .\scripts\dev\test.ps1 -k history     # forwards args verbatim
#   PS> .\scripts\dev\test.ps1 tests/test_warp_parity_followup.py -v

. "$PSScriptRoot\Set-Utf8Encoding.ps1"

py -m pytest @args
exit $LASTEXITCODE
