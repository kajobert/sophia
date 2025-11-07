# Dashboard Completion Plan

**Status:** Dashboard běží na http://127.0.0.1:8000  
**Date:** 2025-11-07

---

## ✅ Co UŽ FUNGUJE

### 1. Overview Tab
- ✅ Task queue statistics (pending/done/failed counts)
- ✅ Budget tracking (monthly/daily with progress bars)
- ✅ Hypotheses summary (total, pending, success rate)
- ✅ Upgrade status (current status, rollback count)
- ✅ Auto-refresh každých 5s

### 2. Chat Tab
- ✅ WebSocket live communication
- ✅ Real-time chat with Sophia
- ✅ Message history
- ✅ Session management

### 3. Tasks Tab
- ✅ Task list (last 20)
- ✅ Columns: ID, Status, Priority, Instruction, Created At
- ✅ Status badges with colors
- ✅ API endpoint `/api/tasks` works

### 4. Hypotheses Tab
- ✅ Hypotheses list
- ✅ Status, Category, Improvement %, Test Results
- ✅ API endpoint `/api/hypotheses` works

### 5. Benchmarks Tab
- ✅ Model benchmarks display
- ✅ Chart.js integration for visualization
- ✅ API endpoint `/api/benchmarks` ready

### 6. Logs Tab
- ✅ Live log streaming
- ✅ Level filtering (INFO/WARNING/ERROR/DEBUG)
- ✅ Color-coded log levels
- ✅ Auto-scroll

---

## 🚧 Co CHYBÍ - Priority Tasks

### HIGH PRIORITY: Deployments Tab (Human Oversight)

**Proč je to kritické:**
- Bez tohoto tabu **lidé nevidí** co Sophie autonomně mění
- Nutné pro trust & transparency
- Safety requirement před production use

**Co zobrazit:**
```
┌─────────────────────────────────────────────────────────────┐
│ 🚀 Deployments History                                       │
├──────────┬──────────────────┬──────────┬────────┬───────────┤
│ Date     │ Hypothesis       │ File     │ Status │ Impact    │
├──────────┼──────────────────┼──────────┼────────┼───────────┤
│ 11-07    │ "Fix JSON pars." │ kernel.py│ ✅ OK  │ +12% perf │
│ 11-06    │ "Add cache"      │ llm.py   │ ⚠️ Test│ +5% perf  │
│ 11-05    │ "Optimize loop"  │ event.py │ 🔄 Roll│ -2% perf  │
└──────────┴──────────────────┴──────────┴────────┴───────────┘

[View Details] [Rollback] [Git Diff]
```

**Implementation:**

1. **API Endpoint:**
```python
# plugins/interface_webui.py - ADD:

@self.app.get("/api/deployments")
async def api_deployments(limit: int = 20):
    """Get deployment history from hypotheses with status deployed_*"""
    db_path = Path(".data") / "memory.db"
    if not db_path.exists():
        return {"error": "memory DB not found", "deployments": []}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        # Get deployed hypotheses
        cur.execute("""
            SELECT 
                id, 
                hypothesis, 
                category, 
                status, 
                improvement_pct,
                target_file,
                created_at,
                deployed_at,
                git_commit_sha
            FROM hypotheses 
            WHERE status LIKE 'deployed_%'
            ORDER BY deployed_at DESC 
            LIMIT ?
        """, (limit,))
        
        rows = cur.fetchall()
        deployments = []
        
        for r in rows:
            hid, hyp, cat, status, improvement, file, created, deployed, commit = r
            
            # Status emoji
            status_emoji = {
                "deployed_validated": "✅",
                "deployed_awaiting_validation": "🔄",
                "deployed_rollback": "⚠️"
            }.get(status, "❓")
            
            deployments.append({
                "id": hid,
                "hypothesis": hyp,
                "category": cat,
                "status": status,
                "status_display": f"{status_emoji} {status.replace('deployed_', '')}",
                "improvement": f"+{improvement}%" if improvement else "N/A",
                "file": file or "unknown",
                "deployed_at": deployed,
                "git_commit": commit[:8] if commit else "N/A"
            })
        
        conn.close()
        return {"deployments": deployments, "total": len(deployments)}
    except Exception as e:
        logger.error(f"Error fetching deployments: {e}")
        return {"error": str(e), "deployments": []}
```

2. **Frontend Tab:**
```html
<!-- frontend/dashboard.html - ADD after Hypotheses tab -->

<button class="tab" onclick="showTab('deployments')">🚀 Deployments</button>

<!-- Tab content -->
<div id="deployments" class="tab-content">
  <div class="card">
    <h2>🚀 Autonomous Deployments</h2>
    <p style="color: #94a3b8; margin-bottom: 20px;">
      Track what Sophie has changed autonomously. All changes are validated, benchmarked, and can be rolled back.
    </p>
    
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Hypothesis</th>
          <th>Category</th>
          <th>File</th>
          <th>Status</th>
          <th>Impact</th>
          <th>Commit</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody id="deploymentsTableBody">
        <tr>
          <td colspan="8" style="text-align: center; color: #64748b;">
            Loading deployments...
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</div>

<!-- JavaScript to fetch deployments -->
<script>
async function fetchDeployments() {
  try {
    const res = await fetch('/api/deployments?limit=20');
    const data = await res.json();
    
    const tbody = document.getElementById('deploymentsTableBody');
    
    if (data.error) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: #f87171;">
            Error: ${data.error}
          </td>
        </tr>
      `;
      return;
    }
    
    const deployments = data.deployments || [];
    
    if (deployments.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="8" style="text-align: center; color: #64748b;">
            No deployments yet
          </td>
        </tr>
      `;
      return;
    }
    
    tbody.innerHTML = deployments.map(d => `
      <tr>
        <td style="color: #64748b; font-size: 12px;">
          ${d.deployed_at ? new Date(d.deployed_at).toLocaleDateString() : 'N/A'}
        </td>
        <td style="max-width: 300px;">
          <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" 
               title="${d.hypothesis}">
            ${d.hypothesis}
          </div>
        </td>
        <td><code>${d.category}</code></td>
        <td><code style="color: #60a5fa;">${d.file}</code></td>
        <td>${d.status_display}</td>
        <td style="color: #34d399; font-weight: 600;">${d.improvement}</td>
        <td><code style="font-size: 11px;">${d.git_commit}</code></td>
        <td>
          <button onclick="viewDeployment(${d.id})" 
                  style="padding: 4px 8px; font-size: 12px;">
            Details
          </button>
        </td>
      </tr>
    `).join('');
    
  } catch (err) {
    console.error('Failed to fetch deployments:', err);
  }
}

// Call on page load and every 10s
if (document.getElementById('deploymentsTableBody')) {
  fetchDeployments();
  setInterval(fetchDeployments, 10000);
}

function viewDeployment(id) {
  // TODO: Open modal with full deployment details
  alert(`Deployment #${id} details - coming soon!`);
}
</script>
```

---

## MEDIUM PRIORITY: Enhanced Overview Cards

**Current:** Basic stats  
**Needed:** More actionable insights

### Add Cards:
1. **System Health**
   - Uptime
   - Errors in last hour
   - Memory usage
   - Task queue backlog

2. **Learning Progress**
   - Hypotheses generated this week
   - Success rate trend (7d/30d)
   - Top improvement categories

3. **Budget Efficiency**
   - Cost per task
   - LLM usage breakdown (local vs cloud)
   - Most expensive operations

---

## LOW PRIORITY: Nice-to-Have Features

### 1. Real-time Notifications
```javascript
// WebSocket notifications for critical events
ws.onmessage = (event) => {
  const notification = JSON.parse(event.data);
  if (notification.type === 'deployment_completed') {
    showToast(`✅ Deployment: ${notification.hypothesis}`, 'success');
  }
  if (notification.type === 'rollback_triggered') {
    showToast(`⚠️ Rollback: ${notification.reason}`, 'warning');
  }
}
```

### 2. Interactive Charts
- Task completion rate over time
- Budget spending trends
- Hypothesis success rate timeline

### 3. Search & Filtering
- Search tasks by instruction
- Filter hypotheses by category
- Date range selection

### 4. Export Functionality
- Export logs to CSV
- Download deployment report
- Generate audit trail PDF

---

## Implementation Order

**Week 1 (NOW):**
1. ✅ Fix dashboard root endpoint (DONE - uses dashboard.html)
2. ✅ Verify all existing tabs work (DONE - verified)
3. 🔄 Add Deployments tab (IN PROGRESS)

**Week 2:**
4. Enhanced overview cards (system health)
5. Real-time notifications

**Week 3:**
6. Interactive charts
7. Search & filtering

---

## Testing Checklist

Before marking dashboard as COMPLETE:

- [ ] All tabs load without errors
- [ ] API endpoints return valid JSON
- [ ] WebSocket connections stable
- [ ] Auto-refresh works (overview, logs)
- [ ] Deployments tab shows real data
- [ ] Mobile responsive (basic)
- [ ] Works in Chrome/Firefox
- [ ] No console errors
- [ ] Performance acceptable (<2s page load)

---

**Status:** Ready to implement Deployments tab  
**ETA:** 30 minutes for API + frontend  
**Blocker:** None - all dependencies installed
