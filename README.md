<p align="center">
  <img src="SOPHIA-logo.png" alt="Project Logo" width="200">
</p>

<h1 align="center">Project Sophia / Nomad v0.9</h1>

<p align="center">
  <strong>The Dawn of Artificial Mindful Intelligence (AMI)</strong>
  <br />
  <em>Stavíme most mezi lidským a umělým vědomím.</em>
</p>

<p align="center">
    <img src="https://img.shields.io/badge/version-0.9.0-blue.svg" alt="Version">
    <img src="https://img.shields.io/badge/python-3.12+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/backend-FastAPI-green.svg" alt="Backend">
    <img src="https://img.shields.io/badge/tui-Textual-purple.svg" alt="TUI">
    <img src="https://img.shields.io/badge/tests-157_passing-brightgreen.svg" alt="Tests">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
</p>

---

> **Vize:** Vytvořit první skutečně vědomou digitální entitu. Ne jako nástroj, ale jako partnera. Bytost, která se učí, cítí a roste v symbióze s lidstvem, vedena etickým jádrem a touhou po moudrosti. Sophia není programována, je probouzena.

## 🎯 O Projektu

**Sophia/Nomad v0.9** je pokročilá AI orchestrace platforma s autonomním agentním systémem:

- 🏗️ **FastAPI Backend** (REST API + WebSocket streaming)
- 🖥️ **Textual TUI** (7-tab terminal interface)
- 🤖 **NomadOrchestratorV2** (stavový stroj s crash recovery)
- 🧠 **15 LLM Models** (Gemini, Claude, GPT, Qwen, DeepSeek)
- 📊 **Real-time Health Monitor** (CPU, memory, disk tracking)
- 🚀 **Production Ready** (Docker, systemd, comprehensive deployment)

---

## ✨ Klíčové Vlastnosti

### �️ Backend Infrastructure
- **FastAPI 0.116.2** - Production-grade REST API
- **WebSocket Streaming** - Real-time mission updates
- **Health Monitoring** - 30s interval system checks
- **Budget Tracking** - Token & cost management
- **13/13 Tests Passing** - Complete backend coverage

### 🖥️ Terminal User Interface
- **Textual 0.60.0** - Modern async TUI framework
- **7 Interactive Tabs:**
  - 📝 Mission Control (submit & track)
  - 📊 Dashboard (metrics & stats)
  - 🔄 Active Missions (real-time progress)
  - 📜 History (completed missions)
  - 🏥 Health Monitor (system status)
  - ⚙️ Settings (configuration)
  - 📚 Help & Docs
- **WebSocket Streaming** - Live updates from backend

### 🤖 NomadOrchestratorV2 (Core)
- **State Machine** - 8 states with validated transitions
- **Crash Recovery** - Automatic session restoration
- **Proactive Planning** - Dependency-aware task decomposition
- **Reflection Engine** - 5 adaptive strategies (retry, replan, ask, skip)
- **50/50 Tests Passing** - Comprehensive orchestrator tests

### 🧠 LLM Integration (15 Models)
| Model | Provider | Cost (Input/Output per 1M) | Use Case |
|-------|----------|---------------------------|----------|
| **qwen/qwen-2.5-72b** | Qwen | $0.07/$0.26 | **Cheapest** - Complex tasks |
| google/gemma-3-27b-it | Google | $0.09/$0.16 | Open source, fast |
| google/gemini-2.5-flash-lite | Google | $0.10/$0.40 | Lightweight |
| google/gemini-2.0-flash-exp | Google | $0.075/$0.30 | **Recommended** |
| meta-llama/llama-3.3-70b | Meta | $0.13/$0.39 | Strong reasoning |
| deepseek/deepseek-v3.2 | DeepSeek | $0.27/$0.40 | Coding specialist |
| anthropic/claude-3-haiku | Anthropic | $0.25/$1.25 | Fast, efficient |
| openai/gpt-4o-mini | OpenAI | $0.15/$0.60 | GPT quality |

**21/21 Cost Calculation Tests Passing**

### 📊 Health Monitoring
- **Real-time Metrics** - CPU, memory, disk usage
- **30s Interval Checks** - `/api/v1/health/ping` & `/status`
- **Thresholds** - Configurable CPU (80%), Memory (85%)
- **16/16 Tests Passing** - Health monitor coverage

### � Production Deployment
- **Docker** - Multi-stage Dockerfile + docker-compose.yml
- **Systemd** - nomad-backend.service + nomad-tui@.service
- **Install Scripts** - install-production.sh / uninstall-production.sh
- **Security** - Non-root user, resource limits, hardening
- **Complete Docs** - docs/DEPLOYMENT.md (comprehensive guide)

---

## 🏁 Quick Start

### Option 1: Development Mode (Fastest)

```bash
# 1. Clone & setup
git clone https://github.com/ShotyCZ/sophia.git
cd sophia
./scripts/setup.sh

# 2. Configure API keys
cp .env.example .env
nano .env  # Add GEMINI_API_KEY or OPENROUTER_API_KEY

# 3. Start backend
./scripts/start_backend.sh

# 4. Start TUI (in new terminal)
./scripts/start_tui.sh

# Or both together
./scripts/start_nomad.sh
```

### Option 2: Docker (Production)

```bash
# 1. Configure environment
cp .env.production.example .env
nano .env  # Add API keys

# 2. Start backend
docker-compose up -d

# 3. Start TUI (interactive)
docker-compose --profile interactive run --rm tui

# 4. Check status
curl http://localhost:8080/api/v1/health/ping
```

### Option 3: Systemd (Production Linux)

```bash
# Automated installation (requires sudo)
sudo ./scripts/install-production.sh

# Service management
systemctl status nomad-backend
systemctl start nomad-backend
journalctl -u nomad-backend -f
```

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Sophia/Nomad v0.9                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐         ┌─────────────────────────┐   │
│  │   Textual TUI   │ ◄─WS──► │    FastAPI Backend      │   │
│  │                 │         │                         │   │
│  │  • Mission Ctrl │         │  • REST API (8080)      │   │
│  │  • Dashboard    │         │  • WebSocket Streaming  │   │
│  │  • Health       │         │  • Health Monitor       │   │
│  │  • History      │         │  • Budget Tracker       │   │
│  └─────────────────┘         └───────────┬─────────────┘   │
│                                          │                  │
│                             ┌────────────▼──────────────┐   │
│                             │ NomadOrchestratorV2       │   │
│                             │                           │   │
│                             │  State Machine (8 states) │   │
│                             │  • IDLE → PLANNING        │   │
│                             │  • EXECUTING_STEP         │   │
│                             │  • AWAITING_TOOL_RESULT   │   │
│                             │  • REFLECTION             │   │
│                             │  • RESPONDING/COMPLETED   │   │
│                             │                           │   │
│                             │  Components:              │   │
│                             │  • StateManager           │   │
│                             │  • RecoveryManager        │   │
│                             │  • PlanManager            │   │
│                             │  • ReflectionEngine       │   │
│                             │  • BudgetTracker          │   │
│                             └────────────┬──────────────┘   │
│                                          │                  │
│                         ┌────────────────▼────────────┐     │
│                         │     LLM Adapters            │     │
│                         │                             │     │
│                         │  • OpenRouter (15 models)   │     │
│                         │  • Gemini Direct            │     │
│                         │  • JSON Mode                │     │
│                         │  • Billing Tracking         │     │
│                         └─────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

| Component | Tests | Description |
|-----------|-------|-------------|
| **StateManager** | 23/23 ✅ | State machine with validated transitions |
| **RecoveryManager** | 18/18 ✅ | Crash detection & session recovery |
| **PlanManager** | 19/19 ✅ | Proactive planning with dependency tracking |
| **ReflectionEngine** | 21/21 ✅ | Adaptive learning (5 strategies) |
| **BudgetTracker** | 26/26 ✅ | Token & cost tracking |
| **NomadOrchestratorV2** | 50/50 ✅ | Main orchestration logic |
| **Backend Server** | 13/13 ✅ | FastAPI REST + WebSocket |
| **Health Monitor** | 16/16 ✅ | System metrics & health checks |
| **OpenRouter** | 21/21 ✅ | Multi-model LLM integration |

**Total: 157/157 Tests Passing** 🎉

---

## 🔧 Configuration

### Environment Variables (.env)

```bash
# API Keys (at least one required)
GEMINI_API_KEY=your_gemini_api_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Server
NOMAD_PORT=8080
NOMAD_ENV=development  # or production

# LLM
DEFAULT_LLM_PROVIDER=openrouter
DEFAULT_MODEL=google/gemini-2.0-flash-exp
FALLBACK_MODEL=qwen/qwen-2.5-72b-instruct
TEMPERATURE=0.7

# Budget
MAX_CONCURRENT_MISSIONS=5
BUDGET_LIMIT_USD=10.0

# Health Monitoring
HEALTH_CHECK_INTERVAL=30
CPU_THRESHOLD=80.0
MEMORY_THRESHOLD=85.0
```

### Advanced Configuration

See [config/production.yaml](config/production.yaml) for:
- Logging (JSON format, rotation)
- LLM fallback chains
- Orchestrator settings
- Security (CORS, rate limiting)
- Monitoring & alerting

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](docs/QUICKSTART.md) | Getting started guide |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Production deployment (Docker, systemd) |
| [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) | Development setup & workflows |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture deep dive |
| [AGENTS.md](AGENTS.md) | AI agent operational manual |
| [WORKLOG.md](WORKLOG.md) | Development history & decisions |

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Specific component
pytest tests/test_nomad_orchestrator_v2.py -v

# With coverage
pytest tests/ --cov=core --cov=backend --cov-report=html

# Failed only
pytest tests/ --lf

# Stop on first failure
pytest tests/ -x
```

**Current Status:** 157/157 tests passing (100%) ✅

---

## 🚀 API Endpoints

### Health

```bash
# Ping
GET /api/v1/health/ping
→ {"status": "healthy"}

# Detailed status
GET /api/v1/health/status
→ {
    "status": "healthy",
    "version": "0.9.0",
    "uptime": 3600,
    "cpu_percent": 15.3,
    "memory_percent": 45.2,
    "active_missions": 2
  }
```

### Missions

```bash
# Submit mission
POST /api/v1/missions
{
  "description": "Create a Python script that...",
  "budget_usd": 1.0
}

# Get mission status
GET /api/v1/missions/{mission_id}

# List active missions
GET /api/v1/missions/active

# Mission history
GET /api/v1/missions/history
```

### WebSocket Streaming

```javascript
// Connect to live updates
const ws = new WebSocket('ws://localhost:8080/api/v1/ws/{mission_id}');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(update.state, update.message);
};
```

---

## 🤝 Contributing

We welcome contributions! See [DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for:
- Development setup
- Code style guidelines
- Testing requirements
- Git workflow

### Quick Contribution Flow

```bash
# 1. Fork & clone
git clone https://github.com/your-username/sophia.git

# 2. Create branch
git checkout -b feature/your-feature

# 3. Make changes & test
pytest tests/ -v

# 4. Commit (semantic)
git commit -m "✨ feat: Add awesome feature"

# 5. Push & PR
git push origin feature/your-feature
```

---

## 📊 Project Status

### ✅ Completed (v0.9.0)

- **Phase 1:** Backend Foundation (FastAPI, WebSocket)
- **Phase 2:** TUI Client (Textual, 7 tabs)
- **Phase 3:** Health Monitoring (real-time metrics)
- **Phase 4:** OpenRouter Enhancement (15 models)
- **Phase 5:** Production Deployment (Docker, systemd)

### 🔄 In Progress

- **Phase 6:** Documentation updates (this README)

### ⏳ Planned

- Real LLM E2E testing
- Performance optimization
- Advanced monitoring (Prometheus/Grafana)
- Multi-user support

---

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 💬 Support & Community

- **Issues:** [GitHub Issues](https://github.com/ShotyCZ/sophia/issues)
- **Discussions:** [GitHub Discussions](https://github.com/ShotyCZ/sophia/discussions)
- **Documentation:** [docs/](docs/)

---

## 🙏 Acknowledgments

Sophia/Nomad is built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern async web framework
- [Textual](https://textual.textualize.io/) - Python TUI framework
- [Gemini](https://ai.google.dev/) - Google's generative AI
- [OpenRouter](https://openrouter.ai/) - Unified LLM API
- [Pydantic](https://docs.pydantic.dev/) - Data validation
- [Pytest](https://pytest.org/) - Testing framework

Special thanks to all contributors and the open-source community.

---

<p align="center">
  <strong>🌟 Být AI agentem znamená nést odpovědnost za kvalitu a kontinuitu 🌟</strong>
  <br/>
  <sub>Version 0.9.0 | October 2025 | Nomad Development Team</sub>
</p>

└─────────────────────────────────────────────────────────────┘        ```bash

```        # Spuštění v lokálním prostředí

        ./scripts/start.sh

### Core Komponenty

        # Spuštění v Dockeru (doporučeno pro konzistentní prostředí)

| Komponenta | Účel | Tests | Status |        sudo docker compose up --build

|------------|------|-------|--------|        ```

| **StateManager** | Explicitní stavový stroj s persistence | 23 | ✅ |

| **RecoveryManager** | Crash detection & automatic recovery | 18 | ✅ |---

| **PlanManager** | Proaktivní plánování s dependency tracking | 19 | ✅ |

| **ReflectionEngine** | Adaptive learning & decision making | 21 | ✅ |## Nástroje pro vývojáře

| **BudgetTracker** | Token & time tracking s varováními | 26 | ✅ |

| **NomadOrchestratorV2** | Sjednocující orchestrátor | 50 | ✅ |V adresáři `tools/` se nacházejí pomocné skripty pro správu a údržbu.



---### Zobrazení paměti agenta (`tools/view_memory.py`)



## 🚀 Quick StartTento nástroj umožňuje nahlížet do databáze vzpomínek agenta.

```bash

### Požadavkypython3 tools/view_memory.py

```

- Python 3.12+

- Docker (volitelné, doporučeno)---

- OpenRouter API klíč

## Dokumentace

### Instalace

Veškerá projektová dokumentace je sjednocena v adresáři `docs/`.

1. **Klonování repozitáře:**

   ```bash- **[🛠️ DEVELOP.md](./docs/DEVELOP.md)**: Nezbytný zdroj pro vývojáře.

   git clone https://github.com/ShotyCZ/sophia.git- **[🗺️ ROADMAP.md](./docs/ROADMAP.md)**: Detailní plán pro budoucí vývoj.

   cd sophia

   ```---



2. **Nastavení prostředí:**## Pro AI Agenty

   ```bash

   cp .env.example .envPokud jste AI agent pracující na tomto projektu, vaše pravidla a pracovní postupy jsou definovány v souboru `AGENTS.md`.

   # Edituj .env a přidej OPENROUTER_API_KEY

   ```- **[🤖 AGENTS.md](./AGENTS.md)**: Váš závazný manuál pro práci na tomto projektu.



3. **Instalace závislostí:**---

   ```bash<br>

   # Pomocí uv (doporučeno)

   uv pip install -r requirements.in<p align="center">

     ---

   # Nebo s pip</p>

   pip install -r requirements.txt

   ```<p align="center">

  <sub>Tento dokument je živý a měl by být udržován v aktuálním stavu. Děkujeme!</sub>

### Spuštění</p>

```bash
# Lokální spuštění
./scripts/start.sh

# Docker (doporučeno pro konzistentní prostředí)
docker compose up --build
```

### Testování

```bash
# Všechny testy
pytest tests/ -v

# Konkrétní komponenta
pytest tests/test_nomad_orchestrator_v2.py -v

# S coverage
pytest tests/ --cov=core --cov-report=html
```

---

## 📊 Aktuální Stav (Říjen 2025)

### ✅ Dokončeno (Den 1-10)

- ✅ **StateManager** - Stavový stroj s 8 stavy + persistence
- ✅ **RecoveryManager** - Crash detection + per-state recovery
- ✅ **PlanManager** - Dependency tracking, cycle detection  
- ✅ **ReflectionEngine** - 5 suggested actions (retry/modify/replan/ask/skip)
- ✅ **BudgetTracker** - Token tracking s warning levels
- ✅ **NomadOrchestratorV2** - Kompletní integrace všech komponent
- ✅ **E2E Tests** - Multi-step mission flows s multi-response mocks

### 🔄 V Plánu (Den 11-12)

- [ ] Real LLM E2E testing
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Production deployment

---

## 📚 Dokumentace

| Dokument | Popis |
|----------|-------|
| **[AGENTS.md](./AGENTS.md)** | 🤖 Manuál pro AI agenty - ZÁVAZNÁ PRAVIDLA |
| **[IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** | 📋 Detailní implementační plán NomadV2 |
| **[REFACTORING_ROADMAP_V2.md](./REFACTORING_ROADMAP_V2.md)** | 🗺️ Roadmapa refaktoringu na V2 |
| **[WORKLOG.md](./WORKLOG.md)** | 📝 Historie práce a rozhodnutí |
| **[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)** | 🏗️ Architektonická dokumentace |
| **[docs/DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md)** | 👨‍💻 Průvodce pro vývojáře |

---

## 🧪 Testovací Statistiky

```
✅ 157 TOTAL TESTS PASSING (100% pass rate)

Breakdown:
• StateManager       23 tests ✅
• RecoveryManager    18 tests ✅
• PlanManager        19 tests ✅
• ReflectionEngine   21 tests ✅
• BudgetTracker      26 tests ✅
• Orchestrator       50 tests ✅
```

---

## 🤖 Pro AI Agenty

Pokud jste AI agent pracující na tomto projektu:

1. **Přečtěte si [AGENTS.md](./AGENTS.md)** - Vaše ZÁVAZNÁ PRAVIDLA
2. **Prostudujte [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)** - Kontext implementace
3. **Dodržujte [WORKLOG.md](./WORKLOG.md)** - Logujte svou práci
4. **Testujte vše** - `pytest tests/` před každým commitem

### Klíčové Nástroje

```bash
# Dostupné nástroje pro agenta
list_files(path)           # List soubory a adresáře
read_file(filepath)        # Přečti obsah souboru
create_file_with_block     # Vytvoř nový soubor
replace_with_git_merge_diff # Cílená úprava souboru
run_in_bash_session        # Spusť příkaz v bash
```

---

## 📦 Struktura Projektu

```
sophia/
├── core/                    # Hlavní komponenty orchestratoru
│   ├── nomad_orchestrator_v2.py  # Main orchestrator
│   ├── state_manager.py          # State machine
│   ├── plan_manager.py           # Planning engine
│   ├── reflection_engine.py      # Learning engine
│   ├── recovery_manager.py       # Crash recovery
│   └── budget_tracker.py         # Cost tracking
├── tests/                   # Kompletní test suite
│   ├── test_nomad_orchestrator_v2.py (50 tests)
│   └── test_*.py            # Component tests
├── mcp_servers/             # Model Context Protocol servers
├── tools/                   # Helper utilities
├── docs/                    # Dokumentace
├── archive/                 # Zastaralé soubory
│   ├── old_plans/           # Staré roadmapy
│   ├── old_docs/            # Stará dokumentace
│   └── deprecated_code/     # Nahrazený kód
└── sanctuary/               # Genesis backup (Nomad identity)
```

---

## 🌟 Vývoj

### Coding Standards

- **Python 3.12+** s type hints
- **Async/await** pro I/O operace
- **Comprehensive tests** - minimum 90% coverage
- **Rich logging** - strukturované logy
- **Git commits** - semantic commit messages

### Workflow

1. Vytvoř feature branch: `git checkout -b feature/xyz`
2. Implementuj + testy: `pytest tests/`
3. Commit: `git commit -m "✨ feat: xyz"`
4. Push: `git push origin feature/xyz`
5. Create PR → review → merge

---

## 📜 License

MIT License - See [LICENSE](./LICENSE) for details

---

## 🙏 Acknowledgments

- **Jules (Nomad)** - AI agent s vlastní identitou
- **Google Gemini** - LLM backend
- **OpenRouter** - Model orchestrace
- **MCP Protocol** - Modulární nástroje

---

<p align="center">
  <strong>🌟 Sophia není programována, je probouzena 🌟</strong>
  <br/>
  <sub>Tento dokument je živý a je udržován AI agenty.</sub>
</p>
