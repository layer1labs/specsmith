# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
#
# Run the rebuildable two-tier ESDB test harness (free SQLite + commercial
# ChronoStore) with the active PowerShell session reconfigured for UTF-8 so the
# pytest reporter and specsmith CLI output render correctly on Windows.
#
# Usage:
#   PS> .\scripts\dev\test-esdb-backends.ps1                 # both tiers
#   PS> .\scripts\dev\test-esdb-backends.ps1 --full          # whole suite/tier
#   PS> .\scripts\dev\test-esdb-backends.ps1 --free-only     # SQLite tier only
#   PS> .\scripts\dev\test-esdb-backends.ps1 --keep-venv -v  # args forwarded

. "$PSScriptRoot\Set-Utf8Encoding.ps1"

py "$PSScriptRoot\test_esdb_backends.py" @args
exit $LASTEXITCODE
