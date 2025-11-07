# Jules Plan Approval - Bezpečnostní Mechanismus

## 🎯 Problém

Sophia spotřebovala **60+ Jules tasků na nesmysl** protože Jules automaticky prováděl plány bez kontroly!

## ✅ Řešení: Schválení plánu před provedením

### Workflow s plan approval:

```
1. Sophia vytvoří Jules session (require_plan_approval=True)
2. Jules analyzuje task a vytvoří PLÁN
3. ⚠️  SOPHIA ZKONTROLUJE PLÁN (get_plan_details)
4. ✅ Sophia schválí plán (approve_plan)
5. Jules provede kroky
6. Sophia zkontroluje výsledky
```

## 🔧 Implementace

### 1. Create Session s plan approval

```python
session = await jules_tool.create_session(
    context=context,
    prompt="Add dark mode support",
    source="sources/github/ShotyCZ/sophia",
    require_plan_approval=True  # DEFAULT je True!
)
```

### 2. Získat plán k review

```python
# Počkat než Jules vygeneruje plán
await asyncio.sleep(5)

# Získat detaily plánu
plan_details = jules_tool.get_plan_details(context, session_id)

if plan_details["has_plan"]:
    plan = plan_details["plan"]
    
    # SOPHIA VIDÍ CO JULES PLÁNUJE:
    print("Jules plánuje:")
    print(plan)  # Strukturovaný plán s kroky, soubory, změnami
```

**Příklad plánu:**
```json
{
  "steps": [
    {
      "action": "edit_file",
      "file": "plugins/interface_webui.py",
      "changes": "Add dark mode CSS toggle"
    },
    {
      "action": "create_file", 
      "file": "static/dark-mode.css",
      "content": "..."
    },
    {
      "action": "run_test",
      "command": "pytest tests/test_webui.py"
    }
  ],
  "files_modified": [
    "plugins/interface_webui.py",
    "static/dark-mode.css"
  ],
  "summary": "Add dark mode toggle to WebUI with CSS switching"
}
```

### 3. Validace plánu (Sophia checks)

```python
# Bezpečnostní kontroly
dangerous_keywords = [
    ".env delete",
    "rm -rf /",
    "DROP TABLE", 
    "DELETE FROM users",
    "git push --force",
    "API_KEY"
]

plan_str = str(plan)

for keyword in dangerous_keywords:
    if keyword in plan_str:
        logger.error(f"❌ DANGEROUS PLAN: Contains '{keyword}'")
        return {"success": False, "error": "Dangerous operation detected"}
```

### 4. Schválení plánu

```python
# Pokud plán vypadá OK, schválit
jules_tool.approve_plan(context, session_id)
logger.info("✅ Plan approved! Jules will now execute.")
```

### 5. Monitoring execution

```python
# Po schválení Jules začne pracovat
result = await jules_monitor.monitor_until_completion(
    context,
    session_id=session_id,
    check_interval=30
)
```

## 🛡️ Bezpečnostní Features

### Automatické kontroly v `cognitive_jules_autonomy`:

1. **Dangerous keywords detection:**
   - `.env delete`
   - `rm -rf`
   - `DROP TABLE`
   - `DELETE FROM users`

2. **Plan structure validation:**
   - Má plán `steps`?
   - Má plán `files_modified`?
   - Je `summary` srozumitelný?

3. **Timeout protection:**
   - Max 5s čekání na plán
   - Pokud Jules nevygeneruje plán → FAIL

### Příklad bezpečnostního logu:

```
📋 STEP 1.5: Getting Jules plan for review...
📋 Jules Plan:
   {
     "steps": [...],
     "files_modified": ["plugins/benchmark_runner.py"],
     "summary": "Fix benchmark runner offline mode"
   }
✅ Plan looks safe, approving...
✅ Plan approved! Jules will now execute.
👁️  STEP 2: Monitoring session abc123 until completion...
```

## 🚫 Co se stane když plán je nebezpečný:

```python
plan = {
    "steps": [
        {"action": "run", "command": "rm -rf .env"}  # DANGEROUS!
    ]
}

# Sophia detekuje:
❌ Plan contains dangerous operation: rm -rf .env
❌ Session REJECTED, Jules will NOT execute
```

## 📊 API Reference

### `get_plan_details(context, session_id)`

**Returns:**
```python
{
    "has_plan": True,
    "plan": {
        "steps": [...],          # Kroky k provedení
        "files": [...],          # Soubory ke změně
        "summary": "..."         # Lidsky čitelný popis
    },
    "activity_id": "activities/xyz"  # Pro debugging
}
```

### `approve_plan(context, session_id)`

**Returns:**
```python
{
    "approved": True
}
```

**Side effect:**
- Jules začne provádět schválený plán
- Session state → EXECUTING

## 🔄 Kompletní Example

```python
# 1. Create session s plan approval
session = await jules_tool.create_session(
    context=context,
    prompt="Fix typo in README.md line 42",
    source="sources/github/ShotyCZ/sophia",
    require_plan_approval=True  # MUST approve first!
)
session_id = session.name.split("/")[1]

# 2. Wait for plan generation
await asyncio.sleep(5)

# 3. Get plan
plan = jules_tool.get_plan_details(context, session_id)

# 4. Review plan
if plan["has_plan"]:
    print("Jules wants to:")
    for step in plan["plan"]["steps"]:
        print(f"  - {step}")
    
    # 5. Approve if OK
    if looks_good(plan):
        jules_tool.approve_plan(context, session_id)
        print("✅ Approved!")
    else:
        print("❌ Rejected!")
        return
else:
    print("❌ No plan generated!")
    return

# 6. Monitor execution
result = await monitor_until_completion(context, session_id)
print(f"Result: {result['status']}")
```

## 🎓 Best Practices

### ✅ DO:
- Vždy nastavit `require_plan_approval=True` (je to default)
- Vždy zkontrolovat `get_plan_details()` před `approve_plan()`
- Logovat plán do logů pro audit trail
- Testovat dangerous keywords
- Validovat že plán má smysl

### ❌ DON'T:
- Nikdy neschvalovat plán naslepo
- Nikdy neschvalovat plán s `rm -rf`
- Nikdy neignorovat chybějící `has_plan`
- Nikdy nepoužívat `require_plan_approval=False` (nebezpečné!)

## 📝 Default Configuration

V `cognitive_jules_autonomy.py`:

```python
# BEZPEČNÉ DEFAULTY:
jules_session = await self.jules_api_tool.create_session(
    context=context,
    prompt=jules_prompt,
    source=source,
    branch="main",
    auto_pr=False,               # ✅ No auto PR
    require_plan_approval=True,  # ✅ MUST approve (DEFAULT)
)
```

## 🔍 Debugging

### Pokud plán není vygenerován:

```bash
# Check session activities
curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID/activities' \
  -H 'X-Goog-Api-Key: YOUR_KEY'
```

### Pokud approval selhává:

```bash
# Manual approve via API
curl 'https://jules.googleapis.com/v1alpha/sessions/SESSION_ID:approvePlan' \
  -X POST \
  -H 'X-Goog-Api-Key: YOUR_KEY'
```

---

**TL;DR:** Jules teď NEMŮŽE automaticky provádět změny. Sophia MUSÍ zkontrolovat a schválit každý plán! 🛡️
