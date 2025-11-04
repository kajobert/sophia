#!/usr/bin/env python3
"""
Quick Sophia + Jules Collaboration Demo

Shows the full workflow without waiting for Jules to complete:
1. Sophia identifies missing capability
2. Sophia creates detailed specification
3. Sophia delegates to Jules
4. Demo how Sophia would use the plugin (simulated)

For full test with Jules completion, see test_sophia_jules_collaboration.py

Author: GitHub Copilot  
Date: 2025-11-04
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import SharedContext
from plugins.tool_jules import JulesAPITool
from plugins.cognitive_jules_monitor import CognitiveJulesMonitor


def analyze_task_needs(task: str, available_plugins: list) -> Dict[str, str]:
    """
    Simple heuristic to determine what plugin is needed.
    In production, Sophia would use LLM reasoning.
    """
    
    task_lower = task.lower()
    
    # Check what's missing
    if "weather" in task_lower and not any("weather" in p for p in available_plugins):
        return {
            "plugin_name": "tool_weather",
            "plugin_type": "tool",
            "description": "OpenWeatherMap API integration for weather data",
            "reason": "User asked about weather but no weather plugin exists",
            "api_needed": "OpenWeatherMap API",
            "key_methods": ["get_current_weather", "get_forecast"],
        }
    
    if ("data" in task_lower or "csv" in task_lower or "analyze" in task_lower) and not any("analytics" in p or "data" in p for p in available_plugins):
        return {
            "plugin_name": "tool_data_analytics", 
            "plugin_type": "tool",
            "description": "Data analysis plugin using pandas and numpy",
            "reason": "User needs data analysis but no analytics plugin exists",
            "api_needed": "pandas, numpy, matplotlib",
            "key_methods": ["analyze_csv", "generate_statistics", "create_visualization"],
        }
    
    if "image" in task_lower and not any("image" in p for p in available_plugins):
        return {
            "plugin_name": "tool_image_processor",
            "plugin_type": "tool", 
            "description": "Image processing using PIL/Pillow",
            "reason": "User needs image processing but no image plugin exists",
            "api_needed": "Pillow (PIL)",
            "key_methods": ["resize_image", "convert_format", "apply_filter"],
        }
    
    return None


def create_plugin_specification(plugin_info: Dict[str, str]) -> str:
    """Create detailed specification for Jules"""
    
    spec = f"""# Sophia AGI Plugin Specification

## Plugin Information
- **Name**: {plugin_info['plugin_name']}
- **Type**: {plugin_info['plugin_type']} 
- **Purpose**: {plugin_info['description']}

## Requirements

### 1. Base Architecture
```python
from plugins.base_plugin import BasePlugin, PluginType
from typing import Dict, Any, List
import logging

class {plugin_info['plugin_name'].title().replace('_', '')}(BasePlugin):
    '''\''{plugin_info['description']}'''\'\'
    
    @property
    def name(self) -> str:
        return "{plugin_info['plugin_name']}"
    
    @property  
    def plugin_type(self) -> PluginType:
        return PluginType.TOOL
    
    @property
    def version(self) -> str:
        return "1.0.0"
```

### 2. Dependency Injection Setup
```python
def setup(self, config: dict) -> None:
    '''\'\'Setup with dependency injection pattern'''\'\'
    self.logger = config.get("logger", logging.getLogger(self.name))
    self.all_plugins = config.get("all_plugins", {{}})
    
    # Get API key from config
    self.api_key = config.get("api_key", "")
    
    if not self.api_key:
        self.logger.warning(f"{{self.name}} API key not configured")
```

### 3. Required Methods
Implement these key methods:
{chr(10).join(f"- `{method}(context: SharedContext, ...)`" for method in plugin_info['key_methods'])}

### 4. Tool Definitions
```python
def get_tool_definitions(self) -> List[dict]:
    return [
        {{
            "name": "{plugin_info['plugin_name']}_action",
            "description": "{plugin_info['description']}",
            "parameters": {{
                "type": "object",
                "properties": {{
                    # Define parameters here
                }},
                "required": []
            }}
        }}
    ]
```

### 5. Integration Requirements
- ✅ Use `SharedContext` for all operations
- ✅ Proper error handling with try/except
- ✅ Logging for all important events  
- ✅ Type hints on all methods
- ✅ Comprehensive docstrings
- ✅ Black formatting (line length 100)
- ✅ Unit tests in `tests/plugins/test_{plugin_info['plugin_name']}.py`

### 6. File Location
- Plugin code: `plugins/{plugin_info['plugin_name']}.py`
- Tests: `tests/plugins/test_{plugin_info['plugin_name']}.py`

### 7. External Dependencies
{plugin_info['api_needed']}

Add to requirements.txt if needed.

## Example Usage
```python
context = SharedContext(session_id="test", current_state="TESTING", logger=logger)

# Setup
plugin = {plugin_info['plugin_name'].title().replace('_', '')}()
plugin.setup({{
    "logger": logger,
    "all_plugins": all_plugins,
    "api_key": os.getenv("API_KEY")
}})

# Use
result = plugin.{plugin_info['key_methods'][0]}(context, ...)
```

## Success Criteria
- [ ] All tests pass
- [ ] Black formatting compliant
- [ ] Proper dependency injection
- [ ] Error handling for API failures
- [ ] Comprehensive logging
- [ ] Works with Sophia's architecture
"""
    
    return spec


async def main():
    print("\n" + "=" * 70)
    print("  🤝 SOPHIA + JULES QUICK COLLABORATION DEMO")
    print("=" * 70)
    
    # Setup
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("demo")
    
    # Initialize Jules
    jules_api = JulesAPITool()
    jules_monitor = CognitiveJulesMonitor()
    
    all_plugins = {
        "tool_jules": jules_api,
        "cognitive_jules_monitor": jules_monitor,
    }
    
    for plugin_name, plugin in all_plugins.items():
        config = {
            "logger": logging.getLogger(f"plugin.{plugin_name}"),
            "all_plugins": all_plugins,
        }
        
        if plugin_name == "tool_jules":
            import os
            from dotenv import load_dotenv
            load_dotenv()
            config["jules_api_key"] = os.getenv("JULES_API_KEY")
        
        plugin.setup(config)
    
    context = SharedContext(
        session_id="quick-demo",
        current_state="DEMO",
        logger=logger,
    )
    
    # === PHASE 1: SOPHIA ANALYZES ===
    print("\n" + "=" * 70)
    print("🧠 PHASE 1: SOPHIA ANALYZES TASK")
    print("=" * 70)
    
    user_request = "What's the weather in Prague?"
    print(f"\n👤 User: {user_request}")
    
    available = list(all_plugins.keys())
    print(f"\n📊 Sophia's current tools: {available}")
    
    plugin_needed = analyze_task_needs(user_request, available)
    
    if plugin_needed:
        print(f"\n💡 Sophia's analysis:")
        print(f"   ❌ Missing: {plugin_needed['reason']}")
        print(f"   ✅ Solution: Create {plugin_needed['plugin_name']}")
        print(f"   📦 Type: {plugin_needed['plugin_type']}")
        print(f"   🔧 Key methods: {', '.join(plugin_needed['key_methods'])}")
    else:
        print(f"\n✅ All required capabilities available!")
        return
    
    # === PHASE 2: SOPHIA CREATES SPECIFICATION ===
    print("\n" + "=" * 70)
    print("📝 PHASE 2: SOPHIA CREATES SPECIFICATION")
    print("=" * 70)
    
    spec = create_plugin_specification(plugin_needed)
    
    print(f"\n📄 Generated specification preview:")
    lines = spec.split('\n')[:30]
    for line in lines:
        print(f"   {line}")
    print(f"   ... ({len(spec.split(chr(10)))} lines total)")
    
    # === PHASE 3: SOPHIA DELEGATES TO JULES ===
    print("\n" + "=" * 70)
    print("🤖 PHASE 3: SOPHIA DELEGATES TO JULES")
    print("=" * 70)
    
    prompt = f"""Create Sophia AGI plugin: {plugin_needed['plugin_name']}

{spec}

Make it production-ready and fully integrated with Sophia's architecture.
File: plugins/{plugin_needed['plugin_name']}.py
Tests: tests/plugins/test_{plugin_needed['plugin_name']}.py
"""
    
    print(f"\n📤 Sending to Jules API...")
    print(f"   Plugin: {plugin_needed['plugin_name']}")
    print(f"   Specification: {len(prompt)} characters")
    
    try:
        session = jules_api.create_session(
            context,
            prompt=prompt,
            source="sources/github/ShotyCZ/sophia",
            branch="feature/year-2030-ami-complete", 
            title=f"Create {plugin_needed['plugin_name']}",
            auto_pr=False
        )
        
        print(f"\n✅ Jules session created!")
        print(f"   Session ID: {session.name}")
        print(f"   State: {session.state or 'PLANNING'}")
        print(f"   Title: {session.title or 'Creating plugin...'}")
        
        print(f"\n⏳ Jules is now working on creating the plugin...")
        print(f"   This typically takes 2-5 minutes")
        
        # Check initial status
        await asyncio.sleep(5)
        status = jules_monitor.check_session_status(context, session.name)
        print(f"\n📊 Current status: {status.state}")
        
        # === PHASE 4: DEMO FUTURE USE ===
        print("\n" + "=" * 70)
        print("🎯 PHASE 4: HOW SOPHIA WILL USE THE PLUGIN")
        print("=" * 70)
        
        print(f"\n📚 Once Jules completes, Sophia will:")
        print(f"   1. Pull changes: `jules pull {session.name}`")
        print(f"   2. Discover new plugin in plugins/ directory")
        print(f"   3. Load plugin dynamically")
        print(f"   4. Call plugin.setup(config) with dependency injection")
        print(f"   5. Use plugin to answer: '{user_request}'")
        
        print(f"\n💻 Example code Sophia will execute:")
        print(f"""
   # Load plugin
   from plugins.{plugin_needed['plugin_name']} import {plugin_needed['plugin_name'].title().replace('_', '')}
   
   # Initialize
   weather_plugin = {plugin_needed['plugin_name'].title().replace('_', '')}()
   weather_plugin.setup({{
       "logger": logger,
       "all_plugins": all_plugins,
       "api_key": os.getenv("OPENWEATHER_API_KEY")
   }})
   
   # Use it
   result = weather_plugin.{plugin_needed['key_methods'][0]}(context, city="Prague")
   print(f"Weather in Prague: {{result['temperature']}}°C")
""")
        
        # === SUCCESS ===
        print("\n" + "=" * 70)
        print("🎉 COLLABORATION WORKFLOW DEMONSTRATED!")
        print("=" * 70)
        
        print(f"\n✅ Sophia analyzed task and identified gap")
        print(f"✅ Sophia created detailed specification")
        print(f"✅ Sophia delegated to Jules (session {session.name})")
        print(f"⏳ Jules is creating the plugin now...")
        
        print(f"\n📋 Next steps:")
        print(f"   1. Wait for Jules to complete (~3-5 min)")
        print(f"   2. Check status: jules status {session.name}")
        print(f"   3. Pull results: jules pull {session.name}")
        print(f"   4. Test plugin: pytest tests/plugins/test_{plugin_needed['plugin_name']}.py")
        print(f"   5. Sophia will auto-discover and use it!")
        
        return session.name
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        session_id = asyncio.run(main())
        print(f"\n✨ Demo complete! Jules session: {session_id}")
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
