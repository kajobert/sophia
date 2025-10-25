# Sophia V2 - Příručka pro vývojáře

Tato příručka poskytuje pokyny a osvědčené postupy pro vývojáře přispívající do projektu Sophia V2.

## 1. Začínáme

### 1.1. Předpoklady
Ujistěte se, že máte v systému nainstalováno následující:
- **Python 3.12 nebo vyšší:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Git:** [https://git-scm.com/downloads](https://git-scm.com/downloads)
- **`uv`:** Rychlý instalátor Python balíčků. Nainstalujte jej přes `pip`:
  ```bash
  pip install uv
  ```

### 1.2. Nastavení prostředí
1.  **Klonujte repozitář:**
    ```bash
    git clone https://github.com/kajobert/sophia.git
    cd sophia
    ```

2.  **Vytvořte a aktivujte virtuální prostředí:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```
    Ve Windows použijte `.venv\Scripts\activate`.

3.  **Nainstalujte závislosti:**
    Nainstalujte jak základní závislosti aplikace, tak i vývojové závislosti.
    ```bash
    uv pip install -r requirements.in -r requirements-dev.in
    ```

4.  **Nastavte pre-commit hooks:**
    Tím zajistíte, že váš kód bude před commitem zformátován a zkontrolován.
    ```bash
    pre-commit install
    ```

## 2. Vývojový proces

### 2.1. Strategie větví
Všechny nové funkce a opravy chyb by měly být vyvíjeny ve feature větvi.
- Vytvořte novou větev z `develop`:
  ```bash
  git checkout develop
  git pull origin develop
  git checkout -b feature/nazev-vasi-funkce
  ```
- Jakmile je vaše práce hotová a otestovaná, vytvořte pull request pro sloučení vaší feature větve zpět do `develop`.

### 2.2. Provádění změn
Když provádíte změny v kódu, ujistěte se, že také aktualizujete veškerou relevantní dokumentaci. Toto je striktní požadavek pro všechny příspěvky.

## 3. Testování

Projekt používá `pytest` pro testování.

### 3.1. Spuštění testů
Pro spuštění celé testovací sady spusťte následující příkaz z kořenového adresáře projektu:
```bash
PYTHONPATH=. .venv/bin/python -m pytest
```

### 3.2. Psaní nových testů
- Veškerý nový kód musí být doprovázen odpovídajícími testy.
- Pro nový plugin `plugins/muj_plugin.py` musíte vytvořit testovací soubor `tests/plugins/test_muj_plugin.py`.
- Testy by měly být soběstačné a neměly by záviset na externích službách nebo API klíčích. Vhodně používejte mocking.

## 4. Kvalita kódu

Používáme `pre-commit` k vynucení standardů kvality kódu. Nakonfigurované nástroje jsou:
- **`black`:** Pro konzistentní formátování kódu.
- **`ruff`:** Pro linting a kontrolu stylu.
- **`mypy`:** Pro statickou kontrolu typů.

Tyto kontroly se spustí automaticky při každém commitu. Můžete je také spustit ručně:
```bash
pre-commit run --all-files
```

## 5. Vytvoření nového pluginu

Architektura je navržena tak, aby byla rozšiřitelná pomocí pluginů.

### 5.1. Kontrakt `BasePlugin`
Všechny pluginy musí dědit z `plugins.base_plugin.BasePlugin` a implementovat následující:
- `name` (property): Unikátní řetězcový identifikátor pluginu.
- `plugin_type` (property): Jeden z `PluginType` enumů (`INTERFACE`, `TOOL`, `MEMORY`).
- `version` (property): Verze pluginu.
- `setup(self, config: dict)`: Metoda volaná Kernelem při startu. Použijte ji k načtení konfigurace, inicializaci zdrojů a nastavení routes, pokud se jedná o webový plugin.
- `async execute(self, context: SharedContext)`: Hlavní vstupní bod pro plugin, který je volán Kernelem během příslušné fáze `consciousness_loop`.

### 5.2. Objekt `SharedContext`
`SharedContext` je datový objekt předávaný mezi pluginy. Umožňuje jim sdílet stav a data v rámci jednoho cyklu `consciousness_loop`. Klíčové atributy zahrnují:
- `user_input`: Vstup přijatý od interface pluginu.
- `history`: Historie konverzace.
- `payload`: Slovník pro ukládání a načítání dat pluginy.

## 6. Dostupné nástrojové pluginy (Tool Plugins)

Tato sekce poskytuje přehled dostupných `TOOL` pluginů, které mohou být použity kognitivními pluginy.

### 6.1. File System Tool (`tool_file_system`)

-   **Účel:** Poskytuje bezpečný, sandboxed přístup k lokálnímu souborovému systému.
-   **Konfigurace (`config/settings.yaml`):**
    ```yaml
    tool_file_system:
      sandbox_dir: "sandbox"
    ```
-   **Metody:**
    -   `read_file(path: str) -> str`: Přečte obsah souboru v sandboxu.
    -   `write_file(path: str, content: str) -> str`: Zapíše obsah do souboru v sandboxu.
    -   `list_directory(path: str) -> List[str]`: Vypíše obsah adresáře v sandboxu.

## 7. Odeslání změn

1.  **Ujistěte se, že všechny testy projdou:** Spusťte `PYTHONPATH=. .venv/bin/python -m pytest`.
2.  **Ujistěte se, že všechny kontroly kvality projdou:** Spusťte `pre-commit run --all-files`.
3.  **Aktualizujte dokumentaci:** Ujistěte se, že všechny změny v codebase se odrážejí v relevantních dokumentačních souborech.
4.  **Vytvořte Pull Request:** Pushněte vaši feature větev do vzdáleného repozitáře a otevřete pull request proti větvi `develop`.
5.  **Code Review:** Váš pull request bude zkontrolován jiným vývojářem. Před sloučením vyřešte veškerou zpětnou vazbu.
