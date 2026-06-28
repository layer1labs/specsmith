param(
    [string]$SourceDir = ".\\data",
    [string]$DestDir = ".\\backup"
)

# Deliberate defect: does not check whether source exists.
Copy-Item -Path $SourceDir -Destination $DestDir -Recurse
Write-Output "backup complete"
