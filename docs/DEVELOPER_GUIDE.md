# Průvodce pro Vývojáře

Tento dokument poskytuje technické informace pro vývojáře, kteří chtějí přispívat do projektu Sophia.

## Nastavení Lokálního Vývojového Prostředí

Tento návod předpokládá, že nechcete používat Docker a chcete si prostředí nastavit manuálně.

### 1. Předpoklady

-   Python 3.12+
-   `pip` a `venv`
-   Git

### 2. Klonování Repozitáře

```bash
git clone <URL_REPOZITARE>
cd <NAZEV_SLOZKY_REPOZITARE>
```

### 3. Vytvoření Virtuálního Prostředí

Důrazně doporučujeme používat virtuální prostředí, aby se zabránilo konfliktům závislostí.

```bash
python3 -m venv .venv
source .venv/bin/activate
```
_Poznámka pro Windows: `.venv\Scripts\activate`_

### 4. Instalace Závislostí

Projekt používá `pip-tools` pro správu závislostí. Závislosti jsou definovány v `requirements.in` a plně pinovaný soubor je `requirements.txt`.

Pro instalaci použijte `uv` (doporučeno pro rychlost) nebo `pip`:
```bash
# Doporučená metoda
uv pip install -r requirements.txt

# Alternativní metoda
pip install -r requirements.txt
```

### 5. Konfigurace Prostředí

1.  Zkopírujte `.env.example` na `.env`.
2.  Otevřete `.env` a vložte svůj `GEMINI_API_KEY`.

### 6. Spuštění Testů

Před provedením jakýchkoliv změn se ujistěte, že celá testovací sada prochází. Testy jsou navrženy tak, aby běžely offline a nevyžadovaly API klíče.

Spusťte testy z kořenového adresáře projektu:
```bash
PYTHONPATH=. pytest
```

Měli byste vidět, že všechny testy prošly úspěšně.

## Struktura Projektu

-   **/agents**: Definuje jednotlivé AI agenty (Planner, Engineer, atd.).
-   **/core**: Jádro aplikace, obsahuje orchestrátor, konfiguraci a etický modul.
-   **/docs**: Veškerá projektová dokumentace (DNA, Architektura, Návody).
-   **/memory**: Správa paměti, integrace s `memorisdk`.
-   **/services**: Podpůrné služby pro webové API (autentizace, role, atd.).
-   **/tools**: Nástroje (`Tools`), které mohou agenti používat (práce se soubory, spouštění kódu).
-   **/web**: Obsahuje backend (`/api`) a frontend (`/ui`) webové aplikace.
-   **/tests**: Všechny jednotkové a integrační testy.
-   **config.yaml**: Hlavní konfigurační soubor pro chování aplikace.
-   **main.py**: Hlavní vstupní bod pro spuštění "cyklu vědomí" Sophie.

## Workflow pro Přispívání

1.  **Vytvořte novou větev:** `git checkout -b feature/nazev-vasi-funkce`
2.  **Proveďte změny:** Upravte kód podle potřeby.
3.  **Spusťte testy:** `PYTHONPATH=. pytest`
4.  **Spusťte pre-commit hooky:** Pokud je máte nainstalované, `pre-commit` se spustí automaticky. Pokud ne, spusťte je manuálně, abyste zajistili formátování a linting:
    ```bash
    pre-commit run --all-files
    ```
5.  **Commitněte změny:** `git commit -m "Stručný popis změn"`
6.  **Vytvořte Pull Request:** Nahrajte svou větev na GitHub a vytvořte Pull Request pro revizi.
