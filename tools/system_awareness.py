import os
from typing import Type
from langchain_core.tools import BaseTool as LangchainBaseTool
from pydantic import BaseModel
from tools.base_tool import BaseTool

class SystemAwarenessTool(LangchainBaseTool, BaseTool):
    name: str = "System Awareness"
    description: str = "Provides information about the system environment."
    args_schema: Type[BaseModel] = None # No arguments needed

    def execute(self, **kwargs) -> str:
        return self._run(**kwargs)

    def _run(self) -> str:
        """Returns the current working directory."""
        return f"Current working directory is: {os.getcwd()}"

    async def _arun(self) -> str:
        """Asynchronous version, returns the same."""
        return self._run()
