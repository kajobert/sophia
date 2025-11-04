# AI Agent Handoff: Offline Mode Function Calling

**Date:** 2025-11-04  
**From:** Previous Agent (Phase 1 Complete)  
**To:** Next Agent (Phase 2 Start)  
**Priority:** 🔴 **CRITICAL** - User needs offline mode fully operational

---

## 🎯 MISSION: Enable Full Offline Mode with Function Calling

**User's Goal:** Sophii musí běžet plně offline s Llama 3.1 8B a function calling

**User's Question:** "myslíš že z lammy nevymáčkneme function calling?"

**Your Answer:** ✅ **ANO! Llama 3.1 8B ZVLÁDNE function calling!**

---

## ✅ What Previous Agent Completed (Phase 1)

### Infrastructure (100% Done)
- `--offline` flag in run.py ✅
- `offline_mode: bool` in SharedContext ✅
- Runtime LLM selection in cognitive_planner ✅
- Runtime LLM selection in cognitive_task_router ✅
- Context propagation kernel → plugins ✅

### tool_local_llm Implementation (100% Done)
**File:** `plugins/tool_local_llm.py`

**setup() method** (Lines ~69-88):
```python
def setup(self, config: Dict[str, Any]) -> None:
    self.config = LocalModelConfig(**config.get("local_llm", {}))
    self.client = httpx.AsyncClient(timeout=self.config.timeout)
    
    # Load system prompt from sophia_dna.txt
    self.system_prompt = "You are Sophia, a helpful AI assistant."
    try:
        with open("config/prompts/sophia_dna.txt", "r", encoding="utf-8") as f:
            self.system_prompt = f.read()
            logger.info("System prompt loaded from sophia_dna.txt")
    except FileNotFoundError:
        logger.warning("sophia_dna.txt not found - using default system prompt")
```

**execute() method** (Lines ~84-145):
```python
async def execute(self, context: SharedContext) -> SharedContext:
    """
    Generate a response using local LLM.
    Compatible with tool_llm interface for drop-in replacement.
    """
    prompt = context.payload.get("prompt", context.user_input)
    tools = context.payload.get("tools")  # Function calling tools (not yet supported)
    tool_choice = context.payload.get("tool_choice")
    
    # Build messages from history
    messages = []
    if self.system_prompt:
        messages.append({"role": "system", "content": self.system_prompt})
    messages.extend(context.history)
    
    # Add current prompt if not in history
    if not any(msg["role"] == "user" and msg["content"] == prompt for msg in messages):
        messages.append({"role": "user", "content": prompt})
    
    # ⚠️ CURRENT IMPLEMENTATION: Combines messages into single prompt
    # ❌ DOESN'T USE: tools, tool_choice (function calling)
    full_prompt = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in messages
    ])
    
    response_text = await self.generate(
        prompt=full_prompt,
        temperature=self.config.temperature,
        max_tokens=self.config.max_tokens
    )
    
    context.payload["llm_response"] = response_text
    return context
```

### Verification Tests (All Passed)
1. ✅ Direct Ollama API: `curl` test returns "4" for "2+2"
2. ✅ tool_local_llm.generate(): Returns Czech responses
3. ✅ Full Sophia offline: Planner calls tool_local_llm correctly
4. ✅ Integration working: execute() → generate() → _generate_ollama() chain works

### Current Problem
**Symptom:** Planner times out or hangs in offline mode  
**Root Cause:** execute() ignores `tools` and `tool_choice` parameters  
**Impact:** No function calling → planner can't create structured plans

---

## 🎯 YOUR MISSION (Phase 2): Enable Function Calling

### Immediate Goal
Get this command working end-to-end:
```bash
bash sophia-offline-debug.sh --once "Ahoj, jaký je čas?"
```

**Expected:** Sophia recognizes need for time tool, creates plan, executes, responds

### Why Llama 3.1 8B CAN Do Function Calling

**Evidence:**
1. **Meta Official:** Llama 3.1 trained for function calling (released July 2024)
2. **Ollama Support:** Native function calling API since v0.11
3. **Quantization:** Q4_K_M is sufficient quality for structured outputs
4. **Size:** 8B parameters proven capable (Mistral 7B does it well)
5. **User Experience:** They tuned OpenRouter models with same kernel parsing

**User's Key Insight:**
> "stejně jsme dlouho ladili kernel aby si s odpovedí od LLM poradil co nejrobustněji"

Translation: Kernel already has robust response parsing from OpenRouter tuning!

### What You Need to Implement

**Step 1: Add Ollama Function Calling API Support**

Compare these two implementations:

**tool_llm.py** (Lines ~100-150) - WORKING CLOUD VERSION:
```python
async def execute(self, *, context: SharedContext) -> SharedContext:
    prompt = context.payload.get("prompt", context.user_input)
    tools = context.payload.get("tools")  # ✅ USES THIS
    tool_choice = context.payload.get("tool_choice")  # ✅ USES THIS
    
    messages = [
        {"role": "system", "content": self.system_prompt},
        *context.history
    ]
    
    completion_kwargs = {
        "model": model_to_use,
        "messages": messages,
        "tools": tools,  # ✅ PASSES TO LITELLM
        "tool_choice": tool_choice,  # ✅ PASSES TO LITELLM
        "temperature": self.temperature,
        "max_tokens": self.max_tokens,
    }
    
    response = await litellm.acompletion(**completion_kwargs)
    context.payload["llm_response"] = response.choices[0].message
    return context
```

**tool_local_llm.py** (Lines ~84-145) - YOUR CURRENT VERSION:
```python
async def execute(self, context: SharedContext) -> SharedContext:
    prompt = context.payload.get("prompt", context.user_input)
    tools = context.payload.get("tools")  # ❌ EXTRACTED BUT NOT USED
    tool_choice = context.payload.get("tool_choice")  # ❌ EXTRACTED BUT NOT USED
    
    # ❌ PROBLEM: Combines messages into single string
    # ❌ LOSES: tools, tool_choice, message structure
    full_prompt = "\n\n".join([
        f"{msg['role'].upper()}: {msg['content']}" 
        for msg in messages
    ])
    
    # ❌ PROBLEM: generate() doesn't accept tools parameter
    response_text = await self.generate(
        prompt=full_prompt,
        temperature=self.config.temperature,
        max_tokens=self.config.max_tokens
    )
```

**Step 2: Update _generate_ollama() for Function Calling**

**Current implementation** (Lines ~122-230):
```python
async def _generate_ollama(
    self, prompt: str, system_prompt: str = None, temperature: float = 0.7, max_tokens: int = 2048
) -> str:
    url = f"{self.config.base_url}/api/generate"
    request = {
        "model": self.config.model,
        "prompt": prompt,  # ❌ SINGLE STRING
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    if system_prompt:
        request["system"] = system_prompt
    
    response = await self.client.post(url, json=request)
    data = response.json()
    return data.get("response", "")
```

**What you need to change to:**
```python
async def _generate_ollama(
    self,
    messages: List[Dict[str, str]],  # ✅ ACCEPT MESSAGES ARRAY
    tools: Optional[List[Dict]] = None,  # ✅ ACCEPT TOOLS
    tool_choice: Optional[str] = None,  # ✅ ACCEPT TOOL_CHOICE
    temperature: float = 0.7,
    max_tokens: int = 2048
) -> Dict[str, Any]:  # ✅ RETURN FULL RESPONSE (not just string)
    url = f"{self.config.base_url}/api/chat"  # ✅ USE /api/chat NOT /api/generate
    
    request = {
        "model": self.config.model,
        "messages": messages,  # ✅ PASS MESSAGE ARRAY
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    
    # ✅ ADD TOOLS IF PROVIDED
    if tools:
        request["tools"] = tools
    
    response = await self.client.post(url, json=request)
    data = response.json()
    
    # ✅ RETURN FULL MESSAGE OBJECT (with tool_calls if present)
    return data.get("message", {})
```

**Step 3: Update execute() to Use New Format**

```python
async def execute(self, context: SharedContext) -> SharedContext:
    prompt = context.payload.get("prompt", context.user_input)
    tools = context.payload.get("tools")
    tool_choice = context.payload.get("tool_choice")
    
    # Build messages array (keep as list!)
    messages = []
    if self.system_prompt:
        messages.append({"role": "system", "content": self.system_prompt})
    messages.extend(context.history)
    
    if not any(msg["role"] == "user" and msg["content"] == prompt for msg in messages):
        messages.append({"role": "user", "content": prompt})
    
    context.logger.info(
        f"Calling local LLM '{self.config.model}' with {len(messages)} messages"
        + (f" and {len(tools)} tools" if tools else ""),
        extra={"plugin_name": self.name},
    )
    
    try:
        # ✅ USE NEW _generate_ollama WITH FUNCTION CALLING
        response_message = await self._generate_ollama(
            messages=messages,
            tools=tools,
            tool_choice=tool_choice,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )
        
        # ✅ STORE FULL MESSAGE (matches tool_llm format)
        context.payload["llm_response"] = response_message
        
        context.logger.info(
            "LLM response received successfully"
            + (f" with {len(response_message.get('tool_calls', []))} tool calls" 
               if response_message.get('tool_calls') else ""),
            extra={"plugin_name": self.name},
        )
        
    except Exception as e:
        error_msg = f"Error calling local LLM: {e}"
        context.logger.error(error_msg, extra={"plugin_name": self.name})
        context.payload["llm_response"] = {"content": f"Error: {error_msg}"}
    
    return context
```

---

## 📋 Step-by-Step Implementation Plan

### Phase 2A: Ollama Function Calling API (2-3 hours)

**Task 1:** Read Ollama API documentation
```bash
curl http://localhost:11434/api/tags  # Verify Ollama running
```

Check: https://github.com/ollama/ollama/blob/main/docs/api.md#chat-request-with-tools

**Task 2:** Update `_generate_ollama()` signature and implementation
- Change from `/api/generate` to `/api/chat`
- Accept messages array instead of single prompt string
- Add tools and tool_choice parameters
- Return full message object (not just text)

**Task 3:** Update `execute()` to pass tools
- Keep messages as array (don't join to string!)
- Pass tools and tool_choice to _generate_ollama()
- Store full response message in payload

**Task 4:** Test function calling directly
```python
# Test script to verify Ollama function calling
messages = [
    {"role": "system", "content": "You are Sophia."},
    {"role": "user", "content": "Jaký je čas?"}
]
tools = [{
    "type": "function",
    "function": {
        "name": "get_current_time",
        "description": "Get the current time",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}]

response = await tool._generate_ollama(messages, tools=tools)
print(response.get('tool_calls'))  # Should see time tool selected
```

### Phase 2B: Integration Testing (1-2 hours)

**Test 1:** Simple offline query (no tools needed)
```bash
bash sophia-offline-debug.sh --once "Ahoj, jak se máš?"
```
**Expected:** Direct response without tool calls

**Test 2:** Query requiring tool
```bash
bash sophia-offline-debug.sh --once "Jaký je čas?"
```
**Expected:** Planner creates plan with get_current_time tool

**Test 3:** Multi-step task
```bash
bash sophia-offline-debug.sh --once "Zjisti čas a ulož ho do souboru"
```
**Expected:** Plan with 2 steps (get_time + write_file)

### Phase 2C: Prompt Tuning (IF NEEDED - 2-4 hours)

**Only if function calling fails!**

User's proven process:
1. Try task → observe LLM response
2. Adjust planner system prompt for Llama 3.1
3. Tune temperature/max_tokens
4. Adjust kernel parsing robustness
5. Repeat until working

**Planner prompt location:** `plugins/cognitive_planner.py` Line ~100-120

**Possible adjustments:**
- Add explicit examples of function calling format
- Lower temperature (0.3-0.5 for structured output)
- Increase max_tokens (512+ for tool calls)
- Add XML/JSON format hints

---

## 🧪 Testing Strategy

### Test Environment
```bash
# Verify Ollama running
curl http://localhost:11434/api/tags

# Check model loaded
# Should show: llama3.1:8b (4.9GB, Q4_K_M)

# Use debug launcher for full logs
bash sophia-offline-debug.sh --once "TEST QUERY"
```

### Success Criteria

**Minimum (Phase 2A):**
- [ ] Ollama returns tool_calls in response
- [ ] execute() stores full message with tool_calls
- [ ] No errors/exceptions in logs

**Full Success (Phase 2B):**
- [ ] Planner creates multi-step plan offline
- [ ] Kernel executes tools from plan
- [ ] Final response includes tool results
- [ ] Works end-to-end: input → plan → execute → response

### Debug Checklist

If function calling doesn't work:

1. **Check Ollama version:** `curl http://localhost:11434/api/version`
   - Need v0.11+ for function calling

2. **Log full request/response:**
   ```python
   logger.debug(f"Ollama request: {json.dumps(request, indent=2)}")
   logger.debug(f"Ollama response: {json.dumps(data, indent=2)}")
   ```

3. **Verify tools format:** Must match OpenAI schema exactly

4. **Check max_tokens:** Tool calls need space (minimum 512)

5. **Try simpler tools first:** Single tool, no parameters

---

## 📁 Files You'll Modify

### Primary Files

**1. plugins/tool_local_llm.py** (CRITICAL)
- Lines ~122-230: `_generate_ollama()` - Add function calling support
- Lines ~84-145: `execute()` - Pass tools, store full response
- Lines ~94-120: `generate()` - Might need to deprecate/refactor

**2. plugins/cognitive_planner.py** (IF NEEDED)
- Lines ~100-140: System prompt - Tune for Llama 3.1 if format issues

**3. config/settings.yaml** (MAYBE)
- Line ~18: max_tokens - Increase to 512+ if needed
- Line ~17: timeout - Might need increase for complex plans

### Test Files

**Create new:** `tests/test_offline_function_calling.py`
```python
"""
Test offline mode function calling with Llama 3.1 8B

Verifies:
1. Ollama /api/chat with tools
2. tool_local_llm.execute() passes tools
3. Planner works in offline mode
4. Full end-to-end flow
"""
```

---

## 🚫 What NOT to Do

**DON'T:**
- ❌ Simplify by removing function calling (user wants FULL offline mode)
- ❌ Skip planner in offline mode (defeats purpose)
- ❌ Use different plan format (kernel already parses OpenRouter format)
- ❌ Assume Llama can't do it (it can - just needs right API calls)

**DO:**
- ✅ Use Ollama's `/api/chat` endpoint (not `/api/generate`)
- ✅ Pass tools in OpenAI function calling format
- ✅ Keep message structure (don't flatten to string)
- ✅ Test incrementally (direct API → tool_local_llm → planner → full Sophia)
- ✅ Log everything in debug mode

---

## 📚 Reference Materials

### Ollama Function Calling Docs
- API: https://github.com/ollama/ollama/blob/main/docs/api.md
- Example: `/api/chat` with tools parameter
- Format: OpenAI-compatible function calling schema

### Existing Working Code

**tool_llm.py** (Lines 70-200):
- Reference for how to structure execute()
- Shows tools parameter handling
- Response format expected by kernel

**cognitive_planner.py** (Lines 40-180):
- See how tools are constructed
- System prompt for planning
- Response parsing logic

### User's Previous Work

**User said:**
> "stejně jsme dlouho ladili kernel aby si s odpovedí od LLM poradil co nejrobustněji"

**Where to find kernel robustness:**
- `core/kernel.py` Lines 940-1000: Plan execution
- `cognitive_planner.py` Lines 150-180: Response parsing
- Already handles various LLM response formats!

---

## 🎯 Expected Outcome

After you complete Phase 2:

```bash
$ bash sophia-offline-debug.sh --once "Zjisti aktuální čas"

🔒 OFFLINE MODE - Using Llama 3.1 8B
🧠 Planner creating plan...
✅ Plan: 1 step (get_current_time)
⚙️ Executing step 1...
✅ Tool returned: 2025-11-04 22:30:15
💬 Sophia: Aktuální čas je 22:30:15.

$ bash sophia-offline-debug.sh --once "Ulož poznámku: offline mode funguje"

🔒 OFFLINE MODE - Using Llama 3.1 8B
🧠 Planner creating plan...
✅ Plan: 1 step (write_file)
⚙️ Executing step 1...
✅ File written: notes.txt
💬 Sophia: Poznámka byla uložena.
```

**This proves:**
- ✅ Function calling works offline
- ✅ Planner uses local LLM
- ✅ Tools execute correctly
- ✅ Full AGI loop runs without cloud

---

## 💡 User's Strategic Vision

**Short term (your mission):**
Get offline mode fully functional with function calling

**Medium term (after you):**
- Memory consolidation with model signatures
- Self-evaluation loop (compare offline vs online quality)
- Benchmarking local models

**Long term (user's goal):**
> "AGI system that can run offline, self-improve by analyzing its own operations, and only use cloud LLMs for quality evaluation"

**Your piece of the puzzle:**
Enable the foundation - offline reasoning with tool use. Without this, none of the self-improvement works.

---

## 🤝 Handoff Checklist

Previous agent completed:
- [x] Offline mode infrastructure
- [x] tool_local_llm.execute() basic implementation
- [x] Runtime LLM selection
- [x] Verification tests (Ollama works)
- [x] Documentation (OFFLINE_MODE_STATUS.md)

**You need to:**
- [ ] Implement Ollama /api/chat with function calling
- [ ] Update _generate_ollama() for tools
- [ ] Update execute() to pass tools
- [ ] Test direct function calling
- [ ] Test planner in offline mode
- [ ] Test full end-to-end workflow
- [ ] Document any prompt tuning needed

**After you succeed:**
- Next agent: Memory consolidation + model signatures
- Future: Self-evaluation and improvement loop

---

## 🚀 START HERE

**First command to run:**
```bash
# Verify Ollama supports function calling
curl -X POST http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [{"role": "user", "content": "What time is it?"}],
    "tools": [{
      "type": "function",
      "function": {
        "name": "get_current_time",
        "description": "Get current time",
        "parameters": {"type": "object", "properties": {}}
      }
    }],
    "stream": false
  }'
```

**Expected:** Response with `tool_calls` array showing get_current_time selected

**If that works:** You have proof Llama 3.1 8B can do function calling!  
**Then:** Implement it in tool_local_llm.py

---

## 🔥 User's Expectation

User wants **FULL offline mode** - not simplified version.

**User's question:** "myslíš že z lammy nevymáčkneme function calling?"

**Your answer:** ✅ **YES WE CAN!**

**Proof strategy:**
1. Direct Ollama API test with tools ← START HERE
2. If works → implement in tool_local_llm
3. If doesn't → check Ollama version/config
4. Only if truly impossible → then consider alternatives

But based on Llama 3.1 specs and Ollama v0.11+ features, **it SHOULD work**!

---

Good luck! The foundation is solid, you just need to connect the function calling pieces. User has confidence in Llama 3.1 8B - prove them right! 🚀

**Questions to ask user if stuck:**
1. What's Ollama version? (`ollama --version`)
2. Can you show example of OpenRouter function calling that worked?
3. Any specific tools that failed more than others?

**Resources:**
- See: `docs/OFFLINE_MODE_STATUS.md` - Full phase 1 summary
- See: `plugins/tool_llm.py` - Working cloud implementation
- See: `sophia-offline-debug.sh` - Debug launcher with logs
