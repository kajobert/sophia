import os
import sys
import json
import asyncio
import inspect
import functools
from typing import List, Dict, Any

# Přidání cesty k projektu pro importy
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

from core.llm_manager import LLMManager
from core.prompt_builder import PromptBuilder
from core.rich_printer import RichPrinter

class ReflectionServer:
    """
    Tento server poskytuje nástroje pro sebereflexi agenta.
    Umožňuje agentovi analyzovat svou nedávnou historii akcí a poučit se z ní.
    """

    def __init__(self, project_root: str = "."):
        self.project_root = os.path.abspath(project_root)
        self.llm_manager = LLMManager(project_root=self.project_root)
        self.reflection_prompt_path = os.path.join(self.project_root, "prompts", "reflection_prompt.txt")

    async def reflect_on_recent_steps(self, history: List[Dict[str, Any]], last_user_input: str) -> str:
        """
        Analyzes a sequence of low-level steps to identify key insights and suggest future learnings.

        Args:
            history: The conversation and action history of the agent, as a list of (request, response) tuples.
            last_user_input: The last user input that led to this sequence of actions.

        Returns:
            A concise learning or key insight.
        """
        try:
            with open(self.reflection_prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            return "Error: Reflection prompt file not found."

        formatted_history = ""
        for i, (request, response) in enumerate(history):
            formatted_history += f"STEP {i+1}:\n"
            formatted_history += f"  THOUGHT/ACTION:\n{request}\n"
            formatted_history += f"  RESULT:\n{response}\n\n"

        prompt = system_prompt.format(
            last_user_input=last_user_input,
            history=formatted_history
        )
        model = self.llm_manager.get_llm(self.llm_manager.default_model_name)

        try:
            RichPrinter.info("Performing self-reflection on sub-task...")
            reflection, _ = await model.generate_content_async(prompt)
            RichPrinter.log_communication("Sub-task Reflection Result", reflection, style="magenta")
            return reflection.strip()
        except Exception as e:
            RichPrinter.log_error_panel("Error during reflection generation", str(e), exception=e)
            return f"Error during LLM communication in reflection: {e}"

    async def summarize_mission_learnings(self, history: str, mission_goal: str) -> str:
        """
        Analyzes the high-level history of an entire mission to generate a strategic learning.

        Args:
            history: A string representing the chronological summary of the mission's main events.
            mission_goal: The original high-level goal of the mission.

        Returns:
            A single, concise, and strategic learning from the mission.
        """
        mission_reflection_prompt_path = os.path.join(self.project_root, "prompts", "mission_reflection_prompt.txt")
        try:
            with open(mission_reflection_prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            return "Error: Mission reflection prompt file not found."

        prompt = system_prompt.format(
            mission_goal=mission_goal,
            history=history
        )
        model = self.llm_manager.get_llm(self.llm_manager.default_model_name)

        try:
            RichPrinter.info("Performing final mission reflection...")
            learning, _ = await model.generate_content_async(prompt)
            RichPrinter.log_communication("Final Mission Learning", learning, style="bold green")
            return learning.strip()
        except Exception as e:
            RichPrinter.log_error_panel("Error during final learning generation", str(e), exception=e)
            return f"Error during LLM communication in final reflection: {e}"

def create_response(request_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

async def main_server_loop():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    server_instance = ReflectionServer(project_root=".")
    tools = {name: func for name, func in inspect.getmembers(server_instance, predicate=inspect.iscoroutinefunction) if not name.startswith('_')}

    while True:
        line = await reader.readline()
        if not line:
            break

        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            response = None

            if method == "initialize":
                tool_definitions = [{"name": name, "description": inspect.getdoc(func) or "No description."} for name, func in tools.items()]
                response = create_response(request_id, {"capabilities": {"tools": tool_definitions}})

            elif method == "mcp/tool/execute":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_args = params.get("args", [])
                tool_kwargs = params.get("kwargs", {})

                if tool_name in tools:
                    tool_func = tools[tool_name]
                    try:
                        sig = inspect.signature(tool_func)
                        bound_args = sig.bind(*tool_args, **tool_kwargs)
                        bound_args.apply_defaults()

                        result = await tool_func(*bound_args.args, **bound_args.kwargs)
                        response = create_response(request_id, {"result": result})
                    except Exception as e:
                        response = create_error_response(request_id, -32000, f"Tool error for {tool_name}: {e}")
                else:
                    response = create_error_response(request_id, -32601, f"Method not found: {tool_name}")
            else:
                response = create_error_response(request_id, -32601, "Method not found")

        except Exception as e:
            response = create_error_response(None, -32603, f"Internal error: {e}")

        if response:
            print(response)
            sys.stdout.flush()

async def main_test():
    # Příklad použití pro manuální testování
    # Příklad historie
    example_history = [
        (
            '{\n  "thought": "Nejprve musím zjistit, jaké soubory jsou v kořenovém adresáři, abych se zorientoval.",\n  "tool_call": {\n    "tool_name": "list_files",\n    "args": [],\n    "kwargs": {}\n  }\n}',
            '["main.py", "requirements.txt", "tests/"]'
        ),
        (
            '{\n  "thought": "Dobře, vidím `main.py`. Chci se podívat na jeho obsah, abych pochopil, co program dělá.",\n  "tool_call": {\n    "tool_name": "read_file",\n    "args": ["main.py"],\n    "kwargs": {}\n  }\n}',
            'def hello():\n    print("Hello, world!")\n\nhello()'
        ),
        (
            '{\n  "thought": "Program je velmi jednoduchý. Úkolem je přidat funkci pro sčítání. Vytvořím novou funkci `add` a upravím volání.",\n  "tool_call": {\n    "tool_name": "replace_with_git_merge_diff",\n    "args": ["main.py"],\n    "kwargs": {\n      "search_block": "def hello():\\n    print(\\"Hello, world!\\")\\n\\nhello()",\n      "replace_block": "def add(a, b):\\n    return a + b\\n\\ndef hello():\\n    print(\\"Hello, world!\\")\\n\\nprint(f\\"2+3={add(2,3)}\\")"\n    }\n  }\n}',
            'File `main.py` updated successfully.'
        ),
        (
            '{\n  "thought": "Udělal jsem chybu. Měl jsem zavolat `hello()` a ne jen `add`. A navíc jsem nevolal `hello`. Musím to opravit.",\n  "tool_call": {\n    "tool_name": "replace_with_git_merge_diff",\n    "args": ["main.py"],\n    "kwargs": {\n      "search_block": "print(f\\\\"2+3={add(2,3)}\\\\")",\n      "replace_block": "hello()\\nprint(f\\\\"2+3={add(2,3)}\\\\")"\n    }\n  }\n}',
            'Tool execution failed: Search block not found in file.'
        )
    ]
    last_user_input = "Přidej do `main.py` funkci, která sečte dvě čísla a zavolej ji."

    server = ReflectionServer(project_root=".")
    reflection = await server.reflect_on_recent_steps(example_history, last_user_input)
    print("\n--- VÝSLEDNÉ PONAUČENÍ ---")
    print(reflection)

if __name__ == "__main__":
    if os.getenv("RUN_MANUAL_TESTS"):
        asyncio.run(main_test())
    else:
        try:
            asyncio.run(main_server_loop())
        except KeyboardInterrupt:
            pass