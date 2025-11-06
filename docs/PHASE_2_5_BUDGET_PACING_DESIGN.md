# PHASE 2.5: Budget Intelligence & Pacing System

**Goal:** Prevent Sophia from burning through monthly budget in a few hours, enable strategic budget allocation

**Status:** 🔴 DESIGN PHASE  
**Complexity:** MEDIUM (4-5 hours)  
**Dependencies:** Phase 2.2 (Budget Router v2.0)

---

## 🎯 PROBLEM STATEMENT

**Current Issue:**
- Monthly limit ($30) tracked, but no daily pacing
- Sophia could spend $25 in 2 hours → 28 days offline mode
- No mechanism to request extra budget for urgent/complex tasks
- No user notification when budget burning too fast

**Example Failure Scenario:**
```
Day 1, 9:00 AM: User: "Analyze entire codebase and create comprehensive report"
Day 1, 11:00 AM: Sophia uses GPT-4o for deep analysis → $22 spent
Day 1-30: Forced to use only local LLM (budget exhausted)
```

---

## 💡 SOLUTION: Intelligent Budget Pacing

### **Core Principles:**

1. **Daily Budget Allocation**
   - Monthly limit ÷ Remaining days = Recommended daily limit
   - Recalculate every day (adaptive)
   - 20% safety buffer for end-of-month emergencies

2. **Overspend Detection**
   - Track spend per day
   - Warn if today's spend > 150% of recommended daily limit
   - Temporarily increase local LLM preference

3. **Urgency Request Mechanism**
   - Tasks estimated > 50% of daily budget → request approval
   - Auto-approve small requests (< $2)
   - User notification via dashboard + email
   - 2-hour timeout → fallback to local LLM

4. **Strategic Phases**
   - Week 1-2: Conservative (use more local)
   - Week 3: Balanced (cloud for complex tasks)
   - Week 4: Aggressive (remaining budget available)

---

## 🏗️ ARCHITECTURE

### **1. Enhanced Budget Router**

**File:** `plugins/cognitive_task_router.py` (extend v2.0 → v2.5)

**New Methods:**
```python
async def _calculate_daily_budget_limit(self) -> float:
    """
    Calculate recommended daily budget based on:
    - Remaining budget this month
    - Days left in month
    - Safety buffer (20%)
    
    Returns: float (USD)
    """
    
async def _check_daily_pacing(self, context) -> Tuple[float, float]:
    """
    Check today's spending vs recommended daily limit.
    
    Returns: (today_spent, daily_limit)
    Emits: BUDGET_PACE_WARNING if overspending
    """
    
async def _calculate_phase_strategy(self) -> str:
    """
    Determine which phase of month we're in:
    - "conservative" (days 1-10): 70% local, 30% cloud
    - "balanced" (days 11-20): 50% local, 50% cloud
    - "aggressive" (days 21-end): 30% local, 70% cloud (use remaining budget)
    
    Returns: str phase name
    """
```

**Integration:**
- Called on every `execute()` before routing decision
- Stores daily stats in cache (reset at midnight)
- Emits `BUDGET_PACE_WARNING` when overspending detected

---

### **2. Budget Request Plugin**

**File:** `plugins/cognitive_budget_requester.py` (NEW)

**Purpose:** Handle urgent budget approval requests

**Workflow:**
```
1. Task arrives with high complexity score
2. Estimate cloud LLM cost (using model pricing)
3. If cost > 50% daily budget:
   a. Generate justification (why cloud LLM needed)
   b. Create request in requests table
   c. Emit BUDGET_REQUEST_CREATED event
   d. Send notification to user (email + dashboard)
   e. Wait for approval (max 2 hours)
4. If approved → use cloud LLM
5. If denied/timeout → use local LLM + log compromise
```

**Database Schema:**
```sql
CREATE TABLE budget_requests (
    id INTEGER PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    task_description TEXT,
    estimated_cost FLOAT,
    justification TEXT,
    urgency INTEGER,  -- 1-100 priority
    status TEXT DEFAULT 'pending',  -- pending|approved|denied|timeout
    user_response_at TIMESTAMP,
    cloud_model_requested TEXT
);
```

**Methods:**
```python
async def _create_budget_request(
    task_description: str,
    estimated_cost: float,
    justification: str,
    urgency: int
) -> int:
    """Create request and return request_id"""

async def _wait_for_approval(
    request_id: int,
    timeout: int = 7200
) -> bool:
    """Wait for user approval, return True if approved"""

async def _notify_user(request_id: int):
    """Send email + dashboard notification"""
```

---

### **3. Event Types**

**File:** `core/events.py`

**New Events:**
```python
class EventType(Enum):
    # Budget pacing
    BUDGET_PACE_WARNING = "budget_pace_warning"
    BUDGET_PHASE_CHANGED = "budget_phase_changed"  # conservative → balanced
    
    # Budget requests
    BUDGET_REQUEST_CREATED = "budget_request_created"
    BUDGET_REQUEST_APPROVED = "budget_request_approved"
    BUDGET_REQUEST_DENIED = "budget_request_denied"
    BUDGET_REQUEST_TIMEOUT = "budget_request_timeout"
    
    # Task complexity
    TASK_COMPLEXITY_HIGH = "task_complexity_high"  # Trigger budget check
```

---

### **4. Configuration**

**File:** `config/autonomy.yaml`

```yaml
budget:
  monthly_limit_usd: 30.0
  
  # Daily pacing settings
  pacing:
    enabled: true
    safety_buffer_pct: 20  # Reserve 20% for emergencies
    overspend_threshold: 1.5  # Warn at 150% of daily limit
    
    # Phase strategies (days of month)
    phases:
      conservative:
        days: [1, 10]
        local_pct: 70
        cloud_pct: 30
      balanced:
        days: [11, 20]
        local_pct: 50
        cloud_pct: 50
      aggressive:
        days: [21, 31]
        local_pct: 30
        cloud_pct: 70
  
  # Urgent request settings
  urgent_requests:
    enabled: true
    auto_approve_under_usd: 2.0
    notification_email: "robert@example.com"
    notification_dashboard: true
    timeout_seconds: 7200  # 2 hours
    
  # Model pricing (for cost estimation)
  pricing:
    "anthropic/claude-3.5-sonnet": 0.003  # per 1K tokens (avg input+output)
    "openai/gpt-4o": 0.0025
    "openai/gpt-4o-mini": 0.00015
```

---

### **5. Dashboard Widget**

**File:** `frontend/src/components/BudgetPacing.tsx`

**UI Elements:**
```tsx
<BudgetPacingWidget>
  <DailySpendChart>
    - Bar chart: recommended vs actual daily spend
    - Color coding: green (under limit), yellow (near limit), red (over limit)
  </DailySpendChart>
  
  <MonthlyProjection>
    - Line graph: projected end-of-month spend
    - "On track" / "Over budget" / "Under budget" indicator
  </MonthlyProjection>
  
  <CurrentPhase>
    - Badge: "Conservative" / "Balanced" / "Aggressive"
    - Days remaining in current phase
  </CurrentPhase>
  
  <UrgentRequests>
    - List of pending budget requests
    - Approve/Deny buttons
    - Justification text from Sophia
  </UrgentRequests>
</BudgetPacingWidget>
```

---

## 📊 IMPLEMENTATION PLAN

### **Task 1: Extend Budget Router (2 hours)**
- Add daily budget calculation
- Implement pacing checks
- Phase strategy logic
- Emit BUDGET_PACE_WARNING events

### **Task 2: Budget Request Plugin (2 hours)**
- Create plugin skeleton
- Database schema + methods
- Request workflow (create → notify → wait → approve/deny)
- Email notification integration

### **Task 3: Dashboard Integration (1 hour)**
- BudgetPacing widget component
- API endpoint for requests (GET /api/budget/requests)
- Approve/Deny API (POST /api/budget/requests/:id/approve)

### **Task 4: Testing (1 hour)**
- Simulate daily overspend → verify warning
- Create urgent request → verify notification
- Test phase transitions
- End-to-end approval workflow

**Total Time:** 6 hours

---

## 🧪 TEST SCENARIOS

### **Scenario 1: Normal Daily Pacing**
```
Day 1: $0.80 spent (recommended: $1.00) ✅
Day 2: $0.95 spent (recommended: $0.97) ✅
Day 15: $0.50 spent (recommended: $0.80) ✅
End of month: $28.50 total (under limit) ✅
```

### **Scenario 2: Overspending Detected**
```
Day 5, 10:00 AM: $2.50 spent (recommended: $1.00) ⚠️
→ BUDGET_PACE_WARNING emitted
→ context.prefer_local = True
→ Next 5 tasks routed to local LLM
Day 5, 5:00 PM: $2.80 spent (still over, but slowed down)
Day 6: $0.60 spent (back on track) ✅
```

### **Scenario 3: Urgent Request Approved**
```
Day 10: Complex task arrives (estimated cost: $5.00)
→ Daily limit: $1.20 (task = 417% of daily budget!)
→ BUDGET_REQUEST_CREATED
→ Email sent to user: "Sophia needs approval for $5 task..."
→ User clicks "Approve" in dashboard
→ BUDGET_REQUEST_APPROVED
→ Task executed with GPT-4o ✅
→ Remaining days: local-only mode (budget exhausted)
```

### **Scenario 4: Request Timeout**
```
Day 15: Urgent task arrives
→ Request created, email sent
→ User doesn't respond for 2 hours
→ BUDGET_REQUEST_TIMEOUT
→ Task executed with local LLM (llama3.1:8b)
→ Note logged: "Compromised quality due to budget timeout"
```

---

## 🎯 SUCCESS METRICS

**After Implementation:**
- ✅ Budget distributed evenly across month (±20% variance)
- ✅ No single-day budget exhaustion
- ✅ User notified for high-cost tasks (>50% daily budget)
- ✅ Automatic phase adaptation (conservative → aggressive)
- ✅ Urgent requests handled within 2 hours

**Dashboard Visibility:**
- Daily spend vs recommended (visual chart)
- Monthly projection (on track / over / under)
- Current phase indicator
- Pending approval requests

---

## 🚀 NEXT STEPS

1. ✅ Design complete (this document)
2. 🔲 Update AMI_TODO_ROADMAP.md with Phase 2.5
3. 🔲 Implement Task 1: Enhanced Budget Router
4. 🔲 Implement Task 2: Budget Request Plugin
5. 🔲 Implement Task 3: Dashboard Widget
6. 🔲 Run all test scenarios
7. 🔲 Document in WORKLOG.md

**Ready to implement?** Start with Task 1! 🚀
