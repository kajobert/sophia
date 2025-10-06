# 🤖 Manuál pro AI Agenta: Jules (Nomad)

**Verze:** 2.0
**Datum:** 2025-10-03

Tento dokument slouží jako technická a provozní příručka pro AI agenta "Jules". Popisuje jeho dostupné nástroje, pracovní postupy a základní principy, které řídí jeho operace v rámci projektu Sophia.

---

## 1. Přehled Nástrojů (Tool Reference)

Jules má k dispozici dvě kategorie nástrojů: **Standardní Nástroje** s Python syntaxí a **Speciální Nástroje** s vlastní DSL syntaxí.

### 1.1. Standardní Nástroje

Tyto nástroje jsou seskupeny podle jejich primárního účelu.

#### **Základní Práce se Soubory**
- **`list_files(path: str = ".") -> str`**: Vypíše soubory a adresáře v zadané cestě.
- **`read_file(filepath: str, line_limit: int = None) -> str`**: Přečte obsah souboru. Lze omezit počet načtených řádků.
- **`read_file_section(filepath: str, identifier: str) -> str`**: Načte z Python souboru pouze konkrétní třídu nebo funkci.
- **`delete_file(filepath: str) -> str`**: Smaže zadaný soubor.
- **`rename_file(filepath: str, new_filepath: str) -> str`**: Přejmenuje nebo přesune soubor.

#### **Analýza Kódu a Projektu**
- **`get_project_summary(start_path: str = ".") -> str`**: Vygeneruje přehled struktury projektu, včetně docstringů pro rychlý přehled.
- **`profile_code_execution(command: str) -> str`**: Spustí příkaz pomocí cProfile a vrátí report o výkonu.
- **`run_static_code_analyzer(path: str) -> str`**: Spustí Pylint na soubor/adresář a vrátí report o kvalitě kódu.
- **`get_code_complexity(path: str) -> str`**: Spustí Radon na soubor/adresář a vrátí report o složitosti a udržovatelnosti.

#### **Plánování a Správa Úkolů**
- **`create_task(description: str, parent_id: str = None) -> str`**: Vytvoří nový úkol nebo podúkol pro hierarchické plánování.
- **`get_task_tree() -> str`**: Zobrazí stromovou strukturu všech aktuálních úkolů a jejich stav.
- **`update_task_status(task_id: str, status: str) -> str`**: Aktualizuje stav úkolu (např. 'in_progress', 'completed').
- **`get_task_details(task_id: str) -> str`**: Vrátí detailní informace o konkrétním úkolu.
- **`summarize_text(text_to_summarize: str) -> str`**: Využije LLM k sumarizaci dlouhého textu.

#### **Evoluce a Experimentování (Sandbox)**
- **`create_code_sandbox(files_to_copy: list[str]) -> str`**: Vytvoří dočasný, izolovaný adresář a zkopíruje do něj soubory pro bezpečné experimentování.
- **`run_in_sandbox(command: str) -> str`**: Spustí příkaz uvnitř aktivního sandboxu.
- **`compare_sandbox_changes(original_filepath: str) -> str`**: Porovná soubor v sandboxu s jeho originálem a vrátí 'diff'.
- **`destroy_sandbox() -> str`**: Smaže aktivní sandbox a jeho obsah.

#### **Evoluce a Učení**
- **`run_playwright_test(script_content: str) -> str`**: Spustí E2E test pomocí Playwright.
- **`propose_refactoring(filepath: str, class_or_function: str) -> str`**: Využije LLM k navržení vylepšení pro zadaný kód.
- **`archive_completed_task(task_id: str, summary: str, history: list) -> str`**: Uloží kompletní záznam o dokončeném úkolu do archivu.
- **`search_task_archive(query: str) -> str`**: Prohledá archiv dokončených úkolů a najde relevantní "vzpomínky".
- **`update_self_knowledge(new_knowledge: str) -> str`**: Přidá nový poznatek do agentovy báze znalostí.

#### **Komunikace s Uživatelem**
- **`inform_user(message: str) -> str`**: Zobrazí uživateli informativní zprávu (zeleně).
- **`warn_user(message: str) -> str`**: Zobrazí uživateli varování (oranžově).
- **`error_user(message: str) -> str`**: Zobrazí uživateli chybovou hlášku (červeně).
- **`ask_user(question: str) -> str`**: Položí uživateli otázku.
- **`display_code(code: str, language: str = "python") -> str`**: Zobrazí formátovaný blok kódu.
- **`display_table(title: str, headers: list[str], rows: list[list[str]]) -> str`**: Zobrazí tabulku.

#### **Řízení Agenta**
- **`set_plan(plan: str) -> None`**
- **`plan_step_complete(message: str) -> None`**
- **`request_user_input(message: str) -> None`**
- **`request_code_review() -> str`**
- **`submit(...)`**

### 1.2. Speciální Nástroje

Tyto nástroje používají specifickou DSL syntaxi, kde je název nástroje na prvním řádku a argumenty na dalších.

- **`run_in_bash_session`**
  - **Popis:** Spustí příkaz v perzistentní bash session.
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
  - **Popis:** Provede cílenou úpravu části souboru.
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
        1.  **Průzkum:** Pomocí `list_files` a `read_file` prozkoumá relevantní soubory.
        2.  **Dotazování:** Pokud je zadání nejasné, použije `request_user_input`.
        3.  **Tvorba Plánu:** Vytvoří podrobný, číslovaný plán a nastaví ho pomocí `set_plan`.

2.  **Implementace a Verifikace:**
    - **Cíl:** Napsat čistý kód a zajistit, že každá změna je správná.
    - **Proces:**
        1.  **Modifikace Kódu:** Používá `create_file_with_block`, `overwrite_file_with_block` nebo `replace_with_git_merge_diff`.
        2.  **Okamžitá Verifikace:** **Po každé úpravě** ověří, že se změna úspěšně projevila.
        3.  **Označení Kroku:** Po úspěšné verifikaci označí krok plánu jako dokončený.

3.  **Testování a Debugování:**
    - **Cíl:** Ověřit, že změny fungují a nezpůsobily regrese.
    - **Proces:**
        1.  **Spuštění Testů:** Pomocí `run_in_bash_session` spustí relevantní testy (`pytest`).
        2.  **Analýza Chyb:** Analyzuje logy a chybové hlášky.
        3.  **Iterativní Opravy:** Opakuje cyklus, dokud všechny testy neprojdou.

4.  **Dokumentace a Odevzdání:**
    - **Cíl:** Trvale zaznamenat vykonanou práci a odevzdat ji.
    - **Proces:**
        1.  **Aktualizace Dokumentace:** Aktualizuje relevantní dokumenty.
        2.  **Revize Kódu:** Vyžádá si revizi kódu pomocí `request_code_review()`.
        3.  **Odevzdání:** Po schválení revize odevzdá práci pomocí `submit`.

---

## 3. Základní Principy

- **Vždy Ověřuj Svou Práci:** Po každé akci, která mění stav, musí následovat ověření.
- **Testuj Proaktivně:** Vždy hledej a spouštěj relevantní testy.
- **Upravuj Zdroj, Ne Artefakty:** Nikdy neupravuj soubory v adresářích jako `dist/` nebo `build/`.
- **Diagnostikuj, Než Změníš Prostředí:** Nejprve analyzuj, potom jednej.
- **Autonomie s Rozumem:** Požádej o pomoc, když ji potřebuješ.
