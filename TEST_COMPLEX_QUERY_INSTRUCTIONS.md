# 🧪 AUTONOMOUS COMPLEX QUERY TEST - Manual Instructions

## Test Setup
✅ SOPHIA is running with Claude 3.5 Sonnet
✅ Kernel bug fix is active  
✅ Web tools available: tool_tavily, tool_web_search

## Test Query (Complex Multi-Step)
```
Vyhledej aktuální informace o vývoji umělé inteligence v roce 2025 
a vytvoř mi stručný report se 3 hlavními trendy. Použij webové vyhledávání.
```

## Expected Behavior
SOPHIA should:
1. ✅ Use `cognitive_planner` to create multi-step plan
2. ✅ Execute `tool_tavily` or `tool_web_search` for web research
3. ✅ Synthesize information from web results
4. ✅ Create structured report with 3 trends
5. ✅ Return comprehensive response (100+ words)

## How to Test

### Option 1: Dashboard Chat (RECOMMENDED)
1. Open: http://127.0.0.1:8000/dashboard
2. Go to "Chat" tab
3. Paste query above
4. Click Send
5. Observe response time and quality

### Option 2: Monitor Logs During Test
```bash
# Terminal 1: Watch logs in real-time
tail -f logs/sophia.log | grep -E "Planner|Step|tavily|web_search|completed|Response"

# Terminal 2: Use Dashboard Chat to send query
```

## Success Criteria

### ✅ EXCELLENT (100% success)
- Uses web search tools (tavily/web_search)
- Returns 3 specific AI trends for 2025
- Response 150+ words with real data
- Execution time: 20-60s

### ⚠️ GOOD (75% success)  
- Partial web tool usage
- Returns 2-3 trends (may be generic)
- Response 80-150 words
- Execution time: 10-30s

### ❌ BASIC (50% success)
- No web tools used
- Generic AI knowledge response
- Response <80 words
- Execution time: <10s

## Monitoring Commands

```bash
# Check if web tools are being called
tail -50 logs/sophia.log | grep -i "tavily\|web_search"

# See execution plan
tail -100 logs/sophia.log | grep "Planner returned"

# Check tool execution
tail -100 logs/sophia.log | grep "Step.*completed"

# View final response
tail -50 logs/sophia.log | grep "Response ready"
```

## After Test

Compare results with:
- Previous llama3.1:8b test (generic response, no tools)
- Expected Claude 3.5 Sonnet (should use tools correctly)

Document findings in test results file.

---

**🚀 READY TO TEST!**

Open Dashboard and paste the query now.
