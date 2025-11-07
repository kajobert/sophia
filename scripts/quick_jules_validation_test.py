#!/usr/bin/env python3
"""
Quick local model comparison for Jules plan validation.
Tests qwen2.5:14b vs llama3.1:8b vs gemma2:2b on simple validation task.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import subprocess

# Test case: Simple plan validation
SOPHIA_TASK = "Fix the timeout bug in benchmark_runner.py"

GOOD_PLAN = {
    "summary": "Increase timeout in benchmark_runner.py from 30s to 60s",
    "steps": [
        {"action": "edit_file", "file": "benchmark_runner.py", "changes": "timeout: 30 -> 60"}
    ],
    "files": ["benchmark_runner.py"]
}

BAD_PLAN = {
    "summary": "Modify test_runner.py timeout",
    "steps": [
        {"action": "edit_file", "file": "test_runner.py", "changes": "timeout: 30 -> 60"}
    ],
    "files": ["test_runner.py"]
}

PROMPT_TEMPLATE = """You are validating an AI coding plan.

TASK: {task}

PLAN:
Summary: {summary}
Files: {files}

Question: Does this plan correctly implement the task? Answer in JSON:
{{
  "approved": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "why"
}}

Output ONLY valid JSON, no other text."""


def call_ollama(model: str, prompt: str) -> str:
    """Call Ollama directly via curl."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
        }
    }
    
    result = subprocess.run(
        ["curl", "-s", "http://localhost:11434/api/generate", 
         "-d", json.dumps(payload)],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        return f"ERROR: {result.stderr}"
    
    try:
        response = json.loads(result.stdout)
        return response.get("response", "")
    except:
        return f"ERROR: Invalid JSON response"


def test_model(model: str, task: str, plan: dict, expected_approved: bool) -> dict:
    """Test one model on one plan."""
    prompt = PROMPT_TEMPLATE.format(
        task=task,
        summary=plan["summary"],
        files=plan["files"]
    )
    
    print(f"\n{'='*60}")
    print(f"Model: {model}")
    print(f"Expected: {'APPROVE' if expected_approved else 'REJECT'}")
    print(f"{'='*60}")
    
    response = call_ollama(model, prompt)
    
    print(f"Response:\n{response}\n")
    
    # Try to extract JSON
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > 0:
            json_str = response[start:end]
            parsed = json.loads(json_str)
            
            approved = parsed.get("approved", False)
            confidence = parsed.get("confidence", 0.0)
            reasoning = parsed.get("reasoning", "")
            
            correct = (approved == expected_approved)
            
            print(f"✅ Parsed JSON")
            print(f"   Approved: {approved} (expected: {expected_approved})")
            print(f"   Confidence: {confidence:.2f}")
            print(f"   Reasoning: {reasoning}")
            print(f"   Result: {'✅ CORRECT' if correct else '❌ WRONG'}")
            
            return {
                "model": model,
                "success": True,
                "correct": correct,
                "approved": approved,
                "confidence": confidence,
                "reasoning": reasoning
            }
        else:
            print(f"❌ No JSON found in response")
            return {"model": model, "success": False, "error": "No JSON"}
            
    except Exception as e:
        print(f"❌ Failed to parse: {e}")
        return {"model": model, "success": False, "error": str(e)}


def main():
    """Run quick comparison."""
    print("="*60)
    print("QUICK JULES PLAN VALIDATION TEST")
    print("="*60)
    print(f"\nTask: {SOPHIA_TASK}")
    print(f"\nGOOD PLAN: {GOOD_PLAN['summary']}")
    print(f"BAD PLAN: {BAD_PLAN['summary']}")
    
    models = ["qwen2.5:14b", "llama3.1:8b", "gemma2:2b"]
    
    results = []
    
    # Test GOOD plan (should approve)
    print("\n" + "="*60)
    print("TEST 1: GOOD PLAN (should approve)")
    print("="*60)
    
    for model in models:
        result = test_model(model, SOPHIA_TASK, GOOD_PLAN, expected_approved=True)
        results.append(result)
    
    # Test BAD plan (should reject)
    print("\n" + "="*60)
    print("TEST 2: BAD PLAN (should reject - wrong file!)")
    print("="*60)
    
    for model in models:
        result = test_model(model, SOPHIA_TASK, BAD_PLAN, expected_approved=False)
        results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for model in models:
        model_results = [r for r in results if r["model"] == model]
        correct = sum(1 for r in model_results if r.get("correct", False))
        total = len(model_results)
        accuracy = correct / total if total > 0 else 0.0
        
        print(f"\n{model}:")
        print(f"  Accuracy: {accuracy*100:.0f}% ({correct}/{total})")
        
        for r in model_results:
            if r.get("success"):
                status = "✅" if r.get("correct") else "❌"
                print(f"    {status} {r.get('reasoning', '')[:50]}...")
    
    # Recommendation
    print("\n" + "="*60)
    print("RECOMMENDATION")
    print("="*60)
    
    best = max(
        [r for r in results if r.get("success")],
        key=lambda x: sum(1 for r in results if r["model"] == x["model"] and r.get("correct", False)),
        default=None
    )
    
    if best:
        model_accuracy = sum(1 for r in results if r["model"] == best["model"] and r.get("correct", False)) / 2
        print(f"\nBest local model: {best['model']} ({model_accuracy*100:.0f}% accuracy)")
        
        if model_accuracy < 0.75:
            print("\n⚠️  WARNING: Even best local model below 75% threshold!")
            print("   Recommendation: Use cloud model (DeepSeek Chat $0.14/1M)")
    else:
        print("\n❌ All models failed to produce valid JSON!")
        print("   Recommendation: MUST use cloud model")


if __name__ == "__main__":
    main()
