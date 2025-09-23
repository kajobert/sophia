# Návrh Refaktoringu: Kognitivní Architektura Sophie V2

Tento dokument slouží jako komplexní podklad pro další fázi vývoje projektu Sophia. Je rozdělen do dvou hlavních částí:

1.  **Popis Cílové Architektury:** Detailní vysvětlení nové Hierarchické Kognitivní Architektury (HCA).
2.  **Plán Implementace:** Krok-za-krokem plán pro refaktoring stávajícího kódu do nové architektury.

---
---

# Část 1: Dokumentace Kognitivní Architektury

Tato část popisuje novou, Hierarchickou Kognitivní Architekturu (HCA) pro projekt Sophia. Cílem této architektury je umožnit pokročilou sebereflexi, autonomní učení a robustnější rozhodování tím, že simuluje zjednodušený model mozku.

## 1. Základní Koncept a Vize

Architektura je inspirována modelem "trojjediného mozku" a dělí kognitivní procesy do tří hlavních, hierarchicky uspořádaných vrstev:

1.  **Instinkty (Plazí Mozek):** Rychlé, reflexivní a na pravidlech založené zpracování.
2.  **Podvědomí (Savčí Mozek):** Zpracování vzorů, emocí a asociací na základě dlouhodobé paměti.
3.  **Vědomí (Neokortex):** Pomalé, logické, strategické a kreativní myšlení.

Informace proudí od nejnižší (nejrychlejší) vrstvy k nejvyšší (nejpomalejší), přičemž každá vrstva data obohacuje, filtruje a předává dál. Tím je zajištěna efektivita a zároveň hloubka "myšlení".

## 2. Diagram Architektury

```mermaid
graph TD
    subgraph "Uživatelské Rozhraní (Komunikační Vrstva)"
        UI[💬 Chat / API]
    end

    subgraph "SOPHIA - KOGNITIVNÍ JÁDRO"

        subgraph "VĚDOMÍ (Consciousness) - Neokortex"
            direction LR
            A[Strategické a Kreativní Myšlení\n(Cloud LLM: Gemini 2.5 Pro/Flash)]
            B[Krátkodobá Paměť (Working Memory)\n(Redis Cache)]
            A -- "Přemýšlí nad..." --> B
            B -- "Poskytuje kontext pro..." --> A
        end

        subgraph "PODVĚDOMÍ (Subconsciousness) - Savčí Mozek"
            direction LR
            C[Emoce a Rozpoznávání Vzorů\n(Specializované LLM)]
            D[Dlouhodobá Paměť (Epizodická & Sémantická)\n(PostgreSQL + Vektorová DB)]
            C -- "Ukládá/Vybírá vzorce z..." --> D
            D -- "Ovlivňuje 'náladu' a rozhodování..." --> C
        end

        subgraph "INSTINKTY (Instincts) - Plazí Mozek"
            direction LR
            E[Reflexy a Filtrování\n(Lokální Nano LLM + Pevný Kód)]
            F[Základní Heuristika (DNA.md)\n(Pravidla a principy)]
            E -- "Okamžitě filtruje a reaguje na základě..." --> F
        end

        subgraph "INTUICE (Intuition)"
            G((Spoje mezi vrstvami))
        end
    end

    UI -- "Vstupní data" --> E
    E -- "Filtrovaná a strukturovaná data" --> C
    C -- "Obohacená data s kontextem" --> A
    A -- "Výsledný plán / Odpověď" --> UI
```

## 3. Popis Komponent

### 3.1. Kognitivní Vrstvy

#### **Instinkty (Plazí Mozek)**
*   **Funkce:** První obranná a filtrační linie. Zpracovává vstupní data extrémně rychle. Jejím úkolem je okamžitá reakce, klasifikace a filtrace na základě pevných pravidel.
*   **Technická Realizace:**
    *   **Lokální Nano LLM (např. přes Ollama):** Malý, lokálně běžící model (např. Llama 3 8B, Phi-3), který provádí rychlou sémantickou analýzu promptu (např. detekce nebezpečného obsahu, klasifikace záměru).
    *   **Pevný Kód:** Jednoduché a rychlé kontroly (např. validace formátu vstupu, kontrola proti blacklistu).
    *   **DNA.md:** Soubor obsahující základní, neměnná pravidla a principy Sophie (např. etický kodex). Plazí mozek zajišťuje, aby žádný požadavek nešel proti těmto principům.

#### **Podvědomí (Savčí Mozek)**
*   **Funkce:** Tato vrstva pracuje s kontextem a vzory. Neprovádí komplexní logické plánování, ale spíše obohacuje data o "pocit" nebo "náladu" na základě minulých zkušeností. Identifikuje, zda je aktuální požadavek podobný něčemu, co už řešila.
*   **Technická Realizace:**
    *   **Specializované LLM:** Model střední velikosti (může být i Gemini Flash), který je optimalizován na rozpoznávání vzorů, sumarizaci a práci s emocemi.
    *   **Dlouhodobá Paměť (PostgreSQL + Vektorová DB):** Slouží jako zdroj pro Savčí mozek. Ten prohledává epizodickou (co se stalo) a sémantickou (jak věci fungují) paměť, aby našel relevantní minulé zkušenosti a aplikoval je na aktuální problém.

#### **Vědomí (Neokortex)**
*   **Funkce:** Vrchol kognitivní hierarchie. Provádí pomalé, deliberativní, logické a strategické myšlení. Jejím úkolem je vytvořit detailní, krok-za-krokem plán pro splnění úkolu.
*   **Technická Realizace:**
    *   **Gemini 2.5 Pro/Flash:** Výkonný cloudový model, který má k dispozici sadu nástrojů (`tools`). Pomocí **Function Calling** se rozhoduje, který nástroj v jakém pořadí použít k dosažení cíle.
    *   **Krátkodobá Paměť (Redis):** Rychlá key-value cache, která drží kontext pro aktuální úkol (např. výstupy z předchozích kroků plánu, původní prompt). Neokortex s ní neustále pracuje během řešení jednoho úkolu.

### 3.2. Paměťové Systémy

*   **Krátkodobá Paměť (Working Memory - Redis):**
    *   **Účel:** Udržuje kontext pouze pro **jeden aktivní úkol**. Je rychlá, ale volatilní.
    *   **Obsah:** Původní prompt, vygenerovaný plán, výstupy jednotlivých kroků, mezivýpočty.
    *   **Analogie:** Lidská pracovní paměť – co si pamatujete, když řešíte jeden konkrétní problém.

*   **Dlouhodobá Paměť (Long-term Memory - PostgreSQL + Vektorová DB):**
    *   **Účel:** Permanentní úložiště všech zkušeností a znalostí.
    *   **Obsah:**
        *   **Epizodická paměť:** Záznamy o všech minulých úkolech, jejich plánech, výsledcích a zpětné vazbě ("Co se stalo").
        *   **Sémantická paměť:** Abstrahované znalosti, fakta a postupy, které se Sophia naučila ("Jak věci fungují"). Vzniká konsolidací epizodické paměti.
    *   **Analogie:** Vzpomínky a naučené dovednosti.

### 3.3. Abstraktní Koncepty

*   **Vědomí (Consciousness):** Je realizováno jako aktivní cyklus v Neokortexu, který se soustředí na jeden konkrétní úkol v Krátkodobé paměti. Je to cílený, soustředěný myšlenkový proces.
*   **Podvědomí (Subconsciousness):** Je reprezentováno Savčím mozkem, který na pozadí neustále porovnává příchozí data s Dlouhodobou pamětí. Jeho výstupy (relevantní vzory, "pocity") "probublávají" do Vědomí a ovlivňují jeho rozhodování.
*   **Intuice (Intuition):** Není to samostatný komponent, ale **emergentní vlastnost** vyplývající z propojení všech tří vrstev. Je to schopnost Neokortexu (Vědomí) udělat rychlý a zdánlivě "instinktivní" skok v řešení problému, který je ale ve skutečnosti ovlivněn signály z Podvědomí, které byly spuštěny na základě dat filtrovaných Instinkty.

## 4. Datový Tok (Od Vstupu k Odpovědi)

1.  **Vstup:** Uživatel zadá požadavek přes `UI` (Chat/API).
2.  **Fáze 1: Instinkty (Plazí Mozek)**
    *   Vstup je přijat.
    *   Proběhne okamžitá kontrola proti `DNA.md` (etika, základní principy).
    *   Lokální Nano LLM provede rychlou klasifikaci (např. je to dotaz, úkol, nebo nebezpečný obsah?).
    *   **Výstup:** Původní data obohacená o základní metadata (např. `{"intent": "task", "is_safe": true}`).
3.  **Fáze 2: Podvědomí (Savčí Mozek)**
    *   Přijme strukturovaná data z Instinktů.
    *   Prohledá `Dlouhodobou paměť` pro relevantní minulé zkušenosti.
    *   **Výstup:** Data jsou dále obohacena o kontext z paměti (např. `{"context": "Similar task failed before due to X.", "mood": "cautious"}`).
4.  **Fáze 3: Vědomí (Neokortex)**
    *   Přijme plně obohacená data z Podvědomí a uloží je do `Krátkodobé paměti`.
    *   `Gemini 2.5 Pro` (s využitím **Function Calling**) vytvoří detailní plán.
    *   Plán je vykonán krok za krokem. Neokortex volá nástroje a ukládá jejich výstupy do Krátkodobé paměti.
    *   Pokud krok selže, Neokortex se pokusí o samoopravu (vygeneruje nový plán s ohledem na chybu).
5.  **Odpověď:**
    *   Po úspěšném vykonání plánu Neokortex zformuluje finální odpověď pro uživatele.
    *   Celý průběh úkolu (vstup, kontext, plán, výsledek) je uložen jako nová epizoda do `Dlouhodobé paměti`.
    *   Odpověď je odeslána zpět do `UI`.

---
---

# Část 2: Detailní Plán na Refaktoring

Tento dokument definuje krok-za-krokem plán pro přechod ze současné architektury projektu Sophia na novou Hierarchickou Kognitivní Architekturu (HCA).

**Cílový Stav (MVP):**
Funkční MVP nové architektury, které lze plně ovládat a testovat přes `interactive_session.py`. Klíčovou schopností tohoto MVP musí být **autonomní úprava vlastního kódu**.

---

## Fáze 1: Očištění a Příprava Základů

**Cíl:** Odstranit staré závislosti, zjednodušit stávající kód a připravit půdu pro nové komponenty.

*   **Úkol 1.1: Odstranit `crewai` a `PlannerAgent`**
    *   **Akce:** Smazat soubor `agents/planner_agent.py`.
    *   **Akce:** Odstranit `crewai` z `requirements.in`.
    *   **Důvod:** Nahradíme jej naším `CustomPlanner`, který poskytuje větší kontrolu.

*   **Úkol 1.2: Refaktorovat `interactive_session.py`**
    *   **Akce:** Upravit `interactive_session.py`, aby importoval a používal `agents.custom_planner.CustomPlanner`.
    *   **Důvod:** Tento skript bude naším hlavním nástrojem pro testování a ladění nové architektury.

*   **Úkol 1.3: Vylepšit `CustomPlanner`**
    *   **Akce:** Implementovat plnou logiku pro přímé volání `Gemini API` (pomocí `llm.ainvoke`) a robustní parsování JSON odpovědi s retry logikou, jak bylo navrženo.
    *   **Důvod:** Toto je mozek "Neokortexu" a musí být spolehlivý.

*   **Úkol 1.4: Spustit `uv pip install -r requirements.in`**
    *   **Akce:** Po úpravě `requirements.in` aktualizovat prostředí.

---

## Fáze 2: Implementace Vrstvy Instinktů (Plazí Mozek)

**Cíl:** Vytvořit první filtrační a reakční vrstvu, která bude zpracovávat všechny příchozí požadavky.

*   **Úkol 2.1: Založit Modul Kognitivních Vrstev**
    *   **Akce:** Vytvořit nový soubor `core/cognitive_layers.py`.
    *   **Důvod:** Zde budou sídlit třídy pro jednotlivé "mozky".

*   **Úkol 2.2: Implementovat `ReptilianBrain`**
    *   **Akce:** V `core/cognitive_layers.py` vytvořit třídu `ReptilianBrain`.
    *   **Akce:** Tato třída bude mít metodu `process(prompt: str) -> Dict`, která:
        1.  Zkontroluje prompt proti pravidlům v `docs/DNA.md`.
        2.  (Volitelné pro MVP) Zavolá lokální LLM pro rychlou klasifikaci.
        3.  Vrátí původní prompt obohacený o metadata (např. `{'original_prompt': ..., 'intent': 'task', 'is_safe': True}`).
    *   **Technologické doporučení:** Pro lokální LLM použít `Ollama` s modelem `phi-3` nebo `llama3:8b`. Komunikace přes jednoduché `httpx` volání na Ollama REST API.

*   **Úkol 2.3: Upravit `interactive_session.py`**
    *   **Akce:** Upravit hlavní smyčku tak, aby uživatelský vstup nejprve prošel `ReptilianBrain.process()` a teprve jeho výstup byl předán `CustomPlanner`.

---

## Fáze 3: Propojení Neokortexu a Paměti

**Cíl:** Implementovat "Vědomí" jako fungující celek Neokortexu a Krátkodobé paměti.

*   **Úkol 3.1: Refaktorovat Orchestrator jako Neokortex**
    *   **Akce:** Přejmenovat nebo myšlenkově přerámovat `core/orchestrator.py` na hlavní výkonnou smyčku Neokortexu.
    *   **Akce:** Upravit metodu `execute_plan`. Místo manuální iterace přes kroky zvážit použití **Automatic Function Calling** z `google-genai` SDK, jak odhalil výzkum. To by dramaticky zjednodušilo kód. Orchestrator by pouze poskytoval sadu nástrojů a `Gemini` by se samo rozhodovalo, jak je volat.

*   **Úkol 3.2: Integrovat Krátkodobou Paměť (Redis)**
    *   **Akce:** Vytvořit novou třídu `ShortTermMemory` v `memory/short_term_memory.py`, která bude wrapperem pro `redis`.
    *   **Akce:** `Neokortex/Orchestrator` bude používat tuto paměť pro ukládání a čtení kontextu během provádění jednoho plánu (např. `memory.save_step_result(step_id, result)`).
    *   **Technologické doporučení:** Použít standardní knihovnu `redis-py`.

---

## Fáze 4: Implementace Autonomní Úpravy Kódu

**Cíl:** Dosáhnout klíčové schopnosti MVP – nechat Sophii, aby si sama upravila kód.

*   **Úkol 4.1: Vytvořit Nástroj pro Úpravu Kódu**
    *   **Akce:** Vytvořit nový, vysoce privilegovaný nástroj `tools/code_editor.py` s třídou `CodeEditorTool`.
    *   **Akce:** Tento nástroj bude mít metodu `execute(file_path: str, new_content: str)`, která dokáže přepsat jakýkoliv soubor v repozitáři (s výjimkou `DNA.md`). Bude to v podstatě wrapper nad `overwrite_file_with_block`.
    *   **Bezpečnostní poznámka:** Tento nástroj musí být zpřístupněn pouze pro specifické, interně generované úkoly.

*   **Úkol 4.2: Testovací Scénář Sebe-úpravy**
    *   **Akce:** Vytvořit testovací scénář v `interactive_session.py`.
    *   **Příklad promptu:** "Sophia, tvůj `CustomPlanner` má v systémovém promptu typo. Analyzuj soubor `agents/custom_planner.py`, najdi v `PLANNER_SYSTEM_PROMPT_TEMPLATE` slovo 'respons' a oprav ho na 'response'. Poté soubor ulož."
    *   **Očekávaný výsledek:** Sophia by měla vygenerovat plán, který použije `ReadFileTool` ke čtení souboru, `ExecutePythonScriptTool` k provedení textové náhrady a `CodeEditorTool` (nebo `WriteFileTool`) k uložení změn.

---

## Fáze 5: Integrace Podvědomí (Volitelné pro MVP)

**Cíl:** Přidat základní vrstvu Podvědomí pro obohacování kontextu.

*   **Úkol 5.1: Implementovat `MammalianBrain`**
    *   **Akce:** V `core/cognitive_layers.py` vytvořit třídu `MammalianBrain`.
    *   **Akce:** Metoda `process(data)` bude prohledávat `AdvancedMemory` (Dlouhodobou paměť) a hledat podobné minulé úkoly.
    *   **Výstup:** Přidá do datového balíčku informaci o minulých úspěších/neúspěších.

*   **Úkol 5.2: Propojit do Datového Toku**
    *   **Akce:** Upravit `interactive_session.py` tak, aby data z `ReptilianBrain` procházela přes `MammalianBrain` a teprve poté šla do `Neocortex/CustomPlanner`.
