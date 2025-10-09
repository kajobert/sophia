# Návrh Implementace: Fáze 1 - Osvícený Manažer

**STATUS: Dokončeno**

*Tato fáze byla úspěšně implementována. Architektura byla refaktorována na model Manager/Worker, který odděluje konverzační logiku od provádění úkolů. Během implementace bylo rozhodnuto, že `ConversationalManager` bude používat interní metody namísto dedikovaného MCP serveru pro své nástroje, což vedlo k čistší a těsněji integrované architektuře.*

---

**Cíl:** Odstranit "hloupé" chování agenta Nomáda. Po dokončení této fáze bude `ConversationalManager` (dále jen "Manažer") chápat svá vlastní omezení a přestane halucinovat nástroje. `WorkerOrchestrator` (dále jen "Worker") bude flexibilnější a nebude zbytečně spouštět komplexní plánování pro jednoduché úkoly.

---

## 1. Refaktoring `MCPClient` a Struktury Nástrojů

**Problém:** V současné době `MCPClient` načítá všechny servery z jednoho adresáře, což znamená, že Manažer i Worker mají přístup ke stejné sadě nástrojů. To je hlavní příčina halucinací Manažera.

**Navrhované Řešení:** Zavedeme "profily" nástrojů. `MCPClient` bude inicializován s konkrétním profilem a bude spouštět pouze servery z odpovídajícího podadresáře.

**Nová Adresářová Struktura:**
```
mcp_servers/
├── manager/
│   └── manager_tools_server.py  # Nástroje pro zjištění stavu
└── worker/
    ├── file_system_server.py      # Nástroje pro práci se soubory
    ├── jules_api_server.py        # Nástroje pro delegování
    └── ... (všechny ostatní stávající servery)
```

**Změny v Kódu:**
-   `core/mcp_client.py`: Konstruktor `__init__` bude upraven na `__init__(self, project_root: str, profile: str)`.
-   Metoda `start_servers` v `MCPClient` bude upravena tak, aby četla soubory pouze z `mcp_servers/{profile}/`.

---

## 2. "Osvícený" `ConversationalManager`

**Problém:** Manažer si myslí, že může upravovat soubory a provádět složité operace, protože nemá jasně definované své schopnosti.

**Navrhované Řešení:** Dáme Manažerovi jeho vlastní, omezenou sadu nástrojů a vlastní prompt, který mu jasně vysvětlí jeho roli.

**Změny v Kódu:**
-   `core/conversational_manager.py`:
    -   Při inicializaci vytvoří vlastní instanci `MCPClient` s profilem "manager":
        ```python
        self.mcp_client = MCPClient(project_root=self.project_root, profile="manager")
        ```
    -   Bude načítat a používat nový, specifický prompt `prompts/manager_prompt.txt`.

**Nový Prompt (`prompts/manager_prompt.txt`):**
-   Bude obsahovat instrukce jako: "Jsi konverzační rozhraní. Tvým úkolem je mluvit s uživatelem a přijímat úkoly. **Nesmíš** upravovat soubory. Pokud se uživatel zeptá na stav práce, **musíš** použít nástroj `get_worker_status`."
-   Bude obsahovat pouze seznam nástrojů dostupných v profilu "manager".

---

## 3. "Adaptivní" `WorkerOrchestrator` a "Rozpočet na Složitost"

**Problém:** Současný triage systém je příliš rigidní. Nutí Workera buď provést jen jeden krok, nebo spustit plnohodnotné a zdlouhavé plánování, i když by stačilo jen pár kroků.

**Navrhované Řešení:** Nahradíme stávající triage systém (`SIMPLE_QUERY`, `COMPLEX_TASK` atd.) dynamickým "rozpočtem na složitost".

**Nový Tok Práce:**
1.  Manažer vždy předá úkol Workerovi s definovaným "rozpočtem" na kroky (např. 5).
2.  Worker se pokusí úkol splnit v rámci tohoto rozpočtu.
3.  **Pokud uspěje:** Vrátí výsledek (`{"status": "completed", ...}`).
4.  **Pokud neuspěje (rozpočet je vyčerpán):** Vrátí stav `{"status": "needs_planning", "summary": "Tento úkol je složitější a vyžaduje formální plán."}`.
5.  Manažer obdrží tento stav a zeptá se uživatele: "Tento úkol je složitější. Chceš, abych pro něj vytvořil detailní plán a pokračoval?"

**Změny v Kódu:**
-   `core/worker_orchestrator.py`:
    -   Odstraníme `Enum TaskType` a logiku spojenou s triage.
    -   Metoda `run` bude upravena tak, aby přijímala parametr `budget`.
    -   Bude upravena tak, aby vracela strukturovaný výsledek včetně stavu `needs_planning`.
-   `prompts/triage_prompt.txt`: Tento soubor bude odstraněn.

---
Tento návrh řeší všechny klíčové problémy, které jsme identifikovali, a posouvá nás k inteligentnějšímu a flexibilnějšímu agentovi. Po jeho schválení se pustím do implementace.