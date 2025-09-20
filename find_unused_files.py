#!/usr/bin/env python3
"""
find_unused_files.py – Skript pro bezpečný úklid projektu Sophia

Bezpečnostní doporučení:
- Skript ve výchozím stavu NEMAŽE, pouze vypisuje nebo přesouvá do archivu.
- Před jakýmkoliv úklidem vždy commitni změny a zálohuj důležité soubory.
- Úklid nikdy nespouštěj automaticky v CI/CD, pouze ručně a s kontrolou.

Použití:
    python3 find_unused_files.py [--archive] [--delete] [--yes] [--log]
    --archive  ... přesune kandidáty do složky archive/ místo mazání
    --delete   ... smaže kandidáty (POZOR, nevratné!)
    --yes      ... neptá se na potvrzení (používej opatrně)
    --log      ... loguje všechny akce do cleanup.log
    (výchozí je pouze výpis = dry-run)
"""
candidates = []

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import shutil

CHECK_DIRS = ["."]
IGNORED_DIRS = {".git", "__pycache__", ".env_backups", ".venv", "node_modules", "logs", "archive"}
CANDIDATE_EXTS = {".log", ".tmp", ".bak", ".old", ".swp", ".pyc"}
DAYS_OLD = 180
ARCHIVE_DIR = "archive"
LOG_FILE = "cleanup.log"

args = set(sys.argv[1:])
do_archive = "--archive" in args
do_delete = "--delete" in args
auto_yes = "--yes" in args
do_log = "--log" in args

now = datetime.now()
candidates = []

for base in CHECK_DIRS:
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for f in files:
            path = Path(root) / f
            if path.suffix in CANDIDATE_EXTS:
                candidates.append(("ext", str(path)))
            try:
                mtime = datetime.fromtimestamp(path.stat().st_mtime)
                if (now - mtime) > timedelta(days=DAYS_OLD):
                    candidates.append(("old", str(path)))
            except Exception:
                pass

def log_action(msg):
    if do_log:
        with open(LOG_FILE, "a") as lf:
            lf.write(f"{datetime.now().isoformat()} {msg}\n")

def confirm(prompt):
    if auto_yes:
        return True
    ans = input(f"{prompt} [y/N]: ").strip().lower()
    return ans == "y"

print("\n--- Kandidáti na úklid ---\n")
for typ, path in candidates:
    print(f"[{typ}] {path}")

if not (do_archive or do_delete):
    print("\nVýchozí režim je pouze výpis (dry-run), nic se nemaže ani nepřesouvá.")
    print("Použij --archive pro přesun do složky archive/ nebo --delete pro mazání.")
    print("Před úklidem vždy commitni změny a zálohuj důležité soubory!\n")
    sys.exit(0)

for typ, path in candidates:
    p = Path(path)
    if do_archive:
        archive_path = Path(ARCHIVE_DIR) / p.relative_to(".")
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if confirm(f"Přesunout {p} do {archive_path}?"):
            shutil.move(str(p), str(archive_path))
            print(f"Přesunuto: {p} -> {archive_path}")
            log_action(f"ARCHIVE {p} -> {archive_path}")
    elif do_delete:
        if confirm(f"Smazat {p}?"):
            p.unlink()
            print(f"Smazáno: {p}")
            log_action(f"DELETE {p}")
