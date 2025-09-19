import os
import json
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI


# --- MOCK LLM FOR TESTING ---
class MockLLM(Runnable):
    """
    A mock LLM for testing purposes. It inherits from Runnable to be compatible with LCEL.
    It returns a pre-defined JSON plan if the prompt asks for one,
    otherwise returns a generic success message.
    This allows testing the workflow without making real API calls.
    """

    def bind(self, *args, **kwargs):
        """A mock bind method that returns self."""
        return self

    def invoke(self, *args, **kwargs):
        prompt = ""
        if args and hasattr(args[0], "to_string"):
            prompt = args[0].to_string()
        else:
            prompt = str(args)

        print("--- MOCK LLM INVOKED ---")

        # Check if this is the planning agent asking for a plan
        if "Odpověz POUZE ve formátu JSON" in prompt:
            print(
                "--- MOCK LLM: Returning a pre-defined plan with Final Answer prefix. ---"
            )
            mock_plan_dict = {
                "plan": [
                    {
                        "step": 1,
                        "description": "Analyzuj kód v `main.py` aby si pochopil jeho funkcionalitu.",
                    },
                    {
                        "step": 2,
                        "description": "Na základe analýzy navrhni obsah pre README.md súbor.",
                    },
                    {
                        "step": 3,
                        "description": "Ulož navrhnutý obsah do súboru `navrh_readme.md`.",
                    },
                ]
            }
            # The CrewAgentParser expects a "Final Answer:" prefix for the task to end.
            return f"Final Answer: {json.dumps(mock_plan_dict)}"
        else:
            # This is an execution task. Force the agent to finish immediately.
            print(
                "--- MOCK LLM: Returning a generic Final Answer for execution step. ---"
            )
            # This will make the agent finish the step without using any tools.
            # It allows us to test the multi-step flow in main.py.
            return "Final Answer: The step was mock-executed successfully."


# --- CENTRALIZED LLM INITIALIZATION ---
# Use the mock LLM if the environment variable is set to "true"
if os.getenv("USE_MOCK_LLM") == "true":
    print("--- Using MOCK LLM for testing ---")
    llm = MockLLM()
else:
    # Initialize real LLM
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable not set and not using mock LLM. Please set it in your .env file."
        )
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", google_api_key=gemini_api_key
    )
