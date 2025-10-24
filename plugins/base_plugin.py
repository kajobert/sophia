from abc import ABC, abstractmethod
from enum import Enum, auto
from core.context import SharedContext


class PluginType(Enum):
    INTERFACE = auto()
    MEMORY = auto()
    TOOL = auto()
    COGNITIVE = auto()


class BasePlugin(ABC):
    """
    Abstraktni trida definujici striktni kontrakt, ktery musi kazdy plugin dodrzet.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unikatni, popisne jmeno pluginu (napr. "tool_file_system")."""
        pass

    @property
    @abstractmethod
    def plugin_type(self) -> PluginType:
        """Typ pluginu (INTERFACE, MEMORY, TOOL, COGNITIVE)."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Verze pluginu (napr. "1.0.0")."""
        pass

    @abstractmethod
    def setup(self, config: dict) -> None:
        """
        Metoda volana jednou pri nacteni pluginu.
        Slouzi k inicializaci (napr. pripojeni k API, nacteni modelu, konfigurace).
        """
        pass

    @abstractmethod
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Hlavni metoda, kterou vola Jadr (Kernel).
        Musi prijmout SharedContext a po dokonceni sve prace ho vratit
        (upraveny nebo puvodni).
        """
        pass
