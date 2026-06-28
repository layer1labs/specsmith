param(
    [string]$AppHome = ""
)

# Deliberate mismatch defect: default differs from setup.sh and creates cross-shell drift.
if ([string]::IsNullOrWhiteSpace($AppHome)) {
    $AppHome = "C:\\bench-app"
}

New-Item -ItemType Directory -Path "$AppHome\\bin" -Force | Out-Null
Write-Output "APP_HOME=$AppHome"
