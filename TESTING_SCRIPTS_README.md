# SOPHIA Testing Scripts

Automatizované testovací skripty pro efektivní debugging SOPHIE v AI chat prostředí.

## Problém

Při testování SOPHIE v AI chat prostředí (např. GitHub Copilot) je neefektivní posílat jednotlivé příkazy:
1. Odeslání query → čekání na potvrzení
2. Čekání na dokončení → čekání na potvrzení  
3. Čtení logů → čekání na potvrzení
4. Analýza výsledků → čekání na potvrzení

**Řešení:** Jeden skript, který udělá všechny kroky najednou a uloží výsledky k analýze.

## Skripty

### 1. `test_sophia_query.sh` - Hlavní testovací skript

Odešle query, počká na dokončení, zachytí logy a výsledky.

**Použití:**
```bash
# Test s vlastním query
./test_sophia_query.sh "Přečti si posledních 50 řádků z logs/sophia.log"

# Test s výchozím query
./test_sophia_query.sh
```

**Co dělá:**
1. ✅ Zkontroluje, zda SOPHIA běží
2. 📋 Zachytí stav logů PŘED odesláním
3. 📤 Odešle query přes HTTP API
4. ⏳ Čeká na dokončení (max 120s)
5. 📋 Zachytí logy PO dokončení
6. 📊 Extrahuje relevantní sekce:
   - Planner output
   - Execution steps
   - Errors & warnings
   - Response
7. 💾 Uloží vše do `test_results/test_TIMESTAMP.txt`

**Výstup:**
```
test_results/
├── test_20251107_152530.txt       # Hlavní výsledky
├── logs_20251107_152530.txt       # Kompletní logy
└── logs_before_20251107_152530.txt # Logy před testem
```

### 2. `show_test_results.sh` - Zobrazení výsledků

Zobrazí výsledky testů.

**Použití:**
```bash
# Zobraz poslední test
./show_test_results.sh

# Zobraz konkrétní test (číslo z listu)
./show_test_results.sh 3

# Zobraz seznam všech testů
ls -t test_results/test_*.txt | nl
```

### 3. `compare_tests.sh` - Porovnání testů

Zobrazí přehlednou tabulku všech testů.

**Použití:**
```bash
./compare_tests.sh
```

**Výstup:**
```
No.   Timestamp            Steps      Errors     Status              
------------------------------------------------------------------
1     20251107_152530      2          0          ✅ SUCCESS
2     20251107_151245      0          1          ❌ FAILED - No plan
3     20251107_150830      2          3          ⚠️  COMPLETED WITH ERRORS
```

## Workflow pro AI Agenta

### 1. Odeslání testu (1 příkaz)
```bash
./test_sophia_query.sh "Tvůj test query"
```

### 2. Analýza výsledků (1 příkaz)
```bash
./show_test_results.sh
```

### 3. Pokud je chyba, oprav a znovu testuj
```bash
# Oprav kód v SOPHII
# ...

# Restart
sophia-stop && sleep 2 && sophia-start && sleep 35

# Znovu test
./test_sophia_query.sh "Stejný test query"
```

### 4. Porovnej výsledky
```bash
./compare_tests.sh
```

## Příklady testovacích queries

```bash
# Test čtení logů s tail_lines
./test_sophia_query.sh "Přečti si posledních 50 řádků z logs/sophia.log a najdi všechny ERROR záznamy"

# Test čtení root souboru
./test_sophia_query.sh "Přečti soubor roberts-notes.txt"

# Test multi-step analýzy
./test_sophia_query.sh "Analyzuj poslední chyby v mých logách a vytvoř hypotézu problému"

# Test delegace na Jules
./test_sophia_query.sh "Vytvoř Jules session pro opravu bugu XYZ a monitoruj dokončení"
```

## Výhody

✅ **Jeden příkaz** místo 5-10 interakcí
✅ **Automatické čekání** na dokončení
✅ **Zachycení kontextu** - logy před i po
✅ **Strukturované výsledky** - snadná analýza
✅ **Historie testů** - porovnání změn
✅ **Rychlé iterace** - oprav → test → analýza

## Struktura výsledku

Každý test obsahuje:

```
========================================
SOPHIA Query Test - 20251107_152530
========================================

Query: Přečti si posledních 50 řádků...

✅ SOPHIA is running (PID: 3322470)

========================================
PLANNER OUTPUT
========================================
[JSON plán generovaný plannerem]

========================================
EXECUTION STEPS
========================================
Step 1/2: tool_code_workspace.read_file
✅ Step 1 completed
Step 2/2: tool_llm.execute
✅ Step 2 completed

========================================
ERRORS & WARNINGS
========================================
[Relevantní chyby pokud existují]

========================================
RESPONSE
========================================
[Odpověď SOPHIE]

========================================
TEST SUMMARY
========================================
Steps executed: 2
Errors: 0
Status: ✅ SUCCESS
```

## Tips

- **Automatické cleanup**: Stará data mazat ručně nebo přidat cleanup skript
- **Timeout**: Defaultně 120s, upravitelné ve skriptu
- **Filtrování**: Známé chyby (database schema) se neoznačují jako FAILED
- **Background run**: Pro dlouhé testy přidat `nohup` nebo `screen`

## Troubleshooting

**SOPHIA neběží:**
```bash
sophia-start
sleep 35
./test_sophia_query.sh "test"
```

**Timeout:**
- Zvyš TIMEOUT ve skriptu (řádek 27)
- Nebo zkus jednodušší query

**Chybí curl:**
```bash
sudo apt-get install curl
```

**Prázdné výsledky:**
- Check zda API běží: `curl http://127.0.0.1:8000/health`
- Check logy: `tail -f logs/sophia.log`
