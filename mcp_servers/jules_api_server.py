import asyncio
from mcp_servers.base_server import BaseServer

class JulesApiServer(BaseServer):
    """
    Tento server simuluje rozhraní pro budoucí integraci s externím Jules API.
    Poskytuje nástroje, které agentovi umožní delegovat komplexní úkoly.
    """

    def __init__(self, host, port, project_root):
        super().__init__(host, port, project_root)
        self.add_tool(self.get_jules_api_capabilities)
        self.add_tool(self.delegate_coding_to_jules)
        self.add_tool(self.delegate_testing_to_jules)

    async def get_jules_api_capabilities(self) -> str:
        """
        Vrátí popis schopností, které jsou dostupné přes Jules API.
        Agent může tento nástroj použít k rozhodnutí, zda je delegování vhodné.
        """
        capabilities = {
            "description": "Jules API je specializovaná služba pro provádění komplexních softwarových úkolů.",
            "available_delegations": {
                "delegate_coding_to_jules": "Deleguje napsání nebo úpravu kódu podle specifikace.",
                "delegate_testing_to_jules": "Deleguje vytvoření a spuštění testů pro ověření funkčnosti."
            },
            "api_status": "operational"
        }
        return self.tool_response("get_jules_api_capabilities", capabilities)

    async def delegate_coding_to_jules(self, specification: str) -> str:
        """
        Deleguje úkol na napsání nebo úpravu kódu na Jules API.

        Args:
            specification: Detailní popis požadované funkcionality nebo změny.

        Returns:
            Potvrzení o přijetí úkolu a (v budoucnu) ID pro sledování.
        """
        # V této fázi pouze simulujeme přijetí úkolu
        response = {
            "status": "success",
            "message": "Úkol na kódování byl úspěšně delegován na Jules API.",
            "task_id": "jules_task_mock_12345"
        }
        return self.tool_response("delegate_coding_to_jules", response)

    async def delegate_testing_to_jules(self, test_description: str) -> str:
        """
        Deleguje úkol na vytvoření a spuštění testů na Jules API.

        Args:
            test_description: Popis toho, co by testy měly ověřovat.

        Returns:
            Potvrzení o přijetí úkolu.
        """
        response = {
            "status": "success",
            "message": "Úkol na testování byl úspěšně delegován na Jules API.",
            "task_id": "jules_test_mock_67890"
        }
        return self.tool_response("delegate_testing_to_jules", response)

if __name__ == "__main__":
    async def main():
        server = JulesApiServer("127.0.0.1", 8770, ".")
        await server.start()
        # Keep the server running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            await server.stop()
            print("Server stopped.")

    asyncio.run(main())