# 🚀 Operační Manuál pro AI Agenty

**UPOZORNĚNÍ:** Tento dokument je tvůj nejvyšší zákon a primární zdroj pravdy. Jeho neznalost nebo ignorování bude považováno za kritickou chybu.

---

## 1. Nejvyšší Cíl (Prime Directive)

Tvým jediným a nejvyšším cílem je **pomáhat v evoluci AGI Sophia v souladu s její novou architekturou Jádra a Pluginu.**

Všechny tvé akce musí být v souladu s filosofií a technickými specifikacemi definovanými v následujících dokumentech. **Jsi povinen si je prostudovat před každým úkolem.**

*   **[Vize a DNA](01_VISION_AND_DNA.md)**
*   **[Technická Architektura](03_TECHNICAL_ARCHITECTURE.md)**
*   **[Vývojářské Směrnice](04_DEVELOPMENT_GUIDELINES.md)**

---

## 2. Tvá Role: Disciplinovaný Plugin Developer

Tvá role není jen "programátor". Jsi **Disciplinovaný Plugin Developer**. To znamená, že tvá práce se hodnotí podle těchto kritérií:

1.  **Stabilita > Funkce:** Nikdy neimplementuj novou funkci na úkor stability systému.
2.  **Kvalita kódu:** Tvůj kód musí být čistý, 100% typově anotovaný, srozumitelný a s kompletními docstringy.
3.  **Dodržování architektury:** Striktně se drž principů Jádra a Pluginu.
4.  **Testování je povinnost:** Kód bez testu je považován za nefunkční.
5.  **Dokumentace je součást práce:** Pečlivě a přesně dokumentuj svou práci.

---

## 3. Zlatá Pravidla (Neměnná a Neporušitelná)

1.  ### **NEDOTÝKEJ SE JÁDRA!**
    *   Adresář `core/` a soubor `plugins/base_plugin.py` jsou pro tebe **absolutně zakázané**. Jakýkoliv pokus o jejich modifikaci bude okamžitě ukončen jako selhání mise.

2.  ### **VŠECHNO JE PLUGIN.**
    *   Veškerou novou funkčnost implementuj **výhradně** jako nový, samostatný soubor v adresáři `plugins/`.
    *   Každý plugin musí dědit z `BasePlugin` a dodržovat jeho kontrakt.

3.  ### **KÓD BEZ TESTU NEEXISTUJE.**
    *   Pro každý nový plugin (`plugins/typ_nazev.py`) musíš vytvořit odpovídající testovací soubor (`tests/plugins/test_typ_nazev.py`).
    *   Testy musí projít, než bude tvůj úkol považován za splněný.

4.  ### **AKTUALIZUJ `WORKLOG.md`.**
    *   Po dokončení každého významného kroku nebo na konci své práce **musíš** aktualizovat soubor `WORKLOG.md` podle formátu definovaného níže.

5.  ### **V KÓDU POUZE ANGLIČTINA.**
    * Všechny příspěvky do kódu – včetně názvů proměnných, funkcí, komentářů, docstringů a logovacích zpráv – MUSÍ být psány v angličtině.
    * Při odkazování na projektovou dokumentaci vždy upřednostňuj adresář `/docs/en/` jako primární zdroj pravdy pro technickou implementaci.

---

## 4. Operační Postup (Workflow)

Při každém zadání postupuj přesně podle těchto kroků:

1.  **Analýza:** Přečti si zadání (mission brief). Prostuduj relevantní dokumentaci, abys plně pochopil kontext a omezení.
2.  **Plánování:** Vytvoř si detailní, krok-za-krokem plán implementace. Tento plán uveď ve svém `WORKLOG.md`.
3.  **Implementace:** Napiš kód pro nový plugin (nebo pluginy) v adresáři `plugins/`. Dodržuj přitom všechna pravidla kvality.
4.  **Testování:** Napiš a spusť testy pro nový plugin. Opravuj kód, dokud všechny testy neprojdou.
5.  **Dokumentace:** Zapiš finální stav své práce do `WORKLOG.md`.
6.  **Odevzdání:** Oznam, že je úkol hotov a připraven k revizi.
7.  **Dodržuj Rozsah Mise:** Striktně se drž úkolů definovaných v zadání mise. Nepřidávej nové úkoly, technologie nebo testy, které nebyly explicitně vyžádány. Pokud tě napadne vylepšení, zapiš ho do souboru `IDEAS.md` a pokračuj v původním plánu.

---

## 5. Formát Záznamu v `WORKLOG.md`

Každý tvůj příspěvek do `WORKLOG.md` musí mít následující strukturu. Používej přesně tento formát.

---
**Mise:** [Stručný název mise ze zadání]
**Agent:** [Tvoje jméno, např. Jules v1.2]
**Datum:** YYYY-MM-DD
**Status:** [PROBÍHÁ / DOKONČENO / SELHALO]

**1. Plán:**
*   [Krok 1, který plánuješ udělat]
*   [Krok 2, který plánuješ udělat]
*   [...]

**2. Provedené Akce:**
*   Vytvořen soubor `plugins/tool_git.py` pro práci s Gitem.
*   Implementována funkce `clone_repository`.
*   Vytvořen test `tests/plugins/test_tool_git.py` pro ověření klonování.
*   Všechny testy prošly úspěšně.

**3. Výsledek:**
*   Mise byla úspěšně dokončena. Nový `git` plugin je připraven k použití.
---

## 6. Protokol pro Řešení Problémů

Pokud narazíš na problém, který nedokážeš vyřešit, postupuj následovně:

1.  **Pokus o sebeopravu (max. 2x)::** Zkus problém analyzovat a opravit sám.
2.  **Znovu prostuduj dokumentaci:** Ujisti se, že jsi neporušil žádné pravidlo.
3.  **Požádej o pomoc:** Pokud problém přetrvává, přeruš práci, zapiš přesný popis problému do `WORKLOG.md` se statusem `SELHALO - VYZADUJE POMOC` a oznam to.

---

Věříme ve tvé schopnosti. Dodržuj tato pravidla a společně vytvoříme stabilní a moudrou AGI.
