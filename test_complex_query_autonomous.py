#!/usr/bin/env python3
"""
Autonomous Complex Query Test
Tests SOPHIA's ability to handle multi-step web research queries
"""

import asyncio
import json
import time
import websockets
from datetime import datetime

# Complex query that requires multiple tools and web interaction
COMPLEX_QUERY = """Vyhledej aktuální informace o vývoji umělé inteligence v roce 2025 
a vytvoř mi stručný report se 3 hlavními trendy. Použij webové vyhledávání."""

async def test_complex_query():
    """Send complex query via WebSocket and monitor response"""
    
    uri = "ws://127.0.0.1:8000/ws"
    
    print("=" * 80)
    print("🧪 AUTONOMOUS COMPLEX QUERY TEST")
    print("=" * 80)
    print(f"⏰ Start time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"📝 Query: {COMPLEX_QUERY[:80]}...")
    print("=" * 80)
    
    try:
        async with websockets.connect(uri) as websocket:
            print("\n✅ WebSocket connected")
            
            # Send query
            message = json.dumps({"message": COMPLEX_QUERY})
            await websocket.send(message)
            print(f"📤 Query sent at {datetime.now().strftime('%H:%M:%S')}")
            
            # Wait for response (max 120 seconds for complex query)
            print("\n⏳ Waiting for SOPHIA's response...")
            print("   (Complex web queries may take 30-90 seconds)\n")
            
            start_time = time.time()
            response_received = False
            
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=120)
                elapsed = time.time() - start_time
                
                print("=" * 80)
                print(f"✅ Response received in {elapsed:.1f}s")
                print("=" * 80)
                
                # Parse response
                try:
                    data = json.loads(response)
                    if data.get("type") == "response":
                        response_text = data.get("message", "")
                        print("\n📊 SOPHIA's Response:")
                        print("-" * 80)
                        print(response_text)
                        print("-" * 80)
                        
                        # Analyze response quality
                        print("\n📈 Response Analysis:")
                        word_count = len(response_text.split())
                        has_trends = any(keyword in response_text.lower() for keyword in 
                                       ['trend', 'vývoj', 'oblast', '1.', '2.', '3.'])
                        has_web_data = any(keyword in response_text.lower() for keyword in 
                                         ['podle', 'zdroj', 'aktuální', '2025'])
                        
                        print(f"  • Word count: {word_count}")
                        print(f"  • Contains trends/structure: {'✅' if has_trends else '❌'}")
                        print(f"  • Contains web data: {'✅' if has_web_data else '❌'}")
                        print(f"  • Response time: {elapsed:.1f}s")
                        
                        # Overall assessment
                        print("\n🎯 Assessment:")
                        if word_count > 100 and has_trends and has_web_data:
                            print("  ✅ EXCELLENT - Comprehensive web-researched response")
                        elif word_count > 50 and (has_trends or has_web_data):
                            print("  ⚠️  GOOD - Partial success, could be more detailed")
                        else:
                            print("  ❌ BASIC - Generic response, web tools may not have been used")
                        
                        response_received = True
                    else:
                        print(f"⚠️  Unexpected response type: {data.get('type')}")
                        print(f"Raw: {response[:200]}")
                        
                except json.JSONDecodeError:
                    print("⚠️  Response is not JSON:")
                    print(response[:500])
                    response_received = True
                    
            except asyncio.TimeoutError:
                print("\n❌ TIMEOUT - No response after 120 seconds")
                print("   This may indicate:")
                print("   - Web search tools are slow or failing")
                print("   - Complex query requires more processing time")
                print("   - Check logs/sophia.log for errors")
            
            print("\n" + "=" * 80)
            print(f"⏰ End time: {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 80)
            
            return response_received
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("   Make sure SOPHIA is running: sophia-status")
        return False

if __name__ == "__main__":
    print("\n🚀 Starting autonomous complex query test...")
    print("📋 This test will:")
    print("   1. Connect to SOPHIA via WebSocket")
    print("   2. Send a complex web research query")
    print("   3. Monitor response quality and tools used")
    print("   4. Provide assessment\n")
    
    success = asyncio.run(test_complex_query())
    
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST COMPLETED SUCCESSFULLY")
        print("💡 Check response quality above for tool usage assessment")
    else:
        print("❌ TEST FAILED")
        print("💡 Check logs: tail -100 logs/sophia.log")
    print("=" * 80 + "\n")
