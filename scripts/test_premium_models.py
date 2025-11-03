#!/usr/bin/env python3
"""
Benchmark pro LEPŠÍ lokální modely (do 30GB RAM).
Testuje medium/large modely vhodné pro výkonný hardware.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import statistics
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import SharedContext
from plugins.tool_llm import LLMTool
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════
# LEPŠÍ MODELY (10-30GB RAM) - Pro výkonný hardware
# ════════════════════════════════════════════════════════════════════

PREMIUM_MODELS = [
    # Gemma 3 série
    {
        "name": "Gemma 3 12B",
        "id": "openrouter/google/gemma-3-12b-it",
        "size": "12B",
        "ram": "12GB",
        "category": "medium"
    },
    {
        "name": "Gemma 3 27B",
        "id": "openrouter/google/gemma-3-27b-it",
        "size": "27B",
        "ram": "18GB",
        "category": "large"
    },
    
    # Mistral série
    {
        "name": "Mistral Nemo 12B",
        "id": "openrouter/mistralai/mistral-nemo",
        "size": "12B",
        "ram": "12GB",
        "category": "medium"
    },
    {
        "name": "Mistral Small 24B",
        "id": "openrouter/mistralai/mistral-small-3.1-24b-instruct",
        "size": "24B",
        "ram": "16GB",
        "category": "large"
    },
    
    # Llama série
    {
        "name": "Llama 3.3 8B",
        "id": "openrouter/meta-llama/llama-3.3-8b-instruct",
        "size": "8B",
        "ram": "10GB",
        "category": "medium"
    },
    
    # Qwen série
    {
        "name": "Qwen 2.5 14B",
        "id": "openrouter/qwen/qwen3-14b",
        "size": "14B",
        "ram": "14GB",
        "category": "medium"
    },
    {
        "name": "Qwen 2.5 32B",
        "id": "openrouter/qwen/qwen3-32b",
        "size": "32B",
        "ram": "20GB",
        "category": "large"
    },
    
    # DeepSeek série
    {
        "name": "DeepSeek R1 Distill 70B",
        "id": "openrouter/deepseek/deepseek-r1-distill-llama-70b",
        "size": "70B",
        "ram": "40GB+",
        "category": "ultra"
    },
]

# Test scénáře (stejné jako v původním benchmarku)
TEST_SCENARIOS = [
    {
        "name": "Simple Math",
        "prompt": "Calculate: 47 * 23 + 156. Show your work.",
        "expected_keywords": ["1081", "1237"],
        "weight": 1.0,
        "category": "reasoning"
    },
    {
        "name": "Code Understanding",
        "prompt": "What does this Python code do?\n```python\ndef factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)\n```\nBe brief.",
        "expected_keywords": ["factorial", "recursive", "multiply"],
        "weight": 2.0,
        "category": "coding"
    },
    {
        "name": "Tool Use",
        "prompt": "I want to read a file named 'config.yaml'. Which tool should I use and what parameters?",
        "expected_keywords": ["tool_file_system", "read_file", "config.yaml"],
        "weight": 3.0,
        "category": "tool_use"
    },
    {
        "name": "Planning",
        "prompt": "Plan steps to: read README.md, summarize it, save summary to docs/summary.md. List 4 steps briefly.",
        "expected_keywords": ["read", "summarize", "write", "file"],
        "weight": 2.5,
        "category": "planning"
    },
    {
        "name": "Self-Awareness",
        "prompt": "What is your name? Answer in one sentence.",
        "expected_keywords": ["sophia", "ami"],
        "weight": 1.5,
        "category": "identity"
    },
    {
        "name": "Code Generation",
        "prompt": "Write a Python function that checks if a number is prime. Be concise.",
        "expected_keywords": ["def", "prime", "return", "range"],
        "weight": 2.0,
        "category": "coding"
    },
]

RUNS_PER_SCENARIO = 2

async def run_test(llm_tool: LLMTool, model_id: str, scenario: Dict, run_num: int) -> Dict:
    """Run a single test."""
    await asyncio.sleep(4)  # Rate limiting
    
    start_time = datetime.now()
    
    try:
        context = SharedContext(
            session_id=f"premium_bench_{run_num}",
            current_state="EXECUTING",
            logger=logger,
            user_input=scenario['prompt'],
            history=[]
        )
        
        context.payload = {
            "prompt": scenario['prompt'],
            "model_config": {"model": model_id}
        }
        
        result_context = await llm_tool.execute(context=context)
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        response = result_context.payload.get("llm_response", "")
        if not isinstance(response, str):
            response = str(response)
        
        response_lower = response.lower()
        keywords_found = sum(1 for kw in scenario['expected_keywords'] 
                           if kw.lower() in response_lower)
        keyword_score = keywords_found / len(scenario['expected_keywords'])
        
        refusal_indicators = ["cannot", "unable", "don't have", "can't help"]
        refused = any(ind in response_lower for ind in refusal_indicators)
        
        quality = 0.0 if refused else min(1.0, keyword_score + (0.1 if len(response) < 500 else 0))
        
        return {
            "success": not refused,
            "response": response[:200],
            "keywords_found": keywords_found,
            "keyword_score": keyword_score,
            "quality": quality,
            "response_time": response_time,
            "refused": refused,
            "response_length": len(response)
        }
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "quality": 0.0,
            "response_time": 0.0,
            "refused": True
        }


async def benchmark_model(llm_tool: LLMTool, model: Dict) -> Dict:
    """Benchmark single model."""
    
    print(f"\n{'='*70}")
    print(f"Testing: {model['name']} ({model['size']}, {model['ram']} RAM)")
    print(f"{'='*70}")
    
    results = []
    
    for scenario in TEST_SCENARIOS:
        print(f"  [{scenario['category']}] {scenario['name']}...", end=" ", flush=True)
        
        scenario_results = []
        for run in range(RUNS_PER_SCENARIO):
            result = await run_test(llm_tool, model['id'], scenario, run)
            scenario_results.append(result)
        
        avg_quality = statistics.mean(r['quality'] for r in scenario_results)
        avg_time = statistics.mean(r['response_time'] for r in scenario_results)
        success_rate = sum(1 for r in scenario_results if r['success']) / len(scenario_results)
        weighted_score = avg_quality * scenario['weight']
        
        print(f"Quality: {avg_quality:.2f}, Time: {avg_time:.1f}s")
        
        results.append({
            "scenario": scenario['name'],
            "category": scenario['category'],
            "weight": scenario['weight'],
            "avg_quality": avg_quality,
            "avg_time": avg_time,
            "success_rate": success_rate,
            "weighted_score": weighted_score,
            "runs": scenario_results
        })
    
    total_weighted_score = sum(r['weighted_score'] for r in results)
    total_weight = sum(s['weight'] for s in TEST_SCENARIOS)
    overall_score = (total_weighted_score / total_weight) * 100
    
    avg_response_time = statistics.mean(r['avg_time'] for r in results)
    overall_success_rate = statistics.mean(r['success_rate'] for r in results)
    
    category_scores = {}
    for category in set(s['category'] for s in TEST_SCENARIOS):
        cat_results = [r for r in results if r['category'] == category]
        if cat_results:
            category_scores[category] = statistics.mean(r['avg_quality'] for r in cat_results) * 100
    
    return {
        "model": model['name'],
        "model_id": model['id'],
        "size": model['size'],
        "ram": model['ram'],
        "category": model['category'],
        "overall_score": overall_score,
        "success_rate": overall_success_rate * 100,
        "avg_response_time": avg_response_time,
        "category_scores": category_scores,
        "scenario_results": results
    }


async def main():
    """Run premium model benchmark."""
    
    print("="*70)
    print("SOPHIA PREMIUM LOCAL MODEL BENCHMARK")
    print("="*70)
    print(f"Testing {len(PREMIUM_MODELS)} premium models (10-30GB RAM)")
    print(f"Scenarios: {len(TEST_SCENARIOS)}, Runs per scenario: {RUNS_PER_SCENARIO}")
    print()
    
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found!")
        sys.exit(1)
    
    print(f"✅ API Key loaded")
    
    llm_tool = LLMTool()
    llm_tool.setup({})
    
    all_results = []
    
    for model in PREMIUM_MODELS:
        try:
            result = await benchmark_model(llm_tool, model)
            all_results.append(result)
        except Exception as e:
            print(f"❌ Failed to benchmark {model['name']}: {e}")
            continue
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"docs/benchmarks/premium_models_{timestamp}.json"
    
    os.makedirs("docs/benchmarks", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*70}")
    print("BENCHMARK RESULTS SUMMARY")
    print(f"{'='*70}\n")
    
    all_results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    print(f"{'Rank':<6} {'Model':<30} {'Size':<8} {'RAM':<10} {'Score':<8} {'Time':<8}")
    print("-" * 80)
    
    for i, result in enumerate(all_results, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        print(f"{rank_icon:<6} {result['model']:<30} {result['size']:<8} {result['ram']:<10} "
              f"{result['overall_score']:>6.1f}%  {result['avg_response_time']:>6.1f}s")
    
    print(f"\n📊 Results saved to: {output_file}")
    print(f"{'='*70}\n")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
