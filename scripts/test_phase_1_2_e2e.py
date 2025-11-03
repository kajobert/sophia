#!/usr/bin/env python3
"""
Quick E2E Test for Phase 1.2 - EventBus Integration

This script runs a quick end-to-end test to verify that:
1. Sophia starts correctly with event-driven mode
2. Events are published during real operation
3. System responds to user input
4. Graceful shutdown works

Expected duration: ~10 minutes
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.kernel import Kernel
from core.events import Event, EventType


async def run_quick_e2e_test():
    """Run quick E2E test with automated inputs."""
    print("=" * 70)
    print("QUICK E2E TEST - Phase 1.2: EventBus Integration")
    print("=" * 70)
    print()
    
    # Track all events
    all_events = []
    
    def event_tracker(event: Event):
        """Track all events silently."""
        all_events.append(event)
    
    # Test scenarios
    test_inputs = [
        ("Simple greeting", "Hello, Sophia!"),
        ("Math question", "What is 2 + 2?"),
        ("Self-awareness", "Who are you?"),
    ]
    
    print("Test Configuration:")
    print(f"  - Event-driven mode: ENABLED")
    print(f"  - Test scenarios: {len(test_inputs)}")
    print(f"  - Event tracking: ACTIVE")
    print()
    
    results = []
    
    for test_name, user_input in test_inputs:
        print(f"\n{'─' * 70}")
        print(f"Test Scenario: {test_name}")
        print(f"Input: \"{user_input}\"")
        print(f"{'─' * 70}")
        
        # Clear events for this test
        scenario_events = []
        
        def scenario_tracker(event: Event):
            all_events.append(event)
            scenario_events.append(event)
        
        try:
            # Create fresh kernel for each test
            kernel = Kernel(use_event_driven=True)
            
            # Subscribe to all events
            await kernel.initialize()
            
            for event_type in EventType:
                kernel.event_bus.subscribe(event_type, scenario_tracker)
            
            # Run single input
            print("\n⏳ Processing...\n")
            await kernel.consciousness_loop(single_run_input=user_input)
            
            # Wait for events to settle
            await asyncio.sleep(0.5)
            
            # Analyze results
            event_types = [e.event_type for e in scenario_events]
            
            # Check for expected events
            has_startup = EventType.SYSTEM_STARTUP in event_types
            has_ready = EventType.SYSTEM_READY in event_types
            has_user_input = EventType.USER_INPUT in event_types
            has_shutdown = EventType.SYSTEM_SHUTDOWN in event_types
            
            # Success if all critical events present
            success = has_startup and has_ready and has_user_input and has_shutdown
            
            print(f"\n📊 Event Analysis:")
            print(f"  Total events: {len(scenario_events)}")
            print(f"  ✅ SYSTEM_STARTUP: {has_startup}")
            print(f"  ✅ SYSTEM_READY: {has_ready}")
            print(f"  ✅ USER_INPUT: {has_user_input}")
            print(f"  ✅ SYSTEM_SHUTDOWN: {has_shutdown}")
            
            # Get stats
            stats = kernel.event_bus.get_stats()
            print(f"\n📈 EventBus Stats:")
            print(f"  Published: {stats['events_published']}")
            print(f"  Processed: {stats['events_processed']}")
            print(f"  Failed: {stats['events_failed']}")
            
            results.append({
                "name": test_name,
                "success": success,
                "events": len(scenario_events),
                "failed": stats['events_failed']
            })
            
            if success:
                print(f"\n✅ Test PASSED: {test_name}")
            else:
                print(f"\n❌ Test FAILED: {test_name}")
            
        except Exception as e:
            print(f"\n❌ Test FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                "name": test_name,
                "success": False,
                "error": str(e)
            })
    
    # Final summary
    print("\n" + "=" * 70)
    print("E2E TEST SUMMARY")
    print("=" * 70)
    print()
    
    passed = sum(1 for r in results if r.get("success", False))
    total = len(results)
    
    print(f"Results: {passed}/{total} tests passed")
    print()
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result.get("success") else "❌ FAIL"
        print(f"  {i}. {result['name']}: {status}")
        if not result.get("success"):
            if "error" in result:
                print(f"     Error: {result['error']}")
    
    print()
    print(f"Total events tracked: {len(all_events)}")
    print()
    
    # Overall result
    all_passed = passed == total
    
    if all_passed:
        print("🎉 ALL TESTS PASSED - EventBus integration working correctly!")
        print()
        print("Next Steps:")
        print("  ✅ Phase 1.2 validated")
        print("  → Ready to proceed with Phase 1.3 (Task Queue)")
    else:
        print("⚠️  SOME TESTS FAILED - Review output above")
        print()
        print("Action Required:")
        print("  1. Fix identified issues")
        print("  2. Re-run this test")
        print("  3. Only proceed to Phase 1.3 after all tests pass")
    
    print()
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    try:
        result = asyncio.run(run_quick_e2e_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ TEST SUITE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
