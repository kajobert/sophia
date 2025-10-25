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

## 4. Zastavení aplikace
Aplikaci zastavíte stisknutím `Ctrl+C` v terminálu, ve kterém je spuštěna.
