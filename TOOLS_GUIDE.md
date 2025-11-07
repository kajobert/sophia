# 🛠️ SOPHIA Tools & Control Center

## 🎯 Přehled

SOPHIA nyní obsahuje kompletní sadu nástrojů pro testování, debugging a správu systému:

### 1️⃣ **Playwright Plugin** - Browser Control pro SOPHIA
- 📁 Soubor: `plugins/cognitive_browser_control.py`
- 🎯 Účel: Umožňuje SOPHIA autonomně testovat své webové rozhraní
- 🔧 Funkce:
  - `browser_navigate(url)` - Navigace na URL
  - `browser_click(selector)` - Kliknutí na element
  - `browser_fill(selector, text)` - Vyplnění formuláře
  - `browser_screenshot(name)` - Screenshot stránky
  - `browser_get_text(selector)` - Získání textu
  - `browser_execute_js(script)` - Spuštění JavaScriptu
  - `test_dashboard()` - **Kompletní self-test Dashboard**

**Příklad použití:**
```python
# SOPHIA může sama testovat svůj Dashboard!
plugin = cognitive_browser_control
result = await plugin.test_dashboard()
# Automaticky otestuje Overview, Chat a Logs záložky
# Vytvoří screenshots
# Vrátí report s výsledky
```

### 2️⃣ **TUI Control Center** - Terminálové menu
- 📁 Soubor: `sophia_control.py`
- 🎯 Účel: Interaktivní menu pro správu SOPHIA z terminálu
- 🚀 Spuštění: `python sophia_control.py`

**Hlavní kategorie:**

#### 1. 🚀 SOPHIA Control
- Start/Stop/Restart SOPHIA
- Různé režimy: --once, daemon, WebUI
- Real-time log monitoring

#### 2. 🧪 Testing & Debugging
- Všechny testy (pytest)
- Dashboard E2E testy
- Interaktivní debugger
- Model escalation test

#### 3. 🔍 Monitoring & Logs
- Live log viewer
- Filtrování errorů
- Task queue monitoring
- Database status

#### 4. 🛠️ Development Tools
- Dashboard screenshots
- Database backup
- Clear queue
- Linter (ruff)

#### 5. 🌐 Ollama Management
- List/pull/test models
- Test llama3.1:8b
- Test qwen2.5:14b
- Service status

#### 6. 📊 Dashboard Tools
- API endpoint testing
- Send test messages
- Export data

#### 7. 🔧 Advanced
- Python shell s SOPHIA context
- SQLite shell
- Git operations
- System diagnostics

**Příklad použití:**
```bash
cd /mnt/c/SOPHIA/sophia
python sophia_control.py

# Zobrazí se menu:
# 11. Start SOPHIA (--once mode)
# 22. Run Dashboard E2E tests
# 42. Generate screenshots
# atd...

# Zadej číslo a stiskni Enter
```

### 3️⃣ **Dashboard Tools Tab** - GUI nástroje
- 📁 Soubor: `frontend/dashboard.html` (nová záložka 🛠️ Tools)
- 🎯 Účel: Webové GUI pro spouštění nástrojů přímo z Dashboard

**Kategorie nástrojů:**

#### 🧪 Testing & Debugging
- 📸 Test Dashboard (Screenshots)
- 🔬 Run E2E Tests
- 🔌 Test All Plugins
- 🐛 Interactive Debugger

#### 🌐 Browser Automation
- 🤖 **SOPHIA Self-Test Dashboard** (autonomní test!)
- 📸 Capture All Tabs
- 🔍 View Trace Debugger

#### ⚙️ System Control
- 💾 Backup Database
- 🗑️ Clear Task Queue
- 🔄 Restart SOPHIA
- 📋 View Full Logs

#### 🤖 Model Management
- 🦙 Test llama3.1:8b
- 🧠 Test qwen2.5:14b
- 📋 List All Models
- 🚀 Test Model Escalation

#### 🔬 Diagnostics
- 📊 System Information
- ❤️ Health Check
- 📤 Export Dashboard Data
- 🩺 Full Diagnostics

#### ⚡ Quick Actions
- 🖥️ Open in New Tab
- 🔄 Refresh All Data
- 🧹 Clear Console
- 📥 Download Logs

**Příklad použití:**
1. Otevři Dashboard: http://127.0.0.1:8000/dashboard
2. Klikni na záložku **🛠️ Tools**
3. Vyber nástroj (např. "🤖 SOPHIA Self-Test Dashboard")
4. Sleduj výstup v "Tool Output" konzoli

---

## 📸 Debugging Scripts

### `dashboard_interactive_test.py`
Automatický test s videem a trace:
```bash
# Viditelný browser (slow motion)
python dashboard_interactive_test.py

# Rychlejší
python dashboard_interactive_test.py --slow 200

# Headless
python dashboard_interactive_test.py --headless

# Pouze WebSocket test
python dashboard_interactive_test.py --ws-only
```

**Výstupy:**
- 8 debug screenshotů
- Video nahrávka celého testu
- Trace soubor pro analýzu: `playwright show-trace screenshots/debug/trace.zip`

### `dashboard_debug.py`
Interaktivní debugger s hooks:
```bash
# Kompletní test s pauzami
python dashboard_debug.py --interactive

# Pouze chat
python dashboard_debug.py --scenario chat

# S vlastní zprávou
python dashboard_debug.py --scenario chat --message "Kolik máš pluginů?"

# Pouze overview
python dashboard_debug.py --scenario overview
```

**Co zachytává:**
- Console logs (všechny typy)
- Network requesty (/api/*)
- WebSocket zprávy (send/receive)
- Page errors (JavaScript)
- Screenshots po každém kroku
- JSON report s historií

### `capture_dashboard_screenshots.py`
Rychlé screenshoty:
```bash
python capture_dashboard_screenshots.py
```
Vytvoří 3 screenshoty (Overview, Chat, Logs) v `screenshots/`

---

## 🤖 SOPHIA Autonomous Testing

**SOPHIA může nyní testovat SAMA SEBE!**

### Přes API:
```bash
curl -X POST http://127.0.0.1:8000/api/tools/browser-test
```

### Přes Chat:
1. Otevři Dashboard
2. Jdi do Chat
3. Napiš: "Otestuj prosím své webové rozhraní"
4. SOPHIA použije `cognitive_browser_control` plugin
5. Autonomně otestuje Dashboard
6. Vrátí report s výsledky a screenshoty

### Přes Tools tab:
1. Dashboard → Tools
2. Klikni "🤖 SOPHIA Self-Test Dashboard"
3. Sleduj output v konzoli

---

## 🎯 Workflow příklady

### Scenario 1: Daily Testing
```bash
# Spusť TUI menu
python sophia_control.py

# Zadej:
22  # Dashboard E2E tests
42  # Generate screenshots
35  # Check database status
```

### Scenario 2: Debugging Issues
```bash
# Interaktivní debug
python dashboard_debug.py --scenario all --interactive

# Pak analyzuj trace
playwright show-trace screenshots/debug/trace.zip

# Prohlédni si logy
python sophia_control.py
→ 31  # View logs
```

### Scenario 3: SOPHIA Self-Testing
```bash
# Dashboard → Tools → 🤖 SOPHIA Self-Test Dashboard
# Nebo z terminálu:
curl -X POST http://127.0.0.1:8000/api/tools/browser-test | python3 -m json.tool
```

### Scenario 4: Model Testing
```bash
python sophia_control.py

53  # Test llama3.1:8b
54  # Test qwen2.5:14b
25  # Test model escalation (konverzace s eskalací)
```

---

## 📋 API Endpoints

### Tools API
```bash
# Spustit nástroj
POST /api/tools/run
{
  "tool": "test_dashboard"  # název nástroje
}

# Browser test
POST /api/tools/browser-test
```

**Dostupné nástroje:**
- `test_dashboard` - Screenshot test
- `test_e2e` - Playwright E2E testy
- `test_plugins` - Plugin testy
- `backup_db` - Záloha databáze
- `clear_queue` - Vyčistit task queue
- `test_llama` - Test llama3.1:8b
- `test_qwen` - Test qwen2.5:14b
- `list_models` - Seznam Ollama modelů
- `system_info` - Systémové info
- `check_health` - Health check
- `export_data` - Export dat
- `run_diagnostics` - Diagnostika

---

## 🚀 Quick Start

1. **Spusť SOPHIA s Dashboard:**
```bash
python sophia_control.py
→ 13  # Start SOPHIA with WebUI
```

2. **Otevři Dashboard:**
```
http://127.0.0.1:8000/dashboard
```

3. **Vyzkoušej Tools:**
- Klikni na 🛠️ Tools
- Zkus "🤖 SOPHIA Self-Test Dashboard"
- Sleduj jak SOPHIA testuje sama sebe!

4. **Testuj z terminálu:**
```bash
python dashboard_debug.py --interactive
```

---

## 💡 Tips

- **TUI menu** je nejrychlejší pro běžné operace
- **Dashboard Tools** pro vizuální kontrolu
- **Debug scripty** pro hloubkovou analýzu
- **SOPHIA self-test** pro autonomní QA
- Kombinuj nástroje pro komplexní testing!

---

Vše je připraveno! SOPHIA má nyní plnou kontrolu nad svým testováním a může autonomně validovat své vlastní rozhraní. 🎉
