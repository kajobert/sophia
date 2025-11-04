# 🤖 GitHub Copilot - Sophia Auto-Install Prompt

**Copy-paste tento prompt do GitHub Copilot Chat ve VS Code pro automatickou instalaci Sophii**

---

## 📋 Prompt pro Copilot

```
Prosím, pomoz mi nainstalovat a nakonfigurovat Sophia AI na Windows 11 s WSL2.

ENVIRONMENT:
- OS: Windows 11 + WSL2 (Ubuntu)
- IDE: VS Code s Remote WSL extension
- Hardware: Gaming laptop (Lenovo Legion/ASUS ROG/MSI) s NVIDIA GPU

ÚKOLY:

1. OVĚŘENÍ WSL2:
   - Zkontroluj, zda WSL2 běží: `wsl --list --verbose`
   - Pokud ne, poskytni PowerShell příkazy pro instalaci
   - Ověř, že jsem v WSL terminálu (ne Windows)

2. INSTALACE PREREQUISITES:
   - Python 3.12 (via deadsnakes PPA)
   - Git
   - uv package manager (curl install)
   - Všechny potřebné apt packages

3. CLONE SOPHIA:
   - Vytvoř ~/workspace/sophia directory
   - Clone z: https://github.com/ShotyCZ/sophia.git
   - Checkout branch: feature/year-2030-ami-complete

4. PYTHON ENVIRONMENT:
   - Vytvoř virtual environment s Python 3.12
   - Aktivuj venv
   - Nainstaluj dependencies z requirements.in pomocí uv

5. KONFIGURACE:
   - Vytvoř .env z .env.example
   - Zobraz mi, jaké API klíče potřebuji nakonfigurovat
   - Poskytni příklad konfigurace pro local LLM (Ollama)

6. PRVNÍ TEST:
   - Spusť: python run.py --once "test"
   - Ověř, že response je ~8 sekund
   - Spusť pytest pro ověření instalace

7. OLLAMA LOCAL LLM (OPTIONAL):
   - Instalace Ollama v WSL2
   - Stažení gemma2:2b modelu
   - Konfigurace .env pro local LLM
   - Test s GPU acceleration

8. VS CODE SETUP:
   - Doporuč extensions (Python, Pylance, Remote WSL)
   - Nastav integrated terminal na WSL bash
   - Vytvoř .vscode/settings.json pro Python 3.12

POŽADAVKY:
- Poskytuj příkazy krok po kroku, které můžu copy-paste
- Zobrazuj očekávané výstupy
- Varuj před kroky vyžadujícími restart nebo admin práva
- Pokud něco selže, nabídni troubleshooting
- Na konci mi dej "Quick Reference" s užitečnými příkazy

DOKUMENTACE K DISPOZICI:
- docs/WINDOWS_WSL2_SETUP.md - Kompletní guide
- docs/WINDOWS_QUICKSTART.md - Rychlý start
- docs/WINDOWS_QUICK_REFERENCE.md - Referenční karta
- docs/LOCAL_LLM_SETUP.md - Ollama setup
- README.md - Hlavní dokumentace

ZAČNI tím, že ověříš můj aktuální stav (WSL2? Python? Git?) a pak postupuj podle potřeby.
```

---

## 🎯 Jak Použít

### Krok 1: Otevři GitHub Copilot Chat

Ve VS Code:
- Stiskni `Ctrl+Shift+I` (nebo `Cmd+Shift+I` na Mac)
- Nebo klikni na ikonu Copilot v levém panelu
- Nebo použij Command Palette: `F1` → "GitHub Copilot: Open Chat"

### Krok 2: Copy-Paste Prompt

1. Zkopíruj **celý prompt** výše (včetně všech úkolů)
2. Vlož do Copilot Chat
3. Stiskni Enter

### Krok 3: Následuj Instrukce

Copilot ti poskytne:
- ✅ Konkrétní příkazy pro tvůj systém
- ✅ Krok-po-kroku instalaci
- ✅ Troubleshooting pokud něco selže
- ✅ Ověření každého kroku

---

## 💡 Pro Tips

### Upřesnění Promptu

Pokud máš specifické požadavky, přidej na začátek:

```
DODATEČNÝ KONTEXT:
- Mám už nainstalovaný: [Python/Git/WSL2/...]
- Chci použít: [VS Code/Terminal/...]
- Preferuji: [local LLM/cloud API/...]
- GPU: [NVIDIA RTX 3060/...]
```

### Interaktivní Režim

Copilot se může ptát na detaily - odpovídej krátce:

```
Copilot: "Máš už WSL2 nainstalovaný?"
Ty: "Ano, Ubuntu 22.04"

Copilot: "Chceš použít local LLM nebo cloud API?"
Ty: "Local LLM s Ollama"
```

### Troubleshooting

Pokud něco selže:

```
Copilot, tento příkaz selhal s chybou:
[vlož error message]

Co mám udělat?
```

---

## 🔄 Alternativní Prompty

### Rychlá Instalace (Zkušení Uživatelé)

```
Copilot, nainstaluj Sophii na WSL2:
- Clone z GitHub: ShotyCZ/sophia
- Branch: feature/year-2030-ami-complete
- Python 3.12 + uv
- requirements.in dependencies
- .env konfigurace
- Quick test

Dej mi jen příkazy, minimální vysvětlování.
```

### Only Local LLM Setup

```
Copilot, pomoz mi nastavit Ollama local LLM pro Sophii:
- WSL2 Ubuntu
- NVIDIA GPU (RTX 3060+)
- Model: gemma2:2b
- Konfigurace .env
- Test GPU acceleration

Chci využít GPU pro rychlou inference.
```

### Only Troubleshooting

```
Copilot, Sophia je nainstalovaná, ale:
[popis problému, např:]
- Response trvá >20 sekund
- Python nevidí .env
- pytest selhává

Projdi diagnostiku a navrhni řešení.
```

---

## 📚 Follow-up Prompty

Po úspěšné instalaci:

### Workflow Setup

```
Copilot, nastav mi efektivní workflow pro Sophii:
- VS Code shortcuts
- Terminal aliases
- Background run setup
- Log monitoring
- Git workflow

Chci maximální produktivitu.
```

### Plugin Development

```
Copilot, chci vytvořit nový Sophia plugin:
- Typ: [tool/cognitive/memory]
- Funkce: [popis]

Vytvoř mi boilerplate kód podle existujících pluginů.
```

### Performance Tuning

```
Copilot, optimalizuj Sophii pro můj gaming laptop:
- NVIDIA RTX [model]
- RAM: [16/32]GB
- WSL2 .wslconfig
- Local LLM performance

Chci maximální rychlost inference.
```

---

## 🎓 Copilot Best Practices

### 1. Buď Specifický

❌ **Špatně:**
```
Nainstaluj Sophii
```

✅ **Dobře:**
```
Nainstaluj Sophii na Windows 11 WSL2 Ubuntu s Python 3.12, 
uv package manager, a local LLM pomocí Ollama s GPU support
```

### 2. Poskytni Kontext

```
CURRENT STATE:
- WSL2: ✅ Installed (Ubuntu 22.04)
- Python: ✅ 3.10 (need upgrade to 3.12)
- Git: ✅ Installed
- Sophia: ❌ Not cloned yet

POKRAČUJ odtud, neprovádej kroky co už mám.
```

### 3. Ověřuj Každý Krok

```
Copilot, právě jsem provedl:
[vlož příkaz a output]

Je to správně? Pokračuji dalším krokem?
```

### 4. Žádej Vysvětlení

```
Copilot, tento příkaz mi není jasný:
uv pip sync requirements.in

Co přesně dělá? Proč použít uv místo pip?
```

---

## 🚀 Kompletní Workflow Příklad

**Session transcript:**

```
Uživatel:
[copy-paste hlavní prompt]

Copilot:
Dobrá, začneme ověřením prostředí. Spusť:
wsl --list --verbose

Uživatel:
  NAME      STATE           VERSION
* Ubuntu    Running         2

Copilot:
Výborně, WSL2 běží. Teď ověř Python:
python3 --version

Uživatel:
Python 3.10.12

Copilot:
Potřebuješ upgrade na 3.12. Postupuj:
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3.12-dev

[... pokračuje instalace ...]

Copilot:
Instalace dokončena! Spusť test:
python run.py --once "test"

Uživatel:
[output zobrazuje úspěch]

Copilot:
Perfektní! Sophia běží. Tady je Quick Reference:
[poskytne užitečné příkazy]
```

---

## 📊 Očekávané Výsledky

Po dokončení budeš mít:

- ✅ WSL2 Ubuntu s Python 3.12
- ✅ Sophia naklonovaná v `~/workspace/sophia`
- ✅ Virtual environment aktivní
- ✅ Dependencies nainstalovány
- ✅ `.env` nakonfigurovaný
- ✅ První test úspěšný (~8s response)
- ✅ pytest passing (196/196 tests)
- ✅ (Optional) Ollama + local LLM s GPU

**Celková doba:** 15-20 minut s Copilot asistencí

---

## 🆘 Pokud Copilot Selhává

### Fallback na Manuální Dokumentaci

```
Copilot mi nepomohl s [konkrétní problém].

Otevři mi relevantní dokumentaci:
- docs/WINDOWS_WSL2_SETUP.md (krok [číslo])
- docs/WINDOWS_QUICK_REFERENCE.md (sekce [název])
```

### Požádej o Troubleshooting Guide

```
Copilot, vytvoř mi troubleshooting checklist pro:
- WSL2 connection issues
- Python environment problems
- Sophia installation errors
- Performance issues
```

---

## 💬 Community Support

Pokud Copilot nedokáže vyřešit problém:

1. **GitHub Issues:** https://github.com/ShotyCZ/sophia/issues
2. **Dokumentace:** Všechny guides v `docs/` složce
3. **WORKLOG.md:** Historie podobných problémů a řešení

---

**Copilot je tvůj AI asistent - využij ho maximálně! 🤖✨**

**Tip:** Ulož si tento dokument do záložek pro budoucí reference!
