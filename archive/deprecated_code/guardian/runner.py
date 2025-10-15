import subprocess
import time
import os
import logging
import sys

# --- Konfigurace ---
TUI_APP_PATH = "tui/app.py"
CRASH_LOG_PATH = "logs/crash.log"
LAST_GOOD_COMMIT_FILE = ".last_known_good_commit"
MAX_RESTART_ATTEMPTS = 3
RESTART_DELAY_SECONDS = 5

# --- Nastavení logování ---
logging.basicConfig(
    level=logging.INFO,
    format="[Guardian] %(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/guardian.log"),
    ]
)

def get_last_known_good_commit() -> str:
    """
    Přečte hash posledního funkčního commitu. Pokud soubor neexistuje,
    vytvoří ho s aktuálním HEAD.
    """
    if not os.path.exists(LAST_GOOD_COMMIT_FILE):
        logging.warning(f"'{LAST_GOOD_COMMIT_FILE}' not found. Initializing with current HEAD.")
        try:
            current_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True, capture_output=True, text=True
            ).stdout.strip()

            with open(LAST_GOOD_COMMIT_FILE, "w") as f:
                f.write(current_commit)
            logging.info(f"Initialized '{LAST_GOOD_COMMIT_FILE}' with commit: {current_commit}")
            return current_commit
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"FATAL: Could not initialize last known good commit from git. Error: {e}")
            sys.exit(1)

    with open(LAST_GOOD_COMMIT_FILE, "r") as f:
        return f.read().strip()

def revert_to_last_known_good():
    """Provede 'git reset --hard' a bezpečný úklid na poslední funkční commit."""
    commit_hash = get_last_known_good_commit()
    logging.warning(f"Attempting to roll back to commit: {commit_hash}")
    try:
        subprocess.run(["git", "reset", "--hard", commit_hash], check=True, capture_output=True, text=True)
        subprocess.run(["git", "clean", "-df"], check=True, capture_output=True, text=True)
        logging.info(f"Successfully rolled back to commit {commit_hash}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"FATAL: Git rollback failed! Stderr: {e.stderr}")
        sys.exit(1)

def main():
    """
    Hlavní smyčka Guardiana, která spouští a monitoruje TUI aplikaci.
    """
    consecutive_failures = 0

    while True:
        logging.info(f"Starting TUI application: {TUI_APP_PATH}")

        # Použijeme Popen pro lepší kontrolu a správné předání TTY.
        # Důležité je, že nepředáváme stdin, stdout, stderr, aby si je proces vzal sám.
        process = subprocess.Popen([sys.executable, TUI_APP_PATH])
        
        # Čekáme, dokud proces neskončí.
        process.wait()

        if process.returncode == 0:
            logging.info("Application exited with code 0. Assuming clean exit. Guardian shutting down.")
            break

        consecutive_failures += 1
        logging.error(f"Application crashed with non-zero exit code {process.returncode}. This is failure #{consecutive_failures}.")
        
        if os.path.exists(CRASH_LOG_PATH):
             logging.info(f"Detailed crash information should be available in: {CRASH_LOG_PATH}")

        if consecutive_failures >= MAX_RESTART_ATTEMPTS:
            logging.warning(f"Reached {MAX_RESTART_ATTEMPTS} consecutive failures. Triggering rollback.")
            revert_to_last_known_good()
            consecutive_failures = 0

        logging.info(f"Restarting application in {RESTART_DELAY_SECONDS} seconds...")
        time.sleep(RESTART_DELAY_SECONDS)

if __name__ == "__main__":
    os.makedirs("logs", exist_ok=True)
    main()