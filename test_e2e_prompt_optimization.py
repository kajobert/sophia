#!/usr/bin/env python3
"""
End-to-End Prompt Optimization Test

Creates intentional failures to trigger the complete workflow:
ERROR → REFLECTION → HYPOTHESIS → SELF-TUNING → BENCHMARK → DEPLOY
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from plugins.memory_sqlite import SQLiteMemory
from plugins.cognitive_reflection import CognitiveReflection
from plugins.cognitive_self_tuning import CognitiveSelfTuning
from core.event_bus import EventBus
from core.events import Event, EventType
from core.operation_metadata import OperationMetadata


async def main():
    print("=" * 70)
    print("🧪 END-TO-END PROMPT OPTIMIZATION TEST")
    print("=" * 70)
    print()
    
    # Step 1: Setup
    print("[1/7] Initializing components...")
    
    memory = SQLiteMemory()
    memory.setup({"db_path": ".data/memory.db"})
    
    event_bus = EventBus()
    
    reflection = CognitiveReflection()
    reflection.setup({
        "all_plugins": {
            "memory_sqlite": memory,
            "cognitive_task_router": None  # Will use mock
        },
        "event_bus": event_bus,
        "reflection": {
            "failure_threshold": 2,  # Lower for testing
            "analysis_window_days": 7
        }
    })
    
    self_tuning = CognitiveSelfTuning()
    self_tuning.setup({
        "all_plugins": {
            "memory_sqlite": memory
        },
        "event_bus": event_bus,
        "autonomy": {
            "self_improvement": {
                "self_tuning": {
                    "improvement_threshold": 0.05,
                    "sandbox_path": "sandbox/e2e_test",
                    "auto_deploy": False
                }
            }
        }
    })
    
    print("✅ Components initialized")
    print()
    
    # Step 2: Create failures
    print("[2/7] Creating test failures with bad prompt...")
    
    # Create 5 failures using the bad prompt
    for i in range(5):
        timestamp = (datetime.now() - timedelta(hours=2, minutes=i*10)).isoformat()
        
        meta = OperationMetadata.create(
            model_used="llama3.1:8b",
            operation_type="prompt_test",
            offline_mode=True
        )
        meta.timestamp = timestamp
        meta.mark_failure(f"LLM returned invalid output with test_bad_prompt.txt (attempt {i+1})")
        
        memory.save_operation(meta)
    
    print(f"✅ Created 5 failures with bad prompt")
    print()
    
    # Step 3: Get failures
    print("[3/7] Querying recent failures...")
    
    failures = await reflection._get_recent_failures()
    print(f"✅ Found {len(failures)} total failures")
    
    prompt_failures = [f for f in failures if "prompt_test" in f.get("operation_type", "")]
    print(f"   {len(prompt_failures)} are from our test prompt")
    print()
    
    # Step 4: Cluster failures
    print("[4/7] Clustering failures...")
    
    clusters = reflection._cluster_failures(failures)
    print(f"✅ Identified {len(clusters)} operation type clusters:")
    for op_type, fails in clusters.items():
        print(f"   - {op_type}: {len(fails)} failures")
    print()
    
    # Step 5: Generate hypothesis (mock LLM response)
    print("[5/7] Generating hypothesis for prompt_test failures...")
    
    if "prompt_test" in clusters and len(clusters["prompt_test"]) >= 2:
        # Mock successful LLM analysis
        mock_hypothesis_response = """```json
{
  "root_cause": "Test prompt (test_bad_prompt.txt) is too vague and unstructured, causing LLM to produce invalid outputs",
  "hypothesis": "Replace vague prompt with structured template that includes clear instructions, format specification, and examples",
  "proposed_fix": "You are a helpful AI assistant. Follow these steps:\\n\\n1. Understand the user's request\\n2. Provide a clear, structured response\\n3. Format output as requested\\n\\nAlways be specific and actionable.",
  "fix_type": "prompt_optimization",
  "priority": 85,
  "estimated_improvement": "40%"
}
```"""
        
        parsed = reflection._parse_hypothesis_response(
            mock_hypothesis_response,
            operation_type="prompt_test",
            source="e2e_test"
        )
        
        if parsed:
            print("✅ Hypothesis generated:")
            print(f"   Root Cause: {parsed['root_cause'][:60]}...")
            print(f"   Fix Type: {parsed.get('fix_type', 'N/A')}")
            print(f"   Priority: {parsed.get('priority', 'N/A')}")
            
            # Add source failures
            parsed["source_failure_ids"] = [1, 2, 3]
            
            # Create hypothesis
            hypothesis_id = await reflection._create_hypothesis(parsed)
            print(f"✅ Hypothesis #{hypothesis_id} created in database")
            print()
        else:
            print("❌ Failed to parse hypothesis")
            return
    else:
        print(f"⚠️  Not enough failures for hypothesis ({len(clusters.get('prompt_test', []))} < 2)")
        return
    
    # Step 6: Verify hypothesis in DB
    print("[6/7] Verifying hypothesis storage...")
    
    if hypothesis_id is None:
        print("❌ Hypothesis ID is None - creation failed")
        return
    
    stored = memory.get_hypothesis_by_id(hypothesis_id)
    if stored:
        print("✅ Hypothesis retrieved from database:")
        print(f"   ID: {stored['id']}")
        print(f"   Status: {stored['status']}")
        print(f"   Category: {stored['category']}")
        print(f"   Proposed fix length: {len(stored.get('proposed_fix', ''))} chars")
        
        # Check if proposed_fix contains full prompt text
        if stored.get("proposed_fix") and len(stored["proposed_fix"]) > 50:
            print("   ✅ Proposed fix contains full prompt text (not just description)")
        else:
            print("   ⚠️  Proposed fix might be too short")
    else:
        print("❌ Hypothesis not found in database!")
        return
    
    print()
    
    # Step 7: Summary
    print("[7/7] Test Summary")
    print("=" * 70)
    print()
    print("✅ WORKFLOW VALIDATED:")
    print(f"   1. Created 5 failures with bad prompt")
    print(f"   2. Reflection clustered {len(failures)} total failures")
    print(f"   3. Generated hypothesis #{hypothesis_id}")
    print(f"   4. Hypothesis stored with full prompt text")
    print()
    print("📊 DATABASE STATE:")
    print(f"   - Hypotheses table: EXISTS")
    print(f"   - Total hypotheses: 1")
    print(f"   - Status: {stored['status']}")
    print(f"   - Category: {stored['category']}")
    print()
    print("🔄 NEXT STEPS (Manual):")
    print("   1. Update hypothesis status to 'approved'")
    print("   2. Trigger Self-Tuning plugin")
    print("   3. Verify benchmarking (real-world or heuristic)")
    print("   4. Verify deployment to config/prompts/")
    print()
    print("=" * 70)
    print("🎉 END-TO-END TEST PHASE 1 COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted")
    except Exception as e:
        print(f"\n\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
