import time
import json
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field

from plugins.base_plugin import BasePlugin, PluginType
from core.context import SharedContext
from plugins.tool_llm import LLMTool


class EvaluateModelArgs(BaseModel):
    """Pydantic model for arguments of the evaluate_model tool."""

    model_name: str = Field(..., description="The name of the model to evaluate.")
    prompt: str = Field(..., description="The prompt to use for the evaluation.")
    evaluation_criteria: List[str] = Field(
        ..., description="A list of criteria for the judge model to evaluate the response."
    )
    judge_model_name: str = Field(
        "openrouter/anthropic/claude-3-opus", description="The name of the judge model."
    )


class ModelEvaluatorTool(BasePlugin):
    """A tool plugin for evaluating LLM models."""

    def __init__(self):
        super().__init__()
        self.llm_tool: Optional[LLMTool] = None

    @property
    def name(self) -> str:
        return "tool_model_evaluator"

    @property
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL

    @property
    def version(self) -> str:
        return "1.0.0"

    def setup(self, config: dict) -> None:
        """Configures the tool and gets a reference to the LLMTool."""
        all_plugins = config.get("all_plugins", {})
        self.llm_tool = all_plugins.get("tool_llm")
        if not self.llm_tool:
            raise ValueError("LLMTool not found in the list of available plugins.")

    async def execute(self, context: SharedContext) -> SharedContext:
        """This tool is not directly executed in the main loop."""
        return context

    async def evaluate_model(
        self,
        context: SharedContext,
        model_name: str,
        prompt: str,
        evaluation_criteria: List[str],
        judge_model_name: str,
    ) -> Dict[str, Any]:
        """
        Evaluates a given LLM model based on performance and quality metrics.
        """
        if not self.llm_tool:
            return {"error": "LLMTool is not initialized."}

        context.logger.info(f"Starting evaluation for model: '{model_name}'")

        # 1. Get response from the model being evaluated
        start_time = time.time()
        try:
            # We need to construct a new context for the LLM tool call
            llm_context = SharedContext(
                session_id=context.session_id,
                current_state="EXECUTING",
                logger=context.logger,
                user_input=prompt,
                payload={"model_config": {"model": model_name}},
                history=[],
            )
            eval_context = await self.llm_tool.execute(context=llm_context)
            response_content = eval_context.payload.get("llm_response")
            response_metadata = eval_context.payload.get("llm_response_metadata", {})
        except Exception as e:
            context.logger.error(f"Error getting response from '{model_name}': {e}", exc_info=True)
            return {
                "error": f"Failed to get response from model '{model_name}'.",
                "details": str(e),
            }
        end_time = time.time()

        # 2. Prepare for quality evaluation
        judge_prompt = self._create_judge_prompt(prompt, response_content, evaluation_criteria)

        # 3. Get evaluation from the judge model
        try:
            judge_context = SharedContext(
                session_id=context.session_id,
                current_state="EXECUTING",
                logger=context.logger,
                user_input=judge_prompt,
                payload={"model_config": {"model": judge_model_name}},
                history=[],
            )
            judge_context = await self.llm_tool.execute(context=judge_context)
            quality_assessment_str = judge_context.payload.get("llm_response")
            quality_assessment = self._parse_json_from_text(quality_assessment_str)
        except Exception as e:
            context.logger.error(
                f"Error getting evaluation from judge model '{judge_model_name}': {e}",
                exc_info=True,
            )
            quality_assessment = {
                "error": "Failed to get a valid JSON response from the judge model."
            }

        # 4. Compile results
        result = {
            "model_name": model_name,
            "performance": {
                "response_time_seconds": round(end_time - start_time, 2),
                "input_tokens": response_metadata.get("input_tokens", 0),
                "output_tokens": response_metadata.get("output_tokens", 0),
                "total_tokens": response_metadata.get("total_tokens", 0),
                "cost_usd": response_metadata.get("cost_usd", 0.0),
            },
            "quality": quality_assessment,
            "response": response_content,
        }

        context.logger.info(f"Finished evaluation for model: '{model_name}'")
        return result

    def _create_judge_prompt(
        self, original_prompt: str, response: str, criteria: List[str]
    ) -> str:
        criteria_str = "\n".join(f"- {c}" for c in criteria)
        return f"""
            You are a fair and impartial AI model evaluator. Your task is to assess the quality of a response generated by another AI model.

            **Original Prompt:**
            ---
            {original_prompt}
            ---

            **Model's Response:**
            ---
            {response}
            ---

            **Evaluation Criteria:**
            Please evaluate the response based on the following criteria:
            {criteria_str}

            **Instructions:**
            Provide your evaluation in a JSON format. The JSON should contain a 'scores' object where each key is a criterion and the value is an integer score from 1 to 10. It should also include a 'justification' string field with a brief explanation of your reasoning. Finally, include an 'overall_score' from 1 to 10.

            Example JSON output:
            {{
                "scores": {{
                    "Clarity": 8,
                    "Relevance": 9
                }},
                "justification": "The response was clear and directly addressed the prompt.",
                "overall_score": 8.5
            }}

            Now, provide your evaluation for the given response. REMINDER: You must respond ONLY with a valid JSON object.
            """

    def _parse_json_from_text(self, text: str) -> Dict[str, Any]:
        try:
            # Basic cleanup in case of markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            return json.loads(text.strip())
        except (json.JSONDecodeError, IndexError):
            return {
                "error": "Failed to parse JSON from judge model response.",
                "raw_response": text,
            }

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Gets the definitions of the tools provided by this plugin."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "evaluate_model",
                    "description": "Evaluates a given LLM model based on performance and quality metrics.",
                    "parameters": EvaluateModelArgs.model_json_schema(),
                },
            }
        ]
