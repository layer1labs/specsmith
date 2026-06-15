# Codity.ai Setup — specsmith
This checklist is for validating Codity onboarding in this repository.
## One-time setup
Windows note: `curl -fsSL https://cli.codity.ai/install.sh | sh` is Linux/macOS-only and fails in native PowerShell/Git-Bash with `unsupported OS: mingw64_nt-*`.
1. Install Codity CLI:
   ```bash
   curl -fsSL https://cli.codity.ai/install.sh | sh
   ```
   Native Windows (PowerShell) install from official release zip:
   ```powershell
   $release = Invoke-RestMethod -Uri "https://api.github.com/repos/codity-ai/codity-cli/releases/latest"
   $version = $release.tag_name.TrimStart("v")
   $asset = $release.assets | Where-Object { $_.name -eq ("codity_" + $version + "_windows_amd64.zip") } | Select-Object -First 1
   $zip = Join-Path $env:TEMP $asset.name
   $tmp = Join-Path $env:TEMP ("codity-install-" + [guid]::NewGuid().ToString())
   Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip
   Expand-Archive -Path $zip -DestinationPath $tmp -Force
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.local\bin" | Out-Null
   Copy-Item (Join-Path $tmp "codity.exe") "$env:USERPROFILE\.local\bin\codity.exe" -Force
   codity doctor
   ```
   WSL fallback (if preferred):
   ```bash
   wsl -d Ubuntu-24.04 -- bash -lc "curl -fsSL https://cli.codity.ai/install.sh | sh"
   ```
2. Authenticate:
   ```bash
   codity login
   ```
   Native PowerShell example in this repository:
   ```powershell
   cd C:\Users\trist\Development\specsmith
   codity login
   ```
   WSL fallback example in this repository:
   ```bash
   wsl -d Ubuntu-24.04 -- bash -lc "cd /mnt/c/Users/trist/Development/specsmith && codity login"
   ```
3. Initialize Codity in the repository root:
   ```bash
   codity init
   ```
   Native PowerShell example:
   ```powershell
   cd C:\Users\trist\Development\specsmith
   codity init
   ```
   WSL fallback example:
   ```bash
   wsl -d Ubuntu-24.04 -- bash -lc "cd /mnt/c/Users/trist/Development/specsmith && codity init"
   ```
4. Install/verify the Codity GitHub App for this repository:
   https://github.com/apps/codity
5. Add `CODITY_ACCESS_TOKEN` as a repository secret if your Codity configuration requires token mode.
## Validation commands
Run these from the repository root:
```bash
codity doctor
codity review --staged
codity scan --staged
codity test-gen --staged
```
Native PowerShell example:
```powershell
cd C:\Users\trist\Development\specsmith
codity doctor
```
WSL fallback example:
```bash
wsl -d Ubuntu-24.04 -- bash -lc "cd /mnt/c/Users/trist/Development/specsmith && codity doctor"
```
## Suggested usage rule
Before commits that touch production code, run:
```bash
codity review --staged
```
Treat HIGH-severity findings as blocking. MEDIUM findings should be acknowledged inline in your PR discussion.
