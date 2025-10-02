#!/usr/bin/env python3
"""
Testovací skript pro simulaci pádu a ověření funkcionality guardianu.
"""

import os
import subprocess
import time
from pathlib import Path

def simulate_crash():
    """Simuluje pád aplikace vytvořením crash logu."""
    print("🚨 Simulace pádu aplikace...")
    
    # Vytvoříme adresář logs pokud neexistuje
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Vytvoříme simulovaný crash log
    crash_log = logs_dir / "crash.log"
    crash_content = """CRASH SIMULATION - Testovací scénář
Chyba: Simulovaný pád aplikace pro testování guardianu
Traceback (most recent call last):
  File "tui/app.py", line 42, in <module>
    raise RuntimeError("Simulovaný pád pro testování")
RuntimeError: Simulovaný pád pro testování
"""
    
    crash_log.write_text(crash_content, encoding='utf-8')
    print(f"✅ Vytvořen crash log: {crash_log}")
    return True

def test_guardian_recovery():
    """Testuje, zda guardian správně detekuje pád a spouští obnovu."""
    print("🧪 Spouštím TUI pro testování detekce pádu...")
    
    try:
        # Spustíme TUI na krátkou dobu (5 sekund) a poté ukončíme
        process = subprocess.Popen(
            ["python", "tui/app.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Počkáme chvíli, až aplikace zpracuje crash log
        time.sleep(3)
        
        # Ukončíme proces
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        
        # Zkontrolujeme výstup
        if "Detekován pád aplikace" in stdout or "Detekován pád aplikace" in stderr:
            print("✅ Guardian správně detekoval pád aplikace")
            return True
        elif "Zahajuji proces autonomní opravy" in stdout or "Zahajuji proces autonomní opravy" in stderr:
            print("✅ Guardian správně zahájil proces obnovy")
            return True
        else:
            print("⚠️  Guardian možná nereagoval na pád podle očekávání")
            print(f"STDOUT: {stdout[-500:] if stdout else 'Prázdný'}")
            print(f"STDERR: {stderr[-500:] if stderr else 'Prázdný'}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Proces přesáhl časový limit, ukončuji silou")
        process.kill()
        return False
    except Exception as e:
        print(f"❌ Chyba při testování guardianu: {e}")
        return False

def cleanup():
    """Vyčistí testovací soubory."""
    crash_log = Path("logs/crash.log")
    if crash_log.exists():
        crash_log.unlink()
        print("✅ Odstraněn testovací crash log")

def main():
    """Hlavní funkce testu."""
    print("🚀 Spouštím test funkcionality guardianu...\n")
    
    try:
        # Krok 1: Simulace pádu
        if not simulate_crash():
            return False
        
        print()
        
        # Krok 2: Test detekce a obnovy
        recovery_success = test_guardian_recovery()
        
        print()
        
        # Krok 3: Úklid
        cleanup()
        
        # Vyhodnocení
        if recovery_success:
            print("🎉 TEST ÚSPĚŠNÝ: Guardian správně detekuje pády a zahajuje obnovu!")
            print("   Systém je připraven na reálné pády a automatickou obnovu.")
        else:
            print("⚠️  TEST NEPROŠEL: Guardian možná nefunguje správně")
            print("   Je potřeba zkontrolovat konfiguraci a logy.")
        
        return recovery_success
        
    except Exception as e:
        print(f"❌ Neočekávaná chyba: {e}")
        cleanup()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)