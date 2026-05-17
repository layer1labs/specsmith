# SPDX-License-Identifier: MIT
"""SSH and remote development skills."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="ssh-workflow",
        name="SSH — key management, config, tunnels, ProxyJump, agent",
        description=(
            "SSH best practices: key generation and management, ~/.ssh/config, "
            "port forwarding, ProxyJump chains, SSH agent, and hardening."
        ),
        domain=SkillDomain.SSH,
        tags=["ssh", "keys", "tunnel", "proxyjump", "agent", "scp",
              "rsync", "remote", "linux", "security"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["ssh"],
        body="""\
# SSH Workflow Skill

## Key generation (best practices)
```bash
# Ed25519 (recommended — fast, secure, small key)
ssh-keygen -t ed25519 -C "user@machine-2024" -f ~/.ssh/id_ed25519_work

# RSA 4096 (for legacy systems that don't support Ed25519)
ssh-keygen -t rsa -b 4096 -C "user@machine" -f ~/.ssh/id_rsa_legacy

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_ed25519_work.pub user@server
# Or manually:
cat ~/.ssh/id_ed25519_work.pub | ssh user@server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

## ~/.ssh/config
```
# ~/.ssh/config
Host bastion
  HostName 203.0.113.10
  User ec2-user
  IdentityFile ~/.ssh/id_ed25519_work
  ServerAliveInterval 60
  ServerAliveCountMax 3

Host prod-server
  HostName 10.0.1.50          # private IP
  User ubuntu
  ProxyJump bastion           # jump through bastion
  IdentityFile ~/.ssh/id_ed25519_work

Host *
  AddKeysToAgent yes          # auto-add to ssh-agent on first use
  IdentitiesOnly yes          # only use specified key
  StrictHostKeyChecking ask
  HashKnownHosts yes          # hash hostnames in known_hosts
```

## SSH agent (avoid passphrase re-entry)
```bash
# Linux / macOS
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519_work

# macOS (Keychain integration)
ssh-add --apple-use-keychain ~/.ssh/id_ed25519_work

# Windows (PowerShell — ensure OpenSSH service is running)
Set-Service -Name ssh-agent -StartupType Automatic
Start-Service ssh-agent
ssh-add $env:USERPROFILE\\.ssh\\id_ed25519_work
```

## Port forwarding
```bash
# Local forward: access remote service locally
ssh -L 5432:localhost:5432 prod-server        # PostgreSQL
ssh -L 8080:internal-server:80 bastion        # HTTP through bastion
ssh -L 3306:db.internal:3306 prod-server -N   # -N: no command (just tunnel)

# Remote forward: expose local port on remote server
ssh -R 9000:localhost:3000 prod-server         # expose local dev server

# Dynamic SOCKS proxy
ssh -D 1080 bastion -N                         # use as SOCKS5 proxy
# Configure browser to use 127.0.0.1:1080 as SOCKS5
```

## File transfer
```bash
scp -r local-dir/ user@server:~/remote-dir/          # copy
scp -i ~/.ssh/id_ed25519_work file.txt user@server:~/ # with explicit key
rsync -avz --progress local-dir/ user@server:~/remote-dir/
rsync -avz --delete --exclude='.git/' \\               # sync with deletion
    local-dir/ user@server:~/remote-dir/
```

## SSH hardening (server-side /etc/ssh/sshd_config)
```
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AllowUsers deployer ubuntu
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
```
```bash
sudo sshd -t && sudo systemctl restart sshd   # validate config + restart
```

## Common pitfalls
- Permission errors: `~/.ssh/` must be `700`, `authorized_keys` must be `600`.
- Known hosts conflict: `ssh-keygen -R hostname` to remove stale entry.
- ProxyJump on Windows: requires OpenSSH (built-in since Windows 10 1803).
- Agent forwarding (`-A`): only use to trusted hosts — it exposes your agent.
""",
    ),
    SkillEntry(
        slug="wsl2-dev",
        name="WSL2 — Windows Subsystem for Linux 2, interop, networking",
        description=(
            "WSL2 development environment: distro management, Windows/Linux "
            "interop, file system access, networking, systemd, and VS Code integration."
        ),
        domain=SkillDomain.SSH,
        tags=["wsl2", "windows", "linux", "ubuntu", "interop",
              "vscode", "systemd", "networking", "docker"],
        platforms=["windows"],
        prerequisites=["wsl"],
        body="""\
# WSL2 Development Skill

## Installation and management
```powershell
# Install WSL2 + Ubuntu (Windows 10 2004+ / Windows 11)
wsl --install                                    # installs Ubuntu by default
wsl --install -d Debian                          # specific distro
wsl --list --online                              # available distros
wsl --list --verbose                             # installed distros + version

# Version and distro management
wsl --set-default-version 2                      # always use WSL2
wsl --set-version Ubuntu 2                       # upgrade existing to WSL2
wsl --terminate Ubuntu                           # stop running distro
wsl --shutdown                                   # stop all WSL instances
wsl --export Ubuntu ubuntu-backup.tar            # backup
wsl --import MyUbuntu C:\\WSL\\MyUbuntu ubuntu-backup.tar  # restore
```

## Windows ↔ Linux interop
```bash
# Access Windows files from Linux
cd /mnt/c/Users/myname/Projects/   # Windows C: drive
ls /mnt/d/                          # D: drive

# Access Linux files from Windows
# Explorer: \\\\wsl$\\Ubuntu\\home\\user\\
# Or: \\\\wsl.localhost\\Ubuntu\\

# Run Linux commands from PowerShell
wsl ls -la ~/
wsl -- bash -c "cd /tmp && tar xf /mnt/c/Users/me/archive.tar.gz"

# Run Windows executables from Linux
notepad.exe README.md
explorer.exe .              # open current dir in Explorer
cmd.exe /c "dir"
/mnt/c/Windows/System32/clip.exe < file.txt   # copy to clipboard
```

## Performance: keep project files in Linux filesystem
```bash
# FAST: /home/user/projects/ (native Linux fs, ~same speed as bare Linux)
# SLOW: /mnt/c/Users/... (WSL2 translates every syscall across VMs)

# Rule: if your tools run in Linux, keep files in Linux
# If you must access from Windows apps: use /mnt/c/ but expect ~3-10x slowdown
```

## Networking
```bash
# Get WSL2 IP (changes on restart)
hostname -I | awk '{print $1}'
# Windows host IP from WSL2
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'

# Access WSL2 port from Windows: localhost:8000 works (since Windows 11 / WSL 2.0)
# For older: use the WSL2 IP directly

# Fixed IP with .wslconfig (Windows %USERPROFILE%\\.wslconfig)
[wsl2]
memory=8GB
processors=4
swap=2GB
localhostForwarding=true   # forward 127.0.0.1 to WSL2 (default on)
```

## Systemd (WSL2 2.0+)
```bash
# Enable systemd (add to /etc/wsl.conf inside WSL):
[boot]
systemd=true

wsl --shutdown && wsl  # restart to apply

# Now you can use systemd normally:
sudo systemctl enable myservice
sudo systemctl start myservice
sudo journalctl -u myservice -f
```

## VS Code integration
```bash
# From WSL2 terminal:
code .                          # opens VS Code with Remote-WSL extension
code ~/.bashrc                  # edit file in VS Code
# Extensions install into WSL2 separately from Windows
# Settings: { "remote.WSL.useShellEnvironment": true }
```

## Docker Desktop integration
```bash
# Enable Docker Desktop → Settings → Resources → WSL Integration → Ubuntu
docker ps          # works directly in WSL2 terminal
docker compose up  # full Docker Compose works
```

## Common pitfalls
- `wsl --shutdown` needed after `.wslconfig` changes.
- File permissions: Windows-created files may have wrong mode (umask issues).
- Line endings: configure `git config core.autocrlf input` in WSL2.
- GPU: WSL2 supports CUDA via `wsl --install --no-distribution` + NVIDIA driver.
""",
    ),
    SkillEntry(
        slug="remote-dev",
        name="Remote Development — VS Code tunnels, rsync, tmux, mosh",
        description=(
            "Remote development patterns: VS Code Remote SSH/Tunnel, "
            "rsync file sync, tmux session persistence, and mosh for unreliable connections."
        ),
        domain=SkillDomain.SSH,
        tags=["remote-dev", "vscode", "ssh", "rsync", "tmux",
              "mosh", "tunnel", "remote", "development"],
        platforms=["windows", "linux", "macos"],
        prerequisites=["ssh", "rsync"],
        body="""\
# Remote Development Skill

## VS Code Remote SSH
```bash
# 1. Install "Remote - SSH" extension in VS Code
# 2. Add to ~/.ssh/config:
Host dev-server
  HostName 203.0.113.50
  User ubuntu
  IdentityFile ~/.ssh/id_ed25519_work

# 3. VS Code: Ctrl+Shift+P → "Remote-SSH: Connect to Host" → dev-server
# Extensions install remotely; file editing is native speed
```

## VS Code Tunnel (no port 22 needed — works through firewall)
```bash
# On remote server:
curl -Lk 'https://code.visualstudio.com/sha/download?build=stable&os=cli-alpine-x64' \
    --output vscode_cli.tar.gz
tar xf vscode_cli.tar.gz && ./code tunnel
# Follow auth prompts; get tunnel URL

# Persist as service:
./code tunnel service install
./code tunnel service start
```

## tmux session management (survive disconnects)
```bash
# Start named session
tmux new -s work

# Common key bindings (prefix = Ctrl+B):
#   Ctrl+B c   → new window
#   Ctrl+B ,   → rename window
#   Ctrl+B %   → split vertical
#   Ctrl+B "   → split horizontal
#   Ctrl+B d   → detach (session survives)
#   Ctrl+B [   → scroll mode (q to exit)

# Reattach after reconnect
tmux attach -t work
tmux ls                           # list sessions

# Share session with colleague
tmux new-session -s shared
tmux attach-session -t shared -r  # read-only join
```

## ~/.tmux.conf best practices
```
# 256 colors
set -g default-terminal "screen-256color"
# Mouse support
set -g mouse on
# Increase history
set -g history-limit 50000
# Status bar
set -g status-right "#(hostname) | %Y-%m-%d %H:%M"
# vi mode
setw -g mode-keys vi
```

## rsync file synchronization
```bash
# Push local → remote (dry-run first)
rsync -avz --dry-run --exclude='.git/' --exclude='node_modules/' \
    ./project/ user@server:~/project/
# Remove --dry-run when satisfied

# Pull remote → local (backup)
rsync -avz user@server:~/project/ ./project-backup/

# Continuous sync (fswatch + rsync — macOS/Linux)
fswatch -o ./src | xargs -n1 -I{} rsync -avz ./src/ user@server:~/project/src/

# Watch + sync script for development:
while inotifywait -r -e modify,create,delete ./src; do
    rsync -avz --delete ./src/ user@server:~/project/src/
done
```

## mosh (Mobile Shell — handles packet loss and roaming)
```bash
# Install on both client and server: sudo apt install mosh
mosh user@server          # connects via SSH then switches to UDP
mosh --ssh="ssh -i ~/.ssh/id_ed25519" user@server
# Same key bindings as SSH; survives wifi changes, sleeps, high-latency links
```

## Common pitfalls
- VS Code Remote extensions must be re-installed into remote (per-host extension storage).
- tmux scrollback: `Ctrl+B [` then PgUp/PgDn; exit with `q`.
- rsync trailing slash: `src/` syncs contents; `src` syncs directory itself.
- mosh requires UDP ports 60000-61000 open on server firewall.
""",
    ),
]
