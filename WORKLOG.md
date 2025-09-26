# Pracovní Deník (Worklog) Projektu Sophia

Tento dokument slouží jako centrální a chronologický záznam o veškeré práci vykonané na tomto projektu. Každý vývojář (včetně AI agentů) je povinen sem po dokončení významného úkolu přidat záznam.

## Formát Záznamu

Každý záznam musí dodržovat následující Markdown strukturu pro zajištění konzistence a čitelnosti.

```markdown
---
**Datum**: YYYY-MM-DD
**Autor**: [Jméno autora nebo kódové označení agenta]
**Ticket/Task**: [Odkaz na relevantní ticket, úkol nebo PR]

### Téma: Stručný a výstižný název vykonané práce.

**Popis Práce:**
- Detailní popis toho, co bylo uděláno.
- Jaké soubory byly změněny, vytvořeny nebo smazány.
- Klíčová rozhodnutí, která byla učiněna.

**Důvod a Kontext:**
- Proč byla tato změna nutná?
- Jaký problém řeší nebo jakou hodnotu přináší?
- Jaké alternativy byly zvažovány a proč byly zamítnuty?

**Narazené Problémy a Řešení:**
- Popis jakýchkoli problémů, na které se narazilo během práce.
- Jak byly tyto problémy vyřešeny? (Toto je klíčové pro budoucí učení).

**Dopad na Projekt:**
- Jak tato změna ovlivňuje zbytek projektu?
- Jsou zde nějaké návazné kroky, které je třeba udělat?
- Co by měli ostatní vývojáři vědět?
---
```

---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Zavedení nových principů spolupráce.

### Téma: Založení WORKLOG.md a formalizace nových pravidel.

**Popis Práce:**
- Vytvořil jsem tento soubor (`WORKLOG.md`) jako centrální deník projektu.
- Definoval jsem standardizovaný formát pro všechny budoucí záznamy.
- Tento záznam je prvním v historii projektu a dokumentuje zavedení nových, klíčových principů pro naši spolupráci.

**Důvod a Kontext:**
- Bylo nutné formalizovat a centralizovat záznamy o práci, aby se zvýšila transparentnost a usnadnilo navazování na práci pro všechny členy týmu.
- Tento krok je součástí širší iniciativy pro vytvoření profesionálního a udržitelného vývojového workflow.

**Narazené Problémy a Řešení:**
- Žádné problémy při zakládání tohoto dokumentu.

**Dopad na Projekt:**
- Všichni vývojáři (včetně mě) jsou nyní povinni po dokončení práce přidat záznam do tohoto souboru.
- Zvyšuje se tím dohledatelnost a sdílení znalostí v rámci projektu.
---
---
**Datum**: 2025-09-25
**Autor**: Jules (Nomad)
**Ticket/Task**: Architektonická Transformace na Asynchronní MCP

### Téma: Refaktoring na terminálově-orientovanou, asynchronní MCP architekturu.

**Popis Práce:**
- Proveden kompletní reset projektu po několika neúspěšných pokusech o refaktoring, které odhalily zásadní nekonzistence v testovacím prostředí a nepochopení původního cíle.
- Implementována nová, jednodušší a robustnější strategie postupného vývoje.
- **Fáze 1 (Zjednodušení):** Projekt byl vyčištěn od nepotřebných souborů staré architektury (FastAPI, Neocortex, atd.).
- **Fáze 2 (Async MCP Servery):** Nástroje (`file_system`, `shell`) byly refaktorovány do samostatných, plně asynchronních MCP serverů komunikujících přes `stdin`/`stdout`.
- **Fáze 3 (Async Orchestrator):** Byla vytvořena nová, plně asynchronní třída `JulesOrchestrator`, která funguje jako MCP Host a spravuje životní cyklus serverů pomocí `asyncio.create_subprocess_exec`.
- **Fáze 4 (Integrace):** Vstupní bod `interactive_session.py` byl přepsán tak, aby správně spouštěl a používal novou asynchronní architekturu.

**Důvod a Kontext:**
- Původní cíl byl refaktorovat projekt na MCP architekturu, ale první pokusy selhaly kvůli špatné interpretaci úkolu a problémům s prostředím.
- Po konzultaci s uživatelem byl cíl upřesněn: nahradit stávající komplexní architekturu novou, jednodušší a plně asynchronní architekturou zaměřenou na maximální výkon a flexibilitu v terminálovém prostředí.

**Narazené Problémy a Řešení:**
- **Problém:** Nekonzistentní pracovní adresář nástroje `run_in_bash_session`, který způsoboval selhání příkazů.
- **Řešení:** Problém byl diagnostikován a vyřešen používáním absolutních cest pro kritické operace a opravou "zaseknutého" stavu shellu.
- **Problém:** Složitost a křehkost původních pokusů o refaktoring.
- **Řešení:** Přechod na nový, bezpečnější plán, který začal vytvořením jednoduchého monolitického skriptu a jeho postupným, ověřovaným refaktoringem.

**Dopad na Projekt:**
- Projekt má nyní čistou, moderní a plně asynchronní architekturu, která je robustní a snadno rozšiřitelná.
- Agent je nyní schopen efektivně spravovat a komunikovat s externími nástroji (MCP servery) bez blokování.
- Projekt je připraven na další rozvoj a implementaci pokročilejších schopností.
---
---
**Datum**: 2025-09-26
**Autor**: Jules (Nomad)
**Ticket/Task**: První úkol sebe-vylepšení: Zvýšení transparentnosti

### Téma: Vylepšení výstupu pro lepší ladění a přehlednost.

**Popis Práce:**
- Na základě zpětné vazby od uživatele a autonomní analýzy jsem identifikoval potřebu vylepšit přehlednost výstupu v `interactive_session.py`.
- Upravil jsem metodu `run` v `core/orchestrator.py`:
    - Přidány barevné výpisy (pomocí ANSI kódů) pro odlišení fází běhu (INFO, AKCE, VÝSLEDEK).
    - Odkomentováno a vylepšeno logování, které nyní zobrazuje kompletní prompt odesílaný do LLM a přesný JSON-RPC požadavek pro MCP servery.
- Opravena chyba v načítání API klíče (použití `GEMINI_API_KEY` místo `GOOGLE_API_KEY`).
- Implementována nová schopnost plnit více-krokové úkoly přidáním nástroje `task_complete` a úpravou rozhodovací smyčky.

**Důvod a Kontext:**
- Původní výstup byl příliš strohý a neumožňoval snadné ladění ani pochopení "myšlenkového" procesu agenta.
- Cílem bylo vytvořit výstup podobný tomu v prostředí `jules.google.com`, který je klíčový pro efektivní spolupráci a další seberozvoj.

**Narazené Problémy a Řešení:**
- **Problém:** Agent se zpočátku zasekával na snaze opravit pozůstatky staré architektury.
- **Řešení:** Proveden důkladný úklid projektu, který odstranil všechny matoucí a nekompatibilní soubory.
- **Problém:** Agent se nespouštěl v ONLINE režimu kvůli chybnému názvu proměnné pro API klíč.
- **Řešení:** Chyba byla po upozornění uživatelem nalezena a opravena.

**Dopad na Projekt:**
- Agent je nyní mnohem transparentnější, což usnadňuje ladění a další vývoj.
- Byla ověřena a posílena jeho schopnost plnit komplexní, více-krokové úkoly.
- Projekt je v robustním a finálním stavu, připravený na další rozšiřování.
---