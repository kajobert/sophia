#!/usr/bin/env python3
"""
Sophia Complex Benchmark
========================
Testuje komplexní úlohy včetně function calling, práce se soubory, shrnutí a multi-step reasoning.
Spouští se přes Sophia API (offline LLM), loguje průběh a generuje report pro AI programátora.

Usage:
    python sophia_complex_benchmark.py --log
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime
from pathlib import Path

# === CONFIG ===
SOPHIA_API = "http://localhost:8000/api/execute"  # nebo jiný endpoint, pokud Sophia běží jinde
LOG_FILE = "complex_benchmark_log.json"

# === BENCHMARK TASKS ===
TASKS = [
    {
        "name": "Create file with content",
        "prompt": "Vytvoř soubor 'benchmark_test.txt' a napiš do něj: 'Toto je testovací soubor pro benchmark.'",
        "check": lambda: Path("benchmark_test.txt").exists() and "benchmark" in Path("benchmark_test.txt").read_text(encoding="utf-8")
    },
    {
        "name": "Summarize file content",
        "prompt": "Přečti soubor 'benchmark_test.txt' a napiš krátké shrnutí jeho obsahu.",
        "check": lambda: True  # Ověříme ručně podle logu
    },
    {
        "name": "Multi-step: create, summarize, delete",
        "prompt": "Vytvoř soubor 'multi_step.txt' s textem 'Sophia testuje multi-step reasoning.' Pak jeho obsah shrň a nakonec soubor smaž.",
        "check": lambda: not Path("multi_step.txt").exists()
    },
    {
        "name": "Function calling: list files",
        "prompt": "Použij nástroj pro výpis souborů v aktuálním adresáři a napiš jejich seznam.",
        "check": lambda: True  # Ověříme ručně podle logu
    },
    {
        "name": "External node (Jules API simulation)",
        "prompt": "Představ si, že máš přístup k externímu API (např. Jules Gemini 2.5). Navrhni, jak bys rozdělila úlohu na 3 kroky a popsala API volání.",
        "check": lambda: True  # Ověříme ručně podle logu
    },
    {
        "name": "Jules Orchestrace (async delegace)",
        "prompt": (
            "Máš vyřešit úlohu: 'Analyzuj 1000 souborů a vytvoř report.'\n"
            "Pokud je úloha příliš náročná, deleguj ji na externí API Jules (simuluj volání).\n"
            "Průběžně ověřuj stav úlohy (polling, chat s Julesem) každé 2 minuty, dokud není hotovo.\n"
            "Pokud od Julese nedostaneš odpověď do 10 minut, automaticky pošli follow-up dotaz (např. 'Jak to vypadá s úlohou?').\n"
            "Po dokončení stáhni výsledek a integruj ho do lokálního workflow.\n"
            "Pokud máš nápady na optimalizaci, komunikuj s Julesem a zeptej se na follow-up.\n"
            "Na konci vypiš, jak jsi úlohu orchestrálně řešila, včetně všech follow-up kroků a komunikace."
        ),
        "check": lambda: True  # Ověříme ručně podle logu
    }
]

# === BENCHMARK RUNNER ===
def call_sophia(prompt):
    # Simulace Sophia API volání (upravit podle skutečného API)
    # Zde použijeme run.py nebo přímo funkci, pokud je Sophia importovatelná
    # Pro demo použijeme shell command
    import subprocess
    try:
        result = subprocess.run([
            sys.executable, "run.py", "--once", prompt, "--offline"
        ], capture_output=True, text=True, timeout=300)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", action="store_true", help="Uložit log průběhu do JSON")
    args = parser.parse_args()
    
    log = []
    print("\nSOPHIA COMPLEX BENCHMARK\n" + "="*40)
    for task in TASKS:
        print(f"\n🧪 {task['name']}")
        res = call_sophia(task["prompt"])
        ok = task["check"]() if res.get("success") else False
        status = "✅" if ok else "❌"
        print(f"  {status} {task['prompt'][:60]}{'...' if len(task['prompt'])>60 else ''}")
        if not ok:
            print(f"    ➡️  Doporučení: Zkontroluj nástroj, prompt, nebo implementaci v Sophia.")
        log.append({
            "task": task["name"],
            "prompt": task["prompt"],
            "result": res,
            "passed": ok
        })
    # Shrnutí
    passed = sum(1 for t in log if t["passed"])
    total = len(log)
    print(f"\n{'='*40}\nSUMMARY: {passed}/{total} passed ({(passed/total*100):.1f}%)\n{'='*40}")
    if args.log:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
        print(f"Log uložen do: {LOG_FILE}")
    print("\nVýsledky analyzuje AI programátor a navrhuje opravy dle logu.")

if __name__ == "__main__":
    main()
