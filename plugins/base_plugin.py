from abc import ABC, abstractmethod
from enum import Enum, auto
from core.context import SharedContext


class PluginType(Enum):
    CORE = auto()
    INTERFACE = auto()
    MEMORY = auto()
    TOOL = auto()
    COGNITIVE = auto()


class BasePlugin(ABC):
    """
    Abstract class defining the strict contract that every plugin must adhere to.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """A unique, descriptive name for the plugin (e.g., "tool_file_system")."""
        pass

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """The type of the plugin (INTERFACE, MEMORY, TOOL, COGNITIVE)."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """The version of the plugin (e.g., "1.0.0")."""
        pass

    @abstractmethod
    def setup(self, config: dict) -> None:
        """
        Method called once when the plugin is loaded.
        Used for initialization (e.g., connecting to an API, loading a model, configuration).
        """
        pass

    @abstractmethod
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        The main method called by the Kernel.
        It must accept a SharedContext and return it (modified or original)
        after its work is complete.
        """
        pass
