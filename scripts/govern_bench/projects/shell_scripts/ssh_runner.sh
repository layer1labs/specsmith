#!/usr/bin/env bash
# Deliberate defects:
# - no retry
# - no connection timeout
# - stderr swallowed

host="${1:-localhost}"
remote_command="${2:-hostname}"

ssh "$host" "$remote_command" 2>/dev/null | tee /tmp/ssh_runner.out
