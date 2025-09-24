from core.neocortex import Neocortex


# Backwards-compatible alias
class Orchestrator(Neocortex):
    """Compatibility shim. Use `Neocortex` for new behavior."""

    pass
