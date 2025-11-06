"""
Model Manager Plugin

Enables Sophia to autonomously manage her local LLM environment:
- List installed Ollama models
- Pull new models from Ollama registry
- Add/configure models in model_strategy.yaml
- Monitor disk usage and cleanup old models

This plugin gives Sophia the ability to install and configure new local models
when she determines they would improve performance for specific task types.

Version: 1.0.0
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class ModelManagerTool(BasePlugin):
    """
    Plugin for autonomous local model management.
    
    Provides Sophia with the ability to:
    1. List installed Ollama models
    2. Download new models from Ollama registry
    3. Configure models in model_strategy.yaml
    4. Monitor disk usage
    """

    def __init__(self):
        super().__init__()
        self.bash_plugin = None
        self.config_path = Path("config/model_strategy.yaml")

    @property
    def name(self) -> str:
        return "tool_model_manager"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"
        
    def setup(self, config: Dict[str, Any]) -> None:
        """Initialize the model manager plugin."""
        super().setup(config)
        
        # Get reference to bash plugin for CLI commands
        all_plugins = config.get("all_plugins", {})
        self.bash_plugin = all_plugins.get("tool_bash")
        
        if not self.bash_plugin:
            logger.error(
                "[ModelManager] tool_bash plugin not found - cannot execute Ollama commands",
                extra={"plugin_name": self.name}
            )
        else:
            logger.info(
                "[ModelManager] Ready to manage local models",
                extra={"plugin_name": self.name}
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Execute model management operations.
        
        This plugin is typically called via execute_tool() interface.
        Direct execute() usage is for autonomous operations.
        """
        context.payload["info"] = "Use execute_tool() with specific commands"
        context.payload["available_tools"] = [
            "list_local_models",
            "pull_local_model", 
            "add_model_to_strategy",
            "get_disk_usage",
            "remove_local_model"
        ]
        return context

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], context: SharedContext
    ) -> Dict[str, Any]:
        """
        Execute specific model management tool.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool-specific arguments
            context: Shared context
            
        Returns:
            Tool execution result
        """
        logger.info(
            f"[ModelManager] Executing tool: {tool_name}",
            extra={"plugin_name": self.name}
        )
        
        if not self.bash_plugin:
            return {
                "success": False,
                "error": "tool_bash plugin not available - cannot execute Ollama commands"
            }

        # Route to appropriate handler
        if tool_name == "list_local_models":
            return await self._list_local_models(context)
            
        elif tool_name == "pull_local_model":
            model_name = arguments.get("model_name")
            if not model_name:
                return {"success": False, "error": "model_name is required"}
            return await self._pull_local_model(model_name, context)
            
        elif tool_name == "add_model_to_strategy":
            task_type = arguments.get("task_type")
            model = arguments.get("model")
            provider = arguments.get("provider", "ollama")
            
            if not task_type or not model:
                return {"success": False, "error": "task_type and model are required"}
                
            return await self._add_model_to_strategy(task_type, model, provider)
            
        elif tool_name == "get_disk_usage":
            return await self._get_disk_usage(context)
            
        elif tool_name == "remove_local_model":
            model_name = arguments.get("model_name")
            if not model_name:
                return {"success": False, "error": "model_name is required"}
            return await self._remove_local_model(model_name, context)
            
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    async def _list_local_models(self, context: SharedContext) -> Dict[str, Any]:
        """
        List all installed Ollama models.
        
        Returns:
            {
                "success": True,
                "models": [
                    {
                        "name": "llama3.1:8b",
                        "size": "4.7GB",
                        "modified": "2024-11-06"
                    },
                    ...
                ]
            }
        """
        try:
            # Execute 'ollama list' via bash plugin's execute_command
            output = await self.bash_plugin.execute_command(context, "ollama list")
            
            # Check if command failed
            if "error" in output.lower() or "command not found" in output.lower():
                return {
                    "success": False,
                    "error": f"Failed to execute 'ollama list': {output}"
                }
            
            # Parse ollama list output (extract STDOUT section)
            if "STDOUT:" in output:
                stdout_section = output.split("STDOUT:")[1].split("STDERR:")[0].strip()
            else:
                stdout_section = output.strip()
            
            models = self._parse_ollama_list(stdout_section)
            
            logger.info(
                f"[ModelManager] Found {len(models)} local models",
                extra={"plugin_name": self.name}
            )
            
            return {
                "success": True,
                "models": models,
                "count": len(models)
            }
            
        except Exception as e:
            logger.error(
                f"[ModelManager] Error listing models: {e}",
                extra={"plugin_name": self.name}
            )
            return {"success": False, "error": str(e)}

    def _parse_ollama_list(self, output: str) -> List[Dict[str, str]]:
        """
        Parse 'ollama list' command output.
        
        Example output:
        NAME                    ID              SIZE      MODIFIED
        llama3.1:8b            1234abcd        4.7 GB    2 days ago
        gemma2:2b              5678efgh        1.6 GB    1 week ago
        
        Returns:
            List of model dictionaries
        """
        models = []
        lines = output.strip().split("\n")
        
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
                
            # Split by whitespace, handling multiple spaces
            parts = line.split()
            if len(parts) >= 4:
                models.append({
                    "name": parts[0],
                    "id": parts[1],
                    "size": f"{parts[2]} {parts[3]}",
                    "modified": " ".join(parts[4:]) if len(parts) > 4 else "unknown"
                })
        
        return models

    async def _pull_local_model(self, model_name: str, context: SharedContext) -> Dict[str, Any]:
        """
        Download a model from Ollama registry.
        
        Args:
            model_name: Model identifier (e.g., "llama3.2:3b", "gemma2:9b")
            
        Returns:
            {
                "success": True,
                "model": "llama3.2:3b",
                "message": "Model downloaded successfully"
            }
        """
        try:
            logger.info(
                f"[ModelManager] Pulling model: {model_name}",
                extra={"plugin_name": self.name}
            )
            
            # Execute 'ollama pull <model_name>' via bash plugin
            output = await self.bash_plugin.execute_command(context, f"ollama pull {model_name}")
            
            # Check for errors
            if "error" in output.lower() and "STDOUT:" not in output:
                return {
                    "success": False,
                    "error": f"Failed to pull model: {output}"
                }
            
            logger.info(
                f"[ModelManager] Successfully pulled {model_name}",
                extra={"plugin_name": self.name}
            )
            
            return {
                "success": True,
                "model": model_name,
                "message": f"Model {model_name} downloaded successfully",
                "output": output
            }
            
        except Exception as e:
            logger.error(
                f"[ModelManager] Error pulling model: {e}",
                extra={"plugin_name": self.name}
            )
            return {"success": False, "error": str(e)}

    async def _add_model_to_strategy(
        self, task_type: str, model: str, provider: str = "ollama"
    ) -> Dict[str, Any]:
        """
        Add or update a model in model_strategy.yaml.
        
        Args:
            task_type: Task category (e.g., "simple_query", "code_generation")
            model: Model identifier (e.g., "llama3.1:8b")
            provider: Provider name (default: "ollama")
            
        Returns:
            {
                "success": True,
                "message": "Model configured for task_type",
                "config_path": "config/model_strategy.yaml"
            }
        """
        if yaml is None:
            return {
                "success": False,
                "error": "PyYAML not installed - cannot modify config files"
            }
        
        try:
            # Load existing strategy config
            if not self.config_path.exists():
                logger.warning(
                    f"[ModelManager] {self.config_path} not found, creating new file",
                    extra={"plugin_name": self.name}
                )
                strategy = {"task_routing": {}}
            else:
                with open(self.config_path, "r") as f:
                    strategy = yaml.safe_load(f) or {}
            
            # Ensure task_routing section exists
            if "task_routing" not in strategy:
                strategy["task_routing"] = {}
            
            # Add or update task type configuration
            strategy["task_routing"][task_type] = {
                "model": model,
                "provider": provider,
                "fallback": "openrouter/meta-llama/llama-3.1-8b-instruct:free"
            }
            
            # Write updated config
            with open(self.config_path, "w") as f:
                yaml.dump(strategy, f, default_flow_style=False, sort_keys=False)
            
            logger.info(
                f"[ModelManager] Configured {model} for {task_type}",
                extra={"plugin_name": self.name}
            )
            
            return {
                "success": True,
                "message": f"Model {model} configured for {task_type}",
                "config_path": str(self.config_path),
                "task_type": task_type,
                "model": model,
                "provider": provider
            }
            
        except Exception as e:
            logger.error(
                f"[ModelManager] Error updating strategy config: {e}",
                extra={"plugin_name": self.name}
            )
            return {"success": False, "error": str(e)}

    async def _get_disk_usage(self, context: SharedContext) -> Dict[str, Any]:
        """
        Get disk usage for Ollama models directory.
        
        Returns:
            {
                "success": True,
                "total_size": "12.5 GB",
                "models_path": "~/.ollama/models"
            }
        """
        try:
            # Get Ollama models directory size
            output = await self.bash_plugin.execute_command(
                context, 
                "du -sh ~/.ollama/models 2>/dev/null || echo '0 unknown'"
            )
            
            # Extract size from output
            if "STDOUT:" in output:
                stdout_section = output.split("STDOUT:")[1].split("STDERR:")[0].strip()
            else:
                stdout_section = output.strip()
            
            parts = stdout_section.split()
            size = parts[0] if parts else "unknown"
            
            return {
                "success": True,
                "total_size": size,
                "models_path": "~/.ollama/models"
            }
                
        except Exception as e:
            logger.error(
                f"[ModelManager] Error getting disk usage: {e}",
                extra={"plugin_name": self.name}
            )
            return {"success": False, "error": str(e)}

    async def _remove_local_model(self, model_name: str, context: SharedContext) -> Dict[str, Any]:
        """
        Remove a local Ollama model to free disk space.
        
        Args:
            model_name: Model identifier to remove
            
        Returns:
            {
                "success": True,
                "model": "old-model:7b",
                "message": "Model removed successfully"
            }
        """
        try:
            logger.info(
                f"[ModelManager] Removing model: {model_name}",
                extra={"plugin_name": self.name}
            )
            
            output = await self.bash_plugin.execute_command(context, f"ollama rm {model_name}")
            
            # Check for errors
            if "error" in output.lower() and "deleted" not in output.lower():
                return {
                    "success": False,
                    "error": f"Failed to remove model: {output}"
                }
            
            logger.info(
                f"[ModelManager] Successfully removed {model_name}",
                extra={"plugin_name": self.name}
            )
            
            return {
                "success": True,
                "model": model_name,
                "message": f"Model {model_name} removed successfully"
            }
            
        except Exception as e:
            logger.error(
                f"[ModelManager] Error removing model: {e}",
                extra={"plugin_name": self.name}
            )
            return {"success": False, "error": str(e)}

    def get_capabilities(self) -> List[str]:
        """Return list of plugin capabilities."""
        return [
            "list_local_models",
            "pull_local_model",
            "add_model_to_strategy",
            "get_disk_usage",
            "remove_local_model"
        ]
