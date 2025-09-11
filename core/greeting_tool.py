from crewai.tools import BaseTool

class GreetingTool(BaseTool):
    """Vrací jednoduchý pozdrav."""

    name: str = "GreetingTool"
    description: str = "Vrací jednoduchý pozdrav."

    def _run(self, *args, **kwargs) -> str:
        """
        Spustí nástroj a vrátí pozdrav.
        """
        return "Ahoj, jsem tvůj nový nástroj!"

    def _arun(self, *args, **kwargs) -> str:
        raise NotImplementedError("Asynchronous execution not implemented for GreetingTool.")