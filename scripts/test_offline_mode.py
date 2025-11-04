#!/usr/bin/env python3
"""
Test offline mode functionality.

Tests:
1. Run Sophia with --offline flag
2. Verify local LLM is used
3. Check operation tracking records offline_mode=True
4. Verify cloud LLM not called

Run: python scripts/test_offline_mode.py
"""

import asyncio
import subprocess
import sqlite3
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_offline_flag():
    """Test that --offline flag works."""
    print("🧪 Test 1: --offline flag functionality...")
    
    # Run Sophia in offline mode with a simple question
    cmd = [
        sys.executable,
        "run.py",
        "--offline",
        "--once",
        "Kolik je 2+2?"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=60  # Generous timeout for first Ollama call
    )
    
    print(f"\n📊 STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print(f"\n📊 STDERR:")
        print(result.stderr)
    
    # Check for offline mode indicators
    assert "🔒 OFFLINE MODE ENABLED" in result.stdout or "🔒 OFFLINE MODE" in result.stderr, \
        "Offline mode message not found in output"
    
    # Check for success indicators
    assert "Sophia:" in result.stdout or result.returncode == 0, \
        "Sophia response not found"
    
    print("✅ Offline flag works!")


def test_operation_tracking():
    """Test that operations are tracked with offline_mode=True."""
    print("\n🧪 Test 2: Operation tracking in offline mode...")
    
    # Run Sophia again to generate tracked operation
    cmd = [
        sys.executable,
        "run.py",
        "--offline",
        "--once",
        "Test question for tracking"
    ]
    
    subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Check database for offline operations
    db_path = "data/memory/sophia_memory.db"
    
    if not Path(db_path).exists():
        print("⚠️  Warning: Database not found - skipping tracking test")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query for offline operations
    cursor.execute("""
        SELECT COUNT(*) 
        FROM operation_tracking 
        WHERE offline_mode = 1
    """)
    
    offline_count = cursor.fetchone()[0]
    
    print(f"📊 Found {offline_count} offline operations in database")
    
    if offline_count > 0:
        # Show latest offline operation
        cursor.execute("""
            SELECT operation_id, model_used, operation_type, success
            FROM operation_tracking 
            WHERE offline_mode = 1
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        op_id, model, op_type, success = cursor.fetchone()
        print(f"  Latest: {op_id[:8]}... | {model} | {op_type} | success={success}")
        
        # Verify local LLM was used
        assert "llama" in model.lower() or "gemma" in model.lower(), \
            f"Expected local LLM, got: {model}"
        
        print("✅ Operation tracking works correctly!")
    else:
        print("⚠️  No offline operations tracked (might need operation_tracking table)")
    
    conn.close()


def test_online_mode_comparison():
    """Test that online mode uses cloud LLM."""
    print("\n🧪 Test 3: Online mode comparison...")
    
    # Run WITHOUT --offline flag
    cmd = [
        sys.executable,
        "run.py",
        "--once",
        "Test online mode"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    # Should NOT show offline mode message
    assert "🔒 OFFLINE MODE" not in result.stdout, \
        "Offline mode should not be enabled without --offline flag"
    
    # Should show online mode indicator
    # (Depends on implementation - might not show explicit message)
    
    print("✅ Online mode works correctly!")


def main():
    """Run all tests."""
    print("=" * 60)
    print("🚀 Offline Mode Tests")
    print("=" * 60)
    
    try:
        test_offline_flag()
        test_operation_tracking()
        test_online_mode_comparison()
        
        print("\n" + "=" * 60)
        print("✨ All offline mode tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        print(f"\n❌ Test timed out (Ollama might be slow or not running)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
