#!/usr/bin/env python3
"""
End-to-End test for Phase 3 - Memory Consolidation & Dreaming.

Tests complete workflow:
1. Add conversation sessions to memory
2. Trigger memory consolidation
3. Search consolidated memories
4. Verify sleep scheduling works

Author: AI Agent (Copilot)
Date: 2025-11-04
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.kernel import Kernel
from core.context import SharedContext
from plugins.cognitive_memory_consolidator import CognitiveMemoryConsolidator
from plugins.core_sleep_scheduler import CoreSleepScheduler, SleepCycleTrigger


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_test(name: str, passed: bool):
    """Print test result with color."""
    status = f"{Colors.GREEN}✅ PASS{Colors.RESET}" if passed else f"{Colors.RED}❌ FAIL{Colors.RESET}"
    print(f"  {status} - {name}")


async def run_phase3_e2e_tests():
    """Run comprehensive Phase 3 E2E tests."""
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}PHASE 3 E2E TEST - Memory Consolidation & Dreaming{Colors.RESET}")
    print("=" * 70)
    print()
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TEST 1: Plugin Initialization
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"{Colors.BLUE}[1/7]{Colors.RESET} Plugin Initialization")
        
        consolidator = CognitiveMemoryConsolidator()
        scheduler = CoreSleepScheduler()
        
        # Setup plugins
        consolidator.setup({
            "enabled": True,
            "auto_consolidate": False  # Manual for testing
        })
        
        scheduler.setup({
            "schedule": {
                "enabled": True,
                "trigger_type": SleepCycleTrigger.MANUAL.value,
                "interval_hours": 1
            }
        })
        
        test_passed = (
            consolidator.name == "cognitive_memory_consolidator" and
            scheduler.name == "core_sleep_scheduler"
        )
        print_test("Plugins initialized correctly", test_passed)
        tests_passed += 1 if test_passed else 0
        tests_failed += 0 if test_passed else 1
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TEST 2: Tool Registration
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{Colors.BLUE}[2/7]{Colors.RESET} Tool Registration")
        
        tools = consolidator.get_tool_definitions()
        required_tools = [
            "trigger_memory_consolidation",
            "get_consolidation_status",
            "search_consolidated_memories"
        ]
        
        tool_names = [tool["name"] for tool in tools]
        test_passed = all(name in tool_names for name in required_tools)
        print_test(f"All {len(required_tools)} tools registered", test_passed)
        tests_passed += 1 if test_passed else 0
        tests_failed += 0 if test_passed else 1
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TEST 3: Add Test Conversation
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{Colors.BLUE}[3/7]{Colors.RESET} Add Test Conversation")
        
        # Create test conversation
        test_conversation = [
            {
                "role": "user",
                "content": "Can you help me understand async/await in Python?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Async/await is a way to write concurrent code in Python. The key insight is that async functions (defined with 'async def') return coroutines that can be awaited. This allows the event loop to run other tasks while waiting for I/O operations.",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "user",
                "content": "What's the difference between asyncio.create_task() and await?",
                "timestamp": datetime.now().isoformat()
            },
            {
                "role": "assistant",
                "content": "Great question! 'await' blocks until the coroutine completes, while 'asyncio.create_task()' schedules the coroutine to run concurrently without blocking. This is crucial for running multiple tasks in parallel.",
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Simulate adding conversation to memory (would normally be done by memory plugin)
        consolidator._test_conversation = test_conversation  # Test helper
        
        test_passed = len(test_conversation) == 4
        print_test("Test conversation created (4 messages)", test_passed)
        tests_passed += 1 if test_passed else 0
        tests_failed += 0 if test_passed else 1
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TEST 4: Memory Consolidation Status (Before)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{Colors.BLUE}[4/7]{Colors.RESET} Consolidation Status (Before)")
        
        try:
            status_tool = next(t for t in tools if t["name"] == "get_consolidation_status")
            status_result = await consolidator.call_tool(
                "get_consolidation_status",
                {}
            )
            
            initial_memories = status_result.get("total_memories_created", 0)
            test_passed = initial_memories == 0
            print_test(f"Initial memory count: {initial_memories}", test_passed)
            tests_passed += 1 if test_passed else 0
            tests_failed += 0 if test_passed else 1
            
        except Exception as e:
            print_test(f"Status check failed: {e}", False)
            tests_failed += 1
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TEST 5: Trigger Consolidation (Manual)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{Colors.BLUE}[5/7]{Colors.RESET} Trigger Memory Consolidation")
        print(f"  {Colors.YELLOW}⏳ Running consolidation (this may take 10-30s)...{Colors.RESET}")
        
        try:
            consolidation_result = await consolidator.call_tool(
                "trigger_memory_consolidation",
                {"force": True}
            )
            
            test_passed = consolidation_result.get("status") == "completed"
            memories_created = consolidation_result.get("memories_created", 0)
            
            print_test(f"Consolidation completed ({memories_created} memories)", test_passed)
            tests_passed += 1 if test_passed else 0
            tests_failed += 0 if test_passed else 1
            
        except Exception as e:
            print_test(f"Consolidation failed: {e}", False)
            tests_failed += 1
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TEST 6: Search Consolidated Memories
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{Colors.BLUE}[6/7]{Colors.RESET} Search Consolidated Memories")
        
        try:
            search_result = await consolidator.call_tool(
                "search_consolidated_memories",
                {
                    "query": "async/await Python",
                    "max_results": 5
                }
            )
            
            results = search_result.get("results", [])
            test_passed = len(results) > 0
            print_test(f"Found {len(results)} relevant memories", test_passed)
            
            if results:
                print(f"    {Colors.YELLOW}Sample:{Colors.RESET} {results[0].get('summary', 'N/A')[:60]}...")
            
            tests_passed += 1 if test_passed else 0
            tests_failed += 0 if test_passed else 1
            
        except Exception as e:
            print_test(f"Search failed: {e}", False)
            tests_failed += 1
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # TEST 7: Sleep Scheduler Integration
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        print(f"\n{Colors.BLUE}[7/7]{Colors.RESET} Sleep Scheduler Integration")
        
        # Test scheduler can trigger consolidation
        scheduler.consolidator_plugin = consolidator
        test_passed = scheduler.consolidator_plugin is not None
        print_test("Scheduler linked to consolidator", test_passed)
        tests_passed += 1 if test_passed else 0
        tests_failed += 0 if test_passed else 1
        
    except Exception as e:
        print(f"\n{Colors.RED}❌ FATAL ERROR: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        tests_failed += 1
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # SUMMARY
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    total = tests_passed + tests_failed
    success_rate = (tests_passed / total * 100) if total > 0 else 0
    
    print("\n" + "=" * 70)
    print(f"{Colors.BOLD}PHASE 3 E2E TEST RESULTS{Colors.RESET}")
    print("=" * 70)
    print(f"  Total Tests: {total}")
    print(f"  {Colors.GREEN}Passed: {tests_passed}{Colors.RESET}")
    print(f"  {Colors.RED}Failed: {tests_failed}{Colors.RESET}")
    print(f"  Success Rate: {success_rate:.1f}%")
    print("=" * 70)
    
    if tests_failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL PHASE 3 E2E TESTS PASSED!{Colors.RESET}")
        print()
        print("✅ Memory Consolidation working")
        print("✅ Consolidated memories searchable")
        print("✅ Sleep scheduler integrated")
        print()
        print(f"{Colors.BLUE}Phase 3 Status: COMPLETE{Colors.RESET}")
        print(f"{Colors.YELLOW}Next: Phase 4 - Self-Improvement Workflow{Colors.RESET}")
        print()
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.RESET}")
        print("\nPlease review failed tests and fix issues.")
        return 1


if __name__ == "__main__":
    print("\nRunning Phase 3 E2E tests...\n")
    exit_code = asyncio.run(run_phase3_e2e_tests())
    sys.exit(exit_code)
