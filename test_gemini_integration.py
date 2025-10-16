"""
Quick test script for Gemini integration with LLMManager.
"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from core.llm_manager import LLMManager


@pytest.mark.asyncio
async def test_llm_manager():
    """Test LLMManager with Gemini."""
    with patch.dict('os.environ', {'GEMINI_API_KEY': 'fake_gemini_key'}):
        print("=" * 60)
        print("Testing LLMManager with Gemini 2.5 Flash")
        print("=" * 60)

        # Initialize LLMManager
        manager = LLMManager(project_root=".")

        # Test 1: Get default adapter (should be Gemini)
        print("\n1️⃣ Testing default adapter...")
        llm = manager.get_llm()
        assert llm is not None
        print(f"   Type: {type(llm).__name__}")
        print(f"   Adapter: {llm}")

        # Test 2: Get Gemini explicitly
        print("\n2️⃣ Testing explicit Gemini (powerful)...")
        llm_powerful = manager.get_llm("powerful")
        assert llm_powerful is not None
        print(f"   Type: {type(llm_powerful).__name__}")
        print(f"   Adapter: {llm_powerful}")

        # Mock the actual call to the LLM for the next tests
        with patch.object(llm, 'generate_content_async', new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = ("Gemini 2.5 Flash is working!", {"usage": {"total_tokens": 10}})
            # Test 3: Generate content
            print("\n3️⃣ Testing content generation...")
            response, usage = await llm.generate_content_async("Say exactly: 'Gemini 2.5 Flash is working!'")
            print(f"   Response: {response}")
            print(f"   Tokens used: {usage['usage']['total_tokens']}")
            assert response == "Gemini 2.5 Flash is working!"

            mock_generate.return_value = ('{"status": "success", "model": "gemini-2.5-flash", "message": "Integration test passed!"}', {"usage": {"total_tokens": 20}})
            # Test 4: JSON mode (structured output)
            print("\n4️⃣ Testing JSON output...")
            json_prompt = """Return a valid JSON object..."""
            response_json, usage_json = await llm.generate_content_async(json_prompt)
            print(f"   Response: {response_json}")
            print(f"   Tokens: {usage_json['usage']['total_tokens']}")
            assert '"status": "success"' in response_json

    print("\n" + "=" * 60)
    print("✅ All tests PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    pytest.main([__file__])