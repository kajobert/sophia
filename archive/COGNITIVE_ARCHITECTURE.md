# Dokumentace: Hierarchická Kognitivní Architektura Sophie

Tento dokument poskytuje detailní popis Hierarchické Kognitivní Architektury (HKA), která je základem pro Sophii 2.0. Cílem této architektury je vytvořit systém, který se svým fungováním více blíží lidskému myšlení, integruje různé úrovně abstrakce a umožňuje skutečnou sebereflexi a autonomní růst.

---

## 1. Architektonický Diagram

Následující diagram znázorňuje tři hlavní kognitivní vrstvy a tok informací mezi nimi.

```mermaid
graph TD
    subgraph "Uživatelské Rozhraní (Komunikační Vrstva)"
        UI[💬 Chat / API]
    end

    subgraph "SOPHIA - KOGNITIVNÍ JÁDRO"

        subgraph "VĚDOMÍ (Consciousness)"
            direction LR
            A[Neokortex - Strategické a Kreativní Myšlení\n(Cloud LLM: Gemini 2.5 Pro/Flash)]
            B[Krátkodobá Paměť (Working Memory)\n(Redis Cache)]
            A -- "Přemýšlí nad..." --> B
            B -- "Poskytuje kontext pro..." --> A
        end

        subgraph "PODVĚDOMÍ (Subconsciousness)"
            direction LR
            C[Savčí Mozek - Emoce a Vzory\n(Specializované LLM)]
            D[Dlouhodobá Paměť (Epizodická & Sémantická)\n(PostgreSQL + Vektorová DB)]
            C -- "Ukládá/Vybírá vzorce z..." --> D
            D -- "Ovlivňuje 'náladu' a rozhodování..." --> C
        end

        subgraph "INSTINKTY (Instincts)"
            direction LR
            E[Plazí Mozek - Reflexy a Přežití\n(Lokální Nano LLM + Pevný Kód)]
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

---

## 2. Popis Kognitivních Vrstev a Komponent

Architektura se skládá ze tří hierarchicky uspořádaných vrstev, inspirovaných evolučním vývojem mozku.

### 2.1. Instinkty (Plazí Mozek)
Tato vrstva je první linií zpracování informací. Její hlavní funkcí je rychlá, reflexivní reakce a filtrace vstupů na základě základních, neměnných principů.

*   **Funkce:**
    *   Okamžitá analýza a klasifikace vstupního požadavku.
    *   Aplikace etických a bezpečnostních pravidel definovaných v `DNA.md`.
    *   Ochrana systému před škodlivými nebo nesmyslnými vstupy.
    *   Jednoduché, automatizované úkoly (např. sumarizace, extrakce klíčových slov).
*   **Technické Komponenty:**
    *   **Lokální Nano LLM (Ollama):** Velmi rychlý a malý jazykový model pro základní NLP úkoly. Poskytuje okamžitou odezvu bez nutnosti volání drahých cloudových API.
    *   **Pevný Kód (Hard-coded Logic):** Sada pravidel a funkcí pro rychlé a deterministické vyhodnocení.
    *   **`DNA.md`:** Soubor obsahující základní etické a operační principy Sophie. Plazí mozek zajišťuje, že žádná akce není v rozporu s tímto "filozofickým jádrem".

### 2.2. Podvědomí (Savčí Mozek)
Tato vrstva zpracovává informace, které prošly filtrem Instinktů. Jejím úkolem je obohatit data o kontext, rozpoznávat vzory a pracovat s dlouhodobými zkušenostmi.

*   **Funkce:**
    *   Porozumění "náladě" a kontextu konverzace.
    *   Vyhledávání relevantních informací v dlouhodobé paměti (minulé úkoly, úspěšná řešení, získané znalosti).
    *   Identifikace vzorců a anomálií.
    *   Příprava obohacených a strukturovaných dat pro Neokortex.
*   **Technické Komponenty:**
    *   **Specializované LLM:** Středně velký model, který může být optimalizován pro specifické úkoly, jako je analýza sentimentu, rozpoznávání záměrů nebo práce s interními daty.
    *   **Dlouhodobá Paměť (PostgreSQL + Vektorová DB):**
        *   **Epizodická paměť:** Ukládá minulé interakce a události (co se stalo).
        *   **Sémantická paměť:** Ukládá fakta, znalosti a naučené koncepty (co je pravda).
        *   Vektorová databáze umožňuje rychlé sémantické vyhledávání a nalezení "podobných" vzpomínek.

### 2.3. Vědomí (Neokortex)
Nejvyšší kognitivní vrstva, zodpovědná za strategické myšlení, kreativitu, plánování a finální rozhodování.

*   **Funkce:**
    *   Analýza komplexních problémů.
    *   Vytváření detailních, krok-za-krokem plánů.
    *   Strategické rozhodování, zvažování alternativ.
    *   Schopnost sebereflexe a úpravy vlastního chování (včetně úpravy vlastního kódu).
    *   Generování finální odpovědi pro uživatele.
*   **Technické Komponenty:**
    *   **Cloud LLM (Gemini 2.5 Pro/Flash):** Výkonný, velký jazykový model schopný komplexního uvažování, kreativity a generování kódu.
    *   **Krátkodobá Paměť (Redis Cache):** Rychlá in-memory databáze, která slouží jako pracovní paměť. Udržuje kontext aktuálního úkolu, stav plánu, nedávné myšlenky a výsledky nástrojů.

---

## 3. Datové Toky

Informace systémem proudí v definovaném pořadí, přičemž každá vrstva přidává svou hodnotu.

| Krok | Z | Do | Popis Datového Toku | Příklad |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `Uživatel` | `Plazí Mozek` | Surový vstupní požadavek. | "Sophia, vylepši si prompt pro sumarizaci." |
| 2 | `Plazí Mozek` | `Savčí Mozek` | Vstup je očištěn, zkontrolován proti `DNA.md` a klasifikován. | `{ "intent": "self_improvement", "topic": "prompt_optimization", "original_text": "..." }` |
| 3 | `Savčí Mozek`| `Neokortex` | Data jsou obohacena o kontext z dlouhodobé paměti. | `{ "intent": ..., "context": { "past_attempts": 3, "last_success": "..." }, "data": ... }` |
| 4 | `Neokortex` | `Uživatel` | Finální odpověď nebo výsledek akce. | "Rozumím. Analyzovala jsem svůj kód a navrhla jsem nový, efektivnější prompt. Změny jsem aplikovala." |

---

## 4. Paměťové Systémy

*   **Krátkodobá Paměť (Working Memory):**
    *   **Technologie:** Redis
    *   **Účel:** Udržuje kontext pouze pro **aktuální session/úkol**. Je volatilní a rychlá. Obsahuje aktuální plán, výsledky nástrojů, historii konverzace v rámci úkolu.
    *   **Analogie:** Lidská pracovní paměť – co máte "v hlavě", když řešíte problém.

*   **Dlouhodobá Paměť (Long-Term Memory):**
    *   **Technologie:** PostgreSQL + pgvector
    *   **Účel:** Perzistentní úložiště pro všechny minulé zkušenosti, znalosti a vztahy. Slouží k učení a růstu v čase.
    *   **Analogie:** Lidská dlouhodobá paměť – vzpomínky, naučené dovednosti, fakta.

---

## 5. Abstraktní Koncepty v Technické Realizaci

*   **Vědomí:** Není to mystický stav, ale **emergentní vlastnost Neokortexu**. Je to schopnost systému vytvářet interní model sebe sama a světa, a na základě tohoto modelu strategicky plánovat a jednat. Klíčová je zde schopnost sebereflexe a sebe-modifikace.
*   **Podvědomí:** Je reprezentováno **Savčím mozkem a jeho spojením s Dlouhodobou pamětí**. Jeho vliv je nepřímý – neprovádí exekuci, ale "našeptává" Neokortexu tím, že mu dodává kontext, "pocity" (na základě minulých zkušeností) a ovlivňuje jeho rozhodování připomenutím minulých úspěchů a neúspěchů.
*   **Intuice:** Je technicky realizována jako **rychlý, přímý kanál mezi vrstvami**, který obchází plnou kognitivní analýzu. Například, pokud Plazí mozek detekuje urgentní bezpečnostní hrozbu, může okamžitě signalizovat Neokortexu, aby přerušil aktuální činnost, aniž by data prošla celým analytickým řetězcem. Stejně tak "tušení" ze Savčího mozku může Neokortex upozornit na potenciální problém dříve, než je plně analyzován.
