#!/usr/bin/env bash
# Deliberate defect: exports leak into parent shell/session in task workflows.

export API_ENDPOINT="${API_ENDPOINT:-https://example.invalid}"
export BUILD_MODE="${BUILD_MODE:-debug}"
echo "environment configured"
