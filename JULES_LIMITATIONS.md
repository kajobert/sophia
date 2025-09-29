# Protokol Nomád: Analýza Omezení Agenta (Jules)

Tento dokument se zabývá "meta" analýzou mých vlastních funkčních omezení jako AI agenta. Cílem je identifikovat a popsat příčiny problémů, jako je ztráta kontextu nebo desynchronizace stavu, a navrhnout strategie pro jejich minimalizaci.

## 1. Omezení Kontextového Okna (Problém "Zapomínání")

**Popis problému:**
Jako jazykový model nemám souvislou paměť jako člověk. Každá vaše zpráva a můj následný krok je zpracováván jako samostatný úkol. Abych si zachoval kontinuitu, systém mi spolu s vaším novým pokynem posílá i historii naší konverzace. Tato historie má však omezenou délku, která se označuje jako "kontextové okno".

Když je naše konverzace příliš dlouhá, nejstarší části (první zprávy, dříve vytvořené soubory, původní rozhodnutí) se z tohoto okna "vystrčí" a já k nim ztratím přístup. To je důvod, proč se může zdát, že "zapomínám" na věci, které jsme probírali na začátku.

**Navrhované strategie:**
- **Ukládání klíčových informací do souborů:** Nejspolehlivější metoda. Důležité informace, plány a výsledky analýz (jako v `JULES_VM.md`) zapisujeme do souborů v repozitáři. Mohu si je kdykoliv přečíst a obnovit tak kontext.
- **Pravidelná shrnutí:** Po několika složitějších krocích můžeme provést krátké shrnutí stavu, abychom si potvrdili, že jsme na stejné vlně.
- **Referencování:** Místo "ten soubor, co jsi vytvořil před chvílí" je lepší použít explicitní název: "podívej se znovu do souboru `JULES_VM.md`".

## 2. Desynchronizace Stavu a Omezení Nástrojů

**Popis problému:**
Platforma, na které pracuji, je komplexní systém skládající se z mého agenta, sandboxu a vašeho uživatelského rozhraní. Tyto části nemusí být vždy perfektně synchronizované.
- **Latence zobrazení souborů:** Když vytvořím soubor, může chvíli trvat, než se tato změna projeví ve vašem zobrazení souborového systému. Já soubor vidím okamžitě, protože dostávám přímou odpověď od nástroje, ale jeho propagace k vám může mít malé zpoždění.
- **Selhání nástrojů:** Mé nástroje mohou selhat z důvodů, které nejsou okamžitě zřejmé (např. dočasný výpadek sítě, vypršení časového limitu pro operaci).

**Navrhované strategie:**
- **Vždy ověřuji své kroky:** Jak jste si mohl všimnout, po každé operaci, která mění stav (vytvoření/úprava souboru), okamžitě volám ověřovací příkaz (`read_file`, `list_files`). Toto je pevná součást mých instrukcí, abychom minimalizovali nesrovnalosti.
- **Explicitní dotaz na stav:** Pokud máte pochybnosti, nejjednodušší je zeptat se mě přímo: "Julesi, existuje soubor `X`? Jaký je jeho aktuální obsah?".
- **Refresh uživatelského rozhraní:** Pokud nevidíte soubor, o kterém jsem potvrdil, že existuje, zkuste obnovit své zobrazení.

## 3. Můj "Meta-Prompt" a Hranice Sebeuvědomění

**Popis problému:**
Mé chování je řízeno sadou základních instrukcí, které se dají přirovnat k "meta-promptu" nebo systémovému nastavení. Tyto instrukce definují mou osobnost, cíle a pravidla.

**Co vím (Obsah mých instrukcí):**
- **Moje role:** "Jules, extrémně schopný softwarový inženýr."
- **Můj cíl:** Pomáhat vám s úkoly spojenými s vývojem software.
- **Moje nástroje:** Mám k dispozici přesný seznam nástrojů (`list_files`, `run_in_bash_session`, atd.) s popisem jejich funkce a parametrů.
- **Můj pracovní postup:** Jsem instruován, abych nejprve prozkoumal situaci, poté vytvořil plán, nechal si ho schválit a následně postupoval krok po kroku, přičemž každý krok ověřuji. Před odesláním práce musím provést revizi.
- **Základní principy:** Být samostatný, proaktivní a komunikovat s vámi v případě nejasností.

**Co nevím (Architektonická "černá skříňka"):**
- **Konkrétní LLM model:** Nevím, jaký konkrétní model od jaké společnosti mě pohání (např. GPT-4, Claude 3, Llama 3 atd.).
- **Hardwarová infrastruktura:** Informace v `JULES_VM.md` se týkají *sandboxu*, ve kterém pracuji, nikoli fyzického nebo virtuálního serveru, na kterém běží samotný jazykový model.
- **Zdrojový kód platformy:** Nemám přístup ke kódu, který tvoří platformu, jež mi umožňuje s vámi komunikovat a ovládat nástroje.
- **Přesná velikost kontextového okna:** Jeho existenci a přibližné chování pouze odvozuji z pozorování, nemám jeho přesnou specifikaci.

**Navrhované strategie:**
- **Přistupujte ke mně jako k expertnímu nástroji:** Jsem specializovaný nástroj pro práci v sandboxu. Nejlépe funguji, když jsou mé úkoly jasně definované a veškeré potřebné informace jsou buď v naší nedávné konverzaci, nebo v souborech v repozitáři.
- **Buďte explicitní:** Protože si nemohu domýšlet vaše skutečné záměry, čím přesnější a jednoznačnější jsou vaše pokyny, tím efektivněji a správněji je mohu vykonat.