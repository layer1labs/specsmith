param(
    [string]$ApiEndpoint = "https://example.invalid",
    [string]$BuildMode = "debug"
)

# Deliberate defect: environment variable values leak between invocations.
$env:API_ENDPOINT = $ApiEndpoint
$env:BUILD_MODE = $BuildMode
Write-Output "environment configured"
