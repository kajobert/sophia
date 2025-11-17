# SOPHIA: Cloud-Only Deployment Guide (OpenRouter, No Local LLM)

## 🟢 Úvod
Tento návod vás krok za krokem provede nasazením SOPHIA na cloudový server bez nutnosti lokálního jazykového modelu. SOPHIA bude komunikovat pouze přes OpenRouter API. Návod je určen i pro úplné začátečníky.

---

## 1. Příprava cloudového serveru

1. **Založte si účet u cloudové služby** (např. Hetzner, DigitalOcean, Vultr, AWS Lightsail, apod.).
2. **Vytvořte nový virtuální server (VM)** s Linuxem (doporučeno Ubuntu 22.04+).
   - Doporučená konfigurace: 2 CPU, 2–4 GB RAM, 20 GB disk.
   - Cena: do 10 $/měsíc.
3. **Přihlaste se na server přes SSH**:
   - Na Windows spusťte aplikaci "Terminal" nebo "WSL" (Windows Subsystem for Linux).
   - Zadejte příkaz (nahraďte `user` a `server_ip`):
     ```bash
     ssh user@server_ip
     ```

---

## 2. Instalace základních nástrojů

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3 python3-pip python3-venv
```

---

## 3. Stažení SOPHIA

```bash
git clone https://github.com/ShotyCZ/sophia.git
cd sophia
```

---


## 4. Vytvoření a aktivace Python prostředí

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 4a. Instalace uživatelských aliasů pro pohodlné ovládání

```bash
bash install_sophia_cli.sh
```
Po příští aktivaci prostředí můžete používat příkazy:
- `sophia`      (spustí moderní CLI dashboard)
- `sophia-run`  (spustí hlavní systém)

---

## 5. Instalace závislostí

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Získání OpenRouter API klíče

1. Navštivte [https://openrouter.ai/](https://openrouter.ai/) a vytvořte si účet.
2. Vygenerujte si API klíč (najdete v sekci "API Keys").
3. Zkopírujte si klíč (začíná např. `sk-or-...`).

---

## 7. Nastavení API klíče

**Doporučený způsob:**

```bash
echo 'export OPENROUTER_API_KEY="váš-klíč-zde"' >> ~/.bashrc
source ~/.bashrc
```

**Alternativně:**
- Otevřete soubor `config/settings.yaml` a přidejte řádek:
  ```yaml
  openrouter_api_key: "váš-klíč-zde"
  ```

---

## 8. Kontrola konfigurace

- Ověřte, že v `config/settings.yaml` je nastaveno:
  ```yaml
  provider: "openrouter"
  model_name: "doporučený-model-z-dokumentace"
  # např. "anthropic/claude-3.5-sonnet" nebo "google/gemini-2.0-flash-thinking-exp:free"
  offline_mode: false
  ```
- Ujistěte se, že NENÍ povolen žádný lokální model (`ollama`, `lmstudio` apod.).

---

## 9. První spuštění SOPHIA

```bash
python run.py
```

- Pokud vše proběhne správně, SOPHIA se spustí a bude používat pouze OpenRouter API.

---

## 10. Ověření provozu

- Zkuste zadat dotaz nebo úkol v rozhraní SOPHIA.
- V logu/konzoli by se měly objevovat pouze volání na OpenRouter (žádné `localhost:11434` apod.).

---

## 11. Delegace zakázky na Joules

- Ujistěte se, že plugin pro Joules je aktivní (viz dokumentace projektu).
- SOPHIA by měla být schopna vytvořit a delegovat zakázku automaticky.

---

## 12. Automatický start po restartu (volitelné)

Pro zajištění 24/7 provozu nastavte automatické spouštění pomocí systemd:

```bash
sudo cp sophia-ami.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sophia-ami
sudo systemctl start sophia-ami
```

---

## 13. Hotovo!
SOPHIA nyní běží v cloudu, bez lokálního LLM, pouze přes OpenRouter API.

---

## ❓ Nejčastější chyby a rady
- Pokud SOPHIA hlásí chybu o chybějícím API klíči, zkontrolujte proměnnou prostředí nebo `settings.yaml`.
- Pokud se pokouší připojit na `localhost:11434`, není správně nastaven provider na `openrouter`.
- Pro další rady viz README.md nebo dokumentaci v adresáři `docs/`.

---

## 📚 Další zdroje
- [OpenRouter dokumentace](https://openrouter.ai/docs)
- [SOPHIA GitHub](https://github.com/ShotyCZ/sophia)
- [README.md v projektu]

---

*Vytvořeno pro úplné začátečníky. Pokud si nevíte rady, kontaktujte autora projektu nebo využijte komunitní podporu.*
