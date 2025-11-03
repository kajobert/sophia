#!/usr/bin/env python3
"""
Quick single model test to diagnose benchmark issues.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import SharedContext
from plugins.tool_llm import LLMTool
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_model():
    """Test a single model with a simple prompt."""
    
    # Test model - using paid version for reliability
    model_id = "openrouter/google/gemma-2-9b-it"
    
    print(f"Testing model: {model_id}\n")
    
    # Initialize LLM tool
    llm_tool = LLMTool()
    llm_tool.setup({})
    
    # Simple test prompt
    prompt = "Calculate: 47 * 23. Show just the answer."
    
    print(f"Prompt: {prompt}")
    print("Sending request...\n")
    
    try:
        context = SharedContext(
            session_id="test_single",
            current_state="EXECUTING",
            logger=logger,
            user_input=prompt,
            history=[]
        )
        
        context.payload = {
            "prompt": prompt,
            "model_config": {
                "model": model_id
            }
        }
        
        result_context = await llm_tool.execute(context=context)
        
        response = result_context.payload.get("llm_response", "")
        
        print(f"✅ SUCCESS!")
        print(f"Response: {response}\n")
        
        # Check if answer is correct
        if "1081" in str(response):
            print("✅ CORRECT ANSWER!")
        else:
            print("⚠️  Answer doesn't contain expected result (1081)")
            
    except Exception as e:
        print(f"❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_model())
