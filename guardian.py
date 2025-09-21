import subprocess
import time
import os
import sys
from datetime import datetime
import psutil
import yaml
from sophia_monitor import check_recurring_errors

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "guardian.log")
MAIN_SCRIPT = "main.py"
CONFIG_FILE = "config.yaml"


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


def load_config():
    """Načte konfiguraci z YAML souboru."""
    try:
        with open(CONFIG_FILE, "r") as f:
            config = yaml.safe_load(f)
        return config.get("guardian", {})
    except FileNotFoundError:
        log_message(f"CHYBA: Konfigurační soubor '{CONFIG_FILE}' nebyl nalezen.")
        return {}
    except yaml.YAMLError as e:
        log_message(
            f"CHYBA: Chyba při parsování konfiguračního souboru '{CONFIG_FILE}': {e}"
        )
        return {}


def reset_repository():
    """Provede 'git reset --hard HEAD' pro obnovení repozitáře."""
    log_message("Guardian's reset_repository is disabled. Skipping git reset.")
    pass


def main():
    """Hlavní funkce Strážce, která spouští a monitoruje main.py."""
    log_message("Inteligentní Strážce (Intelligent Guardian) se spouští.")

    config = load_config()
    cpu_threshold = config.get("cpu_threshold", 90.0)
    ram_threshold = config.get("ram_threshold", 90.0)
    log_message(
        f"Nastavené prahové hodnoty: CPU > {cpu_threshold}%, RAM > {ram_threshold}%"
    )

    python_executable = sys.executable
    log_message(f"Bude použit Python interpret: {python_executable}")

    threshold_breach_counter = 0
    last_error_check = time.time()

    while True:
        log_message(f"Spouštím proces '{MAIN_SCRIPT}'...")
        # Ensure logs directory exists before starting the main script
        ensure_log_dir_exists()
        process = subprocess.Popen(
            [python_executable, MAIN_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        while process.poll() is None:
            # Proaktivní monitoring
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent

            if cpu_usage > cpu_threshold or ram_usage > ram_threshold:
                threshold_breach_counter += 1
                log_message(
                    f"VAROVÁNÍ: Překročení prahové hodnoty ({threshold_breach_counter}/3). CPU: {cpu_usage}%, RAM: {ram_usage}%"
                )
                if threshold_breach_counter >= 3:
                    log_message(
                        "KRITICKÉ: Prahová hodnota překročena 3x po sobě. Provádím měkký restart."
                    )
                    process.terminate()  # Graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        log_message("Proces nereagoval na terminate, provádím kill.")
                        process.kill()
                    break
            else:
                threshold_breach_counter = 0

            # Periodická kontrola chyb
            if time.time() - last_error_check > 300:  # 5 minutes
                log_message("Provádím periodickou kontrolu chronických chyb...")
                try:
                    # We need to pass the log paths to the function
                    log_files = [os.path.join(LOG_DIR, "sophia_main.log"), LOG_FILE]
                    check_recurring_errors(log_files)
                except Exception as e:
                    log_message(f"CHYBA při kontrole chronických chyb: {e}")
                last_error_check = time.time()

            time.sleep(4)  # Celkový cyklus je cca 5s (1s z cpu_percent + 4s sleep)

        stdout, stderr = process.communicate()
        if process.returncode != 0 and threshold_breach_counter < 3:
            log_message(
                f"PROCES '{MAIN_SCRIPT}' SE NEOČEKÁVANĚ UKONČIL S KÓDEM {process.returncode}."
            )
        else:
            log_message(f"Proces '{MAIN_SCRIPT}' byl ukončen.")

        if stdout:
            log_message(f"Stdout:\n{stdout.strip()}")
        if stderr:
            log_message(f"Stderr:\n{stderr.strip()}")

        log_message("Proces se restartuje za 10 sekund...")
        time.sleep(10)

        reset_repository()
        log_message("Restartuji cyklus.")
        threshold_breach_counter = 0  # Reset counter after restart


if __name__ == "__main__":
    main()
