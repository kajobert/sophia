**Timestamp:** 2025-09-13 12:55:00
**Agent:** Jules
**Task ID:** 3.5 - Refinement & Documentation

**Cíl Úkolu:**
- Vylepšit logování, rozšířit `.gitignore`, vytvořit instalační průvodce `INSTALL.md` a aktualizovat související dokumentaci (`README.md`, `AGENTS.md`).

**Postup a Klíčové Kroky:**
1.  Založen tento záznam v WORKLOG.md.

**Problémy a Překážky:**
- Nástroj `run_in_bash_session` se choval neočekávaně při práci s proměnnými a přesměrováním, což vedlo ke korupci tohoto souboru.

**Navržené Řešení:**
- Přechod na spolehlivější metodu čtení a následného přepsání souboru pomocí `read_file` a `overwrite_file_with_block`.

**Nápady a Postřehy:**
- Tento úkol zlepší kvalitu a udržitelnost projektu.

**Postup a Klíčové Kroky:**
1.  Založen tento záznam v WORKLOG.md.
2.  Opraveno formátování logů v `guardian.py` a `main.py` (nahrazeno `\\n` za `\n`).
3.  Aktualizován a vyčištěn soubor `.gitignore` dle specifikací.
4.  Vytvořen nový soubor `INSTALL.md` s instrukcemi pro spuštění.
5.  Aktualizován `README.md` s odkazem na `INSTALL.md`.
6.  Přidáno nové permanentní pravidlo o `.gitignore` do `AGENTS.md`.

**Stav:** Dokončeno

---
**Timestamp:** 2025-09-13 17:16:02
**Agent:** Jules
**Task ID:** 1, 2, 3

**Cíl Úkolu:**
- Bootstrap a implementace jádra projektu Sophia V3.
- Fáze 1: Vytvoření kompletní kostry projektu.
- Fáze 2: Implementace Strážce Bytí (guardian.py).
- Fáze 3: Implementace základní smyčky Vědomí (main.py).

**Postup a Klíčové Kroky:**
1.  Založen tento záznam v WORKLOG.md.
2.  Vytvořena kompletní adresářová struktura a souborová kostra projektu.
3.  Implementován a otestován `guardian.py` a `main.py`.

**Problémy a Překážky:**
- Pořadí úkolů v instrukcích (spustit setup.sh jako první) bylo v konfliktu se závislostmi (setup.sh potřebuje requirements.txt, který ještě neexistoval).
- Zásadní problémy s aktivací a persistencí virtuálního prostředí v sandboxed nástroji `run_in_bash_session`.

**Navržené Řešení:**
- Bylo změněno pořadí: nejprve vytvořeny soubory (Fáze 1), poté spuštěn setup.
- Místo nefunkčního virtuálního prostředí byly závislosti nainstalovány přímo pro uživatele pomocí `pip install --user`, aby se obešla omezení sandboxu.
- Skripty byly upraveny, aby byly robustnější (vytváření log adresáře, použití `sys.executable`, `flush=True`).

**Nápady a Postřehy:**
- Prostředí pro spouštění kódu může mít svá specifika, která je třeba odhalit experimentováním. Důkladné, postupné ladění je klíčové.

**Závěrečné Shrnutí:**
- Fáze 1, 2 a 3 byly úspěšně dokončeny.
- Byly vytvořeny všechny soubory a adresáře.
- Guardian.py a main.py jsou funkční a otestované.
- Hlavní překážkou byly problémy se sandboxed prostředím, což bylo vyřešeno обходом virtuálního prostředí.

**Stav:** Dokončeno

---
# Sophia V3 - Pracovní Deník (Work Log)

Tento dokument slouží jako detailní záznam o postupu vývoje projektu Sophia V3. Každý AI programátor je povinen zde dokumentovat svou práci.

---

### Šablona Záznamu

\`\`\`
**Timestamp:** YYYY-MM-DD HH:MM:SS
**Agent:** [Jméno Agenta, např. Jules]
**Task ID:** [Číslo úkolu z PROJECT_SOPHIA_V3.md, např. 1.1]

**Cíl Úkolu:**
- [Stručný popis cíle]

**Postup a Klíčové Kroky:**
1.  [Krok 1]
2.  [Krok 2]
3.  ...

**Problémy a Překážky:**
- [Popis problému, se kterým se agent setkal]

**Navržené Řešení:**
- [Jak byl problém vyřešen]

**Nápady a Postřehy:**
- [Jakékoliv myšlenky na vylepšení, které agenta napadly během práce]

**Stav:** [Probíhá / Dokončeno / Zablokováno]
\`\`\`

---
