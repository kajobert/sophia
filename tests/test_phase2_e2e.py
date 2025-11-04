"""
End-to-End test for Phase 2 Background Process Management.

This test verifies that:
1. Process Manager can run background processes
2. Events are emitted correctly
3. Integration with Event Bus works
4. Multiple processes can run concurrently
"""

import asyncio
from core.kernel import Kernel
from core.events import EventType


async def test_process_manager_integration():
    """Test Process Manager with full Kernel integration."""
    print("1. Initializing Kernel with event-driven mode...")
    kernel = Kernel(use_event_driven=True)
    await kernel.initialize()

    # Get Process Manager plugin
    process_manager = kernel.all_plugins_map.get("core_process_manager")
    assert process_manager is not None, "Process Manager plugin not loaded!"
    print("   ✅ Process Manager loaded")

    # Track events
    events_received = []

    def track_event(event):
        events_received.append(event)

    kernel.event_bus.subscribe(EventType.PROCESS_STARTED, track_event)
    kernel.event_bus.subscribe(EventType.PROCESS_STOPPED, track_event)
    kernel.event_bus.subscribe(EventType.PROCESS_FAILED, track_event)

    print("\n2. Starting background process (echo test)...")
    from core.context import SharedContext
    from unittest.mock import Mock

    context = SharedContext(session_id="test-e2e", current_state="TESTING", logger=Mock())
    context.event_bus = kernel.event_bus

    # Start a simple process
    result = await process_manager.start_background_process(
        context=context,
        process_type="test_suite",
        name="E2E Test",
        command="echo 'Phase 2 Works!' && sleep 0.1",
        timeout=5,
    )

    assert result["success"] is True, f"Failed to start process: {result}"
    process_id = result["process_id"]
    print(f"   ✅ Process started: {process_id}")

    print("\n3. Waiting for process completion...")
    await asyncio.sleep(1)

    # Check process status
    status = await process_manager.get_process_status(context, process_id)
    assert status["success"] is True
    assert status["state"] == "completed"
    assert "Phase 2 Works!" in status["output"]
    print(f"   ✅ Process completed with output: {status['output'].strip()}")

    print("\n4. Verifying events...")
    await asyncio.sleep(0.5)  # Wait for event processing

    started_events = [e for e in events_received if e.event_type == EventType.PROCESS_STARTED]
    stopped_events = [e for e in events_received if e.event_type == EventType.PROCESS_STOPPED]

    assert len(started_events) >= 1, "PROCESS_STARTED event not received!"
    assert len(stopped_events) >= 1, "PROCESS_STOPPED event not received!"
    print(f"   ✅ Received {len(started_events)} PROCESS_STARTED events")
    print(f"   ✅ Received {len(stopped_events)} PROCESS_STOPPED events")

    print("\n5. Testing concurrent processes...")
    # Start 3 concurrent processes
    tasks = []
    for i in range(3):
        task = process_manager.start_background_process(
            context=context,
            process_type="custom",
            name=f"Concurrent {i}",
            command=f"echo 'Process {i}' && sleep 0.1",
            timeout=5,
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)
    assert all(r["success"] for r in results)
    print(f"   ✅ Started {len(results)} concurrent processes")

    # Wait for all to complete
    await asyncio.sleep(1)

    # List processes
    list_result = await process_manager.list_background_processes(context, "completed")
    assert list_result["success"] is True
    assert list_result["count"] >= 4  # E2E test + 3 concurrent
    print(f"   ✅ {list_result['count']} processes completed successfully")

    print("\n6. Cleanup...")
    await kernel.task_queue.stop()
    await kernel.event_bus.stop()
    print("   ✅ Cleanup complete")

    print("\n" + "=" * 60)
    print("✅ PHASE 2 E2E TEST PASSED!")
    print("=" * 60)


async def test_process_failure_handling():
    """Test that process failures are handled correctly."""
    print("\n" + "=" * 60)
    print("Testing Process Failure Handling...")
    print("=" * 60)

    kernel = Kernel(use_event_driven=True)
    await kernel.initialize()

    process_manager = kernel.all_plugins_map.get("core_process_manager")

    # Track failure events
    failure_events = []

    def track_failure(event):
        failure_events.append(event)

    kernel.event_bus.subscribe(EventType.PROCESS_FAILED, track_failure)

    from core.context import SharedContext
    from unittest.mock import Mock

    context = SharedContext(session_id="test-failure", current_state="TESTING", logger=Mock())
    context.event_bus = kernel.event_bus

    print("\n1. Starting process that will fail...")
    result = await process_manager.start_background_process(
        context=context,
        process_type="test_suite",
        name="Failing Test",
        command="echo 'Starting...' && exit 1",  # Exit with error
        timeout=5,
    )

    process_id = result["process_id"]
    print(f"   ✅ Process started: {process_id}")

    print("\n2. Waiting for failure...")
    await asyncio.sleep(1)

    # Check status
    status = await process_manager.get_process_status(context, process_id)
    assert status["state"] == "failed"
    assert status["exit_code"] == 1
    print(f"   ✅ Process failed as expected (exit code: {status['exit_code']})")

    print("\n3. Verifying PROCESS_FAILED event...")
    await asyncio.sleep(0.5)

    assert len(failure_events) >= 1, "PROCESS_FAILED event not received!"
    print(f"   ✅ Received {len(failure_events)} PROCESS_FAILED events")

    # Cleanup
    await kernel.task_queue.stop()
    await kernel.event_bus.stop()

    print("\n✅ Failure handling test passed!")


if __name__ == "__main__":
    print("Running Phase 2 E2E tests...\n")

    asyncio.run(test_process_manager_integration())
    asyncio.run(test_process_failure_handling())

    print("\n" + "=" * 60)
    print("✅ ALL PHASE 2 E2E TESTS PASSED!")
    print("=" * 60)
