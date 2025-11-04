#!/usr/bin/env python3
"""
Test script for Phase 1: Operation Tracking Foundation

Tests:
1. Schema extension (operation_tracking table)
2. OperationMetadata creation and serialization
3. Saving operations to SQLite
4. Querying unevaluated offline operations
5. Updating quality scores
6. Getting statistics

Run: python scripts/test_phase1.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.operation_metadata import OperationMetadata, track_operation
from plugins.memory_sqlite import SQLiteMemory
from datetime import datetime, timedelta


def test_operation_metadata():
    """Test OperationMetadata class."""
    print("🧪 Test 1: OperationMetadata creation...")
    
    # Create metadata
    metadata = OperationMetadata.create(
        model_used="llama3.1:8b",
        operation_type="planning",
        offline_mode=True,
        session_id="test-session-1"
    )
    
    assert metadata.model_used == "llama3.1:8b"
    assert metadata.model_type == "local"
    assert metadata.operation_type == "planning"
    assert metadata.offline_mode == True
    assert metadata.success == False  # Not marked yet
    
    # Mark success
    metadata.mark_success(prompt_tokens=150, completion_tokens=80, latency_ms=2500)
    
    assert metadata.success == True
    assert metadata.total_tokens == 230
    assert metadata.latency_ms == 2500
    
    # Test serialization
    json_str = metadata.to_json()
    restored = OperationMetadata.from_json(json_str)
    
    assert restored.operation_id == metadata.operation_id
    assert restored.model_used == metadata.model_used
    assert restored.total_tokens == metadata.total_tokens
    
    print("✅ OperationMetadata tests passed")


def test_sqlite_operation_tracking():
    """Test SQLite operation tracking."""
    print("\n🧪 Test 2: SQLite operation tracking...")
    
    # Initialize SQLite plugin
    config = {"db_path": "data/memory/test_sophia_memory.db"}
    sqlite_plugin = SQLiteMemory()
    sqlite_plugin.setup(config)
    
    # Create test operations
    operations = [
        OperationMetadata.create(
            model_used="llama3.1:8b",
            operation_type="planning",
            offline_mode=True,
            session_id="test-session-1"
        ),
        OperationMetadata.create(
            model_used="openrouter/deepseek/deepseek-chat",
            operation_type="response",
            offline_mode=False,
            session_id="test-session-1"
        ),
        OperationMetadata.create(
            model_used="llama3.1:8b",
            operation_type="consolidation",
            offline_mode=True,
            session_id="test-session-2"
        ),
    ]
    
    # Mark some as successful
    operations[0].mark_success(prompt_tokens=150, completion_tokens=80, latency_ms=2500)
    operations[1].mark_success(prompt_tokens=200, completion_tokens=120, latency_ms=1800)
    operations[2].mark_failure("Network timeout")
    
    # Save to database
    for op in operations:
        sqlite_plugin.save_operation(op)
    
    print(f"✅ Saved {len(operations)} operations to database")
    
    # Query unevaluated offline operations
    unevaluated = sqlite_plugin.get_unevaluated_offline_operations()
    
    print(f"📊 Found {len(unevaluated)} unevaluated offline operations:")
    for op in unevaluated:
        print(f"  - {op.operation_id[:8]}... | {op.model_used} | {op.operation_type} | success={op.success}")
    
    assert len(unevaluated) >= 2  # At least 2 offline operations
    
    # Update quality score for first operation
    first_op = unevaluated[0]
    sqlite_plugin.update_operation_quality(
        operation_id=first_op.operation_id,
        quality_score=0.78,
        evaluation_model="openrouter/deepseek/deepseek-chat",
        evaluated_at=datetime.now().isoformat()
    )
    
    print(f"✅ Updated quality score for operation {first_op.operation_id[:8]}...")
    
    # Verify unevaluated count decreased
    unevaluated_after = sqlite_plugin.get_unevaluated_offline_operations()
    assert len(unevaluated_after) == len(unevaluated) - 1
    
    print(f"✅ Unevaluated count decreased: {len(unevaluated)} → {len(unevaluated_after)}")
    
    # Get statistics
    stats = sqlite_plugin.get_operation_statistics(days=7)
    
    print("\n📊 Operation Statistics (Last 7 Days):")
    print(f"  Total operations:     {stats['total_operations']}")
    print(f"  Offline operations:   {stats['offline_operations']} ({stats['offline_percentage']:.1f}%)")
    print(f"  Online operations:    {stats['online_operations']}")
    print(f"  Offline avg quality:  {stats['offline_avg_quality'] or 'N/A'}")
    print(f"  Online avg quality:   {stats['online_avg_quality'] or 'N/A'}")
    print(f"  Quality gap:          {stats['quality_gap'] or 'N/A'}")
    
    print("\n✅ SQLite operation tracking tests passed")


def test_track_operation_helper():
    """Test convenience helper function."""
    print("\n🧪 Test 3: track_operation() helper...")
    
    metadata = track_operation(
        model_used="llama3.1:8b",
        operation_type="response",
        offline_mode=True
    )
    
    assert metadata.model_used == "llama3.1:8b"
    assert metadata.operation_type == "response"
    assert metadata.offline_mode == True
    
    # Simulate operation
    try:
        # ... perform operation ...
        metadata.mark_success(prompt_tokens=100, completion_tokens=50)
    except Exception as e:
        metadata.mark_failure(str(e))
    
    assert metadata.success == True
    
    print("✅ track_operation() helper tests passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Phase 1: Operation Tracking Foundation Tests")
    print("=" * 60)
    
    try:
        test_operation_metadata()
        test_sqlite_operation_tracking()
        test_track_operation_helper()
        
        print("\n" + "=" * 60)
        print("✨ All Phase 1 tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
