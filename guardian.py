import subprocess
import time
import os
import sys
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "guardian.log")
MAIN_SCRIPT = "main.py"

def ensure_log_dir_exists():
    """Zajistí, že adresář pro logy existuje."""
    os.makedirs(LOG_DIR, exist_ok=True)

def log_message(message):
    """Zaznamená zprávu do logovacího souboru s časovým razítkem."""
    ensure_log_dir_exists()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"{timestamp} - {message}\n")
    print(message, flush=True)

def reset_repository():
    """Provede 'git reset --hard HEAD' pro obnovení repozitáře."""
    try:
        log_message("Pokouším se obnovit repozitář do čistého stavu (git reset --hard HEAD)...")
        result = subprocess.run(["git", "reset", "--hard", "HEAD"], check=True, capture_output=True, text=True)
        log_message(f"Repozitář úspěšně obnoven. stdout: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        log_message(f"CHYBA: Obnovení repozitáře selhalo! Chyba: {e.stderr.strip()}")
        return False
    except FileNotFoundError:
        log_message("CHYBA: Příkaz 'git' nebyl nalezen. Ujistěte se, že je Git nainstalován a v PATH.")
        return False

def main():
    """Hlavní funkce Strážce, která spouští a monitoruje main.py."""
    log_message("Strážce Bytí (Guardian) se spouští.")

    # Použijeme python executable, kterým byl spuštěn samotný guardian
    python_executable = sys.executable
    log_message(f"Bude použit Python interpret: {python_executable}")

    while True:
        log_message(f"Spouštím proces '{MAIN_SCRIPT}'...")
        process = subprocess.Popen([python_executable, MAIN_SCRIPT], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        while process.poll() is None:
            time.sleep(5)

        stdout, stderr = process.communicate()
        log_message(f"PROCES '{MAIN_SCRIPT}' SE NEOČEKÁVANĚ UKONČIL S KÓDEM {process.returncode}.")
        if stdout:
            log_message(f"Stdout:\n{stdout.strip()}")
        if stderr:
            log_message(f"Stderr:\n{stderr.strip()}")

        log_message("Proces se restartuje za 10 sekund...")
        time.sleep(10)

        reset_repository()
        log_message("Restartuji cyklus.")

if __name__ == "__main__":
    main()
