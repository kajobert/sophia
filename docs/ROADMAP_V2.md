# Technická Roadmapa: Sophia 2.0 - Cesta k Autonomii

Tento dokument definuje strategickou a technickou vizi pro další evoluční krok projektu Sophia. Cílem verze 2.0 je transformovat Sophii z MVP nástroje na skutečně autonomního agenta schopného dlouhodobého učení, strategického plánování a sebe-zdokonalování. Toho dosáhneme integrací state-of-the-art technologií a přestavbou klíčových částí architektury.

---

## EPIC 1: Upgrade Jádra na "Gemini-Native"

**Cíl:** Přestavět jádro Sophie tak, aby plně a nativně využívalo pokročilé schopnosti Google Gemini API, a opustit tak současné, méně robustní mechanismy.

**Technické Úkoly:**

1.  **Refaktoring LLM Adapteru:**
    *   Upravit `llm/gemini_llm_adapter.py`, aby podporoval všechny klíčové featury: multimodální vstupy (obrázky, v budoucnu video/audio), nativní function calling a dlouhý kontext.
    *   Odstranit stávající manuální parsování nástrojů a nahradit ho přímou integrací s Gemini Function Calling. To zjednoduší `core/orchestrator.py` a sníží chybovost.

2.  **Implementace "Repository-Aware" Kontextu:**
    *   Vytvořit novou strategii pro správu kontextu, která před každým úkolem vloží do promptu klíčové informace o celém repozitáři (struktura souborů, klíčové API, závislosti).
    *   Využít masivní kontextové okno Gemini (1M+ tokenů) k tomu, aby si Sophia "pamatovala" celý relevantní pracovní prostor, místo aby se spoléhala jen na útržkovité informace. To dramaticky zlepší kvalitu plánování a implementace.

3.  **Přechod na Strukturované Výstupy:**
    *   Využít nativní schopnost Gemini generovat JSON a jiné strukturované formáty.
    *   Definovat Pydantic modely pro všechny klíčové datové struktury (plány, výsledky nástrojů, reporty) a vynutit si jejich používání napříč všemi agenty. Tím se zajistí spolehlivá a strojově čitelná komunikace mezi komponentami systému.

---

## EPIC 2: Implementace Strategické Vrstvy ("Meta-Control Protocol")

**Cíl:** Vytvořit novou, nadřazenou řídící vrstvu inspirovanou architekturou MetaGPT, která bude zodpovědná za dlouhodobé cíle a sebe-zdokonalování Sophie.

**Technické Úkoly:**

1.  **Vývoj "Meta-Agenta":**
    *   Vytvořit nového agenta `core/meta_agent.py`, který bude fungovat jako projektový manažer.
    *   Jeho úkolem bude:
        *   Načítat úkoly z externích zdrojů (např. GitHub Issues API).
        *   Prioritizovat backlog úkolů.
        *   Delegovat jednotlivé úkoly na stávající agenty (`PlannerAgent` pro návrh, `ExecutionAgent` pro implementaci).
        *   Monitorovat průběh a výsledek exekuce.

2.  **Implementace Smyčky Sebereflexe (Self-Correction Loop):**
    *   Po každém dokončeném úkolu (commit, PR) Meta-Agent provede analýzu:
        *   **Analýza Úspěšnosti:** Povedlo se úkol splnit? Jak efektivní byl plán? Kolikrát bylo potřeba provést opravu?
        *   **Analýza Kódu:** Porovná nově vytvořený kód s best practices.
        *   **Generování Úkolů pro Sebe-Zlepšení:** Na základě analýzy si Meta-Agent sám vytvoří nové úkoly v backlogu. Například:
            *   `"Refaktoruj nástroj X, protože v posledních 3 úkolech selhal."`
            *   `"Vylepši systémový prompt pro PlannerAgenta, aby lépe zohledňoval Y."`
            *   `"Přidej nový test pro funkci Z, která nebyla pokryta."`

---

## EPIC 3: Perzistentní Paměť a Hluboké Porozumění Kódu

**Cíl:** Nahradit dočasnou paměť (`SharedContext`) za permanentní znalostní bázi, která bude reprezentovat kódovou bázi a historii interakcí, a splnit tak požadavek z `AGENTS.md`.

**Technické Úkoly:**

1.  **Implementace Vektorové Databáze (Knowledge Graph):**
    *   Zavést vektorovou databázi (např. ChromaDB, Pinecone) jako centrální paměť Sophie.
    *   Vytvořit proces, který bude indexovat a vektorizovat:
        *   **Kódovou bázi:** Každou funkci, třídu a soubor jako samostatný dokument s metadaty (cesta, závislosti).
        *   **Dokumentaci:** `README.md`, `DEVELOPER_GUIDE.md` a další klíčové dokumenty.
        *   **Historii Úkolů:** Každý úspěšný i neúspěšný úkol, jeho plán, výsledek a logy.

2.  **Automatická Aktualizace Grafu:**
    *   Vytvořit webhook nebo GitHub Action, který se spustí po každém úspěšném commitu do `master` větve.
    *   Tento proces automaticky re-indexuje změněné soubory a uloží informace o dokončeném úkolu do vektorové databáze.

3.  **Integrace Paměti do Promptu:**
    *   Před generováním plánu provede `PlannerAgent` sémantické vyhledávání v paměti.
    *   Do promptu se automaticky přidají nejrelevantnější úryvky kódu, dokumentace nebo poučení z minulých úkolů. Sophia se tak bude "učit" a nebude opakovat stejné chyby.

---

## EPIC 4: Multimodální Schopnosti v Praxi

**Cíl:** Dát Sophii "oči" a umožnit jí zpracovávat vizuální informace jako součást zadání úkolu.

**Technické Úkoly:**

1.  **Úprava API a UI:**
    *   Rozšířit API (a případné webové rozhraní) o možnost nahrávat obrázky spolu s textovým zadáním.
    *   Umožnit uživatelům poslat například screenshot chyby v aplikaci s popisem "Oprav toto".

2.  **Vývoj "VisionAgenta":**
    *   Vytvořit nového agenta `agents/vision_agent.py`, který bude specializovaný na analýzu obrázků pomocí multimodálních schopností Gemini.
    *   Úkoly VisionAgenta:
        *   **Analýza Screenshotů:** Identifikovat UI komponenty, texty a chyby na screenshotech.
        *   **Analýza Diagramů:** "Přečíst" jednoduchý diagram architektury a přeložit ho do textového popisu nebo pseudokódu.
        *   **Překlad do Instrukcí:** Výstupem VisionAgenta nebude kód, ale strukturovaný textový popis problému, který předá `PlannerAgentovi` k dalšímu zpracování. ("Na základě screenshotu vidím, že tlačítko 'Potvrdit' má špatnou barvu a chybí mu padding. Navrhni plán na úpravu CSS souboru X.")

3.  **Integrace do Orchestrace:**
    *   Upravit `core/orchestrator.py` tak, aby na začátku procesu detekoval, zda vstup obsahuje obrázek. Pokud ano, nejprve zavolá `VisionAgenta` a jeho výstup použije jako vstup pro `PlannerAgenta`.
