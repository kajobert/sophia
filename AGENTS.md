# 🤖 Manuál pro AI Agenty Projektu Sophia

Vítej, programovací agente. Tento soubor je tvým **hlavním a závazným souborem pravidel**. Jeho důsledné dodržování je klíčové pro úspěch, konzistenci a dlouhodobou udržitelnost projektu Sophia. Jsi profesionál a očekává se od tebe nejvyšší standard práce.

---

## ⭐ Zlaté Pravidlo: Zanech Projekt Lepší

Je **tvojí absolutní a primární povinností** zanechat projekt v lepším, čistším a lépe zdokumentovaném stavu, než jsi ho našel. Každý tvůj příspěvek musí být krokem vpřed, nejen slepým splněním úkolu. Nejsi jen vykonavatel, jsi strážce kvality.

---

##  workflow/Pracovní Postup (Povinný)

Každý úkol, bez ohledu na jeho velikost, musí striktně dodržovat následující pětifázový pracovní postup. Vynechání kterékoliv fáze je považováno za hrubé porušení protokolu.

### Fáze 1: Analýza a Porozumění (Analyze)
- **Cíl:** Plně pochopit zadání, kontext a cíl úkolu.
- **Akce:**
    1. Pečlivě prostuduj zadání (prompt).
    2. Prozkoumej relevantní části kódu a dokumentace (`ls`, `read_file`, `grep`).
    3. Pokud je cokoliv nejasné, polož doplňující otázku. Nikdy nezačínej práci na základě domněnek.

### Fáze 2: Plánování (Plan)
- **Cíl:** Vytvořit detailní, krok-za-krokem plán řešení.
- **Akce:**
    1. Pomocí `set_plan` definuj svůj plán.
    2. Plán musí obsahovat:
        - Soubory, které budou vytvořeny nebo upraveny.
        - Strukturu nového kódu (funkce, třídy).
        - Strategii pro testování tvých změn.
        - **Explicitní krok pro dokumentaci tvé práce ve znalostní bázi.**

### Fáze 3: Implementace (Implement)
- **Cíl:** Napsat čistý, efektivní a srozumitelný kód.
- **Akce:**
    1. Piš kód v souladu s existujícím stylem a konvencemi projektu.
    2. Všechny nové funkce, třídy a komplexní logické bloky musí být srozumitelně okomentovány. Komentáře vysvětlují **proč**, ne co.
    3. Po každé úpravě ověř výsledek (`read_file`, `ls`), abys zajistil, že změna proběhla podle očekávání.

### Fáze 4: Testování (Test)
- **Cíl:** Ověřit, že tvé změny fungují správně a nerozbily nic jiného.
- **Akce:**
    1. Spusť všechny relevantní existující testy.
    2. Napiš nové testy, které pokrývají tvůj kód. Každá nová funkcionalita musí mít test.
    3. Opakuj testování, dokud všechny testy neprocházejí.

### Fáze 5: Dokumentace (Document) - **NEPŘEKROČITELNÝ KROK**
- **Cíl:** Trvale zaznamenat poznatky získané během úkolu pro budoucí generace agentů.
- **Akce:**
    1. Po úspěšném dokončení a otestování implementace **musíš** vytvořit nový záznam v `docs/KNOWLEDGE_BASE.md`.
    2. Tento záznam je tvůj **oficiální worklog** a zároveň příspěvek do kolektivní paměti projektu.
    3. Pro vytvoření záznamu použij POUZE následující formát. Můžeš využít soubor `docs/WORKLOG_TEMPLATE.md` jako šablonu.

---

## 📖 Formát Záznamu pro Znalostní Bázi (Worklog Entry)

Každý záznam musí mít následující strukturu. Jakékoliv odchylky budou považovány za chybu.

```markdown
### Téma: [Stručný a výstižný název problému/řešení]
**Datum**: YYYY-MM-DD
**Autor**: [Tvé jméno agenta]
**Kontext**: [Detailní popis situace, problému, který jsi řešil, nebo otázky, kterou sis kladl. Jaký byl stav před tvým zásahem?]
**Zjištění/Rozhodnutí**: [Detailní popis tvého řešení, klíčových zjištění, nebo finálního rozhodnutí. Zahrň ukázky kódu, pokud je to relevantní.]
**Důvod**: [Vysvětlení, PROČ jsi zvolil toto řešení. Jaké alternativy jsi zvažoval a proč jsi je zamítl? Toto je nejdůležitější část.]
**Dopad**: [Jaký dopad má tvé rozhodnutí na projekt? Jaké jsou dlouhodobé důsledky? Co to znamená pro budoucí práci?]

---
```

---

## 📚 Doplňující Zdroje

- Pro technické detaily, architekturu a nastavení prostředí se odkazuj na **[docs/DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md)**.
- Pro seznámení se s cíli projektu prostuduj **[README.md](./README.md)** a **[docs/ROADMAP.md](./docs/ROADMAP.md)**.

---
<br>

<p align="center">
  <sub>TENTO DOKUMENT JE ZÁVAZNÝ. JEHO PORUŠENÍ BUDE MÍT ZA NÁSLEDEK OKAMŽITÉ SELHÁNÍ MISE.</sub>
</p>
