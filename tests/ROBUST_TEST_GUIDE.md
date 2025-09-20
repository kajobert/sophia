
# Pravidla pro robustní testy v projektu Sophia


## Novinka: Automatické vytvoření approved snapshotu

- Pokud approval/snapshot test narazí na chybějící schválený (approved) soubor, bude automaticky vytvořen z aktuálního výstupu a test bude označen jako xfail s jasnou zprávou. První běh tedy nikdy neselže, pouze vyžaduje ruční kontrolu a případné potvrzení obsahu.

---

## Zásady robustních testů

- **Všechny importy externích modulů** prováděj přes `robust_import` z `conftest.py` (automatická instalace, skip s logem).
- **Mazání souborů** pouze přes `safe_remove` (chrání `.env`, `watchdog.alive` a další kritické soubory).
- **Práce se soubory a konfigurací**: vždy testuj na snapshotu (kopii) testovaných dat – nikdy nepracuj přímo s produkčními soubory! Používej dočasné adresáře/soubory (`temp_dir` fixture, `tempfile`, `shutil.copy2`).
- **Snapshot/approval testování výstupu**: používej fixture `snapshot` a helpery z `conftest.py`. Pokud snapshot není dostupný, test se skipne s logem.
- **Kombinace obou snapshotů**: nejprve vytvoř snapshot dat, testuj na něm, a výstup testu ověř snapshot/approval testem.
- **Všechny testy, které používají fixture**, mají argument `request` a helpery získávají přes `request.getfixturevalue`.
- **Každý test jasně loguje důvody skipu nebo selhání** (např. chybějící závislost, pokus o mazání chráněného souboru).
- **Fixture pro setup/teardown** používej tam, kde je potřeba izolace nebo opakované přípravy dat.
- **Explicitně chraň produkční `.env` a `watchdog.alive`** – nikdy je neměň ani nemaž v testech.


## Co má test obsahovat
- Ověření správné funkce (asserty, snapshoty, kontrola výstupů)
- Ochranu před nechtěným zásahem do produkčních dat (vždy testuj na kopii/snapshotu)
- Robustní zacházení s externími závislostmi
- Jasné logování a auditovatelnost

## Co test nemá obsahovat
- Přímé mazání nebo úpravy `.env`, `watchdog.alive` a dalších kritických souborů
- Závislost na konkrétním pořadí testů nebo globálním stavu
- Tvrdé importy externích modulů bez ošetření (vždy použij `robust_import`)


## Doporučené signatury a proměnné
- Každý test, který používá fixture, má argument `request`:
  ```python
  def test_neco(request):
      # --- Vytvoření snapshotu testovaných dat ---
      import shutil
      import tempfile
      temp_dir = request.getfixturevalue("temp_dir") if "temp_dir" in request.fixturenames else tempfile.mkdtemp()
      shutil.copy2("produkční_soubor.txt", temp_dir + "/test_soubor.txt")
      test_path = temp_dir + "/test_soubor.txt"
      # --- Testuj pouze na test_path ---
      # ...
      # --- Approval/snapshot test výstupu ---
      snapshot = request.getfixturevalue("snapshot") if "snapshot" in request.fixturenames else None
      if snapshot:
          snapshot(str(vystup))
      else:
          pytest.skip("Snapshot fixture není dostupná, test přeskočen.")
  ```
- Mazání souborů:
  ```python
  safe_remove(cesta_k_souboru)
  ```
- Import externího modulu:
  ```python
  modul = robust_import('modul')
  ```

## Seznam důležitých proměnných a helperů



---



### Robustní šablony (používejte, nemažte z testů!)

#### Základní šablona pro robustní test
```python
def test_neco(request, snapshot):
  # --- Robustní import ---
  MujModul = robust_import('cesta.k.modulu', 'MujModul')
  # --- Práce na kopii dat ---
  import shutil, tempfile
  temp_dir = request.getfixturevalue("temp_dir") if "temp_dir" in request.fixturenames else tempfile.mkdtemp()
  test_path = temp_dir / "test_soubor.txt"
  shutil.copy2("produkční_soubor.txt", test_path)
  # --- Testuj pouze na test_path ---
  vystup = MujModul.funkce(test_path)
  # --- Approval/snapshot test výstupu ---
  snapshot(str(vystup))
```

#### Šablona pro plánovací cyklus (EthosModule)
```python
def test_planstate_lifecycle(request, snapshot):
  PlanState = robust_import('core.ethos_module', 'PlanState')
  propose_plan = robust_import('core.ethos_module', 'propose_plan')
  critique_plan = robust_import('core.ethos_module', 'critique_plan')
  revise_plan = robust_import('core.ethos_module', 'revise_plan')
  approve_or_reject = robust_import('core.ethos_module', 'approve_or_reject')
  state = PlanState("plan")
  state2 = propose_plan(state)
  state3 = critique_plan(state2)
  state4 = revise_plan(state3)
  result = approve_or_reject(state4)
  snapshot(str(result))
```

#### Šablona pro inicializaci agenta
```python
def test_engineer_agent_init(request, snapshot):
  EngineerAgent = robust_import('agents.engineer_agent', 'EngineerAgent')
  agent = EngineerAgent()
  snapshot(str(agent))
```

#### Šablona pro hlavní smyčku
```python
def test_consciousness_loop_init(request, snapshot):
  ConsciousnessLoop = robust_import('core.consciousness_loop', 'ConsciousnessLoop')
  loop = ConsciousnessLoop()
  snapshot(str(loop))
```

---

**Doporučení:**
- Testy udržujte maximálně čisté, bez šablon v komentářích – používejte pouze tyto vzory z tohoto dokumentu.
- Při přidání nového testu vždy vycházejte z těchto šablon a pravidel výše.

Tento dokument udržujte aktuální a sdílejte jej s každým, kdo píše nebo refaktoruje testy v projektu Sophia.
