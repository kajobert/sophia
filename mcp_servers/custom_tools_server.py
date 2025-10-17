from mcp_servers.base_mcp_server import BaseMCPServer
from tools.http_client import HttpClientTools

# This server is designed to be modified by the agent itself.
# The `create_new_tool` function will add new tools here.

class CustomToolsServer(BaseMCPServer):
    def __init__(self):
        super().__init__()
        http_client_tools = HttpClientTools()
        self.add_tool(
            "send_http_request",
            http_client_tools.send_http_request,
            "Sends an HTTP request (GET, POST, etc.) to a URL and returns the status code and JSON response."
        )

    def get_capabilities(self):
        return {"tools": self.tools}

if __name__ == "__main__":
    server = CustomToolsServer()
    server.run()