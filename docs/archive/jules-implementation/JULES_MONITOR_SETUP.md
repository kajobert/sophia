# Cognitive Jules Monitor - Documentation

## Overview

The **Cognitive Jules Monitor** plugin enables Sophie to autonomously track and respond to delegated Jules tasks. This is a critical component for self-improvement workflows where Sophie delegates coding tasks to Jules and needs to know when they're complete.

## Purpose

Enables Sophie to:
- ✅ Monitor Jules session progress in real-time
- ✅ Detect task completion automatically
- ✅ Identify errors and respond appropriately
- ✅ Read Jules outputs and responses
- ✅ Make autonomous decisions based on Jules status

## Architecture

### Components

1. **Monitoring Engine** - Periodic status checks with configurable intervals
2. **State Detection** - Identifies COMPLETED, FAILED, ACTIVE states
3. **Notification System** - Alerts when important events occur
4. **Summary Extraction** - Parses Jules responses and outputs

### Plugin Type

- **Type:** COGNITIVE
- **Purpose:** Autonomous task monitoring and coordination
- **Dependencies:** Requires `tool_jules` plugin

## Installation

The plugin is automatically loaded when Sophie starts. No additional installation required.

## Configuration

### Environment Variables

None required - uses Jules API credentials from `tool_jules` plugin.

### Setup

```python
from plugins.cognitive_jules_monitor import CognitiveJulesMonitor
from plugins.tool_jules import JulesAPITool

# Initialize monitor
monitor = CognitiveJulesMonitor()
monitor.setup({})

# Inject Jules tool dependency
jules_tool = JulesAPITool()
jules_tool.setup({})  # Uses JULES_API_KEY env var
monitor.set_jules_tool(jules_tool)
```

## Usage

### 1. Start Monitoring a Session

```python
# Sophie delegates task to Jules
session = jules_tool.create_session(
    context, 
    source="sources/github/ShotyCZ/sophia",
    prompt="Create tool_github_issues.py plugin..."
)

# Start monitoring
task = monitor.start_monitoring(
    context,
    session_id=session.name,
    check_interval=60,  # Check every 60 seconds
    max_duration=3600   # Stop after 1 hour
)

print(f"Monitoring: {task.session_id}")
```

### 2. Check Status Once

```python
# Check current status
status = monitor.check_session_status(context, "sessions/123")

print(f"State: {status.state}")
print(f"Completed: {status.is_completed}")
print(f"Error: {status.is_error}")

if status.is_completed:
    print(f"Summary: {status.completion_summary}")
```

### 3. Monitor Until Completion (Blocking)

```python
# Wait for Jules to complete (blocks until done)
final_status = monitor.monitor_until_completion(
    context,
    session_id="sessions/123",
    check_interval=30,  # Check every 30s
    timeout=1800        # Max 30 minutes
)

if final_status.is_completed:
    print("✅ Jules finished!")
    print(final_status.completion_summary)
elif final_status.is_error:
    print("❌ Jules encountered error:")
    print(final_status.error_message)
else:
    print("⏱️ Timeout reached")
```

### 4. List Active Monitors

```python
# Get all active monitoring tasks
active = monitor.list_active_monitors(context)

for task in active:
    print(f"{task.session_id}: {task.status}")
    print(f"  Checks: {task.check_count}")
    print(f"  Last state: {task.last_state}")
```

### 5. Get Monitoring Summary

```python
# Get overall statistics
summary = monitor.get_monitoring_summary(context)

print(f"Active monitors: {summary['active']}")
print(f"Completed: {summary['completed']}")
print(f"Errors: {summary['errors']}")
print(f"Sessions: {summary['sessions']}")
```

### 6. Stop Monitoring

```python
# Stop monitoring a specific session
stopped = monitor.stop_monitoring(context, "sessions/123")
print(f"Stopped: {stopped}")
```

## Response Models

### JulesSessionStatus

Complete status information for a Jules session:

```python
class JulesSessionStatus(BaseModel):
    session_id: str              # Jules session ID
    state: str                   # ACTIVE, COMPLETED, FAILED, etc.
    title: Optional[str]         # Session title
    prompt: str                  # Original task prompt
    create_time: Optional[str]   # When created
    update_time: Optional[str]   # Last update
    last_check: datetime         # When we last checked
    is_completed: bool           # True if finished
    is_error: bool               # True if failed
    error_message: Optional[str] # Error details if failed
    completion_summary: Optional[str]  # Summary if completed
```

### MonitoringTask

Active monitoring task details:

```python
class MonitoringTask(BaseModel):
    session_id: str           # Session being monitored
    started_at: datetime      # When monitoring started
    check_interval: int       # Seconds between checks
    max_duration: int         # Maximum monitoring time
    last_check: datetime      # Last status check
    check_count: int          # Number of checks performed
    status: str               # monitoring, completed, timeout, error
    last_state: Optional[str] # Last known Jules state
```

## Sophie's Workflow Example

### Autonomous Plugin Development

```python
# 1. Sophie identifies need for new plugin
need = "GitHub Issues integration for self-improvement"

# 2. Sophie does research
research = tavily.search(context, query="GitHub Issues API Python best practices")

# 3. Sophie creates specification
spec = llm.analyze(context, research.results)

# 4. Sophie delegates to Jules
session = jules.create_session(
    context,
    source="sources/github/ShotyCZ/sophia",
    prompt=spec.detailed_specification
)

# 5. Sophie starts monitoring
monitor.start_monitoring(
    context,
    session_id=session.name,
    check_interval=60
)

# 6. Sophie continues other work while Jules works
# (Non-blocking - Sophie can do other tasks)

# 7. Later, Sophie checks status
status = monitor.check_session_status(context, session.name)

if status.is_completed:
    # 8. Sophie reads results
    print(f"Jules completed: {status.completion_summary}")
    
    # 9. Sophie can test, merge, or request changes
    # This is where GitHub integration comes in!
```

## Best Practices

### 1. Check Intervals

- **Short tasks (< 5 min):** 15-30 seconds
- **Medium tasks (5-30 min):** 30-60 seconds
- **Long tasks (> 30 min):** 60-120 seconds

### 2. Timeouts

- Set reasonable max_duration based on expected task complexity
- Default 1 hour is good for most plugin development
- Use 2-4 hours for complex features

### 3. Error Handling

Always check for errors:

```python
status = monitor.check_session_status(context, session_id)

if status.is_error:
    context.logger.error(f"Jules failed: {status.error_message}")
    
    # Sophie can:
    # - Retry with modified prompt
    # - Ask for human help
    # - Try alternative approach
```

### 4. Resource Management

Stop monitoring when done:

```python
if status.is_completed or status.is_error:
    monitor.stop_monitoring(context, session_id)
```

## Integration with Other Plugins

### With tool_github

```python
# After Jules completes plugin
status = monitor.monitor_until_completion(context, session_id)

if status.is_completed:
    # Create PR with Jules results
    pr = github.create_pull_request(
        context,
        owner="ShotyCZ",
        repo="sophia",
        title=f"Add {plugin_name} plugin",
        body=status.completion_summary,
        head=jules_branch,
        base="master"
    )
    
    print(f"PR created: {pr.html_url}")
```

### With tool_performance_monitor

```python
# Log Jules delegation
performance.log_tool_usage(
    context,
    tool_name="tool_jules",
    method_name="create_session",
    success=True
)

# Monitor
status = monitor.monitor_until_completion(context, session_id)

# Log completion
performance.log_tool_usage(
    context,
    tool_name="cognitive_jules_monitor",
    method_name="monitor_until_completion",
    success=status.is_completed
)
```

## Troubleshooting

### Monitor Not Working

**Problem:** `RuntimeError: Jules API tool not available`

**Solution:**
```python
# Inject Jules tool
monitor.set_jules_tool(jules_tool)
```

### Session Not Found

**Problem:** `Failed to get Jules session: HTTP 404`

**Solution:**
- Verify session_id format: `sessions/1234567890`
- Check if session exists with Jules API
- Ensure Jules API credentials are valid

### Timeout Issues

**Problem:** Monitor times out before Jules completes

**Solution:**
- Increase `max_duration` parameter
- Check Jules session state manually
- Consider if task is too complex

## Performance Considerations

- **Memory:** Each active monitor uses ~1KB RAM
- **Network:** One API call per check (typically < 1KB)
- **CPU:** Minimal - just periodic polling

## Future Enhancements

Planned features:

1. **Webhook support** - Real-time notifications instead of polling
2. **Progress tracking** - Parse Jules output for completion percentage
3. **Auto-retry** - Restart failed sessions automatically
4. **Multi-session coordination** - Monitor multiple Jules tasks in parallel
5. **Smart intervals** - Adjust check frequency based on task complexity

## See Also

- [Jules API Documentation](JULES_API_DOCUMENTATION.md)
- [Jules API Setup](JULES_API_SETUP.md)
- [GitHub Integration](tool_github.py)
- [Performance Monitor](tool_performance_monitor.py)
