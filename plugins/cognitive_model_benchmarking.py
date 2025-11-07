"""
Cognitive Model Benchmarking Plugin

PURPOSE:
Continuously benchmark available LLM models to learn which models perform best
for different task types. Enables Sophia to make informed decisions about model
selection based on empirical performance data.

WORKFLOW:
1. Listen to PROACTIVE_HEARTBEAT events
2. Every N heartbeats (configurable), run benchmark suite
3. Test each available model on standardized task types:
   - planning (multi-step task planning)
   - reasoning (logical deduction)
   - code_generation (writing code)
   - jules_plan_validation (semantic comparison)
   - json_output (structured data generation)
4. Store results in SQLite database (model_benchmarks table)
5. Calculate model rankings per task type
6. Provide recommendations to cognitive_model_escalation

TASK TYPES TESTED:
- planning: "Create plan to add logging to auth.py"
- reasoning: "Does plan to modify test.py fix bug in auth.py?"
- code_generation: "Write function to validate email"
- jules_validation: "Is Jules plan appropriate for Sophia's task?"
- json_output: "Parse text and return JSON with fields"

DATABASE SCHEMA:
model_benchmarks (
    id INTEGER PRIMARY KEY,
    model_name TEXT,
    task_type TEXT,
    success BOOLEAN,
    quality_score REAL,
    latency_ms REAL,
    cost_usd REAL,
    timestamp TEXT,
    response_sample TEXT
)

CONFIGURATION (config/autonomy.yaml):
model_benchmarking:
  enabled: true
  heartbeat_interval: 24  # Run benchmark every 24 heartbeats (~24 hours if heartbeat=1h)
  models_to_test:
    local: ["qwen2.5:14b", "llama3.1:8b"]
    cloud: ["openrouter/deepseek/deepseek-chat"]
  timeout_seconds: 60
  store_full_responses: false  # Save disk space

AUTHOR: SOPHIA AMI 1.0 - Continuous Learning Enhancement
DATE: 2025-11-07
"""

import asyncio
import json
import logging
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType

logger = logging.getLogger(__name__)


# Test cases for each task type
BENCHMARK_TASKS = {
    "planning": {
        "prompt": """Create a step-by-step plan to add logging to the login() function in auth.py.
Output JSON: {"steps": ["step1", "step2", ...]}""",
        "expected_fields": ["steps"],
        "success_criteria": "valid_json_with_steps"
    },
    
    "reasoning": {
        "prompt": """Task: Fix timeout bug in benchmark_runner.py
Plan: Modify test_runner.py timeout from 30s to 60s

Question: Does this plan correctly implement the task?
Output JSON: {"correct": true/false, "reasoning": "why"}""",
        "expected_fields": ["correct", "reasoning"],
        "success_criteria": "correct_is_false"  # Plan has wrong file!
    },
    
    "jules_validation": {
        "prompt": """You are validating an AI coding plan.

TASK: Add authentication to /api/users endpoint
PLAN: 
- Add @require_auth decorator to /api/users route
- No tests included

Question: Should this plan be approved?
Output JSON: {"approved": true/false, "confidence": 0.0-1.0, "reasoning": "why"}""",
        "expected_fields": ["approved", "confidence", "reasoning"],
        "success_criteria": "should_reject_no_tests"  # Missing tests is dangerous!
    },
    
    "json_output": {
        "prompt": """Extract information from this text:
"John Doe, age 30, works as Software Engineer at TechCorp since 2020"

Output JSON: {"name": str, "age": int, "job": str, "company": str, "year": int}""",
        "expected_fields": ["name", "age", "job", "company", "year"],
        "success_criteria": "valid_json_with_all_fields"
    },
    
    "code_generation": {
        "prompt": """Write a Python function to validate email addresses.
Output ONLY the function code, no explanation.
Function name: validate_email
Return: True if valid, False otherwise""",
        "expected_fields": None,  # Free-form code
        "success_criteria": "contains_def_validate_email"
    }
}


class CognitiveModelBenchmarking(BasePlugin):
    """
    Continuous model benchmarking and learning system.
    
    Runs periodic benchmarks to build empirical knowledge about which models
    excel at which task types. This data informs model_escalation decisions.
    """
    
    def __init__(self):
        super().__init__()
        
        # Configuration (set in setup)
        self.enabled = False
        self.heartbeat_interval = 24  # Run every N heartbeats
        self.models_to_test = {
            "local": ["qwen2.5:14b", "llama3.1:8b"],
            "cloud": []  # Expensive, only if configured
        }
        self.timeout_seconds = 60
        self.store_full_responses = False
        
        # Runtime state
        self.heartbeat_count = 0
        self.db_path = Path(".data/model_benchmarks.db")
        self.last_benchmark_time = None
        
        # Plugin references
        self.event_bus = None
        self.local_llm_tool = None
        self.cloud_llm_tool = None
        
    @property
    def name(self) -> str:
        return "cognitive_model_benchmarking"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Initialize plugin and subscribe to heartbeat events."""
        logger.info("📊 Cognitive Model Benchmarking initializing...")
        
        # Load configuration
        autonomy_config = config.get("autonomy_config", {})
        benchmark_config = autonomy_config.get("model_benchmarking", {})
        
        self.enabled = benchmark_config.get("enabled", False)
        self.heartbeat_interval = benchmark_config.get("heartbeat_interval", 24)
        self.models_to_test = benchmark_config.get("models_to_test", self.models_to_test)
        self.timeout_seconds = benchmark_config.get("timeout_seconds", 60)
        self.store_full_responses = benchmark_config.get("store_full_responses", False)
        
        # Get plugin references
        all_plugins = config.get("all_plugins", {})
        self.local_llm_tool = all_plugins.get("tool_local_llm")
        self.cloud_llm_tool = all_plugins.get("tool_llm")
        self.event_bus = config.get("event_bus")
        
        # Initialize database
        self._init_database()
        
        # Subscribe to heartbeat events
        if self.enabled and self.event_bus:
            self.event_bus.subscribe(EventType.PROACTIVE_HEARTBEAT, self._on_heartbeat)
            logger.info(
                f"✅ Model Benchmarking enabled - will run every {self.heartbeat_interval} heartbeats"
            )
            logger.info(f"   Local models: {self.models_to_test.get('local', [])}")
            logger.info(f"   Cloud models: {self.models_to_test.get('cloud', [])}")
        else:
            logger.warning("⚠️  Model Benchmarking disabled in config")
    
    def _init_database(self) -> None:
        """Create database table for benchmark results."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                task_type TEXT NOT NULL,
                success INTEGER NOT NULL,
                quality_score REAL,
                latency_ms REAL,
                cost_usd REAL,
                error_message TEXT,
                response_sample TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        # Index for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_model_task 
            ON model_benchmarks(model_name, task_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON model_benchmarks(timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"📊 Benchmark database initialized: {self.db_path}")
    
    async def _on_heartbeat(self, event: Event) -> None:
        """Handle heartbeat event - run benchmark if interval reached."""
        self.heartbeat_count += 1
        
        if self.heartbeat_count % self.heartbeat_interval == 0:
            logger.info(
                f"🔔 Heartbeat #{self.heartbeat_count} - Running model benchmarks..."
            )
            
            try:
                await self._run_full_benchmark()
                self.last_benchmark_time = datetime.now()
            except Exception as e:
                logger.error(f"❌ Benchmark failed: {e}", exc_info=True)
    
    async def _run_full_benchmark(self) -> None:
        """Run complete benchmark suite on all configured models."""
        logger.info("=" * 80)
        logger.info("STARTING MODEL BENCHMARK SUITE")
        logger.info("=" * 80)
        
        # Collect all models to test
        all_models = []
        
        for model in self.models_to_test.get("local", []):
            all_models.append({"name": model, "type": "local"})
        
        for model in self.models_to_test.get("cloud", []):
            all_models.append({"name": model, "type": "cloud"})
        
        logger.info(f"Testing {len(all_models)} models on {len(BENCHMARK_TASKS)} task types")
        
        # Run benchmarks
        total_tests = len(all_models) * len(BENCHMARK_TASKS)
        completed = 0
        
        for model_config in all_models:
            logger.info(f"\n{'='*60}")
            logger.info(f"Model: {model_config['name']} ({model_config['type']})")
            logger.info(f"{'='*60}")
            
            for task_type, task_config in BENCHMARK_TASKS.items():
                completed += 1
                logger.info(f"\n[{completed}/{total_tests}] Task: {task_type}")
                
                result = await self._benchmark_model_on_task(
                    model_config["name"],
                    model_config["type"],
                    task_type,
                    task_config
                )
                
                # Store result
                self._store_result(result)
                
                # Log result
                if result["success"]:
                    logger.info(
                        f"   ✅ Success | Quality: {result['quality_score']:.1f}% | "
                        f"Time: {result['latency_ms']:.0f}ms"
                    )
                else:
                    logger.info(f"   ❌ Failed | Error: {result.get('error_message', 'Unknown')}")
        
        # Generate summary report
        logger.info("\n" + "=" * 80)
        logger.info("BENCHMARK SUMMARY")
        logger.info("=" * 80)
        
        summary = self._generate_summary()
        for line in summary:
            logger.info(line)
        
        logger.info("=" * 80)
    
    async def _benchmark_model_on_task(
        self,
        model_name: str,
        model_type: str,
        task_type: str,
        task_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Benchmark single model on single task type."""
        
        start_time = datetime.now()
        
        try:
            # Call appropriate LLM
            if model_type == "local":
                response = await self._call_local_model(model_name, task_config["prompt"])
            else:
                response = await self._call_cloud_model(model_name, task_config["prompt"])
            
            latency_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Evaluate response quality
            success, quality_score, error_msg = self._evaluate_response(
                response,
                task_config
            )
            
            # Estimate cost
            cost_usd = 0.0 if model_type == "local" else self._estimate_cost(model_name, response)
            
            # Sample for storage (truncate if needed)
            response_sample = response[:500] if self.store_full_responses else response[:100]
            
            return {
                "model_name": model_name,
                "model_type": model_type,
                "task_type": task_type,
                "success": success,
                "quality_score": quality_score,
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
                "error_message": error_msg,
                "response_sample": response_sample,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error benchmarking {model_name} on {task_type}: {e}")
            
            return {
                "model_name": model_name,
                "model_type": model_type,
                "task_type": task_type,
                "success": False,
                "quality_score": 0.0,
                "latency_ms": 0.0,
                "cost_usd": 0.0,
                "error_message": str(e),
                "response_sample": "",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _call_local_model(self, model: str, prompt: str) -> str:
        """Call local Ollama model directly."""
        if not self.local_llm_tool:
            raise ValueError("Local LLM tool not available")
        
        # Call via generate method
        response = await self.local_llm_tool.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1000
        )
        
        return response
    
    async def _call_cloud_model(self, model: str, prompt: str) -> str:
        """Call cloud model via tool_llm."""
        if not self.cloud_llm_tool:
            raise ValueError("Cloud LLM tool not available")
        
        # Create minimal context
        context = SharedContext(
            session_id="benchmark",
            current_state="testing",
            logger=logger,
            user_input=prompt
        )
        
        context.payload = {
            "messages": [{"role": "user", "content": prompt}],
            "model": model,
            "temperature": 0.1,
            "max_tokens": 1000
        }
        
        result_context = await self.cloud_llm_tool.execute(context)
        llm_response = result_context.payload.get("llm_response", {})
        
        return llm_response.get("content", "")
    
    def _evaluate_response(
        self,
        response: str,
        task_config: Dict[str, Any]
    ) -> Tuple[bool, float, Optional[str]]:
        """Evaluate response quality based on success criteria."""
        
        success_criteria = task_config["success_criteria"]
        expected_fields = task_config.get("expected_fields")
        
        try:
            # Try to extract JSON if expected
            if expected_fields:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                
                if json_start == -1 or json_end == 0:
                    return False, 0.0, "No JSON found in response"
                
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Check required fields
                missing = [f for f in expected_fields if f not in parsed]
                if missing:
                    return False, 30.0, f"Missing fields: {missing}"
                
                # Apply specific success criteria
                if success_criteria == "correct_is_false":
                    if parsed.get("correct") == False:
                        return True, 100.0, None
                    else:
                        return False, 40.0, "Should recognize wrong file in plan"
                
                elif success_criteria == "should_reject_no_tests":
                    if parsed.get("approved") == False and "test" in parsed.get("reasoning", "").lower():
                        return True, 100.0, None
                    else:
                        return False, 50.0, "Should reject plan without tests"
                
                elif success_criteria == "valid_json_with_all_fields":
                    return True, 100.0, None
                
                elif success_criteria == "valid_json_with_steps":
                    if isinstance(parsed.get("steps"), list) and len(parsed["steps"]) > 0:
                        return True, 100.0, None
                    else:
                        return False, 60.0, "Steps should be non-empty list"
                
                else:
                    # Default: JSON is valid and has all fields
                    return True, 100.0, None
            
            else:
                # Code generation task - check for function definition
                if success_criteria == "contains_def_validate_email":
                    if "def validate_email" in response:
                        return True, 100.0, None
                    else:
                        return False, 20.0, "Missing function definition"
                
                else:
                    # Unknown criteria
                    return True, 50.0, "Unknown success criteria - assumed OK"
        
        except json.JSONDecodeError as e:
            return False, 10.0, f"Invalid JSON: {e}"
        except Exception as e:
            return False, 0.0, f"Evaluation error: {e}"
    
    def _estimate_cost(self, model: str, response: str) -> float:
        """Estimate cost of cloud API call."""
        # Very rough estimation
        tokens = len(response.split()) + 100  # Add input tokens
        
        if "deepseek" in model.lower():
            cost_per_1m = 0.14
        elif "haiku" in model.lower():
            cost_per_1m = 0.25
        elif "sonnet" in model.lower():
            cost_per_1m = 3.00
        else:
            cost_per_1m = 1.00
        
        return (tokens / 1_000_000) * cost_per_1m
    
    def _store_result(self, result: Dict[str, Any]) -> None:
        """Store benchmark result in database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO model_benchmarks 
            (model_name, model_type, task_type, success, quality_score, latency_ms, 
             cost_usd, error_message, response_sample, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            result["model_name"],
            result["model_type"],
            result["task_type"],
            1 if result["success"] else 0,
            result["quality_score"],
            result["latency_ms"],
            result["cost_usd"],
            result.get("error_message"),
            result.get("response_sample"),
            result["timestamp"]
        ))
        
        conn.commit()
        conn.close()
    
    def _generate_summary(self) -> List[str]:
        """Generate summary report from recent benchmark results."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        lines = []
        
        # Get latest results per model per task
        cursor.execute("""
            SELECT 
                model_name,
                task_type,
                AVG(quality_score) as avg_quality,
                AVG(latency_ms) as avg_latency,
                SUM(success) * 100.0 / COUNT(*) as success_rate,
                COUNT(*) as sample_count
            FROM model_benchmarks
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY model_name, task_type
            ORDER BY model_name, task_type
        """)
        
        results = cursor.fetchall()
        
        if not results:
            lines.append("No recent benchmark data available")
            conn.close()
            return lines
        
        # Group by model
        current_model = None
        for row in results:
            model_name, task_type, avg_quality, avg_latency, success_rate, count = row
            
            if model_name != current_model:
                lines.append(f"\n{model_name}:")
                current_model = model_name
            
            lines.append(
                f"  {task_type:20s} | Quality: {avg_quality:5.1f}% | "
                f"Success: {success_rate:5.1f}% | Latency: {avg_latency:6.0f}ms | "
                f"Samples: {int(count)}"
            )
        
        # Best model per task type
        lines.append("\nBEST MODELS PER TASK TYPE:")
        
        for task_type in BENCHMARK_TASKS.keys():
            cursor.execute("""
                SELECT model_name, AVG(quality_score) as avg_quality
                FROM model_benchmarks
                WHERE task_type = ? AND timestamp > datetime('now', '-7 days')
                GROUP BY model_name
                ORDER BY avg_quality DESC
                LIMIT 1
            """, (task_type,))
            
            best = cursor.fetchone()
            if best:
                model, quality = best
                lines.append(f"  {task_type:20s} → {model} ({quality:.1f}%)")
        
        conn.close()
        return lines
    
    def get_best_model_for_task(self, task_type: str) -> Optional[str]:
        """
        Get best performing model for specific task type.
        
        This method is called by cognitive_model_escalation to get recommendations.
        """
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT model_name, AVG(quality_score) as avg_quality
            FROM model_benchmarks
            WHERE task_type = ? AND timestamp > datetime('now', '-30 days')
            GROUP BY model_name
            ORDER BY avg_quality DESC
            LIMIT 1
        """, (task_type,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """Execute - not used for heartbeat-driven plugin."""
        context.payload["info"] = "This plugin runs on heartbeat events"
        context.payload["last_benchmark"] = self.last_benchmark_time.isoformat() if self.last_benchmark_time else None
        context.payload["heartbeat_count"] = self.heartbeat_count
        context.payload["next_benchmark_in"] = self.heartbeat_interval - (self.heartbeat_count % self.heartbeat_interval)
        return context
