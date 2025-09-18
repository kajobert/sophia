#!/usr/bin/env python3
"""
Sophia Starter: Spustí všechny klíčové služby (Redis, backend, Celery, Guardian) a monitoruje je.
"""
import subprocess
import time
import os
import signal
import sys

# --- Nastavení příkazů ---

REDIS_CMD = ["redis-server"]
BACKEND_CMD = ["dotenv", "run", "--", "uvicorn", "web.api.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
CELERY_CMD = ["env", "PYTHONPATH=.", "celery", "-A", "services.celery_worker.celery_app", "worker", "--loglevel=info"]
GUARDIAN_CMD = ["env", "PYTHONPATH=.", "python3", "guardian.py"]

processes = {}

def is_running(process_name):
    try:
        out = subprocess.check_output(["pgrep", "-f", process_name])
        return bool(out.strip())
    except subprocess.CalledProcessError:
        return False

def start_process(name, cmd, cwd=None):
    print(f"[Starter] Spouštím {name}... ({' '.join(cmd)})")
    # Všechny procesy spouštíme z kořene projektu
    project_root = os.path.dirname(os.path.abspath(__file__))
    proc = subprocess.Popen(cmd, cwd=project_root)
    processes[name] = proc
    time.sleep(2)
    return proc

def stop_all():
    print("[Starter] Ukončuji všechny spuštěné procesy...")
    for name, proc in processes.items():
        try:
            proc.terminate()
        except Exception:
            pass
    time.sleep(2)
    for name, proc in processes.items():
        if proc.poll() is None:
            proc.kill()
    print("[Starter] Vše ukončeno.")

def main():
    try:
        # 1. Redis
        if not is_running("redis-server"):
            start_process("redis", REDIS_CMD)
        else:
            print("[Starter] Redis už běží.")
        # 2. Backend
        if not is_running("uvicorn web.api.main:app"):
            start_process("backend", BACKEND_CMD)
        else:
            print("[Starter] Backend už běží.")
        # 3. Celery
        if not is_running("celery.*worker"):
            start_process("celery", CELERY_CMD)
        else:
            print("[Starter] Celery worker už běží.")
        # 4. Guardian
        start_process("guardian", GUARDIAN_CMD)
        print("[Starter] Všechny služby spuštěny. Pro ukončení stiskněte Ctrl+C.")
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n[Starter] Přerušeno uživatelem.")
    finally:
        stop_all()

if __name__ == "__main__":
    main()
