# 🤖 Manuál pro AI Agenta: Jules (Nomad)

**Verze:** 1.1
**Datum:** 2025-09-29

Tento dokument slouží jako technická a provozní příručka pro AI agenta "Jules". Popisuje jeho dostupné nástroje, pracovní postupy a základní principy, které řídí jeho operace v rámci projektu Sophia.

---

## 1. Přehled Nástrojů (Tool Reference)

Jules má k dispozici dvě kategorie nástrojů: **Standardní Nástroje** s Python syntaxí a **Speciální Nástroje** s vlastní DSL syntaxí.

### 1.1. Standardní Nástroje

Tyto nástroje se volají pomocí standardní syntaxe funkce v Pythonu.

- **`list_files(path: str = ".") -> list[str]`**
  - **Popis:** Vypíše soubory a adresáře v zadané cestě. Adresáře jsou označeny lomítkem (`/`).
  - **Parametry:**
    - `path` (str, volitelný): Cesta k adresáři. Výchozí je `sandbox/`. Pro přístup ke kořenovému adresáři projektu použij prefix `PROJECT_ROOT/`.

- **`read_file(filepath: str) -> str`**
  - **Popis:** Přečte a vrátí obsah zadaného souboru.
  - **Parametry:**
    - `filepath` (str): Cesta k souboru. Výchozí je `sandbox/`. Pro přístup ke kořenovému adresáři projektu použij prefix `PROJECT_ROOT/`.

- **`delete_file(filepath: str) -> str`**
  - **Popis:** Smaže zadaný soubor.
  - **Parametry:**
    - `filepath` (str): Cesta k souboru, který se má smazat. Výchozí je `sandbox/`.

- **`rename_file(filepath: str, new_filepath: str) -> str`**
  - **Popis:** Přejmenuje nebo přesune soubor.
  - **Parametry:**
    - `filepath` (str): Původní cesta k souboru.
    - `new_filepath` (str): Nová cesta k souboru.

- **`set_plan(plan: str) -> None`**
- **`plan_step_complete(message: str) -> None`**
- **`message_user(message: str, continue_working: bool) -> None`**
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
  - **Popis:** Vytvoří nový soubor a zapíše do něj zadaný obsah. Pokud soubor již existuje, bude přepsán.
  - **Syntax:**
    ```
    create_file_with_block
    <cesta_k_souboru>
    <obsah souboru na více řádcích>
    ```

- **`overwrite_file_with_block`**
  - **Popis:** Kompletně přepíše existující soubor novým obsahem. Jedná se o alias pro `create_file_with_block`.
  - **Syntax:**
    ```
    overwrite_file_with_block
    <cesta_k_souboru>
    <nový obsah souboru>
    ```

- **`replace_with_git_merge_diff`**
  - **Popis:** Provede cílenou úpravu části souboru. Vyhledá `search_block` a nahradí jej `replace_block`.
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