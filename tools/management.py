import os

class ManagementTools:
    """
    Tools for the agent to manage its own capabilities.
    """
    def __init__(self, mcp_client):
        self.mcp_client = mcp_client

    async def create_new_tool(self, tool_code: str, server_file: str = "mcp_servers/custom_tools_server.py"):
        """
        Adds a new tool to the agent's capabilities by writing Python code to a server file.
        The server must then be reloaded for the tool to become active.

        :param tool_code: A string containing the Python code for the new tool.
                          This code should define a new method and add it to the server's tools.
                          Example:
                          '''
                          def new_tool_function(self, arg1: str):
                              '''A description of the new tool.'''
                              return f"New tool received: {arg1}"

                          self.add_tool("new_tool_name", self.new_tool_function, "description")
                          '''
        :param server_file: The path to the MCP server file to modify.
        """
        if not os.path.exists(server_file):
            return f"Error: Server file not found at {server_file}"

        try:
            with open(server_file, "a") as f:
                f.write("\n\n" + tool_code)
            return f"Successfully added new tool code to {server_file}. Please reload the server to activate it."
        except Exception as e:
            return f"Error writing to server file: {e}"

    async def reload_tools(self, server_name: str):
        """
        Reloads the tools from a specified MCP server by restarting it.

        :param server_name: The name of the server to reload (e.g., 'custom_tools_server.py').
        """
        if server_name not in self.mcp_client.servers:
            return f"Error: Server '{server_name}' not found."

        try:
            await self.mcp_client.restart_server(server_name)
            return f"Server '{server_name}' reloaded successfully. New tools should be available."
        except Exception as e:
            return f"Error reloading server '{server_name}': {e}"