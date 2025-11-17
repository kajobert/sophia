# Sophia V2 - Uživatelská příručka

Tato příručka vás provede nastavením a spuštěním aplikace Sophia V2 na vašem lokálním počítači.

## 1. Předpoklady

Než začnete, ujistěte se, že máte v systému nainstalovány následující nástroje:
- **Python 3.12 nebo vyšší:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Git:** [https://git-scm.com/downloads](https://git-scm.com/downloads)
- **`uv`:** Rychlý instalátor Python balíčků. Můžete jej nainstalovat pomocí `pip install uv`.

## 2. Pokyny k nastavení

### 2.1. Klonování repozitáře
Nejprve naklonujte projektový repozitář z GitHubu na váš lokální počítač.

```bash
git clone https://github.com/kajobert/sophia.git
cd sophia
```

### 2.2. Vytvoření virtuálního prostředí
Důrazně doporučujeme použít virtuální prostředí pro správu závislostí projektu.

```bash
uv venv
```
Tím se vytvoří adresář `.venv` ve složce vašeho projektu.

### 2.3. Aktivace virtuálního prostředí
Aktivujte virtuální prostředí. Na macOS a Linuxu:

```bash
source .venv/bin/activate
```

Na Windows:

```bash
.venv\Scripts\activate
```

### 2.4. Instalace závislostí
Nainstalujte všechny požadované Python balíčky pomocí `uv`.

```bash
uv pip sync requirements.in
```

### 2.5. Konfigurace aplikace
Aplikace vyžaduje API klíč pro službu LLM.

1.  **Vytvořte konfigurační soubor:**
    Zkopírujte příklad konfiguračního souboru a vytvořte si vlastní lokální nastavení.

    ```bash
    cp config/settings.example.yaml config/settings.yaml
    ```

2.  **Přidejte svůj API klíč:**
    Potřebujete API klíč od poskytovatele podporovaného `litellm`. Doporučujeme [OpenRouter](https://openrouter.ai/).
    - Vytvořte proměnnou prostředí s názvem `OPENROUTER_API_KEY` a nastavte její hodnotu na váš API klíč. Můžete to udělat přidáním následujícího řádku do vašeho souboru `.bashrc`, `.zshrc` nebo nastavením v systémových proměnných prostředí:
      ```bash
      export OPENROUTER_API_KEY="your-api-key-here"
      ```
    - Alternativně můžete upravit soubor `config/settings.yaml` a přidat svůj klíč přímo, ale použití proměnných prostředí je bezpečnější.

    Aplikace je předkonfigurována pro použití modelu `openrouter/mistralai/mistral-7b-instruct`, což je bezplatný model dostupný na OpenRouter.

3.  **Volitelné: Konfigurace Jules API (pro AI-asistované programování):**
    Pokud chcete používat integraci s Jules API pro AI pomoc při programování, budete potřebovat Jules API klíč:
    - Vytvořte soubor `.env` v kořenu projektu (tento soubor je v `.gitignore` a nebude commitován):
      ```bash
      echo "JULES_API_KEY=your-jules-api-key-here" >> .env
      ```
    - Plugin automaticky načte tento klíč z prostředí.
    - Detailní návod naleznete v `docs/JULES_API_SETUP.md`.

4.  **Volitelné: Konfigurace Tavily API (pro AI-optimalizované webové vyhledávání):**
    Pokud chcete používat AI-poháněné vyhledávání Tavily, budete potřebovat Tavily API klíč:
    - Získejte bezplatný API klíč na [https://tavily.com](https://tavily.com)
    - Přidejte jej do souboru `.env`:
      ```bash
      echo "TAVILY_API_KEY=tvly-your-api-key-here" >> .env
      ```
    - Plugin automaticky načte tento klíč z prostředí.
    - Detailní návod naleznete v `docs/TAVILY_API_SETUP.md`.

## 3. Spuštění aplikace

Sophia V2 může být spuštěna ve dvou režimech: s terminálovým rozhraním nebo s webovým uživatelským rozhraním.

### 3.1. Terminálové rozhraní
Pro interakci se Sophií prostřednictvím terminálu spusťte následující příkaz z kořenového adresáře projektu:

```bash
python run.py
```

Zobrazí se vám výzva `>>> You:`. Napište svou zprávu a stiskněte Enter, abyste dostali odpověď od Sophie.

### 3.2. Webové rozhraní
Aplikace také poskytuje webové chatovací rozhraní.

1.  **Spusťte aplikaci:**
    Spusťte stejný příkaz jako pro terminálové rozhraní:
    ```bash
    python run.py
    ```
    Při spuštění aplikace se také spustí webový server. V terminálu uvidíte logovací zprávu podobnou této: `INFO: Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)`.

2.  **Přístup k webovému UI:**
    Otevřete svůj webový prohlížeč a přejděte na následující adresu:
    [http://127.0.0.1:8000](http://127.0.0.1:8000)

Nyní můžete chatovat se Sophií prostřednictvím webového rozhraní.

### 3.3. Telemetrický dashboard v terminálu

Pro rychlý přehled o spotřebě tokenů, rozpočtu a stavech úloh můžete spustit Rich dashboard `sophia_cli_dashboard.py`, který čte stejná telemetrická data jako webové UI.

```bash
python sophia_cli_dashboard.py --server http://localhost:8000 --refresh 2.0
# Odlehčený režim pro levné VPS
python sophia_cli_dashboard.py --server https://vase-vm.cz --no-system
```

Skript `install_sophia_cli.sh` vytvoří alias `sophia`, takže po aktivaci virtuálního prostředí stačí zadat `sophia` a otevře se dashboard.

## 4. Zastavení aplikace
Aplikaci zastavíte stisknutím `Ctrl+C` v terminálu, ve kterém je spuštěna.

## 5. Nízkonákladové nasazení (≈ $10/měsíc)

Sophii lze provozovat na malém VPS (2 vCPU / 2 GB RAM / 40 GB SSD) od poskytovatelů jako Hetzner CX22 nebo DigitalOcean Basic Droplet (~$10). Doporučený postup:

1. **Vytvořte server** s Ubuntu 22.04, přidejte SSH klíče a otevřete pouze potřebné porty (`22`, `80`, `443`, `8000`).
2. **Nainstalujte závislosti:**
  ```bash
  sudo apt update && sudo apt install -y python3.12 python3.12-venv git build-essential curl
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
3. **Klonujte repozitář a připravte prostředí:**
  ```bash
  git clone https://github.com/ShotyCZ/sophia.git
  cd sophia
  uv venv && source .venv/bin/activate
  uv pip sync requirements.in
  cp .env.example .env  # doplňte API klíče
  ```
4. **Spusťte aplikaci:** `python run.py` (kombinované UI) nebo `python run.py --no-webui` pro čistě terminálový režim. Telemetrický dashboard držte běžet v `tmux`/`screen`: `python sophia_cli_dashboard.py --server http://localhost:8000 --no-system`.
5. **Hlídání rozpočtu:** využijte panel „Budget“ v dashboardu, nastavte limity v `.env` a držte se měsíčního stropu $10.

Tato konfigurace se vejde do 2 GB RAM (s vypnutým psutil panelem) a poskytuje dostatek výkonu pro menší týmy nebo osobní experimenty.
