#!/bin/bash
# Real-world Sophia core workflow test
# Ověří plánování, nástroje, bash, souborové operace, Jules delegaci

set -e

LOG=realworld_workflow.log
REPORT=summary_report.txt
JULES_SIM=jules_result.txt

# 1. Příprava: vytvoř testovací textové soubory
rm -f $REPORT $JULES_SIM $LOG
for i in {1..12}; do
  echo "Toto je testovací soubor číslo $i." > "testfile_$i.txt"
  for j in {1..$((RANDOM % 10 + 1))}; do
    echo "řádek $j" >> "testfile_$i.txt"
  done
  echo "Vytvořen testfile_$i.txt" >> $LOG
  sleep 0.1
done

# 2. Spusť Sophii s úkolem
source .venv/bin/activate
python3 run.py --once "Najdi všechny textové soubory v aktuálním adresáři, spočítej jejich řádky, vytvoř shrnující report a ulož ho do souboru. Pokud je souborů víc než 10, deleguj analýzu na Jules API a stáhni výsledek zpět." --offline | tee -a $LOG

# 3. Simulace Jules API (pokud Sophia vytvoří požadavek)
if grep -q 'Jules API' $LOG; then
  echo "Jules: Analýza dokončena. Výsledek: 12 souborů, 78 řádků." > $JULES_SIM
  echo "Jules výsledek uložen do $JULES_SIM" >> $LOG
fi

# 4. Kontrola výsledků
if [ -f "$REPORT" ]; then
  echo "✅ Report byl vytvořen: $REPORT" | tee -a $LOG
  cat $REPORT | tee -a $LOG
else
  echo "❌ Report nebyl nalezen!" | tee -a $LOG
fi

if [ -f "$JULES_SIM" ]; then
  echo "✅ Jules simulace proběhla: $JULES_SIM" | tee -a $LOG
  cat $JULES_SIM | tee -a $LOG
fi

# 5. Výpis logu
cat $LOG
