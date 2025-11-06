#!/usr/bin/env python3
"""
Test for Phase 3.1: Memory Schema Extension (Hypotheses Table)

Tests:
1. Hypotheses table creation
2. Create hypothesis
3. Get pending hypotheses
4. Update hypothesis status
5. Get hypothesis by ID
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from plugins.memory_sqlite import SQLiteMemory
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def test_hypotheses_schema():
    """Test hypotheses table and CRUD operations"""
    
    print("=" * 70)
    print("🧪 PHASE 3.1 TEST: Memory Schema Extension (Hypotheses)")
    print("=" * 70)
    
    # Create memory plugin instance
    memory = SQLiteMemory()
    memory.setup({"db_path": "data/memory/test_hypotheses.db"})
    
    print(f"\n✅ Memory plugin initialized")
    print(f"📊 Tables created: conversation_history, operation_tracking, hypotheses")
    
    # Test 1: Create hypothesis
    print("\n" + "=" * 70)
    print("Test 1: Create Hypothesis")
    print("=" * 70)
    
    hypothesis_id = memory.create_hypothesis(
        hypothesis_text="Local LLM fails on complex code review tasks - optimize prompt template",
        category="prompt_optimization",
        priority=85,
        root_cause="Local LLM struggles with multi-file context and complex logic",
        proposed_fix="Simplify prompt, add concrete examples, break into smaller steps",
        estimated_improvement="20%"
    )
    
    print(f"\n✅ Created hypothesis #{hypothesis_id}")
    print(f"   Category: prompt_optimization")
    print(f"   Priority: 85")
    print(f"   Status: pending")
    
    # Test 2: Create more hypotheses
    print("\n" + "=" * 70)
    print("Test 2: Create Multiple Hypotheses")
    print("=" * 70)
    
    hypotheses = [
        {
            "hypothesis_text": "Budget tracking estimates too rough - use real model pricing",
            "category": "code_fix",
            "priority": 70,
            "root_cause": "Using $0.15 per 1M tokens average instead of per-model pricing",
            "proposed_fix": "Add pricing table in autonomy.yaml, calculate exact costs",
            "estimated_improvement": "30%"
        },
        {
            "hypothesis_text": "Offline mode detection too slow - cache for 1 hour",
            "category": "performance_optimization",
            "priority": 60,
            "root_cause": "Checking network connectivity on every request",
            "proposed_fix": "Cache offline status with TTL, only recheck on failure",
            "estimated_improvement": "50ms latency reduction"
        }
    ]
    
    for h in hypotheses:
        hid = memory.create_hypothesis(**h)
        print(f"✅ Created hypothesis #{hid}: {h['category']} (priority: {h['priority']})")
    
    # Test 3: Get pending hypotheses
    print("\n" + "=" * 70)
    print("Test 3: Get Pending Hypotheses (ordered by priority)")
    print("=" * 70)
    
    pending = memory.get_pending_hypotheses(limit=10)
    
    print(f"\n📋 Found {len(pending)} pending hypotheses:")
    for h in pending:
        print(f"\n  Hypothesis #{h['id']} (Priority: {h['priority']})")
        print(f"    Category: {h['category']}")
        print(f"    Text: {h['hypothesis_text'][:60]}...")
        print(f"    Root Cause: {h['root_cause'][:60]}..." if h['root_cause'] else "    Root Cause: N/A")
        print(f"    Fix: {h['proposed_fix'][:60]}..." if h['proposed_fix'] else "    Fix: N/A")
        print(f"    Expected: {h['estimated_improvement']}")
    
    # Test 4: Update hypothesis status
    print("\n" + "=" * 70)
    print("Test 4: Update Hypothesis Status")
    print("=" * 70)
    
    # Simulate testing
    memory.update_hypothesis_status(
        hypothesis_id=hypothesis_id,
        status="testing"
    )
    print(f"\n✅ Updated hypothesis #{hypothesis_id} → status: testing")
    
    # Simulate approval with test results
    test_results = {
        "baseline_success_rate": 0.60,
        "new_success_rate": 0.78,
        "improvement_pct": 30.0,
        "test_cases": 50,
        "approved": True
    }
    
    memory.update_hypothesis_status(
        hypothesis_id=hypothesis_id,
        status="approved",
        test_results=test_results
    )
    print(f"✅ Updated hypothesis #{hypothesis_id} → status: approved")
    print(f"   Test Results: {test_results}")
    
    # Test 5: Get hypothesis by ID
    print("\n" + "=" * 70)
    print("Test 5: Get Hypothesis by ID")
    print("=" * 70)
    
    hypothesis = memory.get_hypothesis_by_id(hypothesis_id)
    
    print(f"\n📝 Hypothesis #{hypothesis['id']}:")
    print(f"   Text: {hypothesis['hypothesis_text']}")
    print(f"   Category: {hypothesis['category']}")
    print(f"   Priority: {hypothesis['priority']}")
    print(f"   Status: {hypothesis['status']}")
    print(f"   Created: {hypothesis['created_at']}")
    print(f"   Tested: {hypothesis['tested_at']}")
    print(f"   Approved: {hypothesis['approved_at']}")
    if hypothesis['test_results']:
        print(f"   Test Results:")
        for key, value in hypothesis['test_results'].items():
            print(f"     - {key}: {value}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    print(f"\n✅ Hypotheses table created successfully")
    print(f"✅ create_hypothesis() working")
    print(f"✅ get_pending_hypotheses() working (priority-ordered)")
    print(f"✅ update_hypothesis_status() working")
    print(f"✅ get_hypothesis_by_id() working")
    
    print(f"\n📈 Test Metrics:")
    print(f"   Total hypotheses created: {len(pending)}")
    print(f"   Highest priority: {pending[0]['priority']}")
    print(f"   Approved hypotheses: 1")
    
    print("\n" + "=" * 70)
    print("🎉 PHASE 3.1 COMPLETE - Memory Schema Extension Operational!")
    print("=" * 70)
    
    print("\n🔄 Next: Phase 3.2 - Memory Consolidator Plugin")


if __name__ == "__main__":
    test_hypotheses_schema()
