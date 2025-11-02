# Gemini Flash Models - Benchmark Results Summary

**Date:** 2025-11-02  
**Purpose:** Test Gemini Flash models to find cheaper alternatives to DeepSeek Chat ($0.14/1M)

---

## Test Results

### ❌ FAILED MODELS (Score < 8/10)

| Model | Score | Cost/1M | Issue |
|-------|-------|---------|-------|
| Gemini 2.0 Flash Exp (FREE) | 1/10 | $0.00 | LiteLLM mapping error |
| Gemini 2.0 Flash Lite 001 | 1/10 | $0.075 | LiteLLM mapping error |
| Gemini 2.0 Flash 001 | 2/10 | $0.10 | Poor quality (only did step 1/8) |

**Problém:** Modely Gemini 2.0 Flash Lite a Exp nejsou správně zmapovány v LiteLLM. Gemini 2.0 Flash 001 je zmapován, ale má velmi slabou kvalitu.

---

### ✅ PASSED MODEL (Score >= 8/10)

| Model | Score | Cost/1M | vs DeepSeek |
|-------|-------|---------|-------------|
| **Gemini 2.5 Flash** | **9.5/10** | **$0.30** | **114% dražší** ❌ |

**Výsledek:** Gemini 2.5 Flash má vynikající kvalitu (9.5/10), ale je **více než 2x dražší** než DeepSeek Chat ($0.14/1M).

---

## Závěr

### 🎯 DOPORUČENÍ: Zůstat u DeepSeek Chat

**Proč?**

1. **DeepSeek Chat: 10/10 @ $0.14/1M** 
   - Nejlepší skóre ze všech testovaných modelů
   - O 53% levnější než Gemini 2.5 Flash
   
2. **Gemini 2.5 Flash: 9.5/10 @ $0.30/1M**
   - Skvělá kvalita, ale dražší
   - Vhodný jako fallback pro úkoly vyžadující multimodalitu

3. **Levnější Gemini modely selhaly**
   - Gemini 2.0 Flash Lite ($0.075/1M) - litellm chyby
   - Gemini 2.0 Flash 001 ($0.10/1M) - nízká kvalita (2/10)

---

## Aktualizovaná Cenová Analýza

### TOP 5 Nejlepších Modelů (Cena vs Kvalita)

| Model | Score | Cost/1M | Kvalita/Cena |
|-------|-------|---------|--------------|
| 1. **DeepSeek Chat** | 10/10 | $0.14 | **71.4** ✅ |
| 2. Mistral Large | 10/10 | $2.00 | 5.0 |
| 3. **Gemini 2.5 Flash** | 9.5/10 | $0.30 | **31.7** |
| 4. Gemini 2.5 Pro | 9.8/10 | $1.25 | 7.8 |
| 5. Claude 3.5 Sonnet | 9/10 | $3.00 | 3.0 |

**Kvalita/Cena = Score / Cost** (vyšší = lepší hodnota)

---

## Multi-Model Strategy Update

Gemini 2.5 Flash by se mohl použít jako premium fallback pro specifické úkoly:

```yaml
task_strategies:
  - task_type: "simple_query"
    model: "openrouter/deepseek/deepseek-chat"  # $0.14/1M
    
  - task_type: "text_summarization"
    model: "openrouter/deepseek/deepseek-chat"  # $0.14/1M
    
  - task_type: "plan_generation"
    model: "openrouter/anthropic/claude-3.5-sonnet"  # $3.00/1M (kritické úkoly)
    
  - task_type: "multimodal_tasks"  # NEW
    model: "openrouter/google/gemini-2.5-flash"  # $0.30/1M (obrázky + text)
    
  - task_type: "json_repair"
    model: "openrouter/deepseek/deepseek-chat"  # $0.14/1M
```

---

## Lessons Learned

1. **LiteLLM Mapping je kritické**
   - Levnější modely (Lite, Exp) často nejsou zmapované
   - Mapovací chyba = model nelze použít pro cost tracking

2. **"Lite" != "Levnější a funkční"**
   - Gemini 2.0 Flash Lite má litellm problémy
   - Gemini 2.0 Flash 001 má nízkou kvalitu
   - "Lite" verze mohou být víc problémů než úspory

3. **DeepSeek Chat zůstává nepřekonatelný**
   - Perfektní skóre (10/10)
   - Nejnižší cena mezi funkčními modely ($0.14/1M)
   - Žádné mapping problémy
   - **ROI šampion!** 🏆

4. **Gemini 2.5 Flash má své místo**
   - Skvělá kvalita (9.5/10)
   - Rychlý (3.5s response time)
   - Vhodný pro multimodální úkoly (obrázky + text)
   - Ale 2x dražší než DeepSeek

---

## Final Recommendation

### Pro běžné úkoly:
**DeepSeek Chat @ $0.14/1M** - Nejlepší poměr cena/výkon

### Pro multimodální úkoly:
**Gemini 2.5 Flash @ $0.30/1M** - Když potřebuješ zpracovat obrázky

### Pro kritické úkoly:
**Claude 3.5 Sonnet @ $3.00/1M** - Maximum kvalita pro důležité věci

---

**Testováno:** 4 Gemini Flash modely  
**Úspěšných:** 1 model (Gemini 2.5 Flash - 9.5/10)  
**Závěr:** DeepSeek Chat zůstává optimální volbou pro standardní provoz 🎯
