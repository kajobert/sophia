from abc import ABC, abstractmethod
from typing import Any

class BaseTool(ABC):
    """
    Abstract base class for all tools to ensure a unified interface.
    """

    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Executes the tool's functionality.

        Note: The return type is `Any` to accommodate tools that may return
        different types of results (e.g., a string, a list of strings, etc.).
        The consumer of the tool is responsible for handling the specific return type.
        """
        pass
