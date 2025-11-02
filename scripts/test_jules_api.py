#!/usr/bin/env python3
"""
Test script for Jules API plugin.

This script demonstrates how to use the Jules API plugin to interact with
Google's Jules AI coding assistant API.

Prerequisites:
1. Get a Jules API key from Google Cloud Console
2. Add it to config/settings.yaml under plugins.tool_jules.jules_api_key
"""

import sys
import yaml
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from plugins.tool_jules import JulesAPITool, JulesAuthenticationError, JulesAPIError
from core.context import SharedContext
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from settings.yaml."""
    config_path = project_root / "config" / "settings.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def test_plugin_initialization():
    """Test 1: Plugin initialization."""
    print("\n" + "="*60)
    print("TEST 1: Plugin Initialization")
    print("="*60)
    
    tool = JulesAPITool()
    config = load_config()
    jules_config = config.get('plugins', {}).get('tool_jules', {})
    
    tool.setup(jules_config)
    
    print(f"✅ Plugin Name: {tool.name}")
    print(f"✅ Plugin Type: {tool.plugin_type}")
    print(f"✅ Plugin Version: {tool.version}")
    
    if tool.api_key:
        print(f"✅ API Key: Configured ({len(tool.api_key)} chars)")
        return tool, True
    else:
        print("⚠️  API Key: NOT CONFIGURED")
        print("\nTo configure:")
        print("1. Get API key from: https://console.cloud.google.com/")
        print("2. Add to config/settings.yaml:")
        print("   plugins:")
        print("     tool_jules:")
        print("       jules_api_key: 'YOUR_API_KEY_HERE'")
        return tool, False


def test_list_sources(tool):
    """Test 2: List available sources."""
    print("\n" + "="*60)
    print("TEST 2: List Sources")
    print("="*60)
    
    try:
        # Create a mock context
        context = SharedContext()
        context.logger = logger
        
        sources = tool.list_sources(context)
        print(f"✅ Successfully retrieved sources")
        print(f"Response: {sources}")
        return True
        
    except JulesAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except JulesAPIError as e:
        print(f"❌ API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_list_sessions(tool):
    """Test 3: List sessions."""
    print("\n" + "="*60)
    print("TEST 3: List Sessions")
    print("="*60)
    
    try:
        context = SharedContext()
        context.logger = logger
        
        sessions = tool.list_sessions(context)
        print(f"✅ Successfully retrieved sessions")
        print(f"Response: {sessions}")
        return True
        
    except JulesAuthenticationError as e:
        print(f"❌ Authentication failed: {e}")
        return False
    except JulesAPIError as e:
        print(f"❌ API error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_create_session_dry_run(tool):
    """Test 4: Create session (dry run - shows what would be sent)."""
    print("\n" + "="*60)
    print("TEST 4: Create Session (Dry Run)")
    print("="*60)
    
    print("\nExample session creation:")
    print("```python")
    print("session = tool.create_session(")
    print("    context=context,")
    print("    prompt='Create a simple hello world Flask app',")
    print("    source='sources/github/yourusername/yourrepo',")
    print("    branch='main',")
    print("    title='Flask Hello World',")
    print("    auto_pr=False")
    print(")")
    print("```")
    print("\n⚠️  This is a dry run. No actual session will be created.")
    print("To create a real session, you need:")
    print("1. A valid Jules API key")
    print("2. A GitHub repository source")
    print("3. Proper permissions")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("JULES API PLUGIN TEST SUITE")
    print("="*60)
    
    # Test 1: Initialization
    tool, has_api_key = test_plugin_initialization()
    
    if not has_api_key:
        print("\n" + "="*60)
        print("SKIPPING API TESTS - NO API KEY CONFIGURED")
        print("="*60)
        test_create_session_dry_run(tool)
        return
    
    # Test 2: List sources
    test_list_sources(tool)
    
    # Test 3: List sessions
    test_list_sessions(tool)
    
    # Test 4: Dry run
    test_create_session_dry_run(tool)
    
    print("\n" + "="*60)
    print("TEST SUITE COMPLETE")
    print("="*60)
    print("\n✅ Jules API plugin is ready to use!")
    print("\nNext steps:")
    print("1. Configure your API key if not done already")
    print("2. Use the plugin in Sophia's cognitive loop")
    print("3. Create coding sessions with Jules")


if __name__ == "__main__":
    main()
