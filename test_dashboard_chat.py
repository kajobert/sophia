#!/usr/bin/env python3
"""
Interactive Dashboard Chat Tester

Tests the Dashboard Chat functionality with model escalation.
Verifies that SOPHIA can respond via WebSocket and escalate from llama3.1 to qwen2.5.
"""

import asyncio
import websockets
import json
import sys
from datetime import datetime

DASHBOARD_URL = "ws://127.0.0.1:8000/ws/test_session"
TEST_MESSAGE = "Jaké jsou tvé aktuální schopnosti?"


async def test_chat():
    """Test Dashboard Chat with model escalation."""
    print("🧪 Dashboard Chat Test")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 Connecting to: {DASHBOARD_URL}")
    print(f"💬 Test message: {TEST_MESSAGE}")
    print("=" * 60)
    print()
    
    try:
        async with websockets.connect(DASHBOARD_URL) as websocket:
            print("✅ WebSocket connected")
            print()
            
            # Send test message
            print(f"📤 Sending: {TEST_MESSAGE}")
            await websocket.send(json.dumps({"message": TEST_MESSAGE}))
            print()
            
            # Wait for response(s)
            print("⏳ Waiting for SOPHIA's response...")
            print("   (This may take 30-60s for planning + execution)")
            print()
            
            response_count = 0
            start_time = datetime.now()
            
            try:
                while True:
                    # Timeout after 120 seconds
                    response = await asyncio.wait_for(websocket.recv(), timeout=120.0)
                    response_count += 1
                    
                    data = json.loads(response)
                    elapsed = (datetime.now() - start_time).total_seconds()
                    
                    print(f"📨 Response #{response_count} (after {elapsed:.1f}s):")
                    print(f"   Type: {data.get('type', 'unknown')}")
                    
                    if data.get('type') == 'response':
                        message = data.get('message', '')
                        print(f"   Message: {message[:200]}...")
                        print()
                        
                        # Check for key indicators
                        if 'plugin' in message.lower() or 'schopnost' in message.lower():
                            print("✅ Response mentions capabilities")
                        
                        # Look for model escalation in logs
                        print("💡 Check logs for model escalation:")
                        print("   grep -i 'escalat\\|tier\\|qwen\\|llama' logs/sophia.log | tail -10")
                        break
                    
            except asyncio.TimeoutError:
                print("⏱️  Timeout waiting for response (120s)")
                print("⚠️  SOPHIA may still be processing, check logs")
            
            print()
            print(f"📊 Total responses received: {response_count}")
            print(f"⏱️  Total time: {(datetime.now() - start_time).total_seconds():.1f}s")
            
    except ConnectionRefusedError:
        print("❌ Connection refused")
        print("   Make sure SOPHIA is running: sophia-start")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("🎯 Test completed!")
    print()
    print("📝 Expected behavior:")
    print("   1. llama3.1:8b attempts to plan")
    print("   2. Plan quality check detects poor plan")
    print("   3. Escalation to qwen2.5:14b")
    print("   4. Better plan generated")
    print("   5. Tools executed")
    print("   6. Quality response returned")
    print()


if __name__ == "__main__":
    asyncio.run(test_chat())
