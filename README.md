[//]: # (Cognitive Memory System section)

## Cognitive Memory System

The `memory/` directory contains the modules for the agent's multi-layered memory system.

-   **`memory_manager.py`**: The main interface for interacting with the agent's memory. It will orchestrate calls to both short-term and long-term memory modules.
-   **`short_term_memory.py`**: Manages the agent's episodic memory, keeping a chronological log of recent events and conversations.
-   **`long_term_memory.py`**: Manages the agent's semantic memory. It will store processed insights and learned knowledge in a vector database for efficient retrieval.
# Sophia

Lightweight project to demo autonomous agents built with CrewAI.

Setup

1. Create a `.env` file in the repository root with required API keys:

```
SERPER_API_KEY="your_serper_api_key"
GEMINI_API_KEY="your_gemini_api_key"
```

2. Install Python deps:

```bash
pip install -r requirements.txt
```

Run

```bash
python main.py
```

Notes

- Do not commit `.env` to the repo.
- The project includes tools for web search (`SerperDevTool`) and local file reading (`FileReadTool`, `DirectoryReadTool`).

Optional: If you prefer pinned versions and the `sophia_v2` layout, a copy of the original `requirements.txt` is available in `sophia_v2/requirements.txt`.

## Custom Tools

### CustomFileWriteTool

This tool provides a way to write text content to a specified file.  It handles file creation, overwriting, and directory creation as needed.

**Purpose:**
Writes text to a file, creating directories and handling potential errors.

**How to Use:**
The tool takes two arguments:

* `file_path` (str): The relative path to the file where the text should be written.
* `text` (str): The text content to be written to the file.

It returns a confirmation message indicating success or failure, including any error messages.
