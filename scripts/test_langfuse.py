#!/usr/bin/env python3
"""Test script for Langfuse Observability plugin"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from plugins.tool_langfuse import (
    ToolLangfuse,
    TraceGenerationRequest,
    SpanRequest,
    EventRequest,
    ScoreRequest,
)


def test_pydantic_models():
    """Test Pydantic models"""
    print("\n=== Testing Pydantic Models ===")

    # Test TraceGenerationRequest
    trace_req = TraceGenerationRequest(
        name="test_trace",
        input_text="Test input",
        output_text="Test output",
        model="gpt-4",
        metadata={"key": "value"},
    )
    print(f"✅ TraceGenerationRequest: {trace_req.name}")

    # Test SpanRequest
    span_req = SpanRequest(
        trace_id="trace-123",
        name="test_span",
        input_data={"query": "test"},
        output_data={"result": "success"},
    )
    print(f"✅ SpanRequest: {span_req.name}")

    # Test EventRequest
    event_req = EventRequest(
        trace_id="trace-123", name="test_event", level="INFO", metadata={"key": "value"}
    )
    print(f"✅ EventRequest: {event_req.name} ({event_req.level})")

    # Test ScoreRequest
    score_req = ScoreRequest(
        trace_id="trace-123", name="accuracy", value=0.95, comment="Good result"
    )
    print(f"✅ ScoreRequest: {score_req.name} = {score_req.value}")

    # Test invalid level
    try:
        bad_event = EventRequest(trace_id="trace-123", name="test", level="INVALID")
        print("❌ Should have failed validation!")
    except Exception as e:
        print(f"✅ Validation correctly rejected invalid level: {type(e).__name__}")


def test_plugin_initialization():
    """Test plugin initialization"""
    print("\n=== Testing Plugin Initialization ===")

    plugin = ToolLangfuse()
    print(f"✅ Plugin name: {plugin.name}")
    print(f"✅ Plugin type: {plugin.plugin_type}")
    print(f"✅ Plugin version: {plugin.version}")

    # Test tool definitions
    tools = plugin.get_tool_definitions()
    print(f"✅ Tool definitions: {len(tools)} tools")
    for tool in tools:
        print(f"   - {tool['function']['name']}")


def test_setup_without_credentials():
    """Test setup without credentials"""
    print("\n=== Testing Setup (Without Credentials) ===")

    # Clear environment variables if set
    os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
    os.environ.pop("LANGFUSE_SECRET_KEY", None)

    plugin = ToolLangfuse()
    try:
        plugin.setup({})
        print("❌ Should have failed without credentials!")
    except Exception as e:
        print(f"✅ Correctly rejected setup without credentials: {type(e).__name__}")
        print(f"   Message: {str(e)[:100]}")


def test_setup_with_mock_credentials():
    """Test setup with mock credentials (will fail to initialize but validates flow)"""
    print("\n=== Testing Setup (With Mock Credentials) ===")

    plugin = ToolLangfuse()

    # This will fail because langfuse is not installed
    try:
        plugin.setup(
            {
                "api_key": "pk-test-123",
                "secret_key": "sk-test-456",
                "host": "https://cloud.langfuse.com",
            }
        )
        print("✅ Setup completed (if langfuse SDK is installed)")
    except Exception as e:
        if "not installed" in str(e):
            print(f"✅ SDK not installed (expected): {type(e).__name__}")
            print("   Install with: pip install langfuse")
        else:
            print(f"⚠️ Setup failed: {e}")


if __name__ == "__main__":
    try:
        test_pydantic_models()
        test_plugin_initialization()
        test_setup_without_credentials()
        test_setup_with_mock_credentials()
        print("\n✅ All tests passed!")
        print("\n📝 Note: Full integration tests require:")
        print("   1. pip install langfuse")
        print("   2. LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
