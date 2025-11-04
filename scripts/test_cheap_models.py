#!/usr/bin/env python3
"""
Quick benchmark test for cheap models.
Tests Llama 3.2 3B and Mistral Nemo on the 8-step benchmark.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import SharedContext
from plugins.tool_model_evaluator import ModelEvaluatorTool
from plugins.tool_llm import LLMTool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models to test
CHEAP_MODELS = [
    "openrouter/meta-llama/llama-3.2-3b-instruct",
    "openrouter/mistralai/mistral-nemo",
]

JUDGE_MODEL = "openrouter/anthropic/claude-3-opus"

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

EVALUATION_CRITERIA = [
    "Correctness: Did the model correctly follow all 8 steps of the plan?",
    "Completeness: Did the model provide a response for every step?",
    "Clarity: Was the output of each step clear and easy to understand?",
    "Adherence_to_Instructions: Did the model strictly follow the instructions without adding extra conversational fluff?",
]

OUTPUT_DIR = "docs/benchmarks"


async def test_model(model_name: str, evaluator: ModelEvaluatorTool, context: SharedContext):
    """Test a single model."""
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print(f"{'='*80}")

    try:
        result = await evaluator.evaluate_model(
            context, model_name, BENCHMARK_PROMPT, EVALUATION_CRITERIA, JUDGE_MODEL
        )

        # Save result
        filename = f"{model_name.replace('/', '_')}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(result, f, indent=4)

        # Print summary
        score = result.get("quality", {}).get("overall_score", 0)
        cost = result.get("performance", {}).get("cost_usd", 0)
        time = result.get("performance", {}).get("response_time_seconds", 0)

        print("\n✅ RESULTS:")
        print(f"   Score: {score}/10")
        print(f"   Cost:  ${cost:.6f}")
        print(f"   Time:  {time:.2f}s")

        if score >= 8:
            print("   ✅ PASSED - Model is suitable for production!")
        else:
            print("   ❌ FAILED - Score too low")

        return result

    except Exception as e:
        logger.error(f"Error testing {model_name}: {e}", exc_info=True)
        return None


async def main():
    """Main test runner."""
    print("\n" + "=" * 80)
    print("CHEAP MODEL BENCHMARK TEST")
    print("Testing candidates for simple_query and task_routing roles")
    print("=" * 80)

    # Setup
    llm_tool = LLMTool()
    llm_tool.setup({})

    evaluator = ModelEvaluatorTool()
    evaluator.setup({"plugins": {"tool_llm": llm_tool}})

    context = SharedContext(
        session_id="cheap_benchmark",
        current_state="EXECUTING",
        logger=logger,
        user_input=BENCHMARK_PROMPT,
        history=[],
    )

    # Test each model
    results = {}
    total_cost = 0.0

    for model in CHEAP_MODELS:
        result = await test_model(model, evaluator, context)
        if result:
            results[model] = result
            total_cost += result.get("performance", {}).get("cost_usd", 0)

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    passed = []
    failed = []

    for model, result in results.items():
        score = result.get("quality", {}).get("overall_score", 0)
        cost = result.get("performance", {}).get("cost_usd", 0)

        if score >= 8:
            passed.append((model, score, cost))
        else:
            failed.append((model, score, cost))

    if passed:
        print("\n✅ PASSED MODELS:")
        for model, score, cost in passed:
            print(f"   {model}")
            print(f"      Score: {score}/10, Cost: ${cost:.6f}")

    if failed:
        print("\n❌ FAILED MODELS:")
        for model, score, cost in failed:
            print(f"   {model}")
            print(f"      Score: {score}/10, Cost: ${cost:.6f}")

    print(f"\nTotal benchmark cost: ${total_cost:.6f}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if passed:
        # Find cheapest passing model
        cheapest = min(passed, key=lambda x: x[2])
        print(f"\n🏆 Best value: {cheapest[0]}")
        print(f"   Score: {cheapest[1]}/10")
        print(f"   Cost: ${cheapest[2]:.6f} per test")
        print("\n   ➡️  Recommended for: simple_query, task_routing")
    else:
        print("\n⚠️  No models passed the 8-step test.")
        print("   Recommendation: Stick with DeepSeek Chat for all tasks.")


if __name__ == "__main__":
    if "OPENROUTER_API_KEY" not in os.environ:
        from dotenv import load_dotenv

        load_dotenv()
        if "OPENROUTER_API_KEY" not in os.environ:
            print("Error: OPENROUTER_API_KEY not set")
            sys.exit(1)

    asyncio.run(main())
