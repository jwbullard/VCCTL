#!/bin/bash
# VCCTL Application Launcher

cd "$(dirname "$0")"

# Remove anaconda from PATH first
export PATH=$(echo "$PATH" | sed 's|/Users/jwbullard/anaconda3/bin:||g')

# Source environment setup
source setup_env.sh > /dev/null 2>&1

# Launch VCCTL with explicit Python path
echo "🚀 Launching VCCTL Desktop Application..."
/usr/bin/python3 src/main.py "$@"