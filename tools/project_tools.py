import os
import ast
from typing import List

class SkeletonVisitor(ast.NodeVisitor):
    """
    An AST visitor that extracts the skeleton of a Python file, including docstrings.
    It collects class and function definitions with correct indentation.
    """
    def __init__(self):
        self.skeleton = []
        self.indent_level = 0

    def _get_args(self, node: ast.FunctionDef) -> str:
        """Formats the arguments of a function definition."""
        args = [a.arg for a in node.args.args]
        return ", ".join(args)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Handles visiting a class definition node."""
        indent = "    " * self.indent_level
        self.skeleton.append(f"{indent}class {node.name}:")

        docstring = ast.get_docstring(node)
        doc_indent = "    " * (self.indent_level + 1)
        if docstring:
            self.skeleton.append(f'{doc_indent}"""{docstring}"""')

        self.indent_level += 1
        # Visit only direct children to process methods
        for child in node.body:
            if isinstance(child, ast.FunctionDef):
                self.visit_FunctionDef(child)
        self.indent_level -= 1
        if self.indent_level == 0: # Add a blank line for separation after top-level classes
            self.skeleton.append("")

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Handles visiting a function or method definition node."""
        indent = "    " * self.indent_level
        args = self._get_args(node)

        docstring = ast.get_docstring(node)
        if docstring:
            self.skeleton.append(f"{indent}def {node.name}({args}):")
            doc_indent = "    " * (self.indent_level + 1)
            self.skeleton.append(f'{doc_indent}"""{docstring}"""')
        else:
            # Keep original behavior for functions without docstrings
            self.skeleton.append(f"{indent}def {node.name}({args}): ...")

def _extract_python_skeleton(filepath: str) -> str:
    """
    Parses a Python file and extracts a skeleton of its structure (classes and functions)
    using a robust AST NodeVisitor.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as source:
            tree = ast.parse(source.read())

        visitor = SkeletonVisitor()
        # Manually iterate over top-level nodes to control visiting order
        # and ensure methods are processed within their class context.
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                visitor.visit(node)

        return "\n".join(visitor.skeleton).strip()
    except Exception as e:
        return f"# Could not parse {os.path.basename(filepath)}: {e}"

def get_project_summary(start_path: str = ".") -> str:
    """
    Generates a summary of the project structure, including skeletons of Python files.

    This tool recursively walks through the project directory from the `start_path`,
    ignoring common unnecessary files/directories. For each Python file, it extracts
    class and function definitions to provide a quick overview of its purpose.

    :param start_path: The directory to start the summary from, relative to the project root. Defaults to the project root (`.`).
    :return: A string containing the formatted project summary.
    """
    path_to_walk = start_path

    ignore_dirs = {
        '__pycache__', '.venv', '.git', 'logs', 'node_modules',
        'build', 'dist', 'site', 'docs'
    }
    ignore_files = {'.DS_Store', 'requirements.txt'}

    summary = []
    for root, dirs, files in os.walk(path_to_walk, topdown=True):
        # Exclude specified directories from traversal
        dirs[:] = [d for d in dirs if d not in ignore_dirs]

        # Calculate indentation level based on directory depth
        relative_path = os.path.relpath(root, path_to_walk)
        if relative_path == ".":
            level = 0
        else:
            level = relative_path.count(os.sep) + 1

        indent = ' ' * 4 * level

        if relative_path != ".":
            summary.append(f"{indent[:-4]}{os.path.basename(root)}/")

        sub_indent = ' ' * 4 * (level)
        for f in sorted(files):
            if f in ignore_files:
                continue

            filepath = os.path.join(root, f)
            summary.append(f"{sub_indent}- {f}")
            if f.endswith(".py"):
                skeleton = _extract_python_skeleton(filepath)
                if skeleton:
                    indented_skeleton = "\n".join([f"{sub_indent}  # {line}" for line in skeleton.split('\n')])
                    summary.append(indented_skeleton)

    return "\n".join(summary)