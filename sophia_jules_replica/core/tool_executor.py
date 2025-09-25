import os
import sys
import importlib
import inspect
import re

class ToolExecutor:
    """
    Třída zodpovědná za registraci, parsování a vykonávání nástrojů.
    """

    def __init__(self, project_root: str = "."):
        """
        Inicializuje ToolExecutor a registruje dostupné nástroje.
        """
        self.project_root = project_root
        self.tools_directory = os.path.join(self.project_root, "tools")
        self.tools = {}
        self._register_tools()

    def _register_tools(self):
        """
        Dynamicky prohledá adresář 'tools/', naimportuje všechny moduly
        a zaregistruje všechny funkce jako dostupné nástroje.
        """
        if self.project_root not in sys.path:
            sys.path.insert(0, self.project_root)

        try:
            for filename in os.listdir(self.tools_directory):
                if filename.endswith(".py") and not filename.startswith("__"):
                    module_name = f"tools.{filename[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for name, func in inspect.getmembers(module, inspect.isfunction):
                            if not name.startswith("_"):
                                self.tools[name] = func
                                print(f"INFO: Nástroj '{name}' byl úspěšně zaregistrován.")
                    except ImportError as e:
                        print(f"CHYBA: Nepodařilo se naimportovat modul nástrojů '{module_name}': {e}")
        finally:
            if self.project_root in sys.path:
                sys.path.remove(self.project_root)

    def get_tool_descriptions(self) -> str:
        """
        Vrátí formátovaný řetězec s popisy všech registrovaných nástrojů.
        """
        if not self.tools:
            return "Žádné nástroje nejsou k dispozici."

        descriptions = []
        for name, func in self.tools.items():
            # Použijeme dedent pro hezké formátování docstringů
            docstring = inspect.getdoc(func) or "Tento nástroj nemá popis."
            descriptions.append(f"- `{name}`: {docstring.strip()}")

        return "\n".join(descriptions)

    def execute_tool(self, tool_call_string: str) -> str:
        """
        Zparsuje řetězec s voláním nástroje a vykoná ho.
        Rozlišuje mezi standardní syntaxí `tool(args)` a DSL `tool\nargs`.
        Vrací výsledek jako textový řetězec.
        """
        tool_call_string = tool_call_string.strip()

        match = re.match(r"(\w+)\((.*)\)$", tool_call_string, re.DOTALL)

        tool_name = None
        args = []

        if match:
            tool_name = match.group(1)
            args_string = match.group(2).strip()
            if args_string:
                args = [arg.strip().strip("'\"") for arg in args_string.split(',')]
            else:
                args = []
        else:
            lines = tool_call_string.split('\n')
            tool_name = lines[0].strip()
            if tool_name == 'create_file_with_block' and len(lines) >= 2:
                filepath = lines[1]
                content = '\n'.join(lines[2:])
                args = [filepath, content]
            else:
                args = [line.strip() for line in lines[1:]]

        if tool_name in self.tools:
            func = self.tools[tool_name]
            try:
                return str(func(*args))
            except TypeError as e:
                return f"Error executing tool '{tool_name}': Incorrect arguments. Details: {e}"
            except Exception as e:
                return f"An unexpected error occurred while executing tool '{tool_name}': {e}"
        else:
            return f"Error: Tool '{tool_name}' not found."