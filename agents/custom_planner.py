import json
import re
from typing import List, Dict, Any

# Předpokládáme, že tyto třídy budou dostupné
from core.context import SharedContext
from core.llm_config import llm as default_llm
from core.utils import list_tools

# Šablona pro systémový prompt
PLANNER_SYSTEM_PROMPT_TEMPLATE = """
You are an expert planner agent. Your task is to analyze a user's request and create a detailed, step-by-step execution plan.
You must only use the tools provided in the list below. Do not invent new tools.
Each step in the plan must be a single call to one of the provided tools.

**Available Tools:**
{tools_description}

**Output Format:**
You must respond with a valid JSON object. The JSON object must be a list of steps.
Each step in the list must be a dictionary with the following keys:
- "step_id": An integer representing the step number, starting from 1.
- "description": A string describing the purpose of the step.
- "tool_name": A string with the exact name of the tool to be used.
- "parameters": A dictionary of key-value pairs representing the parameters for the tool.

If you determine that the user's request cannot be fulfilled with the available tools, respond with a JSON object containing a single key "error" with a string explaining why the task cannot be completed.
Example of an error response: {{"error": "I do not have access to real-time weather information."}}

Do not add any conversational fluff, explanations, or markdown formatting outside of the main JSON object.
"""

class CustomPlanner:
    """
    Vlastní plánovač, který přímo komunikuje s LLM pro vytvoření plánu.
    Nahrazuje `PlannerAgent` založený na `crewai`.
    """

    def __init__(self, llm: Any = None):
        self.llm = llm or default_llm
        self.tools_description = self._get_tools_description()

    def _get_tools_description(self) -> str:
        """
        Získá popis dostupných nástrojů pro vložení do promptu.
        """
        tools = list_tools()
        return "\n".join([f"- {tool['name']}: {tool['description']} (Parameters: {tool['parameters']})" for tool in tools])


    async def generate_plan(self, context: SharedContext, max_retries=3) -> SharedContext:
        """
        Generates a plan based on the user's prompt, with retries for parsing.
        """
        system_prompt = PLANNER_SYSTEM_PROMPT_TEMPLATE.format(tools_description=self.tools_description)
        user_prompt = context.original_prompt

        for attempt in range(max_retries):
            try:
                # Sestavení zpráv pro LLM
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ]

                # Přímé volání LLM
                llm_response = await self.llm.ainvoke(input=messages)

                # Extrakce textu z odpovědi
                response_text = llm_response.content if hasattr(llm_response, 'content') else str(llm_response)

                # 1. Extrahovat JSON blok
                json_match = re.search(r"```(json)?\s*([\s\S]*?)\s*```", response_text)
                if not json_match:
                    # Zkusíme parsovat celý text, pokud nejsou značky
                    json_string = response_text
                else:
                    json_string = json_match.group(2)

                # 2. Parsovat JSON
                parsed_data = json.loads(json_string)

                # 3. Validovat strukturu
                if "error" in parsed_data:
                    context.feedback = f"Planner determined task can't be completed: {parsed_data['error']}"
                    context.payload['plan'] = None
                    return context

                if isinstance(parsed_data, list) and all("step_id" in step for step in parsed_data):
                    context.payload['plan'] = parsed_data
                    context.feedback = "Plan generated successfully."
                    return context

                raise ValueError("Invalid plan structure received from LLM.")

            except (json.JSONDecodeError, ValueError) as e:
                user_prompt = f"{user_prompt}\n\nPrevious attempt failed. The response was not valid JSON or had the wrong structure. Please correct your output. Error: {e}"
                if attempt == max_retries - 1:
                    context.feedback = "Failed to generate a valid plan after multiple retries."
                    context.payload['plan'] = None
                    return context
            except Exception as e:
                context.feedback = f"An unexpected error occurred during planning: {e}"
                context.payload['plan'] = None
                return context

        return context
