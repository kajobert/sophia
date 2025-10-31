#!/bin/bash
set -e

# Ensure all development dependencies from the lock file are installed
/home/jules/.local/bin/uv pip sync requirements-dev.txt

# Run the test suite with the correct python interpreter
.venv/bin/python -m pytest
