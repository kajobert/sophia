import sys
import os
# Adjust the path to import from the root 'core' and 'tools' directories
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_servers.base_mcp_server import BaseMCPServer
from tools.management import ManagementTools
from core.mcp_client import MCPClient

class ManagementServer(BaseMCPServer):
    def __init__(self):
        super().__init__()
        # Note: This is a bit of a hack. The management server needs a reference
        # to the MCPClient to reload other servers. In a real-world scenario,
        # this might be handled via a more robust service discovery or IPC mechanism.
        # For this MVP, we create a temporary client instance.
        # mcp_client = MCPClient(project_root=".") # THIS CAUSES INFINITE RECURSION
        # mcp_client.servers = self.get_server_processes() # Hacky way to share server process list

        # We will pass None for now to break the loop. This will be fixed later.
        management_tools = ManagementTools(None)
        self.add_tool(
            "create_new_tool",
            management_tools.create_new_tool,
            "Adds a new tool to the agent's capabilities by writing Python code to a server file."
        )
        self.add_tool(
            "reload_tools",
            management_tools.reload_tools,
            "Reloads the tools from a specified MCP server by restarting it."
        )

    def get_capabilities(self):
        return {"tools": self.tools}

    def get_server_processes(self):
        # This is a placeholder. In a real system, this would be more sophisticated.
        # It's needed because the management tool needs to know about other servers to restart them.
        return {}

if __name__ == "__main__":
    server = ManagementServer()
    server.run()