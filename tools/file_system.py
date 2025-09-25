import os

def list_files(path: str = ".") -> str:
    """
    Lists files and directories under the given path.
    """
    try:
        command = f"ls -1F --group-directories-first {path}"
        with os.popen(command) as p:
            output = p.read()
        return output.strip()
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filepath: str) -> str:
    """
    Returns the content of the specified file.
    """
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except Exception as e:
        return f"Error reading file: {e}"