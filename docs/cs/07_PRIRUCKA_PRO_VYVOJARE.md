# Sophia V2 - Příručka pro vývojáře

Tato příručka poskytuje pokyny a osvědčené postupy pro vývojáře, kteří přispívají do projektu Sophia V2.

## 1. Začínáme

### 1.1. Předpoklady
Ujistěte se, že máte v systému nainstalovány následující nástroje:
- **Python 3.12 nebo vyšší:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **Git:** [https://git-scm.com/downloads](https://git-scm.com/downloads)
- **`uv`:** Rychlý instalátor Python balíčků. Nainstalujte jej pomocí `pip`:
  ```bash
  pip install uv
  ```

### 1.2. Nastavení prostředí
1.  **Klonování repozitáře:**
    ```bash
    git clone https://github.com/kajobert/sophia.git
    cd sophia
    ```

2.  **Vytvoření a aktivace virtuálního prostředí:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```
    Na Windows použijte `.venv\Scripts\activate`.

3.  **Instalace závislostí:**
    Nainstalujte jak základní závislosti aplikace, tak vývojové závislosti.
    ```bash
    uv pip install -r requirements.in -r requirements-dev.in
    ```

4.  **Nastavení pre-commit hooks:**
    Tím zajistíte, že váš kód bude před commitem zformátován a zkontrolován.
    ```bash
    pre-commit install
    ```

## 2. Vývojový proces

### 2.1. Strategie větví
Všechny nové funkce a opravy chyb by měly být vyvíjeny ve `feature` větvích.
- Vytvořte novou větev z `develop`:
  ```bash
  git checkout develop
  git pull origin develop
  git checkout -b feature/nazev-vasi-funkce
  ```
- Jakmile je vaše práce hotová a otestovaná, vytvořte pull request pro sloučení vaší feature větve zpět do `develop`.

### 2.2. Provádění změn
Při provádění změn v kódu se ujistěte, že také aktualizujete veškerou relevantní dokumentaci. Toto je striktní požadavek pro všechny příspěvky.

## 3. Testování

Projekt používá `pytest` pro testování.

### 3.1. Spouštění testů
Pro spuštění celé testovací sady spusťte následující příkaz z kořenového adresáře projektu:
```bash
PYTHONPATH=. .venv/bin/python -m pytest
```

### 3.2. Psaní nových testů
- Veškerý nový kód musí být doprovázen odpovídajícími testy.
- Pro nový plugin `plugins/muj_plugin.py` musíte vytvořit testovací soubor `tests/plugins/test_muj_plugin.py`.
- Testy by měly být soběstačné a neměly by záviset na externích službách nebo API klíčích. V případě potřeby použijte mocking.

## 4. Kvalita kódu

Pro zajištění kvality kódu používáme `pre-commit`. Nakonfigurované nástroje jsou:
- **`black`:** Pro konzistentní formátování kódu.
- **`ruff`:** Pro linting a kontrolu stylu.
- **`mypy`:** Pro statickou typovou kontrolu.

Tyto kontroly se spustí automaticky při každém commitu. Můžete je také spustit ručně:
```bash
pre-commit run --all-files
```

## 5. Vytvoření nového pluginu

Architektura je navržena tak, aby byla rozšiřitelná pomocí pluginů.

### 5.1. Kontrakt `BasePlugin`
Všechny pluginy musí dědit z `plugins.base_plugin.BasePlugin` a implementovat následující:
- `name` (property): Unikátní řetězcový identifikátor pro plugin.
- `plugin_type` (property): Jeden z `PluginType` enumů (`INTERFACE`, `TOOL`, `MEMORY`).
- `version` (property): Verze pluginu.
- `setup(self, config: dict)`: Metoda volaná Kernelem při startu. Použijte ji k načtení konfigurace, inicializaci zdrojů a nastavení rout, pokud se jedná o webový plugin.
- `async execute(self, context: SharedContext)`: Hlavní vstupní bod pro plugin, který je volán Kernelem během příslušné fáze `consciousness_loop`.

### 5.2. Objekt `SharedContext`
`SharedContext` je datový objekt předávaný mezi pluginy. Umožňuje jim sdílet stav a data v rámci jednoho cyklu `consciousness_loop`. Klíčové atributy zahrnují:
- `user_input`: Vstup přijatý z interface pluginu.
- `history`: Historie konverzace.
- `payload`: Slovník, do kterého mohou pluginy ukládat a načítat data.

### 5.3. Zpřístupnění funkcí jako nástrojů pro AI
Jakýkoli plugin (bez ohledu na jeho `PluginType`) může zpřístupnit své metody, aby je AI mohla volat. Toho je dosaženo pomocí konvence "duck typing". Kernel automaticky objeví jakýkoli plugin, který implementuje metodu `get_tool_definitions`.

Chcete-li zpřístupnit metody pluginu jako nástroje:
1.  **Implementujte `get_tool_definitions(self) -> List[Dict[str, Any]]`:** Přidejte tuto metodu do svého pluginu.
2.  **Definujte Pydantic schéma pro argumenty:** Pro každou funkci, kterou chcete zpřístupnit, vytvořte `pydantic.BaseModel`, který definuje její argumenty. To je klíčové pro správnou funkci "Validation & Repair Loop" v Kernelu.
3.  **Vraťte schéma nástroje:** Metoda `get_tool_definitions` musí vrátit seznam slovníků, kde každý slovník odpovídá specifikaci [OpenAPI JSON Schema](https://swagger.io/specification/), které AI model rozumí.

**Příklad: Zpřístupnění funkce `list_directory` v `FileSystemTool`**
```python
# V souboru plugins/tool_file_system.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any

# 1. Definujte Pydantic schéma pro argumenty funkce
class ListDirectoryArgs(BaseModel):
    path: str = Field(..., description="Cesta k adresáři, jehož obsah se má vypsat.")

class FileSystemTool(BasePlugin):
    # ... další metody pluginu ...

    def list_directory(self, path: str) -> List[str]:
        # ... implementace ...
        return ["soubor1.txt", "soubor2.txt"]

    # 2. Implementujte metodu pro objevení
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "list_directory",
                    "description": "Vypíše obsah adresáře v sandboxu.",
                    # 3. Odkazujte na Pydantic schéma
                    "parameters": ListDirectoryArgs.model_json_schema(),
                },
            }
        ]
```
Dodržením této konvence bude plánovač a exekuční engine Kernelu schopen automaticky vidět, validovat a volat metody vašeho pluginu.

## 6. Odeslání změn

1.  **Ujistěte se, že všechny testy procházejí:** Spusťte `PYTHONPATH=. .venv/bin/python -m pytest`.
2.  **Ujistěte se, že všechny kontroly kvality procházejí:** Spusťte `pre-commit run --all-files`.
3.  **Aktualizujte dokumentaci:** Ujistěte se, že jakékoli změny v kódové základně jsou zohledněny v relevantních dokumentačních souborech.
4.  **Vytvořte Pull Request:** Nahrajte svou feature větev do vzdáleného repozitáře a otevřete pull request proti větvi `develop`.
5.  **Code Review:** Váš pull request bude zkontrolován jiným vývojářem. Před sloučením opravte veškeré připomínky.
