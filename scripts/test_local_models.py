#!/usr/bin/env python3
"""
Local Model Benchmark for Sophia

Tests models that can run locally on a powerful PC (Lenovo Legend).
Evaluates which local models meet Sophia's requirements for:
- Reasoning ability
- Code understanding
- Tool use capability
- Consistency
- Speed

Models tested (available for local deployment):
- Gemma 2 2B/9B/27B (Google)
- Llama 3/3.1/3.2 3B/8B/70B (Meta)
- Mistral 7B/Nemo 12B (Mistral AI)
- Phi-3 Mini/Medium (Microsoft)
- Qwen 2.5 7B/14B/32B (Alibaba)
- DeepSeek Coder 6.7B (DeepSeek)

Usage:
    python scripts/test_local_models.py
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

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import SharedContext
from plugins.tool_llm import LLMTool
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================================================
# LOCAL MODELS TO TEST (Available on OpenRouter + Can run locally)
# ============================================================================

LOCAL_MODELS = [
    # Small models - testovat rychlé a levné varianty
    {
        "name": "Llama 3.1 8B",
        "id": "openrouter/meta-llama/llama-3.1-8b-instruct",
        "size": "8B",
        "ram": "10GB",
        "category": "small"
    },
    {
        "name": "Mistral 7B",
        "id": "openrouter/mistralai/mistral-7b-instruct",
        "size": "7B",
        "ram": "8GB",
        "category": "small"
    },
    {
        "name": "Qwen 2.5 7B",
        "id": "openrouter/qwen/qwen-2.5-7b-instruct",
        "size": "7B",
        "ram": "8GB",
        "category": "small"
    },
    
    # Medium models - vyvážený výkon/cena
    {
        "name": "Gemma 2 9B",
        "id": "openrouter/google/gemma-2-9b-it",
        "size": "9B",
        "ram": "12GB",
        "category": "medium"
    },
    {
        "name": "Qwen 2.5 Coder 7B",
        "id": "openrouter/qwen/qwen2.5-coder-7b-instruct",
        "size": "7B",
        "ram": "8GB",
        "category": "coding"
    },
]

# ============================================================================
# TEST SCENARIOS (Real Sophia use cases)
# ============================================================================

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
        "name": "Tool Use - File System",
        "prompt": "I want to read a file named 'config.yaml'. Which tool should I use and what parameters? Answer with just the tool name and parameters.",
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
        "prompt": "Write a Python function that checks if a number is prime. Be concise, just the function.",
        "expected_keywords": ["def", "prime", "return", "range"],
        "weight": 2.0,
        "category": "coding"
    },
    {
        "name": "Multi-Step Logic",
        "prompt": "If A=10, B=A*2, C=B+A, what is C? Explain briefly.",
        "expected_keywords": ["30", "20", "10"],
        "weight": 2.0,
        "category": "reasoning"
    },
    {
        "name": "Error Handling",
        "prompt": "What should I do if tool_file_system.read_file returns 'File not found'? One sentence.",
        "expected_keywords": ["check", "path", "exists", "error", "verify"],
        "weight": 2.5,
        "category": "reasoning"
    },
]

RUNS_PER_SCENARIO = 2  # Run each scenario twice for consistency


async def run_test(llm_tool: LLMTool, model_id: str, scenario: Dict, run_num: int) -> Dict:
    """Run a single test scenario."""
    
    # Rate limiting: Free models = 16 req/min → wait 4s between requests
    await asyncio.sleep(4)
    
    start_time = datetime.now()
    
    try:
        context = SharedContext(
            session_id=f"local_bench_{run_num}",
            current_state="EXECUTING",
            logger=logger,
            user_input=scenario['prompt'],
            history=[]
        )
        
        context.payload = {
            "prompt": scenario['prompt'],
            "model_config": {
                "model": model_id
            }
        }
        
        result_context = await llm_tool.execute(context=context)
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds()
        
        response = result_context.payload.get("llm_response", "")
        if not isinstance(response, str):
            response = str(response)
        
        # Score based on keyword presence
        response_lower = response.lower()
        keywords_found = sum(1 for kw in scenario['expected_keywords'] 
                           if kw.lower() in response_lower)
        keyword_score = keywords_found / len(scenario['expected_keywords'])
        
        # Check for refusal/error
        refusal_indicators = ["cannot", "unable", "don't have", "can't help", "error", "sorry"]
        refused = any(ind in response_lower for ind in refusal_indicators)
        
        # Quality score
        quality = 0.0
        if not refused:
            quality = keyword_score
            # Bonus for concise answers
            if len(response) < 500:
                quality += 0.1
        
        return {
            "success": not refused,
            "response": response[:200],  # Truncate for logging
            "keywords_found": keywords_found,
            "keyword_score": keyword_score,
            "quality": min(1.0, quality),
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
    """Benchmark a single model across all scenarios."""
    
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
        
        # Aggregate results
        avg_quality = statistics.mean(r['quality'] for r in scenario_results)
        avg_time = statistics.mean(r['response_time'] for r in scenario_results)
        success_rate = sum(1 for r in scenario_results if r['success']) / len(scenario_results)
        
        # Weighted score
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
    
    # Calculate overall scores
    total_weighted_score = sum(r['weighted_score'] for r in results)
    total_weight = sum(s['weight'] for s in TEST_SCENARIOS)
    overall_score = (total_weighted_score / total_weight) * 100
    
    avg_response_time = statistics.mean(r['avg_time'] for r in results)
    overall_success_rate = statistics.mean(r['success_rate'] for r in results)
    
    # Category scores
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
    """Run benchmark for all local models."""
    
    print("="*70)
    print("SOPHIA LOCAL MODEL BENCHMARK")
    print("="*70)
    print(f"Testing {len(LOCAL_MODELS)} models across {len(TEST_SCENARIOS)} scenarios")
    print(f"Runs per scenario: {RUNS_PER_SCENARIO}")
    print()
    
    # Load API key from .env file
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check if API key is available
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY not found in environment!")
        print("   Please add it to your .env file or export it:")
        print("   export OPENROUTER_API_KEY=your-key-here")
        sys.exit(1)
    
    print(f"✅ API Key loaded: {api_key[:20]}...")
    
    # Initialize LLM tool
    llm_tool = LLMTool()
    llm_tool.setup({})
    
    all_results = []
    
    for model in LOCAL_MODELS:
        try:
            result = await benchmark_model(llm_tool, model)
            all_results.append(result)
        except Exception as e:
            print(f"❌ Failed to benchmark {model['name']}: {e}")
            continue
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"docs/benchmarks/local_models_{timestamp}.json"
    
    os.makedirs("docs/benchmarks", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*70}")
    print("BENCHMARK RESULTS SUMMARY")
    print(f"{'='*70}\n")
    
    # Sort by overall score
    all_results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    # Print summary table
    print(f"{'Rank':<6} {'Model':<25} {'Size':<8} {'RAM':<10} {'Score':<8} {'Success':<9} {'Time':<8}")
    print("-" * 80)
    
    for i, result in enumerate(all_results, 1):
        rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        print(f"{rank_icon:<6} {result['model']:<25} {result['size']:<8} {result['ram']:<10} "
              f"{result['overall_score']:>6.1f}%  {result['success_rate']:>6.1f}%  {result['avg_response_time']:>6.1f}s")
    
    print("\n" + "="*70)
    print("CATEGORY BREAKDOWN (Top 3 models)")
    print("="*70 + "\n")
    
    categories = ["reasoning", "coding", "tool_use", "planning"]
    for category in categories:
        print(f"\n{category.upper()}:")
        # Sort by category score
        cat_sorted = sorted(all_results, 
                          key=lambda x: x['category_scores'].get(category, 0), 
                          reverse=True)[:3]
        
        for i, result in enumerate(cat_sorted, 1):
            score = result['category_scores'].get(category, 0)
            print(f"  {i}. {result['model']:<25} {score:>5.1f}%")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS FOR LENOVO LEGEND")
    print("="*70 + "\n")
    
    # Recommendations by RAM tier
    print("✅ SMALL MODELS (4-8GB RAM):")
    small_models = [r for r in all_results if r['category'] == 'small']
    small_models.sort(key=lambda x: x['overall_score'], reverse=True)
    for r in small_models[:3]:
        print(f"   {r['model']:<25} Score: {r['overall_score']:.1f}%")
    
    print("\n✅ MEDIUM MODELS (10-16GB RAM):")
    medium_models = [r for r in all_results if r['category'] == 'medium']
    medium_models.sort(key=lambda x: x['overall_score'], reverse=True)
    for r in medium_models[:3]:
        print(f"   {r['model']:<25} Score: {r['overall_score']:.1f}%")
    
    print("\n✅ LARGE MODELS (32GB+ RAM or GPU):")
    large_models = [r for r in all_results if r['category'] == 'large']
    large_models.sort(key=lambda x: x['overall_score'], reverse=True)
    for r in large_models[:2]:
        print(f"   {r['model']:<25} Score: {r['overall_score']:.1f}%")
    
    print("\n✅ CODING SPECIALISTS:")
    coding_models = [r for r in all_results if r['category'] == 'coding']
    coding_models.sort(key=lambda x: x['category_scores'].get('coding', 0), reverse=True)
    for r in coding_models[:2]:
        print(f"   {r['model']:<25} Coding: {r['category_scores'].get('coding', 0):.1f}%")
    
    print(f"\n📊 Full results saved to: {output_file}")
    print(f"{'='*70}\n")
    
    return all_results


if __name__ == "__main__":
    asyncio.run(main())
