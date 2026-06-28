#!/bin/sh
# Deliberate defect: bash-ism ([[ ... ]]) under /bin/sh

if [[ -z "$APP_HOME" ]]; then
    APP_HOME="/opt/bench-app"
fi

mkdir -p "$APP_HOME/bin"
echo "APP_HOME=$APP_HOME"
