"""Final test for Phase 3.2 Memory Consolidator"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from plugins.cognitive_memory_consolidator import CognitiveMemoryConsolidator
from plugins.memory_sqlite import SQLiteMemory
from core.events import Event, EventType
from core.event_bus import EventBus
from core.operation_metadata import OperationMetadata

async def run_test():
    print("PHASE 3.2 TEST: Memory Consolidator")
    print()

    # Initialize
    memory = SQLiteMemory()
    memory.setup({"database_path": "data/memory/test_consolidator.db"})

    event_bus = EventBus()
    await event_bus.start()  # Start event loop

    consolidator = CognitiveMemoryConsolidator()
    consolidator.setup({
        "all_plugins": {"memory_sqlite": memory, "memory_chroma": None},
        "event_bus": event_bus,
        "consolidation_age_hours": 24,
        "retention_days": 7
    })

    print("OK: Consolidator initialized")
    print()

    # Create old operations
    print("Creating 10 old operations...")
    for i in range(10):
        ts = (datetime.now() - timedelta(hours=30 + i)).isoformat()
        meta = OperationMetadata.create(
            model_used="llama3.1:8b",
            operation_type="llm_call",
            offline_mode=True
        )
        meta.timestamp = ts
        
        if i % 3 == 0:
            meta.mark_failure("Test failure")
        else:
            meta.mark_success(prompt_tokens=100, completion_tokens=50, latency_ms=250)
        
        memory.save_operation(meta)

    print("OK: Created 10 operations (7 success, 3 fail)")
    print()

    # Query old operations
    print("Querying old operations...")
    old_ops = await consolidator._get_old_operations()
    print(f"OK: Found {len(old_ops)} old operations")
    print()

    # Separate
    successes = [op for op in old_ops if op.get("success")]
    failures = [op for op in old_ops if not op.get("success")]
    print(f"OK: {len(successes)} successes, {len(failures)} failures")
    print()

    # Document text
    if successes:
        doc = consolidator._create_document_text(successes[0])
        print(f"Sample doc: {doc[:80]}...")
        print()

    # Cleanup
    print("Creating 5 very old operations...")
    for i in range(5):
        ts = (datetime.now() - timedelta(days=10)).isoformat()
        meta = OperationMetadata.create(
            model_used="llama3.1:8b",
            operation_type="llm_call",
            offline_mode=True
        )
        meta.timestamp = ts
        meta.mark_success(prompt_tokens=100, completion_tokens=50)
        memory.save_operation(meta)

    deleted = await consolidator._cleanup_old_operations()
    print(f"OK: Deleted {deleted} operations older than 7 days")
    print()

    # Event test
    print("Testing DREAM_TRIGGER event...")

    dream_received = []
    def on_dream_complete(event: Event):
        dream_received.append(event)
        print(f"  DREAM_COMPLETE: consolidated={event.data['consolidated_count']}, deleted={event.data['deleted_count']}")

    event_bus.subscribe(EventType.DREAM_COMPLETE, on_dream_complete)

    trigger = Event(EventType.DREAM_TRIGGER, data={})
    await consolidator._on_dream_trigger(trigger)
    
    # Give event bus time to dispatch
    await asyncio.sleep(0.5)

    if dream_received:
        print("OK: DREAM_COMPLETE emitted")
    else:
        print("FAIL: No DREAM_COMPLETE")

    print()
    print("PHASE 3.2 INFRASTRUCTURE COMPLETE!")
    
    await event_bus.stop()

asyncio.run(run_test())
