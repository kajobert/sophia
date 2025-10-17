from mcp_servers.base_mcp_server import BaseMCPServer
from tools import control

class ControlServer(BaseMCPServer):
    def __init__(self):
        super().__init__()
        self.add_tool(
            "task_complete",
            control.task_complete,
            "Signals that the current task is complete."
        )

    def get_capabilities(self):
        return {"tools": self.tools}

if __name__ == "__main__":
    server = ControlServer()
    server.run()