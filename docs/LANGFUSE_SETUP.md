# Langfuse Observability Integration - Setup Guide

## Overview

The Langfuse plugin provides comprehensive tracing, debugging, and performance monitoring for Sophia V2 AI agent using [Langfuse](https://langfuse.com/) - an open-source LLM observability platform.

## Features

✅ **Trace Visualization**
- Map agent decision trees, tool calls, and LLM interactions
- Hierarchical view of execution flow
- Session-based grouping

✅ **Error Analytics**
- Classify failures by type (context window, tool timeout, etc.)
- Track error frequency and patterns
- Link errors to specific code versions (Git integration)

✅ **Performance Metrics**
- Track latency/cost per agent step
- Compare runs across deployments
- Monitor token usage and costs

✅ **Multi-Agent Support**
- Trace inter-agent communication
- Track task delegation
- Monitor reasoning paths

## Installation

### 1. Install Langfuse SDK

```bash
pip install langfuse
```

Or add to `requirements.in`:
```
langfuse>=2.0.0
```

### 2. Get Langfuse Credentials

**Option A: Cloud (Recommended for getting started)**
1. Sign up at https://cloud.langfuse.com
2. Create a new project
3. Copy your Public Key and Secret Key

**Option B: Self-Hosted (For data control)**
1. Follow [Langfuse self-hosting guide](https://langfuse.com/docs/deployment/self-host)
2. Generate API keys in your instance

### 3. Configure Environment Variables

Add to `.env`:
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

### 4. Enable Plugin

The plugin is automatically loaded by Sophia's PluginManager. No additional configuration needed!

## Usage

### Basic Trace Example

```python
# Sophie can use the plugin like this:

# 1. Create a trace to track the entire workflow
trace = tool_langfuse.create_trace(
    context=context,
    name="user_query_processing",
    input_text="What is the weather in Prague?",
    metadata={"user_id": "123", "session": "abc"}
)

# 2. Create spans for individual operations
span_search = tool_langfuse.create_span(
    context=context,
    trace_id=trace.id,
    name="tavily_search",
    input_data={"query": "Prague weather"},
    output_data={"results": 5, "relevance": 0.95}
)

# 3. Log events for debugging
tool_langfuse.log_event(
    context=context,
    trace_id=trace.id,
    name="llm_response_generated",
    level="INFO",
    metadata={"model": "claude-3.5-sonnet", "tokens": 150}
)

# 4. Add quality scores
tool_langfuse.add_score(
    context=context,
    trace_id=trace.id,
    name="response_quality",
    value=0.92,
    comment="User satisfied with answer"
)

# 5. Retrieve traces for analysis
recent_traces = tool_langfuse.get_traces(context, limit=10)
```

### Integration with Consciousness Loop

For automatic tracing of all Sophia operations, you can integrate Langfuse into the Kernel's consciousness loop:

```python
# In core/kernel.py (future enhancement):

async def consciousness_loop(self, context: SharedContext):
    # Create trace at start of loop
    trace = self.langfuse_plugin.create_trace(
        context=context,
        name="consciousness_loop",
        input_text=context.user_input
    )
    
    # Add spans for each phase
    for plugin in self.plugins:
        span = self.langfuse_plugin.create_span(
            context=context,
            trace_id=trace.id,
            name=plugin.name,
            input_data={"state": context.current_state}
        )
        
        # Execute plugin...
        
        # Update span with output
        # (requires Langfuse SDK support for span updates)
```

## Tool Methods

### create_trace()
Creates a new trace for tracking AI agent execution.

**Parameters:**
- `name` (str): Name of the trace
- `input_text` (str): Input text for the trace
- `output_text` (str, optional): Output text
- `model` (str, optional): Model name used
- `metadata` (dict, optional): Additional metadata

**Returns:** `LangfuseTrace` object with `id`, `name`, `timestamp`, `session_id`, `metadata`

### create_span()
Creates a span within a trace to track a specific operation.

**Parameters:**
- `trace_id` (str): ID of the parent trace
- `name` (str): Name of the span (e.g., 'tavily_search', 'llm_call')
- `input_data` (dict, optional): Input data for the span
- `output_data` (dict, optional): Output data from the span
- `metadata` (dict, optional): Additional metadata

**Returns:** `LangfuseSpan` object with `id`, `trace_id`, `name`, `start_time`, etc.

### log_event()
Logs an event within a trace (for debugging, errors, warnings).

**Parameters:**
- `trace_id` (str): ID of the parent trace
- `name` (str): Event name
- `level` (str): Event level - one of: DEBUG, INFO, WARNING, ERROR
- `metadata` (dict, optional): Event metadata

**Returns:** Success message string

### add_score()
Adds a score/evaluation to a trace.

**Parameters:**
- `trace_id` (str): ID of the trace to score
- `name` (str): Name of the score metric (e.g., 'accuracy', 'user_rating')
- `value` (float): Score value
- `comment` (str, optional): Optional comment about the score

**Returns:** Success message string

### get_traces()
Retrieves traces for analysis and debugging.

**Parameters:**
- `limit` (int, optional): Maximum number of traces to retrieve (default: 10)

**Returns:** List of trace dictionaries with `id`, `name`, `timestamp`, etc.

## Langfuse Dashboard

After creating traces, view them in the Langfuse dashboard:

1. **Cloud:** https://cloud.langfuse.com
2. **Self-hosted:** Your instance URL

### Dashboard Features:
- 📊 Trace visualization (tree view)
- 📈 Performance metrics (latency, cost)
- 🔍 Full-text search across traces
- 📉 Cost tracking and budgets
- 🏷️ Filtering by metadata, session, user
- 📝 Annotations and comments

## Best Practices

### 1. Use Descriptive Names
```python
# ✅ Good
create_trace(name="user_query_weather_prague", ...)

# ❌ Bad
create_trace(name="trace1", ...)
```

### 2. Add Metadata for Context
```python
create_trace(
    name="llm_call",
    metadata={
        "model": "claude-3.5-sonnet",
        "user_id": user_id,
        "intent": "information_retrieval",
        "complexity": "simple"
    }
)
```

### 3. Log Errors as Events
```python
try:
    result = tool_tavily.search(...)
except Exception as e:
    log_event(
        trace_id=trace.id,
        name="tool_error",
        level="ERROR",
        metadata={"error": str(e), "tool": "tavily"}
    )
```

### 4. Score Quality
```python
# After generating response
add_score(
    trace_id=trace.id,
    name="hallucination_check",
    value=0.98,  # 0.0 = hallucination, 1.0 = factual
    comment="All facts verified against source"
)
```

## Privacy & Data Control

### Self-Hosting
For full data control, self-host Langfuse:
```bash
# Docker Compose example
version: '3'
services:
  langfuse:
    image: langfuse/langfuse:latest
    environment:
      - DATABASE_URL=postgresql://...
      - NEXTAUTH_SECRET=your-secret
    ports:
      - "3000:3000"
```

Set `LANGFUSE_HOST=http://localhost:3000` in `.env`

### Data Retention
Configure in Langfuse settings:
- Trace retention period
- PII filtering rules
- Export options

## Troubleshooting

### "SDK not installed"
```bash
pip install langfuse
```

### "Authentication failed"
1. Verify keys in `.env`
2. Check key format: `pk-lf-...` and `sk-lf-...`
3. Ensure no extra whitespace in env vars

### "Cannot connect to Langfuse"
1. Check `LANGFUSE_HOST` URL
2. Verify firewall/proxy settings
3. Test connection: `curl https://cloud.langfuse.com`

### "Traces not appearing"
1. Check Langfuse dashboard for your project
2. Verify `session_id` in traces
3. Wait a few seconds for sync (async upload)
4. Check logs for upload errors

## Cost Considerations

### Langfuse Cloud Pricing (as of 2024)
- **Free tier:** 50k observations/month
- **Pro:** $49/month for 500k observations
- **Enterprise:** Custom pricing

### Self-Hosted
- Free (open-source)
- Costs: Infrastructure only (compute + storage)

## Related Documentation

- [Langfuse Official Docs](https://langfuse.com/docs)
- [Langfuse Python SDK](https://langfuse.com/docs/sdk/python)
- [Sophie's Research](../WORKLOG.md#mission-14-langfuse-integration) (when added)

## Example: Full Workflow Trace

```python
# Complete example showing all features

# 1. Start trace
trace = tool_langfuse.create_trace(
    context=context,
    name="research_task",
    input_text="Research AI agent observability tools",
    metadata={"priority": "high"}
)

# 2. Search with Tavily
span_search = tool_langfuse.create_span(
    context=context,
    trace_id=trace.id,
    name="tavily_search",
    input_data={"query": "AI observability 2024"},
    output_data={"results": 5, "avg_score": 0.92}
)

# 3. Log search completion
tool_langfuse.log_event(
    context=context,
    trace_id=trace.id,
    name="search_completed",
    level="INFO",
    metadata={"sources": 5}
)

# 4. Analyze results with LLM
span_llm = tool_langfuse.create_span(
    context=context,
    trace_id=trace.id,
    name="llm_analysis",
    input_data={"model": "claude-3.5-sonnet"},
    output_data={"tokens": 450, "cost": 0.012}
)

# 5. Score the result
tool_langfuse.add_score(
    context=context,
    trace_id=trace.id,
    name="task_completion",
    value=1.0,
    comment="Successfully identified Langfuse as solution"
)

# View in dashboard: https://cloud.langfuse.com/traces/{trace.id}
```

## Next Steps

1. ✅ Install Langfuse SDK
2. ✅ Get API credentials
3. ✅ Configure environment variables
4. 🔄 Test with Sophie
5. 📊 View traces in dashboard
6. 🚀 Integrate into production workflows
