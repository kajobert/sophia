# Dokument 5: Governance, Automatizace a Workflow

Tento dokument definuje procesy, nástroje a automatizaci, které zajišťují kvalitu, efektivitu a přehlednost vývoje projektu Sophia V2.

## 1. GitHub Workflow & Strategie Větvení

Pro zajištění stability a předvídatelnosti dodržujeme strukturovaný Git workflow.

*   **`main`**: Obsahuje pouze stabilní, otestované verze. Merge do `main` je možný pouze přes Pull Request z větve `develop` po důkladné revizi a testování.
*   **`develop`**: Hlavní vývojová větev. Obsahuje nejnovější, integrované funkce a představuje aktuální "edge" verzi aplikace.
*   **`feature/nazev-funkce`**: Veškerý nový vývoj (nové pluginy, funkce, opravy) se odehrává v těchto větvích, které vždy vycházejí z aktuální větve `develop`.

## 2. Pull Requests (PR)

*   Každý PR do větve `develop` musí projít všemi automatickými kontrolami (CI).
*   Používáme šablony pro PR, které vyžadují jasný a strukturovaný popis změn.

## 3. Automatizace (CI/CD) s GitHub Actions

Soubor `.github/workflows/ci.yml` bude automaticky při každém PR spouštět následující úlohy:

1.  **Linting a Formátování**:
    *   **`black`**: Zajišťuje jednotný a čistý formát kódu.
    *   **`ruff`**: Kontroluje kód pro širokou škálu chyb a stylistických problémů.
    *   **`mypy`**: Provádí statickou typovou kontrolu.

2.  **Unit & Integrační Testy**:
    *   **`pytest`**: Spouští všechny testy v adresáři `tests/`.

3.  **Ověření Sestavení Docker Obrazu**:
    *   Poslední krok se pokusí sestavit Docker obraz, aby se předešlo chybám v produkčním prostředí.

## 4. Povinná Dokumentace Práce

*   **`WORKLOG.md`**: Je povinností každého agenta po dokončení práce zapsat strukturovaný záznam podle šablony v `AGENTS.md`.
*   **`IDEAS.md`**: Nový soubor pro zaznamenávání nápadů, které nesouvisí s aktuálním úkolem, aby se předešlo jejich ztrátě.

## 5. Živá Dokumentace Architektury

*   **`PROJECT_STRUCTURE.md`**: Tento soubor bude obsahovat strojově čitelný přehled všech implementovaných pluginů. Bude **automaticky aktualizován** skriptem po každém úspěšném mergi do větve `develop`, což zajistí, že dokumentace nikdy nezastará.
