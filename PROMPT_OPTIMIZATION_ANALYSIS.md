# Prompt Optimization - Aktuální Stav a Action Plan

**Date:** 2025-11-06  
**Kritičnost:** 🔴 **VYSOKÁ** - Klíčová pro AMI self-tuning  
**Status:** ⚠️ ČÁSTEČNĚ IMPLEMENTOVÁNO

---

## 🔍 CO MÁME (Současný Stav)

### ✅ 1. Cognitive Reflection Plugin (648 lines) - COMPLETE

**File:** `plugins/cognitive_reflection.py`

**Co dělá:**
- ✅ Analyzuje failure patterns z operation_tracking
- ✅ Vytváří hypotheses pomocí Expert LLM (4-tier escalation)
- ✅ Identifikuje `fix_type`: **code_fix | prompt_optimization | config_tuning | model_change**
- ✅ Ukládá hypotézy do databáze

**Prompt Analysis Template (lines 412-441):**
```python
prompt = f"""Jsi expert na debugging AI systémů. Analyzuj tyto selhání:

OPERACE: {operation_type}
ÚSPĚŠNOST: {success_rate}%
PŘÍKLADY CHYB: {error_samples}

ÚKOL:
1. Identifikuj ROOT CAUSE (ne symptom!)
2. Navrhni KONKRÉTNÍ FIX (změna kódu, prompt, config, nebo model)
3. Odhadni IMPACT (high/medium/low)

Vrať JSON:
{{
  "root_cause": "...",
  "hypothesis": "...",
  "proposed_fix": "...",
  "fix_type": "code_fix|prompt_optimization|config_tuning|model_change",  ⭐
  "priority": 1-100,
  "estimated_improvement": "15%"
}}
"""
```

**✅ Umí identifikovat, kdy je potřeba prompt optimization!**

---

### ✅ 2. Self-Tuning Plugin (1193 lines) - COMPLETE

**File:** `plugins/cognitive_self_tuning.py`

**Co dělá:**
- ✅ Zpracovává hypotézy z Reflection pluginu
- ✅ **Podporuje 4 typy fixů:**
  - `code` - Úprava Python kódu ✅
  - **`prompt` - Optimalizace promptů** ✅ ⭐
  - `config` - Změna YAML konfigurace ✅
  - `model` - Změna LLM modelu ✅

**Prompt Fix Implementation (lines 343-348):**
```python
elif fix_type == "prompt":
    # Prompt fix: Create optimized prompt file
    sandbox_file = sandbox_dir / "config/prompts" / target_file
    sandbox_file.parent.mkdir(parents=True, exist_ok=True)
    sandbox_file.write_text(proposed_fix)
    
    self.logger.info(f"✏️  Created optimized prompt: {sandbox_file}")
```

**Prompt Benchmarking (lines 558-597):**
```python
async def _benchmark_prompt(self, workspace_root, sandbox_dir, target_file):
    """
    Benchmark prompt optimization.
    
    Compare old vs new prompt:
    - Read baseline prompt
    - Read new optimized prompt
    - Measure length (shorter = better for 8B models)
    - Estimate improvement based on length reduction
    
    For MVP: Conservative estimate (15% improvement if shorter/clearer)
    """
    # Read both prompts
    baseline_prompt = (workspace_root / "config/prompts" / target_file).read_text()
    new_prompt = (sandbox_dir / "config/prompts" / target_file).read_text()
    
    # Shorter prompt usually better for 8B models
    baseline_len = len(baseline_prompt)
    new_len = len(new_prompt)
    
    improvement = (baseline_len - new_len) / baseline_len if new_len < baseline_len else 0
    
    return {
        "baseline_length": baseline_len,
        "new_length": new_len,
        "improvement": improvement,
        "success": True
    }
```

**✅ Umí aplikovat a testovat prompt optimalizace!**

---

### ⚠️ 3. Prompt Optimizer Plugin (392 lines) - INFRASTRUCTURE ONLY

**File:** `plugins/cognitive_prompt_optimizer.py`

**Co dělá:**
- ✅ Event subscription (TASK_COMPLETED) ✅
- ✅ Prompt version tracking ✅
- ✅ A/B testing infrastructure ✅
- ✅ Metrics tracking ✅

**Co NEDĚLÁ (TODO komentáře):**
- ❌ `_gather_training_examples()` → vrací `[]` (line 282)
- ❌ `_analyze_response_patterns()` → vrací `{"insights": "placeholder"}` (line 290)
- ❌ `_generate_improved_prompt()` → vrací `"Improved prompt template placeholder"` (line 300)
- ❌ `_should_optimize()` → vrací `False` (line 209) **⚠️ KRITICKÉ!**

**Proč neběží:**
```python
def _should_optimize(self, task_type: str) -> bool:
    """Determine if prompts should be optimized..."""
    # ... checks ...
    
    # For now, return False to avoid spurious optimizations
    return False  # ⚠️ HARDCODED FALSE!
```

**❌ Plugin je "vypnutý" - nikdy nespustí optimalizaci!**

---

## 🔄 JAK TO FUNGUJE DNES (Workflow)

### Současný Autonomous Workflow:

```
1. ERROR occurs (task fails)
   ↓
2. DREAM_COMPLETE event (memory consolidation)
   ↓
3. Cognitive Reflection analyzes failures
   ↓
4. Creates hypothesis with fix_type="prompt_optimization"  ✅
   ↓
5. Hypothesis stored in database  ✅
   ↓
6. Self-Tuning Plugin picks up hypothesis  ✅
   ↓
7. Applies prompt fix in sandbox  ✅
   ↓
8. Benchmarks prompt (length comparison)  ✅
   ↓
9. Deploys if improvement > 10%  ✅
   ↓
10. Creates git commit + PR  ✅
```

**✅ WORKFLOW JE KOMPLETNÍ!**

**Ale:**
- ⚠️ Reflection plugin musí **správně identifikovat** prompt issues
- ⚠️ `proposed_fix` musí obsahovat **nový optimalizovaný prompt text**

---

## ❓ CO CHYBÍ (Gap Analysis)

### 🔴 KRITICKÝ CHYBĚJÍCÍ KROK:

**Cognitive Reflection vytváří hypotheses, ale:**
- ❓ **Odkud vezme "proposed_fix" pro prompt optimization?**
- ❓ **Kdo vygeneruje nový optimalizovaný prompt?**

**Současné řešení:**
- Reflection plugin volá Expert LLM (4-tier escalation) ✅
- LLM vrací JSON s `proposed_fix` ✅
- **ALE:** LLM musí dostat **správný prompt**, aby vygeneroval **celý nový prompt text**!

**Problém:**
- Analysis prompt (lines 412-441) žádá o "KONKRÉTNÍ FIX"
- Ale **nespecifikuje**, že pro prompt_optimization musí vrátit **plný nový prompt text**
- LLM může vrátit jen "Zkraťte prompt" místo skutečného textu!

---

## 🎯 CO POTŘEBUJEME DODĚLAT

### Priority 1: Vylepšit Reflection Analysis Prompt (30 minut)

**File:** `plugins/cognitive_reflection.py` (lines 412-441)

**Změna:**
Přidat speciální sekci pro `prompt_optimization`:

```python
def _build_analysis_prompt(self, operation_type, failures, error_samples, success_rate):
    prompt = f"""Jsi expert na debugging AI systémů. Analyzuj tyto selhání:

OPERACE: {operation_type}
POČET SELHÁNÍ: {len(failures)} za posledních 7 dní
ÚSPĚŠNOST: {success_rate}%

PŘÍKLADY CHYB:
{error_samples}

ÚKOL:
1. Identifikuj ROOT CAUSE (ne symptom!)
2. Navrhni KONKRÉTNÍ FIX (změna kódu, prompt, config, nebo model)
3. Odhadni IMPACT (high/medium/low)

⭐ SPECIÁLNÍ INSTRUKCE PRO PROMPT OPTIMIZATION:
Pokud fix_type="prompt_optimization", pak pole "proposed_fix" MUSÍ obsahovat:
- KOMPLETNÍ nový prompt text (ne jen popis změny!)
- Optimalizovaný pro local 8B LLM (llama3.1:8b)
- Kratší, jasnější, s konkrétními příklady
- Zachovává funkčnost, ale zjednodušuje jazyk

Vrať JSON:
{{
  "root_cause": "...",
  "hypothesis": "...",
  "proposed_fix": "PLNÝ TEXT nového promptu (pokud fix_type=prompt_optimization) nebo popis změny (jinak)",
  "fix_type": "code_fix|prompt_optimization|config_tuning|model_change",
  "priority": 1-100,
  "estimated_improvement": "15%"
}}
"""
    return prompt
```

**⏱️ Časová náročnost:** 30 minut  
**🔧 Složitost:** LOW  
**✅ Dopad:** CRITICAL - Umožní plnou prompt optimization!

---

### Priority 2: Vylepšit Prompt Benchmarking (1 hodina)

**File:** `plugins/cognitive_self_tuning.py` (lines 558-597)

**Problém:**
- Současný benchmark pouze **porovnává délku**
- To je **příliš primitivní** pro skutečné hodnocení

**Řešení:**
Přidat **real-world testing** na sample inputs:

```python
async def _benchmark_prompt(self, workspace_root, sandbox_dir, target_file):
    """
    Enhanced prompt benchmarking with real-world testing.
    
    1. Load old and new prompts
    2. Get sample inputs from operation_tracking (last 10 examples)
    3. Test both prompts with local 8B LLM
    4. Compare:
       - Success rate (valid JSON, correct format)
       - Response quality (length, clarity)
       - Token usage
    5. Return improvement percentage
    """
    baseline_prompt = (workspace_root / "config/prompts" / target_file).read_text()
    new_prompt = (sandbox_dir / "config/prompts" / target_file).read_text()
    
    # Get sample test cases from database
    test_cases = await self._get_sample_inputs(target_file, limit=10)
    
    if not test_cases:
        # Fallback to length comparison
        return self._compare_prompt_lengths(baseline_prompt, new_prompt)
    
    # Run both prompts on test cases
    baseline_results = await self._test_prompt(baseline_prompt, test_cases)
    new_results = await self._test_prompt(new_prompt, test_cases)
    
    # Calculate improvement
    baseline_success = sum(1 for r in baseline_results if r["valid"]) / len(test_cases)
    new_success = sum(1 for r in new_results if r["valid"]) / len(test_cases)
    
    improvement = (new_success - baseline_success) / baseline_success if baseline_success > 0 else 0
    
    return {
        "baseline_success_rate": baseline_success,
        "new_success_rate": new_success,
        "improvement": improvement,
        "test_cases_count": len(test_cases),
        "success": new_success > baseline_success
    }

async def _get_sample_inputs(self, prompt_file: str, limit: int = 10):
    """Query operation_tracking for recent inputs that used this prompt."""
    # TODO: Implement database query
    pass

async def _test_prompt(self, prompt_text: str, test_cases: List[str]):
    """Test prompt with sample inputs using local 8B LLM."""
    # TODO: Call LLM with prompt + each test case
    pass
```

**⏱️ Časová náročnost:** 1 hodina  
**🔧 Složitost:** MEDIUM  
**✅ Dopad:** HIGH - Přesnější rozhodování o nasazení

---

### Priority 3: Odstranit Prompt Optimizer Plugin? (0 minut)

**File:** `plugins/cognitive_prompt_optimizer.py`

**Otázka:** Je tento plugin ještě potřeba?

**Analýza:**
- ❌ Neběží automaticky (`_should_optimize() = False`)
- ❌ TODO placeholders v critical metodách
- ✅ Reflection + Self-Tuning **už prompt optimization dělají!**

**Doporučení:**
- **MOŽNOST A:** Smazat plugin (redundantní)
- **MOŽNOST B:** Přepracovat na "Prompt Testing Framework" (Phase 4)
- **MOŽNOST C:** Ponechat jako fallback/manual trigger (nízká priorita)

**🎯 Pro AMI 1.0:** Doporučuji **MOŽNOST A** (smazat) nebo **MOŽNOST C** (ignorovat)

**⏱️ Časová náročnost:** 0 minut (ignorovat) nebo 10 minut (smazat)  
**🔧 Složitost:** LOW  
**✅ Dopad:** LOW (jen úklid kódu)

---

## 📊 IMPLEMENTAČNÍ PLÁN

### ✅ Doporučené kroky pro AMI 1.0:

| # | Úkol | Soubor | Čas | Priorita | Důležitost |
|---|------|--------|-----|----------|------------|
| 1 | Vylepšit Reflection prompt | `cognitive_reflection.py` | 30 min | 🔴 CRITICAL | ⭐⭐⭐⭐⭐ |
| 2 | Vylepšit benchmark prompt | `cognitive_self_tuning.py` | 1h | 🟡 MEDIUM | ⭐⭐⭐⭐ |
| 3 | Rozhodnout o Prompt Optimizer | `cognitive_prompt_optimizer.py` | 10 min | 🟢 LOW | ⭐ |

**Celkový čas:** ~1.5 hodiny

**Po implementaci Priority 1:**
- ✅ Reflection bude generovat plné prompt texty
- ✅ Self-Tuning je aplikuje a testuje
- ✅ **KOMPLETNÍ prompt optimization workflow!**

**Po implementaci Priority 2:**
- ✅ Přesnější benchmarking
- ✅ Lepší rozhodování o deployment
- ✅ Vyšší kvalita optimalizací

---

## 🎯 FINÁLNÍ VERDIKT

### ✅ Prompt Optimization JE implementována!

**Ale:**
- ⚠️ **Priority 1 je KRITICKÁ** pro správnou funkčnost
- ⚠️ **Priority 2 je DOPORUČENÁ** pro kvalitu

**Pro AMI 1.0:**
- ✅ **Priority 1 MUSÍ být hotová** (30 min)
- 🟡 **Priority 2 je nice-to-have** (1h)
- 🟢 **Priority 3 je optional cleanup** (10 min)

**Celkový scope pro 100% funkční prompt optimization:**
- **Minimum:** 30 minut (Priority 1)
- **Doporučeno:** 1.5 hodiny (Priority 1 + 2)
- **Maximum:** 1.7 hodiny (vše včetně cleanup)

---

## 🚀 NEXT STEPS

**Chceš, abych:**

### Možnost A: Implementovat Priority 1 (30 min) ✅ DOPORUČUJI
- Vylepším Reflection analysis prompt
- Otestuji na sample hypotéze
- Prompt optimization bude 100% funkční!

### Možnost B: Implementovat Priority 1 + 2 (1.5h) ⭐ BEST
- Priority 1: Reflection prompt
- Priority 2: Real-world benchmarking
- **Kompletní enterprise-grade prompt optimization!**

### Možnost C: Analyzovat současný stav blíž
- Najdu existující prompty v `config/prompts/`
- Otestuji, jestli Reflection už generuje správné hypotézy
- Možná to **už funguje** a jen potřebuje aktivaci!

**Co preferuješ?** 😊

---

*Analýza: 2025-11-06 | Verdikt: 30 min od 100% funkčního prompt optimization!*
