"""
Cognitive Reflection Plugin - Phase 3.3 (CRITICAL)

Purpose: Analyze failures from operation_tracking, identify patterns, generate improvement hypotheses

Event Flow:
  DREAM_COMPLETE → analyze recent failures → LLM root cause analysis → create hypotheses → HYPOTHESIS_CREATED
  SYSTEM_RECOVERY → prioritize crash analysis → immediate hypothesis generation

Key Features:
  - Failure clustering by operation_type
  - Expert LLM (cloud) for root cause analysis
  - Hypothesis generation with proposed fixes
  - Priority-based hypothesis queue
  - Rate limiting (max 10 hypotheses per cycle)
  - Crash prioritization (from SYSTEM_RECOVERY events)

Dependencies:
  - memory_sqlite (query failures, create hypotheses)
  - cognitive_task_router (cloud LLM routing)
  - event_bus (DREAM_COMPLETE, SYSTEM_RECOVERY, HYPOTHESIS_CREATED)
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from core.events import Event, EventType

logger = logging.getLogger(__name__)


class CognitiveReflection(BasePlugin):
    """
    Analyzes system failures and generates improvement hypotheses using Expert LLM.
    
    Workflow:
      1. Listen for DREAM_COMPLETE or SYSTEM_RECOVERY events
      2. Query operation_tracking for recent failures (last 7 days)
      3. Group failures by operation_type
      4. For each failure cluster:
         - Extract error patterns and context
         - Send to Expert LLM for root cause analysis
         - Parse hypothesis JSON response
         - Store in hypotheses table
         - Emit HYPOTHESIS_CREATED event
      5. Rate limit: max 10 hypotheses per dream cycle
    """

    def __init__(self):
        self.memory_plugin = None
        self.event_bus = None
        self.router_plugin = None
        self.max_hypotheses_per_cycle = 10
        self.analysis_window_days = 7
        self.min_failures_for_analysis = 3  # Need at least 3 failures to analyze pattern
        
    @property
    def name(self) -> str:
        return "cognitive_reflection"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """
        Subscribe to DREAM_COMPLETE and SYSTEM_RECOVERY events.
        Get references to memory and router plugins.
        """
        logger.info("🧠 Cognitive Reflection Plugin initializing...")
        
        # Get plugin references
        all_plugins = config.get("all_plugins", {})
        self.memory_plugin = all_plugins.get("memory_sqlite")
        self.router_plugin = all_plugins.get("cognitive_task_router")
        self.event_bus = config.get("event_bus")
        
        if not self.memory_plugin:
            logger.warning("⚠️  memory_sqlite plugin not found - hypotheses storage unavailable")
        
        if not self.router_plugin:
            logger.warning("⚠️  cognitive_task_router plugin not found - cloud LLM unavailable")
        
        if self.event_bus:
            # Subscribe to dream completion and system recovery events
            self.event_bus.subscribe(EventType.DREAM_COMPLETE, self._on_dream_complete)
            self.event_bus.subscribe(EventType.SYSTEM_RECOVERY, self._on_system_recovery)
            logger.info("✅ Subscribed to DREAM_COMPLETE and SYSTEM_RECOVERY events")
        else:
            logger.warning("⚠️  event_bus not available - event subscriptions skipped")
        
        # Load config
        self.max_hypotheses_per_cycle = config.get("max_hypotheses_per_cycle", 10)
        self.analysis_window_days = config.get("analysis_window_days", 7)
        self.min_failures_for_analysis = config.get("min_failures_for_analysis", 3)
        
        logger.info(f"📊 Configuration: max_hypotheses={self.max_hypotheses_per_cycle}, "
                   f"window={self.analysis_window_days}d, min_failures={self.min_failures_for_analysis}")
        
        logger.info("🧠 Cognitive Reflection Plugin ready")

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        This plugin is event-driven, not invoked directly.
        Returns context unchanged.
        """
        return context

    async def _on_dream_complete(self, event: Event):
        """
        Handle DREAM_COMPLETE event - analyze recent failures and generate hypotheses.
        """
        logger.info("🌙 DREAM_COMPLETE received - starting failure reflection...")
        
        try:
            # Get recent failures from operation_tracking
            failures = await self._get_recent_failures()
            
            if not failures:
                logger.info("✅ No failures in analysis window - system healthy!")
                return
            
            logger.info(f"📊 Found {len(failures)} failures in last {self.analysis_window_days} days")
            
            # Cluster failures by operation_type
            failure_clusters = self._cluster_failures(failures)
            
            logger.info(f"📦 Clustered into {len(failure_clusters)} operation types")
            
            # Analyze each cluster (up to max_hypotheses_per_cycle)
            hypotheses_created = 0
            
            for operation_type, failure_group in sorted(
                failure_clusters.items(),
                key=lambda x: len(x[1]),
                reverse=True  # Most frequent failures first
            ):
                if hypotheses_created >= self.max_hypotheses_per_cycle:
                    logger.info(f"⏸️  Rate limit reached ({self.max_hypotheses_per_cycle} hypotheses)")
                    break
                
                # Skip if too few failures to establish pattern
                if len(failure_group) < self.min_failures_for_analysis:
                    logger.debug(f"⏭️  Skipping {operation_type}: only {len(failure_group)} failures "
                               f"(min {self.min_failures_for_analysis})")
                    continue
                
                logger.info(f"🔍 Analyzing {operation_type}: {len(failure_group)} failures")
                
                # Generate hypothesis using LLM
                hypothesis_data = await self._analyze_failure_cluster(
                    operation_type,
                    failure_group,
                    source="dream_cycle"
                )
                
                if hypothesis_data:
                    # Store in database
                    hypothesis_id = await self._create_hypothesis(hypothesis_data)
                    
                    if hypothesis_id:
                        hypotheses_created += 1
                        logger.info(f"✅ Created hypothesis #{hypothesis_id}: {hypothesis_data['category']}")
                        
                        # Emit HYPOTHESIS_CREATED event
                        if self.event_bus:
                            self.event_bus.publish(Event(
                                EventType.HYPOTHESIS_CREATED,
                                data={
                                    "hypothesis_id": hypothesis_id,
                                    "category": hypothesis_data["category"],
                                    "priority": hypothesis_data["priority"],
                                    "source": "dream_cycle"
                                }
                            ))
            
            logger.info(f"🎉 Reflection complete: {hypotheses_created} hypotheses created")
            
        except Exception as e:
            logger.error(f"❌ Error during dream reflection: {e}", exc_info=True)

    async def _on_system_recovery(self, event: Event):
        """
        Handle SYSTEM_RECOVERY event - prioritize crash analysis.
        """
        logger.info("🚨 SYSTEM_RECOVERY received - analyzing crash...")
        
        try:
            crash_log = event.data.get("crash_log", "")
            
            if not crash_log:
                logger.warning("⚠️  No crash log in SYSTEM_RECOVERY event")
                return
            
            logger.info(f"📝 Crash log length: {len(crash_log)} chars")
            
            # Analyze crash with high priority
            hypothesis_data = await self._analyze_crash(crash_log)
            
            if hypothesis_data:
                # Force high priority for crashes
                hypothesis_data["priority"] = 95
                hypothesis_data["category"] = "code_fix"
                
                # Store in database
                hypothesis_id = await self._create_hypothesis(hypothesis_data)
                
                if hypothesis_id:
                    logger.info(f"✅ Created CRITICAL crash hypothesis #{hypothesis_id}")
                    
                    # Emit HYPOTHESIS_CREATED event with crash flag
                    if self.event_bus:
                        self.event_bus.publish(Event(
                            EventType.HYPOTHESIS_CREATED,
                            data={
                                "hypothesis_id": hypothesis_id,
                                "category": "code_fix",
                                "priority": 95,
                                "source": "system_recovery",
                                "is_crash": True
                            }
                        ))
            
        except Exception as e:
            logger.error(f"❌ Error during crash reflection: {e}", exc_info=True)

    async def _get_recent_failures(self) -> List[Dict]:
        """
        Query operation_tracking for failures in the last N days.
        
        Returns list of failure records with:
          - operation_type, timestamp, error_msg, context, model_used
        """
        if not self.memory_plugin:
            logger.warning("⚠️  memory_sqlite not available - cannot query failures")
            return []
        
        try:
            # Calculate cutoff date
            cutoff = (datetime.now() - timedelta(days=self.analysis_window_days)).isoformat()
            
            # Query via memory plugin (if it has query method)
            # For now, we'll use direct SQL access
            from sqlalchemy import select
            
            with self.memory_plugin.engine.connect() as conn:
                result = conn.execute(
                    select(self.memory_plugin.operation_tracking_table).where(
                        self.memory_plugin.operation_tracking_table.c.success == False,
                        self.memory_plugin.operation_tracking_table.c.timestamp >= cutoff
                    )
                )
                
                failures = []
                for row in result:
                    failures.append({
                        "id": row.id,
                        "operation_type": row.operation_type,
                        "timestamp": row.timestamp,
                        "error_msg": row.error_message or "Unknown error",
                        "context": row.raw_metadata or "{}",
                        "model_used": row.model_used or "unknown",
                        "offline_mode": row.offline_mode
                    })
                
                return failures
                
        except Exception as e:
            logger.error(f"❌ Error querying failures: {e}", exc_info=True)
            return []

    def _cluster_failures(self, failures: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group failures by operation_type.
        
        Returns dict: {operation_type: [failure1, failure2, ...]}
        """
        clusters = defaultdict(list)
        
        for failure in failures:
            operation_type = failure.get("operation_type", "unknown")
            clusters[operation_type].append(failure)
        
        return dict(clusters)

    async def _analyze_failure_cluster(
        self,
        operation_type: str,
        failures: List[Dict],
        source: str
    ) -> Optional[Dict]:
        """
        Analyze a cluster of failures using Expert LLM (cloud).
        
        Returns hypothesis data dict or None if analysis fails.
        """
        try:
            # Extract error patterns
            error_samples = []
            context_samples = []
            models_used = set()
            offline_count = 0
            
            for failure in failures[:10]:  # Max 10 samples to avoid token limit
                error_samples.append(failure.get("error_msg", ""))
                context_samples.append(failure.get("context", "{}"))
                models_used.add(failure.get("model_used", "unknown"))
                if failure.get("offline_mode"):
                    offline_count += 1
            
            # Calculate success rate (approximate - need total operations)
            failure_count = len(failures)
            
            # Build analysis prompt
            prompt = self._build_analysis_prompt(
                operation_type=operation_type,
                failure_count=failure_count,
                error_samples=error_samples,
                context_samples=context_samples,
                models_used=list(models_used),
                offline_count=offline_count
            )
            
            logger.debug(f"📝 Analysis prompt length: {len(prompt)} chars")
            
            # Send to Expert LLM via router (force cloud LLM)
            hypothesis_json = await self._call_expert_llm(prompt)
            
            if not hypothesis_json:
                logger.warning(f"⚠️  No hypothesis generated for {operation_type}")
                return None
            
            # Parse and validate
            hypothesis_data = self._parse_hypothesis_response(hypothesis_json, operation_type, source)
            
            # Add source failure IDs
            hypothesis_data["source_failure_ids"] = [f["id"] for f in failures[:5]]
            
            return hypothesis_data
            
        except Exception as e:
            logger.error(f"❌ Error analyzing {operation_type}: {e}", exc_info=True)
            return None

    async def _analyze_crash(self, crash_log: str) -> Optional[Dict]:
        """
        Analyze crash log using Expert LLM.
        """
        try:
            # Build crash analysis prompt
            prompt = f"""Jsi expert na debugging Python systémů. Analyzuj tento crash log:

CRASH LOG:
{crash_log[:2000]}  # Limit to first 2000 chars

ÚKOL:
1. Identifikuj ROOT CAUSE (ne symptom!)
2. Navrhni KONKRÉTNÍ FIX (změna kódu)
3. Odhadni IMPACT (high/medium/low)

Vrať JSON:
{{
  "root_cause": "...",
  "hypothesis": "...",
  "proposed_fix": "...",
  "fix_type": "code_fix",
  "priority": 95,
  "estimated_improvement": "..."
}}

POUZE JSON, žádný další text!"""

            # Call Expert LLM
            hypothesis_json = await self._call_expert_llm(prompt)
            
            if not hypothesis_json:
                return None
            
            # Parse response
            hypothesis_data = self._parse_hypothesis_response(hypothesis_json, "crash_recovery", "system_recovery")
            
            return hypothesis_data
            
        except Exception as e:
            logger.error(f"❌ Error analyzing crash: {e}", exc_info=True)
            return None

    def _build_analysis_prompt(
        self,
        operation_type: str,
        failure_count: int,
        error_samples: List[str],
        context_samples: List[str],
        models_used: List[str],
        offline_count: int
    ) -> str:
        """
        Build analysis prompt for Expert LLM.
        """
        # Truncate error samples
        error_text = "\n".join([f"- {err[:200]}" for err in error_samples[:5]])
        
        prompt = f"""Jsi expert na debugging AI systémů. Analyzuj tyto selhání:

OPERACE: {operation_type}
POČET SELHÁNÍ: {failure_count} za posledních 7 dní

PŘÍKLADY CHYB:
{error_text}

KONTEXT:
- Modely použité: {', '.join(models_used)}
- Offline režim: {offline_count}/{failure_count} případů

ÚKOL:
1. Identifikuj ROOT CAUSE (ne symptom!)
2. Navrhni KONKRÉTNÍ FIX (změna kódu, prompt, config, nebo model)
3. Odhadni IMPACT (kolik % zlepšení)

⚠️ DŮLEŽITÉ PRO PROMPT OPTIMIZATION:
Pokud fix_type="prompt_optimization", pak "proposed_fix" MUSÍ obsahovat KOMPLETNÍ nový prompt text,
NIKOLI jen popis změny! Musí to být ready-to-deploy prompt který můžeme okamžitě použít v produkci.

Vrať JSON:
{{
  "root_cause": "...",
  "hypothesis": "...",
  "proposed_fix": "...",
  "fix_type": "code_fix|prompt_optimization|config_tuning|model_change",
  "priority": 1-100,
  "estimated_improvement": "XX%"
}}

POUZE JSON, žádný další text!"""

        return prompt

    async def _call_expert_llm(self, prompt: str) -> Optional[str]:
        """
        Call Expert LLM with intelligent escalation strategy.
        
        Strategy:
          Level 1: llama3.1:8b (3 attempts) - FREE
          Level 2: llama3.1:70b (3 attempts) - FREE (if available)
          Level 3: gpt-4o-mini (1 attempt) - $0.005
          Level 4: claude-3.5-sonnet (1 attempt) - $0.015
        
        Returns best response or None if all fail.
        """
        if not self.router_plugin:
            logger.warning("⚠️  cognitive_task_router not available - cannot call LLM")
            return None
        
        # Escalation tiers
        escalation_tiers = [
            # Tier 1: Local 8B model (3 attempts)
            {"model": "llama3.1:8b", "attempts": 3, "cost": 0.0, "provider": "ollama"},
            # Tier 2: Local 70B model (3 attempts) - if available
            {"model": "llama3.1:70b", "attempts": 3, "cost": 0.0, "provider": "ollama"},
            # Tier 3: Cloud mini (1 attempt)
            {"model": "openrouter/openai/gpt-4o-mini", "attempts": 1, "cost": 0.005, "provider": "cloud"},
            # Tier 4: Cloud premium (1 attempt)
            {"model": "openrouter/anthropic/claude-3.5-sonnet", "attempts": 1, "cost": 0.015, "provider": "cloud"}
        ]
        
        best_response = None
        total_cost = 0.0
        
        for tier_idx, tier in enumerate(escalation_tiers):
            model = tier["model"]
            max_attempts = tier["attempts"]
            tier_cost = tier["cost"]
            provider = tier["provider"]
            
            logger.info(f"🔄 Escalation Tier {tier_idx + 1}: {model} ({max_attempts} attempts, ${tier_cost:.3f})")
            
            for attempt in range(max_attempts):
                try:
                    # Create context for LLM call
                    context = SharedContext(
                        session_id="reflection_analysis",
                        current_state="reflection",
                        user_input=prompt,
                        logger=logger
                    )
                    
                    # Force specific model
                    context.payload["force_model"] = model
                    context.payload["force_cloud"] = (provider == "cloud")
                    context.payload["complexity"] = 10  # High complexity
                    
                    # Route via cognitive_task_router
                    result_context = await self.router_plugin.execute(context)
                    
                    # Extract LLM response
                    response = result_context.payload.get("llm_response", "")
                    
                    if not response:
                        logger.warning(f"⚠️  Empty response (attempt {attempt + 1}/{max_attempts})")
                        continue
                    
                    # Validate JSON structure
                    if self._validate_hypothesis_json(response):
                        logger.info(f"✅ Tier {tier_idx + 1} SUCCESS on attempt {attempt + 1}")
                        total_cost += tier_cost
                        
                        # Log budget savings
                        max_cost = sum(t["cost"] * t["attempts"] for t in escalation_tiers)
                        savings = max_cost - total_cost
                        savings_pct = (savings / max_cost * 100) if max_cost > 0 else 0
                        
                        logger.info(f"💰 Cost: ${total_cost:.3f} (saved ${savings:.3f} = {savings_pct:.0f}%)")
                        
                        return response
                    else:
                        logger.warning(f"⚠️  Invalid JSON (attempt {attempt + 1}/{max_attempts})")
                        best_response = response  # Keep as fallback
                        
                except Exception as e:
                    logger.warning(f"⚠️  Attempt {attempt + 1} failed: {e}")
                    continue
            
            # If all attempts in tier failed, escalate to next tier
            logger.warning(f"❌ Tier {tier_idx + 1} exhausted, escalating...")
        
        # All tiers exhausted
        if best_response:
            logger.warning(f"⚠️  Using best available response (may have invalid JSON)")
            return best_response
        
        logger.error(f"❌ All escalation tiers failed")
        return None
    
    def _validate_hypothesis_json(self, response: str) -> bool:
        """
        Quick validation of hypothesis JSON structure.
        Returns True if response looks like valid hypothesis JSON.
        """
        try:
            # Remove markdown
            json_str = response.strip()
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            json_str = json_str.strip()
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Check required fields
            required = ["root_cause", "hypothesis", "proposed_fix", "fix_type"]
            return all(field in data for field in required)
            
        except (json.JSONDecodeError, TypeError):
            return False

    def _parse_hypothesis_response(
        self,
        response: str,
        operation_type: str,
        source: str
    ) -> Dict:
        """
        Parse LLM JSON response and validate structure.
        """
        try:
            # Try to extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            
            if json_str.startswith("```json"):
                json_str = json_str[7:]
            if json_str.startswith("```"):
                json_str = json_str[3:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
            
            json_str = json_str.strip()
            
            # Parse JSON
            data = json.loads(json_str)
            
            # Validate required fields
            required = ["root_cause", "hypothesis", "proposed_fix", "fix_type", "priority"]
            for field in required:
                if field not in data:
                    logger.warning(f"⚠️  Missing field in hypothesis: {field}")
                    data[field] = "N/A" if field != "priority" else 50
            
            # Map fix_type to category
            fix_type_map = {
                "code_fix": "code_fix",
                "prompt_optimization": "prompt_optimization",
                "config_tuning": "config_tuning",
                "model_change": "model_change"
            }
            
            data["category"] = fix_type_map.get(data["fix_type"], "code_fix")
            
            # Ensure priority is int
            data["priority"] = int(data.get("priority", 50))
            
            # Add metadata
            data["operation_type"] = operation_type
            data["source"] = source
            
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON from LLM: {e}")
            logger.debug(f"Response was: {response[:500]}")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing hypothesis: {e}", exc_info=True)
            return None

    async def _create_hypothesis(self, hypothesis_data: Dict) -> Optional[int]:
        """
        Store hypothesis in database using memory_sqlite.create_hypothesis()
        """
        if not self.memory_plugin:
            logger.warning("⚠️  memory_sqlite not available - cannot store hypothesis")
            return None
        
        try:
            hypothesis_id = self.memory_plugin.create_hypothesis(
                hypothesis_text=hypothesis_data.get("hypothesis", ""),
                category=hypothesis_data.get("category", "code_fix"),
                priority=hypothesis_data.get("priority", 50),
                source_failure_id=hypothesis_data.get("source_failure_ids", [None])[0],
                root_cause=hypothesis_data.get("root_cause"),
                proposed_fix=hypothesis_data.get("proposed_fix"),
                estimated_improvement=hypothesis_data.get("estimated_improvement")
            )
            
            return hypothesis_id
            
        except Exception as e:
            logger.error(f"❌ Error creating hypothesis: {e}", exc_info=True)
            return None
