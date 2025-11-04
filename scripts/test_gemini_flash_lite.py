#!/usr/bin/env python3
"""
Test Gemini Flash Lite models on the 8-step benchmark.
Testing candidates that are cheaper than or equal to DeepSeek Chat ($0.14/1M).
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

# Models to test (cheaper than or equal to DeepSeek Chat at $0.14/1M)
GEMINI_MODELS = [
    ("openrouter/google/gemini-2.0-flash-exp:free", "Gemini 2.0 Flash Exp (FREE)", 0.00),
    ("openrouter/google/gemini-2.0-flash-lite-001", "Gemini 2.0 Flash Lite", 0.075),
    ("openrouter/google/gemini-2.0-flash-001", "Gemini 2.0 Flash (tested earlier)", 0.10),
    ("openrouter/google/gemini-2.5-flash-lite", "Gemini 2.5 Flash Lite", 0.10),
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


async def test_model(
    model_id: str,
    model_name: str,
    cost_per_1m: float,
    evaluator: ModelEvaluatorTool,
    context: SharedContext,
):
    """Test a single model."""
    print(f"\n{'='*80}")
    print(f"Testing: {model_name}")
    print(f"Model ID: {model_id}")
    print(f"Cost: ${cost_per_1m}/1M tokens")
    print(f"{'='*80}")

    try:
        result = await evaluator.evaluate_model(
            context, model_id, BENCHMARK_PROMPT, EVALUATION_CRITERIA, JUDGE_MODEL
        )

        # Save result
        filename = f"{model_id.replace('/', '_').replace(':', '_')}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(result, f, indent=4)

        # Print summary
        score = result.get("quality", {}).get("overall_score", 0)
        cost = result.get("performance", {}).get("cost_usd", 0)
        time = result.get("performance", {}).get("response_time_seconds", 0)

        print("\n✅ RESULTS:")
        print(f"   Score: {score}/10")
        print(f"   Benchmark Cost: ${cost:.6f}")
        print(f"   Time:  {time:.2f}s")
        print(f"   Per 1M tokens: ${cost_per_1m}/1M")

        if score >= 8:
            print("   ✅ PASSED - Suitable for production!")
            if cost_per_1m < 0.14:
                savings = (0.14 - cost_per_1m) / 0.14 * 100
                print(f"   💰 {savings:.1f}% cheaper than DeepSeek Chat!")
        else:
            print("   ❌ FAILED - Score too low")

        return result, cost_per_1m

    except Exception as e:
        logger.error(f"Error testing {model_name}: {e}", exc_info=True)
        return None, cost_per_1m


async def main():
    """Main test runner."""
    print("\n" + "=" * 80)
    print("GEMINI FLASH LITE BENCHMARK TEST")
    print("Testing models cheaper than or equal to DeepSeek Chat ($0.14/1M)")
    print("=" * 80)

    # Setup
    llm_tool = LLMTool()
    llm_tool.setup({})

    evaluator = ModelEvaluatorTool()
    evaluator.setup({"plugins": {"tool_llm": llm_tool}})

    context = SharedContext(
        session_id="gemini_benchmark",
        current_state="EXECUTING",
        logger=logger,
        user_input=BENCHMARK_PROMPT,
        history=[],
    )

    # Test each model
    results = {}
    total_cost = 0.0

    for model_id, model_name, cost_per_1m in GEMINI_MODELS:
        result, cost_1m = await test_model(model_id, model_name, cost_per_1m, evaluator, context)
        if result:
            results[model_id] = {"result": result, "name": model_name, "cost_per_1m": cost_1m}
            total_cost += result.get("performance", {}).get("cost_usd", 0)

    # Final summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    passed = []
    failed = []

    for model_id, data in results.items():
        result = data["result"]
        score = result.get("quality", {}).get("overall_score", 0)
        cost = result.get("performance", {}).get("cost_usd", 0)
        cost_1m = data["cost_per_1m"]
        name = data["name"]

        if score >= 8:
            passed.append((model_id, name, score, cost, cost_1m))
        else:
            failed.append((model_id, name, score, cost, cost_1m))

    if passed:
        print("\n✅ PASSED MODELS:")
        for model_id, name, score, cost, cost_1m in passed:
            print(f"   {name}")
            print(f"      Score: {score}/10, Cost: ${cost_1m}/1M tokens")

    if failed:
        print("\n❌ FAILED MODELS:")
        for model_id, name, score, cost, cost_1m in failed:
            print(f"   {name}")
            print(f"      Score: {score}/10, Cost: ${cost_1m}/1M tokens")

    print(f"\nTotal benchmark cost: ${total_cost:.6f}")

    # Recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    if passed:
        # Find cheapest passing model
        cheapest = min(passed, key=lambda x: x[4])  # x[4] is cost_per_1m
        print(f"\n🏆 BEST VALUE: {cheapest[1]}")
        print(f"   Model ID: {cheapest[0]}")
        print(f"   Score: {cheapest[2]}/10")
        print(f"   Cost: ${cheapest[4]}/1M tokens")

        if cheapest[4] < 0.14:
            savings = (0.14 - cheapest[4]) / 0.14 * 100
            print(f"   💰 Savings: {savings:.1f}% cheaper than DeepSeek Chat!")
            print(f"\n   ➡️  RECOMMENDATION: Replace DeepSeek Chat with {cheapest[1]}")
        elif cheapest[4] == 0.14:
            print("\n   ➡️  Same price as DeepSeek Chat - keep current configuration")

        print("\n   Recommended for: Default model, simple_query, text_summarization")
    else:
        print("\n⚠️  No models passed the 8-step test.")
        print("   Recommendation: Stick with DeepSeek Chat ($0.14/1M) as minimum viable option.")


if __name__ == "__main__":
    if "OPENROUTER_API_KEY" not in os.environ:
        from dotenv import load_dotenv

        load_dotenv()
        if "OPENROUTER_API_KEY" not in os.environ:
            print("Error: OPENROUTER_API_KEY not set")
            sys.exit(1)

    asyncio.run(main())
