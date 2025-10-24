# Roadmapa 02: Integrace Nástrojů

**Cíl Fáze:** Vybavit Sophii základní sadou nástrojů, které jí umožní interagovat s digitálním světem a upravovat své vlastní softwarové prostředí. Tato fáze přemění Sophii z čistě konverzační entity na funkčního agenta.

Detailní implementační plán pro tuto fázi bude vytvořen po úspěšném dokončení MVP.

---

### Klíčové Cíle:

1.  **Plugin pro Souborový Systém (`tool_file_system`):**
    *   **Účel:** Umožnit Sophii číst, zapisovat a vypisovat soubory a adresáře.
    *   **Základní Schopnosti:** `read_file`, `write_file`, `list_directory`.

2.  **Plugin pro Bash Shell (`tool_bash`):**
    *   **Účel:** Poskytnout Sophii schopnost spouštět libovolné příkazy v shellu v rámci jejího sandboxovaného prostředí.
    *   **Základní Schopnosti:** `execute_command`.
    *   **Kritická Poznámka:** Tento plugin musí mít robustní bezpečnostní mechanismy, včetně whitelisting/blacklisting příkazů a vynucování časových limitů.

3.  **Plugin pro Git Operace (`tool_git`):**
    *   **Účel:** Umožnit Sophii interagovat s jejím vlastním repozitářem se zdrojovým kódem.
    *   **Základní Schopnosti:** `git_clone`, `git_status`, `git_diff`, `git_commit`, `git_push`.

4.  **Plugin pro Vyhledávání na Webu (`tool_web_search`):**
    *   **Účel:** Poskytnout Sophii schopnost přistupovat k aktuálním informacím z internetu.
    *   **Základní Schopnosti:** `search_web`, `read_website_content`.

---

**Kritéria Úspěchu:** Sophia dokáže na základě instrukce naklonovat repozitář, přečíst z něj soubor, vyhledat na webu informace související s tímto souborem a následně zapsat shrnutí do nového souboru, a to vše bez lidského zásahu kromě počátečního příkazu.
