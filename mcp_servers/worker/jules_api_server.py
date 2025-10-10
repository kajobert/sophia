import os
import sys
import httpx
import yaml
import json
import asyncio
import inspect
from typing import Optional

# Add project root to the Python path
project_root_for_import = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root_for_import not in sys.path:
    sys.path.insert(0, project_root_for_import)

# --- Configuration Loading Function ---
def load_config():
    """Loads the application configuration from the YAML file."""
    config_path = os.path.join("config/config.yaml")
    if not os.path.exists(config_path):
        config_path = os.path.join(os.path.dirname(__file__), '../../config/config.yaml')
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}

# --- Tool Functions ---

async def list_jules_sources() -> str:
    """
    Lists all available sources (e.g., GitHub repositories) that Jules can work with. This is the first step before delegating a task.
    """
    config = load_config()
    jules_api_config = config.get("jules_api", {})
    base_url = jules_api_config.get("base_url", "https://jules.googleapis.com/v1alpha")
    timeout = jules_api_config.get("list_sources_timeout", 30.0)

    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        return json.dumps({"error": "JULES_API_KEY is not configured."})

    headers = {"X-Goog-Api-Key": jules_api_key}
    url = f"{base_url}/sources"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to list Jules sources: {e}"})

async def delegate_task_to_jules(
    prompt: str,
    source: str,
    starting_branch: str,
    title: Optional[str] = None,
    requirePlanApproval: bool = False,
    automationMode: Optional[str] = None
) -> str:
    """
    Deleguje komplexní úkol na externího specializovaného agenta Jules.

    Tento nástroj vytvoří novou pracovní session v Jules API. Je klíčové správně specifikovat všechny parametry.

    Args:
        prompt (str): Detailní popis úkolu pro Jules. Musí být jasný a jednoznačný.
        source (str): Povinný identifikátor zdrojového repozitáře, kde má Jules pracovat. Získáš ho zavoláním nástroje `list_jules_sources`.
        starting_branch (str): Povinný název větve v repozitáři, ze které má Jules vycházet.
        title (Optional[str]): Volitelný krátký název pro úkol (např. "Implementace přihlašovací stránky").
        requirePlanApproval (Optional[bool]): Volitelný příznak. Pokud je `True`, Jules nejprve vytvoří plán a počká na jeho schválení, než začne s implementací.
        automationMode (Optional[str]): Volitelný režim automatizace. Možné hodnoty jsou "full" nebo "step-by-step".

    Returns:
        str: JSON string s odpovědí od Jules API, obsahující ID nově vytvořené session.
    """
    config = load_config()
    jules_api_config = config.get("jules_api", {})
    base_url = jules_api_config.get("base_url", "https://jules.googleapis.com/v1alpha")
    timeout = jules_api_config.get("delegate_task_timeout", 45.0)

    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        return json.dumps({"error": "JULES_API_KEY is not configured."})

    headers = {"X-Goog-Api-Key": jules_api_key, "Content-Type": "application/json"}

    payload = {
        "prompt": prompt,
        "sourceContext": {
            "source": source,
            "githubRepoContext": {"startingBranch": starting_branch}
        },
        "requirePlanApproval": requirePlanApproval
    }
    if title: payload["title"] = title
    if automationMode: payload["automationMode"] = automationMode

    url = f"{base_url}/sessions"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to delegate task to Jules: {e}"})

async def get_jules_task_status(task_id: str) -> str:
    """
    Fetches the status of a task from the Jules API.
    """
    config = load_config()
    jules_api_config = config.get("jules_api", {})
    base_url = jules_api_config.get("base_url", "https://jules.googleapis.com/v1alpha")
    timeout = jules_api_config.get("get_status_timeout", 30.0)

    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        return json.dumps({"error": "JULES_API_KEY is not configured."})

    headers = {"X-Goog-Api-Key": jules_api_key}
    url = f"{base_url}/sessions/{task_id}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to get Jules task status: {e}"})

async def get_jules_task_result(task_id: str) -> str:
    """
    Downloads the result of a completed task from the Jules API.
    """
    config = load_config()
    jules_api_config = config.get("jules_api", {})
    base_url = jules_api_config.get("base_url", "https://jules.googleapis.com/v1alpha")
    timeout = jules_api_config.get("get_result_timeout", 60.0)

    jules_api_key = os.getenv("JULES_API_KEY")
    if not jules_api_key:
        return json.dumps({"error": "JULES_API_KEY is not configured."})

    headers = {"X-Goog-Api-Key": jules_api_key}
    url = f"{base_url}/sessions/{task_id}/result"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to get Jules task result: {e}"})

# --- Tool Metadata with Examples ---
TOOLS = {
    "list_jules_sources": {
        "func": list_jules_sources,
        "examples": [
            {
                "use_case": "Zjistit, s jakými repozitáři může Jules pracovat, než mu deleguji úkol.",
                "code": '{"tool_name": "list_jules_sources", "kwargs": {}}'
            }
        ]
    },
    "delegate_task_to_jules": {
        "func": delegate_task_to_jules,
        "examples": [
            {
                "use_case": "Delegovat úkol na agenta Jules, aby implementoval novou funkci v konkrétním repozitáři, který jsem zjistil pomocí 'list_jules_sources'.",
                "code": '{"tool_name": "delegate_task_to_jules", "kwargs": {"prompt": "Implement a new login page using React", "source": "sources/github/your_org/your_repo", "starting_branch": "main", "title": "Implement Login Page"}}'
            },
            {
                "use_case": "Delegovat komplexní refaktoring a vyžadovat manuální schválení plánu agenta, než začne pracovat.",
                "code": '{"tool_name": "delegate_task_to_jules", "kwargs": {"prompt": "Refactor the database schema for performance", "source": "sources/github/your_org/your_repo", "starting_branch": "develop", "requirePlanApproval": true}}'
            }
        ]
    },
    "get_jules_task_status": {
        "func": get_jules_task_status,
        "examples": [
            {
                "use_case": "Zkontrolovat stav úkolu, který byl dříve delegován na Jules.",
                "code": '{"tool_name": "get_jules_task_status", "kwargs": {"task_id": "session-id-12345"}}'
            }
        ]
    },
    "get_jules_task_result": {
        "func": get_jules_task_result,
        "examples": [
            {
                "use_case": "Stáhnout výsledek dokončeného úkolu od Jules.",
                "code": '{"tool_name": "get_jules_task_result", "kwargs": {"task_id": "session-id-12345"}}'
            }
        ]
    }
}

# --- MCP Server Boilerplate ---
def create_response(request_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

async def main():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    while True:
        line = await reader.readline()
        if not line: break
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            if method == "initialize":
                tool_definitions = [
                    {
                        "name": name,
                        "description": inspect.getdoc(meta["func"]) or "",
                        "examples": meta.get("examples", [])
                    }
                    for name, meta in TOOLS.items()
                ]
                response = create_response(request_id, {"capabilities": {"tools": tool_definitions}})
            elif method == "mcp/tool/execute":
                params = request.get("params", {})
                tool_name = params.get("name")
                if tool_name in TOOLS:
                    tool_func = TOOLS[tool_name]["func"]
                    tool_args = params.get("args", [])
                    tool_kwargs = params.get("kwargs", {})

                    try:
                        # Inteligentní spojení args a kwargs do jednoho volání
                        sig = inspect.signature(tool_func)
                        bound_args = sig.bind(*tool_args, **tool_kwargs)
                        bound_args.apply_defaults()

                        result = await tool_func(*bound_args.args, **bound_args.kwargs)
                        response = create_response(request_id, {"result": result})
                    except TypeError as e:
                        response = create_error_response(request_id, -32602, f"Invalid params for {tool_name}: {e}")
                else:
                    response = create_error_response(request_id, -32601, f"Method not found: {tool_name}")
            else:
                response = create_error_response(request_id, -32601, "Method not found")
        except Exception as e:
            response = create_error_response(None, -32603, f"Internal error: {e}")

        if response:
            print(response)
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())