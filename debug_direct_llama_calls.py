#!/usr/bin/env python3
"""
Debug script: Call Llama directly multiple times to test reliability
Tests both simple queries and function calling
"""
import asyncio
import httpx
import time
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.1:8b"

async def call_ollama(test_name: str, messages: list, tools: list = None):
    """Single Ollama API call with timing"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
    
    request = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 512}
    }
    
    if tools:
        request["tools"] = tools
        print(f"Tools: {[t['function']['name'] for t in tools]}")
    
    start = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(OLLAMA_URL, json=request)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                content = message.get("content", "")
                tool_calls = message.get("tool_calls", [])
                
                print(f"✅ SUCCESS ({elapsed:.2f}s)")
                if tool_calls:
                    print(f"📞 Tool calls: {len(tool_calls)}")
                    for tc in tool_calls:
                        print(f"   - {tc['function']['name']}")
                if content:
                    print(f"💬 Content: {content[:100]}")
                
                return True, elapsed
            else:
                print(f"❌ HTTP {response.status_code}")
                return False, elapsed
                
    except asyncio.TimeoutError:
        elapsed = time.time() - start
        print(f"⏱️ TIMEOUT after {elapsed:.2f}s")
        return False, elapsed
    except Exception as e:
        elapsed = time.time() - start
        print(f"💥 ERROR ({elapsed:.2f}s): {e}")
        return False, elapsed

async def main():
    print("🧪 LLAMA 3.1 8B RELIABILITY TEST")
    print("="*60)
    
    tests = [
        {
            "name": "Simple greeting",
            "messages": [
                {"role": "system", "content": "You are Sophia"},
                {"role": "user", "content": "Ahoj"}
            ],
            "tools": None
        },
        {
            "name": "Function calling: get_time",
            "messages": [
                {"role": "system", "content": "You are Sophia"},
                {"role": "user", "content": "Jaký je čas?"}
            ],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get current time",
                    "parameters": {"type": "object", "properties": {}}
                }
            }]
        },
        {
            "name": "Function calling: create_plan",
            "messages": [
                {"role": "system", "content": "You are a planner"},
                {"role": "user", "content": "Respond to: Hi"}
            ],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "create_plan",
                    "description": "Create execution plan",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "plan": {
                                "type": "string",
                                "description": "JSON array of steps"
                            }
                        }
                    }
                }
            }]
        },
        {
            "name": "Repeat: Simple greeting #2",
            "messages": [
                {"role": "system", "content": "You are Sophia"},
                {"role": "user", "content": "Hello"}
            ],
            "tools": None
        },
        {
            "name": "Repeat: Function calling #2",
            "messages": [
                {"role": "system", "content": "You are Sophia"},
                {"role": "user", "content": "What time is it?"}
            ],
            "tools": [{
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get current time",
                    "parameters": {"type": "object", "properties": {}}
                }
            }]
        }
    ]
    
    results = []
    for test in tests:
        success, elapsed = await call_ollama(
            test["name"],
            test["messages"],
            test.get("tools")
        )
        results.append((test["name"], success, elapsed))
        
        # Small delay between tests
        await asyncio.sleep(0.5)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    avg_time = sum(elapsed for _, _, elapsed in results) / total
    
    print(f"Tests passed: {passed}/{total}")
    print(f"Average time: {avg_time:.2f}s")
    print()
    
    for name, success, elapsed in results:
        status = "✅" if success else "❌"
        print(f"{status} {name:.<40} {elapsed:.2f}s")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED!")
        print("Ollama is stable and reliable for function calling")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed")
        print("Check Ollama service or model loading")

if __name__ == "__main__":
    asyncio.run(main())
