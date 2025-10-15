"""
Quick test script for Gemini integration with LLMManager.
"""

import asyncio
from core.llm_manager import LLMManager


async def test_llm_manager():
    """Test LLMManager with Gemini."""
    print("=" * 60)
    print("Testing LLMManager with Gemini 2.5 Flash")
    print("=" * 60)
    
    # Initialize LLMManager
    manager = LLMManager(project_root="/workspaces/sophia")
    
    # Test 1: Get default adapter (should be Gemini)
    print("\n1️⃣ Testing default adapter...")
    llm = manager.get_llm()
    print(f"   Type: {type(llm).__name__}")
    print(f"   Adapter: {llm}")
    
    # Test 2: Get Gemini explicitly
    print("\n2️⃣ Testing explicit Gemini (powerful)...")
    llm_powerful = manager.get_llm("powerful")
    print(f"   Type: {type(llm_powerful).__name__}")
    print(f"   Adapter: {llm_powerful}")
    
    # Test 3: Generate content
    print("\n3️⃣ Testing content generation...")
    response, usage = await llm.generate_content_async("Say exactly: 'Gemini 2.5 Flash is working!'")
    print(f"   Response: {response}")
    print(f"   Tokens used: {usage['usage']['total_tokens']}")
    
    # Test 4: JSON mode (structured output)
    print("\n4️⃣ Testing JSON output...")
    json_prompt = """Return a valid JSON object with this structure:
{
  "status": "success",
  "model": "gemini-2.5-flash",
  "message": "Integration test passed!"
}"""
    response_json, usage_json = await llm.generate_content_async(json_prompt)
    print(f"   Response: {response_json}")
    print(f"   Tokens: {usage_json['usage']['total_tokens']}")
    
    print("\n" + "=" * 60)
    print("✅ All tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_llm_manager())
