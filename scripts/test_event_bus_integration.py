#!/usr/bin/env python3
"""
Test script for Phase 1.2: EventBus integration with Kernel.

This script tests that:
1. EventBus can be initialized in Kernel
2. Events are published during consciousness loop
3. System shuts down gracefully
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.kernel import Kernel
from core.events import Event, EventType


async def test_event_bus_integration():
    """Test EventBus integration with Kernel."""
    print("=" * 60)
    print("Phase 1.2: Testing EventBus Integration")
    print("=" * 60)
    
    # Track events
    received_events = []
    
    def event_logger(event: Event):
        """Log all events."""
        received_events.append(event)
        print(f"📨 Event: {event.event_type.value} from {event.source}")
        print(f"   Priority: {event.priority.name}")
        if event.data:
            print(f"   Data: {event.data}")
        print()
    
    # Create kernel with event-driven mode
    print("\n1. Creating Kernel with event-driven mode...")
    kernel = Kernel(use_event_driven=True)
    
    # Initialize
    print("2. Initializing Kernel...")
    await kernel.initialize()
    
    # Verify event bus exists
    assert kernel.event_bus is not None, "EventBus should be initialized"
    assert kernel.event_bus._running, "EventBus should be running"
    print("   ✅ EventBus initialized and running")
    
    # Subscribe to all events
    print("\n3. Subscribing to events...")
    for event_type in EventType:
        kernel.event_bus.subscribe(event_type, event_logger)
    print(f"   ✅ Subscribed to {len(EventType)} event types")
    
    # Run single input
    print("\n4. Running consciousness loop with single input...")
    print("   Input: 'Hello, Sophia! This is a test.'")
    await kernel.consciousness_loop(single_run_input="Hello, Sophia! This is a test.")
    
    # Wait for events to process
    await asyncio.sleep(1)
    
    # Analyze results
    print("\n5. Analyzing results...")
    print(f"   Total events received: {len(received_events)}")
    
    # Check for expected events
    event_types_received = [e.event_type for e in received_events]
    
    expected_events = [
        EventType.SYSTEM_STARTUP,
        EventType.SYSTEM_READY,
        EventType.USER_INPUT,
        EventType.SYSTEM_SHUTDOWN,
    ]
    
    for expected in expected_events:
        if expected in event_types_received:
            print(f"   ✅ {expected.value} event received")
        else:
            print(f"   ❌ {expected.value} event NOT received")
    
    # Get statistics
    stats = kernel.event_bus.get_stats()
    print(f"\n6. EventBus Statistics:")
    print(f"   Events published: {stats['events_published']}")
    print(f"   Events processed: {stats['events_processed']}")
    print(f"   Handlers executed: {stats['handlers_executed']}")
    print(f"   Events failed: {stats['events_failed']}")
    
    # Success criteria
    print("\n" + "=" * 60)
    success = (
        EventType.SYSTEM_STARTUP in event_types_received and
        EventType.SYSTEM_READY in event_types_received and
        EventType.USER_INPUT in event_types_received and
        EventType.SYSTEM_SHUTDOWN in event_types_received and
        stats['events_failed'] == 0
    )
    
    if success:
        print("✅ TEST PASSED - EventBus integration successful!")
    else:
        print("❌ TEST FAILED - Check output above")
    
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(test_event_bus_integration())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED WITH EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
