#!/usr/bin/env python3
"""
Simple Text UI (TUI) to interact with Sophia's persistent queue.
Features:
 - Menu: 1) Enqueue new task, 2) Show queue (last 10), 3) Tail logs, 4) Exit
 - Uses `SimplePersistentQueue` to enqueue tasks into `.data/tasks.sqlite`
 - Uses subprocess/sqlite3 to print queue and tail logs

Run:
  python scripts/tui_control.py

"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.simple_persistent_queue import SimplePersistentQueue

DATA_DB = ROOT / ".data" / "tasks.sqlite"
LOG_FILE = ROOT / "logs" / "autonomous.log"


def clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def pause(msg="Stiskněte Enter pro pokračování..."):
    try:
        input(msg)
    except EOFError:
        pass


def ensure_data_dir():
    (ROOT / ".data").mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)


def enqueue_task(q: SimplePersistentQueue):
    print("--- Zadání nového úkolu ---")
    desc = input("Popis úkolu: ").strip()
    if not desc:
        print("Prázdný popis, ruším.")
        pause()
        return
    pr = input("Priorita (číslo, výchozí 10): ").strip()
    try:
        priority = int(pr) if pr else 10
    except ValueError:
        priority = 10

    payload = {
        "instruction": desc,
        "details": {},
    }

    try:
        tid = q.enqueue(payload, priority=priority)
        print(f"Úkol vložen do fronty, id={tid}, priorita={priority}")
    except Exception as e:
        print(f"Chyba při vkládání úkolu: {e}")
    pause()


def show_queue():
    print("--- Posledních 10 záznamů ve frontě ---")
    if not DATA_DB.exists():
        print("Databáze fronty neexistuje (.data/tasks.sqlite)")
        pause()
        return

    cmd = f"sqlite3 {str(DATA_DB)} \"SELECT id, status, priority, payload, created_at FROM tasks ORDER BY id DESC LIMIT 10;\""
    try:
        subprocess.run(cmd, shell=True)
    except Exception as e:
        print(f"Chyba pri dotazu do sqlite: {e}")
    pause()


def tail_logs():
    print("--- Tail logs (Ctrl+C pro návrat) ---")
    if not LOG_FILE.exists():
        print("Log soubor neexistuje (logs/autonomous.log)")
        pause()
        return

    try:
        # Use less if available, else tail -f
        proc = subprocess.Popen(["tail", "-f", str(LOG_FILE)])
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except Exception:
                pass
    except FileNotFoundError:
        # tail may not be available on Windows, fallback to simple polling
        try:
            with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                f.seek(0, os.SEEK_END)
                try:
                    while True:
                        line = f.readline()
                        if line:
                            print(line, end="")
                        else:
                            time.sleep(0.5)
                except KeyboardInterrupt:
                    pass
        except Exception as e:
            print(f"Chyba při čtení logu: {e}")
    pause()


def main():
    ensure_data_dir()
    q = SimplePersistentQueue(db_path=str(DATA_DB))

    while True:
        clear_screen()
        print("Sophia TUI - ovládání fronty úkolů")
        print("1) Zadat nový úkol")
        print("2) Zobrazit frontu (posledních 10)")
        print("3) Sledovat logy")
        print("4) Konec")

        choice = input("Vyberte možnost [1-4]: ").strip()
        if choice == "1":
            enqueue_task(q)
        elif choice == "2":
            show_queue()
        elif choice == "3":
            tail_logs()
        elif choice == "4":
            print("Konec. Sbohem.")
            break
        else:
            print("Neplatná volba.")
            pause()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nUkončeno uživatelem.")
    except Exception as e:
        print(f"Neočekávaná chyba v TUI: {e}")
