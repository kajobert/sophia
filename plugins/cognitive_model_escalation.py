"""
Cognitive Model Escalation Plugin - Intelligent Multi-Tier LLM Selection

PURPOSE:
Automatically escalate between local and cloud LLMs based on task complexity and success rate.
Learn from failures and optimize model selection over time.

WORKFLOW:
1. Try local model (llama3.1:8b) up to 3 times
2. Evaluate each attempt (quality score 0-100%)
3. If avg success < 70% → escalate to tier 2 (qwen2.5:14b)
4. If tier 2 fails → escalate to tier 3 (cloud: gemini-flash-1.5)
5. Log all attempts to database for self-tuning analysis
6. During sleep, reflection analyzes patterns and creates hypotheses

TIERS:
- Tier 1: llama3.1:8b (fast, cheap, most tasks)
- Tier 2: qwen2.5:14b (better reasoning, complex tasks)
- Tier 3: Cloud LLM (premium quality, fallback only)

METRICS TRACKED:
- Task type (planning, reasoning, creative, factual)
- Model used for each attempt
- Success rate per model per task type
- Response quality score
- Latency
- Escalation triggers

AUTHOR: SOPHIA AMI 1.0
DATE: 2025-11-07
"""

import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType

logger = logging.getLogger(__name__)


@dataclass
class AttemptMetrics:
    """Metrics for a single LLM attempt"""
    model: str
    tier: int
    success: bool
    quality_score: float  # 0-100%
    latency_ms: float
    error: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class CognitiveModelEscalation(BasePlugin):
    """
    Intelligent model selection with automatic escalation and learning.
    """
    
    def __init__(self):
        # Model tier configuration
        self.tier_config = {
            1: {"model": "llama3.1:8b", "max_retries": 3, "tool_name": "tool_local_llm"},
            2: {"model": "qwen2.5:14b", "max_retries": 2, "tool_name": "tool_local_llm"},
            3: {"model": "gemini-flash-1.5", "max_retries": 1, "tool_name": "tool_llm"}
        }
        
        # Escalation thresholds
        self.min_success_rate = 0.70  # 70% avg quality to avoid escalation
        self.quality_threshold = 60.0  # Minimum quality score (0-100)
        
        # Plugin references
        self.memory_plugin = None
        self.event_bus = None
        
        # Runtime state
        self.attempt_history: List[AttemptMetrics] = []
        self.task_type_stats: Dict[str, Dict[str, Any]] = {}
        
        self.logger = logging.getLogger(__name__)
    
    @property
    def name(self) -> str:
        return "cognitive_model_escalation"
    
    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def setup(self, config: Dict[str, Any]) -> None:
        """Initialize plugin and load historical stats"""
        self.logger.info("🎯 Cognitive Model Escalation initializing...")
        
        # Get plugin references
        all_plugins = config.get("all_plugins", {})
        self.memory_plugin = all_plugins.get("memory_sqlite")
        self.event_bus = config.get("event_bus")
        
        # Load config overrides
        self.min_success_rate = config.get("min_success_rate", 0.70)
        self.quality_threshold = config.get("quality_threshold", 60.0)
        
        # Load historical stats from database
        if self.memory_plugin:
            self._load_historical_stats()
        
        self.logger.info(f"✅ Model Escalation ready (threshold: {self.min_success_rate*100}%)")
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Main execution method - try models with escalation.
        
        This is called by planner/executor when they need LLM with auto-escalation.
        """
        task_type = context.payload.get("task_type", "general")
        self.logger.info(f"🎯 [Escalation] Task type: {task_type}")
        
        # Try each tier until success
        for tier in [1, 2, 3]:
            tier_cfg = self.tier_config[tier]
            max_retries = tier_cfg["max_retries"]
            
            self.logger.info(f"🔄 [Escalation] Trying Tier {tier}: {tier_cfg['model']} (up to {max_retries} attempts)")
            
            tier_attempts = []
            for attempt in range(max_retries):
                result, metrics = await self._try_model(
                    tier=tier,
                    tier_config=tier_cfg,
                    context=context,
                    attempt=attempt + 1
                )
                
                tier_attempts.append(metrics)
                self.attempt_history.append(metrics)
                
                # Check if this attempt succeeded
                if result and metrics.quality_score >= self.quality_threshold:
                    self.logger.info(f"✅ [Escalation] Success with {tier_cfg['model']} (quality: {metrics.quality_score:.1f}%)")
                    self._log_success(task_type, tier, tier_attempts)
                    context.payload["llm_response"] = result
                    context.payload["model_used"] = tier_cfg["model"]
                    context.payload["tier"] = tier
                    return context
            
            # Calculate tier average quality
            avg_quality = sum(m.quality_score for m in tier_attempts) / len(tier_attempts)
            self.logger.warning(f"⚠️  [Escalation] Tier {tier} avg quality: {avg_quality:.1f}% (threshold: {self.min_success_rate*100}%)")
            
            # If tier 3 failed, we're out of options
            if tier == 3:
                self.logger.error(f"❌ [Escalation] All tiers failed")
                self._log_failure(task_type, tier_attempts)
                context.payload["error"] = "All model tiers exhausted"
                return context
            
            # Escalate to next tier
            self.logger.info(f"🔼 [Escalation] Escalating to Tier {tier + 1}")
        
        return context
    
    async def _try_model(
        self, 
        tier: int, 
        tier_config: Dict[str, Any],
        context: SharedContext,
        attempt: int
    ) -> Tuple[Optional[str], AttemptMetrics]:
        """
        Try a single model and return (result, metrics).
        """
        model = tier_config["model"]
        tool_name = tier_config["tool_name"]
        
        start_time = time.time()
        
        try:
            # Get all plugins from kernel
            all_plugins = context.payload.get("all_plugins", {})
            
            # Override model for local LLM BEFORE getting the tool
            original_model = None
            if tool_name == "tool_local_llm":
                import os
                original_model = os.getenv("LOCAL_LLM_MODEL")
                os.environ["LOCAL_LLM_MODEL"] = model
                self.logger.info(f"   🔧 Model override: {original_model} → {model}")
            
            # Get the LLM tool
            tool_plugin = all_plugins.get(tool_name)
            if not tool_plugin:
                raise RuntimeError(f"Tool {tool_name} not available in all_plugins")
            
            # Execute LLM call with current context
            result_context = await tool_plugin.execute(context)
            result = result_context.payload.get("llm_response")
            
            # Restore original model
            if tool_name == "tool_local_llm":
                import os
                if original_model:
                    os.environ["LOCAL_LLM_MODEL"] = original_model
                else:
                    # If no original, restore default
                    os.environ["LOCAL_LLM_MODEL"] = "llama3.1:8b"
            
            # Calculate quality score
            quality_score = self._evaluate_quality(result, context)
            
            latency_ms = (time.time() - start_time) * 1000
            
            metrics = AttemptMetrics(
                model=model,
                tier=tier,
                success=True,
                quality_score=quality_score,
                latency_ms=latency_ms
            )
            
            self.logger.info(f"   Attempt {attempt}: quality={quality_score:.1f}%, latency={latency_ms:.0f}ms")
            
            return result, metrics
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            
            metrics = AttemptMetrics(
                model=model,
                tier=tier,
                success=False,
                quality_score=0.0,
                latency_ms=latency_ms,
                error=str(e)
            )
            
            self.logger.error(f"   Attempt {attempt} failed: {e}")
            
            return None, metrics
    
    def _evaluate_quality(self, response: Optional[str], context: SharedContext) -> float:
        """
        Evaluate response quality (0-100%).
        
        Heuristics:
        - Has response: +30%
        - Length appropriate: +20%
        - Contains expected keywords: +30%
        - Valid JSON (if expected): +20%
        """
        if not response:
            return 0.0
        
        score = 30.0  # Base score for having a response
        
        # Length check
        if 50 < len(response) < 5000:
            score += 20.0
        elif len(response) >= 5000:
            score += 10.0
        
        # Keyword relevance (simple heuristic)
        task_type = context.payload.get("task_type", "general")
        user_input = context.user_input or ""
        
        # Extract key terms from user input
        important_words = [w for w in user_input.lower().split() if len(w) > 4]
        if important_words:
            matches = sum(1 for word in important_words if word in response.lower())
            relevance = min(matches / len(important_words), 1.0)
            score += relevance * 30.0
        else:
            score += 15.0  # Default partial score
        
        # JSON validity check (if planning task)
        if task_type == "planning":
            try:
                import json
                json.loads(response)
                score += 20.0
            except:
                pass
        else:
            score += 10.0  # Partial score for non-JSON tasks
        
        return min(score, 100.0)
    
    def _log_success(self, task_type: str, tier: int, attempts: List[AttemptMetrics]):
        """Log successful completion for learning"""
        if not self.memory_plugin:
            return
        
        try:
            metrics_data = {
                "task_type": task_type,
                "tier": tier,
                "attempts": len(attempts),
                "avg_quality": sum(a.quality_score for a in attempts) / len(attempts),
                "total_latency_ms": sum(a.latency_ms for a in attempts),
                "timestamp": datetime.now().isoformat()
            }
            
            # Store in operation_tracking table
            self.memory_plugin.track_operation(
                operation_type="model_escalation_success",
                status="success",
                details=metrics_data
            )
            
        except Exception as e:
            self.logger.error(f"Failed to log success: {e}")
    
    def _log_failure(self, task_type: str, all_attempts: List[AttemptMetrics]):
        """Log failure for reflection analysis"""
        if not self.memory_plugin:
            return
        
        try:
            metrics_data = {
                "task_type": task_type,
                "total_attempts": len(all_attempts),
                "tiers_tried": list(set(a.tier for a in all_attempts)),
                "best_quality": max(a.quality_score for a in all_attempts) if all_attempts else 0,
                "errors": [a.error for a in all_attempts if a.error],
                "timestamp": datetime.now().isoformat()
            }
            
            # Store for reflection plugin to analyze
            self.memory_plugin.track_operation(
                operation_type="model_escalation_failure",
                status="failed",
                details=metrics_data
            )
            
            # Emit event for immediate reflection (critical failure)
            if self.event_bus:
                self.event_bus.publish(Event(
                    event_type=EventType.SYSTEM_RECOVERY,
                    data={
                        "error_type": "model_escalation_exhausted",
                        "task_type": task_type,
                        "attempts": len(all_attempts)
                    }
                ))
            
        except Exception as e:
            self.logger.error(f"Failed to log failure: {e}")
    
    def _load_historical_stats(self):
        """Load historical success rates from database"""
        try:
            # Query operation_tracking for past escalations
            # This would use memory_plugin.query_operations()
            # For now, initialize empty stats
            self.task_type_stats = {}
            self.logger.info("📊 Historical stats loaded")
        except Exception as e:
            self.logger.warning(f"Could not load historical stats: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current escalation statistics"""
        return {
            "total_attempts": len(self.attempt_history),
            "tier_usage": {
                tier: len([a for a in self.attempt_history if a.tier == tier])
                for tier in [1, 2, 3]
            },
            "avg_quality_by_tier": {
                tier: sum(a.quality_score for a in self.attempt_history if a.tier == tier) / 
                      len([a for a in self.attempt_history if a.tier == tier])
                for tier in [1, 2, 3]
                if [a for a in self.attempt_history if a.tier == tier]
            }
        }
