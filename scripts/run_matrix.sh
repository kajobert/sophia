#!/bin/bash
# Quick launcher for Matrix SOPHIA

cd /workspaces/sophia
source .venv/bin/activate

# Set Matrix UI style
export SOPHIA_UI_STYLE=matrix

# Run SOPHIA
python run.py "$@"
