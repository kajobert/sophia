#!/usr/bin/env python3
"""
Isolated planner test - skip full Sophia kernel
Tests just: planner → tool_local_llm → Ollama
"""
import asyncio
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from plugins.cognitive_planner import CognitivePlanner
from plugins.tool_local_llm import LocalLLMTool
from core.context import SharedContext
from core.plugin_manager import PluginManager
import yaml

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test")

async def test_planner_offline():
    """Test planner with local LLM"""
    print("🧪 Testing Planner + tool_local_llm in isolation")
    print("="*60)
    
    # Load config
    with open("config/settings.yaml") as f:
        config = yaml.safe_load(f)
    
    # Create plugin manager (minimal)
    plugin_manager = PluginManager()
    
    # Setup tool_local_llm
    print("\n1️⃣ Setting up tool_local_llm...")
    tool_llm = LocalLLMTool()
    tool_llm.setup(config.get("plugins", {}))
    plugin_manager.register_plugin(tool_llm)
    print("   ✅ tool_local_llm ready")
    
    # Setup planner
    print("\n2️⃣ Setting up cognitive_planner...")
    planner = CognitivePlanner()
    planner.setup(config.get("plugins", {}))
    planner.set_plugins(plugin_manager.get_all_plugins())
    print("   ✅ cognitive_planner ready")
    
    # Create context
    print("\n3️⃣ Creating test context...")
    context = SharedContext(
        session_id="test-planner",
        current_state="planning",
        user_input="Ahoj, jak se máš?",
        history=[],
        payload={},
        logger=logger,
        offline_mode=True  # CRITICAL: Enable offline mode
    )
    print("   ✅ Context created (offline_mode=True)")
    
    # Execute planner
    print("\n4️⃣ Executing planner...")
    print("   User input: ", context.user_input)
    
    try:
        result = await planner.execute(context)
        
        plan = result.payload.get("plan", [])
        print(f"\n✅ Planner completed!")
        print(f"   Plan steps: {len(plan)}")
        
        if plan:
            print("\n📋 Plan:")
            for i, step in enumerate(plan, 1):
                print(f"   {i}. {step.get('tool_name')}.{step.get('method_name')}")
                if step.get('arguments'):
                    print(f"      Args: {step.get('arguments')}")
        else:
            print("\n⚠️ Empty plan returned")
            
        return True
        
    except asyncio.TimeoutError:
        print("\n❌ TIMEOUT in planner!")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_multiple_runs():
    """Test planner multiple times to check consistency"""
    print("\n\n🔄 Running multiple tests...")
    print("="*60)
    
    test_inputs = [
        "Ahoj",
        "Jaký je čas?",
        "Napiš soubor test.txt",
        "Hello",
        "Co umíš?"
    ]
    
    results = []
    for i, user_input in enumerate(test_inputs, 1):
        print(f"\n--- Test {i}/{len(test_inputs)}: {user_input} ---")
        
        # Quick setup for each test
        with open("config/settings.yaml") as f:
            config = yaml.safe_load(f)
        
        plugin_manager = PluginManager()
        tool_llm = LocalLLMTool()
        tool_llm.setup(config.get("plugins", {}))
        plugin_manager.register_plugin(tool_llm)
        
        planner = CognitivePlanner()
        planner.setup(config.get("plugins", {}))
        planner.set_plugins(plugin_manager.get_all_plugins())
        
        context = SharedContext(
            session_id=f"test-{i}",
            current_state="planning",
            user_input=user_input,
            history=[],
            payload={},
            logger=logger,
            offline_mode=True
        )
        
        try:
            result = await asyncio.wait_for(planner.execute(context), timeout=15)
            plan = result.payload.get("plan", [])
            print(f"   ✅ Plan: {len(plan)} steps")
            results.append((user_input, True, len(plan)))
        except asyncio.TimeoutError:
            print(f"   ⏱️ TIMEOUT")
            results.append((user_input, False, 0))
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results.append((user_input, False, 0))
        
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n\n📊 SUMMARY")
    print("="*60)
    passed = sum(1 for _, success, _ in results if success)
    print(f"Tests passed: {passed}/{len(results)}")
    
    for input_text, success, steps in results:
        status = "✅" if success else "❌"
        print(f"{status} {input_text:.<40} {steps} steps")
    
    return passed == len(results)

async def main():
    print("🎯 ISOLATED PLANNER TEST")
    print("="*60)
    print("Testing planner + tool_local_llm WITHOUT full Sophia kernel")
    print()
    
    # Single test first
    success = await test_planner_offline()
    
    if success:
        # Multiple tests
        all_passed = await test_multiple_runs()
        
        if all_passed:
            print("\n\n🏆 SUCCESS! Planner works perfectly offline!")
            print("Problem must be in full kernel integration")
        else:
            print("\n\n⚠️ Some tests failed - planner has consistency issues")
    else:
        print("\n\n❌ Basic test failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())
