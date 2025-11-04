#!/usr/bin/env python3
"""
Minimal test of httpx → Ollama /api/chat with tools parameter.
Tests if httpx hangs when called from async context similar to Sophia.
"""
import asyncio
import httpx
import json

async def test_ollama_simple():
    """Test simple chat without tools"""
    url = "http://localhost:11434/api/chat"
    request = {
        "model": "llama3.1:8b",
        "messages": [{"role": "user", "content": "Hello!"}],
        "stream": False
    }
    
    print("Test 1: Simple chat (no tools)")
    print(f"Request: {json.dumps(request, indent=2)}")
    
    limits = httpx.Limits(max_connections=1, max_keepalive_connections=0)
    async with httpx.AsyncClient(timeout=30.0, limits=limits) as client:
        response = await client.post(url, json=request)
        result = response.json()
        message = result.get("message", {})
        print(f"✅ Response: {message.get('content', '')[:100]}")
        return message

async def test_ollama_with_tools():
    """Test chat with tools parameter"""
    url = "http://localhost:11434/api/chat"
    
    # Minimal tool definition
    tools = [{
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get current time",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }]
    
    request = {
        "model": "llama3.1:8b",
        "messages": [{"role": "user", "content": "What time is it?"}],
        "tools": tools,
        "stream": False
    }
    
    print("\nTest 2: Chat with tools")
    print(f"Request size: {len(json.dumps(request))} bytes")
    print(f"Tools: {len(tools)}")
    
    limits = httpx.Limits(max_connections=1, max_keepalive_connections=0)
    async with httpx.AsyncClient(timeout=30.0, limits=limits) as client:
        print("Sending request...")
        response = await client.post(url, json=request)
        result = response.json()
        message = result.get("message", {})
        
        if message.get("tool_calls"):
            print(f"✅ Tool calls: {message.get('tool_calls')}")
        else:
            print(f"✅ Content: {message.get('content', '')[:100]}")
        
        return message

async def test_ollama_large_prompt():
    """Test with larger prompt similar to planner"""
    url = "http://localhost:11434/api/chat"
    
    # Simulate large system prompt
    system_prompt = "You are a planning assistant. " * 100  # ~3KB
    
    tools = [{
        "type": "function",
        "function": {
            "name": "create_plan",
            "description": "Create execution plan",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["plan"]
            }
        }
    }]
    
    request = {
        "model": "llama3.1:8b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Create a plan to say hello"}
        ],
        "tools": tools,
        "stream": False
    }
    
    print("\nTest 3: Large prompt with tools")
    print(f"Request size: {len(json.dumps(request))} bytes")
    print(f"System prompt: {len(system_prompt)} chars")
    
    limits = httpx.Limits(max_connections=1, max_keepalive_connections=0)
    async with httpx.AsyncClient(timeout=60.0, limits=limits) as client:
        print("Sending large request...")
        response = await client.post(url, json=request)
        result = response.json()
        message = result.get("message", {})
        
        if message.get("tool_calls"):
            print(f"✅ Tool calls returned")
        else:
            print(f"✅ Content: {len(message.get('content', ''))} chars")
        
        return message

async def main():
    try:
        await test_ollama_simple()
        await test_ollama_with_tools()
        await test_ollama_large_prompt()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
