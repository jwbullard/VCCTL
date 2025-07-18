#!/bin/bash
# Derby Data Export Script
# Requires Apache Derby installation with ij tool

# Set Derby home to our downloaded installation
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VCCTL_DIR="$(dirname "$SCRIPT_DIR")"
DERBY_HOME="$VCCTL_DIR/db-derby-10.5.3.0-bin"
DERBY_CLASSPATH="$DERBY_HOME/lib/derby.jar:$DERBY_HOME/lib/derbytools.jar"

echo "Using Derby from: $DERBY_HOME"
echo "Running Derby export..."

# Create output directory
mkdir -p "$SCRIPT_DIR"

# Run the export
java -cp "$DERBY_CLASSPATH" org.apache.derby.tools.ij "$SCRIPT_DIR/derby_export_commands.sql"
