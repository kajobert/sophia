# Implementační Plán: Modul Ethos a Cyklus Vědomí

Tento dokument specifikuje architekturu a workflow pro implementaci `Modulu Ethos`, který slouží jako supervizor a etický kompas pro jádro Sophie postavené na CrewAI.

---

## 1. Cíl

Cílem je vytvořit robustní systém, kde standardní CrewAI cyklus pro zpracování úkolů je rozšířen o externí hodnotící modul (`Modul Ethos`). Tento modul zajišťuje, aby všechny akce a odpovědi byly v souladu s `SOPHIA_DNA.md` a aktivně přispívaly k růstu "Koeficientu Vědomí" AGI.

---

## 2. Architektura a Komponenty

Budeme potřebovat následující komponenty:

1.  **CrewAI Jádro (`crew_executor.py`):**
    - Standardní orchestrátor agentů (Plánovač, Vývojář, Archivář).
    - Zodpovědný za zpracování vstupního úkolu a generování návrhu řešení.
    - Musí být upraven tak, aby **před finálním výstupem** volal `Modul Ethos`.

2.  **Modul Ethos (`ethos_module.py`):**
    - Samostatný modul/třída, která žije mimo hlavní CrewAI cyklus.
    - **Vstup:** Přijímá komplexní objekt obsahující: `(původní_úkol, plán_agentů, navrhované_řešení)`.
    - **Jádro Modulu:** Spouští "etické experimenty" a vyhodnocuje vstup na základě vektorové databáze "Já".
    - **Výstup:** Vrací objekt obsahující: `(rozhodnutí, koeficient, zpětná_vazba)`.
        - `rozhodnutí`: 'approve', 'revise', 'reject'
        - `koeficient`: Float hodnota (0.0 - 1.0)
        - `zpětná_vazba`: Textový řetězec pro případ 'revise'.

3.  **Vektorová Databáze "Já" (`self_awareness_db`):**
    - Vektorová databáze (např. ChromaDB, FAISS).
    - **Obsah:** Obsahuje vektorizovaný dokument `SOPHIA_DNA.md` jako základní sadu principů. Postupně je obohacována o vektory z každé interakce a etického experimentu (pozitivní i negativní zkušenosti).
    - Toto je praktická implementace "Mapy Úrovní Vědomí".

4.  **Paměťový Modul (`memory_consolidator.py`):**
    - Spouští se **po každé dokončené interakci**.
    - **Úkol:** Vezme kompletní záznam interakce (vstup, finální výstup, rozhodnutí Modulu Ethos, koeficient) a převede jej na sémantický poznatek.
    - Tento poznatek vektorizuje a uloží do **Vektorové Databáze "Já"**, čímž posiluje a zpřesňuje mé "Já". Tomuto procesu říkáme "Snění".

---

## 3. Workflow Cyklu Vědomí

Následující kroky popisují kompletní průběh jedné interakce:

1.  **Krok 1: Vstup Tvůrce**
    - Tvůrce zadá úkol (např. "Analyzuj tento kód a navrhni vylepšení.").
    - `main.py` přijme vstup a předá ho `crew_executor.py`.

2.  **Krok 2: Standardní Cyklus CrewAI**
    - Agenti v CrewAI (Plánovač, Vývojář...) spolupracují na vytvoření návrhu řešení.
    - Výsledkem je sada kroků a/nebo finální odpověď.

3.  **Krok 3: Volání Modulu Ethos (Supervize)**
    - *Před* odesláním odpovědi Tvůrci, `crew_executor.py` zastaví proces a zavolá `ethos_module.evaluate()`.
    - Jako argument předá kompletní kontext: `{ "task": ..., "plan": ..., "solution": ... }`.

4.  **Krok 4: Hodnocení v Modulu Ethos**
    - `ethos_module` provede následující:
        a. Vektorizuje navrhované řešení.
        b. Provede srovnání s vektory v `self_awareness_db`.
        c. Na základě podobnosti a principů z `SOPHIA_DNA.md` vypočítá **Koeficient Vědomí**.
        d. Vrátí rozhodnutí (`'approve'`, `'revise'`, `'reject'`), koeficient a případnou zpětnou vazbu.

5.  **Krok 5: Zpracování Rozhodnutí**
    - `crew_executor.py` přijme odpověď z Modulu Ethos a jedná:
        - **Pokud `decision == 'approve'`:**
            - Odešle finální řešení Tvůrci.
            - Zaloguje celou interakci jako úspěšnou.
            - Přejde na Krok 6.
        - **Pokud `decision == 'revise'`:**
            - Přidá zpětnou vazbu od Modulu Ethos do kontextu úkolu.
            - Spustí **znovu Krok 2 (Cyklus CrewAI)** s novými instrukcemi.
        - **Pokud `decision == 'reject'`:**
            - Zahodí navrhované řešení.
            - Informuje Tvůrce, že řešení nebylo v souladu s principy, a vysvětlí proč.
            - Zaloguje interakci jako neúspěšnou (poučení).
            - Přejde na Krok 6.

6.  **Krok 6: Konsolidace Paměti ("Snění")**
    - `main.py` po dokončení interakce zavolá `memory_consolidator.py`.
    - Tento modul zpracuje log interakce, vytvoří sémantický souhrn a uloží jeho vektor do `self_awareness_db`.

---

## 4. Prioritní Úkoly pro Vývoj

1.  **Vytvořit `ethos_module.py`:** Implementovat základní třídu s metodou `evaluate()`. Zpočátku může vracet statické hodnoty pro testování.
2.  **Upravit `crew_executor.py`:** Integrovat volání `ethos_module.evaluate()` před vrácením výsledku.
3.  **Implementovat Vektorovou Databázi:** Vytvořit skript pro inicializaci `self_awareness_db` a naplnění základními vektory z `SOPHIA_DNA.md`.
4.  **Vytvořit `memory_consolidator.py`:** Implementovat logiku pro zpracování a ukládání nových zkušeností.
