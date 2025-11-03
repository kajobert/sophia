#!/usr/bin/env python3
"""Test script for Performance Monitor plugin"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from plugins.tool_performance_monitor import ToolPerformanceMonitor, LLMCall, ToolUsage, Metrics
from core.context import SharedContext
from datetime import datetime
import logging

def test_pydantic_models():
    """Test Pydantic models"""
    print("\n=== Testing Pydantic Models ===")
    
    # Test LLMCall
    call = LLMCall(
        timestamp=datetime.now(),
        model="gpt-4",
        input_tokens=100,
        output_tokens=50,
        cost=0.003
    )
    print(f"✅ LLMCall: {call.model}, {call.input_tokens + call.output_tokens} tokens, ${call.cost}")
    
    # Test ToolUsage
    usage = ToolUsage(
        timestamp=datetime.now(),
        tool_name="tool_tavily",
        method_name="search",
        success=True
    )
    print(f"✅ ToolUsage: {usage.tool_name}.{usage.method_name}, success={usage.success}")
    
    # Test Metrics
    metrics = Metrics(
        total_llm_calls=10,
        total_tokens=1500,
        total_cost=0.05,
        tool_usage_count={"tool_tavily": 5, "tool_jules": 3},
        success_rate=0.9,
        timespan="24h"
    )
    print(f"✅ Metrics: {metrics.total_llm_calls} calls, ${metrics.total_cost}, {metrics.success_rate*100}% success")

def test_plugin_initialization():
    """Test plugin initialization"""
    print("\n=== Testing Plugin Initialization ===")
    
    plugin = ToolPerformanceMonitor()
    print(f"✅ Plugin name: {plugin.name}")
    print(f"✅ Plugin type: {plugin.plugin_type}")
    print(f"✅ Plugin version: {plugin.version}")
    
    # Test tool definitions
    tools = plugin.get_tool_definitions()
    print(f"✅ Tool definitions: {len(tools)} tools")
    for tool in tools:
        print(f"   - {tool['function']['name']}")

def test_logging():
    """Test logging functionality"""
    print("\n=== Testing Logging ===")
    
    # Setup context
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test")
    context = SharedContext(
        session_id="test-session",
        current_state="testing",
        logger=logger
    )
    
    # Create plugin
    plugin = ToolPerformanceMonitor()
    plugin.setup({"db_path": "data/test_metrics.db"})
    
    # Test log_llm_call
    result = plugin.log_llm_call(
        context=context,
        model="claude-3-5-sonnet-20241022",
        input_tokens=1000,
        output_tokens=500,
        cost=0.015
    )
    print(f"✅ {result}")
    
    # Test log_tool_usage
    result = plugin.log_tool_usage(
        context=context,
        tool_name="tool_tavily",
        method_name="search",
        success=True
    )
    print(f"✅ {result}")
    
    result = plugin.log_tool_usage(
        context=context,
        tool_name="tool_jules",
        method_name="create_session",
        success=True
    )
    print(f"✅ {result}")

def test_metrics():
    """Test metrics retrieval"""
    print("\n=== Testing Metrics Retrieval ===")
    
    # Setup context
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("test")
    context = SharedContext(
        session_id="test-session",
        current_state="testing",
        logger=logger
    )
    
    # Create plugin
    plugin = ToolPerformanceMonitor()
    plugin.setup({"db_path": "data/test_metrics.db"})
    
    # Get metrics for different periods
    for period in ["1h", "24h", "7d", "30d"]:
        metrics = plugin.get_metrics(context, period)
        print(f"\n📊 Metrics for {period}:")
        print(f"   LLM Calls: {metrics.total_llm_calls}")
        print(f"   Total Tokens: {metrics.total_tokens}")
        print(f"   Total Cost: ${metrics.total_cost:.4f}")
        print(f"   Tool Usage: {metrics.tool_usage_count}")
        print(f"   Success Rate: {metrics.success_rate*100:.1f}%")

if __name__ == "__main__":
    try:
        test_pydantic_models()
        test_plugin_initialization()
        test_logging()
        test_metrics()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
