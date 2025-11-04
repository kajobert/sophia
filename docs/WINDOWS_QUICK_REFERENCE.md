# 🎯 Sophia - Windows Quick Reference

**Rychlá referenční karta pro Windows 11 + WSL2 uživatele**

---

## 🚀 Základní Příkazy

### Spuštění WSL

```powershell
# Z Windows (PowerShell/CMD)
wsl                          # Spustit default WSL distro
wsl -d Ubuntu               # Spustit specifickou distro
wsl --shutdown              # Vypnout všechny WSL instance
wsl --list --verbose        # Zobrazit instalované distros
```

### VS Code

```bash
# V WSL terminálu
code .                      # Otevřít current folder ve VS Code
code ~/workspace/sophia     # Otevřít Sophia workspace

# Klávesové zkratky
Ctrl+`                      # Toggle integrated terminal
Ctrl+Shift+P                # Command Palette
F1                          # Command Palette (alternate)
```

### Sophia Operace

```bash
# Aktivace environment
cd ~/workspace/sophia
source .venv/bin/activate

# Spuštění režimy
python run.py --no-webui                    # Terminal-only (doporučeno)
python run.py --once "Tvá otázka"          # Single-run (rychlý test)
python run.py                               # Full mode (Terminal + WebUI)
python run.py --ui cyberpunk                # Sci-fi UI style

# Testy
python -m pytest tests/ -v                  # Všechny testy
python -m pytest tests/test_kernel.py -v   # Specifický test

# Utility
python run.py --once "test"                 # Quick health check (~8s)
```

---

## 🏠 Local LLM (Ollama)

### Ollama Příkazy

```bash
# Server
ollama serve                            # Start Ollama server
ollama serve &                          # Start na pozadí

# Modely
ollama list                             # Zobrazit stažené modely
ollama pull gemma2:2b                   # Stáhnout model (1.5GB)
ollama pull llama3.2:3b                 # Větší model (2GB)
ollama run gemma2:2b                    # Interaktivní chat

# Správa
ollama rm gemma2:2b                     # Smazat model
ollama ps                               # Zobrazit běžící modely
```

### Sophia s Local LLM

```bash
# .env konfigurace
LOCAL_LLM_RUNTIME=ollama
LOCAL_LLM_MODEL=gemma2:2b

# Test
python run.py --once "Using local AI, solve: 2+2"
```

---

## 📁 Filesystem Navigation

### Windows ↔ WSL Paths

```bash
# Z WSL přístup k Windows
cd /mnt/c/Users/YourName/Desktop        # Windows Desktop
cd /mnt/d/                              # D: drive

# Z Windows přístup k WSL
\\wsl$\Ubuntu\home\radek\workspace      # File Explorer path
```

### Doporučené Lokace

```bash
# ✅ DOBŘE: Projekty v WSL (rychlé)
~/workspace/sophia
~/projects/

# ❌ ŠPATNĚ: Projekty ve Windows (pomalé)
/mnt/c/Users/Radek/sophia
```

---

## 🔧 System Management

### WSL Management

```powershell
# PowerShell jako Admin
wsl --update                            # Update WSL kernel
wsl --status                            # Zobrazit WSL status
wsl --set-default-version 2             # Nastavit WSL2 jako default
wsl --set-version Ubuntu 2              # Upgradovat distro na WSL2
```

### WSL2 Restart

```powershell
# Soft restart
wsl --shutdown
wsl

# Hard restart (pokud problém)
Get-Service LxssManager | Restart-Service
```

### Resource Monitoring

```bash
# V WSL
htop                                    # CPU/RAM monitor (install: sudo apt install htop)
nvidia-smi                              # GPU monitor (pokud máš NVIDIA)
watch -n 1 nvidia-smi                   # Live GPU monitoring

# Ve Windows
Task Manager → Performance → WSL        # WSL resource usage
```

---

## 🐛 Troubleshooting Quick Fixes

### "Command not found"

```bash
# Reload bash profile
source ~/.bashrc

# Check PATH
echo $PATH

# Reinstall uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### "Permission denied"

```bash
# Fix venv activation
chmod +x .venv/bin/activate

# Fix script
chmod +x script.sh
```

### Slow Performance

```bash
# 1. Check if project in WSL (not /mnt/c/)
pwd                                     # Should be /home/... (not /mnt/...)

# 2. Check WSL2 memory (.wslconfig)
# Windows: Edit C:\Users\YourName\.wslconfig
# Set memory=16GB

# 3. Restart WSL
# PowerShell: wsl --shutdown
```

### VS Code Connection Issues

```bash
# 1. Uninstall + Reinstall "Remote - WSL" extension
# 2. Restart VS Code
# 3. Try manual connection
code ~/workspace/sophia
```

---

## 💡 Pro Tips

### Background Processes

```bash
# Spustit Sophia na pozadí
nohup python run.py --no-webui > sophia.log 2>&1 &

# Zobrazit logs
tail -f sophia.log

# Zastavit background process
pkill -f "python run.py"
```

### Quick Aliases

```bash
# Přidat do ~/.bashrc
alias sophia='cd ~/workspace/sophia && source .venv/bin/activate'
alias srun='python run.py --no-webui'
alias stest='python run.py --once'

# Reload
source ~/.bashrc

# Použití
sophia          # Jump to Sophia + activate venv
srun            # Spustit Sophia terminal mode
stest "ahoj"    # Quick test
```

### Git Quick Commands

```bash
# Status
git status -s                           # Short status

# Pull latest
git pull origin feature/year-2030-ami-complete

# Commit
git add .
git commit -m "your message"
git push

# Branch info
git branch -a                           # Všechny branches
```

---

## 📊 Performance Benchmarks

### Expected Response Times

```bash
python run.py --once "test"
# ✅ Normal: 8-10 seconds (4s startup + 4-6s LLM)
# ⚠️  Slow: 15-20 seconds (check network/API)
# ❌ Error: >30 seconds (timeout, check logs)
```

### Local LLM Speed (with GPU)

```bash
# NVIDIA RTX 3060+ expected:
# gemma2:2b:    50-80 tokens/s
# llama3.2:3b:  30-50 tokens/s
# llama3.1:8b:  15-25 tokens/s
```

---

## 🔗 Useful Links

- **WSL2 Setup:** [WINDOWS_WSL2_SETUP.md](WINDOWS_WSL2_SETUP.md)
- **Quick Start:** [WINDOWS_QUICKSTART.md](WINDOWS_QUICKSTART.md)
- **Local LLM:** [LOCAL_LLM_SETUP.md](LOCAL_LLM_SETUP.md)
- **Main README:** [../README.md](../README.md)

---

## ⌨️ Keyboard Shortcuts Cheat Sheet

### VS Code (Windows)

```
Ctrl+`              Toggle integrated terminal
Ctrl+Shift+P        Command Palette
Ctrl+P              Quick file open
Ctrl+B              Toggle sidebar
Ctrl+Shift+E        Explorer view
Ctrl+Shift+G        Git view
Ctrl+Shift+F        Search across files
F5                  Debug
```

### Terminal (bash)

```
Ctrl+C              Kill running process
Ctrl+Z              Suspend process
Ctrl+D              Exit terminal
Ctrl+L              Clear screen
Ctrl+R              Reverse search history
Ctrl+A              Jump to line start
Ctrl+E              Jump to line end
↑/↓                 Command history
Tab                 Auto-complete
```

---

**Print this page for quick reference!** 🖨️
