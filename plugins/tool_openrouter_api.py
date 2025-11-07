"""
OpenRouter API Integration Plugin

Fetches available models from OpenRouter with pricing, context limits, and capabilities.
Stores model catalog in database for comparison with internal benchmarks.

Architecture:
- Tool plugin (provides get_models, get_model_details methods)
- Periodic refresh via heartbeat events
- SQLite storage: .data/openrouter_models.db

Usage:
    models = await tool_openrouter_api.get_models()
    details = await tool_openrouter_api.get_model_details("openai/gpt-4")
"""

import asyncio
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class OpenRouterAPIPlugin(BasePlugin):
    """Fetch and cache model data from OpenRouter API."""

    def __init__(self):
        self.api_key: Optional[str] = None
        self.db_path: Path = Path(".data/openrouter_models.db")
        self.base_url = "https://openrouter.ai/api/v1"
        self.last_refresh: Optional[datetime] = None
        self.refresh_interval_hours = 24  # Refresh catalog daily

    @property
    def name(self) -> str:
        return "tool_openrouter_api"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initialize OpenRouter API client."""
        self.api_key = config.get("api_key") or config.get("openrouter_api_key")
        
        if not self.api_key:
            logger.warning("OpenRouter API key not provided - using public endpoints only")

        # Create database
        self._init_database()

        # Subscribe to heartbeat for periodic refresh
        event_bus = config.get("event_bus")
        if event_bus:
            event_bus.subscribe("PROACTIVE_HEARTBEAT", self._on_heartbeat)
            logger.info("Subscribed to PROACTIVE_HEARTBEAT for model catalog refresh")

    def _init_database(self) -> None:
        """Create SQLite database for model catalog."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS models (
                model_id TEXT PRIMARY KEY,
                model_name TEXT NOT NULL,
                provider TEXT,
                context_length INTEGER,
                pricing_prompt REAL,
                pricing_completion REAL,
                pricing_image REAL,
                supports_function_calling BOOLEAN,
                supports_vision BOOLEAN,
                supports_tool_use BOOLEAN,
                top_provider TEXT,
                architecture TEXT,
                modality TEXT,
                raw_data TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_provider ON models(provider)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_pricing ON models(pricing_prompt)
        """)

        conn.commit()
        conn.close()

        logger.info(f"OpenRouter models database initialized: {self.db_path}")

    async def _on_heartbeat(self, event: Dict[str, Any]) -> None:
        """Refresh model catalog on heartbeat events."""
        # Only refresh if 24+ hours since last refresh
        if self.last_refresh:
            hours_since = (datetime.now() - self.last_refresh).total_seconds() / 3600
            if hours_since < self.refresh_interval_hours:
                return

        logger.info("Refreshing OpenRouter model catalog (heartbeat trigger)")
        try:
            await self.refresh_model_catalog()
        except Exception as e:
            logger.error(f"Failed to refresh model catalog: {e}")

    async def get_models(
        self,
        context: SharedContext,
        provider: Optional[str] = None,
        supports_function_calling: Optional[bool] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get list of models from local cache with optional filtering.

        Args:
            context: Shared context
            provider: Filter by provider (e.g., "openai", "anthropic")
            supports_function_calling: Filter by function calling support
            max_price: Maximum price per 1M tokens (prompt)

        Returns:
            List of model dictionaries
        """
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        # Build query with filters
        query = "SELECT * FROM models WHERE 1=1"
        params = []

        if provider:
            query += " AND provider = ?"
            params.append(provider)

        if supports_function_calling is not None:
            query += " AND supports_function_calling = ?"
            params.append(1 if supports_function_calling else 0)

        if max_price is not None:
            query += " AND pricing_prompt <= ?"
            params.append(max_price)

        query += " ORDER BY pricing_prompt ASC"

        cur.execute(query, params)
        rows = cur.fetchall()

        models = []
        for row in rows:
            models.append({
                "model_id": row[0],
                "model_name": row[1],
                "provider": row[2],
                "context_length": row[3],
                "pricing": {
                    "prompt": row[4],
                    "completion": row[5],
                    "image": row[6],
                },
                "supports_function_calling": bool(row[7]),
                "supports_vision": bool(row[8]),
                "supports_tool_use": bool(row[9]),
                "top_provider": row[10],
                "architecture": row[11],
                "modality": row[12],
                "last_updated": row[14],
            })

        conn.close()

        context.logger.info(f"Retrieved {len(models)} models from cache")
        return models

    async def get_model_details(
        self, context: SharedContext, model_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific model.

        Args:
            context: Shared context
            model_id: Model ID (e.g., "openai/gpt-4")

        Returns:
            Model details dict or None if not found
        """
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        cur.execute("SELECT * FROM models WHERE model_id = ?", (model_id,))
        row = cur.fetchone()

        if not row:
            conn.close()
            return None

        conn.close()

        return {
            "model_id": row[0],
            "model_name": row[1],
            "provider": row[2],
            "context_length": row[3],
            "pricing": {
                "prompt": row[4],
                "completion": row[5],
                "image": row[6],
            },
            "supports_function_calling": bool(row[7]),
            "supports_vision": bool(row[8]),
            "supports_tool_use": bool(row[9]),
            "top_provider": row[10],
            "architecture": row[11],
            "modality": row[12],
            "raw_data": row[13],
            "last_updated": row[14],
        }

    async def refresh_model_catalog(self, context: Optional[SharedContext] = None) -> Dict[str, Any]:
        """
        Fetch latest model catalog from OpenRouter API.

        Returns:
            Dict with success status and model count
        """
        if context:
            logger = context.logger
        else:
            logger = logging.getLogger(__name__)

        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()

            models_data = data.get("data", [])
            logger.info(f"Fetched {len(models_data)} models from OpenRouter API")

            # Store in database
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()

            stored_count = 0
            for model in models_data:
                model_id = model.get("id")
                if not model_id:
                    continue

                # Extract pricing (convert to cost per 1M tokens)
                pricing = model.get("pricing", {})
                prompt_price = float(pricing.get("prompt", 0)) * 1_000_000
                completion_price = float(pricing.get("completion", 0)) * 1_000_000
                image_price = float(pricing.get("image", 0)) * 1_000_000

                # Extract capabilities
                supports_fc = model.get("supports_function_calling", False)
                supports_vision = "vision" in model.get("modality", "").lower()
                supports_tools = model.get("supports_tools", False)

                cur.execute("""
                    INSERT OR REPLACE INTO models (
                        model_id, model_name, provider, context_length,
                        pricing_prompt, pricing_completion, pricing_image,
                        supports_function_calling, supports_vision, supports_tool_use,
                        top_provider, architecture, modality, raw_data, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    model_id,
                    model.get("name", model_id),
                    model.get("provider", "unknown"),
                    model.get("context_length", 0),
                    prompt_price,
                    completion_price,
                    image_price,
                    supports_fc,
                    supports_vision,
                    supports_tools,
                    model.get("top_provider"),
                    model.get("architecture", {}).get("tokenizer"),
                    model.get("modality", "text"),
                    str(model),  # Store full JSON for future reference
                ))
                stored_count += 1

            conn.commit()
            conn.close()

            self.last_refresh = datetime.now()
            logger.info(f"Stored {stored_count} models in database")

            return {"success": True, "models_stored": stored_count}

        except Exception as e:
            logger.error(f"Failed to refresh model catalog: {e}")
            return {"success": False, "error": str(e)}

    async def execute(self, context: SharedContext) -> SharedContext:
        """Cognitive execute - not used for tool plugins."""
        context.payload["info"] = "Use get_models() or refresh_model_catalog() methods"
        return context

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return tool definitions for OpenRouter API operations."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_models",
                    "description": "Get list of available models from OpenRouter with filtering options. Returns cached data from local database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "description": "Filter by provider (e.g., 'openai', 'anthropic', 'google')",
                            },
                            "supports_function_calling": {
                                "type": "boolean",
                                "description": "Filter models that support function calling",
                            },
                            "max_price": {
                                "type": "number",
                                "description": "Maximum price per 1M tokens (prompt)",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_model_details",
                    "description": "Get detailed information about a specific model including pricing, capabilities, and specifications.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model_id": {
                                "type": "string",
                                "description": "Model ID (e.g., 'openai/gpt-4', 'anthropic/claude-3-sonnet')",
                            },
                        },
                        "required": ["model_id"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "refresh_model_catalog",
                    "description": "Manually refresh model catalog from OpenRouter API. Normally refreshes automatically every 24 hours.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        ]
