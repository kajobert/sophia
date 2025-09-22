# Průvodce pro `interactive_session.py`

Tento dokument slouží jako kompletní průvodce pro práci s interaktivním skriptem `interactive_session.py`. Jeho cílem je usnadnit vývoj, testování a ladění jádra Sophie.

---

## 1. Účel Nástroje

Skript `interactive_session.py` byl vytvořen jako **nástroj pro rychlý vývoj a ladění**. Umožňuje komunikovat s jádrem Sophie – konkrétně s jejím plánovacím a prováděcím mechanismem – přímo z terminálu.

Hlavní výhody:
- **Rychlost:** Nemusíte spouštět celou webovou aplikaci a databáze přes Docker.
- **Přehlednost:** Veškerý výstup, včetně generovaného plánu a výsledků jednotlivých kroků, vidíte okamžitě v konzoli.
- **Iterace:** Umožňuje rychle zkoušet různé zadání (prompty) a okamžitě vidět, jak na ně Sophia reaguje.

---

## 2. Příprava a Spuštění

Pro úspěšné spuštění interaktivní session je potřeba splnit několik předpokladů.

### Krok 1: Příprava Prostředí
Ujistěte se, že máte aktivní virtuální prostředí a nainstalované všechny závislosti.

```bash
# Vytvoření a aktivace virtuálního prostředí (pokud ještě nemáte)
python3 -m venv .venv
source .venv/bin/activate

# Instalace všech potřebných závislostí
.venv/bin/pip install -r requirements.txt
```

### Krok 2: Konfigurace
Skript vyžaduje pro inicializaci LLM adaptéru soubor `.env`.

1.  Zkopírujte soubor `.env.example` do nového souboru s názvem `.env`:
    ```bash
    cp .env.example .env
    ```
2.  **Důležité:** Otevřete soubor `.env` a ujistěte se, že proměnná `GEMINI_API_KEY` má alespoň nějakou dočasnou (ne-prázdnou) hodnotu, například:
    ```
    GEMINI_API_KEY="DUMMY_KEY"
    ```
    I když plánovač a LLM mohou běžet v offline režimu (s mockovanými odpověďmi), inicializační logika adaptéru vyžaduje, aby tato proměnná existovala a nebyla prázdná.

### Krok 3: Spuštění Skriptu
Nyní můžete skript spustit. Ujistěte se, že používáte Python interpret z vašeho virtuálního prostředí.

```bash
.venv/bin/python interactive_session.py
```

Po spuštění uvidíte uvítací zprávu a výzvu `>`. Nyní můžete zadávat své požadavky. Pro ukončení napište `exit` nebo `quit`.

---

## 3. Možnosti Využití

Tento nástroj je flexibilní a lze ho použít v mnoha fázích vývoje.

### Příklad 1: Testování základních příkazů
Můžete zadat jednoduchý úkol a sledovat, jak si s ním Sophia poradí.

**Vstup:**
```
> Vypiš všechny soubory v aktuálním adresáři.
```

**Očekávaný výstup:**
Skript vypíše, že byl vygenerován plán (např. 1 krok), a poté zobrazí výsledek provedení tohoto kroku, který bude obsahovat seznam souborů.

### Příklad 2: Ladění komplexních plánů
Zadejte složitější úkol, který vyžaduje více kroků.

**Vstup:**
```
> Přečti obsah souboru README.md, najdi v něm sekci "Dokumentace" a vytvoř nový soubor `doc_summary.txt` s obsahem této sekce.
```

**Co sledovat:**
- **Vygenerovaný plán:** Podívejte se, jestli plánovač správně rozložil úkol na logické kroky (čtení, analýza, zápis).
- **Výstupy jednotlivých kroků:** Pokud nějaký krok selže, skript vypíše chybu. To vám pomůže identifikovat, zda je problém v logice nástroje (např. `WriteFileTool`) nebo v plánu samotném.

### Příklad 3: Testování nového nástroje
Představte si, že jste právě vytvořili nový nástroj `WeatherTool`, který zjišťuje počasí.
1.  Vytvoříte soubor `tools/weather_tool.py` s vaším nástrojem.
2.  Spustíte `interactive_session.py`.
3.  Zadáte požadavek, který by měl váš nový nástroj aktivovat.

**Vstup:**
```
> Jaké je počasí v Praze?
```

**Co sledovat:**
- Zda plánovač správně identifikoval, že má použít `WeatherTool`.
- Zda se nástroj spustil se správnými parametry (`{"city": "Prague"}`).
- Jaký byl výstup nástroje a zda byl správně zaznamenán.

---

## 4. Jak Tím Vylepšovat Sophii

Interaktivní session je klíčovým nástrojem pro **iterativní vylepšování** Sophie.

- **Zlepšování Plánovače:** Opakovaným zadáváním různých úkolů můžete zjistit, kde má `PlannerAgent` slabiny. Pokud generuje neefektivní nebo chybné plány, můžete vylepšit jeho základní prompt (`goal`, `backstory`) v `agents/planner_agent.py`, aby lépe rozuměl kontextu a dostupným nástrojům.

- **Odlaďování Nástrojů:** Když plán selže, často je to chyba v samotném nástroji. Interaktivní session vám poskytne přesnou chybovou hlášku a kontext, což vám umožní rychle opravit chybu v kódu nástroje.

- **Rozšiřování Schopností:** Tento nástroj vám umožňuje snadno experimentovat. Můžete rychle otestovat, jak by Sophia reagovala na úkoly, pro které ještě nemá nástroje, a tím identifikovat, jaké nové schopnosti (nástroje) je potřeba vytvořit.

Stručně řečeno, `interactive_session.py` transformuje abstraktní ladění na konkrétní, praktický a rychlý proces. Je to váš primární "pískoviště" pro experimenty, které dělají Sophii chytřejší a spolehlivější.
