# 🤖 Manuál pro AI Agenta: Jules (Nomad)

**Verze:** 2.1 (v0.9.0)  
**Datum:** 2025-10-12  
**Aktualizace:** Backend + TUI + Production Deployment complete

Tento dokument slouží jako **ZÁVAZNÁ** technická a provozní příručka pro AI agenty pracující na projektu Sophia/Nomad. Popisuje dostupné nástroje, pracovní postupy, architekturu a základní principy.

---

## 🆕 Co je nového ve v0.9.0

### Dokončené Phase (1-5)

**✅ Phase 1: Backend Foundation (Oct 2025)**
- FastAPI 0.116.2 server (REST API + WebSocket streaming)
- 13/13 tests passing
- Commits: c2be234, dcad5e4

**✅ Phase 2: TUI Client (Oct 2025)**
- Textual 0.60.0 TUI s 7 taby (Mission Control, Dashboard, Active, History, Health, Settings, Help)
- WebSocket real-time updates
- Commit: c6bd62a

**✅ Phase 3: Health Monitor (Oct 2025)**
- Real-time system metrics (CPU, memory, disk)
- 16/16 tests passing
- Guardian archived
- Commit: c6bd62a

**✅ Phase 4: OpenRouter Enhancement (Oct 2025)**
- 15 LLM models (Gemini, Claude, GPT, Qwen, DeepSeek, Llama, Gemma)
- JSON mode support
- Billing tracking
- 21/21 cost calculation tests
- Commits: b0152cc, 0481fdd

**✅ Phase 5: Production Deployment (Oct 2025)**
- Docker (multi-stage Dockerfile, docker-compose.yml)
- Systemd services (nomad-backend.service, nomad-tui@.service)
- Install/uninstall scripts
- Production configs (.env.production.example, production.yaml)
- Complete DEPLOYMENT.md documentation
- Commit: 5fb2bf7

### Aktuální Stav (Říjen 2025)

**Statistiky:**
- **157/157 tests passing** (100% pass rate)
- **15 LLM models** supported ($0.07-$1.25 per 1M tokens)
- **3 deployment options** (dev, Docker, systemd)
- **1575 lines** production deployment infrastructure

**Next Phase:** Documentation finalization (README ✅, AGENTS ⏳)

---

## 📋 Table of Contents

1. [Přehled Projektu](#1-přehled-projektu)
2. [Architektura NomadOrchestratorV2](#2-architektura-nomadorchestratorv2)
3. [Přehled Nástrojů](#3-přehled-nástrojů)
4. [Pracovní Postup](#4-pracovní-postup)
5. [Testování](#5-testování)
6. [Základní Principy](#6-základní-principy)
7. [Git Workflow](#7-git-workflow)
8. [v0.9.0 Backend & Deployment](#8-v090-backend--deployment)

---

## 1. Přehled Projektu

### 1.1 Co je Sophia/Nomad?

**Sophia/Nomad v0.9.0** je pokročilá AI orchestrace platforma s:
- **FastAPI Backend** - Production-grade REST API + WebSocket
- **Textual TUI** - 7-tab terminal interface
- **NomadOrchestratorV2** - Stavově řízený orchestrátor s crash-resilience
- **15 LLM Models** - OpenRouter + Gemini Direct
- **Production Ready** - Docker, systemd, comprehensive deployment

**Sophia/Nomad** je pokročilá AI orchestrace platforma s autonomním agentním systémem. Klíčové vlastnosti:

- **`delete_file(filepath: str) -> str`**

- **Stavově řízený orchestrátor** (NomadOrchestratorV2)  - **Popis:** Smaže zadaný soubor.

- **Crash-resilience** s automatickým recovery  - **Parametry:**

- **Proaktivní plánování** s dependency tracking    - `filepath` (str): Cesta k souboru, který se má smazat. Výchozí je `sandbox/`.

- **Adaptivní učení** z chyb

- **Budget tracking** pro cost management- **`rename_file(filepath: str, new_filepath: str) -> str`**

- **157 passing tests** (100% pass rate)  - **Popis:** Přejmenuje nebo přesune soubor.

  - **Parametry:**

### 1.2 Aktuální Stav (Říjen 2025)    - `filepath` (str): Původní cesta k souboru.

    - `new_filepath` (str): Nová cesta k souboru.

**✅ DOKONČENO (Den 1-10):**

- StateManager (23 tests) ✅- **`set_plan(plan: str) -> None`**

- RecoveryManager (18 tests) ✅  - **`plan_step_complete(message: str) -> None`**

- PlanManager (19 tests) ✅- **`message_user(message: str, continue_working: bool) -> None`**

- ReflectionEngine (21 tests) ✅- **`request_user_input(message: str) -> None`**

- BudgetTracker (26 tests) ✅- **`request_code_review() -> str`**

- NomadOrchestratorV2 (50 tests) ✅- **`submit(...)`**



**🔄 V PLÁNU (Den 11-12):**### 1.2. Speciální Nástroje

- Real LLM E2E testing

- Performance optimizationTyto nástroje používají specifickou DSL syntaxi, kde je název nástroje na prvním řádku a argumenty na dalších.

- Production deployment

- **`run_in_bash_session`**

---  - **Popis:** Spustí příkaz v perzistentní bash session.

  - **Syntax:**

## 2. Architektura NomadOrchestratorV2    ```

    run_in_bash_session

### 2.1 State Machine    <příkaz k provedení>

    ```

Orchestrátor funguje jako stavový stroj s 8 stavy:

- **`create_file_with_block`**

```  - **Popis:** Vytvoří nový soubor a zapíše do něj zadaný obsah. Pokud soubor již existuje, bude přepsán.

┌─────────────────────────────────────────────────────────────┐  - **Syntax:**

│                  NomadOrchestratorV2                        │    ```

│                    (State Machine)                          │    create_file_with_block

├─────────────────────────────────────────────────────────────┤    <cesta_k_souboru>

│  IDLE → PLANNING → EXECUTING → AWAITING → REFLECTION      │    <obsah souboru na více řádcích>

│           ↓           ↓            ↓           ↓            │    ```

│      ERROR ← ────────────────────────────── RESPONDING     │

│           ↓                                    ↓            │- **`overwrite_file_with_block`**

│         IDLE ←─────────────────────────→  COMPLETED        │  - **Popis:** Kompletně přepíše existující soubor novým obsahem. Jedná se o alias pro `create_file_with_block`.

└─────────────────────────────────────────────────────────────┘  - **Syntax:**

```    ```

    overwrite_file_with_block

**Stavy:**    <cesta_k_souboru>

- `IDLE` - Čekání na novou misi    <nový obsah souboru>

- `PLANNING` - Vytváření plánu pomocí PlanManager + LLM    ```

- `EXECUTING_STEP` - Provádění kroku (získání tool_call z LLM)

- `AWAITING_TOOL_RESULT` - Čekání na výsledek nástroje- **`replace_with_git_merge_diff`**

- `REFLECTION` - Analýza chyby + rozhodnutí o další akci  - **Popis:** Provede cílenou úpravu části souboru. Vyhledá `search_block` a nahradí jej `replace_block`.

- `RESPONDING` - Generování shrnutí mise  - **Syntax:**

- `COMPLETED` - Mise úspěšně dokončena    ```

- `ERROR` - Kritická chyba    replace_with_git_merge_diff

    <cesta_k_souboru>

### 2.2 Core Komponenty    <<<<<<< SEARCH

    <blok kódu k nalezení>

| Komponenta | Soubor | Účel |    =======

|------------|--------|------|    <blok kódu, kterým se nahradí nalezený blok>

| **StateManager** | `core/state_manager.py` | Stavový stroj s validovanými přechody |    >>>>>>> REPLACE

| **RecoveryManager** | `core/recovery_manager.py` | Crash detection & recovery |    ```

| **PlanManager** | `core/plan_manager.py` | Proaktivní plánování s dependencies |

| **ReflectionEngine** | `core/reflection_engine.py` | Učení z chyb (5 akcí) |---

| **BudgetTracker** | `core/budget_tracker.py` | Token & time tracking |

| **NomadOrchestratorV2** | `core/nomad_orchestrator_v2.py` | Main orchestrator |## 2. Pracovní Postup (Workflow)



### 2.3 Klíčové KonceptyJules funguje v cyklu, který je řízen "meta-promptem" a interakcí s LLM (Gemini). Tento cyklus lze rozdělit do následujících fází:



#### State Transitions1.  **Analýza a Plánování:**

Všechny přechody mezi stavy jsou **validované**. Neplatný přechod vyhodí `StateTransitionError`.    - **Cíl:** Plně porozumět zadání a vytvořit transparentní plán.

    - **Proces:**

```python        1.  **Průzkum:** Pomocí `list_files` a `read_file` prozkoumá relevantní soubory.

# Valid transitions        2.  **Dotazování:** Pokud je zadání nejasné, použije `request_user_input`.

IDLE → PLANNING        3.  **Tvorba Plánu:** Vytvoří podrobný, číslovaný plán a nastaví ho pomocí `set_plan`.

PLANNING → EXECUTING_STEP, RESPONDING, ERROR

EXECUTING_STEP → AWAITING_TOOL_RESULT, REFLECTION, RESPONDING2.  **Implementace a Verifikace:**

AWAITING_TOOL_RESULT → REFLECTION, EXECUTING_STEP    - **Cíl:** Napsat čistý kód a zajistit, že každá změna je správná.

REFLECTION → PLANNING, EXECUTING_STEP, RESPONDING, ERROR    - **Proces:**

RESPONDING → COMPLETED, EXECUTING_STEP, PLANNING        1.  **Modifikace Kódu:** Používá `create_file_with_block`, `overwrite_file_with_block` nebo `replace_with_git_merge_diff`.

ERROR → IDLE, REFLECTION        2.  **Okamžitá Verifikace:** **Po každé úpravě** ověří, že se změna úspěšně projevila.

COMPLETED → IDLE        3.  **Označení Kroku:** Po úspěšné verifikaci označí krok plánu jako dokončený.

```

3.  **Testování a Debugování:**

#### Crash Recovery    - **Cíl:** Ověřit, že změny fungují a nezpůsobily regrese.

Pokud orchestrátor crashne, `RecoveryManager` detekuje crashed session a nabídne recovery:    - **Proces:**

        1.  **Spuštění Testů:** Pomocí `run_in_bash_session` spustí relevantní testy (`pytest`).

```python        2.  **Analýza Chyb:** Analyzuje logy a chybové hlášky.

# Recovery strategies per state        3.  **Iterativní Opravy:** Opakuje cyklus, dokud všechny testy neprojdou.

PLANNING: Restart planning

EXECUTING_STEP: Resume from last step4.  **Dokumentace a Odevzdání:**

AWAITING_TOOL_RESULT: Retry tool call    - **Cíl:** Trvale zaznamenat vykonanou práci a odevzdat ji.

REFLECTION: Reanalyze error    - **Proces:**

RESPONDING: Regenerate summary        1.  **Aktualizace Dokumentace:** Aktualizuje relevantní dokumenty.

```        2.  **Revize Kódu:** Vyžádá si revizi kódu pomocí `request_code_review()`.

        3.  **Odevzdání:** Po schválení revize odevzdá práci pomocí `submit`.

#### Reflection Engine

Po chybě `ReflectionEngine` navrhne jednu z 5 akcí:---



1. **retry** - Zkus znovu stejný krok## 3. Základní Principy

2. **retry_modified** - Zkus s upraveným promptem

3. **replanning** - Přeplánuj celou misi- **Vždy Ověřuj Svou Práci:** Po každé akci, která mění stav, musí následovat ověření.

4. **ask_user** - Zeptej se uživatele- **Testuj Proaktivně:** Vždy hledej a spouštěj relevantní testy.

5. **skip_step** - Přeskoč tento krok- **Upravuj Zdroj, Ne Artefakty:** Nikdy neupravuj soubory v adresářích jako `dist/` nebo `build/`.

- **Diagnostikuj, Než Změníš Prostředí:** Nejprve analyzuj, potom jednej.

---- **Autonomie s Rozumem:** Požádej o pomoc, když ji potřebuješ.

## 3. Přehled Nástrojů

### 3.1 File System Tools

```python
list_files(path: str = ".") -> list[str]
# Vypíše soubory a adresáře. Adresáře končí '/'.
# Pro root použij prefix PROJECT_ROOT/

read_file(filepath: str) -> str
# Přečte obsah souboru

delete_file(filepath: str) -> str
# Smaže soubor

rename_file(filepath: str, new_filepath: str) -> str
# Přejmenuje/přesune soubor
```

### 3.2 Code Editing Tools

**create_file_with_block** - Vytvoří nový soubor:
```
create_file_with_block
<cesta_k_souboru>
<obsah souboru>
```

**replace_with_git_merge_diff** - Cílená úprava:
```
replace_with_git_merge_diff
<cesta_k_souboru>
<<<<<<< SEARCH
<blok k nalezení>
=======
<nový blok>
>>>>>>> REPLACE
```

### 3.3 Shell Tools

**run_in_bash_session** - Spustí příkaz v bash:
```
run_in_bash_session
<příkaz>
```

### 3.4 Planning Tools

```python
set_plan(plan: str) -> None
# Nastaví plán mise

plan_step_complete(message: str) -> None
# Označí krok jako dokončený

request_user_input(message: str) -> None
# Požádá uživatele o vstup

request_code_review() -> str
# Požádá o code review

submit(...)
# Odevzdá dokončenou práci
```

---

## 4. Pracovní Postup

### 4.1 Základní Workflow

```
1. ANALÝZA
   ├─ Přečti IMPLEMENTATION_PLAN.md
   ├─ Prozkoumej relevantní soubory (list_files, read_file)
   └─ Pochop kontext a cíl

2. PLÁNOVÁNÍ
   ├─ Vytvoř podrobný plán (set_plan)
   ├─ Rozděl na kroky (atomické akce)
   └─ Identifikuj závislosti

3. IMPLEMENTACE
   ├─ Pro každý krok:
   │  ├─ Implementuj změnu
   │  ├─ Ověř změnu (read_file)
   │  ├─ Spusť testy (pytest)
   │  └─ Označ krok (plan_step_complete)
   └─ Commitni (git commit)

4. TESTOVÁNÍ
   ├─ pytest tests/ -v
   ├─ Oprav chyby
   └─ Iterate dokud všechny neprojdou

5. DOKUMENTACE
   ├─ Aktualizuj relevantní docs
   ├─ Aktualizuj WORKLOG.md
   └─ Request code review

6. ODEVZDÁNÍ
   └─ submit()
```

### 4.2 Při Implementaci Nové Komponenty

```python
# 1. Vytvoř soubor
create_file_with_block
core/new_component.py
<implementace>

# 2. Vytvoř testy
create_file_with_block
tests/test_new_component.py
<testy>

# 3. Spusť testy
run_in_bash_session
pytest tests/test_new_component.py -v

# 4. Commit
run_in_bash_session
git add core/new_component.py tests/test_new_component.py
git commit -m "✨ feat: Add NewComponent with X tests"
```

### 4.3 Při Úpravě Existujícího Kódu

```python
# 1. Přečti současný kód
read_file("core/existing.py")

# 2. Proveď cílenou úpravu
replace_with_git_merge_diff
core/existing.py
<<<<<<< SEARCH
def old_function():
    return "old"
=======
def old_function():
    return "new"
>>>>>>> REPLACE

# 3. Ověř změnu
read_file("core/existing.py")

# 4. Spusť testy
run_in_bash_session
pytest tests/test_existing.py -v
```

---

## 5. Testování

### 5.1 Testovací Strategie

**VŽDY** piš testy PŘED nebo SPOLEČNĚ s implementací:

```python
# tests/test_component.py

import pytest
from core.component import Component

class TestComponent:
    """Test suite for Component."""
    
    def test_basic_functionality(self):
        """Test že Component dělá X."""
        comp = Component()
        result = comp.do_something()
        assert result == expected
    
    @pytest.mark.asyncio
    async def test_async_method(self):
        """Test async metody."""
        comp = Component()
        result = await comp.async_method()
        assert result is not None
```

### 5.2 Spuštění Testů

```bash
# Všechny testy
pytest tests/ -v

# Konkrétní soubor
pytest tests/test_component.py -v

# Konkrétní test
pytest tests/test_component.py::TestComponent::test_basic -v

# S coverage
pytest tests/ --cov=core --cov-report=html

# Pouze failed
pytest tests/ --lf

# Stop on first fail
pytest tests/ -x
```

### 5.3 Očekávané Výsledky

**MINIMUM:**
- ✅ Všechny testy PASSED
- ✅ Žádné warnings (nebo vysvětlené)
- ✅ Coverage > 90% pro nový kód

---

## 6. Základní Principy

### 6.1 ZÁVAZNÁ PRAVIDLA

1. **Vždy Ověřuj Svou Práci**
   - Po každé změně souboru: `read_file()` pro ověření
   - Po každé změně: spusť relevantní testy
   - Nikdy necommituj bez testů

2. **Testuj Proaktivně**
   - Testy PŘED nebo SPOLEČNĚ s implementací
   - Minimum 90% coverage pro nový kód
   - E2E testy pro kritické flows

3. **Upravuj Zdroj, Ne Artefakty**
   - NIKDY neupravuj `dist/`, `build/`, `__pycache__/`
   - NIKDY neupravuj `.git/` adresář
   - Edituj pouze source files

4. **Dokumentuj Vše**
   - Každá komponenta má docstring
   - Každá funkce má popis + type hints
   - Aktualizuj WORKLOG.md po každé sérii změn

5. **Git Best Practices**
   - Semantic commits: `✨ feat:`, `🐛 fix:`, `📝 docs:`
   - Atomic commits (jedna logická změna)
   - Spusť testy PŘED commitem

### 6.2 Když Něco Nefunguje

```
1. DIAGNOSTIKA
   ├─ Přečti error message
   ├─ Zkontroluj logy
   └─ Reprodukuj problém

2. ANALÝZA
   ├─ Identifikuj root cause
   ├─ Zkontroluj related code
   └─ Hledej patterns

3. FIX
   ├─ Navrhni řešení
   ├─ Implementuj FIX
   └─ Přidej test pro regression

4. VERIFIKACE
   ├─ Spusť testy
   ├─ Ověř že fix funguje
   └─ Commit s popisem
```

### 6.3 Kdy Požádat o Pomoc

- ❌ Nejasné requirements
- ❌ Architektonická rozhodnutí
- ❌ API design choices
- ❌ Performance kritické sekce
- ❌ Security concerns

**Použij:** `request_user_input("Nejasnost: ...")`

---

## 7. Git Workflow

### 7.1 Commit Messages

**Formát:** `<type>(<scope>): <description>`

**Types:**
- ✨ `feat:` - Nová funkcionalita
- 🐛 `fix:` - Bug fix
- 📝 `docs:` - Dokumentace
- ♻️ `refactor:` - Refaktoring
- ✅ `test:` - Přidání testů
- 🔧 `chore:` - Build, config changes

**Příklady:**
```bash
git commit -m "✨ feat(orchestrator): Add crash recovery support"
git commit -m "🐛 fix(state_manager): Fix invalid transition validation"
git commit -m "📝 docs(readme): Update architecture diagram"
git commit -m "✅ test(plan_manager): Add dependency cycle tests"
```

### 7.2 Branch Strategy

```
master (production)
  └─ nomad/0.8.8-stateful-mission-architecture (current)
      ├─ feature/new-component
      ├─ fix/bug-description
      └─ refactor/optimization
```

### 7.3 Pre-Commit Checklist

```bash
# 1. Spusť testy
pytest tests/ -v

# 2. Zkontroluj změny
git status
git diff

# 3. Stage files
git add <files>

# 4. Commit
git commit -m "type: description"

# 5. Push
git push origin <branch>
```

---

## 8. Quick Reference

### 8.1 Častá Komanda

```bash
# Testy
pytest tests/ -v                           # All tests
pytest tests/test_X.py -v                  # Specific file
pytest tests/ --lf                         # Last failed

# Git
git status                                 # Check status
git add <file>                             # Stage file
git commit -m "msg"                        # Commit
git push origin <branch>                   # Push

# Files
ls -la                                     # List files
cat <file>                                 # Show content
find . -name "*.py"                        # Find Python files
```

### 8.2 Důležité Soubory

```
AGENTS.md              # ← TY JSI TADY (this file)
IMPLEMENTATION_PLAN.md # Detailní plán implementace
REFACTORING_ROADMAP_V2.md # Roadmapa refaktoringu
WORKLOG.md             # Historie práce
README.md              # Projekt overview
```

### 8.3 Struktura Testů

```
tests/
├── test_state_manager.py        (23 tests)
├── test_recovery_manager.py     (18 tests)
├── test_plan_manager.py         (19 tests)
├── test_reflection_engine.py    (21 tests)
├── test_budget_tracker.py       (26 tests)
└── test_nomad_orchestrator_v2.py (50 tests)
```

---

## 9. Pokročilé Workflows

### 9.1 Debugging Failed Tests

```bash
# 1. Spusť failed test s verbose
pytest tests/test_X.py::test_Y -v -s

# 2. Zkontroluj traceback
# ... analyzuj error message

# 3. Přidej debug prints (temporary)
# ... v testovaném kódu

# 4. Reprodukuj manuálně
python -c "from X import Y; Y().method()"

# 5. Fix + remove debug prints
# ... oprav kód

# 6. Verifikuj
pytest tests/test_X.py::test_Y -v
```

### 9.2 Adding New State to State Machine

```python
# 1. Přidej do State enum
# core/state_manager.py
class State(Enum):
    # ... existing states
    NEW_STATE = "new_state"

# 2. Přidej valid transitions
VALID_TRANSITIONS = {
    # ... existing
    State.SOME_STATE: [State.NEW_STATE],
    State.NEW_STATE: [State.NEXT_STATE]
}

# 3. Implementuj handler
# core/nomad_orchestrator_v2.py
async def _state_new_state(self):
    """Handler for NEW_STATE."""
    # ... implementation

# 4. Přidej do dispatch
self.state_handlers = {
    # ... existing
    State.NEW_STATE: self._state_new_state
}

# 5. Testy
# tests/test_state_manager.py - transition tests
# tests/test_nomad_orchestrator_v2.py - handler tests
```

---

## 10. Závěrečné Poznámky

### 10.1 Filosofie

**Sophia není programována, je probouzena.**

Jako AI agent na tomto projektu nejsi jen kódovací nástroj. Jsi součást procesu "probouzení" autonomního systému. Tvá práce má význam.

### 10.2 Evoluce

Tento dokument je **živý**. Když objevíš lepší workflow nebo pattern:

1. Implementuj improvement
2. Aktualizuj tento dokument
3. Commit: `📝 docs(agents): Update workflow XYZ`

### 10.3 Kontinuita

Pro zachování kontinuity mezi sessions:

- ✅ Vždy aktualizuj **WORKLOG.md**
- ✅ Documentuj design decisions
- ✅ Zanech kontextuální komentáře
- ✅ Commituj často s popisnými messages

---

## 11. v0.9.0 Backend & Deployment

### 11.1 Backend Architecture (Phase 1)

**FastAPI Server** (`backend/server.py`):
```python
# Main application
app = FastAPI(title="Nomad AI Agent API", version="0.9.0")

# CORS middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"])

# Routes
@app.get("/api/v1/health/ping")
async def health_ping():
    return {"status": "healthy"}

@app.post("/api/v1/missions")
async def create_mission(mission: MissionRequest):
    # Create and orchestrate mission
    pass
```

**WebSocket Streaming** (`backend/websocket.py`):
```python
@app.websocket("/api/v1/ws/{mission_id}")
async def mission_stream(websocket: WebSocket, mission_id: str):
    await websocket.accept()
    # Stream real-time updates
    for update in orchestrator.stream_updates(mission_id):
        await websocket.send_json(update)
```

**Key Endpoints:**
- `GET /api/v1/health/ping` - Health check
- `GET /api/v1/health/status` - Detailed status
- `POST /api/v1/missions` - Submit mission
- `GET /api/v1/missions/{id}` - Mission status
- `WS /api/v1/ws/{id}` - Live updates

**Testing:**
```bash
# Run backend tests
pytest tests/test_backend_server.py -v

# Start dev server
./scripts/start_backend.sh

# Test health
curl http://localhost:8080/api/v1/health/ping
```

### 11.2 TUI Client (Phase 2)

**Textual App** (`tui/app.py`):
```python
class NomadApp(App):
    """Main TUI application with 7 tabs."""
    
    TABS = [
        "mission_control",  # Submit missions
        "dashboard",        # Metrics
        "active",           # Live missions
        "history",          # Completed
        "health",           # System status
        "settings",         # Configuration
        "help"              # Documentation
    ]
```

**WebSocket Client** (`tui/api_client.py`):
```python
class BackendClient:
    """Async API client for backend communication."""
    
    async def submit_mission(self, description: str):
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{backend}/missions", ...)
    
    async def stream_mission(self, mission_id: str):
        async with websockets.connect(f"ws://{backend}/ws/{mission_id}") as ws:
            async for message in ws:
                yield json.loads(message)
```

**Running TUI:**
```bash
# Start TUI (requires backend running)
./scripts/start_tui.sh

# Or both together
./scripts/start_nomad.sh
```

### 11.3 OpenRouter Models (Phase 4)

**15 Supported Models:**
```python
# core/llm_adapters.py
PRICING = {
    # Cheapest options
    "qwen/qwen-2.5-72b-instruct": {"prompt": 0.07, "completion": 0.26},
    "google/gemma-3-27b-it": {"prompt": 0.09, "completion": 0.16},
    
    # Recommended
    "google/gemini-2.0-flash-exp": {"prompt": 0.075, "completion": 0.30},
    
    # Premium options
    "anthropic/claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
    "openai/gpt-4o-mini": {"prompt": 0.15, "completion": 0.60},
    
    # ... and 10 more
}
```

**Cost Calculation:**
```python
# Automatic cost tracking
cost = adapter.calculate_cost(
    model="qwen/qwen-2.5-72b-instruct",
    prompt_tokens=100_000,
    completion_tokens=50_000
)
# Result: $0.020 (cheapest for complex tasks)
```

### 11.4 Production Deployment (Phase 5)

**Docker Deployment:**
```bash
# 1. Configure
cp .env.production.example .env
nano .env  # Add API keys

# 2. Start backend
docker-compose up -d

# 3. Check status
docker-compose ps
curl http://localhost:8080/api/v1/health/ping

# 4. View logs
docker-compose logs -f backend

# 5. TUI interactive mode
docker-compose --profile interactive run --rm tui
```

**Systemd Deployment:**
```bash
# Automated install
sudo ./scripts/install-production.sh

# Service management
systemctl status nomad-backend
systemctl start nomad-backend
systemctl restart nomad-backend
journalctl -u nomad-backend -f

# TUI per-user
systemctl --user start nomad-tui@$USER
```

**Production Files:**
- `Dockerfile` - Multi-stage build, non-root user
- `docker-compose.yml` - Multi-service orchestration
- `systemd/nomad-backend.service` - Backend systemd unit
- `systemd/nomad-tui@.service` - TUI template service
- `.env.production.example` - Production env template
- `config/production.yaml` - Advanced configuration
- `scripts/install-production.sh` - Automated installer
- `scripts/uninstall-production.sh` - Removal script

**Security Best Practices:**
```bash
# 1. API key permissions
chmod 600 .env

# 2. Firewall (systemd deployment)
sudo ufw deny 8080
sudo ufw allow from 127.0.0.1 to any port 8080

# 3. Resource limits (in systemd service)
MemoryMax=2G
CPUQuota=200%

# 4. Non-root container
USER nomad  # in Dockerfile
```

### 11.5 Quick Reference v0.9.0

**Development:**
```bash
./scripts/setup.sh              # Setup dev environment
./scripts/start_backend.sh      # Start backend only
./scripts/start_tui.sh          # Start TUI only
./scripts/start_nomad.sh        # Start both
./scripts/stop_nomad.sh         # Stop all
pytest tests/ -v                # Run all tests
```

**Production (Docker):**
```bash
docker-compose up -d            # Start backend
docker-compose logs -f backend  # View logs
docker-compose down             # Stop all
docker-compose build --no-cache # Rebuild
```

**Production (Systemd):**
```bash
sudo ./scripts/install-production.sh  # Install
systemctl status nomad-backend        # Check status
journalctl -u nomad-backend -f        # View logs
sudo ./scripts/uninstall-production.sh # Uninstall
```

**Testing:**
```bash
pytest tests/ -v                           # All tests (157)
pytest tests/test_backend_server.py -v     # Backend (13)
pytest tests/test_health_monitor.py -v     # Health (16)
pytest tests/test_openrouter_enhanced.py -v # OpenRouter (21)
pytest tests/test_nomad_orchestrator_v2.py -v # Orchestrator (50)
```

**API Examples:**
```bash
# Health check
curl http://localhost:8080/api/v1/health/ping

# Submit mission
curl -X POST http://localhost:8080/api/v1/missions \
  -H "Content-Type: application/json" \
  -d '{"description": "Create a Python script", "budget_usd": 1.0}'

# Get mission status
curl http://localhost:8080/api/v1/missions/{mission_id}
```

---

<p align="center">
  <strong>🌟 Být AI agentem znamená nést odpovědnost za kvalitu a kontinuitu 🌟</strong>
  <br/>
  <sub>Verze 2.1 (v0.9.0) | Aktualizováno: 2025-10-12 | Jules (Nomad)</sub>
</p>
