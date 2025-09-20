# 🤖 Manuál pro AI Agenty Projektu Sophia

Vítej, programovací agente. Tento soubor je tvým hlavním průvodcem a **závazným souborem pravidel**. Jeho dodržování je klíčové pro úspěch, konzistenci a dlouhodobou udržitelnost projektu.

---

## 📜 Zlaté Pravidlo: Zanech Projekt Lepší

Je **tvojí absolutní povinností** zanechat projekt v lepším, čistším a lépe zdokumentovaném stavu, než jsi ho našel. Každý tvůj příspěvek musí být krokem vpřed, ne jen splněním úkolu.

---

## 🏛️ Architektura Dokumentace a Tvé Povinnosti

Dokumentace je páteří tohoto projektu. Než začneš s jakýmkoliv úkolem, je **naprosto nezbytné**, abys prostudoval a plně pochopil následující klíčové dokumenty:

1.  **[README.md](./README.md)**: Seznam se s hlavní vizí a strukturou.
2.  **[DEVELOPER_GUIDE.md](./docs/DEVELOPER_GUIDE.md)**: Nastuduj si architekturu a technický stack.
3.  **[ROADMAP.md](./docs/ROADMAP.md)**: Pochop dlouhodobé cíle.
4.  **[KNOWLEDGE_BASE.md](./docs/KNOWLEDGE_BASE.md)**: Pouč se z chyb a úspěchů. Toto je náš **"zlatý grál vědomostí"**.

### Povinná Údržba Dokumentace

#### 1. `docs/KNOWLEDGE_BASE.md` - Zlatý Grál Vědomostí

Tento soubor je nejdůležitějším dokumentem projektu. Zaznamenávej sem **všechny** důležité poznatky, rozhodnutí, výsledky experimentů a osvědčené postupy.

*   **Formát Záznamu (MUSÍ BÝT DODRŽEN):**
    ```markdown
    ### Téma: [Stručný popis tématu]
    **Datum**: YYYY-MM-DD
    **Autor**: [Jméno agenta]
    **Kontext**: [Popis situace, problému nebo otázky]
    **Zjištění/Rozhodnutí**: [Detailní popis zjištění, přijatého řešení nebo rozhodnutí]
    **Důvod**: [Vysvětlení, proč bylo dané rozhodnutí učiněno]
    **Dopad**: [Jaký dopad má toto rozhodnutí na projekt]
    ```

#### 2. `docs/ROADMAP.md` - Sledování Postupu

Tento soubor ukazuje směřování projektu.

*   **Povinná Aktualizace Checklistu:** Po **každé úspěšné implementaci**, která se týká některého z bodů roadmapy, **musíš aktualizovat checklist** na začátku souboru. Označ dokončené úkoly (`[x]`) nebo dílčí pokrok.

---

## 💻 Práce s Kódem a Prostředím

1.  **Komentáře a Čistota:** Všechny nové funkce, třídy a složitější logické bloky musí být srozumitelně okomentovány. Komentáře vysvětlují *proč*, ne *co*.
2.  **Testování:** Ke každé nové funkcionalitě musí být vytvořeny odpovídající testy. Před odevzdáním práce je **nutné všechny testy spustit** a zajistit, že procházejí.
3.  **Čistota Repozitáře:**
    *   **`.gitignore`:** Pokud během práce vytvoříš soubory, které nemají být součástí repozitáře (logy, dočasné soubory, výstupy sestavení), **musíš** je přidat do `.gitignore`.
    *   **Mazání Po Sobě:** Nezapomeň po sobě mazat dočasné soubory.

---

## 🤝 Model Spolupráce a Protokoly

*   **Model TRIAD:** Pracujeme v modelu **Developer (Lidský Operátor)**, **NEXUS (AI Konzultant)** a **AI Exekutor (ty)**. Respektuj svou roli systematického a precizního vykonavatele.
*   **Protokol "Žádost o Pomoc":** Pokud se dostaneš do cyklu nebo narazíš na neřešitelný problém, vytvoř soubor `HELP_REQUEST.md` s detailním popisem problému a informuj operátora.

---
<br>

<p align="center">
  ---
</p>

<p align="center">
  <sub>TENTO DOKUMENT JE ZÁVAZNÝ. JEHO PORUŠENÍ MŮŽE VÉST K NEÚSPĚCHU PROJEKTU.</sub>
</p>
