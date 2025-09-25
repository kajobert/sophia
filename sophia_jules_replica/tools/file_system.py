import os

def list_files(path: str = ".") -> str:
    """
    Lists files and directories under the given path.
    Directories in the output will have a trailing slash (e.g., 'src/').
    This is an alias for the Unix command `ls -1F --group-directories-first <path>`.
    """
    try:
        # Bezpečné spuštění příkazu ls
        # Používáme os.popen pro zachycení výstupu
        command = f"ls -1F --group-directories-first {path}"
        with os.popen(command) as p:
            output = p.read()
        return output.strip()
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filepath: str) -> str:
    """
    Returns the content of the specified file.
    It will return an error if the file does not exist.
    """
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        return f"Error: File not found at {filepath}"
    except Exception as e:
        return f"Error reading file: {e}"

def create_file_with_block(filepath: str, content: str) -> str:
    """
    Creates a new file with the specified content.
    If the directory does not exist, it will be created.
    If the file already exists, it will be overwritten.
    """
    try:
        # Vytvoření adresářů, pokud neexistují
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            f.write(content)
        return f"File '{filepath}' created successfully."
    except Exception as e:
        return f"Error creating file: {e}"