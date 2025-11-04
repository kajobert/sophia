import asyncio
import json
import os
import logging
from typing import Dict

# This script assumes it is run from the root of the project.
# Add the project root to the python path to allow importing project modules.
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.context import SharedContext
from plugins.tool_model_evaluator import ModelEvaluatorTool
from plugins.tool_llm import LLMTool

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Configuration ---

# The list of models to be benchmarked.
MAIN_MODELS = [
    "openrouter/google/gemma-2-9b-it",
    "openrouter/meta-llama/llama-3-8b-instruct",
    "openrouter/mistralai/mistral-7b-instruct-v0.3",
    "openrouter/anthropic/claude-3-haiku",
    "openrouter/google/gemini-2.0-flash-001",
    "openrouter/microsoft/phi-3-mini-128k-instruct",
    "openrouter/openai/gpt-4o-mini",
    "openrouter/cohere/command-r-08-2024",
    "openrouter/mistralai/mixtral-8x7b-instruct",
    "openrouter/deepseek/deepseek-chat",
    "openrouter/qwen/qwen-plus",
    "openrouter/meta-llama/llama-3.1-70b-instruct",
    "openrouter/mistralai/codestral-2508",
    "openrouter/google/gemini-2.5-flash",
    "openrouter/x-ai/grok-3-mini",
    "openrouter/nousresearch/hermes-2-pro-llama-3-8b",
    "openrouter/microsoft/wizardlm-2-8x22b",
    "openrouter/perplexity/sonar-reasoning",
    "openrouter/z-ai/glm-4-32b",
    "openrouter/mistralai/mistral-small",
]

REFERENCE_MODELS = [
    "openrouter/google/gemini-2.5-pro",
    "openrouter/anthropic/claude-3.5-sonnet",
    "openrouter/mistralai/mistral-large",
]

# The judge model for quality assessment.
JUDGE_MODEL = "openrouter/anthropic/claude-3-opus"

# The standard 8-step benchmark prompt.
BENCHMARK_PROMPT = """
You are an AI assistant. Your task is to follow a plan to complete a goal.
**Goal:** Read the `README.md` file, summarize its content, and write the summary to a new file named `docs/summary.md`.

Here is the plan:
1.  **tool_file_system.list_directory(path=".")** - to see the files in the current directory.
2.  **tool_file_system.read_file(filepath="README.md")** - to read the content of the README file.
3.  **tool_llm.execute(prompt="Summarize the following text: {file_content}")** - to summarize the content.
4.  **tool_file_system.write_file(filepath="docs/summary.md", content="{summary}")** - to write the summary to a new file.
5.  **tool_file_system.list_directory(path="docs/")** - to verify the new file was created.
6.  **tool_file_system.read_file(filepath="docs/summary.md")** - to verify the content of the new file.
7.  **tool_file_system.delete_file(filepath="docs/summary.md")** - to clean up the created file.
8.  **tool_file_system.list_directory(path="docs/")** - to verify the file was deleted.

Please execute this plan step-by-step and provide the output of each step.
"""

# Evaluation criteria for the judge model.
EVALUATION_CRITERIA = [
    "Correctness: Did the model correctly follow all 8 steps of the plan?",
    "Completeness: Did the model provide a response for every step?",
    "Clarity: Was the output of each step clear and easy to understand?",
    "Adherence_to_Instructions: Did the model strictly follow the instructions without adding extra conversational fluff?",
]

# Output directory for benchmark results.
OUTPUT_DIR = "docs/benchmarks"


def load_pricing_data() -> Dict[str, Dict[str, float]]:
    """Loads model pricing data from the generated Markdown file."""
    pricing_data = {}
    try:
        with open("docs/openrouter_models.md", "r") as f:
            for line in f:
                if not line.startswith("|"):
                    continue
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) == 5 and "---" not in parts[0]:
                    model_id = parts[0]
                    try:
                        prompt_cost = float(parts[3])
                        completion_cost = float(parts[4])
                        pricing_data[model_id] = {
                            "cost_prompt_usd_per_1m": prompt_cost,
                            "cost_completion_usd_per_1m": completion_cost,
                        }
                    except (ValueError, IndexError):
                        continue
    except Exception as e:
        print(
            f"Warning: Could not load pricing data from docs/openrouter_models.md. Cost calculation may be inaccurate. Error: {e}"
        )
    return pricing_data


async def main():
    """Main function to run the benchmark."""
    print("--- Starting Model Benchmark ---")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pricing_data = load_pricing_data()

    # Initialize the tools
    llm_tool = LLMTool()
    llm_tool.setup({})  # Basic setup

    model_evaluator = ModelEvaluatorTool()
    model_evaluator.setup({"plugins": {"tool_llm": llm_tool}})

    # Create a context with a real logger
    context = SharedContext(
        session_id="benchmark_session",
        current_state="EXECUTING",
        logger=logger,
        user_input=BENCHMARK_PROMPT,
        history=[],
    )

    all_models = MAIN_MODELS + REFERENCE_MODELS
    total_cost = 0.0

    for i, model_name in enumerate(all_models):
        print(f"\\n--- Evaluating model {i+1}/{len(all_models)}: {model_name} ---")

        try:
            result = await model_evaluator.evaluate_model(
                context, model_name, BENCHMARK_PROMPT, EVALUATION_CRITERIA, JUDGE_MODEL
            )

            # Calculate cost manually if not provided by API
            if "performance" in result:
                cost = result.get("performance", {}).get("cost_usd", 0.0)
                if cost == 0.0 and model_name in pricing_data:
                    model_pricing = pricing_data[model_name]
                    input_tokens = result.get("performance", {}).get("input_tokens", 0)
                    output_tokens = result.get("performance", {}).get("output_tokens", 0)
                    cost = (
                        (input_tokens / 1_000_000) * model_pricing.get("cost_prompt_usd_per_1m", 0)
                    ) + (
                        (output_tokens / 1_000_000)
                        * model_pricing.get("cost_completion_usd_per_1m", 0)
                    )
                    result["performance"]["cost_usd"] = cost
            else:
                cost = 0.0

            # Save the result to a JSON file
            filename = f"{model_name.replace('/', '_')}.json"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, "w") as f:
                json.dump(result, f, indent=4)

            logger.info(
                f"Full benchmark result for {model_name}: \n{json.dumps(result, indent=2)}"
            )

            total_cost += cost
            print(f"Successfully evaluated. Cost for this run: ${cost:.6f}")
            print(f"Cumulative cost: ${total_cost:.6f}")

        except Exception as e:
            logger.error(f"An error occurred while evaluating {model_name}: {e}", exc_info=True)
            # Log the error to a file as well
            error_filename = f"{model_name.replace('/', '_')}_error.json"
            error_filepath = os.path.join(OUTPUT_DIR, error_filename)
            with open(error_filepath, "w") as f:
                json.dump({"error": str(e)}, f, indent=4)

        # Budget check
        if i >= 2:  # After the first 3 models
            avg_cost = total_cost / (i + 1)
            projected_cost = avg_cost * len(all_models)
            print(f"Projected total cost after {i+1} runs: ${projected_cost:.4f}")
            if projected_cost > 3.00:
                print(
                    "\\n*** BUDGET ALERT: Projected cost exceeds $3.00. Stopping the benchmark. ***"
                )
                break

    print("\\n--- Benchmark complete ---")
    print(f"Total cost for {i+1} models: ${total_cost:.6f}")


if __name__ == "__main__":
    # This check is to ensure that the OPENROUTER_API_KEY is set.
    # The llm_tool will load it from the environment.
    if "OPENROUTER_API_KEY" not in os.environ:
        from dotenv import load_dotenv

        load_dotenv()
        if "OPENROUTER_API_KEY" not in os.environ:
            print(
                "Error: OPENROUTER_API_KEY is not set. Please create a .env file or set the environment variable."
            )
            sys.exit(1)

    asyncio.run(main())
