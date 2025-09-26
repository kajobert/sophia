import os

SANDBOX_DIR = "sandbox"
PROJECT_ROOT_PREFIX = "PROJECT_ROOT/"

def _resolve_path(user_path: str) -> str:
    """
    Safely resolves a user-provided path.
    - If the path starts with 'PROJECT_ROOT/', it resolves from the project root.
    - Otherwise, it defaults to the 'sandbox/' directory.
    - Prevents any path traversal attacks ('..').
    """
    # Normalize to prevent basic traversal
    norm_user_path = os.path.normpath(user_path)
    if os.path.isabs(norm_user_path) or norm_user_path.startswith(".."):
        raise ValueError(f"Path traversal detected. Absolute paths and '..' are not allowed. Provided: '{user_path}'")

    if user_path.startswith(PROJECT_ROOT_PREFIX):
        # Path is relative to the project root
        base_dir = "."
        path_to_join = user_path[len(PROJECT_ROOT_PREFIX):]
    else:
        # Path is relative to the sandbox
        base_dir = SANDBOX_DIR
        path_to_join = user_path
        # Create sandbox if it doesn't exist for sandbox operations
        if not os.path.exists(SANDBOX_DIR):
            os.makedirs(SANDBOX_DIR)

    # Safely join the path
    safe_path = os.path.join(base_dir, path_to_join)

    # Final check to ensure the resolved path is within the intended directory
    abs_base_dir = os.path.abspath(base_dir)
    abs_safe_path = os.path.abspath(safe_path)

    if not abs_safe_path.startswith(abs_base_dir):
        raise ValueError(f"Path traversal detected. Final path '{safe_path}' is outside the allowed directory.")

    return safe_path

def list_files(path: str = ".") -> str:
    """
    Lists files and directories under a given path.
    Defaults to the 'sandbox/' directory.
    To list files from the project root, use the 'PROJECT_ROOT/' prefix (e.g., 'PROJECT_ROOT/core').
    """
    try:
        safe_path = _resolve_path(path)
        return "\n".join(os.listdir(safe_path))
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filepath: str) -> str:
    """
    Returns the content of the specified file.
    Defaults to the 'sandbox/' directory.
    To read a file from the project root, use the 'PROJECT_ROOT/' prefix (e.g., 'PROJECT_ROOT/core/orchestrator.py').
    """
    try:
        safe_path = _resolve_path(filepath)
        with open(safe_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{filepath}'."
    except Exception as e:
        return f"Error reading file: {e}"

def write_to_file(filepath: str, content: str) -> str:
    """
    Writes content to a file.
    Defaults to the 'sandbox/' directory.
    To write to a file in the project root, use the 'PROJECT_ROOT/' prefix.
    """
    try:
        safe_path = _resolve_path(filepath)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w') as f:
            f.write(content)
        return f"File '{filepath}' written successfully."
    except Exception as e:
        return f"Error writing to file: {e}"