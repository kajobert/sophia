# Průvodce Vývojovým Prostředím

Tento dokument slouží jako kompletní průvodce pro nastavení a práci s vývojovým prostředím projektu Sophia. Cílem je zajistit konzistentní, spolehlivé a snadno použitelné prostředí pro všechny vývojáře bez ohledu na jejich operační systém.

---

## 1. Doporučený Přístup: Docker

**Proč Docker?**
- **Konzistence:** Všichni vývojáři pracují ve stejném Linuxovém prostředí s identickými závislostmi. Tím se eliminují problémy typu "na mém stroji to funguje".
- **Jednoduchost:** Místo manuální instalace Pythonu, vytváření virtuálních prostředí a instalace balíčků stačí spustit jeden příkaz.
- **Izolace:** Projekt a jeho závislosti jsou plně izolovány od vašeho lokálního systému.

### Krok 1: Předpoklady
Ujistěte se, že máte nainstalovaný a spuštěný **Docker** a **Docker Compose**.
- [Instalace Docker Desktop](https://www.docker.com/products/docker-desktop/) (obsahuje Docker Compose)

### Krok 2: Příprava Konfigurace
Aplikace vyžaduje pro přístup k LLM API klíčům soubor `.env`.

1.  Zkopírujte soubor `.env.example` do nového souboru s názvem `.env`:
    ```bash
    # V terminálu v kořenovém adresáři projektu
    cp .env.example .env
    ```
2.  **Důležité:** Otevřete nově vytvořený soubor `.env` a vložte své skutečné API klíče.
    ```
    GEMINI_API_KEY="skutecny-api-klic-pro-gemini"
    DEEPSEEK_API_KEY="skutecny-api-klic-pro-deepseek"
    ```

### Krok 3: Spuštění Vývojového Prostředí
Nyní můžete aplikaci spustit.

1.  **Sestavení a spuštění kontejneru:**
    ```bash
    # Tento příkaz sestaví Docker image (pokud ještě neexistuje) a spustí kontejner na pozadí (-d).
    docker-compose up --build -d
    ```

2.  **Sledování logů:**
    Pro zobrazení výstupu aplikace (logů) v reálném čase použijte:
    ```bash
    docker-compose logs -f
    ```

Aplikace nyní běží. Díky nastavení "live-reloading" se jakákoliv změna ve zdrojovém kódu automaticky projeví a server se sám restartuje.

### Krok 4: Spouštění Testů
Testy by měly být spouštěny **uvnitř Docker kontejneru**, aby se zajistilo, že běží ve správném prostředí.

1.  Otevřete interaktivní shell v běžícím kontejneru:
    ```bash
    docker-compose exec app /bin/bash
    ```

2.  Uvnitř kontejneru můžete spouštět testy:
    ```bash
    # Spuštění všech testů
    pytest

    # Spuštění konkrétního testovacího souboru
    pytest tests/test_llm_manager.py
    ```

### Krok 5: Zastavení Prostředí
Až budete s prací hotovi, zastavte kontejner:
```bash
docker-compose down
```
Tento příkaz zastaví a odstraní kontejner, ale vaše zdrojové kódy a `.env` soubor zůstanou nedotčeny.

---

## 2. Alternativní Přístup (Legacy): Manuální Nastavení

Tento přístup se **nedoporučuje** kvůli možným problémům s kompatibilitou mezi různými operačními systémy. Použijte jej pouze v případě, že nemůžete nebo nechcete použít Docker.

### Krok 1: Příprava Prostředí
Ujistěte se, že máte aktivní virtuální prostředí a nainstalované všechny závislosti.

```bash
# Vytvoření a aktivace virtuálního prostředí (příkazy se mohou lišit pro Windows)
python3 -m venv .venv
source .venv/bin/activate

# Instalace všech potřebných závislostí
uv pip install -r requirements.in
```

### Krok 2: Spuštění Aplikace
Spusťte TUI aplikaci:
```bash
python tui/app.py
```