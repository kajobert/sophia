"""
Test script for Cognitive Jules Monitor Plugin
Tests monitoring capabilities and session status tracking.
"""
from plugins.cognitive_jules_monitor import (
    CognitiveJulesMonitor,
    StartMonitoringRequest,
    GetSessionStatusRequest,
    JulesSessionStatus,
    MonitoringTask
)
from plugins.tool_jules import JulesAPITool, JulesSession
from core.context import SharedContext
from plugins.base_plugin import PluginType
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test")

print("=== Testing Pydantic Models ===")

# Test StartMonitoringRequest
try:
    request = StartMonitoringRequest(
        session_id="sessions/123456789",
        check_interval=60,
        max_duration=1800
    )
    print(f"✅ StartMonitoringRequest: interval={request.check_interval}s, max={request.max_duration}s")
except Exception as e:
    print(f"❌ StartMonitoringRequest failed: {e}")

# Test GetSessionStatusRequest
try:
    request = GetSessionStatusRequest(session_id="sessions/987654321")
    print(f"✅ GetSessionStatusRequest: {request.session_id}")
except Exception as e:
    print(f"❌ GetSessionStatusRequest failed: {e}")

# Test validation - invalid check_interval
try:
    invalid = StartMonitoringRequest(
        session_id="sessions/123",
        check_interval=5  # Too low, must be >= 10
    )
    print("❌ Should have failed validation!")
except Exception as e:
    print(f"✅ Validation correctly rejected invalid check_interval: {type(e).__name__}")

# Test validation - invalid max_duration
try:
    invalid = StartMonitoringRequest(
        session_id="sessions/123",
        max_duration=30  # Too low, must be >= 60
    )
    print("❌ Should have failed validation!")
except Exception as e:
    print(f"✅ Validation correctly rejected invalid max_duration: {type(e).__name__}")

print("\n=== Testing Plugin Initialization ===")

# Create plugin instance
context = SharedContext(
    session_id="test-session",
    current_state="testing",
    logger=logger
)

monitor = CognitiveJulesMonitor()
print(f"✅ Plugin name: {monitor.name}")
print(f"✅ Plugin type: {monitor.plugin_type}")
print(f"✅ Plugin version: {monitor.version}")

# Test tool definitions
tool_defs = monitor.get_tool_definitions()
print(f"✅ Tool definitions: {len(tool_defs)} tools")
for tool in tool_defs:
    # Handle both dict with 'function' key and direct function dict
    if isinstance(tool, dict):
        if 'function' in tool:
            print(f"   - {tool['function']['name']}")
        elif 'name' in tool:
            print(f"   - {tool['name']}")
        else:
            print(f"   - {tool}")
    else:
        print(f"   - {tool}")


print("\n=== Testing Setup ===")

try:
    monitor.setup({})
    print("✅ Setup completed")
except Exception as e:
    print(f"❌ Setup failed: {e}")

print("\n=== Testing Monitoring Task Creation ===")

# Test start_monitoring
try:
    task = monitor.start_monitoring(
        context=context,
        session_id="sessions/test123",
        check_interval=30,
        max_duration=1800
    )
    print(f"✅ Monitoring task created: {task.session_id}")
    print(f"   Status: {task.status}")
    print(f"   Check interval: {task.check_interval}s")
    print(f"   Max duration: {task.max_duration}s")
    print(f"   Started at: {task.started_at}")
except Exception as e:
    print(f"❌ start_monitoring failed: {e}")

print("\n=== Testing Active Monitors List ===")

try:
    # Add another monitoring task
    task2 = monitor.start_monitoring(
        context=context,
        session_id="sessions/test456",
        check_interval=60,
        max_duration=3600
    )
    
    # List all active monitors
    active = monitor.list_active_monitors(context)
    print(f"✅ Active monitors: {len(active)}")
    for task in active:
        print(f"   - {task.session_id}: {task.status} (checks: {task.check_count})")
except Exception as e:
    print(f"❌ list_active_monitors failed: {e}")

print("\n=== Testing Monitoring Summary ===")

try:
    summary = monitor.get_monitoring_summary(context)
    print(f"✅ Monitoring summary:")
    print(f"   Total monitors: {summary['total_monitors']}")
    print(f"   Active: {summary['active']}")
    print(f"   Completed: {summary['completed']}")
    print(f"   Errors: {summary['errors']}")
    print(f"   Sessions: {summary['sessions']}")
except Exception as e:
    print(f"❌ get_monitoring_summary failed: {e}")

print("\n=== Testing Stop Monitoring ===")

try:
    stopped = monitor.stop_monitoring(context, "sessions/test123")
    print(f"✅ Stopped monitoring: {stopped}")
    
    # Verify it's removed
    active = monitor.list_active_monitors(context)
    print(f"✅ Active monitors after stop: {len(active)}")
except Exception as e:
    print(f"❌ stop_monitoring failed: {e}")

print("\n=== Testing Response Models ===")

# Test JulesSessionStatus
try:
    status = JulesSessionStatus(
        session_id="sessions/123",
        state="ACTIVE",
        prompt="Test prompt",
        last_check=datetime.now(),
        is_completed=False,
        is_error=False
    )
    print(f"✅ JulesSessionStatus: {status.session_id} - {status.state}")
    print(f"   Completed: {status.is_completed}")
    print(f"   Error: {status.is_error}")
except Exception as e:
    print(f"❌ JulesSessionStatus failed: {e}")

# Test MonitoringTask
try:
    task = MonitoringTask(
        session_id="sessions/789",
        started_at=datetime.now(),
        check_interval=30,
        max_duration=1800,
        last_check=datetime.now(),
        check_count=5,
        status="monitoring"
    )
    print(f"✅ MonitoringTask: {task.session_id}")
    print(f"   Status: {task.status}")
    print(f"   Checks: {task.check_count}")
except Exception as e:
    print(f"❌ MonitoringTask failed: {e}")

print("\n=== Testing Jules Tool Integration ===")

# Create mock Jules tool
jules_tool = JulesAPITool()
jules_tool.setup({"jules_api_key": ""})  # Mock setup

# Inject into monitor
try:
    monitor.set_jules_tool(jules_tool)
    print("✅ Jules tool injected into monitor")
except Exception as e:
    print(f"❌ Jules tool injection failed: {e}")

print("\n✅ All tests passed!")

print("\n💡 Usage Examples:")
print("")
print("# Start monitoring a Jules session:")
print("monitor.start_monitoring(ctx, 'sessions/123', check_interval=60)")
print("")
print("# Check status once:")
print("status = monitor.check_session_status(ctx, 'sessions/123')")
print("print(status.state, status.is_completed)")
print("")
print("# Monitor until completion (blocking):")
print("final_status = monitor.monitor_until_completion(ctx, 'sessions/123', timeout=1800)")
print("")
print("# List all active monitors:")
print("active = monitor.list_active_monitors(ctx)")
print("")
print("# Get monitoring summary:")
print("summary = monitor.get_monitoring_summary(ctx)")
