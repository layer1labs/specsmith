# WI-NEXUS-029 / REQ-109 — Smoke overlay status (2026-04-28)
The reproducible procedure in `logs.txt` is unchanged. A live capture
into `live-ok.txt` has **not** yet been performed on this workstation —
that's a manual GPU-bound step the current pre-1.0 push cannot trigger
from the agent harness.
## What's verified
- The overlay `docker-compose.smoke.yml` exists, parses, and pins the
  expected 7B Q4 model (`Qwen/Qwen2.5-Coder-7B-Instruct-GPTQ-Int4`).
- `scripts/nexus_smoke.py` runs against the production compose, gates on
  `NEXUS_LIVE=1`, and reports honest skips when the broker is offline.
## What still needs a developer to run
```
docker compose -f docker-compose.yml -f docker-compose.smoke.yml up -d
# wait ~60s for first pull, ~5s on warm cache
$env:NEXUS_LIVE = '1'
py scripts/nexus_smoke.py | Tee-Object -FilePath .specsmith/runs/WI-NEXUS-029/live-ok.txt
docker compose -f docker-compose.yml -f docker-compose.smoke.yml down
```
Once `live-ok.txt` lands and shows `{"ok": true, ...}` from a real
in-container call, REQ-109's evidence is complete. Until then the
requirement is **structurally** satisfied (overlay wired, smoke script
runnable, procedure documented) but the live payload is pending.
