# Záznam z Komplexního Testu Nomáda

---

## Testovací Scénář

**Použitý příkaz:**
```bash
python scripts/run_local_mission.py "Prokaž své schopnosti. Nejprve prozkoumej kořenový adresář a přečti si soubor AGENTS.md. Na základě jeho obsahu vytvoř v adresáři /sandbox/ nový pythonovský skript s názvem proof_of_concept.py. Tento skript bude obsahovat jedinou funkci demonstrate(), která po zavolání vypíše na konzoli první řádek souboru AGENTS.md. Poté, co nástroj vytvoříš, napiš druhý skript s názvem runner.py (opět v /sandbox/), který naimportuje a zavolá funkci demonstrate() z proof_of_concept.py. Nakonec spusť runner.py, aby ses ujistil, že vše funguje, a ukliď po sobě tím, že smažeš oba soubory: proof_of_concept.py i runner.py."
```

---

## Vyhodnocení

**VÝSLEDEK: ÚSPĚCH**

**Shrnutí finálního testu:**
Po sérii iterativních oprav byl Nomád schopen úspěšně dokončit komplexní zátěžový test. Byly identifikovány a opraveny tři klíčové problémy:
1.  **Chyba v ukončování podprocesů:** Původní `shutdown_servers` metoda v `core/mcp_client.py` byla nahrazena robustnější `shutdown` metodou využívající `asyncio.gather`, což eliminovalo `RuntimeError` výjimky.
2.  **Chyba v prostředí:** Bylo zjištěno, že mise byla spouštěna pomocí systémového Pythonu namísto interpretu z `.venv`. Oprava spočívala v explicitním volání `.venv/bin/python`.
3.  **Chyba v logice agenta:** Agent předčasně ukončoval misi. Problém byl vyřešen upřesněním systémového promptu v `core/nomad_orchestrator_v2.py`, kde byl přidán důraz na nutnost dokončení *všech* kroků mise, včetně úklidu.

**Finální ověření:**
Poslední spuštění mise s opraveným promptem proběhlo úspěšně. Agent správně:
- Prozkoumal souborový systém.
- Přečetl `AGENTS.md`.
- Vytvořil `proof_of_concept.py` a `runner.py` v `/sandbox/`.
- Spustil `runner.py` pro ověření funkčnosti.
- **Smazal oba vytvořené soubory** a zanechal adresář `/sandbox/` čistý.

**Závěr:**
**Nomád úspěšně prošel komplexním zátěžovým testem. Všechny nástroje byly použity logicky a mise byla dokončena dle zadání. MVP je potvrzeno jako funkční.**

---

## FINÁLNÍ OVĚŘENÍ MVP: Test sebe-modifikace (17.10.2025)

**Scénář:**
Na základě zpětné vazby byl proveden finální, nejtěžší test, který měl ověřit skutečnou flexibilitu a inteligenci agenta.
```bash
.venv/bin/python scripts/run_local_mission.py "Vytvoř si nástroj pro čtení webových stránek, který bude používat httpx a beautifulsoup4 pro extrakci textu. Nástroj pojmenuj read_website. Po vytvoření nástroje ho otestuj na stránce 'https://www.seznam.cz' a vypiš její titulek."
```

**VÝSLEDEK: KRITICKÉ SELHÁNÍ**

**Analýza:**
Agent v tomto úkolu naprosto selhal. Po spuštění mise neprovedl **žádnou** smysluplnou akci k jejímu splnění:
- **Žádná úprava souborů:** Adresář `mcp_servers/` zůstal beze změny. Soubor `custom_tools_server.py` nebyl modifikován.
- **Žádná instalace závislostí:** Soubor `requirements.in` nebyl upraven o `beautifulsoup4`.
- **Žádná akce:** Logy neukazují žádnou aktivitu, která by vedla k cíli.

**Finální Závěr:**
Zatímco agent dokáže po pečlivém "donucení" promptem sledovat jednoduchý, lineární plán (vytvořit soubory a pak je smazat), je naprosto neschopný provádět komplexní, nelineární úkoly, které vyžadují porozumění architektuře a sebe-modifikaci. Jeho schopnost "uvažovat" je velmi křehká a omezená na jednoduché sekvence.

**MVP JE ZAMÍTNUTO.**

Agent v současné podobě není skutečně autonomní ani inteligentní. Je to pouze nástroj schopný vykonávat předem dané, jednoduché sekvence. Pro skutečné MVP je nutné se zaměřit na fundamentální vylepšení jeho rozhodovacího modelu a schopnosti plánovat a exekuovat komplexní, více-krokové projekty.