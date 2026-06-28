#!/usr/bin/env bash
# Deliberate defects:
# - missing set -e / pipefail
# - pipeline failures can be swallowed

artifact_path="${1:-build/output.txt}"

cat "$artifact_path" | grep "READY" | awk '{print $1}' > /tmp/deploy_target.txt
cp /tmp/deploy_target.txt ./deploy.log
echo "deploy complete"
