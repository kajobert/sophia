# ZADÁNÍ: Integrace Dlouhodobé Paměti a "Procesu Snění"

## CÍL
Upravit `main.py` tak, aby po každé interakci s uživatelem došlo k automatickému spuštění procesu "konsolidace paměti", ve kterém si `MemoryAgent` uloží klíčové poznatky do dlouhodobé paměti.

## KONTEXT
Máme funkční interaktivní smyčku s krátkodobou pamětí. Dlouhodobá paměť je také implementována, ale není zatím využívána. Tímto krokem oba systémy propojíme a vytvoříme plnohodnotný kognitivní cyklus.

## PLÁN KROK ZA KROKEM

### Krok 1: Aktualizace importů v `main.py`
Do souboru `main.py` přidej importy pro `MemoryAgenta` a jeho úkol.

### Krok 2: Vytvoření funkce pro "Snění"
Vytvoř v `main.py` novou funkci `run_memory_consolidation()`. Uvnitř této funkce:
1.  Vytvoř novou instanci `Crew` s `memory_agent` a `memory_consolidation_task`.
2.  Spusť tuto posádku pomocí `kickoff()`.
3.  Vypiš na obrazovku zprávu, že proces konsolidace paměti proběhl.

### Krok 3: Volání "Snění" v hlavní smyčce
Uvnitř `while` smyčky v `main()` přidej na konec volání naší nové funkce `run_memory_consolidation()`. Tím zajistíš, že po každé odpovědi od Sophie dojde k "zamyšlení" a uložení do paměti.

### Krok 4: Zajištění dostupnosti všech modulů
Ověř, že soubory `core/agents.py` a `core/tasks.py` obsahují definice pro všechny potřebné agenty a úkoly (`developer_agent`, `memory_agent`, `memory_consolidation_task`). Pokud chybí, doplň je podle naší předchozí práce.

## OČEKÁVANÝ VÝSLEDEK
Upravený `main.py`, který po každé interakci s uživatelem automaticky spustí druhý `Crew` pro konsolidaci paměti. Po každé odpovědi od Sophie by se v terminálu měla objevit zpráva o tom, že probíhá a dokončil se proces "snění".