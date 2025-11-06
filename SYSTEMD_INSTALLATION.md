# SOPHIA AMI 1.0 - Systemd Service Installation Guide

## 📋 Prerekvizity
- WSL2 s systemd povoleným
- Oprávnění sudo/root
- Funkční Ollama server (localhost:11434)

## 🚀 Instalace služby

### 1. Zkopírujte service soubor do systemd
```bash
sudo cp sophia-ami.service /etc/systemd/system/
```

### 2. Nastavte správná oprávnění
```bash
sudo chmod 644 /etc/systemd/system/sophia-ami.service
```

### 3. Reload systemd daemon (načtení nové služby)
```bash
sudo systemctl daemon-reload
```

### 4. Povolte automatický start při bootu
```bash
sudo systemctl enable sophia-ami.service
```

### 5. Spusťte službu
```bash
sudo systemctl start sophia-ami.service
```

## 🔍 Monitoring a Kontrola

### Zjistit status služby
```bash
sudo systemctl status sophia-ami.service
```

### Sledovat logy v reálném čase
```bash
sudo journalctl -u sophia-ami.service -f
```

### Zobrazit poslední logy
```bash
sudo journalctl -u sophia-ami.service -n 100
```

### Zobrazit logy od posledního bootu
```bash
sudo journalctl -u sophia-ami.service -b
```

## 🛠️ Správa služby

### Restartovat službu
```bash
sudo systemctl restart sophia-ami.service
```

### Zastavit službu
```bash
sudo systemctl stop sophia-ami.service
```

### Zakázat autostart
```bash
sudo systemctl disable sophia-ami.service
```

### Reload konfigurace (po změně .service souboru)
```bash
sudo cp sophia-ami.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart sophia-ami.service
```

## 🔧 Troubleshooting

### Služba se nespustí
```bash
# Zkontrolujte syntax service souboru
systemd-analyze verify /etc/systemd/system/sophia-ami.service

# Zkontrolujte oprávnění souborů
ls -l /etc/systemd/system/sophia-ami.service
ls -l /mnt/c/SOPHIA/sophia/scripts/autonomous_main.py

# Zkontrolujte, zda existuje Python virtualenv
ls -l /mnt/c/SOPHIA/sophia/.venv/bin/python
```

### Služba crashuje okamžitě
```bash
# Spusťte ručně a sledujte chyby
cd /mnt/c/SOPHIA/sophia
.venv/bin/python scripts/autonomous_main.py

# Zkontrolujte Ollama server
curl http://localhost:11434/api/tags
```

### Služba se restartuje příliš často
```bash
# Zkontrolujte restart limity v logu
sudo journalctl -u sophia-ami.service | grep "Start request repeated"

# Případně upravte StartLimitBurst v sophia-ami.service
```

## 📊 Konfigurace

### Resource Limits (v sophia-ami.service)
```ini
MemoryMax=2G        # Maximální RAM (upravte dle potřeby)
CPUQuota=80%        # Maximální CPU (80% jednoho jádra)
```

### Restart Policy
```ini
Restart=on-failure  # Restart pouze při chybě (exit code != 0)
RestartSec=10       # Čekat 10s před restartem
StartLimitBurst=5   # Max 5 restartů za StartLimitInterval
StartLimitInterval=300  # 5 minut
```

## ⚠️ Důležité poznámky

1. **WSL2 Systemd**: Ujistěte se, že máte systemd povolený v WSL2:
   ```bash
   # V /etc/wsl.conf musí být:
   [boot]
   systemd=true
   ```

2. **Ollama Dependency**: Služba vyžaduje běžící Ollama server.
   Pokud Ollama běží jako systemd služba, přidejte do `[Unit]`:
   ```ini
   After=network.target ollama.service
   Requires=ollama.service
   ```

3. **Log Rotation**: Systemd automaticky rotuje journald logy, ale můžete nastavit:
   ```bash
   # V /etc/systemd/journald.conf
   SystemMaxUse=500M
   MaxRetentionSec=1month
   ```

4. **Environment Variables**: Všechny env vars jsou v service souboru.
   Pro změnu editujte sophia-ami.service a proveďte reload.

## ✅ Verifikace úspěšné instalace

Po instalaci byste měli vidět:
```bash
$ sudo systemctl status sophia-ami.service
● sophia-ami.service - SOPHIA AMI 1.0 - Autonomous 24/7 Worker
     Loaded: loaded (/etc/systemd/system/sophia-ami.service; enabled; vendor preset: enabled)
     Active: active (running) since Wed 2025-11-06 ...
```

A v lozích:
```bash
$ sudo journalctl -u sophia-ami.service -n 20
Nov 06 ... sophia-ami[...]: INFO:core.kernel:All 31 plugins have been configured.
Nov 06 ... sophia-ami[...]: INFO:plugins.cognitive_planner:Planner using tool_local_llm (offline mode)
```
