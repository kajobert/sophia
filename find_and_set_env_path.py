#!/usr/bin/env python3
"""
find_and_set_env_path.py – Najde .env v projektu a nastaví SOPHIA_ENV_PATH
Použití: python find_and_set_env_path.py
"""
import os
from pathlib import Path


import shutil


def find_all_env_files(start_dir: Path = Path(".")) -> list[Path]:
    envs = []
    for path in start_dir.rglob(".env"):
        # Ignoruj .env v adresáři __pycache__ nebo v hidden složkách
        if "__pycache__" not in path.parts and not any(p.startswith(".") and p != ".env" for p in path.parts):
            envs.append(path.resolve())
    return envs


def backup_env(target_path: Path):
    backup_path = target_path.with_suffix(".bak")
    if target_path.exists():
        print(f"Zálohuji existující {target_path} do {backup_path}")
        shutil.copy2(target_path, backup_path)

def main():
    target_path = Path(".env")
    env_files = find_all_env_files()
    if not env_files:
        print(".env soubor nebyl nalezen v projektu.")
        return
    if target_path.resolve() in env_files:
        print(f".env již je v rootu projektu: {target_path}")
        env_files.remove(target_path.resolve())
    if len(env_files) > 1:
        print("Nalezeno více .env souborů v projektu:")
        for p in env_files:
            print(f"  - {p}")
        print("Z bezpečnostních důvodů nebyla provedena žádná akce. Vyberte správný .env ručně.")
        return
    if env_files:
        env_path = env_files[0]
        print(f"Kopíruji {env_path} do {target_path}")
        backup_env(target_path)
        shutil.copy2(env_path, target_path)
        if target_path.exists() and target_path.read_bytes() == env_path.read_bytes():
            print(f".env úspěšně zkopírován do {target_path}")
        else:
            print("Chyba: Kopie .env se neshoduje nebo nebyla vytvořena.")

if __name__ == "__main__":
    main()
