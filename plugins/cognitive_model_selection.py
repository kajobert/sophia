"""
Intelligent Model Selection Plugin

Analyzes internal benchmarks vs external benchmark data to identify:
1. Models worth testing (performance gaps, cost efficiency)
2. Task-specific strengths
3. Priority models for next benchmark run

Architecture:
- Cognitive plugin (runs on heartbeat events)
- Compares data from:
  - .data/model_benchmarks.db (internal tests)
  - .data/external_benchmarks.db (scraped data)
  - .data/openrouter_models.db (available models)
- Generates recommendations stored in .data/model_recommendations.db

Algorithm:
1. Find models in OpenRouter catalog but not yet benchmarked internally
2. Compare external benchmark scores with our internal results
3. Identify models with high external ratings + low cost
4. Prioritize models for specific task types based on architecture/capabilities
5. Generate ranked list of models to test next

Usage:
    # Runs automatically on heartbeat
    recommendations = await get_model_recommendations(task_type="planning")
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext

logger = logging.getLogger(__name__)


class ModelSelectionPlugin(BasePlugin):
    """Intelligent model selection based on internal/external benchmark comparison."""

    def __init__(self):
        self.db_path: Path = Path(".data/model_recommendations.db")
        self.last_analysis: Optional[datetime] = None
        self.analysis_interval_heartbeats = 24  # Run daily

    @property
    def name(self) -> str:
        return "cognitive_model_selection"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Initialize model selection system."""
        self._logger = config.get("logger", logger)
        self._init_database()

        # Subscribe to heartbeat
        event_bus = config.get("event_bus")
        if event_bus:
            event_bus.subscribe("PROACTIVE_HEARTBEAT", self._on_heartbeat)
            self._logger.info("Model selection plugin subscribed to heartbeat")

    def _init_database(self) -> None:
        """Create recommendations database."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT NOT NULL,
                model_name TEXT NOT NULL,
                recommendation_type TEXT NOT NULL,
                task_type TEXT,
                priority_score REAL NOT NULL,
                reasoning TEXT,
                external_quality_score REAL,
                external_cost REAL,
                external_speed REAL,
                already_tested BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(model_id, task_type)
            )
        """)

        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_priority ON recommendations(priority_score DESC)
        """)

        conn.commit()
        conn.close()

        self._logger.info(f"Model recommendations database initialized: {self.db_path}")

    async def _on_heartbeat(self, event: Dict[str, Any]) -> None:
        """Run model selection analysis on heartbeat."""
        # Check if enough time passed
        if self.last_analysis:
            heartbeats_passed = (datetime.now() - self.last_analysis).total_seconds() / 3600
            if heartbeats_passed < self.analysis_interval_heartbeats:
                return

        self._logger.info("Running model selection analysis (heartbeat trigger)")
        try:
            # Create minimal context for analysis
            from core.state import State
            context = SharedContext(
                session_id="model_selection_analysis",
                current_state=State.IDLE,
                logger=self._logger
            )
            await self.analyze_and_recommend(context)
        except Exception as e:
            self._logger.error(f"Model selection analysis failed: {e}")

    async def analyze_and_recommend(self, context: SharedContext) -> Dict[str, Any]:
        """
        Analyze models and generate recommendations.

        Returns:
            Dict with analysis results and recommendation count
        """
        recommendations = []

        # 1. Find untested models
        untested = self._find_untested_models()
        context.logger.info(f"Found {len(untested)} untested models in OpenRouter catalog")

        for model_info in untested:
            # Get external benchmark data
            external_data = self._get_external_benchmark(model_info["model_id"])

            # Calculate priority score
            priority = self._calculate_priority(model_info, external_data)

            # Generate reasoning
            reasoning = self._generate_reasoning(model_info, external_data, priority)

            # Determine recommended task types
            task_types = self._recommend_task_types(model_info)

            for task_type in task_types:
                recommendations.append({
                    "model_id": model_info["model_id"],
                    "model_name": model_info["model_name"],
                    "task_type": task_type,
                    "priority_score": priority,
                    "reasoning": reasoning,
                    "external_data": external_data,
                })

        # 2. Find models with performance gaps (external high, internal low)
        gaps = self._find_performance_gaps()
        context.logger.info(f"Found {len(gaps)} models with performance gaps")

        for gap_info in gaps:
            recommendations.append({
                "model_id": gap_info["model_id"],
                "model_name": gap_info["model_name"],
                "task_type": gap_info["task_type"],
                "priority_score": gap_info["priority"],
                "reasoning": gap_info["reasoning"],
                "external_data": gap_info.get("external_data", {}),
            })

        # 3. Store recommendations
        stored = self._store_recommendations(recommendations)
        context.logger.info(f"Stored {stored} model recommendations")

        self.last_analysis = datetime.now()

        return {
            "success": True,
            "untested_models": len(untested),
            "performance_gaps": len(gaps),
            "total_recommendations": stored,
        }

    def _find_untested_models(self) -> List[Dict[str, Any]]:
        """Find models in OpenRouter catalog that haven't been benchmarked."""
        openrouter_db = Path(".data/openrouter_models.db")
        benchmarks_db = Path(".data/model_benchmarks.db")

        if not openrouter_db.exists():
            return []

        conn_or = sqlite3.connect(str(openrouter_db))
        cur_or = conn_or.cursor()

        # Get all available models
        cur_or.execute("""
            SELECT model_id, model_name, provider, pricing_prompt, 
                   supports_function_calling, context_length
            FROM models
            WHERE pricing_prompt > 0  -- Exclude unavailable models
        """)
        available_models = cur_or.fetchall()
        conn_or.close()

        # Get tested models
        tested_model_ids = set()
        if benchmarks_db.exists():
            conn_bm = sqlite3.connect(str(benchmarks_db))
            cur_bm = conn_bm.cursor()
            cur_bm.execute("SELECT DISTINCT model_name FROM model_benchmarks")
            tested_model_ids = {row[0] for row in cur_bm.fetchall()}
            conn_bm.close()

        # Find untested
        untested = []
        for model in available_models:
            model_id = model[0]
            if model_id not in tested_model_ids:
                untested.append({
                    "model_id": model_id,
                    "model_name": model[1],
                    "provider": model[2],
                    "cost": model[3],
                    "supports_fc": bool(model[4]),
                    "context_length": model[5],
                })

        return untested

    def _find_performance_gaps(self) -> List[Dict[str, Any]]:
        """Find models with high external scores but low internal scores."""
        external_db = Path(".data/external_benchmarks.db")
        benchmarks_db = Path(".data/model_benchmarks.db")

        if not external_db.exists() or not benchmarks_db.exists():
            return []

        gaps = []

        # Get models with external data
        conn_ext = sqlite3.connect(str(external_db))
        cur_ext = conn_ext.cursor()

        cur_ext.execute("""
            SELECT model_name, AVG(metric_value) as avg_external_score
            FROM external_benchmarks
            WHERE metric_name IN ('quality', 'elo_rating', 'arena_score')
            GROUP BY model_name
            HAVING avg_external_score > 70  -- High external rating
        """)
        external_scores = cur_ext.fetchall()
        conn_ext.close()

        # Compare with internal scores
        conn_bm = sqlite3.connect(str(benchmarks_db))
        cur_bm = conn_bm.cursor()

        for model_name, ext_score in external_scores:
            cur_bm.execute("""
                SELECT AVG(quality_score) as avg_internal_score
                FROM model_benchmarks
                WHERE model_name = ?
            """, (model_name,))
            
            result = cur_bm.fetchone()
            if result and result[0] is not None:
                int_score = result[0]
                
                # Gap detected: external high, internal low
                if ext_score > int_score + 20:  # 20-point gap
                    gaps.append({
                        "model_id": model_name,
                        "model_name": model_name,
                        "task_type": "all",
                        "priority": 90,  # High priority
                        "reasoning": f"Performance gap: External={ext_score:.1f}, Internal={int_score:.1f}. Retest recommended.",
                        "external_data": {"quality": ext_score},
                    })

        conn_bm.close()
        return gaps

    def _get_external_benchmark(self, model_id: str) -> Dict[str, Any]:
        """Get external benchmark data for a model."""
        external_db = Path(".data/external_benchmarks.db")
        if not external_db.exists():
            return {}

        conn = sqlite3.connect(str(external_db))
        cur = conn.cursor()

        cur.execute("""
            SELECT metric_name, AVG(metric_value) as avg_value
            FROM external_benchmarks
            WHERE model_name = ?
            GROUP BY metric_name
        """, (model_id,))

        data = {}
        for row in cur.fetchall():
            data[row[0]] = row[1]

        conn.close()
        return data

    def _calculate_priority(
        self, model_info: Dict[str, Any], external_data: Dict[str, Any]
    ) -> float:
        """
        Calculate priority score (0-100) for testing this model.

        Factors:
        - External quality score (higher = more priority)
        - Cost efficiency (lower cost = more priority)
        - Function calling support (+10 points)
        - Large context window (+5 points)
        """
        priority = 50.0  # Base priority

        # External quality boost
        quality = external_data.get("quality", 0)
        elo = external_data.get("elo_rating", 0)
        if quality > 0:
            priority += (quality / 100) * 30  # Up to +30
        elif elo > 0:
            priority += ((elo - 1000) / 1000) * 30  # Normalize ELO

        # Cost efficiency boost (inverse: cheaper = better)
        cost = model_info.get("cost", 999)
        if cost < 0.5:  # Very cheap
            priority += 15
        elif cost < 2.0:  # Cheap
            priority += 10
        elif cost < 5.0:  # Medium
            priority += 5

        # Feature bonuses
        if model_info.get("supports_fc"):
            priority += 10

        if model_info.get("context_length", 0) > 100000:
            priority += 5

        return min(priority, 100.0)  # Cap at 100

    def _recommend_task_types(self, model_info: Dict[str, Any]) -> List[str]:
        """Determine which task types this model is suited for."""
        task_types = []

        # All models: planning, reasoning
        task_types.extend(["planning", "reasoning"])

        # Function calling models: jules_validation, json_output
        if model_info.get("supports_fc"):
            task_types.extend(["jules_validation", "json_output"])

        # Large context models: code_generation
        if model_info.get("context_length", 0) > 32000:
            task_types.append("code_generation")

        return task_types

    def _generate_reasoning(
        self,
        model_info: Dict[str, Any],
        external_data: Dict[str, Any],
        priority: float,
    ) -> str:
        """Generate human-readable reasoning for recommendation."""
        reasons = []

        # Cost
        cost = model_info.get("cost", 0)
        if cost < 0.5:
            reasons.append(f"Very cost-efficient (${cost:.2f}/1M)")
        elif cost < 2.0:
            reasons.append(f"Cost-efficient (${cost:.2f}/1M)")

        # External scores
        if "quality" in external_data:
            reasons.append(f"High quality score ({external_data['quality']:.1f}/100)")
        if "elo_rating" in external_data:
            reasons.append(f"Strong ELO rating ({external_data['elo_rating']:.0f})")

        # Features
        if model_info.get("supports_fc"):
            reasons.append("Supports function calling")
        if model_info.get("context_length", 0) > 100000:
            reasons.append(f"Large context ({model_info['context_length']:,} tokens)")

        # Priority level
        if priority > 80:
            reasons.append("⭐ HIGH PRIORITY")
        elif priority > 60:
            reasons.append("🔹 Medium priority")

        return " | ".join(reasons) if reasons else "Untested model in catalog"

    def _store_recommendations(self, recommendations: List[Dict[str, Any]]) -> int:
        """Store recommendations in database."""
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        stored = 0
        for rec in recommendations:
            try:
                external_data = rec.get("external_data", {})
                
                cur.execute("""
                    INSERT OR REPLACE INTO recommendations (
                        model_id, model_name, recommendation_type, task_type,
                        priority_score, reasoning,
                        external_quality_score, external_cost, external_speed,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    rec["model_id"],
                    rec["model_name"],
                    "untested",
                    rec.get("task_type", "all"),
                    rec["priority_score"],
                    rec["reasoning"],
                    external_data.get("quality"),
                    external_data.get("cost"),
                    external_data.get("speed"),
                ))
                stored += 1
            except Exception as e:
                self._logger.error(f"Failed to store recommendation for {rec['model_id']}: {e}")

        conn.commit()
        conn.close()

        return stored

    async def get_recommendations(
        self,
        context: SharedContext,
        task_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Get model recommendations with filtering.

        Args:
            context: Shared context
            task_type: Filter by task type
            limit: Maximum recommendations to return

        Returns:
            List of recommendations sorted by priority
        """
        conn = sqlite3.connect(str(self.db_path))
        cur = conn.cursor()

        query = "SELECT * FROM recommendations WHERE 1=1"
        params = []

        if task_type:
            query += " AND task_type = ?"
            params.append(task_type)

        query += " ORDER BY priority_score DESC LIMIT ?"
        params.append(limit)

        cur.execute(query, params)
        rows = cur.fetchall()

        recommendations = []
        for row in rows:
            recommendations.append({
                "model_id": row[1],
                "model_name": row[2],
                "task_type": row[4],
                "priority_score": row[5],
                "reasoning": row[6],
                "external_quality": row[7],
                "external_cost": row[8],
                "external_speed": row[9],
                "already_tested": bool(row[10]),
                "created_at": row[11],
            })

        conn.close()

        context.logger.info(f"Retrieved {len(recommendations)} model recommendations")
        return recommendations

    async def execute(self, context: SharedContext) -> SharedContext:
        """Execute model selection analysis."""
        result = await self.analyze_and_recommend(context)
        context.payload["model_selection_result"] = result
        return context

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Tool definitions for model selection."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "get_recommendations",
                    "description": "Get intelligent model recommendations based on internal/external benchmark comparison. Returns priority-sorted list.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task_type": {
                                "type": "string",
                                "description": "Filter by task type (planning/reasoning/jules_validation/json_output/code_generation)",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum recommendations to return (default 10)",
                            },
                        },
                        "required": [],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_and_recommend",
                    "description": "Manually trigger model selection analysis. Normally runs automatically on heartbeat.",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                },
            },
        ]
