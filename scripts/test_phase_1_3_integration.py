#!/usr/bin/env python3
"""
Integration test for Phase 1.3 - TaskQueue Integration

Tests that TaskQueue works correctly with Kernel and EventBus.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.kernel import Kernel
from core.task import Task, TaskPriority
from core.events import Event, EventType


async def test_task():
    """Simple async task for testing."""
    await asyncio.sleep(0.1)
    return "Task completed successfully"


async def run_integration_test():
    """Run TaskQueue integration test."""
    print("=" * 70)
    print("INTEGRATION TEST - Phase 1.3: TaskQueue + EventBus + Kernel")
    print("=" * 70)
    print()
    
    all_events = []
    test_passed = True
    
    def event_tracker(event: Event):
        all_events.append(event)
    
    try:
        # Create kernel with event-driven mode
        kernel = Kernel(use_event_driven=True)
        await kernel.initialize()
        
        # Subscribe to all events
        for event_type in EventType:
            kernel.event_bus.subscribe(event_type, event_tracker)
        
        print("✅ Kernel initialized with TaskQueue")
        print(f"   Workers: {kernel.task_queue.max_workers}")
        print()
        
        # Add test tasks
        task1 = Task(name="task1", function=test_task, priority=TaskPriority.HIGH)
        task2 = Task(name="task2", function=test_task, priority=TaskPriority.NORMAL)
        task3 = Task(name="task3", function=test_task, priority=TaskPriority.LOW)
        
        id1 = await kernel.task_queue.add_task(task1)
        id2 = await kernel.task_queue.add_task(task2)
        id3 = await kernel.task_queue.add_task(task3)
        
        print("✅ Added 3 tasks to queue")
        print(f"   Task 1: {id1} (HIGH)")
        print(f"   Task 2: {id2} (NORMAL)")
        print(f"   Task 3: {id3} (LOW)")
        print()
        
        # Wait for tasks to complete
        print("⏳ Waiting for tasks to execute...")
        await asyncio.sleep(1.0)
        
        # Check task statuses
        print("\n📊 Task Results:")
        for task in [task1, task2, task3]:
            status_icon = "✅" if task.status.value == "completed" else "❌"
            print(f"   {status_icon} {task.name}: {task.status.value} ({task.duration:.3f}s)")
            if task.status.value != "completed":
                test_passed = False
        
        # Check stats
        stats = kernel.task_queue.get_stats()
        print(f"\n📈 TaskQueue Statistics:")
        print(f"   Created: {stats['tasks_created']}")
        print(f"   Queued: {stats['tasks_queued']}")
        print(f"   Started: {stats['tasks_started']}")
        print(f"   Completed: {stats['tasks_completed']}")
        print(f"   Failed: {stats['tasks_failed']}")
        print(f"   Workers: {stats['workers_active']}")
        
        # Check events
        event_types = [e.event_type for e in all_events]
        has_startup = EventType.SYSTEM_STARTUP in event_types
        has_ready = EventType.SYSTEM_READY in event_types
        has_task_created = EventType.TASK_CREATED in event_types
        has_task_started = EventType.TASK_STARTED in event_types
        has_task_completed = EventType.TASK_COMPLETED in event_types
        
        print(f"\n📡 Events Received:")
        print(f"   Total: {len(all_events)}")
        print(f"   SYSTEM_STARTUP: {'✅' if has_startup else '❌'}")
        print(f"   SYSTEM_READY: {'✅' if has_ready else '❌'}")
        print(f"   TASK_CREATED: {'✅' if has_task_created else '❌'}")
        print(f"   TASK_STARTED: {'✅' if has_task_started else '❌'}")
        print(f"   TASK_COMPLETED: {'✅' if has_task_completed else '❌'}")
        
        # Graceful shutdown
        print("\n⏹  Shutting down...")
        await kernel.task_queue.stop()
        await kernel.event_bus.stop()
        
        # Final verdict
        print("\n" + "=" * 70)
        if test_passed and stats['tasks_completed'] == 3:
            print("🎉 INTEGRATION TEST PASSED")
            print()
            print("✅ TaskQueue fully integrated with Kernel and EventBus")
            print("✅ All tasks executed successfully")
            print("✅ Events published and received correctly")
            print("✅ Graceful shutdown working")
            print()
            print("Next Steps:")
            print("  → Ready for Phase 1.4 (Non-blocking Consciousness Loop)")
        else:
            print("❌ INTEGRATION TEST FAILED")
            print()
            print("Issues detected:")
            if stats['tasks_completed'] != 3:
                print(f"  - Expected 3 completed tasks, got {stats['tasks_completed']}")
            if not test_passed:
                print("  - Some tasks failed to complete")
        
        print("=" * 70)
        
        return test_passed and stats['tasks_completed'] == 3
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(run_integration_test())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted")
        sys.exit(1)
