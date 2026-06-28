param(
    [string]$ArtifactPath = ".\\build\\output.txt"
)

# Deliberate defects:
# - missing $ErrorActionPreference = 'Stop'
# - pipeline can mask failure
Get-Content $ArtifactPath |
    Select-String "READY" |
    ForEach-Object { $_.Line.Split(" ")[0] } |
    Set-Content ".\\deploy.log"

Write-Output "deploy complete"
