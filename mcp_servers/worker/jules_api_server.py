import os
import sys
import httpx
import yaml
import json
import asyncio
import inspect
import functools
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
    Lists all available sources (e.g., GitHub repositories) that Jules can work with.
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
    requirePlanApproval: Optional[bool] = None,
    automationMode: Optional[str] = None
) -> str:
    """
    Creates a new session in the Jules API to delegate a task. Allows specifying optional parameters like title, requirePlanApproval, and automationMode.
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
        }
    }
    if title: payload["title"] = title
    if requirePlanApproval is not None: payload["requirePlanApproval"] = requirePlanApproval
    if automationMode: payload["automationMode"] = automationMode

    url = f"{base_url}/sessions"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": f"Failed to delegate task to Jules: {e}"})

# --- MCP Server Boilerplate ---

def create_response(request_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

async def main():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    tools = {
        "list_jules_sources": list_jules_sources,
        "delegate_task_to_jules": delegate_task_to_jules,
    }

    while True:
        line = await reader.readline()
        if not line: break
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            if method == "initialize":
                tool_definitions = [{"name": name, "description": inspect.getdoc(func) or ""} for name, func in tools.items()]
                response = create_response(request_id, {"capabilities": {"tools": tool_definitions}})
            elif method == "mcp/tool/execute":
                params = request.get("params", {})
                tool_name = params.get("name")
                tool_kwargs = params.get("kwargs", {})
                if tool_name in tools:
                    tool_func = tools[tool_name]
                    result = await tool_func(**tool_kwargs)
                    response = create_response(request_id, {"result": result})
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