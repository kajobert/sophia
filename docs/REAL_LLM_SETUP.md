# 🔧 Real LLM Integration Setup Guide

**Den 11-12:** Integrace s reálným Gemini API

---

## 📋 Prerekvizity

### 1. API Klíč

Potřebuješ získat Gemini API klíč:

1. Jdi na [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Vytvoř nový API klíč
3. Zkopíruj klíč

### 2. Vytvoření .env souboru

```bash
# V kořenovém adresáři projektu
cp .env.example .env
```

Pak edituj `.env` a přidej svůj klíč:

```bash
GEMINI_API_KEY="AIza..."  # Tvůj skutečný klíč
```

### 3. Verifikace Setup

```bash
# Test že klíč funguje
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('GEMINI_API_KEY')
print('✅ API key loaded' if key else '❌ No API key')
"
```

---

## 🧪 Real LLM Testing Strategy

### Fáze 1: Základní Connectivity Test

```python
# tests/test_e2e_real_llm.py

import pytest
from core.llm_manager import LLMManager
from core.config import Config

@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_gemini_basic_connectivity():
    """Test že můžeme volat Gemini API."""
    config = Config()
    llm_manager = LLMManager()
    
    model = llm_manager.get_llm("powerful")
    response, usage = await model.generate_content_async("Say 'Hello'")
    
    assert response is not None
    assert len(response) > 0
    assert usage is not None
    assert "total_tokens" in usage.get("usage", {})
```

### Fáze 2: Planning Generation Test

```python
@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_real_planning_generation():
    """Test real LLM plánování."""
    from core.plan_manager import PlanManager
    from core.llm_manager import LLMManager
    
    llm = LLMManager()
    pm = PlanManager(llm)
    
    # Simple task
    plan = await pm.create_plan(
        mission_goal="List files in sandbox/ directory"
    )
    
    assert len(plan) > 0
    assert all(step.id > 0 for step in plan)
    assert all(step.description for step in plan)
```

### Fáze 3: Full E2E Mission

```python
@pytest.mark.real_llm
@pytest.mark.asyncio
async def test_full_real_mission():
    """Kompletní mise s reálným LLM."""
    from core.nomad_orchestrator_v2 import NomadOrchestratorV2
    
    orch = NomadOrchestratorV2()
    await orch.initialize()
    
    await orch.start_mission(
        mission_goal="Create a file sandbox/hello.txt with content 'Hello from Nomad!'"
    )
    
    # Verify
    assert orch.state_manager.get_state().value == "completed"
    assert os.path.exists("sandbox/hello.txt")
    
    # Cleanup
    await orch.shutdown()
```

---

## 🎯 Running Real LLM Tests

```bash
# Pouze real LLM testy (vyžaduje API klíč)
python -m pytest tests/ -v -m real_llm

# Skip real LLM testy (pro CI/CD)
python -m pytest tests/ -v -m "not real_llm"

# Všechny testy (včetně real LLM)
python -m pytest tests/ -v
```

---

## 💰 Cost Management

**VAROVÁNÍ:** Real LLM volání stojí peníze!

### Estimated Costs (Gemini Pro):

- **Planning:** ~500 tokens input, ~200 tokens output = $0.001
- **Tool Call Generation:** ~300 tokens input, ~100 tokens output = $0.0005
- **Reflection:** ~400 tokens input, ~150 tokens output = $0.0007

**Simple Mission:** ~$0.005 (cca 0.12 Kč)  
**Complex Mission (10 steps):** ~$0.05 (cca 1.20 Kč)

### Budget Protection:

BudgetTracker automaticky zastaví misi při překročení limitu:

```python
budget_tracker = BudgetTracker(
    max_tokens=100000,  # Hard limit
    max_time_seconds=3600  # 1 hour max
)
```

---

## 🔒 Security Best Practices

1. **NIKDY necommituj .env soubor**
   - Je v `.gitignore`
   - Zkontroluj: `git status` by nemělo ukazovat `.env`

2. **Používej environment-specific konfig**
   ```python
   # Development
   GEMINI_API_KEY="development_key"
   
   # Production  
   GEMINI_API_KEY="production_key"
   ```

3. **Rotuj klíče pravidelně**
   - Minimálně každé 3 měsíce
   - Po každém security incidentu okamžitě

---

## 🐛 Troubleshooting

### "API Key not found"

```bash
# Zkontroluj že .env existuje
ls -la .env

# Zkontroluj že python-dotenv je nainstalován
pip list | grep dotenv

# Debug load
python -c "
from dotenv import load_dotenv
import os
load_dotenv(verbose=True)
print(os.getenv('GEMINI_API_KEY'))
"
```

### "Rate limit exceeded"

Gemini má limity:
- **Free tier:** 60 requests/minute
- **Paid tier:** 360 requests/minute

Řešení:
```python
# Implementuj rate limiting
from core.utils import RateLimiter

limiter = RateLimiter(max_requests=50, window_seconds=60)
await limiter.acquire()
response = await model.generate_content_async(prompt)
```

### "Invalid API key"

1. Zkontroluj že klíč začíná `AIza`
2. Zkontroluj že není expirated
3. Vygeneruj nový klíč v AI Studio

---

## 📊 Monitoring Real LLM Usage

```python
# Sleduj statistiky v BudgetTracker
summary = budget_tracker.get_detailed_summary()

print(f"""
Total Tokens: {summary['total_tokens']}
Total Cost: ${summary['total_cost']:.4f}
Avg per Step: {summary['average_cost_per_step']:.4f}
""")
```

---

**Status:** 🔜 Připraveno pro implementaci  
**Next:** Vytvoř `.env` a spusť první real LLM test
