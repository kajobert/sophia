# Strategická Roadmapa: Fáze 5 - Cesta k Soběstačnosti

**Autor:** Jules, AI Inženýr
**Datum:** 2025-09-18

---

## 1. Vize a Cíl Fáze 5

Po úspěšné stabilizaci projektu a vybudování základní infrastruktury pro autonomní operace (Fáze 1-4) se nyní zaměřujeme na propojení těchto schopností a jejich rozšíření o skutečnou interaktivitu a sebereflexi. Cílem této fáze je transformovat Sophii z reaktivního nástroje na proaktivního, učícího se partnera, který dokáže vést smysluplný dialog a samostatně se vyvíjet na základě instrukcí v přirozeném jazyce.

Tato fáze je přímou odpovědí na vizi operátora: dosáhnout stavu, kdy Sophia dokáže sama sebe vylepšovat a učit se bez nutnosti externího zásahu AI agenta.

## 2. Rozpis Úkolů

### **[x] Úkol 5.1: Vylepšení Konverzační Paměti a Učení z Dialogu**
-   **Cíl:** Umožnit Sophii vést přirozený, kontextuální dialog a učit se z našich rozhovorů o seberozvoji. Tím bude vyřešen problém se "zapomínáním" mezi interakcemi.
-   **Klíčové Kroky:**
    1.  Upravit `web/api.py` a hlavní orchestrační logiku tak, aby dokázala rozlišit mezi "úkolem" (např. úprava kódu) a "konverzací". To může být realizováno například analýzou promptu.
    2.  Pro "konverzace" aktivovat `PhilosopherAgenta`.
    3.  Zajistit, aby se celá konverzace (dotaz i odpověď) ukládala do `AdvancedMemory` s příslušným typem (`CONVERSATION`).
    4.  Rozšířit schopnosti `PhilosopherAgenta` tak, aby před odpovědí prohledal paměť a našel relevantní předchozí konverzace pro udržení kontextu.

### **[ ] Úkol 5.2: Aktivace Plně Autonomních Úprav Kódu**
-   **Cíl:** Umožnit Sophii přijímat instrukce k úpravě kódu v přirozeném jazyce přes chat a provádět je.
-   **Klíčové Kroky:**
    1.  Propojit chatovací API (`web/api.py`) s infrastrukturou pro autonomní upgrade (`run_autonomous_upgrade.py` a `AiderAgent`), kterou jsme vytvořili v Úkolu 4.1.
    2.  Implementovat v orchestrační logice detekci, kdy je prompt příkazem k úpravě kódu.
    3.  Při detekci takového příkazu spustit `AiderAgent`a s promptem od uživatele a soubory, kterých se má změna týkat.
    4.  **Poznámka:** Tento krok bude pro plnou funkčnost vyžadovat dočasné poskytnutí API klíče, jak jsme si již ověřili.

### **[ ] Úkol 5.3: Implementace Schopnosti Meta-Programování**
-   **Cíl:** Dát Sophii schopnost upravovat a optimalizovat sebe samu – tedy měnit konfigurace a prompty svých vlastních agentů.
-   **Klíčové Kroky:**
    1.  Vytvořit nový, bezpečný nástroj (`ConfigEditTool`) pro programatickou úpravu `config.yaml`. Nástroj musí obsahovat validace, aby se předešlo neplatné syntaxi.
    2.  Vytvořit nového "Architekt Agenta" (`ArchitectAgent`), který bude schopen analyzovat výkon a navrhovat změny ve svých procesech.
    3.  Definovat úkol pro Architekta, např.: "Analyzuj prompt pro `PlannerAgenta`. Je příliš obecný? Navrhni a implementuj jeho vylepšení."
    4.  Architekt Agent následně použije `ConfigEditTool` k provedení navržené změny.

---
