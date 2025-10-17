import os

SANDBOX_DIR = "sandbox"
PROJECT_ROOT_PREFIX = "PROJECT_ROOT/"

def _resolve_path(user_path: str, project_root: str = None) -> str:
    """
    Safely resolves a user-provided path against a project root.

    - If `project_root` is not provided, it defaults to the current working directory.
    - Paths starting with `PROJECT_ROOT/` are resolved from the `project_root`.
    - All other paths are resolved relative to the `sandbox/` directory within the `project_root`.
    - It actively prevents path traversal ('..') and absolute paths.
    """
    if project_root is None:
        project_root = os.getcwd()

    # Normalize user_path to prevent basic traversal attacks like '..'
    norm_user_path = os.path.normpath(user_path)

    if os.path.isabs(norm_user_path) or norm_user_path.startswith(".."):
        raise ValueError(f"Path traversal detected. Absolute paths and '..' are not allowed. Provided: '{user_path}'")

    # Determine the base directory for the operation
    if norm_user_path.startswith(PROJECT_ROOT_PREFIX):
        base_dir = os.path.abspath(project_root)
        path_to_join = norm_user_path[len(PROJECT_ROOT_PREFIX):]
    else:
        # Default to the sandbox directory
        sandbox_path = os.path.join(project_root, SANDBOX_DIR)
        base_dir = os.path.abspath(sandbox_path)
        path_to_join = norm_user_path

        # Create the sandbox directory if it doesn't exist
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

    # Safely join the base directory and the user-provided path
    safe_path = os.path.abspath(os.path.join(base_dir, path_to_join))

    # Security check: Ensure the resolved path is within the allowed base directory
    if not safe_path.startswith(base_dir):
        # This check is crucial to prevent users from escaping the intended directory
        raise ValueError(f"Path traversal detected. Final path '{user_path}' resolves outside the allowed directory.")

    return safe_path

def list_files(path: str = ".", project_root: str = None) -> str:
    """
    Lists files and directories under a given path.
    Defaults to the 'sandbox/' directory.
    To list files from the project root, use the 'PROJECT_ROOT/' prefix (e.g., 'PROJECT_ROOT/core').
    """
    try:
        safe_path = _resolve_path(path, project_root)
        return "\n".join(os.listdir(safe_path))
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filepath: str, line_limit: int = None, project_root: str = None) -> str:
    """
    Returns the content of the specified file.
    Defaults to the 'sandbox/' directory.
    To read a file from the project root, use the 'PROJECT_ROOT/' prefix.
    :param filepath: The path to the file to read.
    :param line_limit: Optional. If provided, only this many lines will be read from the start of the file.
    """
    try:
        safe_path = _resolve_path(filepath, project_root)
        with open(safe_path, 'r', encoding='utf-8') as f:
            # If line_limit is not a positive integer, read the whole file.
            if not isinstance(line_limit, int) or line_limit <= 0:
                return f.read()

            lines = []
            for _ in range(line_limit):
                try:
                    lines.append(next(f))
                except StopIteration:
                    # Reached end of file before reaching the limit
                    return "".join(lines)

            content = "".join(lines)

            # Check if there's at least one more line to confirm truncation
            try:
                next(f)
                content.rstrip('\\n')
                content += f"\\n... (soubor zkrácen na {line_limit} řádků) ..."
            except StopIteration:
                # The file has exactly line_limit lines, no truncation message needed
                pass

            return content
    except FileNotFoundError:
        return f"Error: File not found at '{filepath}'."
    except Exception as e:
        return f"Error reading file: {e}"

def overwrite_file_with_block(filepath: str, content: str, project_root: str = None) -> str:
    """
    Overwrites an existing file with new content. If the file does not exist, it is created.
    This special tool is designed to work with multi-line content blocks.
    Defaults to the 'sandbox/' directory. To operate on a file in the project root, use the 'PROJECT_ROOT/' prefix.
    """
    try:
        safe_path = _resolve_path(filepath, project_root)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w') as f:
            f.write(content)
        return f"File '{filepath}' written successfully."
    except Exception as e:
        return f"Error writing to file: {e}"

# Alias for `create_file_with_block` as specified in JULES.md special tools
create_file_with_block = overwrite_file_with_block

def create_file(filepath: str, project_root: str = None) -> str:
    """
    Creates an empty file at the specified path.
    Defaults to the 'sandbox/' directory.
    To create a file in the project root, use the 'PROJECT_ROOT/' prefix.
    """
    return overwrite_file_with_block(filepath, "", project_root)

def create_new_tool(tool_filename: str, code: str) -> str:
    """
    Creates a new tool file with the given code in the 'sandbox/custom_tools/' directory.
    The filename must end with '.py'.
    This is the primary method for the agent to create new, reusable capabilities for itself.
    """
    if not tool_filename.endswith(".py"):
        return "Error: Tool filename must end with .py"
    if "/" in tool_filename or "\\" in tool_filename:
        return "Error: Tool filename cannot contain path separators. It must be a simple filename."

    # Ensure the custom_tools directory exists
    custom_tools_dir = os.path.join(SANDBOX_DIR, "custom_tools")
    if not os.path.exists(custom_tools_dir):
        os.makedirs(custom_tools_dir)

    # Safely construct the final path
    safe_path = os.path.join(custom_tools_dir, tool_filename)

    try:
        with open(safe_path, 'w') as f:
            f.write(code)
        return f"New tool '{tool_filename}' created successfully in 'sandbox/custom_tools/'."
    except Exception as e:
        return f"Error creating new tool: {e}"


def delete_file(filepath: str, project_root: str = None) -> str:
    """
    Deletes the specified file.
    Defaults to the 'sandbox/' directory.
    To delete a file from the project root, use the 'PROJECT_ROOT/' prefix.
    """
    try:
        safe_path = _resolve_path(filepath, project_root)
        os.remove(safe_path)
        return f"File '{filepath}' deleted successfully."
    except FileNotFoundError:
        return f"Error: File not found at '{filepath}'."
    except Exception as e:
        return f"Error deleting file: {e}"


def rename_file(filepath: str, new_filepath: str, project_root: str = None) -> str:
    """
    Renames or moves a file.
    Defaults to the 'sandbox/' directory for both paths.
    To use paths from the project root, use the 'PROJECT_ROOT/' prefix.
    """
    try:
        safe_old_path = _resolve_path(filepath, project_root)
        safe_new_path = _resolve_path(new_filepath, project_root)
        os.rename(safe_old_path, safe_new_path)
        return f"File '{filepath}' renamed to '{new_filepath}' successfully."
    except FileNotFoundError:
        return f"Error: Source file not found at '{filepath}'."
    except Exception as e:
        return f"Error renaming file: {e}"


def replace_with_git_merge_diff(filepath: str, search_block: str, replace_block: str, project_root: str = None) -> str:
    """
    Performs a targeted search-and-replace within a file.
    This special tool takes a search block and a replace block to perform the update.
    The search block must match a part of the file content exactly.
    """
    try:
        original_content = read_file(filepath, project_root=project_root)
        if original_content.startswith("Error:"):
            return original_content

        if search_block not in original_content:
            return f"Error: SEARCH block not found in file '{filepath}'. Please ensure the search block is an exact match."

        new_content = original_content.replace(search_block, replace_block, 1)

        write_result = overwrite_file_with_block(filepath, new_content, project_root=project_root)
        if write_result.startswith("Error"):
            return write_result
        else:
            return f"File '{filepath}' updated successfully via replace/diff."
    except Exception as e:
        return f"Error applying replace/diff: {e}"