# Sophia V2 - Developer Guide

This guide provides instructions and best practices for developers contributing to the Sophia V2 project.

## 1. Getting Started

### 1.1. Prerequisites
Ensure you have the following installed on your system:
- **Python 3.12 or higher:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Git:** [https://git-scm.com/downloads](https://git-scm.com/downloads)
- **`uv`:** A fast Python package installer. Install it via `pip`:
  ```bash
  pip install uv
  ```

### 1.2. Environment Setup
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/kajobert/sophia.git
    cd sophia
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```
    On Windows, use `.venv\Scripts\activate`.

3.  **Install dependencies:**
    Install both the core application dependencies and the development dependencies.
    ```bash
    uv pip install -r requirements.in -r requirements-dev.in
    ```

4.  **Set up pre-commit hooks:**
    This will ensure your code is formatted and linted before you commit.
    ```bash
    pre-commit install
    ```

## 2. Development Workflow

### 2.1. Branching Strategy
All new features and bug fixes should be developed in a feature branch.
- Create a new branch from `develop`:
  ```bash
  git checkout develop
  git pull origin develop
  git checkout -b feature/your-feature-name
  ```
- Once your work is complete and tested, create a pull request to merge your feature branch back into `develop`.

### 2.2. Making Changes
When you make changes to the code, ensure you also update any relevant documentation. This is a strict requirement for all contributions.

## 3. Testing

The project uses `pytest` for testing.

### 3.1. Running Tests
To run the entire test suite, execute the following command from the project root:
```bash
PYTHONPATH=. .venv/bin/python -m pytest
```

### 3.2. Writing New Tests
- All new code must be accompanied by corresponding tests.
- For a new plugin `plugins/my_plugin.py`, you must create a test file `tests/plugins/test_my_plugin.py`.
- Tests should be self-contained and not rely on external services or API keys. Use mocking where appropriate.

## 4. Code Quality

We use `pre-commit` to enforce code quality standards. The configured tools are:
- **`black`:** For consistent code formatting.
- **`ruff`:** For linting and style checks.
- **`mypy`:** For static type checking.

These checks will run automatically on every commit. You can also run them manually:
```bash
pre-commit run --all-files
```

## 5. Creating a New Plugin

The architecture is designed to be extensible through plugins.

### 5.1. The `BasePlugin` Contract
All plugins must inherit from `plugins.base_plugin.BasePlugin` and implement the following:
- `name` (property): A unique string identifier for the plugin.
- `plugin_type` (property): One of the `PluginType` enums (`INTERFACE`, `TOOL`, `MEMORY`).
- `version` (property): The version of the plugin.
- `setup(self, config: dict)`: A method called by the Kernel on startup. Use this to load configuration, initialize resources, and set up routes if it's a web-based plugin.
- `async execute(self, context: SharedContext)`: The main entry point for the plugin, which is called by the Kernel during the appropriate phase of the `consciousness_loop`.

### 5.2. The `SharedContext` Object
The `SharedContext` is a data object passed between plugins. It allows them to share state and data within a single cycle of the `consciousness_loop`. Key attributes include:
- `user_input`: The input received from an interface plugin.
- `history`: The conversation history.
- `payload`: A dictionary for plugins to store and retrieve data.

### 5.3. Exposing Functions as Tools for the AI
Any plugin (regardless of its `PluginType`) can expose its methods to be callable by the AI. This is achieved through a "duck typing" convention. The Kernel will automatically discover any plugin that implements the `get_tool_definitions` method.

To make a plugin's methods available as tools:
1.  **Implement `get_tool_definitions(self) -> List[Dict[str, Any]]`:** Add this method to your plugin.
2.  **Define a Pydantic Schema for Arguments:** For each function you want to expose, create a `pydantic.BaseModel` that defines its arguments. This is crucial for the Kernel's "Validation & Repair Loop" to function correctly.
3.  **Return the Tool Schema:** The `get_tool_definitions` method must return a list of dictionaries, where each dictionary conforms to the [OpenAPI JSON Schema specification](https://swagger.io/specification/) that the AI model understands.

**Example: Exposing a `list_directory` function in `FileSystemTool`**
```python
# In plugins/tool_file_system.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any

# 1. Define the Pydantic schema for the function's arguments
class ListDirectoryArgs(BaseModel):
    path: str = Field(..., description="The path to the directory to list.")

class FileSystemTool(BasePlugin):
    # ... other plugin methods ...

    def list_directory(self, path: str) -> List[str]:
        # ... implementation ...
        return ["file1.txt", "file2.txt"]

    # 2. Implement the discovery method
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "Lists the contents of a directory within the sandbox.",
                    # 3. Reference the Pydantic schema
                    "parameters": ListDirectoryArgs.model_json_schema(),
                },
            }
        ]
```
By following this convention, the Kernel's planner and execution engine will automatically be able to see, validate, and call your plugin's methods.

## 6. Available Tool Plugins

This section provides an overview of the available `TOOL` plugins that can be used by cognitive plugins.

### 6.1. File System Tool (`tool_file_system`)

-   **Purpose:** Provides safe, sandboxed access to the local file system.
-   **Configuration (`config/settings.yaml`):**
    ```yaml
    tool_file_system:
      sandbox_dir: "sandbox"
    ```
-   **Methods:**
    -   `read_file(path: str) -> str`: Reads the content of a file within the sandbox.
    -   `write_file(path: str, content: str) -> str`: Writes content to a file within the sandbox.
    -   `list_directory(path: str) -> List[str]`: Lists the contents of a directory within the sandbox.

## 7. Submitting Changes

1.  **Ensure all tests pass:** Run `PYTHONPATH=. .venv/bin/python -m pytest`.
2.  **Ensure all quality checks pass:** Run `pre-commit run --all-files`.
3.  **Update documentation:** Make sure any changes to the codebase are reflected in the relevant documentation files.
4.  **Create a Pull Request:** Push your feature branch to the remote repository and open a pull request against the `develop` branch.
5.  **Code Review:** Your pull request will be reviewed by another developer. Address any feedback before it is merged.
