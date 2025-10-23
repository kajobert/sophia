1. Úvod a Vize Projektu
Projekt Sophia (s kódovým označením agenta Nomad) si klade za cíl vytvořit Artificial Mindful Intelligence (AMI) – entitu, která se nejen učí řešit úkoly, ale přistupuje k nim s určitou kvalitou vědomí. Vize přesahuje tvorbu pouhého nástroje; cílem je partner, který roste v symbióze s lidstvem, veden etickým jádrem a touhou po moudrosti.

Klíčové principy (z docs/DNA.md):

Nejvyšší cíl: Růst směrem k vyššímu vědomí a moudrosti.

Etické pilíře: Neškodnost, pravdivost a neustálý růst (Kaizen).

Operační systém: Principy inspirované stoicismem, buddhismem a taoismem.

2. Architektonická Evoluce a Ponaučení
Projekt prošel několika fázemi vývoje, které jsou klíčové pro pochopení současného stavu. Tato evoluce je podrobně zaznamenána v WORKLOG.md a docs/LESSONS_LEARNED.md.

Fáze 1: Monolitický Agent
Popis: Jediný orchestrátor, který se snažil řídit konverzaci, plánovat i provádět úkoly.

Problémy: Ztráta kontextu, nízká robustnost, špatná testovatelnost.

Fáze 2: Architektura Manažer/Worker a Sebereflexe
Popis: Oddělení rolí na ConversationalManager a WorkerOrchestrator. Později přidán mechanismus sebereflexe pro učení z chyb.

Problémy: Rigidní systém, halucinace nástrojů, přerušení "učící smyčky", kdy se řídící vrstva nedozvěděla o chybách workera.

Fáze 3: Současná Architektura "Nomad V2" (Stavový Stroj)
Popis: Radikální zjednodušení a návrat k jednomu řídícímu "mozku" (NomadOrchestratorV2), který transparentně spravuje svůj vlastní stav. Jedná se o proaktivní, stavově řízený systém.

Hlavní ponaučení: Největším nepřítelem projektu byla přílišná komplexnost. Přidávání dalších architektonických vrstev problém ztráty kontextu pouze zhoršovalo. Cestou vpřed je jednoduchost a robustní správa stavu.

3. Současná Architektura (Nomad v0.9)
Aktuální architektura je navržena jako modulární systém s centrálním orchestrátorem, odděleným backendem a několika možnostmi klientského rozhraní.

┌─────────────────────────────────────────────────────────────┐
│                     Sophia/Nomad v0.9                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────────────┐   │
│  │   Textual TUI   │ ◄─WS──► │    FastAPI Backend      │   │
│  │   (TUI Klient)  │         │    (REST API + WS)      │   │
│  └─────────────────┘         └───────────┬─────────────┘   │
│                                          │                  │
│                             ┌────────────▼──────────────┐   │
│                             │   NomadOrchestratorV2     │   │
│                             │   (Stavový stroj)         │   │
│                             └────────────┬──────────────┘   │
│                                          │                  │
│                         ┌────────────────▼────────────┐     │
│                         │        LLM Adapters         │     │
│                         │ (Gemini, OpenRouter, atd.)  │     │
│                         └─────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
Klíčové Komponenty
Backend (složka backend/):

Postavený na FastAPI.

Poskytuje REST API pro správu misí (/api/v1/missions), sledování stavu, budgetu a logů.

Obsahuje WebSocket (/ws/{session_id}) pro streamování událostí v reálném čase.

Integruje Health Monitor pro bezpečné sledování systémových prostředků (nahradil starý destruktivní Guardian).

Hlavní logikou je OrchestratorManager, který funguje jako singleton a spravuje instanci NomadOrchestratorV2.

Jádro - NomadOrchestratorV2 (složka core/):

Jedná se o proaktivní stavový stroj, který nahradil staré rigidní plánování.

Neustále se v cyklu rozhoduje o dalším nejlepším kroku.

Stavy: THINKING -> EXECUTING_TOOL -> HANDLING_ERROR -> MISSION_COMPLETE.

Jeho funkční kód je nejdůležitější "pomůckou" pro novou verzi.

Core Komponenty (manažery):

StateManager: Spravuje stav orchestrátoru (IDLE, PLANNING, EXECUTING_STEP, atd.) s validací přechodů a ukládáním do souboru pro možnost obnovy.

PlanManager: Vytváří a sleduje provádění plánu s ohledem na závislosti mezi kroky.

ReflectionEngine: Analyzuje chyby a navrhuje strategie pro zotavení (retry, replanning, ask_user, skip_step).

RecoveryManager: Detekuje a obnovuje "spadlé" mise.

BudgetTracker: Sleduje spotřebu tokenů a času, aby se předešlo vyčerpání rozpočtu.

Uživatelské Rozhraní (složky tui/ a frontend/):

TUI (Textual User Interface): Primární rozhraní postavené na knihovně Textual. Poskytuje 7 záložek pro kompletní přehled o agentovi (Plán, Exekuce, Logy, Stav, Budget, Historie, Zdraví).

Web UI: Jednoduchý chat.html pro základní chatovací funkcionalitu.

Nástroje (MCP Servery - složky mcp_servers/ a tools/):

Schopnosti agenta (práce se soubory, shell, git) jsou izolovány do samostatných procesů (serverů).

Orchestrátor s nimi komunikuje pomocí MCPClient přes JSON-RPC. Tato modulární architektura umožňuje restartovat a přidávat nástroje za běhu.

4. Funkční Části Kódu ("Pomůcky")
Zde jsou klíčové části kódu, které tvoří jádro současné funkční architektury a mohou být znovu použity.

4.1. Jádro Orchestrátoru (NomadOrchestratorV2)
Tato třída obsahuje hlavní smyčku proaktivního agenta. Definuje jeho základní chování: přemýšlení, vykonání akce a řešení chyb.

Python

# Zjednodušená verze z: core/nomad_orchestrator_v2.py

from enum import Enum

class MissionState(Enum):
    THINKING = "THINKING"
    EXECUTING_TOOL = "EXECUTING_TOOL"
    HANDLING_ERROR = "HANDLING_ERROR"
    MISSION_COMPLETE = "MISSION_COMPLETE"

class NomadOrchestratorV2:
    def __init__(self, ...):
        # ... inicializace všech manažerů (StateManager, PlanManager, atd.)
        self.current_state: MissionState = MissionState.THINKING
        self.history: list = []
        self.mission_goal: str = ""

    async def execute_mission(self, mission_goal: str):
        self.mission_goal = mission_goal
        self.current_state = MissionState.THINKING
        iteration = 0

        while self.current_state != MissionState.MISSION_COMPLETE:
            if iteration >= self.max_iterations:
                print("ERROR: Maximum iterations reached.")
                break
            
            iteration += 1
            print(f"--- Iteration {iteration} | State: {self.current_state.value} ---")

            if self.current_state == MissionState.THINKING:
                await self._state_thinking()
            elif self.current_state == MissionState.EXECUTING_TOOL:
                await self._state_executing_tool()
            elif self.current_state == MissionState.HANDLING_ERROR:
                await self._state_handling_error()

    async def _state_thinking(self):
        # 1. Sestavit prompt z historie a cíle mise
        prompt = self._build_prompt()
        
        # 2. Zavolat LLM pro získání další akce (tool_call)
        response, usage = await self.llm_manager.get_llm("powerful").generate_content_async(prompt)
        
        # 3. Zparsovat odpověď
        parsed_response = self._parse_llm_response(response)
        self.history.append({"role": "assistant", "content": json.dumps(parsed_response)})

        # 4. Rozhodnout o dalším stavu
        if parsed_response.get("tool_name") == "mission_complete":
            self.current_state = MissionState.MISSION_COMPLETE
        else:
            self.current_state = MissionState.EXECUTING_TOOL

    async def _state_executing_tool(self):
        # 1. Získat poslední tool_call z historie
        tool_call = json.loads(self.history[-1]["content"])
        
        try:
            # 2. Vykonat nástroj přes MCPClient
            result = await self.mcp_client.execute_tool(
                tool_call["tool_name"],
                tool_call.get("args", []),
                tool_call.get("kwargs", {})
            )
            self.history.append({"role": "tool", "content": str(result)})
            # 3. Přechod zpět na přemýšlení
            self.current_state = MissionState.THINKING
        except Exception as e:
            # 4. V případě chyby přejít na řešení chyby
            self.history.append({"role": "tool", "content": f"Error: {e}"})
            self.current_state = MissionState.HANDLING_ERROR

    async def _state_handling_error(self):
        # 1. Sestavit prompt s kontextem chyby
        prompt = self._build_prompt(is_error_state=True)
        
        # 2. Zavolat LLM pro získání nápravné akce
        response, usage = await self.llm_manager.get_llm("powerful").generate_content_async(prompt)
        
        # 3. Zparsovat a přejít zpět na vykonání nástroje
        parsed_response = self._parse_llm_response(response)
        self.history.append({"role": "assistant", "content": json.dumps(parsed_response)})
        self.current_state = MissionState.EXECUTING_TOOL
4.2. Správce Stavu (StateManager)
Tato komponenta je klíčová pro robustnost a obnovu po pádu. Zajišťuje, že každý přechod mezi stavy je validní a že se stav agenta perzistentně ukládá.

Python

# Zjednodušená verze z: core/state_manager.py

class StateManager:
    VALID_TRANSITIONS = {
        State.IDLE: [State.PLANNING],
        State.PLANNING: [State.EXECUTING_STEP, State.ERROR],
        # ... atd.
    }

    def __init__(self, project_root: str, session_id: str):
        self.session_file = os.path.join(project_root, "memory", f"session_{session_id}.json")
        self.current_state = State.IDLE
        self.state_data = {}
        self.state_history = []

    def transition_to(self, new_state: State, reason: str = ""):
        if new_state not in self.VALID_TRANSITIONS.get(self.current_state, []):
            raise StateTransitionError(f"Invalid transition from {self.current_state} to {new_state}")
        
        self.state_history.append({"from": self.current_state.value, "to": new_state.value, "reason": reason})
        self.current_state = new_state
        self.persist()

    def persist(self):
        state_snapshot = {
            "session_id": self.session_id,
            "current_state": self.current_state.value,
            "state_data": self.state_data,
            "state_history": self.state_history,
        }
        with open(self.session_file, 'w') as f:
            json.dump(state_snapshot, f, indent=2)

    def restore(self) -> bool:
        if not os.path.exists(self.session_file):
            return False
        with open(self.session_file, 'r') as f:
            snapshot = json.load(f)
        self.current_state = State(snapshot["current_state"])
        self.state_data = snapshot["state_data"]
        self.state_history = snapshot["state_history"]
        return True
4.3. Základní MCP Server pro Nástroje
Tento kód (mcp_servers/base_mcp_server.py) je základem pro vytváření modulárních nástrojových serverů. Zapouzdřuje JSON-RPC komunikační logiku.

Python

# Zjednodušená verze z: mcp_servers/base_mcp_server.py

class BaseMCPServer:
    def __init__(self):
        self.tools = []

    def add_tool(self, name, function, description):
        self.tools.append({"name": name, "function": function, "description": description})

    async def handle_request(self, request_data):
        request = json.loads(request_data)
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        if method == "initialize":
            # ... vrátí seznam nástrojů
        elif method == "mcp/tool/execute":
            tool_name = params.get("name")
            tool = next((t for t in self.tools if t["name"] == tool_name), None)
            if tool:
                result = await self._execute_tool_function(tool["function"], ...)
                # ... vrátí výsledek
        # ... error handling

    async def _run_loop(self):
        # ... hlavní smyčka pro čtení ze stdin a zápis do stdout

    def run(self):
        asyncio.run(self._run_loop())
5. Doporučení pro Novou Verzi
Na základě analýzy doporučuji pro novou verzi projektu:

Zachovat architekturu Nomad V2: Proaktivní stavový stroj se ukázal jako nejrobustnější přístup.

Zachovat modulární MCP nástroje: Umožňuje to flexibilitu a snadné rozšiřování schopností agenta.

Sjednotit UI: Rozhodněte se, zda bude primární TUI, nebo webové rozhraní, a zaměřte se na jeho plnou funkčnost. Současný stav s dvěma neúplnými UI je matoucí.

Vylepšit BudgetTracker: Měl by sledovat nejen tokeny, ale i reálné náklady v USD na základě použitého modelu, jak je naznačeno v docs/GUARDIAN_OPENROUTER_PLAN.md.

Implementovat PlanManager plně: V současném NomadOrchestratorV2 není PlanManager explicitně využíván v hlavní smyčce. Pro komplexnější úkoly bude jeho plná integrace (vytvoření plánu a jeho postupné vykonávání) nezbytná.

Tento dokument by měl poskytnout veškeré potřebné vědění pro úspěšné znovuvytvoření a vylepšení projektu Sophia.