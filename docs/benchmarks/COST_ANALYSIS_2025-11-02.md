# Analýza nejlevnějších modelů pro provoz Sophie
**Datum:** 2025-11-02  
**Účel:** Najít nejnižší možnou cenu za 1M tokenů pro plně funkční Sophii

---

## 🏆 VÍTĚZ: DeepSeek Chat

### **Proč DeepSeek Chat?**

✅ **Score: 10/10** - Perfektní úspěšnost na 8-krokovém testu  
✅ **Cena: $0.14/1M tokenů** (průměr prompt + completion)  
✅ **Skutečná cena za test run: $0.000246** (1029 tokenů)  
✅ **Context: 163,840 tokenů** - dostatečný pro složité úlohy

### **Srovnání s aktuálně používaným modelem:**

| Model | Cena/1M | Score | Test Cost | Rychlost |
|-------|---------|-------|-----------|----------|
| **DeepSeek Chat** | **$0.14** | **10/10** | **$0.000246** | 14.3s |
| Claude 3 Haiku (current) | $0.25 | 10/10 | $0.001304 | 6.7s |
| Claude 3.5 Sonnet | $3.00 | 9/10 | $0.005892 | 5.4s |
| Gemini 2.5 Pro | $1.25 | 9.8/10 | $0.004942 | 3.5s |

**ÚSPORA: 44%** oproti Claude 3 Haiku  
**ÚSPORA: 95%** oproti Claude 3.5 Sonnet

---

## 📊 TOP 5 NEJLEVNĚJŠÍCH FUNKČNÍCH MODELŮ

### 1. **DeepSeek Chat** ⭐ DOPORUČENO
- **Cena:** $0.30/1M tokenů (prompt + completion průměr: $0.14)
- **Score:** 10/10 ✅ OVĚŘENO
- **Použití:** Hlavní model pro Sophie - general purpose

### 2. **Llama 3.2 1B Instruct**
- **Cena:** $0.0075/1M tokenů
- **Score:** ❓ NETESTOVÁNO
- **Použití:** Extrémně levný, ale malý (1B parametrů) - vhodný jen pro VELMI jednoduché úlohy

### 3. **Llama 3.2 3B Instruct**
- **Cena:** $0.02/1M tokenů
- **Score:** ❓ NETESTOVÁNO
- **Použití:** Levný, malý model - možná vhodný pro task routing

### 4. **Llama 3.1 8B Instruct**
- **Cena:** $0.025/1M tokenů
- **Score:** ❓ NETESTOVÁNO (pravděpodobně selže - starší benchmark failed)
- **Použití:** Starší verze selhala, nová může fungovat

### 5. **Mistral Nemo**
- **Cena:** $0.03/1M tokenů
- **Score:** ❓ NETESTOVÁNO
- **Použití:** Levný Mistral model, 131K context

---

## 💡 DOPORUČENÁ STRATEGIE PRO SOPHII

### **Multi-Model Strategy (optimalizace nákladů)**

```yaml
# config/model_strategy.yaml

strategies:
  # Pro jednoduchéchat/FAQ - nejlevnější
  simple_query:
    model: "openrouter/meta-llama/llama-3.2-3b-instruct"
    cost_per_1m: 0.02
    
  # Pro task routing - rychlý a levný
  task_classification:
    model: "openrouter/mistralai/mistral-nemo"
    cost_per_1m: 0.03
    
  # Pro hlavní práci - nejlepší poměr cena/výkon
  planning:
    model: "openrouter/deepseek/deepseek-chat"
    cost_per_1m: 0.14
    
  # Pro složité úlohy - kvalita nad cenou
  complex_reasoning:
    model: "openrouter/anthropic/claude-3-haiku"
    cost_per_1m: 0.25
    
  # Pro kritickou komunikaci (Google outreach)
  critical_communication:
    model: "openrouter/anthropic/claude-3.5-sonnet"
    cost_per_1m: 3.00
```

### **Odhadované úspory:**

- **Běžný provoz:** 70-80% úspora (většina requestů na cheap models)
- **S plánováním:** 50-60% úspora (DeepSeek pro většinu práce)
- **Kritické úlohy:** Kvalita zachována (Claude 3.5 Sonnet pro důležité věci)

---

## 🎯 KONKRÉTNÍ DOPORUČENÍ PRO GOOGLE OUTREACH

### **Fáze 1: Příprava (Llama 3.2 3B)**
- Brainstorming nápadů
- Základní research
- **Cena:** ~$0.02/1M

### **Fáze 2: Plánování (DeepSeek Chat)**
- Vytvoření strategie komunikace
- Struktura prezentace
- **Cena:** ~$0.14/1M

### **Fáze 3: Tvorba obsahu (Claude 3 Haiku)**
- Draft emailu/prezentace
- Technické detaily
- **Cena:** ~$0.25/1M

### **Fáze 4: Finální verze (Claude 3.5 Sonnet)**
- Polishing
- Kontrola tónu a stylu
- Finální schválení
- **Cena:** ~$3.00/1M

**Celková odhadovaná cena:** $5-10 za celou kampaň (vs. $50-100 s pouze Claude 3.5)

---

## 🔬 CO DÁLE OTESTOVAT?

### **Priorita HIGH:**
1. ✅ **DeepSeek Chat** - už ověřeno jako vítěz
2. 🔲 **Llama 3.2 3B** - může být skvělý pro simple queries
3. 🔲 **Mistral Nemo** - levný s velkým contextem

### **Priorita MEDIUM:**
4. 🔲 **Mistral 7B Instruct** - levný klasický model
5. 🔲 **Gemma 2 9B** - Google model, dobrý výkon

### **Priorita LOW:**
6. 🔲 **Llama 3.2 1B** - příliš malý, ale extrémně levný

---

## 📈 PROJEKCE NÁKLADŮ

### **Scénář: 1 milion tokenů zpracování/měsíc**

| Strategie | Model Mix | Měsíční náklady |
|-----------|-----------|----------------|
| **All Claude 3.5** | 100% top tier | **$3,000** |
| **All Claude 3 Haiku** | 100% mid tier | **$250** |
| **All DeepSeek** | 100% DeepSeek | **$140** 💚 |
| **Smart Mix** | 60% DeepSeek + 30% Llama + 10% Claude | **$90** 🏆 |

### **Úspora Smart Mix:** **97% vs. Claude 3.5!**

---

## ✅ AKČNÍ KROKY

1. ✅ **Změnit default model v Sophie na DeepSeek Chat**
   ```yaml
   # config/settings.yaml
   llm:
     model: "openrouter/deepseek/deepseek-chat"
   ```

2. 🔲 **Otestovat Llama 3.2 3B a Mistral Nemo**
   - Spustit 8-step benchmark
   - Ověřit kvalitu výstupu

3. 🔲 **Implementovat multi-model routing v cognitive_task_router**
   - Přidat levné modely pro simple queries
   - Zachovat DeepSeek pro planning

4. 🔲 **Monitorovat kvalitu**
   - Sledovat success rate
   - Ajustovat model selection podle výsledků

---

## 🎓 ZÁVĚR

**DeepSeek Chat je jasným vítězem** pro provoz Sophie:
- ✅ 10/10 quality score (perfektní)
- ✅ $0.14/1M tokens (44% levnější než Haiku)
- ✅ 163K context (dostatečný)
- ✅ Rychlý (14s response time je OK)

**Pro Google outreach:**
- Použít **multi-tier strategii**
- DeepSeek pro přípravu a plánování
- Claude 3.5 Sonnet pouze pro finální verzi
- **Odhadovaná úspora:** 80-90% vs. all-Claude approach
