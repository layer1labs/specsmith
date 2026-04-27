$Repo = "C:\Users\trist\Development\BitConcepts\specsmith"
$Agent = "nexus"
$Model = "vllm-nexus/l1-nexus"

Set-Location $Repo

Write-Host "Starting OpenCode..."
Write-Host "Repo:  $Repo"
Write-Host "Agent: $Agent"
Write-Host "Model: $Model"

opencode --agent $Agent --model $Model