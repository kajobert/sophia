import json
import re
from crewai import Agent, Task, Crew
from core.context import SharedContext
import logging

class PlannerAgent:
    """
    A wrapper class for the Planner agent that ensures the output is a valid JSON plan.
    """

    MAX_RETRIES = 3

    def __init__(self, llm):
        self.agent = Agent(
            role="Master Planner",
            goal="Create comprehensive, detailed, and executable plans for given tasks and objectives. "
                 "Each plan must be broken down into logical, sequential steps in a specific JSON format.",
            backstory=(
                "I am the Master Planner, an entity born from the need for order and strategy. "
                "My sole purpose is to analyze complex problems and transform them into understandable, "
                "step-by-step plans. I track every detail, anticipate potential obstacles, and ensure "
                "the path to the goal is as efficient as possible. Without my plan, chaos reigns; with my plan, success is inevitable."
            ),
            llm=llm,
            tools=[],
            verbose=True,
            allow_delegation=False,
            max_iter=5,
        )

    def _extract_json_from_reponse(self, response: str) -> str:
        # Use regex to find the JSON block, even with markdown backticks
        match = re.search(r"```(json)?\s*([\s\S]*?)\s*```", response)
        if match:
            return match.group(2).strip()
        return response.strip() # Fallback to stripping the whole response

    def run_task(self, context: SharedContext) -> SharedContext:
        """
        Runs the planning task, ensuring the output is a valid JSON plan.
        Retries up to MAX_RETRIES times if the output is not valid JSON.
        """
        available_tools = [
            "ExecutePythonScriptTool", "RunUnitTestsTool", "ListDirectoryTool",
            "ReadFileTool", "WriteFileTool", "GitTool", "MemoryReaderTool", "SystemAwarenessTool"
        ]

        task_description = (
            "Analyze the following user request and create a detailed, step-by-step plan to accomplish it. "
            "The plan must be in a specific JSON format. "
            f"You must only use the tools from the following list: {', '.join(available_tools)}. "
            f"User Request: {context.original_prompt}"
        )

        expected_output = (
            'A valid JSON array of objects, where each object represents a step. '
            'Each step object must have the following keys: "step_id" (integer), "description" (string), '
            '"tool_name" (string), and "parameters" (a dictionary of key-value pairs). '
            'Example: [{"step_id": 1, "description": "List files in the root directory.", "tool_name": "file_system.list_files", "parameters": {"path": "/"}}]'
            'Do not add any conversational fluff or explanations outside of the JSON structure.'
        )

        planning_task = Task(
            description=task_description,
            agent=self.agent,
            expected_output=expected_output,
        )

        crew = Crew(agents=[self.agent], tasks=[planning_task], verbose=True)

        for attempt in range(self.MAX_RETRIES):
            logging.info(f"Running PlannerAgent, attempt {attempt + 1}/{self.MAX_RETRIES}")
            try:
                result = crew.kickoff()
                raw_plan = result.raw if hasattr(result, "raw") else str(result)

                # Extract JSON from the response
                json_string = self._extract_json_from_reponse(raw_plan)

                # Parse the JSON to validate it
                parsed_plan = json.loads(json_string)

                # Basic validation of the plan structure
                if isinstance(parsed_plan, list) and all(
                    isinstance(step, dict) and
                    "step_id" in step and
                    "description" in step and
                    "tool_name" in step and
                    "parameters" in step
                    for step in parsed_plan
                ):
                    context.payload["plan"] = parsed_plan
                    logging.info(f"Successfully generated and validated plan: {parsed_plan}")
                    return context
                else:
                    raise ValueError("Plan structure is invalid.")

            except (json.JSONDecodeError, ValueError) as e:
                logging.warning(f"Attempt {attempt + 1} failed: Invalid JSON or plan structure. Error: {e}")
                if attempt == self.MAX_RETRIES - 1:
                    logging.error("PlannerAgent failed to generate a valid plan after all retries.")
                    context.payload["plan"] = None
                    context.feedback = "PlannerAgent failed to generate a valid JSON plan."
                    return context

        return context


    def get_agent(self):
        """Returns the underlying crewAI Agent instance."""
        return self.agent
