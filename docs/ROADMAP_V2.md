# Technická Roadmapa: Sophia 2.0 - Cesta k Autonomii (vylepšená verze)

Tento dokument definuje strategickou a technickou vizi pro další evoluční krok projektu Sophia. Cílem verze 2.0 je transformovat Sophii z MVP nástroje na skutečně autonomního agenta schopného dlouhodobého učení, strategického plánování a sebe-zdokonalování. Toho dosáhneme integrací state-of-the-art technologií a přestavbou klíčových částí architektury.

---

## EPIC 1: Přechod na MCP a Gemini-Native Architekturu

**Cíl:** Fundamentálně přebudovat způsob, jakým Sophia interaguje s nástroji a daty, přechodem na otevřený standard **Model Context Protocol (MCP)** a plnou integrací s Gemini API.

**Technické Úkoly:**

1.  **Implementace Architektury MCP (Host/Server):**
    *   **Sophia jako MCP Host:** Refaktorovat `core/orchestrator.py`. Orchestrator se stane "MCP Hostem", který nebude přímo volat nástroje, ale bude komunikovat se standardizovaným MCP rozhraním.
    *   **Nástroje jako MCP Servery:** Každý nástroj ze stávajícího `Toolbeltu` (např. `FileSystemTool`, `GitTool`) bude zapouzdřen do vlastního, lehkého MCP serveru. To umožní:
        *   **Dynamické objevování nástrojů:** Sophia se bude moci za běhu připojit k novým nástrojům bez nutnosti rekompilace nebo restartu.
        *   **Standardizovanou komunikaci:** Odstraní se křehké, na míru psané integrace.
        *   **Budoucí rozšířitelnost:** Jakýkoliv nový nástroj (i od třetích stran) bude stačit, aby implementoval MCP rozhraní.

2.  **Využití Plného Potenciálu Gemini API:**
    *   **Repository-Aware Kontext:** Využít 1M+ tokenové kontextové okno Gemini k tomu, aby si Sophia před každým úkolem "načetla" celý repozitář, včetně klíčových souborů, závislostí a `AGENTS.md`. Tím získá bezprecedentní přehled.
    *   **Strukturované Výstupy (JSON Mode):** Důsledně využívat schopnost Gemini generovat garantovaný JSON pro všechny interní datové struktury (plány, reporty, výsledky analýz). Tím se zajistí robustní a strojově čitelná komunikace mezi agenty.

---

## EPIC 2: Implementace Strategické Vrstvy ("Meta-Control Protocol")

**Cíl:** Vytvořit novou, nadřazenou řídící vrstvu inspirovanou architekturou MetaGPT, která bude zodpovědná za dlouhodobé cíle a pokročilé sebe-zdokonalování Sophie.

**Technické Úkoly:**

1.  **Vývoj "Meta-Agenta":**
    *   Vytvořit `core/meta_agent.py`, který bude fungovat jako projektový manažer. Jeho úkolem bude spravovat backlog úkolů (např. z GitHub Issues), prioritizovat je a delegovat na specializované agenty.

2.  **Pokročilá Smyčka Sebereflexe (Advanced Self-Correction Loop):**
    *   Po každém úkolu Meta-Agent provede hloubkovou analýzu:
        *   **Analýza Výstupů Pomocí `Logprobs`:** Využít `Logprobs` z Gemini API k posouzení, jak si byl model "jistý" svými odpověďmi v jednotlivých krocích. Nízká jistota může indikovat problematickou oblast.
        *   **Automatické Spouštění Fine-Tuning Úloh:** Pokud Meta-Agent opakovaně detekuje stejný typ chyby (např. špatné formátování kódu, nepochopení určitého konceptu), automaticky vygeneruje dataset z těchto neúspěšných pokusů a **spustí fine-tuning job** pro Gemini model, aby se v budoucnu v této oblasti zlepšil.
        *   **Generování Úkolů pro Sebe-Zlepšení:** Na základě analýzy si Meta-Agent sám vytvoří nové úkoly v backlogu (např. `"Refaktoruj nástroj X"`, `"Vylepši prompt pro PlannerAgenta"`).

---

## EPIC 3: Perzistentní Paměť a Hluboké Porozumění Kódu

**Cíl:** Nahradit dočasnou paměť za permanentní, multimodální znalostní bázi, která bude klíčová pro dlouhodobé učení a kontextuální pochopení.

**Technické Úkoly:**

1.  **Implementace Multimodální Vektorové Databáze:**
    *   Zavést vektorovou databázi (např. ChromaDB) a nakonfigurovat ji pro ukládání **multimodálních embeddingů**.
    *   Vytvořit proces, který bude indexovat:
        *   **Kód a Dokumentaci:** Každou funkci, třídu a dokument jako textový embedding.
        *   **Vizuální Kontext:** Screenshoty UI komponent, diagramy architektur. Embeddingy z těchto obrázků budou uloženy spolu s embeddingy kódu, který je generuje. Tím vznikne **přímé propojení mezi kódem a jeho vizuální reprezentací**.
        *   **Historii Úkolů:** Úspěšné i neúspěšné pokusy, včetně logů, chyb a finálních řešení.

2.  **Sémantické Vyhledávání v Reálném Čase:**
    *   Před každým úkolem provedou agenti sémantické vyhledávání v této databázi. Do promptu se tak automaticky vloží nejen relevantní úryvky kódu z aktuálního repozitáře, ale i:
        *   Poučení z podobného úkolu řešeného v minulosti.
        *   Relevantní část firemní dokumentace.
        *   Screenshot, jak má výsledná komponenta vypadat.

---

## EPIC 4: Multimodální Schopnosti a Rozšířená Interakce

**Cíl:** Dát Sophii "oči a uši" a umožnit jí chápat komplexní, více-krokové a multimodální problémy.

**Technické Úkoly:**

1.  **Vývoj Pokročilého "VisionAgenta":**
    *   Vytvořit `agents/vision_agent.py` schopného **uvažování nad sekvencemi obrázků**.
    *   **Příklad úkolu:** Uživatel nahraje 3 screenshoty ukazující kroky, které vedou k chybě. VisionAgent analyzuje celou sekvenci, pochopí uživatelskou cestu a identifikuje, kde a proč k chybě došlo.
    *   **Překlad Diagramů na Kód:** Schopnost přeložit UML nebo architektonický diagram přímo na kostru kódu (placeholdery pro třídy a metody).

2.  **Experimentální "AudioAgent":**
    *   Jako výhled do budoucna, navrhnout prototyp `agents/audio_agent.py`.
    *   Tento agent by využíval Geminiho schopnosti pro zpracování zvuku a umožnil by uživatelům **nadiktovat bug report nebo zadání úkolu hlasem**. Agent by přepsal mluvené slovo na strukturovaný text a předal ho Meta-Agentovi.

3.  **Integrace do Orchestrace:**
    *   Upravit `core/orchestrator.py` a `core/meta_agent.py` tak, aby dokázaly pracovat s multimodálními vstupy (obrázky, sekvence obrázků, audio) a na jejich základě delegovat práci správným specializovaným agentům (`VisionAgent`, `AudioAgent`).
