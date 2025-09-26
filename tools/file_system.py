import os

SANDBOX_DIR = "sandbox"

def _resolve_sandbox_path(user_path: str) -> str:
    """
    Safely resolves a user-provided path against the sandbox directory.
    Prevents path traversal attacks.
    """
    # Create sandbox if it doesn't exist
    if not os.path.exists(SANDBOX_DIR):
        os.makedirs(SANDBOX_DIR)

    # Normalize the user path to prevent '..' traversal
    norm_user_path = os.path.normpath(user_path)
    if os.path.isabs(norm_user_path) or norm_user_path.startswith(".."):
        raise ValueError(f"Path traversal detected. Only relative paths within the sandbox are allowed. Provided: '{user_path}'")

    # Safely join the path
    safe_path = os.path.join(SANDBOX_DIR, norm_user_path)

    # Final check to ensure the resolved path is within the sandbox
    if not os.path.abspath(safe_path).startswith(os.path.abspath(SANDBOX_DIR)):
        raise ValueError(f"Path traversal detected. Final path '{safe_path}' is outside the sandbox.")

    return safe_path

def list_files(path: str = ".") -> str:
    """
    Lists files and directories under a given path within the sandbox.
    """
    try:
        safe_path = _resolve_sandbox_path(path)
        command = f"ls -1F --group-directories-first {safe_path}"
        with os.popen(command) as p:
            output = p.read()
        return output.strip()
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filepath: str) -> str:
    """
    Returns the content of the specified file within the sandbox.
    """
    try:
        safe_path = _resolve_sandbox_path(filepath)
        with open(safe_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at '{filepath}' in sandbox."
    except Exception as e:
        return f"Error reading file: {e}"

def write_to_file(filepath: str, content: str) -> str:
    """
    Writes content to a file within the sandbox.
    If the directory does not exist, it will be created.
    If the file exists, it will be overwritten.
    """
    try:
        safe_path = _resolve_sandbox_path(filepath)
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w') as f:
            f.write(content)
        return f"File '{filepath}' written successfully in sandbox."
    except Exception as e:
        return f"Error writing to file: {e}"

def create_file(filepath: str) -> str:
    """
    Creates an empty file at the specified path within the sandbox.
    """
    return write_to_file(filepath, "")