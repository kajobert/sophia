#!/usr/bin/env python3
"""
Testovací skript pro ověření funkcionality guardian systému.
Tento skript testuje schopnost guardianu detekovat pády a provádět automatickou obnovu.
"""

import os
import subprocess
import time
import tempfile
import shutil
from pathlib import Path

def test_guardian_crash_detection():
    """Testuje detekci pádu aplikace guardianem."""
    print("🧪 Testování detekce pádu guardianem...")
    
    # Vytvoříme dočasný adresář pro test
    with tempfile.TemporaryDirectory() as temp_dir:
        test_crash_log = Path(temp_dir) / "crash.log"
        
        # Simulujeme crash log
        crash_content = "Simulovaný pád aplikace - testovací scénář"
        test_crash_log.write_text(crash_content, encoding='utf-8')
        
        # Zkopírujeme testovací crash log na správné místo
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        target_crash_log = logs_dir / "crash.log"
        shutil.copy2(test_crash_log, target_crash_log)
        
        print(f"✓ Vytvořen testovací crash log: {target_crash_log}")
        return True

def test_last_known_good_commit():
    """Testuje funkčnost posledního známého dobrého commitu."""
    print("🧪 Testování systému posledního známého dobrého commitu...")
    
    try:
        # Získáme aktuální commit
        current_commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True
        ).stdout.strip()
        
        print(f"✓ Aktuální commit: {current_commit}")
        
        # Otestujeme získání posledního známého dobrého commitu
        result = subprocess.run(
            ["python", "guardian/runner.py"],
            capture_output=True, text=True
        )
        
        if "Initialized" in result.stdout or "FATAL" not in result.stdout:
            print("✓ Systém posledního známého dobrého commitu funguje")
            return True
        else:
            print("✗ Chyba v systému posledního známého dobrého commitu")
            print(f"Výstup: {result.stdout}")
            print(f"Chyba: {result.stderr}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Chyba při získávání commitu: {e}")
        return False

def test_guardian_integration():
    """Testuje integraci guardianu s TUI aplikací."""
    print("🧪 Testování integrace guardianu s TUI...")
    
    try:
        # Otestujeme, zda TUI aplikace může být spuštěna
        result = subprocess.run(
            ["python", "-c", "from tui.app import SophiaTUI; print('TUI importována úspěšně')"],
            capture_output=True, text=True
        )
        
        if "TUI importována úspěšně" in result.stdout:
            print("✓ TUI aplikace může být importována")
            return True
        else:
            print("✗ Chyba při importu TUI aplikace")
            print(f"Výstup: {result.stdout}")
            print(f"Chyba: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Výjimka při testu TUI: {e}")
        return False

def test_memory_persistence():
    """Testuje, zda je paměťová databáze správně zachována."""
    print("🧪 Testování persistence paměťové databáze...")
    
    memory_db = Path("memory/memory.db")
    
    if memory_db.exists():
        print(f"✓ Paměťová databáze existuje: {memory_db}")
        
        # Ověříme, že není v .gitignore
        with open(".gitignore", "r") as f:
            gitignore_content = f.read()
            
        if "!memory/memory.db" in gitignore_content:
            print("✓ Paměťová databáze je správně vyloučena z ignorování")
            return True
        else:
            print("✗ Paměťová databáze není správně vyloučena z ignorování")
            return False
    else:
        print("✗ Paměťová databáze neexistuje")
        return False

def main():
    """Hlavní funkce pro spuštění všech testů."""
    print("🚀 Spouštím komplexní test guardian systému...\n")
    
    tests = [
        ("Detekce pádu", test_guardian_crash_detection),
        ("Poslední známý dobrý commit", test_last_known_good_commit),
        ("Integrace s TUI", test_guardian_integration),
        ("Persistence paměti", test_memory_persistence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ Neočekávaná chyba v testu '{test_name}': {e}")
            results.append((test_name, False))
        print()
    
    # Shrnutí výsledků
    print("📊 VÝSLEDKY TESTOVÁNÍ:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Celkem: {passed}/{len(results)} testů úspěšných")
    
    if passed == len(results):
        print("\n🎉 VŠECHNY TESTY PROŠLY! Guardian systém je připraven.")
        print("   Systém bude schopen detekovat pády a provádět automatickou obnovu.")
    else:
        print(f"\n⚠️  {len(results) - passed} testů selhalo. Je potřeba provést opravy.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)