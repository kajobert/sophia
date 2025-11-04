"""
End-to-End test for Phase 1 Event-Driven Architecture.

This test verifies that the event-driven consciousness loop works
correctly with the full Kernel initialization.
"""

import asyncio


# Test that kernel can initialize with event-driven mode
def test_kernel_event_driven_init():
    """Test that Kernel initializes with event-driven mode."""
    from core.kernel import Kernel

    # Create kernel with event-driven enabled
    kernel = Kernel(use_event_driven=True)

    assert kernel.use_event_driven is True
    assert kernel.event_bus is None  # Not initialized until initialize() is called
    assert kernel.task_queue is None


async def test_kernel_event_driven_initialization():
    """Test that Kernel properly initializes event-driven components."""
    from core.kernel import Kernel

    # Create kernel with event-driven enabled
    kernel = Kernel(use_event_driven=True)

    # Initialize kernel
    await kernel.initialize()

    # Verify event-driven components are created
    assert kernel.event_bus is not None
    assert kernel.task_queue is not None

    # Verify components are started
    assert kernel.event_bus._running is True
    assert kernel.task_queue._running is True

    # Cleanup
    await kernel.task_queue.stop()
    await kernel.event_bus.stop()


async def test_event_driven_loop_with_single_input():
    """Test event-driven loop with single input (non-interactive mode)."""
    from core.kernel import Kernel

    # Create kernel with event-driven enabled
    kernel = Kernel(use_event_driven=True)
    await kernel.initialize()

    # Track events
    events_received = []

    def track_event(event):
        events_received.append(event)

    # Subscribe to USER_INPUT events
    from core.events import EventType

    kernel.event_bus.subscribe(EventType.USER_INPUT, track_event)

    # Run consciousness loop with single input
    # Note: This will try to process the input but won't have full plugin setup
    # We're just testing that the event-driven loop runs without crashing
    try:
        # Use asyncio.wait_for to timeout if loop doesn't exit
        await asyncio.wait_for(
            kernel.consciousness_loop(single_run_input="test input"), timeout=5.0
        )
    except asyncio.TimeoutError:
        # If timeout, something is wrong
        assert False, "Consciousness loop didn't exit in single-run mode"

    # Verify at least one event was published
    await asyncio.sleep(0.2)  # Wait for event processing
    assert len(events_received) > 0, "No USER_INPUT events were published"

    # Find our test input event
    test_events = [e for e in events_received if e.data.get("input") == "test input"]
    assert len(test_events) > 0, "Test input event was not published"

    print(f"✅ Event-driven loop test passed! Received {len(events_received)} events")


if __name__ == "__main__":
    print("Running Phase 1 E2E tests...\n")

    print("1. Testing Kernel initialization with event-driven mode...")
    test_kernel_event_driven_init()
    print("   ✅ Passed\n")

    print("2. Testing event-driven component initialization...")
    asyncio.run(test_kernel_event_driven_initialization())
    print("   ✅ Passed\n")

    print("3. Testing event-driven loop with single input...")
    asyncio.run(test_event_driven_loop_with_single_input())
    print("   ✅ Passed\n")

    print("=" * 60)
    print("✅ ALL PHASE 1 E2E TESTS PASSED!")
    print("=" * 60)
