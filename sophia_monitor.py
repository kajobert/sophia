# --- AUDIT: Detekce chyb v logu (pro guardian/testy) ---
import re
def check_backend_crash_log(log_path, lines=10):
    """
    Vrací dict s posledními řádky a nalezenými chybovými vzory (ImportError, Traceback).
    """
    result = {"last_lines": [], "error_matches": []}
    if not os.path.exists(log_path):
        return result
    with open(log_path, encoding="utf-8", errors="ignore") as f:
        all_lines = f.readlines()
    last_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
    result["last_lines"] = [l.rstrip("\n") for l in last_lines]
    error_patterns = [r"ImportError", r"Traceback"]
    for i, line in enumerate(last_lines):
        for pat in error_patterns:
            if re.search(pat, line):
                result["error_matches"].append((i, line.strip(), pat))
    return result
import os
import sys
import time
import json
import socket
import threading
import atexit
import hashlib
import shutil
from datetime import datetime, timezone

# --- HEARTBEAT ---
def get_heartbeat_path():
    return os.path.abspath("watchdog.alive")

def write_heartbeat(started, version="1.0.0"):
    data = {
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "started": started,
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "version": version
    }
    try:
        with open(get_heartbeat_path(), "w") as f:
            json.dump(data, f)
        print(f"[watchdog] Heartbeat aktualizován: {data}")
    except Exception as e:
        print(f"[watchdog] Chyba při zápisu heartbeat: {e}")

def remove_heartbeat(started):
    hb_path = get_heartbeat_path()
    if os.path.exists(hb_path):
        try:
            with open(hb_path) as f:
                data = json.load(f)
            if data.get("pid") == os.getpid() and data.get("started") == started:
                os.remove(hb_path)
                print(f"[watchdog] Heartbeat soubor smazán.")
            else:
                print(f"[watchdog] Heartbeat soubor nesmazán (patří jinému procesu nebo byl změněn).")
        except Exception as e:
            print(f"[watchdog] Chyba při mazání heartbeat: {e}")

# --- .ENV BACKUP ---
def watch_env_file(env_path=".env", backup_dir=".env_backups", interval=2):
    env_path = os.path.abspath(env_path)
    backup_dir = os.path.abspath(backup_dir)
    os.makedirs(backup_dir, exist_ok=True)
    last_hash = None
    print(f"[watchdog] Sleduji {env_path}, zálohy do {backup_dir}")
    while True:
        if os.path.exists(env_path):
            with open(env_path, "rb") as f:
                content = f.read()
                current_hash = hashlib.sha256(content).hexdigest()
            if last_hash is None:
                last_hash = current_hash
            elif current_hash != last_hash:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f".env_{timestamp}.bak")
                shutil.copy2(env_path, backup_path)
                print(f"[watchdog] Změna detekována, záloha vytvořena: {backup_path}")
                last_hash = current_hash
        time.sleep(interval)

# --- ENTRYPOINT ---
def main():
    if "--watch-env" in sys.argv:
        print("Spouštím watchdog pro .env soubor...")
        started = datetime.now(timezone.utc).isoformat()
        version = "1.0.0"
        def heartbeat_loop():
            while True:
                write_heartbeat(started, version)
                time.sleep(2)
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        atexit.register(remove_heartbeat, started)
        try:
            watch_env_file()
        except KeyboardInterrupt:
            print("\nWatchdog ukončen uživatelem.")
        finally:
            remove_heartbeat(started)
        sys.exit(0)

if __name__ == "__main__":
    main()
import os
import sys
import time
import json
import socket
import threading
import atexit
import hashlib
import shutil
from datetime import datetime, timezone

# --- HEARTBEAT ---
def get_heartbeat_path():
    return os.path.abspath("watchdog.alive")

def write_heartbeat(started, version="1.0.0"):
    data = {
        "pid": os.getpid(),
        "hostname": socket.gethostname(),
        "started": started,
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
        "version": version
    }
    try:
        with open(get_heartbeat_path(), "w") as f:
            json.dump(data, f)
        print(f"[watchdog] Heartbeat aktualizován: {data}")
    except Exception as e:
        print(f"[watchdog] Chyba při zápisu heartbeat: {e}")

def remove_heartbeat(started):
    hb_path = get_heartbeat_path()
    if os.path.exists(hb_path):
        try:
            with open(hb_path) as f:
                data = json.load(f)
            if data.get("pid") == os.getpid() and data.get("started") == started:
                os.remove(hb_path)
                print(f"[watchdog] Heartbeat soubor smazán.")
            else:
                print(f"[watchdog] Heartbeat soubor nesmazán (patří jinému procesu nebo byl změněn).")
        except Exception as e:
            print(f"[watchdog] Chyba při mazání heartbeat: {e}")

# --- .ENV BACKUP ---
def watch_env_file(env_path=".env", backup_dir=".env_backups", interval=2):
    env_path = os.path.abspath(env_path)
    backup_dir = os.path.abspath(backup_dir)
    os.makedirs(backup_dir, exist_ok=True)
    last_hash = None
    print(f"[watchdog] Sleduji {env_path}, zálohy do {backup_dir}")
    while True:
        if os.path.exists(env_path):
            with open(env_path, "rb") as f:
                content = f.read()
                current_hash = hashlib.sha256(content).hexdigest()
            if last_hash is None:
                last_hash = current_hash
            elif current_hash != last_hash:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(backup_dir, f".env_{timestamp}.bak")
                shutil.copy2(env_path, backup_path)
                print(f"[watchdog] Změna detekována, záloha vytvořena: {backup_path}")
                last_hash = current_hash
        time.sleep(interval)

# --- ENTRYPOINT ---
def main():
    if "--watch-env" in sys.argv:
        print("Spouštím watchdog pro .env soubor...")
        started = datetime.now(timezone.utc).isoformat()
        version = "1.0.0"
        def heartbeat_loop():
            while True:
                write_heartbeat(started, version)
                time.sleep(2)
        heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        atexit.register(remove_heartbeat, started)
        try:
            watch_env_file()
        except KeyboardInterrupt:
            print("\nWatchdog ukončen uživatelem.")
        finally:
            remove_heartbeat(started)
        sys.exit(0)

if __name__ == "__main__":
    main()
