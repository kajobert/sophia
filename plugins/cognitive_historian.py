import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class Historian(BasePlugin):
    """A cognitive plugin for analyzing the project's history from WORKLOG.md."""

    def __init__(self):
        super().__init__()
        self.worklog_path: Optional[Path] = None

    @property
    def name(self) -> str:
        return "cognitive_historian"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Sets up the path to the WORKLOG.md file."""
        worklog_file = config.get("worklog_file", "WORKLOG.md")
        self.worklog_path = Path(worklog_file).resolve()
        if not self.worklog_path.is_file():
            logger.warning(
                "WORKLOG.md not found at '%s'.",
                self.worklog_path,
            )
        else:
            logger.info(
                "Historian initialized. WORKLOG is at" " '%s'",
                self.worklog_path,
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """This plugin is not directly executed; its methods are called by other cognitive processes."""
        return context

    def review_past_missions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Parses WORKLOG.md and returns a structured list of the most recent missions.
        """
        if not self.worklog_path or not self.worklog_path.is_file():
            return [{"error": "WORKLOG.md not found."}]

        try:
            content = self.worklog_path.read_text(encoding="utf-8")
            missions = []
            # Missions are separated by '---'
            for mission_text in content.split("---")[1:]:  # Skip first split part if empty
                if not mission_text.strip():
                    continue

                mission_data: Dict[str, Any] = {}
                lines = mission_text.strip().split("\n")
                for line in lines:
                    if line.startswith("**Mise:**"):
                        mission_data["mission"] = line.replace("**Mise:**", "").strip()
                    elif line.startswith("**Agent:**"):
                        mission_data["agent"] = line.replace("**Agent:**", "").strip()
                    elif line.startswith("**Datum:**"):
                        mission_data["date"] = line.replace("**Datum:**", "").strip()
                    elif line.startswith("**Status:**"):
                        mission_data["status"] = line.replace("**Status:**", "").strip()

                if mission_data:
                    missions.append(mission_data)

            # Return the most recent missions
            return missions[-limit:]
        except Exception as e:
            logger.error(f"Error parsing WORKLOG.md: {e}", exc_info=True)
            return [{"error": f"Failed to parse WORKLOG.md: {e}"}]
