# 🧠 SOPHIA Self-Improvement Workflow - Start

## 📋 Autonomní Self-Improvement Úkol

**Poslat tento dotaz v Dashboard Chat:**

```
Spusť autonomní self-improvement proces:

1. ANALYZUJ moje logy (logs/sophia.log) - najdi všechny ERROR a WARNING za poslední 3 hodiny
2. PŘEČTI roberts-notes.txt - zpracuj všechny úkoly které tam jsou
3. VYGENERUJ hypotézy o vylepšeních na základě:
   - Chyb v logách (zejména Jules API, consolidation)
   - Úkolů v roberts-notes
   - Tvých schopností a dostupných nástrojů
4. VYTVOŘ prioritizovaný action plan s konkrétními kroky

Použij cognitive_code_reader pro čtení souborů a tool_llm pro analýzu.
Výstup strukturuj jako:
- 🔍 Nalezené problémy (top 3)
- 💡 Hypotézy řešení (každý problém)
- 📊 Action plan (prioritizovaný seznam kroků)
- ⚡ Doporučení pro okamžité akce
```

## 🎯 Očekávaný Výsledek

SOPHIA by měla:
1. ✅ Přečíst logs/sophia.log pomocí cognitive_code_reader
2. ✅ Najít recurring errors:
   - `JulesAPITool.create_session() missing 1 required positional argument: 'context'`
   - `CognitiveMemoryConsolidator' object has no attribute 'trigger_consolidation'`
3. ✅ Přečíst roberts-notes.txt
4. ✅ Identifikovat úkoly (Priority 85, 70, 50)
5. ✅ Vygenerovat hypotézy pomocí Claude 3.5 Sonnet
6. ✅ Vytvořit strukturovaný action plan

## 📊 Monitoring

Sleduj logy během execution:
```bash
tail -f logs/sophia.log | grep -E "cognitive_code_reader|Step|ERROR|completed"
```

## 🚀 Po dokončení

SOPHIA ti vrátí report s:
- Identifikovanými problémy z logů
- Analýzou roberts-notes úkolů
- Hypotézami řešení
- Konkrétním action planem

Následně můžeš říct: "Proveď první 3 kroky z action planu" a SOPHIA je autonomně vykoná!

---

**READY TO START!** 
Otevři Dashboard Chat a pošli dotaz výše.
