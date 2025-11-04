#!/usr/bin/env python3
"""Direct Ollama API test with timing"""
import asyncio
import httpx
import json
import time

async def test_ollama_chat():
    """Test Ollama /api/chat endpoint directly"""
    url = "http://localhost:11434/api/chat"
    
    request = {
        "model": "llama3.1:8b",
        "messages": [
            {"role": "system", "content": "You are Sophia"},
            {"role": "user", "content": "Ahoj"}
        ],
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 512
        }
    }
    
    print("🔄 Sending request to Ollama...")
    print(f"Model: {request['model']}")
    print(f"Messages: {len(request['messages'])}")
    
    start = time.time()
    
    async with httpx.AsyncClient(timeout=120) as client:
        try:
            print(f"\n⏱️ Start time: {time.strftime('%H:%M:%S')}")
            response = await client.post(url, json=request)
            elapsed = time.time() - start
            
            print(f"⏱️ End time: {time.strftime('%H:%M:%S')}")
            print(f"⏱️ Elapsed: {elapsed:.2f}s")
            print(f"\n✅ Status: {response.status_code}")
            
            data = response.json()
            message = data.get("message", {})
            content = message.get("content", "")
            
            print(f"\n📝 Response content ({len(content)} chars):")
            print(content[:200] if len(content) > 200 else content)
            
            if "total_duration" in data:
                total_ms = data["total_duration"] / 1_000_000
                print(f"\n⏱️ Ollama timing:")
                print(f"  Total: {total_ms:.0f}ms")
                if "load_duration" in data:
                    print(f"  Load: {data['load_duration'] / 1_000_000:.0f}ms")
                if "prompt_eval_duration" in data:
                    print(f"  Prompt eval: {data['prompt_eval_duration'] / 1_000_000:.0f}ms")
                if "eval_duration" in data:
                    print(f"  Generation: {data['eval_duration'] / 1_000_000:.0f}ms")
            
        except httpx.TimeoutException as e:
            elapsed = time.time() - start
            print(f"\n❌ TIMEOUT after {elapsed:.2f}s: {e}")
        except Exception as e:
            elapsed = time.time() - start
            print(f"\n❌ ERROR after {elapsed:.2f}s: {e}")

if __name__ == "__main__":
    asyncio.run(test_ollama_chat())
