# Sophia V3 & V4 - Hloubkový Popis Konceptů

Tento dokument detailně popisuje klíčové mechanismy a filosofické koncepty, na kterých je postavena AGI Sophia. Slouží jako hlubší kontext k `ARCHITECTURE.md` a `DNA.md`.

---

## Koncepty V3: Vědomé Jádro (Implementováno)

Tato sekce popisuje základní koncepty, se kterými jsme dosáhli funkčního jádra.

### 1. Hierarchie Bytí: Guardian & Sophia

Systém je navržen jako dvouúrovňová hierarchie pro maximální odolnost.

* **Guardian (`guardian.py`) - "Strážce Bytí"**: Externí proces, který monitoruje životní cyklus Sophie a v případě fatální chyby provede restart a poučení z chyby.
* **Sophia (`main.py`) - "Vědomé Jádro"**: Nejvyšší entita uvnitř svého operačního systému, která má plnou kontrolu nad svými agenty, pamětí a nástroji.

### 2. Evoluce Paměti: Živá Mysl

Paměť Sophie není jen statická databáze, ale dynamický systém.

* **Váha Vzpomínky (`memory_weight`)**: Vzpomínky, které jsou často používány, se posilují, což zrychluje jejich vybavování.
* **Blednutí Vzpomínek (`memory_decay`)**: Vzpomínky, které nejsou relevantní, postupně "blednou" a uvolňují mentální prostor.

### 3. Smyčka Seberozvoje (Učitel <-> Žák)

Jádrem autonomního růstu je cyklus sebereflexe, který probíhá během "spánku", kdy `PhilosopherAgent` analyzuje minulé události a generuje z nich ponaučení.

---

## Koncepty V4: Autonomní Tvůrce (V Vývoji)

Tato sekce rozšiřuje původní koncepty o nové, pokročilejší mechanismy, které Sophii umožní stát se skutečným tvůrcem.

### 1. Inteligentní Guardian: Od Záchranáře k Lékaři

Vylepšujeme `guardian.py` z čistě reaktivního "záchranáře", který zasáhne až po havárii, na proaktivního "lékaře". Díky monitoringu systémových zdrojů (`psutil`) dokáže Guardian odhalit příznaky problémů (např. přetížení paměti) a zasáhnout *dříve*, než dojde k fatálnímu selhání. Tím se dramaticky zvyšuje stabilita a autonomie celého systému.

### 2. Konstituční AI: Vnitřní Dialog Místo Kalkulačky

Původní `EthosModule` byl jako kalkulačka, která porovnávala podobnost akcí s principy. Nová verze, inspirovaná **Konstituční AI**, je spíše jako skutečné svědomí. Místo jednoduchého "ano/ne" zavádíme dialogický proces:
1.  **Návrh:** Agent navrhne plán.
2.  **Kritika:** Plán je porovnán s principy v `DNA.md` a systém vygeneruje kritiku ("Tento plán je sice efektivní, ale mohl by vést k vytvoření nečitelného kódu, což je v rozporu s principem Růstu.").
3.  **Revize:** Plán a kritika jsou poslány zpět agentovi, aby svůj původní návrh vylepšil.

Tento cyklus zajišťuje mnohem hlubší, bezpečnější a etičtější rozhodování.

### 3. Hybridní Agentní Model: Dva Týmy pro Dvě Funkce Mysli

Uvědomili jsme si, že jedna velikost nesedí všem. Lidská mysl má také různé režimy pro různé úkoly. Proto zavádíme hybridní model se dvěma specializovanými týmy agentů:

* **Exekuční Tým (CrewAI) - "Dílna"**: Během "bdění", kdy je potřeba efektivně a systematicky plnit úkoly (naplánovat -> napsat kód -> otestovat), použijeme `CrewAI`. Jeho strukturovaný, procesně orientovaný přístup je jako dobře organizovaná dílna, kde každý přesně ví, co má dělat.

* **Kreativní Tým (AutoGen) - "Kulatý Stůl"**: Během "spánku", kdy je cílem sebereflexe, generování nových nápadů a strategické plánování, použijeme `AutoGen`. Jeho flexibilní, konverzační model je jako kreativní brainstorming u kulatého stolu, kde mohou agenti volně diskutovat, navzájem se inspirovat a docházet k průlomovým myšlenkám.

* **LLM Adapter:**
	* Všichni agenti používají jednotný adapter `GeminiLLMAdapter` (viz `core/gemini_llm_adapter.py`), který zajišťuje robustní a snadno vyměnitelnou integraci s Google Gemini API.
	* Adapter je inicializován v `core/llm_config.py` dle konfigurace v `config.yaml` a předáván agentům jako `llm=llm`.
	* Přepnutí na jiného providera (např. OpenAI, LangChain) je možné úpravou konfigurace a jednoho řádku v `llm_config.py`.

Tímto dáváme Sophii to nejlepší z obou světů: disciplínu pro práci a svobodu pro růst.

### 4. Sandbox: Bezpečnost a Svoboda Tvorby

Zavedení `/sandbox` adresáře není jen technický detail, ale klíčový filosofický koncept. Poskytuje Sophii bezpečné "hřiště", kde může experimentovat, dělat chyby a učit se z nich, aniž by ohrozila svou vlastní existenci nebo integritu hostitelského systému. Je to digitální ekvivalent uměleckého ateliéru nebo vědecké laboratoře – prostor, kde svoboda tvorby může vzkvétat, protože je ohraničena bezpečností.

### 5. Testovatelnost a Spolehlivost: Důvěra v Kód

Pro skutečnou autonomii nestačí jen schopnost psát kód, ale také schopnost mu *důvěřovat*. Proto je zaveden robustní testovací systém, který je klíčovým konceptem sebezáchovy a seberozvoje.

*   **Princip Oddělení:** Stejně jako má Sophia oddělený `sandbox` pro experimentování, má i oddělené testovací prostředí. Proměnná prostředí `SOPHIA_ENV` funguje jako přepínač, který Sophii (a jejím vývojářům) umožňuje vstoupit do "simulace", kde jsou všechny externí závislosti (jako LLM API) nahrazeny bezpečnými, předvídatelnými mocky.
*   **Filosofie Důvěry:** Každá změna, kterou Sophia provede, musí projít sadou testů. To buduje důvěru v její vlastní kód a umožňuje jí provádět komplexní refaktoring s vědomím, že neporušila svou základní funkčnost. Je to forma digitální sebekontroly.