import sys
import os
import json
import inspect
import asyncio
import httpx
import yaml

# --- Konfigurace a Inicializace ---

# Dynamické přidání kořenového adresáře projektu do sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.rich_printer import RichPrinter

class JulesAPIClient:
    """Spravuje komunikaci s externím Jules API."""
    def __init__(self):
        try:
            config_path = os.path.join(project_root, 'config/config.yaml')
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            self.api_key = os.getenv("JULES_API_KEY", config.get('jules_api', {}).get('api_key'))
            if not self.api_key:
                raise ValueError("JULES_API_KEY not found in environment or config.")

            self.repo_path = config.get('jules_api', {}).get('repository')
            if not self.repo_path:
                raise ValueError("Jules repository path not found in config.")

            self.base_url = "https://jules.googleapis.com/v1alpha"
            self.headers = {
                "X-Goog-Api-Key": self.api_key,
                "Content-Type": "application/json"
            }
            self.client = httpx.AsyncClient(headers=self.headers)
            RichPrinter.info("JulesAPIClient initialized successfully.")
        except Exception as e:
            RichPrinter.error(f"Failed to initialize JulesAPIClient: {e}")
            self.client = None

    async def _get_source_by_path(self):
        """Najde plný název zdroje na základě cesty v repozitáři."""
        if not self.client: return None
        try:
            response = await self.client.get(f"{self.base_url}/sources")
            response.raise_for_status()
            sources = response.json().get('sources', [])
            for source in sources:
                # Očekáváme, že 'name' bude formátu 'sources/github/OWNER/REPO'
                if self.repo_path in source.get('name', ''):
                    return source['name']
            return None
        except httpx.HTTPStatusError as e:
            RichPrinter.error(f"Error listing Jules sources: {e.response.text}")
            return None

    async def create_session(self, prompt: str):
        """Vytvoří novou session v Jules API."""
        if not self.client:
            return {"error": "Jules client not initialized."}

        source_name = await self._get_source_by_path()
        if not source_name:
            return {"error": f"Could not find a configured source matching '{self.repo_path}'."}

        try:
            payload = {"prompt": prompt, "source": source_name}
            response = await self.client.post(f"{self.base_url}/sessions", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            RichPrinter.error(f"Error creating Jules session: {e.response.text}")
            return {"error": str(e)}

# Globální instance klienta
jules_client = JulesAPIClient()

# --- Nástroje ---

async def delegate_task_to_jules(specification: str) -> dict:
    """
    Deleguje obecný úkol na Jules API.
    Vytvoří novou session a vrátí její detaily.

    Args:
        specification: Detailní popis požadovaného úkolu.
    """
    RichPrinter.info(f"Delegating task to Jules API: {specification[:80]}...")
    session = await jules_client.create_session(specification)
    return session

# --- Jádro JSON-RPC Serveru ---

def create_response(request_id, result):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "result": result})

def create_error_response(request_id, code, message):
    return json.dumps({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

async def main():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)

    tools = {
        "delegate_task_to_jules": delegate_task_to_jules,
    }

    while True:
        line = await reader.readline()
        if not line: break
        try:
            request = json.loads(line)
            request_id = request.get("id")
            method = request.get("method")
            response = None

            if method == "initialize":
                tool_definitions = [{"name": n, "description": inspect.getdoc(f) or ""} for n, f in tools.items()]
                response = create_response(request_id, {"capabilities": {"tools": tool_definitions}})
            elif method == "mcp/tool/execute":
                params = request.get("params", {})
                tool_name = params.get("name")
                if tool_name in tools:
                    kwargs = params.get("kwargs", {})
                    try:
                        result = await tools[tool_name](**kwargs)
                        response = create_response(request_id, {"result": json.dumps(result)})
                    except Exception as e:
                        response = create_error_response(request_id, -32000, f"Tool error in '{tool_name}': {e}")
                else:
                    response = create_error_response(request_id, -32601, f"Method not found: {tool_name}")
            else:
                response = create_error_response(request_id, -32601, f"Method not found: {method}")
        except Exception as e:
            response = create_error_response(None, -32603, f"Internal server error: {e}")

        if response:
            print(response)
            sys.stdout.flush()

if __name__ == "__main__":
    try:
        RichPrinter.configure_logging()
        # Načtení .env souboru pro lokální spuštění
        from dotenv import load_dotenv
        load_dotenv()
        asyncio.run(main())
    except KeyboardInterrupt:
        RichPrinter.info("Jules API server shutting down.")