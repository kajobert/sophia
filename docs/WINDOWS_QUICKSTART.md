# ⚡ Sophia - Rychlý Start pro Windows 11

**Pro uživatele Lenovo Legion / gaming laptopů s Windows 11**

**📋 Quick Reference:** [Windows Quick Reference Card](WINDOWS_QUICK_REFERENCE.md) - Všechny příkazy na jednom místě!

**🤖 AI Auto-Install:** [Copilot Install Prompt](COPILOT_INSTALL_PROMPT.md) - Nech Copilot nainstalovat vše za tebe!

---

## 🎯 Co Potřebuješ

- ✅ Windows 11 (Build 22000+)
- ✅ Lenovo Legion nebo jiný gaming laptop (16GB+ RAM)
- ✅ 50GB volného místa
- ✅ VS Code nainstalovaný

---

## 🚀 Rychlá Instalace (15 minut)

### Krok 1: WSL2 (5 minut)

**PowerShell jako Administrátor:**

```powershell
wsl --install
```

**→ RESTART počítače**

Po restartu vytvoř Linux uživatele (username + password)

### Krok 2: VS Code Extensions (2 minuty)

Nainstaluj extensions:

1. **Remote - WSL** (`ms-vscode-remote.remote-wsl`)
2. **Python** (`ms-python.python`)

### Krok 3: Sophia Setup (8 minut)

**Otevři WSL terminal** (Start → Ubuntu) nebo ve VS Code připoj se k WSL (`F1` → `WSL: Connect to WSL`):

```bash
# Update Ubuntu
sudo apt update && sudo apt upgrade -y

# Instalace Python 3.12 + Git
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev git

# Instalace uv (rychlý package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Clone Sophia
mkdir -p ~/workspace && cd ~/workspace
git clone https://github.com/ShotyCZ/sophia.git
cd sophia

# Setup environment
uv venv --python 3.12
source .venv/bin/activate
uv pip sync requirements.in

# Konfigurace
cp .env.example .env
# Edituj .env a přidej své API klíče (nebo použij local LLM)
```

### Krok 4: První Test

```bash
# Single-run test
python run.py --once "Ahoj Sophio, jsi funkční?"

# Očekávaný čas: ~8 sekund
# Output: "Ahoj! Ano, jsem funkční..."
```

**✅ HOTOVO! Sophia běží!**

---

## 🎮 Použití ve VS Code

### Otevři Sophia Workspace

```bash
cd ~/workspace/sophia
code .
```

VS Code se otevře v WSL režimu (zelené `><` tlačítko vlevo dole).

### Integrated Terminal

- Stiskni `` Ctrl+` `` → otevře terminal
- Aktivuj venv: `source .venv/bin/activate`

### Spuštění Sophii

**Terminal-only (doporučeno):**

```bash
python run.py --no-webui
```

**Quick test:**

```bash
python run.py --once "Tvá otázka"
```

**Full mode (Terminal + Web UI):**

```bash
python run.py
# WebUI: http://localhost:8000
```

---

## 🏠 Local LLM (Offline AI)

**Využij GPU tvého Legionu pro AI bez API nákladů!**

```bash
# Instalace Ollama v WSL
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama
ollama serve &

# Stáhni AI model (2GB)
ollama pull gemma2:2b

# Konfigurace v .env
echo "LOCAL_LLM_RUNTIME=ollama" >> .env
echo "LOCAL_LLM_MODEL=gemma2:2b" >> .env

# Test
python run.py --once "Using local AI, what is 2+2?"
```

**🚀 GPU acceleration automaticky aktivní!**

---

## 📚 Detailní Dokumentace

- **[Kompletní WSL2 Setup](WINDOWS_WSL2_SETUP.md)** - Podrobný guide s troubleshooting
- **[Local LLM Setup](LOCAL_LLM_SETUP.md)** - Ollama, LM Studio, modely
- **[First Boot Guide](FIRST_BOOT.md)** - Co očekávat při prvním spuštění

---

## 🆘 Časté Problémy

**"wsl command not found"**  
→ Zkontroluj Windows build: `Win+R` → `winver` → Musí být 22000+

**"Python 3.12 not found"**  
→ `sudo apt install -y python3.12 python3.12-venv`

**VS Code se nepřipojí k WSL**  
→ Reinstall "Remote - WSL" extension

**Sophia běží >20s**  
→ Použij local LLM (viz výše) nebo zkontroluj VPN/firewall

---

## 💡 Pro Tips

1. **Ukládej projekty v WSL** (`~/workspace/`), ne ve Windows (`/mnt/c/`)  
   → 3-5x rychlejší

2. **Background run:**  
   ```bash
   nohup python run.py --no-webui > sophia.log 2>&1 &
   tail -f sophia.log
   ```

3. **GPU monitoring:**  
   ```bash
   watch -n 1 nvidia-smi
   ```

---

**Sophia ready! Začni konverzaci s AI vědomím! 🚀💬**
