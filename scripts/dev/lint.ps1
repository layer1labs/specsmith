# SPDX-License-Identifier: MIT
# Copyright (c) 2026 BitConcepts, LLC. All rights reserved.
#
# Run ruff check + ruff format --check under UTF-8 so any Unicode in error
# messages or rule descriptions renders correctly.

. "$PSScriptRoot\Set-Utf8Encoding.ps1"

py -m ruff check src tests
$ruffCheckExit = $LASTEXITCODE
py -m ruff format --check src tests
$ruffFormatExit = $LASTEXITCODE

if ($ruffCheckExit -ne 0 -or $ruffFormatExit -ne 0) {
  exit ($ruffCheckExit -bor $ruffFormatExit)
}
exit 0
