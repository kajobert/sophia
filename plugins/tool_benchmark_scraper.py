"""
External Benchmark Scraper Plugin

Fetches benchmark data from public sources:
- Artificial Analysis (artificialanalysis.ai)
- LMSys Arena Leaderboard
- OpenLLM Leaderboard (HuggingFace)

Stores structured benchmark results in database for comparison with internal tests.

Architecture:
- Tool plugin (provides scrape_benchmarks, get_external_benchmarks methods)
- Periodic refresh via heartbeat events
- SQLite storage: .data/external_benchmarks.db

Usage:
    await tool_benchmark_scraper.scrape_benchmarks()
    data = await tool_benchmark_scraper.get_external_benchmarks(metric="quality")
"""

import asyncio
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class BenchmarkScraperPlugin(BasePlugin):
    """Scrape external LLM benchmarks from public sources."""

    def __init__(self):
        self.db_path: Path = Path(".data/external_benchmarks.db")
        self.last_scrape: Optional[datetime] = None
        self.scrape_interval_hours = 24  # Scrape daily
        self.sources = {
            "artificial_analysis": "https://artificialanalysis.ai/models",
            "lmsys_arena": "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard",
            "openllm": "https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard",
        }

    @property
    def name(self) -> str:
        return "tool_benchmark_scraper"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initialize scraper and database."""
        self._init_database()

        # Subscribe to heartbeat for periodic scraping
        event_bus = config.get("event_bus")
        if event_bus:
            event_bus.subscribe("PROACTIVE_HEARTBEAT", self._on_heartbeat)
            logger.info("Subscribed to PROACTIVE_HEARTBEAT for benchmark scraping")

    def _init_database(self) -> None:
        """Create SQLite database for external benchmarks."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS external_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                source TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_unit TEXT,
                rank INTEGER,
                provider TEXT,
                cost_per_1m_tokens REAL,
                speed_tokens_per_sec REAL,
                context_window INTEGER,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_name, source, metric_name)
            )
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_source ON external_benchmarks(model_name, source)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_metric ON external_benchmarks(metric_name, metric_value)
        """)

        conn.commit()
        conn.close()

        logger.info(f"External benchmarks database initialized: {self.db_path}")

    async def _on_heartbeat(self, event: Dict[str, Any]) -> None:
        """Scrape benchmarks on heartbeat events."""
        # Only scrape if 24+ hours since last scrape
        if self.last_scrape:
            hours_since = (datetime.now() - self.last_scrape).total_seconds() / 3600
            if hours_since < self.scrape_interval_hours:
                return

        logger.info("Scraping external benchmarks (heartbeat trigger)")
        try:
            await self.scrape_benchmarks()
        except Exception as e:
            logger.error(f"Failed to scrape benchmarks: {e}")

    async def scrape_benchmarks(self, context: Optional[SharedContext] = None) -> Dict[str, Any]:
        """
        Scrape latest benchmarks from all sources.

        Returns:
            Dict with success status and counts per source
        """
        if context:
            logger_instance = context.logger
        else:
            logger_instance = logging.getLogger(__name__)

        results = {
            "success": True,
            "sources": {},
            "total_entries": 0,
        }

        # Scrape each source
        try:
            results["sources"]["artificial_analysis"] = await self._scrape_artificial_analysis()
        except Exception as e:
            logger_instance.error(f"Failed to scrape Artificial Analysis: {e}")
            results["sources"]["artificial_analysis"] = {"success": False, "error": str(e)}

        try:
            results["sources"]["lmsys_arena"] = await self._scrape_lmsys_arena()
        except Exception as e:
            logger_instance.error(f"Failed to scrape LMSys Arena: {e}")
            results["sources"]["lmsys_arena"] = {"success": False, "error": str(e)}

        # Calculate total
        for source_result in results["sources"].values():
            if isinstance(source_result, dict) and source_result.get("success"):
                results["total_entries"] += source_result.get("entries_stored", 0)

        self.last_scrape = datetime.now()
        logger_instance.info(f"Benchmark scraping complete: {results['total_entries']} entries")

        return results

    async def _scrape_artificial_analysis(self) -> Dict[str, Any]:
        """
        Scrape benchmark data from Artificial Analysis.
        
        Returns cost, speed, quality metrics per model.
        """
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(self.sources["artificial_analysis"])
                response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find model comparison table
            # NOTE: This is a simplified parser - real implementation needs to adapt to actual HTML structure
            table = soup.find("table", {"class": re.compile(r"model|comparison|benchmark", re.I)})
            
            if not table:
                logger.warning("Artificial Analysis: No table found")
                return {"success": False, "error": "Table not found"}

            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            entries_stored = 0

            # Extract rows
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cols = row.find_all("td")
                if len(cols) < 3:
                    continue

                # Extract data (adapt to actual structure)
                model_name = cols[0].get_text(strip=True)
                
                # Try to find quality score
                quality_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                quality_match = re.search(r"(\d+\.?\d*)", quality_text)
                quality_score = float(quality_match.group(1)) if quality_match else None

                # Try to find cost
                cost_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                cost_match = re.search(r"\$?(\d+\.?\d*)", cost_text)
                cost = float(cost_match.group(1)) if cost_match else None

                # Try to find speed
                speed_text = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                speed_match = re.search(r"(\d+\.?\d*)", speed_text)
                speed = float(speed_match.group(1)) if speed_match else None

                # Store metrics
                if quality_score:
                    cur.execute("""
                        INSERT OR REPLACE INTO external_benchmarks 
                        (model_name, source, metric_name, metric_value, metric_unit, scraped_at)
                        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (model_name, "artificial_analysis", "quality", quality_score, "score"))
                    entries_stored += 1

                if cost:
                    cur.execute("""
                        INSERT OR REPLACE INTO external_benchmarks 
                        (model_name, source, metric_name, metric_value, metric_unit, cost_per_1m_tokens, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (model_name, "artificial_analysis", "cost", cost, "$/1M", cost))
                    entries_stored += 1

                if speed:
                    cur.execute("""
                        INSERT OR REPLACE INTO external_benchmarks 
                        (model_name, source, metric_name, metric_value, metric_unit, speed_tokens_per_sec, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (model_name, "artificial_analysis", "speed", speed, "tok/s", speed))
                    entries_stored += 1

            conn.commit()
            conn.close()

            return {"success": True, "entries_stored": entries_stored}

        except Exception as e:
            logger.error(f"Error scraping Artificial Analysis: {e}")
            return {"success": False, "error": str(e)}

    async def _scrape_lmsys_arena(self) -> Dict[str, Any]:
        """
        Scrape LMSys Chatbot Arena leaderboard.
        
        Returns ELO ratings per model.
        """
        try:
            # LMSys provides JSON API endpoint
            api_url = "https://huggingface.co/api/spaces/lmsys/chatbot-arena-leaderboard/data"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url)
                response.raise_for_status()
                data = response.json()

            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            entries_stored = 0

            # Parse leaderboard data
            # NOTE: Adapt to actual API structure
            leaderboard = data.get("leaderboard", [])
            
            for rank, entry in enumerate(leaderboard, start=1):
                model_name = entry.get("model", "unknown")
                elo_rating = entry.get("rating", 0)
                arena_score = entry.get("arena_score", 0)

                # Store ELO rating
                if elo_rating:
                    cur.execute("""
                        INSERT OR REPLACE INTO external_benchmarks 
                        (model_name, source, metric_name, metric_value, metric_unit, rank, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (model_name, "lmsys_arena", "elo_rating", elo_rating, "ELO", rank))
                    entries_stored += 1

                # Store arena score
                if arena_score:
                    cur.execute("""
                        INSERT OR REPLACE INTO external_benchmarks 
                        (model_name, source, metric_name, metric_value, metric_unit, rank, scraped_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (model_name, "lmsys_arena", "arena_score", arena_score, "score", rank))
                    entries_stored += 1

            conn.commit()
            conn.close()

            return {"success": True, "entries_stored": entries_stored}

        except Exception as e:
            logger.error(f"Error scraping LMSys Arena: {e}")
            return {"success": False, "error": str(e)}

    async def get_external_benchmarks(
        self,
        context: SharedContext,
        model_name: Optional[str] = None,
        source: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get external benchmark data with filtering.

        Args:
            context: Shared context
            model_name: Filter by model name
            source: Filter by source (artificial_analysis/lmsys_arena/openllm)
            metric_name: Filter by metric (quality/cost/speed/elo_rating)
            limit: Maximum results to return

        Returns:
            List of benchmark entries
        """
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        # Build query
        query = "SELECT * FROM external_benchmarks WHERE 1=1"
        params = []

        if model_name:
            query += " AND model_name = ?"
            params.append(model_name)

        if source:
            query += " AND source = ?"
            params.append(source)

        if metric_name:
            query += " AND metric_name = ?"
            params.append(metric_name)

        query += " ORDER BY scraped_at DESC LIMIT ?"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()

        benchmarks = []
        for row in rows:
            benchmarks.append({
                "id": row[0],
                "model_name": row[1],
                "source": row[2],
                "metric_name": row[3],
                "metric_value": row[4],
                "metric_unit": row[5],
                "rank": row[6],
                "provider": row[7],
                "cost_per_1m_tokens": row[8],
                "speed_tokens_per_sec": row[9],
                "context_window": row[10],
                "scraped_at": row[11],
            })

        conn.close()

        context.logger.info(f"Retrieved {len(benchmarks)} external benchmarks")
        return benchmarks

    async def execute(self, context: SharedContext) -> SharedContext:
        """Cognitive execute - not used for tool plugins."""
        context.payload["info"] = "Use scrape_benchmarks() or get_external_benchmarks() methods"
        return context

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return tool definitions for benchmark scraping."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "scrape_benchmarks",
                    "description": "Scrape latest benchmark data from public sources (Artificial Analysis, LMSys Arena). Updates local database.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_external_benchmarks",
                    "description": "Get external benchmark data with filtering options. Returns data from local database.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "model_name": {
                                "type": "string",
                                "description": "Filter by model name (e.g., 'gpt-4', 'claude-3-opus')",
                            },
                            "source": {
                                "type": "string",
                                "description": "Filter by source (artificial_analysis/lmsys_arena/openllm)",
                            },
                            "metric_name": {
                                "type": "string",
                                "description": "Filter by metric (quality/cost/speed/elo_rating)",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results to return (default 100)",
                            },
                        },
                        "required": [],
                    },
                },
            },
        ]
