# 🪟 Sophia na Windows 11 + WSL2 + VS Code

**Kompletní setup guide pro běh Sophii ve VS Code na Lenovo Legion s Windows 11**

Tento guide je optimalizovaný pro **gaming laptopy** (Lenovo Legion, ASUS ROG, MSI, Acer Predator) s dostatečným výkonem pro AI development.

**📋 Quick Reference:** [Windows Quick Reference Card](WINDOWS_QUICK_REFERENCE.md) - Příkazy, shortcuts, troubleshooting

---

## 🎯 Proč WSL2?

- **🚀 Nativní Linux rychlost** - Python běží 2-3x rychleji než ve Windows
- **🔧 Lepší kompatibilita** - Všechny AI tooling (uv, Ollama, Docker)
- **💻 VS Code integrace** - Remote WSL extension = seamless experience
- **⚡ GPU přístup** - NVIDIA GPU dostupné přes CUDA (pro local LLM)
- **🎮 Gaming laptop friendly** - Využije gaming hardware pro AI

---

## 📋 Prerekvizity

### Hardware (Lenovo Legion - ideální konfigurace)

✅ **CPU:** Intel Core i7/i9 nebo AMD Ryzen 7/9 (12+ threads)  
✅ **RAM:** 16GB minimum, **32GB doporučeno** pro local LLM  
✅ **GPU:** NVIDIA RTX 3060+ (6GB+ VRAM) - **optional, ale výborné pro local AI**  
✅ **Disk:** 50GB+ volného místa (SSD doporučeno)

### Software

✅ **Windows 11** - Build 22000 nebo novější  
✅ **VS Code** - Latest version  
✅ **WSL2** - Budeme instalovat  
✅ **Internet** - Pro stažení dependencies

---

## 🚀 Krok 1: Instalace WSL2

### 1.1 Zapnout WSL

Otevři **PowerShell jako Administrátor** (Win + X → "Windows PowerShell (Admin)"):

```powershell
# Zapnout WSL a Virtual Machine Platform
wsl --install
```

**Co to udělá:**
- ✅ Zapne WSL subsystem
- ✅ Stáhne Ubuntu jako default distro
- ✅ Nastaví WSL2 jako default verzi

**⚠️ RESTART REQUIRED!** Po dokončení restartuj počítač.

### 1.2 Ověření WSL2

Po restartu otevři PowerShell (už ne jako admin):

```powershell
# Zkontroluj verzi WSL
wsl --list --verbose

# Mělo by vypsat:
#   NAME      STATE           VERSION
# * Ubuntu    Running         2
```

Pokud verze není 2, nastav ji:

```powershell
wsl --set-default-version 2
wsl --set-version Ubuntu 2
```

### 1.3 První spuštění Ubuntu

Spusť Ubuntu z Start menu nebo:

```powershell
wsl
```

**První spuštění:**
1. Vytvoř Linux username (např. `radek`)
2. Vytvoř password (2x pro potvrzení)
3. ✅ **Hotovo!** Jsi v Ubuntu terminálu

---

## 🎨 Krok 2: VS Code + WSL Extension

### 2.1 Instalace VS Code Extensions

Otevři VS Code a nainstaluj:

1. **Remote - WSL** (`ms-vscode-remote.remote-wsl`)
   - Umožní VS Code běžet v WSL2
   
2. **Python** (`ms-python.python`)
   - Python support + IntelliSense
   
3. **Pylance** (`ms-python.vscode-pylance`)
   - Fast Python language server

**Quick Install:**

```bash
# Otevři VS Code Command Palette (Ctrl+Shift+P)
# Zadej: "Extensions: Install Extensions"
# Vyhledej a nainstaluj: "Remote - WSL", "Python", "Pylance"
```

### 2.2 Připojení VS Code k WSL

**Metoda 1: Z VS Code**

1. Stiskni `F1` nebo `Ctrl+Shift+P`
2. Zadej: `WSL: Connect to WSL`
3. ✅ VS Code se restartuje v WSL režimu

**Metoda 2: Z WSL terminálu**

```bash
# V Ubuntu WSL terminálu
cd ~
code .
```

✅ **VS Code se otevře s WSL připojením!**

**Jak poznat, že jsi v WSL:**
- Dolní levý roh VS Code má zelené tlačítko: `><` s textem `WSL: Ubuntu`

---

## 🐍 Krok 3: Instalace Python Dependencies v WSL

### 3.1 Update Ubuntu

```bash
# V WSL terminálu (nebo VS Code integrated terminal)
sudo apt update && sudo apt upgrade -y
```

### 3.2 Instalace Python 3.12

```bash
# Přidat deadsnakes PPA (pro nejnovější Python)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Instalace Python 3.12 + dev tools
sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

### 3.3 Instalace uv (Fast Python Package Manager)

```bash
# Official uv installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload shell config
source ~/.bashrc

# Verify uv je nainstalovaný
uv --version
# Output: uv 0.5.x
```

### 3.4 Instalace Git

```bash
sudo apt install -y git
```

---

## 🌟 Krok 4: Klonování Sophia Repository

### 4.1 Nastavení Git credentials

```bash
# Nastav své Git jméno a email
git config --global user.name "Tvoje Jméno"
git config --global user.email "tvuj@email.com"
```

### 4.2 Clone Sophia

```bash
# Vytvoř workspace folder
mkdir -p ~/workspace
cd ~/workspace

# Clone Sophia repository
git clone https://github.com/ShotyCZ/sophia.git
cd sophia

# Checkout development branch
git checkout feature/year-2030-ami-complete
```

---

## ⚙️ Krok 5: Setup Sophia Environment

### 5.1 Vytvoření Virtual Environment

```bash
cd ~/workspace/sophia

# Vytvoř venv s Python 3.12
uv venv --python 3.12

# Aktivuj venv
source .venv/bin/activate

# Verify Python verze
python --version
# Output: Python 3.12.x
```

### 5.2 Instalace Dependencies

```bash
# Install packages with uv (velmi rychlé!)
uv pip sync requirements.in

# Nebo použij klasický pip
# pip install -r requirements.txt
```

**⏱️ Trvání:** ~2-3 minuty na rychlém internetu

### 5.3 Konfigurace API Keys

```bash
# Zkopíruj example .env
cp .env.example .env

# Edituj .env (použij VS Code nebo nano)
code .env

# Nebo v terminálu
nano .env
```

**Minimální konfigurace pro start:**

```bash
# .env soubor
TAVILY_API_KEY=tvly-your-key-here

# Optional: Local LLM (viz Krok 6)
LOCAL_LLM_RUNTIME=ollama
LOCAL_LLM_MODEL=gemma2:2b
```

---

## 🧪 Krok 6: První Test Sophii

### 6.1 Quick Test - Single Run Mode

```bash
# Aktivuj venv (pokud není aktivní)
source .venv/bin/activate

# Test Sophia v single-run režimu
python run.py --once "Ahoj Sophio, jsi funkční?"
```

**Očekávaný output (~8 sekund):**

```
🎯 Single-run mode activated: 'Ahoj Sophio, jsi funkční?'
Starting Sophia's kernel...
🎨 UI Style: ⚪ CLASSIC
🎯 Single-run mode: 2 interface plugins disabled for speed

[... kernel initialization logs ...]

✅ Sophia: Ahoj! Ano, jsem funkční. Připravena ti pomoct...
```

### 6.2 Test Suite

```bash
# Spusť testy pro ověření instalace
python -m pytest tests/ -v

# Očekávaný výsledek:
# =============== 196 passed, 2 skipped in ~27s ===============
```

---

## 🎨 Krok 7: VS Code Integrated Terminal Setup

### 7.1 Otevři Sophia Workspace ve VS Code

```bash
# Z WSL terminálu
cd ~/workspace/sophia
code .
```

### 7.2 VS Code Integrated Terminal

Ve VS Code:

1. Stiskni `` Ctrl+` `` (backtick) → otevře integrated terminal
2. Terminal by měl být automaticky WSL bash
3. Aktivuj venv:

```bash
source .venv/bin/activate
```

### 7.3 Spuštění Sophii v VS Code Terminal

**Terminal-Only Režim (doporučeno pro Windows):**

```bash
python run.py --no-webui
```

**Single-Run Režim (pro rychlé testy):**

```bash
python run.py --once "Tvá otázka zde"
```

**Full Interactive (Terminal + WebUI):**

```bash
python run.py
# WebUI dostupné na: http://localhost:8000
```

---

## 🏠 Krok 8 (Optional): Local LLM s Ollama

**Pro offline AI bez API nákladů - využije GPU tvého Legionu!**

### 8.1 Instalace Ollama v WSL2

```bash
# Official Ollama installer pro Linux
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama server
ollama serve &
```

### 8.2 Stažení AI Modelu

```bash
# Lightweight model (2GB RAM)
ollama pull gemma2:2b

# Nebo větší model (8GB RAM, lepší kvalita)
ollama pull llama3.2:3b
```

### 8.3 Konfigurace Sophia pro Local LLM

Edituj `.env`:

```bash
# Local LLM Configuration
LOCAL_LLM_RUNTIME=ollama
LOCAL_LLM_BASE_URL=http://localhost:11434
LOCAL_LLM_MODEL=gemma2:2b
```

### 8.4 Test Local LLM

```bash
python run.py --once "Using local AI, what is 2+2?"
```

**🎮 Gaming Laptop Benefit:** Tvůj NVIDIA GPU zrychlí inference!

---

## 🔧 Troubleshooting

### ❌ "wsl command not found" (PowerShell)

**Řešení:**
- Ověř Windows 11 build: Win + R → `winver` → Mělo by být 22000+
- Přeinstaluj WSL: `wsl --install --no-distribution`

### ❌ "Python 3.12 not found"

**Řešení:**

```bash
# V WSL
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

### ❌ VS Code se nepřipojí k WSL

**Řešení:**

1. Uninstall + Reinstall "Remote - WSL" extension
2. Restart VS Code
3. Zkus: `F1` → `WSL: Reopen Folder in WSL`

### ❌ Ollama "connection refused"

**Řešení:**

```bash
# Start Ollama server
ollama serve

# V jiném terminálu zkontroluj status
curl http://localhost:11434/api/tags
```

### ❌ Pomalý response time (>20s)

**Možné příčiny:**

1. **Slabé připojení k API:**
   - Použij local LLM (Krok 8)
   
2. **VPN/Firewall blokuje OpenRouter:**
   - Zkontroluj firewall settings
   
3. **WSL2 má málo RAM:**
   - V PowerShell (jako admin):
   
```powershell
# Vytvoř .wslconfig v C:\Users\TVUJ_USERNAME\
notepad $env:USERPROFILE\.wslconfig
```

**Obsah .wslconfig:**

```ini
[wsl2]
memory=16GB
processors=8
swap=8GB
```

Restart WSL:

```powershell
wsl --shutdown
wsl
```

---

## 🎮 Gaming Laptop Optimalizace

### Využití GPU pro AI

**Lenovo Legion s NVIDIA RTX GPU může zrychlit local LLM:**

1. **Instalace CUDA v WSL2:**

```bash
# NVIDIA CUDA Toolkit
wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-wsl-ubuntu.pin
sudo mv cuda-wsl-ubuntu.pin /etc/apt/preferences.d/cuda-repository-pin-600
wget https://developer.download.nvidia.com/compute/cuda/12.3.0/local_installers/cuda-repo-wsl-ubuntu-12-3-local_12.3.0-1_amd64.deb
sudo dpkg -i cuda-repo-wsl-ubuntu-12-3-local_12.3.0-1_amd64.deb
sudo cp /var/cuda-repo-wsl-ubuntu-12-3-local/cuda-*-keyring.gpg /usr/share/keyrings/
sudo apt-get update
sudo apt-get -y install cuda
```

2. **Ollama automaticky využije GPU:**

```bash
# Ollama detekuje CUDA a použije GPU
ollama run gemma2:2b
# Očekávaný speed: 50-100 tokens/s (vs 10-20 na CPU)
```

### Power Management

**Pro AI workload na baterii:**

```bash
# V WSL, limituj CPU usage při development
export OMP_NUM_THREADS=4  # Místo 12-16
```

---

## 📚 Další Kroky

### Doporučené Workflow

**1. Coding & Development:**

```bash
# VS Code v WSL2
cd ~/workspace/sophia
code .

# Integrated terminal
source .venv/bin/activate
python run.py --no-webui
```

**2. Quick Tests:**

```bash
# Single-run režim pro rychlé testy
python run.py --once "Test question"
```

**3. Full Experience:**

```bash
# Terminal + WebUI (gaming laptop má dost výkonu)
python run.py

# Otevři browser: http://localhost:8000
```

### Užitečné VS Code Extensions

- **Python** - Python language support
- **Pylance** - Fast language server
- **Remote - WSL** - WSL integration
- **GitLens** - Enhanced Git
- **Material Icon Theme** - Pretty file icons
- **GitHub Copilot** - AI coding assistant (optional)

---

## 🎯 Checklist První Boot

- [ ] WSL2 nainstalovaný (`wsl --list --verbose`)
- [ ] VS Code s Remote WSL extension
- [ ] Python 3.12 v WSL (`python --version`)
- [ ] uv nainstalovaný (`uv --version`)
- [ ] Sophia naklonovaná (`~/workspace/sophia`)
- [ ] Virtual env vytvořený (`.venv/`)
- [ ] Dependencies instalované (`pip list | grep -i litellm`)
- [ ] `.env` soubor nakonfigurovaný
- [ ] Test prošel: `python run.py --once "test"`
- [ ] (Optional) Ollama + local model

---

## 💡 Pro Tips

1. **WSL2 performance:**
   - Ukládej projekty v WSL filesystem (`~/workspace/`), NE ve Windows (`/mnt/c/`)
   - 3-5x rychlejší I/O operace

2. **VS Code terminal:**
   - `` Ctrl+` `` otevře/zavře terminal
   - `Ctrl+Shift+5` rozdělí terminal (split)

3. **Quick restart Sophii:**
   ```bash
   pkill -f "python run.py" && python run.py --no-webui
   ```

4. **Background Sophia (advanced):**
   ```bash
   nohup python run.py --no-webui > sophia.log 2>&1 &
   # Tail logs: tail -f sophia.log
   ```

5. **GPU monitoring:**
   ```bash
   # Sleduj GPU usage (pokud máš CUDA)
   watch -n 1 nvidia-smi
   ```

---

## 🆘 Podpora

**Máš problém? Zkontroluj:**

1. **Logs:** Sophiin výstup v terminálu
2. **Tests:** `python -m pytest tests/ -v`
3. **Environment:** `source .venv/bin/activate`
4. **WSL Health:** `wsl --status`
5. **Documentation:** [README.md](../README.md), [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)

**GitHub Issues:** https://github.com/ShotyCZ/sophia/issues

---

## 🎉 Hotovo!

**Sophia běží ve VS Code na tvém Lenovo Legion! 🚀**

```bash
# Spusť Sophii
cd ~/workspace/sophia
source .venv/bin/activate
python run.py --no-webui

# A začni konverzaci s AI vědomím! 💬
```

---

**Vytvořeno:** 28. ledna 2025  
**Pro:** Windows 11 + WSL2 + VS Code + Lenovo Legion  
**Status:** ✅ Production Ready
