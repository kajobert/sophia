#!/bin/bash
set -e

# Ensure all dependencies from the lock file are installed
/home/jules/.local/bin/uv pip sync requirements-dev.txt

# Run the benchmark command with the correct python interpreter
.venv/bin/python run.py "List all available tools. Then, write the list of tools to a file named 'tools.txt'. After that, read the content of the 'tools.txt' file. Next, use the LLMTool to summarize the content of the file. Finally, delete the 'tools.txt' file."
