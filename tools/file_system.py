import os
import ast
import json

def _resolve_path(user_path: str) -> str:
    """
    Safely resolves a user-provided path relative to the project root.
    Prevents any path traversal attacks ('..').
    """
    # Prevent absolute paths immediately.
    if os.path.isabs(user_path):
        raise ValueError(f"Path traversal detected. Absolute paths are not allowed. Provided: '{user_path}'")

    # Normalize path to resolve things like 'a/b/../c' -> 'a/c'.
    # This is done on the user_path which is confirmed to be relative.
    norm_user_path = os.path.normpath(user_path)

    # After normalization, check for '..' components again.
    # This catches attempts like '../' or 'a/../../b' which normpath might not fully resolve
    # if the path doesn't exist.
    if '..' in norm_user_path.split(os.path.sep):
        raise ValueError(f"Path traversal detected. '..' is not allowed. Provided: '{user_path}'")

    # All paths are relative to the project root.
    base_dir = os.path.abspath(".")

    # Safely join the path.
    safe_path = os.path.join(base_dir, norm_user_path)

    # Final, most important check: ensure the fully resolved path is within the project directory.
    # This is the ultimate safeguard against any clever traversal techniques.
    if not os.path.abspath(safe_path).startswith(base_dir):
        raise ValueError(f"Path traversal detected. Final path '{safe_path}' is outside the allowed project directory.")

    return safe_path

def list_files(path: str = ".") -> str:
    """
    Lists files and directories under a given path, relative to the project root.
    For example, `list_files("core")` will list files in the 'core' directory.
    Defaults to the project root.
    """
    try:
        safe_path = _resolve_path(path)
        # Check if the path exists and is a directory
        if not os.path.isdir(safe_path):
            return f"Error: Path '{path}' is not a valid directory."
        return "\n".join(os.listdir(safe_path))
    except Exception as e:
        return f"Error listing files: {e}"

def read_file(filepath: str, line_limit: int = 100) -> str:
    """
    Vrátí obsah zadaného souboru jako JSON objekt.
    Umožňuje omezit počet načtených řádků a informuje o celkové velikosti souboru.

    :param filepath: Cesta k souboru (např. 'tools/file_system.py').
    :param line_limit: Maximální počet řádků k načtení. Výchozí je 100.
    :return: JSON string s klíči 'content', 'total_lines', 'lines_read', 'is_truncated'.
    """
    try:
        safe_path = _resolve_path(filepath)
        with open(safe_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        total_lines = len(all_lines)
        is_truncated = total_lines > line_limit

        # Omezení počtu řádků, pokud je to nutné
        content_lines = all_lines[:line_limit]
        content = "".join(content_lines)
        lines_read = len(content_lines)

        response = {
            "content": content,
            "total_lines": total_lines,
            "lines_read": lines_read,
            "is_truncated": is_truncated
        }

        return json.dumps(response, ensure_ascii=False, indent=2)

    except FileNotFoundError:
        return json.dumps({"error": f"File not found at '{filepath}'"})
    except Exception as e:
        return json.dumps({"error": f"Error reading file: {e}"})

def overwrite_file_with_block(filepath: str, content: str) -> str:
    """
    Overwrites or creates a file with new content, relative to the project root.
    This special tool is designed to work with multi-line content blocks.
    """
    try:
        safe_path = _resolve_path(filepath)
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        with open(safe_path, 'w') as f:
            f.write(content)
        return f"File '{filepath}' written successfully."
    except Exception as e:
        return f"Error writing to file: {e}"

# Alias for `create_file_with_block` as specified in JULES.md special tools
create_file_with_block = overwrite_file_with_block

def create_file(filepath: str) -> str:
    """
    Creates an empty file at the specified path, relative to the project root.
    """
    return overwrite_file_with_block(filepath, "")

def delete_file(filepath: str) -> str:
    """
    Deletes the specified file, relative to the project root.
    """
    try:
        safe_path = _resolve_path(filepath)
        os.remove(safe_path)
        return f"File '{filepath}' deleted successfully."
    except FileNotFoundError:
        return f"Error: File not found at '{filepath}'."
    except Exception as e:
        return f"Error deleting file: {e}"


def rename_file(filepath: str, new_filepath: str) -> str:
    """
    Renames or moves a file, with paths relative to the project root.
    """
    try:
        safe_old_path = _resolve_path(filepath)
        safe_new_path = _resolve_path(new_filepath)
        os.rename(safe_old_path, safe_new_path)
        return f"File '{filepath}' renamed to '{new_filepath}' successfully."
    except FileNotFoundError:
        return f"Error: Source file not found at '{filepath}'."
    except Exception as e:
        return f"Error renaming file: {e}"


def replace_with_git_merge_diff(filepath: str, search_block: str, replace_block: str) -> str:
    """
    Performs a targeted search-and-replace within a file, relative to the project root.
    This special tool takes a search block and a replace block to perform the update.
    The search block must match a part of the file content exactly.
    """
    try:
        # read_file now returns a JSON string, so we need to parse it.
        original_content_json = read_file(filepath)

        try:
            original_content_data = json.loads(original_content_json)
        except json.JSONDecodeError:
            return f"Error: Could not decode JSON from read_file for '{filepath}'. Returned: {original_content_json}"

        if "error" in original_content_data:
            return f"Error reading file for replacement: {original_content_data['error']}"

        original_content = original_content_data.get("content", "")

        if search_block not in original_content:
            return f"Error: SEARCH block not found in file '{filepath}'. Please ensure the search block is an exact match."

        new_content = original_content.replace(search_block, replace_block, 1)

        write_result = overwrite_file_with_block(filepath, new_content)
        if write_result.startswith("Error"):
            return write_result
        else:
            return f"File '{filepath}' updated successfully via replace/diff."
    except Exception as e:
        return f"Error applying replace/diff: {e}"


def read_file_section(filepath: str, identifier: str) -> str:
    """
    Reads a specific section (a function or a class) from a Python file, relative to the project root.
    This is useful for focusing on a specific piece of code without loading the entire file.

    :param filepath: The path to the Python file (e.g., 'tools/file_system.py').
    :param identifier: The name of the function or class to extract.
    :return: A string containing the source code of the specified section, or an error message.
    """
    try:
        safe_path = _resolve_path(filepath)
        with open(safe_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = ast.parse(source_code)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == identifier:
                # If the node is a function with decorators, adjust the start line
                # to include the decorators in the source segment.
                if isinstance(node, ast.FunctionDef) and node.decorator_list:
                    first_decorator = node.decorator_list[0]
                    # Create a new dummy node or adjust coordinates to span the whole block
                    # In this case, we can simply get the source from the first decorator
                    # to the end of the function.
                    # Note: ast.get_source_segment is sensitive to the node's line numbers.
                    # A robust way is to find the start of the first decorator.
                    start_lineno = first_decorator.lineno

                    # Manually find the source segment from the original code
                    lines = source_code.splitlines(True)
                    # The end line number is available from the node
                    end_lineno = node.end_lineno

                    # Extract lines from start of decorator to end of function
                    return "".join(lines[start_lineno-1:end_lineno])

                # For classes or functions without decorators, the default behavior is correct
                return ast.get_source_segment(source_code, node)

        return f"Error: Identifier '{identifier}' not found in file '{filepath}'."

    except FileNotFoundError:
        return f"Error: File not found at '{filepath}'."
    except SyntaxError as e:
        return f"Error: Could not parse Python file '{filepath}'. Invalid syntax: {e}"
    except Exception as e:
        return f"Error reading file section: {e}"
