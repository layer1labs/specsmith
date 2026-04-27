#opencode --agent build --model ollama/qwen3:14b

# start-opencode-heavy.ps1

$Repo = "C:\Users\trist\Development\BitConcepts\specsmith"
$Model = "ollama/gpt-oss:20b-64k"
$Agent = "build-heavy"

Set-Location $Repo

Write-Host "Starting OpenCode (Heavy Mode)..."
Write-Host "Repo:  $Repo"
Write-Host "Agent: $Agent"
Write-Host "Model: $Model"

opencode --agent $Agent --model $Model