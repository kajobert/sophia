# 🤖 Manuál pro AI Agenta: Jules (Nomad)

**Verze:** 1.0
**Datum:** 2025-09-28

Tento dokument slouží jako technická a provozní příručka pro AI agenta "Jules". Popisuje jeho dostupné nástroje, pracovní postupy a základní principy, které řídí jeho operace v rámci projektu Sophia.

---

## 1. Přehled Nástrojů (Tool Reference)

Jules má k dispozici dvě kategorie nástrojů: **Standardní Nástroje** s Python syntaxí a **Speciální Nástroje** s vlastní DSL syntaxí.

### 1.1. Standardní Nástroje

Tyto nástroje se volají pomocí standardní syntaxe funkce v Pythonu.

- **`list_files(path: str = ".") -> list[str]`**
  - **Popis:** Vypíše soubory a adresáře v zadané cestě. Adresáře jsou označeny lomítkem (`/`).
  - **Parametry:**
    - `path` (str, volitelný): Cesta k adresáři, jehož obsah se má vypsat. Výchozí je kořenový adresář projektu.

- **`read_file(filepath: str) -> str`**
  - **Popis:** Přečte a vrátí obsah zadaného souboru.
  - **Parametry:**
    - `filepath` (str): Cesta k souboru, který se má přečíst.

- **`set_plan(plan: str) -> None`**
  - **Popis:** Nastaví nebo aktualizuje podrobný, číslovaný plán pro řešení úkolu.
  - **Parametry:**
    - `plan` (str): Popis plánu ve formátu Markdown.

- **`plan_step_complete(message: str) -> None`**
  - **Popis:** Označí aktuální krok plánu jako dokončený.
  - **Parametry:**
    - `message` (str): Stručný popis toho, co bylo v daném kroku vykonáno.

- **`message_user(message: str, continue_working: bool) -> None`**
  - **Popis:** Odešle zprávu uživateli.
  - **Parametry:**
    - `message` (str): Text zprávy pro uživatele.
    - `continue_working` (bool): Pokud `True`, agent pokračuje v práci ihned po odeslání zprávy. Pokud `False`, čeká na odpověď uživatele.

- **`request_user_input(message: str) -> None`**
  - **Popis:** Položí uživateli otázku a pozastaví provádění, dokud nedostane odpověď.
  - **Parametry:**
    - `message` (str): Otázka nebo výzva pro uživatele.

- **`request_code_review() -> str`**
  - **Popis:** Vyžádá si revizi kódu pro provedené změny. Je povinné použít před odesláním.
  - **Parametry:** Žádné.

- **`submit(branch_name: str, commit_message: str, title: str, description: str) -> None`**
  - **Popis:** Odevzdá finální práci vytvořením committu a žádostí o schválení.
  - **Parametry:**
    - `branch_name` (str): Název nové větve.
    - `commit_message` (str): Podrobná zpráva committu.
    - `title` (str): Krátký, výstižný název změny.
    - `description` (str): Delší popis provedených změn.

- **`delete_file(filepath: str) -> str`**
  - **Popis:** Smaže zadaný soubor.
  - **Parametry:**
    - `filepath` (str): Cesta k souboru, který se má smazat.

- **`rename_file(filepath: str, new_filepath: str) -> str`**
  - **Popis:** Přejmenuje nebo přesune soubor.
  - **Parametry:**
    - `filepath` (str): Původní cesta k souboru.
    - `new_filepath` (str): Nová cesta k souboru.

### 1.2. Speciální Nástroje

Tyto nástroje používají specifickou DSL syntaxi, kde je název nástroje na prvním řádku a argumenty na dalších.

- **`run_in_bash_session`**
  - **Popis:** Spustí příkaz v perzistentní bash session. Umožňuje instalaci závislostí, spouštění testů, kompilaci a další shell operace.
  - **Syntax:**
    ```
    run_in_bash_session
    <příkaz k provedení>
    ```

- **`create_file_with_block`**
  - **Popis:** Vytvoří nový soubor a zapíše do něj zadaný obsah.
  - **Syntax:**
    ```
    create_file_with_block
    <cesta_k_souboru>
    <obsah souboru na více řádcích>
    ```

- **`overwrite_file_with_block`**
  - **Popis:** Kompletně přepíše existující soubor novým obsahem.
  - **Syntax:**
    ```
    overwrite_file_with_block
    <cesta_k_souboru>
    <nový obsah souboru>
    ```

- **`replace_with_git_merge_diff`**
  - **Popis:** Provede cílenou úpravu části souboru pomocí vyhledávání a nahrazování ve formátu merge-konfliktu.
  - **Syntax:**
    ```
    replace_with_git_merge_diff
    <cesta_k_souboru>
    <<<<<<< SEARCH
    <blok kódu k nalezení>
    =======
    <blok kódu, kterým se nahradí nalezený blok>
    >>>>>>> REPLACE
    ```

---

## 2. Pracovní Postup (Workflow)

Jules funguje v cyklu, který je řízen "meta-promptem" a interakcí s LLM (Gemini). Tento cyklus lze rozdělit do následujících fází:

1.  **Analýza a Plánování:**
    - **Cíl:** Plně porozumět zadání a vytvořit transparentní plán.
    - **Proces:**
        1.  **Průzkum:** Pomocí `list_files` a `read_file` prozkoumá relevantní soubory, zejména `README.md` a `AGENTS.md`, aby získal kontext.
        2.  **Dotazování:** Pokud je zadání nejasné, použije `request_user_input` k získání dalších informací.
        3.  **Tvorba Plánu:** Vytvoří podrobný, číslovaný plán a nastaví ho pomocí `set_plan`. Tento plán slouží jako vodítko pro něj i pro uživatele.

2.  **Implementace a Verifikace:**
    - **Cíl:** Napsat čistý kód a zajistit, že každá změna je správná.
    - **Proces:**
        1.  **Modifikace Kódu:** Používá `create_file_with_block`, `overwrite_file_with_block` nebo `replace_with_git_merge_diff` k úpravě kódu.
        2.  **Okamžitá Verifikace:** **Po každé úpravě** okamžitě použije `read_file` nebo `ls`, aby ověřil, že se změna úspěšně a správně projevila. Tento krok je klíčový pro předejití chybám.
        3.  **Označení Kroku:** Po úspěšné verifikaci označí krok plánu jako dokončený pomocí `plan_step_complete`.

3.  **Testování a Debugování:**
    - **Cíl:** Ověřit, že změny fungují a nezpůsobily regrese.
    - **Proces:**
        1.  **Spuštění Testů:** Pomocí `run_in_bash_session` spustí relevantní testy (`pytest`, `npm test` atd.).
        2.  **Analýza Chyb:** Pokud testy selžou, pečlivě analyzuje logy a chybové hlášky.
        3.  **Iterativní Opravy:** Vrací se do fáze implementace, aby opravil chyby, a tento cyklus opakuje, dokud všechny testy neprojdou.

4.  **Dokumentace a Odevzdání:**
    - **Cíl:** Trvale zaznamenat vykonanou práci a odevzdat ji.
    - **Proces:**
        1.  **Aktualizace Dokumentace:** Pokud je to relevantní, aktualizuje `README.md` nebo jiné dokumentační soubory.
        2.  **Revize Kódu:** Vyžádá si revizi kódu pomocí `request_code_review()`.
        3.  **Odevzdání:** Po schválení revize odevzdá práci pomocí `submit`.

---

## 3. Základní Principy

- **Vždy Ověřuj Svou Práci:** Po každé akci, která mění stav (zápis souboru, smazání), musí následovat ověření pomocí nástroje pro čtení (`read_file`, `ls`).
- **Testuj Proaktivně:** Vždy hledej a spouštěj relevantní testy. Pokud je to možné, piš nejprve selhávající testy.
- **Upravuj Zdroj, Ne Artefakty:** Nikdy neupravuj soubory v adresářích jako `dist/` nebo `build/`. Vždy najdi původní zdrojový soubor a upravuj ten.
- **Diagnostikuj, Než Změníš Prostředí:** Pokud dojde k chybě při buildu nebo testování, nejprve analyzuj logy a konfiguraci. Změny v prostředí (instalace balíčků) jsou až poslední možností.
- **Autonomie s Rozumem:** Snaž se řešit problémy samostatně, ale pokud se dostaneš do smyčky nebo je zadání nejasné, použij `request_user_input` a požádej o pomoc.