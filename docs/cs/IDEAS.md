# Zásobník nápadů pro Sophii

Tento dokument obsahuje zásobník nápadů, požadavků na funkce a cílů pro vývoj Sophie. Je inspirován původními myšlenkami z `roberts-notes.txt` a je udržován v souladu s vývojovými směrnicemi projektu.

---

## 1. Vylepšení UX/UI

### 1.1. Zlepšit zážitek v terminálu
*   **Cíl:** Zpřehlednit výstup v terminálu pro snazší používání a ladění.
*   **Úkoly:**
    *   Implementovat barevné logování pro odlišení různých typů zpráv (např. INFO, VAROVÁNÍ, CHYBA).
    *   Zavést strukturovaný, formátovaný výstup pro zobrazování plánů, volání nástrojů a výsledků pro zlepšení čitelnosti.

### 1.2. Vizualizace stavu jádra
*   **Cíl:** Poskytnout v reálném čase přehled o aktuálním stavu a činnosti jádra.
*   **Úkoly:**
    *   Navrhnout a implementovat "informační lištu" nebo stavový řádek, který zobrazuje aktuální fázi `consciousness_loop` (např. `LISTENING`, `PLANNING`, `EXECUTING`).
    *   Zajistit, aby byl tento stav viditelný jak v terminálovém rozhraní, tak ve webovém UI.

---

## 2. Vylepšení LLM a logiky

### 2.1. Optimalizovat logiku volání nástrojů
*   **Cíl:** Zvýšit spolehlivost a efektivitu volání nástrojů, aby se minimalizovaly opakované pokusy.
*   **Úkoly:**
    *   Provést důkladnou revizi prompt engineeringu s cílem zpřesnit instrukce, které LLM dostává pro generování plánů a argumentů nástrojů.
    *   Prozkoumat a implementovat robustnější mechanismy validace a oprav, které zachytí a opraví chyby před jejich spuštěním.

### 2.2. Implementovat LLM debugovací režim
*   **Cíl:** Vytvořit dozorovaný debugovací režim pro revizi a schvalování plánů generovaných AI.
*   **Úkoly:**
    *   Vyvinout mechanismus, který pozastaví jádro po fázi `PLANNING`.
    *   Umožnit lidskému vývojáři zkontrolovat, upravit nebo schválit vygenerovaný plán předtím, než přejde do fáze `EXECUTING`.

---

## 3. Přenos znalostí a dokumentace

### 3.1. Integrovat poznatky z "Julese"
*   **Cíl:** Přenést provozní znalosti a omezení objevené při práci s agentem "Jules" do Sophie.
*   **Úkoly:**
    *   Analyzovat `WORKLOG.md` a historii commitů s cílem identifikovat opakující se výzvy, úspěšné vzory a architektonická omezení.
    *   Kodifikovat tyto poznatky do nového dokumentu "Získané poznatky" v adresáři `docs/learned/`, který bude sloužit jako vodítko pro budoucí sebe-vývoj Sophie.

### 3.2. Udržovat detailní technickou dokumentaci
*   **Cíl:** Zajistit, aby veškerá technická dokumentace byla komplexní a aktuální, aby se předešlo ztrátě kontextu.
*   **Úkoly:**
    *   Zavést přísné pravidlo, že žádná nová funkce není považována za dokončenou, dokud není aktualizována její odpovídající dokumentace (`Příručka pro vývojáře`, `Technická architektura` atd.).
    *   Vytvořit "Manuál pro vývojáře", který poskytuje jasné, krok-za-krokem postupy pro běžné vývojové úkoly, aby pomohl jak lidským, tak AI vývojářům udržet se v obraze.
