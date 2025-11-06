#!/usr/bin/env python3
"""
Quick test for Model Manager Plugin

Tests:
1. List local Ollama models
2. Check disk usage
3. Parse ollama list output

Run: python test_model_manager.py
"""

import asyncio
import logging
from core.context import SharedContext
from plugins.tool_model_manager import ModelManagerTool
from plugins.tool_bash import BashTool

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_model_manager():
    """Test model manager plugin functionality."""
    
    print("=" * 60)
    print("🧪 MODEL MANAGER PLUGIN TEST")
    print("=" * 60)
    
    # Initialize plugins
    model_manager = ModelManagerTool()
    bash_tool = BashTool()
    
    # Setup bash tool
    bash_tool.setup({"timeout": 30})
    
    # Setup model manager with bash plugin reference
    model_manager.setup({
        "all_plugins": {"tool_bash": bash_tool}
    })
    
    # Create shared context
    context = SharedContext(
        session_id="test-session",
        current_state="testing",
        logger=logger
    )
    
    # Test 1: List local models
    print("\n📋 Test 1: Listing local Ollama models...")
    result = await model_manager.execute_tool(
        "list_local_models",
        {},
        context
    )
    
    if result.get("success"):
        models = result.get("models", [])
        print(f"✅ SUCCESS: Found {len(models)} models")
        for model in models:
            print(f"  📦 {model['name']} ({model['size']}) - modified {model['modified']}")
    else:
        print(f"❌ FAILED: {result.get('error')}")
    
    # Test 2: Get disk usage
    print("\n💾 Test 2: Checking disk usage...")
    result = await model_manager.execute_tool(
        "get_disk_usage",
        {},
        context
    )
    
    if result.get("success"):
        print(f"✅ SUCCESS: Models directory uses {result.get('total_size')}")
        print(f"  📁 Path: {result.get('models_path')}")
    else:
        print(f"❌ FAILED: {result.get('error')}")
    
    # Test 3: Capabilities
    print("\n🔧 Test 3: Plugin capabilities...")
    capabilities = model_manager.get_capabilities()
    print(f"✅ Available tools: {len(capabilities)}")
    for cap in capabilities:
        print(f"  • {cap}")
    
    print("\n" + "=" * 60)
    print("🎉 MODEL MANAGER TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_model_manager())
