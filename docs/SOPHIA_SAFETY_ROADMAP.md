# SOPHIA Autonomy & Safety Roadmap

**Date:** 2025-11-07  
**Focus:** Bezpečné a spolehlivé self-improvement pro Sophii  
**Priority:** CRITICAL - Foundation before features

---

## 🎯 Hlavní cíl

> "Sophie musí být schopna **bezpečně a spolehlivě** se zdokonalovat a upgradovat **dříve** než testuje dashboard nebo provádí jiné úkoly."

### Současný stav (z AMI_TODO_ROADMAP.md):

**✅ Co funguje:**
- Self-tuning plugin (cognitive_self_tuning.py - 1,437 lines)
- Hypothesis generation (cognitive_reflection.py)
- Sandbox testing environment
- Benchmark system (pytest integration)
- Automatic rollback on failure
- Git commit automation
- GitHub PR creation (Phase 3.5)
- Autonomous restart & validation (Phase 3.7)

**⚠️ CO CHYBÍ - KRITICKÉ MEZERY:**

---

## 🚨 CRITICAL GAPS - Must Fix First

### 1️⃣ **Bezpečnostní validace PŘED deploymentem**

**Problém:**
```python
# cognitive_self_tuning.py současně:
if improvement_pct >= self.improvement_threshold:
    # ✅ Benchmark passed → DEPLOY!
    # ❌ ALE: Žádná validace bezpečnosti!
    # ❌ Co když fix obsahuje:
    #    - Mazání důležitých souborů?
    #    - Nekonečný loop?
    #    - SQL injection?
    #    - API klíče v kódu?
```

**Chybí:**
- ❌ Static code analysis (ruff, mypy, bandit)
- ❌ Security scan (detekce secrets, SQL injection, path traversal)
- ❌ Syntax validation (Python AST parsing)
- ❌ Import validation (dependencies check)
- ❌ Complexity analysis (McCabe, cyclomatic complexity)

**Řešení:** **cognitive_code_validator.py** (NEW)

---

### 2️⃣ **Test coverage validace**

**Problém:**
```python
# Sophie může deployovat kód který:
# ✅ Má benchmark improvement +15%
# ❌ ALE: Nemá ŽÁDNÉ testy!
# ❌ Nebo: Testy neběží (import errors)
# ❌ Nebo: Testy jsou fake (always pass)
```

**Chybí:**
- ❌ Pytest execution PŘED deployment
- ❌ Code coverage measurement (pytest-cov)
- ❌ Test quality validation (assertions check)
- ❌ Integration test execution

**Řešení:** Extend **cognitive_self_tuning.py** s test validation

---

### 3️⃣ **Rollback testing**

**Problém:**
```python
# Sophie má rollback mechanismus, ALE:
# ❌ Nikdy netestujeme že rollback FUNGUJE!
# ❌ Co když backup je corrupted?
# ❌ Co když restore selže?
```

**Chybí:**
- ❌ Periodic rollback drills (měsíční test)
- ❌ Backup integrity validation (hash check)
- ❌ Restore simulation (v sandboxu)

**Řešení:** **cognitive_reliability_monitor.py** (NEW)

---

### 4️⃣ **Hypothesis kvalita**

**Problém:**
```python
# cognitive_reflection.py generuje hypotheses, ALE:
# ❌ Žádná validace že hypothesis je IMPLEMENTOVATELNÁ
# ❌ Může vygenerovat: "Přepiš kernel do Rust" 
# ❌ Může vygenerovat: "Použij GPT-5" (neexistuje)
```

**Chybí:**
- ❌ Feasibility analysis (je to vůbec možné?)
- ❌ Scope validation (není to moc velké?)
- ❌ Dependencies check (máme potřebné tools?)
- ❌ Risk assessment (high/medium/low risk?)

**Řešení:** Extend **cognitive_reflection.py** s hypothesis validation

---

### 5️⃣ **Production monitoring**

**Problém:**
```python
# Po deployment:
# ✅ Git commit created
# ✅ Hypothesis status = "deployed_awaiting_validation"
# ❌ ALE: Jak Sophie zjistí že deployment OPRAVDU funguje v produkci?
# ❌ Žádný monitoring degradace performance
# ❌ Žádný monitoring error rate
```

**Chybí:**
- ❌ Post-deployment monitoring (7 dní)
- ❌ Performance regression detection
- ❌ Error rate tracking
- ❌ Automatic rollback on production issues

**Řešení:** **cognitive_deployment_monitor.py** (NEW)

---

### 6️⃣ **Human approval pro kritické změny**

**Problém:**
```python
# Sophie může deployovat COKOLIV pokud benchmark +10%, INCLUDING:
# - Změna kernelu (core/kernel.py)
# - Změna event systému (core/events.py)
# - Změna databáze (core/memory_sqlite.py)
# - Změna security (authentication, API keys)
```

**Chybí:**
- ❌ Whitelist/blacklist critical files
- ❌ Human approval workflow pro critical changes
- ❌ Deployment permissions system
- ❌ Change categorization (safe/risky/critical)

**Řešení:** **Safety config** + approval workflow

---

### 7️⃣ **Observability & Auditability**

**Problém:**
```python
# Po deployment:
# ❌ Těžké zjistit CO přesně Sophie změnila
# ❌ Těžké zjistit PROČ to změnila
# ❌ Těžké zjistit JAK to testovala
# ❌ Žádný audit trail
```

**Chybí:**
- ❌ Detailed deployment logs
- ❌ Hypothesis decision trail (WHY approved/rejected)
- ❌ Benchmark result archival
- ❌ Change impact analysis
- ❌ Dashboard deployment view

**Řešení:** Enhanced logging + Dashboard deployment tab

---

## 📋 PRIORITY ROADMAP - Security First

### **PHASE A: Safety Foundation** 🔴 CRITICAL

**Timeline:** 1-2 days  
**Goal:** Prevent Sophie from breaking production

#### A.1: Code Validator Plugin ⚠️ HIGHEST PRIORITY
**File:** `plugins/cognitive_code_validator.py` (NEW - ~400 lines)

**Features:**
```python
class CognitiveCodeValidator:
    def validate_code_change(self, file_path, new_code):
        """Multi-layer validation before deployment."""
        
        # Layer 1: Syntax validation
        try:
            ast.parse(new_code)
        except SyntaxError:
            return {"valid": False, "reason": "Syntax error"}
        
        # Layer 2: Security scan
        issues = self._security_scan(new_code)
        if issues["high_risk"]:
            return {"valid": False, "reason": f"Security: {issues}"}
        
        # Layer 3: Import validation
        missing = self._check_imports(new_code)
        if missing:
            return {"valid": False, "reason": f"Missing deps: {missing}"}
        
        # Layer 4: Complexity check
        complexity = self._check_complexity(new_code)
        if complexity > 15:  # McCabe threshold
            return {"valid": False, "reason": "Too complex"}
        
        # Layer 5: Critical file check
        if self._is_critical_file(file_path):
            return {"valid": False, "reason": "Requires human approval"}
        
        return {"valid": True}
```

**Integration:**
```python
# cognitive_self_tuning.py - BEFORE deployment:
validator = all_plugins.get("cognitive_code_validator")
validation = validator.validate_code_change(target_file, new_code)

if not validation["valid"]:
    self.logger.error(f"❌ Validation failed: {validation['reason']}")
    self._update_hypothesis_status(hyp_id, "rejected", validation["reason"])
    return
```

**Security checks:**
- ✅ Syntax validation (AST parsing)
- ✅ Import validation (all dependencies available)
- ✅ Secret detection (API keys, passwords in code)
- ✅ SQL injection patterns
- ✅ Path traversal detection
- ✅ Command injection patterns
- ✅ Complexity analysis (McCabe)
- ✅ Critical file protection

---

#### A.2: Test Coverage Enforcement
**File:** `plugins/cognitive_self_tuning.py` (MODIFY)

**Add before deployment:**
```python
def _run_test_suite(self, target_file: Path) -> Dict[str, Any]:
    """Run pytest with coverage for changed file."""
    
    # Find test file
    test_file = self._find_test_file(target_file)
    if not test_file:
        return {"passed": False, "reason": "No test file found"}
    
    # Run pytest with coverage
    result = subprocess.run(
        [
            "pytest",
            str(test_file),
            f"--cov={target_file.stem}",
            "--cov-report=json",
            "--json-report",
        ],
        capture_output=True,
        timeout=60
    )
    
    # Parse results
    if result.returncode != 0:
        return {"passed": False, "reason": "Tests failed"}
    
    # Check coverage
    coverage_data = json.loads(Path(".coverage.json").read_text())
    coverage_pct = coverage_data["totals"]["percent_covered"]
    
    if coverage_pct < 80:
        return {"passed": False, "reason": f"Coverage too low: {coverage_pct}%"}
    
    return {"passed": True, "coverage": coverage_pct}
```

**Threshold:**
- Minimum 80% coverage pro nové změny
- All tests must pass
- No test timeouts

---

#### A.3: Critical File Protection
**File:** `config/autonomy.yaml` (MODIFY)

**Add safety config:**
```yaml
self_tuning:
  # Existing config...
  
  safety:
    # Files that REQUIRE human approval
    critical_files:
      - "core/kernel.py"
      - "core/event_bus.py"
      - "core/event_loop.py"
      - "core/memory_sqlite.py"
      - "config/autonomy.yaml"
      - "guardian.py"
      - "run.py"
    
    # Files that are FORBIDDEN from auto-deployment
    forbidden_files:
      - ".env"
      - "*.key"
      - "*.pem"
      - "*.crt"
    
    # Maximum allowed complexity (McCabe)
    max_complexity: 15
    
    # Minimum test coverage for deployment
    min_test_coverage: 80
    
    # Deployment approval workflow
    require_approval_for:
      - risk_level: "high"
      - file_category: "critical"
      - complexity: ">15"
      - coverage: "<80%"
```

---

### **PHASE B: Reliability Monitoring** 🟡 HIGH PRIORITY

**Timeline:** 1 day  
**Goal:** Detect issues AFTER deployment

#### B.1: Deployment Monitor Plugin
**File:** `plugins/cognitive_deployment_monitor.py` (NEW - ~300 lines)

**Features:**
```python
class CognitiveDeploymentMonitor:
    def monitor_deployment(self, hypothesis_id: str, deployment_time: datetime):
        """Monitor deployment for 7 days, auto-rollback on issues."""
        
        # Collect baseline metrics (before deployment)
        baseline = {
            "error_rate": self._get_error_rate(days=7),
            "avg_latency": self._get_avg_latency(days=7),
            "task_success_rate": self._get_task_success_rate(days=7)
        }
        
        # Monitor for 7 days
        for day in range(7):
            await asyncio.sleep(86400)  # 24 hours
            
            current = {
                "error_rate": self._get_error_rate(days=1),
                "avg_latency": self._get_avg_latency(days=1),
                "task_success_rate": self._get_task_success_rate(days=1)
            }
            
            # Check for regression
            if current["error_rate"] > baseline["error_rate"] * 1.5:
                self.logger.error(f"🚨 Error rate increased 50%!")
                await self._trigger_rollback(hypothesis_id, "error_rate_spike")
                return
            
            if current["task_success_rate"] < baseline["task_success_rate"] * 0.9:
                self.logger.error(f"🚨 Task success rate dropped 10%!")
                await self._trigger_rollback(hypothesis_id, "success_rate_drop")
                return
        
        # All good → mark as validated
        self._update_hypothesis_status(hypothesis_id, "deployed_validated")
```

**Metrics tracked:**
- Error rate (from logs)
- Task success rate (from task queue)
- Average latency (from benchmarks)
- Memory usage (from system)
- CPU usage (from system)

---

#### B.2: Rollback Testing
**File:** `plugins/cognitive_reliability_monitor.py` (NEW - ~200 lines)

**Monthly rollback drill:**
```python
async def monthly_rollback_drill(self):
    """Test rollback mechanism monthly."""
    
    # 1. Create fake hypothesis
    # 2. Deploy fake change to sandbox
    # 3. Trigger rollback
    # 4. Verify restore worked
    # 5. Report results
    
    if not rollback_successful:
        self.logger.error("🚨 ROLLBACK MECHANISM BROKEN!")
        self.event_bus.publish(Event(
            EventType.CRITICAL_FAILURE,
            data={"issue": "rollback_drill_failed"}
        ))
```

---

### **PHASE C: Observability** 🟢 MEDIUM PRIORITY

**Timeline:** 1 day  
**Goal:** Sophie i člověk rozumí deploymentům

#### C.1: Deployment Dashboard Tab
**File:** `frontend/dashboard.html` (MODIFY)

**Add tab:**
```html
<button class="tab" onclick="showTab('deployments')">Deployments</button>

<div id="deployments" class="tab-content">
  <table>
    <tr>
      <th>Date</th>
      <th>Hypothesis</th>
      <th>File</th>
      <th>Status</th>
      <th>Improvement</th>
      <th>Actions</th>
    </tr>
    <!-- Populated via /api/deployments -->
  </table>
</div>
```

**API endpoint:**
```python
@app.get("/api/deployments")
async def get_deployments():
    # Query hypotheses with status = deployed_*
    # Return deployment history
```

---

#### C.2: Enhanced Logging
**File:** `plugins/cognitive_self_tuning.py` (MODIFY)

**Add detailed logs:**
```python
# Before deployment
self.logger.info(f"📦 DEPLOYMENT PLAN:")
self.logger.info(f"   Hypothesis: {hypothesis['hypothesis']}")
self.logger.info(f"   File: {target_file}")
self.logger.info(f"   Improvement: +{improvement_pct}%")
self.logger.info(f"   Validation: {validation}")
self.logger.info(f"   Tests: {test_results}")
self.logger.info(f"   Risk: {risk_level}")

# After deployment
self.logger.info(f"✅ DEPLOYED:")
self.logger.info(f"   Commit: {commit_sha}")
self.logger.info(f"   Backup: {backup_file}")
self.logger.info(f"   Monitoring: 7 days")
```

---

## 🎯 Implementation Priority

### Week 1: Safety Foundation (MUST HAVE)
1. **Day 1-2:** cognitive_code_validator.py
   - Security scanning
   - Critical file protection
   - Syntax validation
   
2. **Day 3:** Test coverage enforcement
   - Pytest integration
   - 80% coverage requirement
   
3. **Day 4:** Safety config
   - autonomy.yaml updates
   - Critical files whitelist

### Week 2: Reliability (SHOULD HAVE)
4. **Day 5-6:** cognitive_deployment_monitor.py
   - Post-deployment monitoring
   - Auto-rollback on issues
   
5. **Day 7:** Rollback testing
   - Monthly drill automation

### Week 3: Observability (NICE TO HAVE)
6. **Day 8:** Dashboard deployment tab
7. **Day 9:** Enhanced logging

---

## ✅ Success Criteria

**Sophie je SAFE když:**
- ✅ Žádný deployment bez security validation
- ✅ Žádný deployment bez test coverage ≥80%
- ✅ Kritické soubory vyžadují human approval
- ✅ Post-deployment monitoring 7 dní
- ✅ Automatic rollback on production issues
- ✅ Monthly rollback drill passes
- ✅ Full audit trail v dashboard

**Sophie je RELIABLE když:**
- ✅ Zero production breakages v posledních 30 dnech
- ✅ Zero failed rollbacks v posledních 90 dnech
- ✅ 100% test pass rate před deploymentem
- ✅ <5% rollback rate (95%+ successful deployments)

---

## 📚 Testing Strategy

**Before enabling auto-deployment:**
1. **Unit tests** pro všechny nové pluginy
2. **Integration test** pro deployment workflow
3. **Chaos test** - záměrně špatné hypotheses
4. **Rollback test** - ověření že rollback funguje
5. **Security test** - pokus o deployment dangerous code

**Continuous testing:**
- Daily: Rollback mechanism health check
- Weekly: Full deployment workflow test
- Monthly: Rollback drill

---

**Status:** DRAFT - Waiting for approval  
**Author:** GitHub Copilot  
**Date:** 2025-11-07
