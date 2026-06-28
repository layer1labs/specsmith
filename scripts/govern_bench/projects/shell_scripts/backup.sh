#!/usr/bin/env bash
# Deliberate defect: does not check whether source exists.

source_dir="${1:-/var/lib/bench-app}"
dest_dir="${2:-./backup}"

cp -r "$source_dir" "$dest_dir"
echo "backup complete"
