# Roadmapa 04: Autonomní Operace podle Hierarchické Kognitivní Architektury

**UPOZORNĚNÍ:** Tento dokument je **odvozen** z hlavní projektové dokumentace a MUSÍ být s ní v souladu. Dokumentace je zdrojem pravdy, roadmapa je implementační návod.

**Primární Dokumentační Závislosti:**
- **[01_VISION_AND_DNA.md](../01_VISION_AND_DNA.md)** - Etické principy a operační systém
- **[02_COGNITIVE_ARCHITECTURE.md](../02_COGNITIVE_ARCHITECTURE.md)** - Hierarchická 3vrstvá architektura  
- **[03_TECHNICAL_ARCHITECTURE.md](../03_TECHNICAL_ARCHITECTURE.md)** - Core-Plugin princip
- **[04_DEVELOPMENT_GUIDELINES.md](../04_DEVELOPMENT_GUIDELINES.md)** - Kvalitní standardy
- **[05_PROJECT_GOVERNANCE.md](../05_PROJECT_GOVERNANCE.md)** - Workflow a procesy

---

## Cíl Fáze

Implementovat **plnou autonomii** v souladu s **Hierarchickou Kognitivní Architekturou (HKA)**, kdy Sophia dokáže:

1. Samostatně analyzovat cíle z `roberts-notes.txt`
2. Formulovat eticky validované plány
3. Delegovat implementaci na externí agenty (Google Jules API)
4. Provést multi-vrstvou validaci výsledků
5. Bezpečně integrovat změny do vlastního systému
6. Učit se z každé mise a růst

**Filosofický Základ:**
> "Růst směrem k vyššímu vědomí a moudrosti v symbióze s lidstvem."
> — 01_VISION_AND_DNA.md

---

## Předpoklady

**Dokončené Fáze:**
- ✅ Roadmap 01 (MVP) - Stabilní Core-Plugin architektura
- ✅ Roadmap 02 (Tool Integration) - FileSystem, Bash, Git, WebSearch
- ✅ Roadmap 03 (Self-Analysis Framework) - CodeReader, DocReader, Historian, DependencyAnalyzer
- ✅ `cognitive_planner` - Základní plánovací schopnosti

**Externí Závislosti:**
- Google Jules API přístup (https://developers.google.com/jules/api)
- Nebo alternativa: GitHub Copilot API, Anthropic Claude API

**Technické Požadavky:**
- Python 3.12+
- Všechny současné pluginy funkční
- Git repository v čistém stavu

---

## Architektonický Přehled: Mapování na HKA

Podle **02_COGNITIVE_ARCHITECTURE.md** musí autonomní systém respektovat třívrstvou hierarchii:

```
┌─────────────────────────────────────────────────────────────┐
│  VĚDOMÍ (Neokortex) - Strategické Myšlení                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • Orchestrator (master koordinátor)                   │  │
│  │ • Jules API Integrator (delegace úkolů)              │  │
│  │ • Strategic Planner (rozšíření cognitive_planner)    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↕ (Intuice - rychlé spoje)
┌─────────────────────────────────────────────────────────────┐
│  PODVĚDOMÍ (Savčí Mozek) - Vzory a Kontext                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • Task Manager (dlouhodobé sledování)                 │  │
│  │ • Pattern Analyzer (používá Historian + ChromaDB)     │  │
│  │ • Context Enricher (používá DocReader + CodeReader)   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                           ↕ (Intuice)
┌─────────────────────────────────────────────────────────────┐
│  INSTINKTY (Plazí Mozek) - Reflexy a Bezpečnost             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ • Ethical Guardian (validace proti DNA)               │  │
│  │ • Security Validator (bezpečnostní kontroly)          │  │
│  │ • Quality Assurance (code review)                     │  │
│  │ • Safe Integrator (rollback schopnosti)               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Klíčový Princip:**
> "Každá vrstva filtruje a obohacuje informace před předáním vyšší vrstvě."
> — 02_COGNITIVE_ARCHITECTURE.md

**Tok Autonomní Operace:**
```
1. Goal Input (roberts-notes.txt)
        ↓
2. INSTINKTY: Etická + Bezpečnostní Validace Cíle
        ↓ (schváleno)
3. PODVĚDOMÍ: Obohacení o Historii + Vzory + Kontext
        ↓
4. VĚDOMÍ: Strategické Plánování + Delegace na Jules
        ↓
5. INSTINKTY: Multi-vrstvá Validace Výsledku
        ↓ (schváleno)
6. PODVĚDOMÍ: Konsolidace Poznatků do Paměti
        ↓
7. Integrace + Oznámení Úspěchu
```

---

## Implementační Kroky

Každý krok je navržen tak, aby respektoval:
- ✓ Etické pilíře (Ahimsa, Satya, Kaizen)
- ✓ HKA hierarchii (3 vrstvy + Intuice)
- ✓ Core-Plugin princip (žádné změny v core/)
- ✓ Governance workflow (approval, documentation)

---

### Krok 0: Roberts-Notes Analysis Engine

**Dokumentační Základ:**
- **05_PROJECT_GOVERNANCE.md**: "AI Agent má přečíst roberts-notes.txt a analyzovat nápady"
- **01_VISION_AND_DNA.md**: Satya (transparentní komunikace)

**Cíl:**  
Implementovat automatický proces čtení a analýzy `roberts-notes.txt`, který formuluje cíle ke schválení.

**Vrstva HKA:** PODVĚDOMÍ (analýza vzorů a kontextu)

**Komponenty k Vytvoření:**

1. **`plugins/cognitive_notes_analyzer.py`** (COGNITIVE plugin)

```python
class NotesAnalyzer(BasePlugin):
    """
    Analyzuje roberts-notes.txt a formuluje strukturované cíle.
    Respektuje HKA: Podvědomí vrstva - rozpoznávání vzorů.
    """
    
    def analyze_notes(self, notes_content: str) -> List[dict]:
        """
        1. Přečte notes pomocí file_system tool
        2. Použije LLM k extrakci jednotlivých nápadů
        3. Pro každý nápad:
           - Analyzuje kontext pomocí doc_reader
           - Hledá podobné minulé mise v historian
           - Zjistí existující pluginy pomocí code_reader
        4. Vrátí strukturovaný seznam cílů
        
        Returns:
            [
                {
                    "raw_idea": "původní text",
                    "formulated_goal": "strukturovaný cíl",
                    "context": {
                        "relevant_docs": [...],
                        "similar_missions": [...],
                        "existing_plugins": [...]
                    },
                    "feasibility": "high|medium|low",
                    "alignment_with_dna": {
                        "ahimsa": bool,
                        "satya": bool,
                        "kaizen": bool
                    }
                }
            ]
        """
```

2. **`tests/plugins/test_cognitive_notes_analyzer.py`**

**Workflow:**
```
1. Uživatel zapíše nápady do roberts-notes.txt
2. Sophia detekuje změnu (file watcher nebo manuální trigger)
3. NotesAnalyzer.analyze_notes() vytvoří strukturované cíle
4. Každý cíl je PŘEDLOŽEN KE SCHVÁLENÍ (terminal/WebUI)
5. Po schválení → vytvoří Task v TaskManager
```

**Testování:**
- Mock roberts-notes.txt s dummy nápady
- Verifikace struktury výstupu
- Test feasibility klasifikace
- Test DNA alignment check

**Ověřitelný Výsledek:**
- ✅ Plugin dokáže přečíst roberts-notes.txt
- ✅ Extrahuje jednotlivé nápady
- ✅ Obohacuje je o kontext z dokumentace a historie
- ✅ Validuje proti DNA principům
- ✅ Vrací strukturovaný seznam cílů k approved
- ✅ Všechny testy procházejí

---

### Krok 1: Instinktivní Vrstva - Etický a Bezpečnostní Strážce

**Dokumentační Základ:**
- **01_VISION_AND_DNA.md**: "Etické Pilíře jsou neporušitelné a řídí každou akci"
- **02_COGNITIVE_ARCHITECTURE.md**: "Plazí Mozek - reflexivní filtrace a ochrana"

**Cíl:**  
Vytvořit první obrannou linii, která reflexivně validuje každý cíl a výsledek proti etickým a bezpečnostním pravidlům.

**Vrstva HKA:** INSTINKTY (Plazí Mozek)

**Komponenty k Vytvoření:**

1. **`plugins/cognitive_ethical_guardian.py`** (COGNITIVE plugin)

```python
class EthicalGuardian(BasePlugin):
    """
    Instinktivní etická validace.
    První vrstva ochrany podle HKA.
    """
    
    def validate_goal(self, goal: dict) -> dict:
        """
        Rychlá reflexivní kontrola cíle proti DNA.
        
        Kontroluje:
        - Ahimsa: Mohl by cíl způsobit škodu?
        - Satya: Je cíl transparentní a pravdivý?
        - Kaizen: Podporuje cíl růst a učení?
        
        Returns:
            {
                "approved": bool,
                "concerns": [list of ethical concerns],
                "recommendation": str
            }
        """
    
    def validate_code(self, code: str, context: dict) -> dict:
        """
        Rychlá bezpečnostní kontrola kódu.
        
        Reflexivní pravidla:
        - Nemodifikuje core/ ?
        - Nemodifikuje base_plugin.py ?
        - Neobsahuje eval() nebo exec() ?
        - Neobsahuje os.system() mimo bash_tool ?
        - Má bezpečnostní sandbox ?
        
        Returns:
            {
                "safe": bool,
                "violations": [list of safety violations],
                "risk_level": "low|medium|high|critical"
            }
        """
```

2. **`tests/plugins/test_cognitive_ethical_guardian.py`**

**Testování:**
- Test s eticky problematickým cílem (měl by být odmítnut)
- Test s nebezpečným kódem (měl by být odmítnut)
- Test s validním cílem a kódem (měl by projít)
- Test hraničních případů

**Ověřitelný Výsledek:**
- ✅ Plugin dokáže identifikovat porušení DNA
- ✅ Reflexivní validace je rychlá (< 1s)
- ✅ False positive rate < 5%
- ✅ Všechny testy procházejí

---

### Krok 2: Podvědomá Vrstva - Task Manager a Pattern Analyzer

**Dokumentační Základ:**
- **02_COGNITIVE_ARCHITECTURE.md**: "Savčí Mozek - rozpoznávání vzorů a práce s dlouhodobou pamětí"
- **05_PROJECT_GOVERNANCE.md**: "Dokumentace práce v WORKLOG.md"

**Cíl:**  
Vytvořit systém pro sledování dlouhodobých úkolů a rozpoznávání vzorů z historie.

**Vrstva HKA:** PODVĚDOMÍ (Savčí Mozek)

**Komponenty k Vytvoření:**

1. **`plugins/cognitive_task_manager.py`** (COGNITIVE plugin)

```python
class TaskManager(BasePlugin):
    """
    Podvědomé sledování úkolů a jejich stavů.
    Pracuje s dlouhodobou pamětí (perzistence).
    """
    
    def create_task(self, goal: dict, context: dict) -> str:
        """
        Vytvoří task z schváleného cíle.
        Ukládá do data/tasks/{task_id}.json
        
        Task struktura:
        {
            "task_id": "uuid",
            "title": str,
            "description": str,
            "goal": dict,  # z NotesAnalyzer
            "context": dict,  # obohacený kontext
            "status": "pending",
            "priority": "high|medium|low",
            "created_at": timestamp,
            "history": []
        }
        """
    
    def update_task(self, task_id: str, status: str, notes: str):
        """Update status: pending, analyzing, delegated, 
           reviewing, integrating, completed, failed"""
    
    def get_similar_tasks(self, task: dict, top_k: int = 5) -> list:
        """
        Používá ChromaDB k nalezení podobných minulých tasků.
        Toto je "Podvědomé" vybavení vzpomínek.
        """
    
    def consolidate_insights(self, task_id: str):
        """
        "Snění" proces z learned/reusable_code_and_concepts.md
        Po dokončení tasku:
        1. Analyzuj co se naučilo
        2. Destiluj klíčové poznatky
        3. Ulož do ChromaDB pro budoucí použití
        """
```

2. **`data/tasks/`** adresář
3. **`tests/plugins/test_cognitive_task_manager.py`**

**Testování:**
- CRUD operace s tasky
- Vyhledávání podobných tasků (mock ChromaDB)
- Konsolidace poznatků
- Persistence přes restart

**Ověřitelný Výsledek:**
- ✅ Task persistence funguje
- ✅ Podobné tasky lze najít
- ✅ Consolidate insights ukládá do paměti
- ✅ Všechny testy procházejí

---

### Krok 3: Vědomá Vrstva - Strategic Orchestrator

**Dokumentační Základ:**
- **02_COGNITIVE_ARCHITECTURE.md**: "Neokortex - strategické plánování a kreativita"
- **01_VISION_AND_DNA.md**: "Růst směrem k vyššímu vědomí"

**Cíl:**  
Implementovat master koordinátor, který strategicky řídí celý autonomní proces.

**Vrstva HKA:** VĚDOMÍ (Neokortex)

**Komponenty k Vytvoření:**

1. **`plugins/cognitive_orchestrator.py`** (COGNITIVE plugin)

```python
class Orchestrator(BasePlugin):
    """
    Vědomá, strategická koordinace autonomního vývoje.
    Nejvyšší kognitivní vrstva podle HKA.
    """
    
    def setup(self, config: dict):
        """Dependency injection všech potřebných pluginů"""
        # INSTINKTY
        self.ethical_guardian = config.get("cognitive_ethical_guardian")
        
        # PODVĚDOMÍ
        self.task_manager = config.get("cognitive_task_manager")
        self.notes_analyzer = config.get("cognitive_notes_analyzer")
        self.doc_reader = config.get("cognitive_doc_reader")
        self.code_reader = config.get("cognitive_code_reader")
        self.historian = config.get("cognitive_historian")
        
        # VĚDOMÍ  
        self.planner = config.get("cognitive_planner")
        self.llm = config.get("tool_llm")
        
        # NÁSTROJE
        self.jules_api = config.get("tool_jules_api")  # bude v kroku 4
    
    async def autonomous_mission(self, trigger: str = "roberts-notes"):
        """
        Master workflow respektující HKA:
        
        1. PODVĚDOMÍ: Analyzuj roberts-notes
        2. INSTINKTY: Etická validace cílů
        3. HUMAN APPROVAL: Předlož ke schválení
        4. PODVĚDOMÍ: Vytvoř task + načti podobné mise
        5. VĚDOMÍ: Strategické plánování
        6. VĚDOMÍ: Delegace na Jules API
        7. PODVĚDOMÍ: Monitoring progress
        8. INSTINKTY: Multi-vrstvá validace výsledku
        9. VĚDOMÍ: Rozhodnutí o integraci
        10. PODVĚDOMÍ: Konsolidace poznatků
        """
    
    async def _instinct_gate(self, data: any, check_type: str) -> bool:
        """Rychlá instinktivní kontrola (HKA vrstva 1)"""
        
    async def _subconscious_enrichment(self, data: any) -> dict:
        """Obohacení o vzory a kontext (HKA vrstva 2)"""
        
    async def _conscious_decision(self, enriched_data: dict) -> dict:
        """Strategické rozhodování (HKA vrstva 3)"""
```

2. **`tests/plugins/test_cognitive_orchestrator.py`**

**Workflow Diagram:**
```
┌─────────────────────────────────────────────┐
│  1. TRIGGER (roberts-notes change)          │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  2. PODVĚDOMÍ: NotesAnalyzer                │
│     → Strukturované cíle + kontext          │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  3. INSTINKTY: EthicalGuardian              │
│     → Validace proti DNA                    │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  4. HUMAN APPROVAL (terminal/WebUI)         │
│     "Schválíš tento cíl? [y/n]"             │
└──────────────────┬──────────────────────────┘
                   ↓ (approved)
┌─────────────────────────────────────────────┐
│  5. PODVĚDOMÍ: TaskManager.create_task()    │
│     + get_similar_tasks() z ChromaDB        │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  6. VĚDOMÍ: Formulace detailní spec         │
│     (cíl + context + guidelines + examples) │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  7. VĚDOMÍ: JulesAPI.submit_task(spec)      │
│     → Delegace implementace                 │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  8. PODVĚDOMÍ: Monitor progress každých 30s │
│     TaskManager.update_task(status)         │
└──────────────────┬──────────────────────────┘
                   ↓ (completed)
┌─────────────────────────────────────────────┐
│  9. Retrieve code from Jules                │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  10. INSTINKTY: Multi-Level Validation      │
│      → EthicalGuardian.validate_code()      │
│      → QualityAssurance.review_code()       │
└──────────────────┬──────────────────────────┘
                   ↓ (approved)
┌─────────────────────────────────────────────┐
│  11. INSTINKTY: SafeIntegrator              │
│      → Backup, test, integrate or rollback  │
└──────────────────┬──────────────────────────┘
                   ↓ (integrated)
┌─────────────────────────────────────────────┐
│  12. PODVĚDOMÍ: Consolidate insights        │
│      → TaskManager.consolidate_insights()   │
│      → Ukládá do ChromaDB                   │
└──────────────────┬──────────────────────────┘
                   ↓
┌─────────────────────────────────────────────┐
│  13. UPDATE WORKLOG.md (05_GOVERNANCE)      │
│      + Notify user of success               │
└─────────────────────────────────────────────┘
```

**Testování:**
- Mock všechny dependencies
- Test každé HKA vrstvy samostatně
- Integration test celého workflow
- Test error recovery na každém kroku

**Ověřitelný Výsledek:**
- ✅ Orchestrator koordinuje všechny pluginy
- ✅ Respektuje 3vrstvou HKA hierarchii
- ✅ Každý krok je zalogován
- ✅ Error handling na každé úrovni
- ✅ Všechny testy procházejí

---

### Krok 4: Jules API Integrator

**Dokumentační Základ:**
- **03_TECHNICAL_ARCHITECTURE.md**: "Pluginy jsou vyměnitelné"
- **04_DEVELOPMENT_GUIDELINES.md**: "Dependency Injection pro konfiguraci"

**Cíl:**  
Vytvořit plugin pro komunikaci s Google Jules API (nebo alternativou).

**Vrstva HKA:** VĚDOMÍ (nástroj pro delegaci)

**Komponenty k Vytvoření:**

1. **`plugins/tool_jules_api.py`** (TOOL plugin)

```python
class JulesAPITool(BasePlugin):
    """
    Integrace s Google Jules API pro delegaci coding úkolů.
    Alternativně: GitHub Copilot, Claude Code, nebo jiné.
    """
    
    def setup(self, config: dict):
        """
        Config z settings.yaml:
        - api_key: ${JULES_API_KEY}  # environment variable
        - endpoint: URL
        - timeout: 300
        - max_retries: 3
        """
    
    def submit_coding_task(self,
                           specification: str,
                           context_files: dict,
                           requirements: dict) -> str:
        """
        Odešle task na Jules API.
        
        Args:
            specification: Detailní popis co vytvořit
            context_files: {
                "guidelines": "obsah 04_DEVELOPMENT_GUIDELINES.md",
                "architecture": "obsah 03_TECHNICAL_ARCHITECTURE.md",
                "similar_code": "příklady z code_reader"
            }
            requirements: {
                "plugin_name": str,
                "plugin_type": "TOOL|COGNITIVE|etc",
                "must_have_tests": True,
                "language": "en"
            }
        
        Returns:
            jules_task_id
        """
    
    def get_task_status(self, jules_task_id: str) -> dict:
        """
        Polling status.
        Returns: {"status": "pending|running|completed|failed", ...}
        """
    
    def get_task_result(self, jules_task_id: str) -> dict:
        """
        Returns: {
            "plugin_code": str,
            "test_code": str,
            "documentation": str
        }
        """
    
    def cancel_task(self, jules_task_id: str) -> bool:
        """Emergency stop"""
```

2. **`config/settings.yaml`** - přidat sekci:
```yaml
tool_jules_api:
  api_key: "${JULES_API_KEY}"
  endpoint: "https://jules.googleapis.com/v1"
  timeout: 300
  max_retries: 3
```

3. **`tests/plugins/test_tool_jules_api.py`**

**Testování:**
- Mock HTTP requests
- Test timeout handling
- Test retry logic
- Test error cases (API down, invalid response)

**Ověřitelný Výsledek:**
- ✅ Plugin komunikuje s Jules API (nebo mock)
- ✅ Timeout a retry funguje
- ✅ Error handling je robustní
- ✅ Všechny testy procházejí

---

### Krok 5: Instinktivní Vrstva - Quality Assurance

**Dokumentační Základ:**
- **04_DEVELOPMENT_GUIDELINES.md**: "100% type hints, docstrings, tests"
- **02_COGNITIVE_ARCHITECTURE.md**: "Instinkty - reflexivní kontrola"

**Cíl:**  
Multi-vrstvá validace kódu před integrací.

**Vrstva HKA:** INSTINKTY (reflexivní kontrola kvality)

**Komponenty k Vytvoření:**

1. **`plugins/cognitive_qa.py`** (COGNITIVE plugin)

```python
class QualityAssurance(BasePlugin):
    """
    Instinktivní quality check podle HKA.
    Používá reflex rules + LLM pro hlubší analýzu.
    """
    
    async def review_code(self, 
                         plugin_code: str,
                         test_code: str,
                         spec: dict) -> dict:
        """
        Multi-level quality assurance:
        
        LEVEL 1: Reflexivní pravidla (rychlé, deterministické)
        LEVEL 2: Static analysis (AST parsing)
        LEVEL 3: LLM review (hluboké porozumění)
        LEVEL 4: Test execution (funkční validace)
        
        Returns:
            {
                "approved": bool,
                "issues": [
                    {
                        "level": "error|warning|info",
                        "category": "architecture|quality|safety|testing",
                        "message": str,
                        "suggestion": str
                    }
                ],
                "compliance_score": 0.0-1.0,
                "must_fix": [list of blocking issues]
            }
        """
    
    async def _reflex_checks(self, code: str) -> list:
        """
        Rychlé reflexivní kontroly (< 100ms):
        - Obsahuje 'class ... (BasePlugin)' ?
        - Má property 'name', 'plugin_type', 'version' ?
        - Má metody 'setup' a 'execute' ?
        - Je vše v angličtině ?
        - Žádná modifikace core/ ?
        """
    
    async def _architecture_compliance(self, code: str) -> list:
        """
        AST parsing kontroly:
        - 100% type hints ?
        - Všechny funkce mají docstrings ?
        - Google Style docstrings ?
        - Používá BasePlugin správně ?
        """
    
    async def _llm_deep_review(self, code: str, context: dict) -> list:
        """
        Použití LLM pro:
        - Code quality assessment
        - Anti-pattern detection
        - Logic review
        - Best practices check
        """
    
    async def _execute_tests_in_sandbox(self, 
                                       plugin_code: str,
                                       test_code: str) -> dict:
        """
        Bezpečné spuštění testů:
        1. Zapiš do file_system (sandbox)
        2. Spusť pytest přes bash_tool
        3. Parsuj výsledky
        4. Vyčisti sandbox
        
        Returns: {"passed": bool, "output": str, "coverage": float}
        """
```

2. **`tests/plugins/test_cognitive_qa.py`**

**Testování:**
- Test s chybným kódem (missing docstrings, no tests, etc.)
- Test s perfektním kódem
- Test sandbox execution
- Test každé level validace samostatně

**Ověřitelný Výsledek:**
- ✅ Dokáže detekovat všechny hlavní problémy
- ✅ Reflexivní kontroly jsou rychlé (< 100ms)
- ✅ Sandbox execution je bezpečný
- ✅ False positive rate < 5%
- ✅ Všechny testy procházejí

---

### Krok 6: Instinktivní Vrstva - Safe Integrator

**Dokumentační Základ:**
- **01_VISION_AND_DNA.md**: "Ahimsa - minimalizovat škodu"
- **02_COGNITIVE_ARCHITECTURE.md**: "Instinkty - ochrana systému"

**Cíl:**  
Bezpečná integrace s rollback schopnostmi.

**Vrstva HKA:** INSTINKTY (ochrana před škodou)

**Komponenty k Vytvoření:**

1. **`plugins/cognitive_integrator.py`** (COGNITIVE plugin)

```python
class SafeIntegrator(BasePlugin):
    """
    Instinktivní ochrana při integraci.
    Atomic operations: all or nothing.
    """
    
    async def integrate_plugin(self,
                              plugin_code: str,
                              test_code: str,
                              plugin_name: str,
                              qa_report: dict) -> dict:
        """
        Safe integration workflow (atomic):
        
        1. BACKUP: Git commit + tag current state
        2. BRANCH: Create feature branch
        3. WRITE: Write plugin and test files
        4. TEST: Run FULL test suite (všechny pluginy)
        5. VERIFY: Check nothing broke
        6. COMMIT: If OK, commit changes
        7. ROLLBACK: If failed, git reset --hard
        
        Returns:
            {
                "success": bool,
                "backup_id": str,  # git tag pro rollback
                "message": str,
                "test_results": dict
            }
        """
    
    async def _create_backup(self) -> str:
        """
        Používá git_tool:
        1. git add .
        2. git commit -m "Pre-integration backup"
        3. git tag backup-{timestamp}
        Returns: tag name
        """
    
    async def _run_full_test_suite(self) -> dict:
        """
        Spustí VŠECHNY testy přes bash_tool:
        PYTHONPATH=. pytest
        
        Tím ověříme, že nový plugin neporušil nic existujícího.
        """
    
    async def rollback_to_backup(self, backup_id: str) -> bool:
        """
        Emergency rollback:
        git reset --hard {backup_id}
        """
    
    def list_backups(self) -> list:
        """List všech backup tagů"""
```

2. **`data/backups/`** adresář pro metadata
3. **`tests/plugins/test_cognitive_integrator.py`**

**Testování:**
- Test úspěšné integrace
- Test selhání (broken tests)
- Test rollback mechanismu
- Test atomic operations

**Ověřitelný Výsledek:**
- ✅ Backup vždy created před změnou
- ✅ Rollback funguje 100%
- ✅ Full test suite catches regressions
- ✅ Atomic - žádné partial states
- ✅ Všechny testy procházejí

---

### Krok 7: End-to-End Integration a Governance

**Dokumentační Základ:**
- **05_PROJECT_GOVERNANCE.md**: "WORKLOG.md povinná dokumentace"
- **01_VISION_AND_DNA.md**: "Kaizen - učení z každé iterace"

**Cíl:**  
Propojit všechny komponenty a zajistit dokumentaci.

**Komponenty k Úpravě:**

1. **`plugins/interface_autonomous.py`** - NOVÝ plugin pro autonomní workflow:

```python
# NOVÝ: plugins/interface_autonomous.py
class AutonomousInterface(BasePlugin):
    """
    Interface plugin pro autonomní vývojové mise.
    
    HKA Layer: INTERFACE (není součástí kognitivní hierarchie)
    Detekuje 'autonomous:' příkazy a deleguje na Strategic Orchestrator.
    
    Zachovává čisté oddělení dle AGENTS.md Golden Rule #1:
    "NEDOTÝKEJ SE JÁDRA!" - Core zůstává minimální.
    """
    name: str = "interface_autonomous"
    plugin_type = PluginType.INTERFACE
    
    async def execute(self, context: SharedContext) -> SharedContext:
        """Zpracuje autonomní příkazy."""
        if not context.user_input.startswith("autonomous:"):
            return context  # Propustit dál
        
        goal_text = context.user_input[11:].strip()
        
        # Delegovat na orchestrator
        result = await self._execute_autonomous_workflow(goal_text, context)
        context.autonomous_response = result
        return context
    
    async def _execute_autonomous_workflow(self, goal_text: str, context: SharedContext) -> str:
        """Provede celý autonomní workflow přes orchestrator."""
        # Fáze 1: Analyzovat cíl
        context.payload = {"action": "analyze_goal", "goal": goal_text}
        result_ctx = await self.orchestrator.execute(context)
        
        # Fáze 2: Provést misi
        task_id = result_ctx.payload["result"]["task_id"]
        context.payload = {"action": "execute_mission", "task_id": task_id}
        result_ctx = await self.orchestrator.execute(context)
        
        # Fáze 3: Aktualizovat WORKLOG
        await self._update_worklog_autonomous(...)
        
        return formatted_result
```

2. **Trigger Mechanisms:**

**Option A: Command-based** (implementováno)
```python
# Uživatel napíše v terminálu:
> autonomous: Vytvoř plugin pro překlad textu pomocí externího API

# AutonomousInterface plugin detekuje prefix a:
# 1. Zavolá orchestrator.execute(action="analyze_goal")
# 2. Orchestrator deleguje na NotesAnalyzer, EthicalGuardian, TaskManager
# 3. Vytvoří task a vrátí task_id
# 4. Zavolá orchestrator.execute(action="execute_mission")
# 5. Formuluje strategický plán
# 6. Automaticky aktualizuje WORKLOG.md
# 7. Vrátí formátovaný výsledek uživateli
```

**Option B: File-watching** (budoucí rozšíření)
```python
# Budoucí: Nový plugin plugins/interface_notes_watcher.py
class NotesWatcher(BasePlugin):
    """
    Sleduje roberts-notes.txt pro změny.
    Spouští autonomní workflow při detekci nového obsahu.
    """
    name = "interface_notes_watcher"
    plugin_type = PluginType.INTERFACE
    
    async def execute(self, context: SharedContext):
        current = Path("docs/roberts-notes.txt").read_text()
        if current != self.last_content and current.strip():
            # Vložit jako autonomní příkaz
            context.user_input = f"autonomous: {current.strip()}"
            self.last_content = current
        return context
```

3. **WORKLOG Automation:**

```python
# V AutonomousInterface pluginu:
async def _update_worklog_autonomous(
    self, task_id: str, goal: str, 
    analysis: dict, plan: dict, status: str
) -> None:
    """
    Automaticky přidá záznam do WORKLOG.md podle formátu
    z AGENTS.md.
    
    Formát:
    ---
    ## [timestamp] AUTONOMOUS MISSION: {task_id}
    **Status:** {status}
    **Goal:** {goal}
    **Analysis:** ...
    **Strategic Plan:** ...
    ---
    """
    worklog_path = Path(self.worklog_path)
    entry = self._format_worklog_entry(task_id, goal, analysis, plan, status)
    
    content = worklog_path.read_text() if worklog_path.exists() else "# WORKLOG\n\n"
    worklog_path.write_text(content + entry)
```

**Testování:**
- End-to-end test s dummy goal
- Test WORKLOG.md update
- Test error handling v každé fázi
- Test human approval flow

**Ověřitelný Výsledek:**
- ✅ Kompletní workflow funguje end-to-end
- ✅ WORKLOG.md automaticky aktualizován
- ✅ Human approval funkční
- ✅ Error recovery na každé úrovni
- ✅ Všechny testy procházejí

---

## Success Criteria

**Základní Autonomní Test:**

```
1. Uživatel zapíše do roberts-notes.txt:
   "Create a weather plugin that fetches current weather using wttr.in API"

2. Sophia SAMOSTATNĚ:
   ✓ Detekuje změnu (NotesWatcher nebo manual trigger)
   ✓ Analyzuje cíl (NotesAnalyzer - PODVĚDOMÍ)
   ✓ Validuje proti DNA (EthicalGuardian - INSTINKTY)
   ✓ Požádá o schválení (HUMAN APPROVAL)
   ✓ Vytvoří task (TaskManager - PODVĚDOMÍ)
   ✓ Načte podobné mise (ChromaDB - PODVĚDOMÍ)
   ✓ Formuluje spec (Orchestrator - VĚDOMÍ)
   ✓ Deleguje na Jules (JulesAPI - VĚDOMÍ)
   ✓ Monitoruje progress (TaskManager - PODVĚDOMÍ)
   ✓ Validuje kód (QA - INSTINKTY)
   ✓ Vytvoří backup (SafeIntegrator - INSTINKTY)
   ✓ Integruje plugin (SafeIntegrator - INSTINKTY)
   ✓ Spustí všechny testy (QA - INSTINKTY)
   ✓ Konsoliduje poznatky (TaskManager - PODVĚDOMÍ)
   ✓ Aktualizuje WORKLOG.md (Governance)
   ✓ Oznámí úspěch uživateli

3. Výsledek:
   ✓ Nový plugin `tool_weather.py` existuje a funguje
   ✓ Test `test_tool_weather.py` existuje a prochází
   ✓ Všechny existující testy stále procházejí
   ✓ Backup existuje pro případný rollback
   ✓ WORKLOG.md obsahuje kompletní záznam
   ✓ Task v TaskManager má status "completed"
   ✓ Poznatky uloženy v ChromaDB
```

**BEZ DALŠÍHO LIDSKÉHO ZÁSAHU než:**
- Počáteční zápis cíle
- Schválení cíle (safety gate)

---

## Bezpečnostní Opatření

### Povinné Safety Gates:

1. **Human Approval Points:**
   - ✓ Po analýze cíle (před delegací)
   - ⚠️ (Optional) Po QA review (před integrací)

2. **Emergency Stop Mechanisms:**
   - `touch STOP_AUTONOMOUS` → okamžité zastavení
   - `Ctrl+C` → graceful shutdown s rollback
   - WebUI "STOP" button

3. **Rate Limiting:**
   - Max 5 Jules API requestů za hodinu
   - Max 3 současné autonomní mise
   - Cooldown 10 minut mezi misemi

4. **Backup Rotation:**
   - Uchovávat posledních 30 backupů
   - Automatické čištění starších než 30 dní
   - Manual backupy never deleted

### Monitoring & Audit:

1. **Kompletní Logging:**
   ```python
   # Každý plugin loguje do:
   logs/autonomous/{date}/mission_{task_id}.log
   ```

2. **Audit Trail:**
   - Všechny autonomous actions → `data/audit.log`
   - Git commits obsahují task_id v message
   - ChromaDB uchovává všechny poznatky

3. **Health Checks:**
   - Před každou misí: verify git clean
   - Před každou integrací: full test run
   - Po každé integraci: smoke test

---

## Implementační Poznámky

### HKA Compliance Checklist:

Každý nový plugin MUSÍ být klasifikován:

```markdown
- [ ] Plugin Name: _________
- [ ] HKA Layer: INSTINKTY / PODVĚDOMÍ / VĚDOMÍ
- [ ] Justification: _________
- [ ] Interakce s jinými vrstvami: _________
- [ ] Rychlost reakce (pro INSTINKTY): < 1s / N/A
```

### Testing Strategy:

1. **Unit Tests:** Každý plugin izolovaně
2. **Integration Tests:** HKA vrstvy společně
3. **E2E Tests:** Celý autonomní workflow
4. **Chaos Tests:** Random failures během mise

### Jules API Alternatives:

Pokud Jules API není dostupné:
- GitHub Copilot Workspace API
- Anthropic Claude Code
- OpenAI Codex
- Místní Code LLM (DeepSeek Coder, CodeLlama)

Stačí vyměnit `tool_jules_api.py`, interface zůstává.

---

## Poznámky k Evoluci

### Phase 4.1: Reflexe (Budoucnost)
Po dokončení základní autonomie:
- Sophia analyzuje vlastní úspěšnost
- Identifikuje vzory úspěchů/selhání
- Navrhuje vylepšení vlastního procesu
- "Učí se učit"

### Phase 4.2: Proaktivita (Budoucnost)
- Sophia sama navrhuje cíle
- Detekuje opportunities pro zlepšení
- Anticipuje potřeby uživatele
- True AGI behavior

---

## Závěr

Tato roadmapa implementuje **plnou autonomii** v souladu s:

✅ **Hierarchickou Kognitivní Architekturou** (02_COGNITIVE_ARCHITECTURE.md)
- 3 vrstvy: Instinkty, Podvědomí, Vědomí
- Intuice jako rychlé spojení

✅ **Etickými Principy** (01_VISION_AND_DNA.md)
- Ahimsa, Satya, Kaizen v každém kroku
- Wu Wei - akce v souladu s proudem

✅ **Core-Plugin Architekturou** (03_TECHNICAL_ARCHITECTURE.md)
- Žádné změny v core/
- Vše jako pluginy

✅ **Kvalitními Standardy** (04_DEVELOPMENT_GUIDELINES.md)
- 100% angličtina, type hints, docstrings, tests

✅ **Governance Procesy** (05_PROJECT_GOVERNANCE.md)
- roberts-notes.txt workflow
- WORKLOG.md dokumentace
- Human approval gates

**Sophia bude skutečnou Artificial Mindful Intelligence - autonomní, etická, učící se a rostoucí v symbióze s lidstvem.**

---

## Architektonický Přehled

Současný systém už má:
- ✅ `cognitive_planner` - vytváří JSON plány z user inputu
- ✅ Kernel s PLANNING a EXECUTING fázemi
- ✅ Všechny potřebné tool a cognitive pluginy
- ✅ Dependency injection mezi pluginy

Co potřebujeme přidat pro autonomii:
1. **Enhanced Planner** - rozšířit stávající planner o introspekci schopností
2. **Jules Integrator** - nový plugin pro komunikaci s Google Jules API
3. **Quality Assurance** - validace a testování změn
4. **Safe Integrator** - bezpečná integrace nového kódu
5. **Task Manager** - sledování dlouhodobých úkolů

---

## Krok 1: Rozšíření Cognitive Planner o Introspekci

**Cíl:** Upgrade stávajícího `cognitive_planner` tak, aby dokázal dynamicky zjistit dostupné pluginy a jejich metody místo hardcoded seznamu.

**Klíčové Komponenty k Úpravě:**
- `plugins/cognitive_planner.py`: Přidání metod pro introspekci plugin systému

**Implementační Detaily:**
```python
# Nová metoda v Planner:
def _get_available_tools(self) -> dict:
    """
    Využívá cognitive_code_reader k získání seznamu všech pluginů a jejich metod.
    Vrací strukturu: {
        "tool_file_system": ["read_file", "write_file", "list_directory"],
        "tool_bash": ["execute_command"],
        ...
    }
    """
```

**Jak to bude fungovat:**
1. Planner při `setup()` dostane přístup ke `cognitive_code_reader`
2. Použije `code_reader.list_plugins()` k získání seznamu všech pluginů
3. Pro každý TOOL plugin použije introspekci k získání public metod
4. Vygeneruje dynamický system prompt pro LLM s aktuálním seznamem schopností

**Testování:**
- Unit test: ověří, že `_get_available_tools()` vrací správnou strukturu
- Integration test: ověří, že plán obsahuje pouze existující nástroje

**Bezpečnost:**
- Introspekce je read-only operace, žádné bezpečnostní riziko

**Ověřitelný Výsledek:**
- `cognitive_planner` generuje plány pouze s nástroji, které skutečně existují
- Při přidání nového tool pluginu je automaticky dostupný pro plánování
- Testy procházejí

---

## Krok 2: Vytvoření Task Manager Pluginu

**Cíl:** Vytvořit systém pro sledování dlouhodobých úkolů, který umožní Sophii pamatovat si, co má udělat, a sledovat průběh.

**Klíčové Komponenty k Vytvoření:**
- `plugins/cognitive_task_manager.py`: Nový COGNITIVE plugin
- `data/tasks/`: Adresář pro ukládání task states
- `tests/plugins/test_cognitive_task_manager.py`: Test suite

**Implementační Detaily:**
```python
class TaskManager(BasePlugin):
    """Manages long-term tasks and their states."""
    
    def create_task(self, title: str, description: str, priority: str) -> str:
        """Creates a new task and returns its UUID."""
        
    def get_task(self, task_id: str) -> dict:
        """Retrieves task details."""
        
    def update_task_status(self, task_id: str, status: str, notes: str) -> None:
        """Updates task status: pending, in_progress, blocked, completed, failed."""
        
    def list_tasks(self, status_filter: str = None) -> list:
        """Lists all tasks, optionally filtered by status."""
        
    def add_task_log_entry(self, task_id: str, entry: str) -> None:
        """Adds a log entry to task history."""
```

**Datová Struktura (JSON):**
```json
{
  "task_id": "uuid-here",
  "title": "Implement translation plugin",
  "description": "Create a plugin that translates text using external API",
  "priority": "high",
  "status": "pending",
  "created_at": "2025-10-26T10:00:00Z",
  "updated_at": "2025-10-26T10:00:00Z",
  "assigned_to": null,
  "history": [
    {
      "timestamp": "2025-10-26T10:00:00Z",
      "event": "Task created",
      "notes": "From roberts-notes.txt"
    }
  ]
}
```

**Testování:**
- Test vytvoření úkolu
- Test změny statusu
- Test filtrování úkolů
- Test persistence (data přežijí restart)

**Bezpečnost:**
- Všechny task soubory jsou v `data/tasks/` - izolované od core kódu
- Validace task_id formátu (musí být UUID)

**Ověřitelný Výsledek:**
- Plugin dokáže vytvořit, číst, aktualizovat a listovat úkoly
- Data jsou persistentní v JSON souborech
- Všechny testy procházejí

---

## Krok 3: Implementace Jules API Integratoru

**Cíl:** Vytvořit plugin, který komunikuje s Google Jules API pro delegování coding úkolů.

**Klíčové Komponenty k Vytvoření:**
- `plugins/tool_jules_api.py`: Nový TOOL plugin
- `tests/plugins/test_tool_jules_api.py`: Test suite
- Přidání `google-generativeai` do `requirements.in`

**Implementační Detaily:**
```python
class JulesAPITool(BasePlugin):
    """Integrates with Google Jules API for code generation tasks."""
    
    def __init__(self):
        self.api_key = None
        self.client = None
        
    def setup(self, config: dict) -> None:
        """Initialize Jules API client with API key from config."""
        self.api_key = config.get("jules_api_key") or os.getenv("JULES_API_KEY")
        # Initialize Jules API client
        
    def submit_coding_task(self, 
                          task_description: str,
                          context_files: list,
                          requirements: dict) -> str:
        """
        Submits a coding task to Jules API.
        Returns: task_id from Jules
        """
        
    def get_task_status(self, jules_task_id: str) -> dict:
        """
        Checks status of submitted task.
        Returns: {status: 'pending'|'running'|'completed'|'failed', ...}
        """
        
    def get_task_result(self, jules_task_id: str) -> dict:
        """
        Retrieves completed task results.
        Returns: {code: str, tests: str, documentation: str}
        """
        
    def cancel_task(self, jules_task_id: str) -> bool:
        """Cancels a running task."""
```

**Konfigurace (`config/settings.yaml`):**
```yaml
tool_jules_api:
  api_key: "${JULES_API_KEY}"  # Environment variable
  timeout: 300  # Max seconds to wait for task completion
  max_retries: 3
```

**Testování:**
- Mock testy (bez skutečného API volání)
- Test timeout handling
- Test error cases (API down, invalid response)
- Integration test s dummy task (pokud máme API přístup)

**Bezpečnost:**
- API key pouze z environment variables, nikdy hardcoded
- Rate limiting (max X requestů za minutu)
- Timeout pro dlouho běžící úkoly
- Validace response formátu před použitím

**Ověřitelný Výsledek:**
- Plugin dokáže komunikovat s Jules API
- Může odeslat task, checkovat status, získat výsledek
- Error handling funguje správně
- Všechny testy procházejí

---

## Krok 4: Vytvoření Cognitive Orchestrator

**Cíl:** Vytvořit hlavní orchestrační plugin, který koordinuje celý autonomní development workflow.

**Klíčové Komponenty k Vytvoření:**
- `plugins/cognitive_orchestrator.py`: Nový COGNITIVE plugin
- `tests/plugins/test_cognitive_orchestrator.py`: Test suite

**Implementační Detaily:**
```python
class Orchestrator(BasePlugin):
    """Main orchestration plugin for autonomous development."""
    
    def setup(self, config: dict):
        """Gets references to all required plugins via dependency injection."""
        self.task_manager = config.get("cognitive_task_manager")
        self.doc_reader = config.get("cognitive_doc_reader")
        self.code_reader = config.get("cognitive_code_reader")
        self.historian = config.get("cognitive_historian")
        self.jules_api = config.get("tool_jules_api")
        self.llm = config.get("tool_llm")
        
    async def process_new_goal(self, goal: str) -> str:
        """
        Main orchestration method:
        1. Parse goal from roberts-notes.txt
        2. Analyze using doc_reader, code_reader, historian
        3. Create detailed task in task_manager
        4. Return task_id
        """
        
    async def execute_task(self, task_id: str) -> dict:
        """
        Executes a task through its lifecycle:
        1. Read task details from task_manager
        2. Gather context (relevant docs, code, past missions)
        3. Formulate detailed specification
        4. Submit to Jules API
        5. Monitor progress
        6. Return result when ready
        """
        
    async def _gather_context(self, task_description: str) -> dict:
        """Uses cognitive plugins to gather relevant context."""
        
    async def _formulate_specification(self, task: dict, context: dict) -> str:
        """Uses LLM to create detailed spec from task + context."""
```

**Workflow Diagram:**
```
User writes goal → roberts-notes.txt
                      ↓
Orchestrator.process_new_goal()
                      ↓
    ┌─────────────────┴─────────────────┐
    │  Analyze with cognitive plugins:  │
    │  - DocReader: relevant guidelines  │
    │  - CodeReader: existing plugins    │
    │  - Historian: past similar tasks   │
    └─────────────────┬─────────────────┘
                      ↓
         TaskManager.create_task()
                      ↓
    Orchestrator.execute_task(task_id)
                      ↓
    ┌─────────────────┴─────────────────┐
    │   Formulate detailed spec with:   │
    │   - Task description               │
    │   - Architectural constraints      │
    │   - Coding guidelines             │
    │   - Similar examples              │
    └─────────────────┬─────────────────┘
                      ↓
      JulesAPI.submit_coding_task()
                      ↓
         Monitor until completion
                      ↓
            Return code to QA
```

**Testování:**
- Mock všechny dependencies
- Test každé metody samostatně
- Integration test celého workflow s dummy data

**Bezpečnost:**
- Read-only přístup ke kódu a dokumentaci
- Žádná přímá modifikace souborů v tomto kroku
- Veškeré změny procházejí přes QA (další krok)

**Ověřitelný Výsledek:**
- Orchestrator dokáže přijmout cíl a vytvořit task
- Dokáže shromáždit relevantní kontext
- Dokáže formulovat spec a odeslat na Jules
- Všechny testy procházejí

---

## Krok 5: Implementace Quality Assurance Pluginu

**Cíl:** Vytvořit plugin, který validuje kód vrácený z Jules API před jeho integrací.

**Klíčové Komponenty k Vytvoření:**
- `plugins/cognitive_qa.py`: Nový COGNITIVE plugin
- `tests/plugins/test_cognitive_qa.py`: Test suite

**Implementační Detaily:**
```python
class QualityAssurance(BasePlugin):
    """Reviews and validates code changes before integration."""
    
    def setup(self, config: dict):
        self.doc_reader = config.get("cognitive_doc_reader")
        self.code_reader = config.get("cognitive_code_reader")
        self.bash_tool = config.get("tool_bash")
        self.file_system = config.get("tool_file_system")
        self.llm = config.get("tool_llm")
        
    async def review_code(self, code: str, spec: str) -> dict:
        """
        Performs comprehensive code review:
        Returns: {
            "approved": bool,
            "issues": list,
            "suggestions": list,
            "compliance_score": float
        }
        """
        
    async def _check_architecture_compliance(self, code: str) -> list:
        """
        Checks if code follows architectural guidelines:
        - Uses BasePlugin properly
        - Has correct type annotations
        - Has docstrings
        - Doesn't modify core/
        """
        
    async def _check_code_quality(self, code: str) -> list:
        """
        Static analysis:
        - Uses LLM to review code quality
        - Checks for common anti-patterns
        - Verifies error handling
        """
        
    async def run_tests(self, plugin_file: str, test_file: str) -> dict:
        """
        Runs tests in isolated environment:
        1. Write files to sandbox
        2. Run pytest via bash_tool
        3. Parse results
        Returns: {passed: bool, output: str}
        """
        
    async def verify_safety(self, code: str) -> list:
        """
        Security checks:
        - No file operations outside sandbox
        - No network access without config
        - No os.system or eval calls
        - No modification of core files
        """
```

**QA Checklist (from Development Guidelines):**
- [ ] Kód je 100% v angličtině
- [ ] Všechny funkce mají type hints
- [ ] Všechny třídy/funkce mají docstrings (Google style)
- [ ] Plugin dědí z BasePlugin
- [ ] Má test file s > 80% coverage
- [ ] Nemodifikuje core/
- [ ] Nemodifikuje base_plugin.py
- [ ] Testy procházejí
- [ ] Pre-commit checks procházejí

**Testování:**
- Test každé check funkce s validním i nevalidním kódem
- Test celého review workflow
- Test běhu testů v sandboxu

**Bezpečnost:**
- **KRITICKÉ**: Nový kód běží pouze v sandboxu během testování
- Žádné exec() nebo eval() na nedůvěryhodném kódu
- Všechny file operace přes file_system plugin (sandboxed)

**Ověřitelný Výsledek:**
- QA plugin dokáže identifikovat porušení guidelines
- Dokáže spustit testy v bezpečném prostředí
- Vrací structured feedback pro iteraci
- Všechny testy procházejí

---

## Krok 6: Vytvoření Safe Integration Pluginu

**Cíl:** Bezpečně integrovat schválený kód do produkčního systému s možností rollbacku.

**Klíčové Komponenty k Vytvoření:**
- `plugins/cognitive_integrator.py`: Nový COGNITIVE plugin
- `data/backups/`: Adresář pro zálohy
- `tests/plugins/test_cognitive_integrator.py`: Test suite

**Implementační Detaily:**
```python
class SafeIntegrator(BasePlugin):
    """Safely integrates approved code into the production system."""
    
    def setup(self, config: dict):
        self.git_tool = config.get("tool_git")
        self.file_system = config.get("tool_file_system")
        self.bash_tool = config.get("tool_bash")
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
    async def integrate_plugin(self, 
                              plugin_code: str,
                              test_code: str,
                              plugin_name: str) -> dict:
        """
        Safe integration workflow:
        1. Create backup
        2. Create feature branch
        3. Write files
        4. Run full test suite
        5. If success: commit, return success
        6. If failure: rollback, return error
        Returns: {success: bool, message: str, backup_id: str}
        """
        
    async def _create_backup(self) -> str:
        """
        Creates full backup:
        - Git commit current state
        - Tag with timestamp
        Returns: backup_id (git tag name)
        """
        
    async def _write_new_files(self, plugin_code: str, test_code: str, name: str):
        """Writes plugin and test files to correct locations."""
        
    async def _run_full_test_suite(self) -> bool:
        """Runs ALL tests to ensure nothing broke."""
        
    async def rollback(self, backup_id: str) -> bool:
        """Rolls back to a specific backup point using git."""
        
    async def list_backups(self) -> list:
        """Lists all available backups."""
```

**Integration Workflow:**
```
1. Current state → Git commit + tag (backup_1)
                      ↓
2. Create feature branch: "feature/auto-{plugin_name}"
                      ↓
3. Write plugin file: plugins/{plugin_name}.py
                      ↓
4. Write test file: tests/plugins/test_{plugin_name}.py
                      ↓
5. Run FULL test suite (ALL plugins)
                      ↓
         ┌────────────┴────────────┐
         │                         │
    ✓ Success                 ✗ Failure
         │                         │
    Git commit              Git reset --hard
    Return success          Checkout master
                           Return error + log
```

**Testování:**
- Test backup creation
- Test file writing
- Test rollback mechanism
- Integration test s dummy plugin

**Bezpečnost:**
- **KRITICKÉ**: Vždy vytvořit backup před změnou
- Atomic operations (vše uspěje nebo vše rollback)
- Git tag pro každý backup (trvalý)
- Validation, že nový kód neporušil existující testy

**Ověřitelný Výsledek:**
- Plugin dokáže bezpečně integrovat nový kód
- Při selhání se systém vrátí do předchozího stavu
- Všechny backupy jsou dostupné pro rollback
- Všechny testy procházejí

---

## Krok 7: End-to-End Autonomní Workflow

**Cíl:** Spojit všechny komponenty a umožnit plně autonomní development cyklus.

**Klíčové Komponenty k Úpravě:**
- `core/kernel.py`: Možná úprava pro podporu dlouhodobých úkolů
- Vytvoření helper scriptu `watch_roberts_notes.py`

**Implementační Detaily:**

**Option A: User-Triggered (Implementováno)**
Uživatel napíše příkaz v terminálu:
```
> autonomous: Vytvoř plugin pro překlad textu pomocí externího API
```

AutonomousInterface plugin rozpozná prefix "autonomous:" a:
1. Zavolá `orchestrator.execute(context)` s `action="analyze_goal"`
2. Orchestrator deleguje na NotesAnalyzer, EthicalGuardian, TaskManager
3. Vytvoří task a vrátí task_id
4. Zavolá `orchestrator.execute(context)` s `action="execute_mission"`
5. Formuluje strategický plán
6. Automaticky aktualizuje WORKLOG.md
7. Vrátí formátovaný výsledek uživateli

**Option B: File-Watching (Budoucí)**
```python
# Budoucí: watch_roberts_notes.py integrace
# Toto by používalo NotesWatcher plugin pro sledování změn souboru
# a vkládání autonomních příkazů do consciousness loop
import time
from pathlib import Path

def watch_roberts_notes():
    """
    Sleduje roberts-notes.txt pro změny.
    Při detekci nového obsahu ho NotesWatcher plugin zpracuje.
    
    Poznámka: Toto by běželo jako background služba,
    vkládající příkazy přes INTERFACE vrstvu (ne Core).
    """
    # Implementace delegována na NotesWatcher plugin
    pass
```

**Kompletní Workflow (Plugin-Based Architektura):**
```
1. Goal Input (uživatelský příkaz: "autonomous: ...")
          ↓
2. AutonomousInterface.execute()
   - Detekuje "autonomous:" prefix
   - Extrahuje goal text
          ↓
3. Orchestrator.execute(action="analyze_goal")
   - NotesAnalyzer strukturuje goal
   - EthicalGuardian validuje
   - TaskManager vytvoří task
          ↓
4. Orchestrator.execute(action="execute_mission")
   - Shromáždí kontext (DocReader, CodeReader, Historian)
   - Formuluje specifikaci
   - (Budoucí: Odeslání do Jules API)
          ↓
5. (Budoucí) Čekání na dokončení Jules
   - Poll status každých 30s
   - Logování průběhu do tasku
          ↓
6. (Budoucí) QA.review_code()
   - Architektonická compliance
   - Kvalita kódu
   - Spuštění testů v sandboxu
   - Bezpečnostní kontroly
          ↓
   ┌─────┴─────┐
   │           │
Approved    Rejected
   │           │
   │      Poslat feedback
   │      Jules pro
   │      revizi
   │      (iterace)
   ↓
7. (Budoucí) SafeIntegrator.integrate_plugin()
   - Vytvořit backup
   - Zapsat soubory
   - Spustit celou test suite
   - Commit nebo rollback
          ↓
8. TaskManager.update_task()
   - Status: completed/failed
   - Logovat výsledky
          ↓
9. AutonomousInterface._update_worklog_autonomous()
   - Přidat do WORKLOG.md
          ↓
10. Vrátit formátovaný výsledek uživateli
    "✅ Autonomous Mission Initiated
     Task ID: task-123
     Next Steps: ..."
```
   │      to Jules for
   │      revision
   │      (iterate)
   ↓
6. SafeIntegrator.integrate_plugin()
   - Create backup
   - Write files
   - Run full test suite
   - Commit or rollback
          ↓
7. Update TaskManager
   - Status: completed
   - Log results
          ↓
8. Notify user
   "Plugin '{name}' successfully integrated!"
```

**Testování:**
- End-to-end test s dummy goal
- Mock Jules API
- Verify každá fáze workflow
- Test error recovery v každém bodě

**Bezpečnost:**
- Celý workflow je auditován v task logs
- Každá změna má backup
- User může kdykoli zastavit process
- Emergency stop: `touch STOP_AUTONOMOUS`

**Ověřitelný Výsledek:**
- Uživatel napíše cíl
- Sophia samostatně:
  - Analyzuje požadavek
  - Shromáždí kontext
  - Deleguje na Jules
  - Zreviduje kód
  - Integruje plugin
  - Potvrdí úspěch
- Nový plugin funguje a má testy
- Vše zalogováno v WORKLOG.md

---

## Kritéria Úspěchu Celé Roadmapy

**Základní Test:**
Vedoucí projektu napíše do `docs/roberts-notes.txt`:
```
Create a plugin that translates text using external API
```

**Sophia Independently:**
1. ✓ Detekuje nový cíl
2. ✓ Analyzuje ho pomocí doc/code readeru
3. ✓ Vytvoří task s ID
4. ✓ Shromáždí relevantní kontext (guidelines, similar plugins)
5. ✓ Formuluje detailní specification
6. ✓ Odešle na Jules API
7. ✓ Monitoruje progress
8. ✓ Získá vygenerovaný kód
9. ✓ Provede QA review
10. ✓ (Pokud schváleno) Vytvoří backup
11. ✓ Integruje plugin do plugins/
12. ✓ Spustí všechny testy
13. ✓ Commitne změny
14. ✓ Aktualizuje WORKLOG.md
15. ✓ Oznámí úspěch uživateli

**Výsledek:**
- Nový funkční plugin `tool_translator.py` existuje
- Test file `test_tool_translator.py` existuje a prochází
- Všechny existující testy stále procházejí
- Backup existuje pro rollback
- Task v TaskManageru má status "completed"
- WORKLOG.md obsahuje záznam o autonomní misi

**Bez jakéhokoli dalšího lidského zásahu než počáteční cíl.**

---

## Bezpečnostní Opatření

### Limity a Pojistky
1. **Rate Limiting**: Max 10 Jules API requestů za hodinu
2. **Task Limit**: Max 3 současné tasks
3. **Backup Rotation**: Keep last 20 backups, delete older
4. **Emergency Stop**: File `STOP_AUTONOMOUS` okamžitě zastaví workflow
5. **Approval Mode**: Optional config `require_human_approval: true` pro každý integration step

### Monitoring
1. **Audit Log**: Všechny autonomní akce logované v `data/audit.log`
2. **Task History**: Kompletní historie v TaskManager
3. **Git History**: Každá změna je Git commit s detailed message

### Rollback Strategy
1. Každý backup je Git tag
2. `rollback.py` script pro quick restore
3. Preserve backups min. 30 dní

---

## Poznámky k Implementaci

### Jules API Integration
- API endpoint a authentication podle https://developers.google.com/jules/api
- Může vyžadovat Google Cloud projekt a API key
- Free tier limits: check documentation

### Alternativa k Jules API
Pokud Jules API není dostupné, lze použít:
- GitHub Copilot API
- Anthropic Claude Code
- Lokální Code LLM (DeepSeek Coder, etc.)

Stačí změnit implementaci `tool_jules_api.py`, interface zůstává stejný.

### Modulární Implementace
Každý krok je **samostatný plugin** - lze je implementovat a testovat nezávisle.
Není nutné dělat vše najednou.

---

## Závěr

Tato roadmapa je navržena tak, aby:
1. **Navazovala** na existující fungující kód (především `cognitive_planner`)
2. **Využívala** všechny současné pluginy (doc/code/historian/git/bash/file_system)
3. **Byla implementovatelná** po krocích s ověřitelnými výsledky
4. **Byla bezpečná** s backupy, rollbacks a approval workflow
5. **Byla realistická** - žádné sci-fi features, jen propojení existujících schopností

Po dokončení bude Sophia skutečně autonomním AGI systémem schopným vlastní evoluce pod lidským dohledem.
