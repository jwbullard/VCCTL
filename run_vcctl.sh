#!/bin/bash
# VCCTL Application Launcher

cd "$(dirname "$0")"

# Source environment setup
source setup_env.sh > /dev/null 2>&1

# Launch VCCTL
echo "🚀 Launching VCCTL Desktop Application..."
python src/main.py "$@"