# 🎨 TUI Redesign & Architecture Modernization Plan

**Datum:** 2025-10-12  
**Verze:** 1.0  
**Status:** NÁVRH - Čeká na schválení  
**Autor:** GitHub Copilot AI Agent

---

## 📋 Executive Summary

Tento dokument popisuje kompletní redesign TUI (Terminal User Interface) pro Sophia/Nomad projekt s přechodem na **client-server architekturu**. Cílem je vytvořit robustní, transparentní a profesionální rozhraní pro interakci s NomadOrchestratorV2.

### Klíčové Změny

1. ✅ **Client-Server Architecture** - Backend běží nezávisle na TUI
2. ✅ **Modern TUI Design** - Přehledné, logické, profesionální
3. ✅ **Complete Transparency** - Real-time debugging, logging, state visibility
4. ✅ **Robust Deployment** - Docker, systemd, standalone modes
5. ✅ **Developer Experience** - Snadná instalace, spuštění, debugging

---

## 🏗️ Architektura

### Současný Stav (Problematický)

```
┌─────────────────────────────────────┐
│         TUI Application             │
│  ┌──────────────────────────────┐   │
│  │  NomadOrchestratorV2         │   │
│  │  (Běží přímo v TUI procesu)  │   │
│  └──────────────────────────────┘   │
│                                     │
│  Problémy:                          │
│  - TUI crash = Nomad crash          │
│  - Nelze připojit více klientů      │
│  - Těžké debugování                 │
│  - Docker compose up nefunguje      │
└─────────────────────────────────────┘
```

### Nový Design (Client-Server)

```
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND SERVER                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (port 8080)                              │   │
│  │  ├─ REST API (mission management)                        │   │
│  │  ├─ WebSocket (real-time updates)                        │   │
│  │  └─ Health checks                                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  NomadOrchestratorV2 Manager                             │   │
│  │  ├─ Session management                                   │   │
│  │  ├─ Mission queue                                        │   │
│  │  ├─ State broadcasting                                   │   │
│  │  └─ Event streaming                                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  NomadOrchestratorV2 Core                                │   │
│  │  StateManager | PlanManager | ReflectionEngine           │   │
│  │  RecoveryManager | BudgetTracker                         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                           ↑
            ┌──────────────┼──────────────┐
            │              │              │
      ┌─────▼─────┐  ┌─────▼─────┐  ┌────▼────┐
      │ TUI       │  │ Web UI    │  │ CLI     │
      │ Client    │  │ Client    │  │ Client  │
      │ (Textual) │  │ (Browser) │  │ (curl)  │
      └───────────┘  └───────────┘  └─────────┘
```

**Výhody:**
- ✅ Backend běží nezávisle (crash TUI ≠ crash Nomad)
- ✅ Více klientů současně (TUI + Web + API)
- ✅ Snadné debugování (připoj/odpoj klienta kdykoliv)
- ✅ Monitoring & logging oddělené
- ✅ Production-ready deployment

---

## 🎨 Nový TUI Design

### Layout Concept

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  Nomad AI Agent v0.8.9 │ Connected to localhost:8080 │ ⚡ Gemini 2.5 Flash ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ╭─ Mission Status ─────────────────────────────────────────────────────╮   ║
║  │ 🎯 Mission: Implement user authentication                            │   ║
║  │ 📊 State: EXECUTING_STEP (Step 3/7)                                  │   ║
║  │ ⏱️  Time: 00:02:34 | Tokens: 12,543 / 100,000 (12.5%)                │   ║
║  │ 💰 Cost: $0.15 | Budget: $5.00                                       │   ║
║  ╰───────────────────────────────────────────────────────────────────────╯   ║
║                                                                              ║
║  ╭─ Tabs ───────────────────────────────────────────────────────────────╮   ║
║  │ [Plan] [Execution] [Logs] [State] [Budget] [History]                │   ║
║  ├───────────────────────────────────────────────────────────────────────┤   ║
║  │                                                                       │   ║
║  │  ┌─ Current Step ───────────────────────────────────────────────┐    │   ║
║  │  │ Step 3: Create database schema                               │    │   ║
║  │  │                                                               │    │   ║
║  │  │ Thought Process:                                             │    │   ║
║  │  │ I need to design the user table with proper constraints...   │    │   ║
║  │  └───────────────────────────────────────────────────────────────┘    │   ║
║  │                                                                       │   ║
║  │  ┌─ Tool Execution ─────────────────────────────────────────────┐    │   ║
║  │  │ ➤ create_file_with_block                                     │    │   ║
║  │  │   File: database/schema.sql                                  │    │   ║
║  │  │   Status: ✅ Success (342 bytes written)                      │    │   ║
║  │  └───────────────────────────────────────────────────────────────┘    │   ║
║  │                                                                       │   ║
║  │  ┌─ Live Stream ─────────────────────────────────────────────────┐   │   ║
║  │  │ [13:45:23] Planning step 3...                                │   │   ║
║  │  │ [13:45:24] Calling LLM (gemini-2.0-flash-exp)...             │   │   ║
║  │  │ [13:45:27] Received response (1,234 tokens)                  │   │   ║
║  │  │ [13:45:27] Executing tool: create_file_with_block            │   │   ║
║  │  │ [13:45:28] ✅ Tool succeeded                                  │   │   ║
║  │  └───────────────────────────────────────────────────────────────┘    │   ║
║  │                                                                       │   ║
║  ╰───────────────────────────────────────────────────────────────────────╯   ║
║                                                                              ║
║  ╭─ Input ──────────────────────────────────────────────────────────────╮   ║
║  │ > New mission: Implement OAuth2 authentication                       │   ║
║  ╰───────────────────────────────────────────────────────────────────────╯   ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ F1:Help  F2:Pause  F3:Stop  F5:Refresh  Ctrl+C:Exit  Ctrl+L:Clear           ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### Tab Descriptions

#### 1. **Plan Tab** 📋
- Celý mission plán s progressem
- Vizuální indikace completed/current/pending steps
- Dependency grafy
- Timeline estimation

#### 2. **Execution Tab** ⚡
- Current step detail
- LLM thought process (streaming)
- Tool calls & results
- Live execution log

#### 3. **Logs Tab** 📝
- Strukturované logy (DEBUG/INFO/WARNING/ERROR)
- Filtrovatelné podle úrovně
- Searchable
- Export možnosti

#### 4. **State Tab** 🔄
- State machine visualization
- State history
- Transition log
- Session persistence info

#### 5. **Budget Tab** 💰
- Token usage breakdown
- Cost per LLM call
- Time tracking
- Budget alerts

#### 6. **History Tab** 📚
- Previous missions
- Session recovery
- Replay možnosti
- Statistics

---

## 🔌 Backend API Design

### REST Endpoints

```python
# Health & Info
GET  /api/v1/health              # Health check
GET  /api/v1/info                # Server info (version, model, etc.)

# Missions
POST /api/v1/missions            # Create new mission
GET  /api/v1/missions            # List all missions
GET  /api/v1/missions/{id}       # Get mission detail
DELETE /api/v1/missions/{id}     # Stop/cancel mission

# State
GET  /api/v1/state               # Current orchestrator state
GET  /api/v1/state/history       # State transition history

# Plan
GET  /api/v1/plan                # Current mission plan
GET  /api/v1/plan/steps/{id}     # Specific step detail

# Budget
GET  /api/v1/budget              # Budget summary
GET  /api/v1/budget/breakdown    # Detailed token/cost breakdown

# Sessions
GET  /api/v1/sessions            # List sessions
POST /api/v1/sessions/{id}/recover  # Recover crashed session
```

### WebSocket Protocol

```json
// Client → Server
{
  "type": "subscribe",
  "channels": ["mission", "logs", "state", "budget"]
}

// Server → Client: Mission updates
{
  "channel": "mission",
  "type": "state_change",
  "data": {
    "from": "PLANNING",
    "to": "EXECUTING_STEP",
    "reason": "Plan created"
  }
}

// Server → Client: Log stream
{
  "channel": "logs",
  "type": "log",
  "data": {
    "level": "INFO",
    "timestamp": "2025-10-12T13:45:23Z",
    "message": "Executing step 3..."
  }
}

// Server → Client: LLM thought stream
{
  "channel": "mission",
  "type": "llm_thinking",
  "data": {
    "chunk": "I need to create a database schema...",
    "step_id": 3
  }
}

// Server → Client: Tool execution
{
  "channel": "mission",
  "type": "tool_call",
  "data": {
    "tool": "create_file_with_block",
    "args": {"filepath": "schema.sql"},
    "status": "started"
  }
}
```

---

## 📦 Deployment Strategy

### Módy Spuštění

#### 1. **Development Mode** (Jednoduchý start)
```bash
# Terminál 1: Backend
./nomad server --dev

# Terminál 2: TUI Client
./nomad tui

# nebo vše najednou:
./nomad dev  # Spustí backend + TUI v tmux/screen
```

#### 2. **Docker Compose Mode** (Doporučeno)
```yaml
# docker-compose.yml
services:
  nomad-backend:
    build: .
    command: python -m backend.server
    ports:
      - "8080:8080"
    env_file: .env
    volumes:
      - ./logs:/app/logs
      - ./memory:/app/memory
    healthcheck:
      test: curl -f http://localhost:8080/api/v1/health
      interval: 10s

  nomad-tui:
    build: .
    command: python -m tui.client
    depends_on:
      nomad-backend:
        condition: service_healthy
    environment:
      - NOMAD_SERVER=http://nomad-backend:8080
    stdin_open: true
    tty: true
```

```bash
# Spuštění:
docker-compose up -d nomad-backend  # Backend běží na pozadí
docker-compose run nomad-tui        # TUI připojí se k backendu
```

#### 3. **Production Mode** (Systemd)
```bash
# Backend jako systemd service
sudo systemctl start nomad-backend
sudo systemctl enable nomad-backend

# TUI jako normální command
nomad tui
```

#### 4. **Standalone Mode** (Bez TUI)
```bash
# Backend API only
nomad server --port 8080

# Použití přes curl/API
curl -X POST http://localhost:8080/api/v1/missions \
  -H "Content-Type: application/json" \
  -d '{"goal": "Fix bug in auth.py"}'
```

### Installation Flow

```bash
# 1. Clone repo
git clone https://github.com/ShotyCZ/sophia.git
cd sophia

# 2. Setup (automatický script)
./scripts/setup.sh
# - Detekuje OS (Linux/Mac/Windows)
# - Instaluje dependencies (Python, Docker, etc.)
# - Vytvoří .env z template
# - Inicializuje databázi
# - Vytvoří systemd service files (Linux)

# 3. Konfigurace
nano .env  # Nastaví GEMINI_API_KEY

# 4. Test instalace
./nomad doctor
# ✅ Python 3.12+ installed
# ✅ Dependencies installed
# ✅ .env configured
# ✅ Gemini API key valid
# ✅ Docker available
# ✅ Ports 8080 available

# 5. První spuštění
./nomad dev  # Development mode
# nebo
docker-compose up  # Docker mode
# nebo
./nomad server & ./nomad tui  # Manual mode
```

---

## 🔍 Transparency & Debugging

### Built-in Debugging Features

#### 1. **Real-time State Inspector**
```
State Tab zobrazuje:
- Current state (EXECUTING_STEP)
- State history (IDLE → PLANNING → EXECUTING_STEP)
- Transition timestamps
- Transition reasons
- Session persistence status
```

#### 2. **LLM Call Tracer**
```
Pro každý LLM call:
- Full prompt (před/po)
- Model used (gemini-2.0-flash-exp)
- Tokens used (1,234 input / 567 output)
- Response time (2.3s)
- Cost ($0.0012)
- Success/retry status
```

#### 3. **Tool Execution Viewer**
```
Pro každý tool call:
- Tool name + full arguments
- Execution time
- Output (full/truncated)
- Success/failure status
- Error messages if failed
```

#### 4. **Log Export**
```bash
# Export logs to file
./nomad logs export --format json --output debug.json

# Tail logs in real-time
./nomad logs tail --level DEBUG

# Search logs
./nomad logs search "error" --since 1h
```

#### 5. **Mission Replay**
```bash
# Replay previous mission step-by-step
./nomad replay mission_abc123 --step-by-step

# Export mission trace
./nomad export mission_abc123 --format markdown
```

#### 6. **HTTP API Debug Endpoint**
```bash
# Get current state snapshot
curl http://localhost:8080/api/v1/debug/snapshot

# Get memory dump
curl http://localhost:8080/api/v1/debug/memory

# Get performance metrics
curl http://localhost:8080/api/v1/debug/metrics
```

---

## 📁 File Structure

```
sophia/
├── backend/                      # NEW: Backend server
│   ├── __init__.py
│   ├── server.py                 # FastAPI app
│   ├── websocket.py              # WebSocket handler
│   ├── models.py                 # Pydantic models
│   ├── orchestrator_manager.py   # Nomad wrapper
│   └── routes/
│       ├── missions.py
│       ├── state.py
│       ├── budget.py
│       └── debug.py
│
├── tui/                          # REDESIGNED: TUI client
│   ├── __init__.py
│   ├── client.py                 # Main TUI app (Textual)
│   ├── api_client.py             # HTTP/WS client
│   ├── widgets/
│   │   ├── mission_status.py
│   │   ├── plan_viewer.py
│   │   ├── execution_viewer.py
│   │   ├── log_viewer.py
│   │   ├── state_viewer.py
│   │   ├── budget_viewer.py
│   │   └── history_viewer.py
│   └── theme.py
│
├── core/                         # UNCHANGED: Core logic
│   ├── nomad_orchestrator_v2.py
│   ├── state_manager.py
│   ├── plan_manager.py
│   └── ...
│
├── scripts/
│   ├── setup.sh                  # NEW: Universal setup
│   ├── doctor.sh                 # NEW: Health check
│   └── install-systemd.sh        # NEW: Systemd installer
│
├── config/
│   ├── config.yaml
│   └── .env.template             # NEW: Environment template
│
├── docker/
│   ├── Dockerfile.backend        # NEW: Backend image
│   ├── Dockerfile.tui            # NEW: TUI image
│   └── docker-compose.yml        # UPDATED
│
├── nomad                         # NEW: CLI entrypoint
└── README.md                     # UPDATED
```

---

## 🚀 Implementation Roadmap

### Phase 1: Backend Foundation (2-3 days)
- [ ] Create FastAPI server (`backend/server.py`)
- [ ] Implement REST endpoints (missions, state, budget)
- [ ] Add WebSocket support for real-time updates
- [ ] Create OrchestratorManager wrapper
- [ ] Add health checks & monitoring
- [ ] Write backend tests

### Phase 2: TUI Client (2-3 days)
- [ ] Design new Textual layout
- [ ] Implement API client (HTTP + WebSocket)
- [ ] Create all tab widgets (Plan, Execution, Logs, State, Budget, History)
- [ ] Add real-time update handling
- [ ] Implement keyboard shortcuts
- [ ] Add theme customization

### Phase 3: Deployment (1-2 days)
- [ ] Create `setup.sh` script
- [ ] Create `nomad` CLI entrypoint
- [ ] Update Docker Compose
- [ ] Create systemd service files
- [ ] Write deployment docs
- [ ] Create `doctor.sh` diagnostic tool

### Phase 4: Testing & Polish (1-2 days)
- [ ] E2E testing (backend + TUI)
- [ ] Performance testing
- [ ] Error handling refinement
- [ ] Documentation update
- [ ] Demo video/GIF creation

**Total Estimate:** 6-10 days

---

## ✅ Success Criteria

### Functional Requirements
- ✅ Backend běží nezávisle na TUI
- ✅ TUI se může připojit/odpojit kdykoliv
- ✅ Multiple clients supported
- ✅ Real-time state updates
- ✅ Complete transparency (all LLM calls visible)
- ✅ Crash recovery works across client/server
- ✅ Docker Compose funguje správně

### Non-Functional Requirements
- ✅ Installation < 5 minut
- ✅ Startup time < 10 sekund
- ✅ UI response time < 100ms
- ✅ Memory usage < 500MB (backend)
- ✅ CPU usage < 50% (idle)

### User Experience
- ✅ Intuitivní ovládání
- ✅ Snadné debugování
- ✅ Profesionální vzhled
- ✅ Comprehensive docs
- ✅ Error messages jsou helpful

---

## 🤔 Open Questions

1. **WebUI Priority:** Chcete paralelně i web-based UI (Next.js/React)?
2. **Authentication:** Potřebujeme API authentication (API keys, JWT)?
3. **Multi-user:** Podporovat více uživatelů/sessions současně?
4. **Persistence:** Jaká databáze pro session storage? (SQLite/PostgreSQL/Redis)
5. **Monitoring:** Integrace s Prometheus/Grafana?

---

## 💡 Future Enhancements (Post-MVP)

- 🌐 Web UI (React/Next.js frontend)
- 📊 Advanced analytics dashboard
- 🔔 Notifications (Slack, Email, Discord)
- 🎮 Interactive debugging (breakpoints, step-through)
- 📸 Mission recording & playback
- 🤖 Multi-agent support
- 🔌 Plugin system pro custom tools
- 📱 Mobile app (React Native)

---

## 📝 Poznámky

- **Backwards Compatibility:** Starý TUI bude fungovat až do dokončení nového
- **Migration Path:** Smooth upgrade bez data loss
- **Documentation First:** Docs před kódem
- **Test Coverage:** Minimum 80% pro nový kód
- **Performance Budget:** Žádný feature nesmí zpomalit > 10%

---

## ✍️ Schválení & Review

**Pro pokračování potřebuji:**
1. ✅ Schválení architektury (client-server vs monolith)
2. ✅ Schválení TUI designu (layout, tabs)
3. ✅ Schválení deployment strategie (Docker Compose primary)
4. ✅ Odpovědi na Open Questions
5. ✅ Priority (co implementovat první)

**Po schválení:**
- Vytvořím detailní technical specs
- Začnu implementaci podle roadmapy
- Daily progress updates do WORKLOG.md

---

**Připraven začít jakmile dostanu 👍**

