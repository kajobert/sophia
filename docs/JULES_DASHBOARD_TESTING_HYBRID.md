# Task for Jules: E2E Dashboard Testing with HYBRID Server

**Priority:** HIGH  
**Type:** Full Integration Testing with REAL LLM  
**Estimated Time:** 15-20 minutes  
**Deliverable:** Test report + Screenshots + Chat interaction logs

---

## 🎯 Objective

Test SOPHIA dashboard with **REAL interaction capabilities**:
- ✅ Real-time chat with OpenRouter LLM (DeepSeek)
- ✅ WebSocket communication
- ✅ Task queue functionality
- ✅ E2E frontend testing with Playwright

**NO full Sophia kernel, but REAL LLM responses!**

---

## 🔑 Prerequisites

### 1. OpenRouter API Key (Jules needs this)

**Get free API key:**
1. Visit: https://openrouter.ai/keys
2. Sign up (free tier available)
3. Create API key
4. Copy key (format: `sk-or-v1-...`)

**Set environment variable:**
```bash
export OPENROUTER_API_KEY="sk-or-v1-xxxxxxxxxxxxx"
```

### 2. Python Dependencies (Jules VM has Python 3.12)

```bash
pip install pytest pytest-playwright playwright fastapi uvicorn httpx
playwright install chromium
```

---

## 📋 Testing Strategy: 3 Modes

### **Mode 1: MOCK Server** (No API key needed)
- ✅ Frontend-only testing
- ✅ Fake data, no LLM
- ✅ Fast (< 5 minutes)
- ❌ No chat interaction

### **Mode 2: HYBRID Server** ⭐ RECOMMENDED
- ✅ Real LLM chat (OpenRouter)
- ✅ WebSocket support
- ✅ Task queue
- ⚠️ Requires API key
- ⚠️ Costs ~$0.001 per test run

### **Mode 3: FULL Sophia** (Impossible in Jules VM)
- ❌ Needs Ollama (local LLM)
- ❌ Needs all cognitive plugins
- ❌ Complex setup
- ❌ Jules VM cannot run this

---

## 🚀 Execution: HYBRID Mode (Recommended)

### Step 1: Set API Key

```bash
# Jules creates secrets file
cat > .env.test << 'EOF'
OPENROUTER_API_KEY=sk-or-v1-PASTE_YOUR_KEY_HERE
EOF

# Load environment
export $(cat .env.test | xargs)

# Verify
echo $OPENROUTER_API_KEY  # Should show your key
```

### Step 2: Start Hybrid Server

```bash
# Terminal 1: Start server
python scripts/dashboard_server_hybrid.py
```

**Expected output:**
```
============================================================
🚀 SOPHIA Dashboard Server - HYBRID MODE
============================================================

📊 Dashboard: http://127.0.0.1:8000/dashboard
💬 Chat: WebSocket enabled (real-time)
🤖 LLM: OpenRouter API (DeepSeek - $0.14/1M tokens)
📦 Features:
   ✅ Real-time chat with LLM
   ✅ Task queue (SQLite)
   ✅ WebSocket support
   ✅ API endpoints
   ⚠️  No cognitive plugins (simplified)
   ⚠️  No Ollama needed

🔑 API Key: sk-or-v1-...

Press Ctrl+C to stop
============================================================
```

### Step 3: Manual Chat Test (Before Playwright)

```bash
# Open browser manually
chromium http://127.0.0.1:8000/dashboard
```

**Test chat:**
1. Click "Chat" tab
2. Type: "Hello, what can you do?"
3. Wait for LLM response (3-5 seconds)
4. Verify: Should see intelligent response from DeepSeek

**If chat works → Proceed to automated tests**  
**If chat fails → Check API key, check logs**

### Step 4: Run Playwright Tests

```bash
# Terminal 2: Run E2E tests
pytest tests/e2e/test_dashboard.py -v --html=test_report_hybrid.html --self-contained-html

# Or with visible browser:
pytest tests/e2e/test_dashboard.py -v --headed --slowmo=500
```

**Expected:**
- ✅ Page loads
- ✅ Chat tab works
- ✅ WebSocket connects
- ✅ LLM responds to messages
- ✅ Tasks appear in queue
- ⚠️ Hypotheses/Benchmarks empty (no cognitive plugins)

### Step 5: Chat Interaction Test

Create new test file: `tests/e2e/test_chat_interaction.py`

```python
"""
E2E Chat Interaction Test

Tests real-time chat with OpenRouter LLM.
"""

import pytest
from playwright.sync_api import Page, expect
import time


def test_chat_sends_message(page: Page):
    """Test sending message to chat."""
    page.goto("http://localhost:8000/dashboard")
    
    # Switch to Chat tab
    page.click("button:has-text('Chat')")
    
    # Type message
    page.fill("#chatInput", "Hello SOPHIA, what is 2+2?")
    
    # Send message
    page.click("button:has-text('Send')")
    
    # Wait for response (LLM takes 3-5 seconds)
    time.sleep(6)
    
    # Check message appeared
    expect(page.locator(".chat-messages")).to_contain_text("Hello SOPHIA")
    
    # Check LLM response (should mention "4")
    expect(page.locator(".chat-messages")).to_contain_text("4", timeout=10000)


def test_chat_multiple_messages(page: Page):
    """Test multiple chat exchanges."""
    page.goto("http://localhost:8000/dashboard")
    page.click("button:has-text('Chat')")
    
    messages = [
        "What is your name?",
        "What can you help me with?",
        "Thank you!"
    ]
    
    for msg in messages:
        page.fill("#chatInput", msg)
        page.click("button:has-text('Send')")
        time.sleep(4)  # Wait for LLM
        
        # Verify message appeared
        expect(page.locator(".chat-messages")).to_contain_text(msg)
    
    # Should have at least 6 messages (3 user + 3 bot)
    message_count = page.locator(".chat-message").count()
    assert message_count >= 6, f"Expected >= 6 messages, got {message_count}"


def test_chat_websocket_connection(page: Page):
    """Test WebSocket connection status."""
    page.goto("http://localhost:8000/dashboard")
    page.click("button:has-text('Chat')")
    
    # Wait for connection message
    time.sleep(2)
    
    # Should see "Connected" message
    expect(page.locator(".chat-messages")).to_contain_text("Connected", timeout=5000)
```

Run chat tests:
```bash
pytest tests/e2e/test_chat_interaction.py -v --headed
```

---

## 📊 Test Results Analysis

### What to Check:

**1. Chat Interaction Quality:**
- ✅ LLM responses are relevant?
- ✅ Response time < 10 seconds?
- ✅ No error messages?
- ✅ WebSocket stays connected?

**2. Task Queue:**
- ✅ Tasks appear in Overview tab?
- ✅ Chat messages create tasks?
- ✅ SQLite database created (.data/tasks.sqlite)?

**3. API Endpoints:**
- ✅ /api/tasks returns data?
- ✅ /api/stats shows correct counts?
- ✅ WebSocket /ws/{id} accepts connections?

**4. Frontend:**
- ✅ All tabs work?
- ✅ No JavaScript errors in console?
- ✅ Charts render (even if empty)?

---

## 📝 Deliverables

Create: `docs/DASHBOARD_HYBRID_TEST_REPORT.md`

```markdown
# Dashboard Hybrid Mode Test Report

**Date:** <date>  
**Tester:** Jules  
**Mode:** Hybrid (OpenRouter LLM)  
**API Key:** sk-or-v1-...(last 10 chars)  
**LLM Model:** deepseek/deepseek-chat  
**Cost:** ~$0.001 USD

---

## Summary

- **Total Tests:** <N>
- **Passed:** <N>
- **Failed:** <N>
- **Chat Messages Sent:** <N>
- **LLM Response Time:** <avg> seconds

---

## Chat Interaction Test

### Test 1: Simple Question
**User:** "Hello SOPHIA, what is 2+2?"  
**LLM Response:** "<response>"  
**Response Time:** <seconds>s  
**Quality:** ✅ Good / ⚠️ Slow / ❌ Error

### Test 2: Complex Question
**User:** "What can you help me with?"  
**LLM Response:** "<response>"  
**Response Time:** <seconds>s  
**Quality:** ✅ Good / ⚠️ Slow / ❌ Error

---

## WebSocket Stability

- ✅/❌ Connection established
- ✅/❌ Messages sent successfully
- ✅/❌ Responses received
- ✅/❌ No disconnections during test

---

## API Endpoints

| Endpoint | Status | Response Time | Notes |
|----------|--------|---------------|-------|
| /api/tasks | ✅/❌ | <ms>ms | <notes> |
| /api/stats | ✅/❌ | <ms>ms | <notes> |
| /api/hypotheses | ✅ | <ms>ms | Empty (expected) |
| /api/benchmarks | ✅ | <ms>ms | Empty (expected) |

---

## Cost Analysis

- **LLM API Calls:** <N>
- **Total Tokens:** ~<N> (estimated)
- **Cost:** ~$<amount> USD
- **Model:** deepseek/deepseek-chat ($0.14/1M tokens)

---

## Comparison: Mock vs Hybrid

| Feature | Mock Mode | Hybrid Mode |
|---------|-----------|-------------|
| Chat interaction | ❌ Fake | ✅ Real LLM |
| WebSocket | ❌ No | ✅ Yes |
| Task queue | ❌ Fake data | ✅ Real SQLite |
| API cost | $0 | ~$0.001 |
| Setup time | 2 min | 5 min |
| Test accuracy | 60% | 95% |

---

## Recommendations

**For future testing:**
1. Use Hybrid mode for full E2E tests
2. Use Mock mode for quick frontend-only tests
3. Monitor API costs (set budget limit)
4. Cache LLM responses for repeated tests

**Proposed fixes:**
<list any issues found>
```

---

## 💰 Cost Considerations

**OpenRouter Pricing:**
- Model: `deepseek/deepseek-chat`
- Cost: **$0.14 per 1M tokens**
- Average response: ~300 tokens
- **Cost per test message: ~$0.00004 USD**

**Test run estimate:**
- 20 Playwright tests
- 10 chat messages
- Total: ~3,000 tokens
- **Total cost: ~$0.0004 USD (less than 1 cent!)**

**Free tier:**
- OpenRouter offers $5 free credit
- Enough for **~12,000 test runs**

---

## 🎯 Success Criteria

- [ ] Hybrid server starts successfully
- [ ] OpenRouter API key works
- [ ] Chat sends message and receives response
- [ ] WebSocket connection stable
- [ ] Tasks appear in queue
- [ ] At least 18/20 tests pass (90%+)
- [ ] LLM response quality is good
- [ ] Total cost < $0.01 USD

---

## 🔧 Troubleshooting

**Problem:** "OPENROUTER_API_KEY not set"  
**Solution:** `export OPENROUTER_API_KEY="sk-or-v1-..."`

**Problem:** LLM returns error  
**Solution:** Check API key is valid, check OpenRouter status

**Problem:** Chat messages don't appear  
**Solution:** Check browser console for WebSocket errors

**Problem:** Tests timeout  
**Solution:** Increase LLM wait time (default 10s might be too short)

---

## 📚 Resources

- OpenRouter Dashboard: https://openrouter.ai/activity
- OpenRouter Models: https://openrouter.ai/models
- OpenRouter Docs: https://openrouter.ai/docs

---

**Task Status:** READY (requires OpenRouter API key)  
**Author:** GitHub Copilot  
**Date:** 2025-11-07
