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

### 3.3. Pokročilé ověření: 5krokový benchmark a autonomní ladění
Pro významné změny v Kernelu nebo klíčových pluginech se používá komplexní, 5krokový benchmark k ověření end-to-end funkčnosti systému. Tento test je navržen pro spuštění v neinteraktivním "testovacím režimu" aplikace a ověřuje několik klíčových architektonických prvků najednou.

**Účel:**
Benchmark potvrzuje správnou funkci:
1.  **Objevování nástrojů:** Schopnost plánovače vidět všechny dostupné nástroje.
2.  **Práce se soubory (I/O):** Schopnost `FileSystemTool` zapisovat a číst soubory.
3.  **Řetězení výsledků:** "Krátkodobá paměť" Kernelu pro použití výstupu jednoho kroku jako vstupu pro další.
4.  **Vkládání kontextu a propagace historie:** Schopnost Kernelu poskytovat nástrojům potřebný kontext a historii konverzace.

**Spuštění benchmarku:**
Spusťte následující příkaz z kořenového adresáře projektu:
```bash
python run.py --test "List all available tools. Then, write the list of tools to a file named 'tools.txt'. After that, read the content of the 'tools.txt' file. Next, use the LLMTool to summarize the content of the file. Finally, delete the 'tools.txt' file."
```

**Klíčové architektonické koncepty ověřené benchmarkem:**
Úspěšné spuštění tohoto benchmarku závisí na dvou kritických architektonických prvcích implementovaných v Kernelu:

1.  **Vkládání kontextu (Context Injection):**
    Kernel dokáže inteligentně poskytnout kontext nástrojům, které jej potřebují. Prozkoumá signaturu metody nástroje, a pokud je přítomen parametr `context`, Kernel automaticky vytvoří a vloží objekt `SharedContext`. To umožňuje nástrojům přistupovat k ID sezení, loggeru a historii konverzace, aniž by jim tyto argumenty musely být explicitně předány v plánu.

2.  **Propagace historie (History Propagation):**
    U vícekrokových plánů je udržení kontextu klíčové. Kernel zajišťuje, že LLM má pro každý krok potřebné informace, vytvořením nového `SharedContext` objektu s kompletní historií pro každé volání nástroje. Tento kontext zahrnuje původní požadavek uživatele *plus* výsledky všech předchozích kroků jako zprávy od "asistenta" v historii. To dává AI kompletní přehled o probíhajícím úkolu, což je nezbytné pro komplexní operace, jako je shrnutí souboru, který byl právě zapsán.

### 3.4. Poznámka k `pytest` a logování
Při psaní integračních testů, které zahrnují `Kernel`, je důležité si být vědom potenciálního konfliktu s `pytest` fixturou `caplog`. Inicializační proces Kernelu konfiguruje logovací systém aplikace, což může narušit schopnost `caplog` zachytávat logovací záznamy.

Pokud narazíte na problémy, kdy `caplog` nezachytává logy podle očekávání, doporučeným řešením je patchnout nastavení logování aplikace po dobu trvání testu. To lze provést pomocí dekorátoru:
```python
@patch("core.logging_config.setup_logging")
def test_my_kernel_integration(mock_setup_logging, caplog):
    # Váš testovací kód zde
```
Tím zajistíte, že test poběží s výchozí konfigurací logování, kterou `caplog` očekává, a poskytne spolehlivé zachycení logů pro vaše aserce.

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

## 6. Kognitivní Pluginy (Cognitive Plugins)

Kognitivní pluginy jsou "mozkem" agenta, zodpovědné za interpretaci uživatelských požadavků a rozhodování.

### 6.1. Cognitive Task Router (`cognitive_task_router`)
- **Účel:** Fungovat jako strategický orchestrátor, který vybírá nejvhodnější LLM pro daný úkol na základě jeho složitosti. Tím se optimalizují náklady i výkon.
- **Pracovní postup:**
  1.  Přijme počáteční vstup od uživatele z Kernelu.
  2.  Použije rychlý a levný LLM k zařazení vstupu do předdefinované kategorie (např. "jednoducha_otazka", "komplexni_uvazovani").
  3.  Vyhledá nejlepší model pro danou kategorii v konfiguračním souboru strategie.
  4.  Vloží název vybraného modelu do `payload` objektu `SharedContext`.
- **Konfigurace (`config/model_strategy.yaml`):**
  Chování routeru je definováno v YAML souboru. To umožňuje aktualizovat strategie bez změny kódu pluginu.
  ```yaml
  # Definuje model použitý pro samotný krok klasifikace
  classification_model: "openrouter/anthropic/claude-3-haiku"

  # Model, který se použije, pokud klasifikace z jakéhokoli důvodu selže
  default_model: "openrouter/anthropic/claude-3-sonnet"

  # Seznam různých strategií
  task_strategies:
    - name: "jednoducha_otazka"
      description: "Pro rychlé a jednoduché otázky a odpovědi."
      # Použijte levný a rychlý model pro jednoduché úkoly
      model: "openrouter/anthropic/claude-3-haiku"
    - name: "komplexni_uvazovani"
      description: "Pro složité plánování a volání nástrojů, které vyžaduje vysoce kvalitní uvažování."
      # Použijte výkonný model pro složité úkoly
      model: "openrouter/anthropic/claude-3-sonnet"
  ```
- **Následné použití:** Plugin `LLMTool` je navržen tak, aby kontroloval `SharedContext`, zda v `payload` existuje klíč `selected_model`. Pokud ano, použije tento model pro své API volání a přepíše tak celosystémové výchozí nastavení.

### 6.2. Cognitive Planner (`cognitive_planner`)
- **Účel:** Analyzuje požadavek uživatele a dostupné nástroje k vytvoření podrobného plánu, který může Kernel vykonat.
- **Poznámka:** Tento plugin běží *po* `CognitiveTaskRouter`, takže bude těžit z výběru modelu, který router provedl.

## 7. Dostupné Nástrojové Pluginy (Tool Plugins)

Tato sekce poskytuje přehled dostupných `TOOL` pluginů, které mohou kognitivní pluginy používat.

### 7.1. File System Tool (`tool_file_system`)

-   **Účel:** Poskytuje bezpečný, izolovaný přístup k lokálnímu souborovému systému.
-   **Konfigurace (`config/settings.yaml`):**
    ```yaml
    tool_file_system:
      sandbox_dir: "sandbox"
    ```
-   **Metody:**
    -   `read_file(path: str) -> str`: Čte obsah souboru v sandboxu.
    -   `write_file(path: str, content: str) -> str`: Zapisuje obsah do souboru v sandboxu.
    -   `list_directory(path: str) -> List[str]`: Vypíše obsah adresáře v sandboxu.

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
