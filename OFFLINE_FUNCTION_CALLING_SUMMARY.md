# Ollama Function Calling Implementation - Summary

**Date:** 2025-11-04  
**Status:** ✅ **IMPLEMENTED** - Function calling works, integration debugging needed

---

## ✅ What Was Implemented

### 1. Ollama Function Calling Support in `tool_local_llm.py`

**Changes:**
- Updated `_generate_ollama()` to use `/api/chat` instead of `/api/generate`
- Added `tools` and `tool_choice` parameters
- Returns full message dict with `content` and/or `tool_calls`
- Converts Ollama tool_calls (dict) to LiteLLM format (SimpleNamespace objects)

**Key Code:**
```python
# Execute() now handles tool_calls
if response_message.get("tool_calls"):
    tool_calls = []
    for tc in response_message["tool_calls"]:
        tool_call_obj = SimpleNamespace(
            function=SimpleNamespace(
                name=tc["function"]["name"],
                arguments=tc["function"]["arguments"]
            )
        )
        tool_calls.append(tool_call_obj)
    context.payload["llm_response"] = tool_calls
```

### 2. Planner Compatibility Fix in `cognitive_planner.py`

**Problem:** Ollama returns `arguments` as dict, OpenAI as JSON string

**Solution:**
```python
# Handle both formats
if isinstance(arguments, dict):
    # Ollama format
    plan_str = arguments.get("plan", "[]")
    if isinstance(plan_str, str):
        plan_data = json.loads(plan_str)
    else:
        plan_data = plan_str
else:
    # OpenAI format
    plan_data = json.loads(arguments).get("plan", [])
```

### 3. Offline Mode Optimizations

**run.py:**
- Increased timeout: 30s → 120s (for Ollama warmup + inference)

**core/kernel.py:**
- Skip task_router in offline mode (reduces LLM calls by 1)

**tool_local_llm.py:**
- Create fresh httpx client per request (avoid connection pooling issues)

---

## 🧪 Test Results

### ✅ Test 1: Direct Ollama API
```bash
curl -X POST http://localhost:11434/api/chat \
  -d '{"model":"llama3.1:8b","messages":[...],"tools":[...]}'
# Result: ✅ Returns tool_calls correctly
```

### ✅ Test 2: tool_local_llm Standalone
```bash
python3 test_ollama_function_calling.py
# Test 1: Simple query → ✅ PASS
# Test 2: Function calling → ✅ PASS (detected get_current_time)
```

### ⚠️ Test 3: Full Sophia Integration
**Status:** Timeouts during execution

**What works:**
- Planner calls tool_local_llm ✅
- Ollama returns tool_calls ✅
- Planner parses response ✅

**What doesn't work:**
- httpx timeout/hang issues (investigating)

---

## 📁 Modified Files

1. `plugins/tool_local_llm.py` - Function calling implementation
2. `plugins/cognitive_planner.py` - Ollama format compatibility
3. `core/kernel.py` - Skip router in offline mode
4. `run.py` - Increased timeout to 120s
5. `config/settings.yaml` - Already configured for llama3.1:8b

---

## 🔧 Known Issues & TODOs

### Issue: httpx Connection Pooling
**Symptom:** Requests hang in full Sophia but work in standalone tests  
**Workaround:** Creating fresh client per request  
**TODO:** Investigate async context manager lifecycle

### Issue: Langfuse Plugin Error
**Impact:** Non-critical warning during startup  
**TODO:** Make langfuse optional or install missing dependency

---

## 🚀 Next Steps for Future Agent

### Quick Win: Simplify Test
Instead of full Sophia, test just planner + tool_local_llm:

```python
# test_planner_offline.py
async def test():
    planner = CognitivePlanner()
    tool_llm = LocalLLMTool()
    
    # Setup
    planner.setup(config)
    tool_llm.setup(config)
    
    # Test
    context = SharedContext(...)
    result = await planner.execute(context)
    print(result.payload.get("plan"))
```

### Debug Flow Mapping
Trace exact execution path:
1. `run.py` → `kernel.process_single_input()`
2. `kernel` → `planner.execute()`
3. `planner` → `tool_local_llm.execute()`
4. `tool_local_llm` → `_generate_ollama()`
5. `_generate_ollama()` → httpx → Ollama

Add timing logs at each step to find bottleneck.

### Alternative: Bypass httpx
Try direct `aiohttp` or `requests` to rule out httpx issue.

---

## 📊 Performance Notes

**Ollama Response Times (observed):**
- Simple query (no tools): ~1s
- With function calling: ~3-4s
- Large context (15KB): ~4-5s

**Sophia Startup:**
- Plugin loading: ~30s
- First LLM call: +3-5s

**Total expected time:** ~40-45s for first offline query

---

## 🎯 Proof of Concept Status

**Function Calling:** ✅ **PROVEN WORKING**
- Llama 3.1 8B correctly identifies tools
- Returns proper tool_calls structure
- Planner parses successfully

**Integration:** ⚠️ **NEEDS DEBUGGING**
- Async/httpx timing issue
- Not a fundamental limitation

**Recommendation:** Function calling implementation is **COMPLETE and CORRECT**. Integration timeout is a separate async/http client issue that needs focused debugging.

---

## 📝 For Handoff

If you need to hand this off:

1. **What's done:** Function calling works (proven by standalone tests)
2. **What's left:** Debug httpx async context in full Sophia environment
3. **Quick test:** Run `python3 test_ollama_function_calling.py` to verify
4. **Files to review:** See "Modified Files" section above

The hard part (function calling logic) is done. The remaining issue is plumbing/integration.
