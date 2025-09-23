import json
import re
import logging
from core.context import SharedContext
from core.gemini_llm_adapter import GeminiLLMAdapter


class PlannerAgent:
    """
    A class to generate executable plans using a language model, without external frameworks.
    """

    MAX_RETRIES = 3

    def __init__(self, llm: GeminiLLMAdapter):
        """
        Initializes the PlannerAgent with a direct LLM adapter.
        """
        self.llm = llm
        self.logger = logging.getLogger(__name__)

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extracts a JSON code block from the LLM's string response.
        """
        # Regex to find the JSON block, even with markdown backticks
        match = re.search(r"```(json)?\s*([\s\S]*?)\s*```", response)
        if match:
            return match.group(2).strip()
        # Fallback for responses that might just be a raw JSON string
        return response.strip()

    def _build_prompt(self, context: SharedContext) -> str:
        """
        Builds a detailed, structured prompt for the LLM to generate a plan.
        """
        available_tools = [
            "ExecutePythonScriptTool",
            "RunUnitTestsTool",
            "ListDirectoryTool",
            "ReadFileTool",
            "WriteFileTool",
            "GitTool",
            "MemoryReaderTool",
            "SystemAwarenessTool",
        ]

        # This structured prompt is designed to be more robust and give the LLM clear instructions.
        prompt = f"""
You are a master planner AI. Your task is to analyze a user's request and create a detailed, step-by-step execution plan.

**Constraints & Rules:**
1.  The plan must be a valid JSON array of objects.
2.  Each step in the JSON array must be an object with the following keys: `step_id` (integer), `description` (string), `tool_name` (string), and `parameters` (a dictionary).
3.  You can ONLY use tools from this list: {', '.join(available_tools)}. Do not invent tools.
4.  If the user's request is impossible or outside your capabilities (e.g., asking for the weather, accessing the internet), you must return an empty JSON array `[]` and nothing else.
5.  Your entire response must be ONLY the JSON plan. Do not include any other text, explanations, or markdown formatting outside of the JSON itself.

**User Request:**
"{context.original_prompt}"

**Example of a valid response:**
```json
[
  {{
    "step_id": 1,
    "description": "List all files in the root of the sandbox directory.",
    "tool_name": "ListDirectoryTool",
    "parameters": {{
      "path": "."
    }}
  }}
]
```

Now, generate the plan for the user's request.
"""
        return prompt

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Runs the planning task by calling the LLM directly and validating the output.
        Retries up to MAX_RETRIES times if the output is not a valid JSON plan.
        """
        prompt = self._build_prompt(context)

        for attempt in range(self.MAX_RETRIES):
            self.logger.info(
                f"Running PlannerAgent, attempt {attempt + 1}/{self.MAX_RETRIES}"
            )
            try:
                # Direct LLM call
                raw_response = self.llm.invoke(prompt)

                if not raw_response or not raw_response.strip():
                    # This specifically handles the "None or empty response from LLM" error
                    raise ValueError("Received an empty response from the LLM.")

                json_string = self._extract_json_from_response(raw_response)
                parsed_plan = json.loads(json_string)

                # Handle the case where the LLM correctly decides the task is impossible
                if isinstance(parsed_plan, list) and not parsed_plan:
                    self.logger.info(
                        "Planner correctly determined the task is un-plannable."
                    )
                    context.payload["plan"] = []
                    context.feedback = "The task could not be completed as it is outside my capabilities."
                    return context

                # Validate the structure of the plan
                if isinstance(parsed_plan, list) and all(
                    isinstance(step, dict)
                    and "step_id" in step
                    and "description" in step
                    and "tool_name" in step
                    and "parameters" in step
                    for step in parsed_plan
                ):
                    context.payload["plan"] = parsed_plan
                    self.logger.info(
                        f"Successfully generated and validated plan: {parsed_plan}"
                    )
                    return context
                else:
                    raise ValueError("Plan structure is invalid.")

            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(
                    f"Attempt {attempt + 1} failed: Invalid JSON or plan structure. Error: {e}"
                )
                if attempt == self.MAX_RETRIES - 1:
                    self.logger.error(
                        "PlannerAgent failed to generate a valid plan after all retries."
                    )
                    context.payload["plan"] = None
                    context.feedback = (
                        "PlannerAgent failed to generate a valid JSON plan."
                    )
                    return context

        return context
