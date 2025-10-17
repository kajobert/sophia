from mcp_servers.base_mcp_server import BaseMCPServer
from tools import debug

class DebugServer(BaseMCPServer):
    def __init__(self):
        super().__init__()
        self.add_tool(
            "show_last_output",
            debug.show_last_output,
            "Shows the last output from the agent."
        )

    def get_capabilities(self):
        return {"tools": self.tools}

if __name__ == "__main__":
    server = DebugServer()
    server.run()