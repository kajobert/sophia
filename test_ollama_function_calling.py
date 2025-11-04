#!/usr/bin/env python3
"""
Quick test for Ollama function calling with tool_local_llm
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from plugins.tool_local_llm import LocalLLMTool
from core.context import SharedContext

# Create simple logger
logger = logging.getLogger("test")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
logger.addHandler(handler)

async def test_simple_query():
    """Test simple query without tools"""
    print("\n=== TEST 1: Simple Query (No Tools) ===")
    
    tool = LocalLLMTool()
    tool.setup({"local_llm": {
        "runtime": "ollama",
        "base_url": "http://localhost:11434",
        "model": "llama3.1:8b",
        "timeout": 30,
        "max_tokens": 512,
        "temperature": 0.7
    }})
    
    context = SharedContext(
        session_id="test-session-1",
        current_state="idle",
        user_input="Ahoj, jak se jmenuješ?",
        payload={"prompt": "Ahoj, jak se jmenuješ?"},
        history=[],
        logger=logger
    )
    
    print(f"Input: {context.user_input}")
    result = await tool.execute(context)
    response = result.payload.get("llm_response")
    print(f"Response: {response}")
    print(f"Type: {type(response)}")
    
    return "✅ PASS" if response else "❌ FAIL"

async def test_function_calling():
    """Test query that should trigger function calling"""
    print("\n=== TEST 2: Function Calling (With Tools) ===")
    
    tool = LocalLLMTool()
    tool.setup({"local_llm": {
        "runtime": "ollama",
        "base_url": "http://localhost:11434",
        "model": "llama3.1:8b",
        "timeout": 30,
        "max_tokens": 512,
        "temperature": 0.7
    }})
    
    # Define a simple tool
    tools = [{
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Zjistí aktuální čas",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }]
    
    context = SharedContext(
        session_id="test-session-2",
        current_state="idle",
        user_input="Jaký je čas?",
        payload={
            "prompt": "Jaký je čas?",
            "tools": tools,
            "tool_choice": "auto"
        },
        history=[],
        logger=logger
    )
    
    print(f"Input: {context.user_input}")
    print(f"Tools: {[t['function']['name'] for t in tools]}")
    result = await tool.execute(context)
    response = result.payload.get("llm_response")
    print(f"Response: {response}")
    print(f"Type: {type(response)}")
    
    if isinstance(response, list):
        print(f"Tool calls detected: {len(response)}")
        for i, tc in enumerate(response):
            print(f"  Tool call {i+1}: {tc.function.name}")
        return "✅ PASS - Function calling works!"
    elif isinstance(response, str):
        return "⚠️ WARNING - Got text response instead of tool call"
    else:
        return "❌ FAIL - Unexpected response type"

async def main():
    print("🧪 Testing Ollama Function Calling")
    print("=" * 50)
    
    # Test 1: Simple query
    try:
        result1 = await test_simple_query()
        print(f"\nTest 1 Result: {result1}")
    except Exception as e:
        print(f"\nTest 1 Result: ❌ FAIL - {e}")
    
    # Test 2: Function calling
    try:
        result2 = await test_function_calling()
        print(f"\nTest 2 Result: {result2}")
    except Exception as e:
        print(f"\nTest 2 Result: ❌ FAIL - {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Tests Complete!")

if __name__ == "__main__":
    asyncio.run(main())
