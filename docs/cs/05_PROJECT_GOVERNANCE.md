# Dokument 5: Governance, Automatizace a Workflow

Tento dokument definuje procesy, nástroje a automatizaci, které zajišťují kvalitu, efektivitu a přehlednost vývoje projektu Sophia V2.

## 1. GitHub Workflow & Strategie Větvení

Pro zajištění stability a předvídatelnosti dodržujeme strukturovaný Git workflow.

*   **`main`**: Tato větev je zdrojem pravdy pro stabilní, produkčně připravený kód. Přímé nahrávání (push) je zakázáno. Sloučení do `main` je povoleno pouze prostřednictvím Pull Requestu z větve `develop` po důkladné revizi a testování.
*   **`develop`**: Primární vývojová větev. Obsahuje nejnovější integrované funkce a představuje aktuální "edge" verzi aplikace. Všechny feature větve jsou slučovány do `develop`.
*   **`feature/<nazev-pluginu>` nebo `fix/<nazev-problemu>`**: Veškerý nový vývoj, ať už se jedná o nový plugin nebo opravu chyby, musí probíhat v samostatné větvi pro danou funkci nebo opravu. Tyto větve jsou vytvářeny z nejnovější verze větve `develop`.

## 2. Proces Pull Requestu (PR)

Každá změna kódu musí být odeslána prostřednictvím Pull Requestu do větve `develop`.

1.  **Šablona pro PR:** PR musí dodržovat šablonu definovanou v `.github/PULL_REQUEST_TEMPLATE.md`, která vyžaduje jasný popis změn, důvod "proč" a odkaz na relevantní problémy (issues).
2.  **Povinné CI Kontroly:** PR nelze sloučit, dokud všechny automatizované kontroly (CI) úspěšně neprojdou.
3.  **Revize Kódu (Code Review):** Alespoň jeden další vývojář musí PR zkontrolovat a schválit, než může být sloučen.

## 3. Automatizace (CI/CD) s GitHub Actions

Continuous Integration (CI) pipeline, definovaná v `.github/workflows/ci.yml`, se automaticky spouští při každém push a Pull Requestu do větví `develop` a `main`. Jejím účelem je zaručit kvalitu a stabilitu kódu.

CI pipeline se skládá z následujících úloh:

1.  **Linting & Formátování:**
    *   **`black`**: Vynucuje nekompromisní formátování kódu.
    *   **`ruff`**: Extrémně rychlý linter, který kontroluje širokou škálu chyb a stylistických problémů.
    *   **`mypy`**: Provádí statickou typovou kontrolu, aby zajistil 100% soulad s typovými anotacemi.

2.  **Unit & Integrační Testování:**
    *   **`pytest`**: Automaticky objevuje a spouští všechny testy v adresáři `tests/`.
    *   **Analýza Pokrytí (Coverage Analysis)**: Reportuje procento kódu pokrytého testy. Snížení pokrytí může zablokovat sloučení PR.

3.  **Kompatibilita s Více Verzemi:**
    *   Testovací sada se spouští na matici verzí Pythonu (např. 3.10, 3.11, 3.12), aby bylo zajištěno, že kód je kompatibilní se všemi podporovanými prostředími.

4.  **Bezpečnostní Skenování (Budoucí Cíl):**
    *   Integrace nástrojů jako `bandit` nebo `Snyk` pro skenování běžných bezpečnostních zranitelností v kódu a závislostech.

5.  **Ověření Sestavení Docker Obrazu:**
    *   Poslední krok se pokusí sestavit Docker obraz z poskytnutého `Dockerfile`. To zajišťuje, že aplikace a její závislosti mohou být úspěšně kontejnerizovány, což předchází běhovým chybám v produkci.

## 4. Povinná Dokumentace Práce

*   **`WORKLOG.md`**: Jak je definováno v `AGENTS.md`, je přísnou povinností každého agenta po dokončení úkolu zaznamenat svou práci do tohoto souboru pomocí specifikovaného formátu. Tím se vytváří lidsky čitelný auditní záznam všech vývojových aktivit.
*   **`IDEAS.md`**: Tento soubor je vyhrazeným prostorem pro zaznamenávání nápadů, návrhů nebo potenciálních vylepšení, která jsou mimo rozsah aktuálního úkolu. Tím se zabrání ztrátě dobrých nápadů.

## 5. Živá Dokumentace Architektury

*   **`PROJECT_STRUCTURE.md`**: Tento soubor bude obsahovat strojově čitelný přehled všech implementovaných pluginů, jejich typů a stručný popis. Bude **automaticky aktualizován** skriptem (`scripts/update_structure_doc.py`) spouštěným pomocí GitHub Action po každém úspěšném sloučení do větve `develop`. Tím je zajištěno, že dokumentace nikdy nezastará.
