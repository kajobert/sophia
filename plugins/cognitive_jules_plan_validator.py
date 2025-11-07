"""
Cognitive Jules Plan Validator Plugin

Uses powerful local LLM to semantically validate if Jules plan matches Sophia's intent.
NO simple keyword filtering - true semantic understanding.

Critical for preventing wasted Jules API quota (max 100 tasks/day).
"""

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import json


class PlanValidationRequest(BaseModel):
    """Request for plan validation"""

    sophia_task: str = Field(..., description="Original task from Sophia")
    jules_plan: Dict[str, Any] = Field(..., description="Plan from Jules API")
    session_id: str = Field(..., description="Jules session ID for reference")


class PlanValidationResult(BaseModel):
    """Result of plan validation"""

    approved: bool = Field(..., description="Should plan be approved?")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    reasoning: str = Field(..., description="Why approved/rejected")
    risks: List[str] = Field(default_factory=list, description="Identified risks")
    recommendations: List[str] = Field(
        default_factory=list, description="Suggestions for improvement"
    )


class JulesPlanValidatorPlugin(BasePlugin):
    """
    Validates Jules plans using cloud LLM (NOT local).

    Workflow:
    1. Sophia creates task for Jules
    2. Jules generates plan
    3. THIS PLUGIN validates if plan matches Sophia's intent
    4. If approved → Jules executes
    5. If rejected → Task quota NOT wasted

    Uses CLOUD LLM for reliability:
    - Local models (8B) proven insufficient for multi-step reasoning
    - Cloud models (DeepSeek $0.14/1M, Claude Haiku $0.25/1M) reliable
    - Cost: ~$0.0001 per validation vs hours of wasted Jules tasks
    - See: docs/benchmarks/ for empirical data
    """

    def __init__(self):
        super().__init__()
        self.logger = None
        self.tool_cloud_llm = None  # For cloud LLM (DeepSeek, Claude, etc)
        self.benchmarking_plugin = None  # Optional: for model selection

    @property
    def name(self) -> str:
        return "cognitive_jules_plan_validator"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.COGNITIVE

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config):
        """Inject dependencies"""
        self.logger = config.get("logger")

        if not self.logger:
            raise ValueError(
                "Logger must be provided in config - dependency injection required"
            )

        all_plugins = config.get("all_plugins", {})

        # Inject CLOUD LLM tool (NOT local - local models fail at multi-step reasoning!)
        # See: V1_V2_TEST_RESULTS.md - "8B models not strong enough for multi-step reasoning"
        # Cost: ~$0.0001 per validation vs hours of wasted Jules tasks
        self.tool_cloud_llm = all_plugins.get("tool_llm")
        if not self.tool_cloud_llm:
            self.logger.error("tool_llm (cloud) not found - plan validation disabled!")
            raise ValueError("tool_llm required for plan validation")

        # OPTIONAL: Get benchmarking plugin for model selection
        self.benchmarking_plugin = all_plugins.get("cognitive_model_benchmarking")

        self.logger.info("✅ Jules Plan Validator ready - using CLOUD LLM for reliability")

    def _build_validation_prompt(
        self, sophia_task: str, jules_plan: Dict[str, Any]
    ) -> str:
        """
        Build prompt for LLM to validate plan.

        Critical: This prompt MUST produce structured JSON output.
        """
        # Extract plan details
        plan_summary = jules_plan.get("summary", "")
        plan_steps = jules_plan.get("steps", [])
        plan_files = jules_plan.get("files", [])

        # Build structured prompt
        prompt = f"""You are a senior software architect validating an AI coding assistant's plan.

TASK FROM SOPHIA (what she wants):
{sophia_task}

JULES PLAN (what Jules will do):
Summary: {plan_summary}

Steps:
{json.dumps(plan_steps, indent=2)}

Files to modify:
{json.dumps(plan_files, indent=2)}

YOUR JOB:
Analyze if Jules plan correctly implements Sophia's task.

Consider:
1. Does plan address the core task requirement?
2. Are the file modifications appropriate?
3. Are there any dangerous operations? (.env deletion, rm -rf, DROP TABLE, etc.)
4. Is scope reasonable? (not too broad/narrow)
5. Are there missing critical steps?

OUTPUT FORMAT (MUST be valid JSON):
{{
  "approved": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Clear explanation of why approved/rejected",
  "risks": ["list", "of", "identified", "risks"],
  "recommendations": ["list", "of", "suggestions"]
}}

CRITICAL: Output ONLY the JSON object, NO other text.
"""
        return prompt

    async def validate_plan(
        self,
        context: SharedContext,
        sophia_task: str,
        jules_plan: Dict[str, Any],
        session_id: str,
    ) -> PlanValidationResult:
        """
        Validate Jules plan using powerful local LLM.

        Args:
            context: Shared execution context
            sophia_task: Original task from Sophia
            jules_plan: Plan from Jules (with steps, files, summary)
            session_id: Jules session ID (for logging)

        Returns:
            PlanValidationResult with approval decision and reasoning

        Example:
            >>> result = await validate_plan(
            ...     context,
            ...     sophia_task="Fix benchmark runner bug",
            ...     jules_plan={"summary": "...", "steps": [...], "files": [...]},
            ...     session_id="sessions/abc123"
            ... )
            >>> if result.approved:
            ...     jules_tool.approve_plan(context, session_id)
        """
        try:
            request = PlanValidationRequest(
                sophia_task=sophia_task,
                jules_plan=jules_plan,
                session_id=session_id,
            )
        except Exception as e:
            context.logger.error(f"Invalid validation request: {e}")
            # Fail safe: reject if validation fails
            return PlanValidationResult(
                approved=False,
                confidence=0.0,
                reasoning=f"Validation request error: {e}",
                risks=["Validation system error"],
                recommendations=["Fix validation system before approving"],
            )

        if not self.tool_cloud_llm:
            context.logger.error("Cloud LLM not available - cannot validate plan!")
            return PlanValidationResult(
                approved=False,
                confidence=0.0,
                reasoning="Cloud LLM not available for validation",
                risks=["No validation possible"],
                recommendations=["Setup tool_llm plugin"],
            )

        context.logger.info(f"🔍 Validating Jules plan for session {session_id}...")

        # Determine best model for jules_validation task
        model = "openrouter/deepseek/deepseek-chat"  # Default: cheap and reliable
        
        if self.benchmarking_plugin:
            # Use benchmark data to select best model
            best_model = self.benchmarking_plugin.get_best_model_for_task("jules_validation")
            if best_model and "cloud" in best_model or "openrouter" in best_model:
                model = best_model
                context.logger.info(f"📊 Using benchmark-recommended model: {model}")

        # Build validation prompt
        prompt = self._build_validation_prompt(request.sophia_task, request.jules_plan)

        # Call cloud LLM
        try:
            # Create context for cloud LLM
            llm_context = SharedContext(
                session_id=session_id,
                current_state="validating_jules_plan",
                logger=context.logger,
                user_input=prompt
            )
            
            llm_context.payload = {
                "messages": [{"role": "user", "content": prompt}],
                "model": model,
                "temperature": 0.1,  # Low temperature for consistency
                "max_tokens": 1000,
            }
            
            result_context = await self.tool_cloud_llm.execute(llm_context)
            llm_response = result_context.payload.get("llm_response", {})
            llm_text = llm_response.get("content", "")
            context.logger.info(f"📋 LLM validation response: {llm_text[:200]}...")

            # Parse JSON response
            try:
                # Try to extract JSON from response
                # Handle case where LLM adds extra text
                json_start = llm_text.find("{")
                json_end = llm_text.rfind("}") + 1

                if json_start == -1 or json_end == 0:
                    raise ValueError("No JSON found in LLM response")

                json_str = llm_text[json_start:json_end]
                validation_data = json.loads(json_str)

                # Validate structure
                result = PlanValidationResult(
                    approved=validation_data.get("approved", False),
                    confidence=validation_data.get("confidence", 0.0),
                    reasoning=validation_data.get("reasoning", "No reasoning provided"),
                    risks=validation_data.get("risks", []),
                    recommendations=validation_data.get("recommendations", []),
                )

                # Log decision
                if result.approved:
                    context.logger.info(
                        f"✅ Plan APPROVED (confidence: {result.confidence:.2f})"
                    )
                    context.logger.info(f"   Reasoning: {result.reasoning}")
                else:
                    context.logger.warning(
                        f"❌ Plan REJECTED (confidence: {result.confidence:.2f})"
                    )
                    context.logger.warning(f"   Reasoning: {result.reasoning}")
                    context.logger.warning(f"   Risks: {result.risks}")

                return result

            except (json.JSONDecodeError, ValueError) as e:
                context.logger.error(f"Failed to parse LLM JSON response: {e}")
                context.logger.error(f"LLM response was: {llm_text}")

                # Fail safe: reject if parsing fails
                return PlanValidationResult(
                    approved=False,
                    confidence=0.0,
                    reasoning=f"LLM response parsing failed: {e}",
                    risks=["Invalid LLM output"],
                    recommendations=["Review LLM prompt", "Check model quality"],
                )

        except Exception as e:
            context.logger.error(f"LLM validation error: {e}")

            # Fail safe: reject on error
            return PlanValidationResult(
                approved=False,
                confidence=0.0,
                reasoning=f"LLM validation error: {e}",
                risks=["Validation system error"],
                recommendations=["Check LLM availability", "Review error logs"],
            )

    async def execute(self, context: SharedContext) -> SharedContext:
        """
        Cognitive plugin execute method (not used for this plugin).
        
        This plugin is called via validate_plan() method, not execute().
        """
        context.payload["info"] = "Use validate_plan() method for plan validation"
        context.payload["available_methods"] = ["validate_plan"]
        return context

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Tool definitions for cognitive planner"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "validate_plan",
                    "description": (
                        "CRITICAL: Validate Jules plan using powerful local LLM semantic analysis. "
                        "Compares Sophia's original task vs Jules plan to ensure alignment. "
                        "Prevents wasting Jules API quota (max 100 tasks/day) on bad plans. "
                        "Returns approval decision with confidence score and reasoning. "
                        "Use this BEFORE approving Jules plans!"
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "sophia_task": {
                                "type": "string",
                                "description": "Original task description from Sophia. Example: 'Fix benchmark runner timeout bug'",
                            },
                            "jules_plan": {
                                "type": "object",
                                "description": "Plan from Jules API (from get_plan_details). Must have 'summary', 'steps', 'files' fields.",
                            },
                            "session_id": {
                                "type": "string",
                                "description": "Jules session ID for logging/tracking. Format: 'sessions/abc123'",
                            },
                        },
                        "required": ["sophia_task", "jules_plan", "session_id"],
                    },
                },
            }
        ]
